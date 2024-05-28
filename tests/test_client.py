import base64
import functools
import hashlib
import logging
import os
import re
import shutil
import tempfile
import time
import zipfile

import httpretty
import pytest
import requests
import six
from deepomatic.api.client import Client
from deepomatic.api.exceptions import ServerError, ClientError, TaskError, TaskTimeout, HTTPRetryError, TaskRetryError
from deepomatic.api.http_retry import HTTPRetry
from deepomatic.api.inputs import ImageInput
from deepomatic.api.version import __title__, __version__
from requests.exceptions import ConnectionError, MissingSchema
from tenacity import RetryError, stop_after_delay

from pytest_voluptuous import S
from voluptuous.validators import All, Any, Length

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

DEMO_URL = "https://deepo-tests.s3-eu-west-1.amazonaws.com/api-clients/dog1.jpg"

USER_AGENT_PREFIX = '{}-tests/{}'.format(__title__, __version__)


def ExactLen(nb):
    return Length(min=nb, max=nb)


def download_file(url):
    _, ext = os.path.splitext(url)
    filename = os.path.join(tempfile.gettempdir(),
                            hashlib.sha1(url.encode()).hexdigest() + ext)
    if os.path.exists(filename):  # avoid redownloading
        return filename
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(filename, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)
    return filename


def get_client(*args, **kwargs):
    return Client(*args, user_agent_prefix=USER_AGENT_PREFIX, **kwargs)


@pytest.fixture(scope='session')
def client():
    yield get_client()


@pytest.fixture(scope='session')
def custom_network(client):
    extract_dir = '/tmp/inception_v3'
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)

    net_zip = download_file('https://s3-eu-west-1.amazonaws.com/deepo-public/run-demo-networks/imagenet-inception-v3/network.zip')
    preproc_zip = download_file('https://s3-eu-west-1.amazonaws.com/deepo-public/run-demo-networks/imagenet-inception-v3/preprocessing.zip')

    model_file_name = 'saved_model.pb'
    variables_file_name = 'variables.index'
    variables_data_file_name = 'variables.data-00000-of-00001'
    mean_file_name = 'mean.proto.bin'

    model_file = os.path.join(extract_dir, model_file_name)
    mean_file = os.path.join(extract_dir, mean_file_name)
    variables_file = os.path.join(extract_dir + '/variables/', variables_file_name)
    variables_data_file = os.path.join(extract_dir + '/variables/', variables_data_file_name)

    if not os.path.exists(model_file):
        with zipfile.ZipFile(net_zip) as f:
            f.extractall(extract_dir)
    if not os.path.exists(mean_file):
        with zipfile.ZipFile(preproc_zip) as f:
            f.extractall(extract_dir)

    preprocessing = {
        "inputs": [
            {
                "tensor_name": "map/TensorArrayStack/TensorArrayGatherV3:0",
                "image": {
                    "dimension_order": "NHWC",
                    "target_size": "299x299",
                    "resize_type": "CROP",
                    "mean_file": mean_file_name,
                    "color_channels": "BGR",
                    "pixel_scaling": 2.0,
                    "data_type": "FLOAT32"
                }
            }
        ],
        "batched_output": True
    }

    files = {
        model_file_name: open(model_file, 'rb'),
        variables_file_name: open(variables_file, 'rb'),
        variables_data_file_name: open(variables_data_file, 'rb'),
        mean_file_name: open(mean_file, 'rb')
    }

    network = client.Network.create(name="My first network",
                                    framework='tensorflow-1.x',
                                    preprocessing=preprocessing,
                                    files=files)
    assert network['id']
    data = network.data()
    assert network['name'] == 'My first network'
    assert 'description' in data
    assert 'create_date' in data
    assert 'update_date' in data

    yield network
    network.delete()


def check_first_prediction(first_label_name, first_score_range):
    def check(predicted):
        assert predicted[0]['label_name'] == first_label_name
        assert predicted[0]['score'] > first_score_range
        return predicted
    return check


def check_score_threshold(is_predicted):
    def check(predicted):
        for pred in predicted:
            if is_predicted:
                assert pred['score'] >= pred['threshold']
            else:
                assert pred['score'] < pred['threshold']
        return predicted
    return check


def prediction_schema(exact_len, *args):
    return All([{
        'threshold': float,
        'label_id': int,
        'score': float,
        'label_name': Any(*six.string_types),
    }], ExactLen(exact_len), *args)


def inference_schema(predicted_len, discarded_len, first_label, first_score):
    return S({
        'outputs': All([{
            'labels': {
                'predicted': prediction_schema(predicted_len, check_first_prediction(first_label, first_score),
                                               check_score_threshold(is_predicted=True)),
                'discarded': prediction_schema(discarded_len, check_score_threshold(is_predicted=False))
            }
        }], ExactLen(1)),
    })


class TestClient(object):

    def test_headers(self, client):
        http_helper = client.http_helper
        session_headers = http_helper.session.headers
        assert session_headers['User-Agent'].startswith(
            '{}-tests/{} {}-python-client/{}'.format(__title__, __version__, __title__, __version__))
        assert 'platform/' in session_headers['User-Agent']
        assert 'python/' in session_headers['User-Agent']
        assert session_headers['X-API-KEY']

        headers = http_helper.setup_headers(headers={'Hello': 'World'},
                                            content_type='application/json')
        assert headers == {
            'Hello': 'World',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def test_list_specs(self, client):
        specs = client.RecognitionSpec.list(public=True)
        assert specs.count() > 0
        for spec in specs:
            assert spec['id']
            data = spec.data()
            assert 'name' in data
            assert 'description' in data
            assert 'update_date' in data

        result = client.RecognitionSpec.list(public=True).data()
        assert len(result['results']) > 0
        assert result['count'] > 0

    def test_retrieve_spec(self, client):
        spec = client.RecognitionSpec.retrieve('imagenet-inception-v3')
        assert spec['id']
        data = spec.data()
        assert 'name' in data
        assert 'description' in data
        assert 'update_date' in data

    def test_inference_spec(self, client):
        spec = client.RecognitionSpec.retrieve('imagenet-inception-v3')
        first_result = spec.inference(inputs=[ImageInput(DEMO_URL)], show_discarded=True, max_predictions=3)

        assert inference_schema(2, 1, 'golden retriever', 0.8) == first_result

        f = open(download_file(DEMO_URL), 'rb')
        result = spec.inference(inputs=[ImageInput(f)], show_discarded=True, max_predictions=3)
        assert result == first_result

        f.seek(0)
        binary_data = f.read()
        result = spec.inference(inputs=[ImageInput(binary_data, encoding="binary")], show_discarded=True, max_predictions=3)
        assert result == first_result

        b64 = base64.b64encode(binary_data)
        result = spec.inference(inputs=[ImageInput(b64, encoding="base64")], show_discarded=True, max_predictions=3)
        assert result == first_result

    def test_create_custom_reco_and_infer(self, client, custom_network):

        # test query by id
        network = client.Network.retrieve(custom_network['id'])
        assert network['name']
        custom_network.update(description="I had forgotten the description")

        outputs = client.RecognitionSpec.retrieve('imagenet-inception-v3')['outputs']

        spec = client.RecognitionSpec.create(name="My recognition model", outputs=outputs)

        version = client.RecognitionVersion.create(network_id=custom_network['id'], spec_id=spec['id'], post_processings=[
            {
                "classification": {
                    "output_tensor": "inception_v3/logits/predictions",
                }
            }

        ])
        assert version['id']
        data = version.data()
        assert data['network_id'] == custom_network['id']
        assert 'post_processings' in data

        client.Task.retrieve(custom_network['task_id']).wait()

        result = spec.inference(inputs=[ImageInput(DEMO_URL)], show_discarded=False, max_predictions=3)
        assert inference_schema(2, 0, 'golden retriever', 0.8) == result

        result = version.inference(inputs=[ImageInput(DEMO_URL, bbox={"xmin": 0.1, "ymin": 0.1, "xmax": 0.9, "ymax": 0.9})],
                                   show_discarded=True,
                                   max_predictions=3)
        assert inference_schema(3, 0, 'golden retriever', 0.5) == result

        versions = spec.versions()
        assert versions.count() > 0
        data = versions.data()
        assert len(data['results']) > 0
        assert data['count'] > 0

        task = spec.inference(inputs=[ImageInput(DEMO_URL)], return_task=True, wait_task=False)
        task_id = task.pk
        tasks = client.Task.list(task_ids=[task_id])
        tasks = list(tasks)  # convert iterables to list
        assert len(tasks) == 1
        task = tasks[0]
        assert task['status'] in ['pending', 'success']
        assert task['error'] is None
        task.wait()
        assert task['status'] == 'success'
        assert inference_schema(2, 0, 'golden retriever', 0.8) == task['data']

    def test_batch_wait(self, client):
        spec = client.RecognitionSpec.retrieve('imagenet-inception-v3')
        tasks = []
        timeout = 30
        nb_inference = 20

        for _ in range(nb_inference):
            task = spec.inference(inputs=[ImageInput(DEMO_URL)], return_task=True, wait_task=False)
            tasks.append(task)

        pending_tasks, success_tasks, error_tasks = client.Task.batch_wait(tasks=tasks, timeout=timeout)
        assert len(pending_tasks) == 0
        assert len(error_tasks) == 0
        assert len(success_tasks) == len(tasks)

        # pending_tasks, error_tasks and success_tasks contains the original offset of the input parameter tasks
        for pos, pending in pending_tasks:
            assert (tasks[pos].pk == pending.pk)
        for pos, err in error_tasks:
            assert (tasks[pos].pk == err.pk)
        for pos, success in success_tasks:
            assert (tasks[pos].pk == success.pk)
            assert inference_schema(2, 0, 'golden retriever', 0.8) == success['data']

        # Task* str(): oneliners (easier to parse in log tooling)
        task = success_tasks[0][1]
        task_error = TaskError(task._data)
        task_timeout = TaskTimeout(task._data)
        assert '\n' not in str(task)
        assert '\n' not in str(task_error)
        assert '\n' not in str(task_timeout)

    def test_client_error(self, client):
        spec = client.RecognitionSpec.retrieve('imagenet-inception-v3')
        with pytest.raises(ClientError) as exc:
            spec.inference(inputs=[])

        assert 400 == exc.value.status_code
        assert 'error' in exc.value.json()


class TestClientRetry(object):
    DEFAULT_TIMEOUT = 2
    DEFAULT_MIN_ATTEMPT_NUMBER = 3

    def get_client_with_retry(self):
        http_retry = HTTPRetry(stop=stop_after_delay(self.DEFAULT_TIMEOUT))
        return get_client(http_retry=http_retry)

    def send_request_and_expect_retry(self, client, timeout, min_attempt_number):
        spec = client.RecognitionSpec.retrieve('imagenet-inception-v3')  # doesn't make any http call
        start_time = time.time()
        with pytest.raises(RetryError) as exc:
            print(spec.data())  # does make a http call

        diff = time.time() - start_time
        assert diff > timeout and diff < timeout + HTTPRetry.Default.RETRY_EXP_MAX
        last_attempt = exc.value.last_attempt
        assert last_attempt.attempt_number >= min_attempt_number
        return last_attempt

    def test_retry_network_failure(self):
        http_retry = HTTPRetry(stop=stop_after_delay(self.DEFAULT_TIMEOUT))
        client = get_client(host='http://invalid-domain.deepomatic.com',
                            http_retry=http_retry)
        last_attempt = self.send_request_and_expect_retry(client, self.DEFAULT_TIMEOUT,
                                                          self.DEFAULT_MIN_ATTEMPT_NUMBER)
        exc = last_attempt.exception(timeout=0)
        assert isinstance(exc, ConnectionError)
        assert 'Name or service not known' in str(exc)

        spec = client.RecognitionSpec.retrieve('imagenet-inception-v3')  # doesn't make any http call
        with pytest.raises(HTTPRetryError) as exc:
            print(spec.data())  # does make a http call

        # raise Exception(exc.value)
        assert str(exc.value).startswith(
            """Last attempt was an exception <class 'requests.exceptions.ConnectionError'> \""""
            """HTTPConnectionPool(host='invalid-domain.deepomatic.com', port=80): Max retries exceeded with url: """
            """/v0.7/recognition/public/imagenet-inception-v3/ (Caused by NameResolutionError"""
            """("<urllib3.connection.HTTPConnection object at"""
        )
        assert str(exc.value).endswith("""
        >: Failed to resolve 'invalid-domain.deepomatic.com' ([Errno -2] Name or service not known)"))"
        """.strip())

    def test_retry_bad_status_code(self):
        client = get_client(host='https://httpbin.org', version=None)
        with httpretty.enabled():
            httpretty.register_uri(
                httpretty.GET,
                re.compile(r'https?://.*?/?'),
                status=502,
            )  # to avoid flakyness we prefer to mock even though httpbin is done for that
            with pytest.raises(HTTPRetryError) as retry_error:
                client.http_helper.get('/status/502')
            assert str(retry_error.value) == "Last attempt was a Response <status_code=502 method=GET url=https://httpbin.org//status/502>"

    def register_uri(self, methods, status):
        for method in methods:
            httpretty.register_uri(
                method,
                re.compile(r'https?://.*'),
                status=502,
                content_type="application/json"
            )

    @httpretty.activate
    def test_retry_bad_http_status(self):
        self.register_uri([httpretty.GET, httpretty.POST], 502)
        client = self.get_client_with_retry()
        last_attempt = self.send_request_and_expect_retry(client, self.DEFAULT_TIMEOUT,
                                                          self.DEFAULT_MIN_ATTEMPT_NUMBER)
        assert last_attempt.exception(timeout=0) is None  # no exception raised during retry
        last_response = last_attempt.result()
        assert 502 == last_response.status_code

    @httpretty.activate
    def test_no_retry_create_network(self):
        self.register_uri([httpretty.GET, httpretty.POST], 502)
        client = self.get_client_with_retry()
        # Creating network doesn't retry, we directly get a 502
        t = time.time()
        with pytest.raises(ServerError) as exc:
            client.Network.create(name="My first network",
                                  framework='tensorflow-1.x',
                                  preprocessing=["useless"],
                                  files=["useless"])
        assert 502 == exc.value.status_code
        assert time.time() - t < 0.3

    def test_retry_task_with_http_errors(self):
        # We create two clients on purpose because of a bug in httpretty
        # https://github.com/gabrielfalcao/HTTPretty/issues/381
        # Also this allow us to test a simple requests with no retryer

        client = get_client(http_retry=None)
        spec = client.RecognitionSpec.retrieve('imagenet-inception-v3')
        task = spec.inference(inputs=[ImageInput(DEMO_URL)], return_task=True, wait_task=False)

        client = self.get_client_with_retry()
        with httpretty.enabled():
            task = client.Task.retrieve(task.pk)
            httpretty.register_uri(
                httpretty.GET,
                re.compile(r'https?://.*?/tasks/\d+/?'),
                status=502,
            )

            with pytest.raises(TaskTimeout) as task_timeout:
                task.wait(timeout=5)

            # Test nested retry errors
            # TaskRetryError has been raised because of too many HTTPRetryError
            # (couldn't refresh the status once)
            retry_error = task_timeout.value.retry_error
            assert isinstance(retry_error, TaskRetryError)
            last_exception = retry_error.last_attempt.exception(timeout=0)
            assert isinstance(last_exception, HTTPRetryError)
            assert 502 == last_exception.last_attempt.result().status_code

    def test_no_retry_blacklist_exception(self):
        client = self.get_client_with_retry()
        # check that there is no retry on exceptions from DEFAULT_RETRY_EXCEPTION_TYPES_BLACKLIST
        with pytest.raises(MissingSchema):
            client.http_helper.http_retry.retry(functools.partial(requests.get, ''))
