import os
import base64
import pytest
import tempfile
import hashlib
import shutil
import requests
import zipfile
from tenacity import RetryError
from deepomatic.api.version import __title__, __version__
from deepomatic.api.client import Client
from deepomatic.api.inputs import ImageInput
from pytest_voluptuous import S
from voluptuous.validators import All, Length, Any
import six
import time

import logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

DEMO_URL = "https://static.deepomatic.com/resources/demos/api-clients/dog1.jpg"

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


@pytest.fixture(scope='session')
def client():
    yield Client(user_agent_prefix=USER_AGENT_PREFIX)


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
    variables_file = os.path.join(extract_dir+'/variables/', variables_file_name)
    variables_data_file = os.path.join(extract_dir+'/variables/', variables_data_file_name)

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
        assert session_headers['User-Agent'].startswith('{}-tests/{} {}-python-client/{}'.format(__title__, __version__, __title__, __version__))
        assert 'platform/' in session_headers['User-Agent']
        assert 'python/' in session_headers['User-Agent']
        assert session_headers['X-APP-ID']
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

        result = version.inference(inputs=[ImageInput(DEMO_URL, bbox={"xmin": 0.1, "ymin": 0.1, "xmax": 0.9, "ymax": 0.9})], show_discarded=True, max_predictions=3)
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

        for i in range(nb_inference):
            task = spec.inference(inputs=[ImageInput(DEMO_URL)], return_task=True, wait_task=False)
            tasks.append(task)

        pending_tasks, success_tasks, error_tasks = client.Task.batch_wait(tasks=tasks, timeout=timeout)
        assert len(pending_tasks) == 0
        assert len(error_tasks) == 0
        assert len(success_tasks) == len(tasks)

        # pending_tasks, error_tasks and success_tasks contains the original offset of the input parameter tasks
        for pos, pending in pending_tasks:
            assert(tasks[pos].pk == pending.pk)
        for pos, err in error_tasks:
            assert(tasks[pos].pk == err.pk)
        for pos, success in success_tasks:
            assert(tasks[pos].pk == success.pk)
            assert inference_schema(2, 0, 'golden retriever', 0.8) == success['data']


def test_retry_client():
    timeout = 5
    client = Client(host='http://unknown-domain.com', retry_kwargs={'timeout': timeout})
    spec = client.RecognitionSpec.retrieve('imagenet-inception-v3')
    start_time = time.time()
    with pytest.raises(RetryError) as e:
        print(spec.data())

    assert time.time() - start_time > timeout
