import os
import base64
import tarfile
import pytest
import tempfile
import hashlib
import shutil
import requests
from deepomatic.api.client import Client
from deepomatic.api.inputs import ImageInput
from pytest_voluptuous import S
from voluptuous.validators import All, Length, Any
import six

import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

DEMO_URL = "https://static.deepomatic.com/resources/demos/api-clients/dog1.jpg"


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
    api_host = os.getenv('DEEPOMATIC_API_URL')
    app_id = os.environ['DEEPOMATIC_APP_ID']
    api_key = os.environ['DEEPOMATIC_API_KEY']
    yield Client(app_id, api_key, host=api_host)


@pytest.fixture(scope='session')
def custom_network(client):
    deploy_prototxt = download_file('https://raw.githubusercontent.com/BVLC/caffe/master/models/bvlc_googlenet/deploy.prototxt')
    snapshot_caffemodel = download_file('http://dl.caffe.berkeleyvision.org/bvlc_googlenet.caffemodel')
    extract_dir = tempfile.gettempdir()
    mean_file = os.path.join(extract_dir, 'imagenet_mean.binaryproto')
    if not os.path.exists(mean_file):
        archive = download_file('http://dl.caffe.berkeleyvision.org/caffe_ilsvrc12.tar.gz')
        tar = tarfile.open(archive, "r:gz")
        tar.extractall(path=extract_dir)
        tar.close()

    preprocessing = {
        "inputs": [
            {
                "tensor_name": "data",
                "image": {
                    "color_channels": "BGR",
                    "target_size": "224x224",
                    "resize_type": "SQUASH",
                    "mean_file": "mean.binaryproto",
                    "dimension_order": "NCHW",
                    "pixel_scaling": 255.0,
                    "data_type": "FLOAT32"
                }
            }
        ],
        "batched_output": True
    }

    files = {
        'deploy.prototxt': deploy_prototxt,
        'snapshot.caffemodel': snapshot_caffemodel,
        'mean.binaryproto': mean_file
    }

    network = client.Network.create(name="My first network",
                                    framework='nv-caffe-0.x-mod',
                                    preprocessing=preprocessing,
                                    files=files)
    assert network['id']
    assert network['name'] == 'My first network'
    data = network.data()
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
        'label_name': All(Any(*six.string_types)),
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
    def test_retrieve_network(self, client):
        network = client.Network.retrieve('imagenet-inception-v1')
        assert network['id']
        data = network.data()
        assert 'name' in data
        assert 'description' in data
        assert 'create_date' in data
        assert 'update_date' in data

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
        spec = client.RecognitionSpec.retrieve('imagenet-inception-v1')
        assert spec['id']
        data = spec.data()
        assert 'name' in data
        assert 'description' in data
        assert 'update_date' in data

    def test_inference_spec(self, client):
        spec = client.RecognitionSpec.retrieve('imagenet-inception-v1')
        first_result = spec.inference(inputs=[ImageInput(DEMO_URL)], show_discarded=True, max_predictions=3)

        assert inference_schema(1, 2, 'golden retriever', 0.9) == first_result

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
        custom_network.update(description="I had forgotten the description")

        outputs = client.RecognitionSpec.retrieve('imagenet-inception-v1')['outputs']

        spec = client.RecognitionSpec.create(name="My recognition model", outputs=outputs)

        version = client.RecognitionVersion.create(network_id=custom_network['id'], spec_id=spec['id'], post_processings=[
            {
                "classification": {
                    "output_tensor": "prob",
                }
            }

        ])
        assert version['id']
        data = version.data()
        assert data['network_id'] == custom_network['id']
        assert 'post_processings' in data

        client.Task.retrieve(custom_network['task_id']).wait()

        result = spec.inference(inputs=[ImageInput(DEMO_URL)], show_discarded=False, max_predictions=3)
        assert inference_schema(1, 0, 'golden retriever', 0.9) == result

        result = version.inference(inputs=[ImageInput(DEMO_URL, bbox={"xmin": 0.1, "ymin": 0.1, "xmax": 0.9, "ymax": 0.9})], show_discarded=True, max_predictions=3)
        assert inference_schema(1, 2, 'golden retriever', 0.9) == result

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
        assert inference_schema(1, 0, 'golden retriever', 0.9) == task['data']

    def test_batch_wait(self, client):
        spec = client.RecognitionSpec.retrieve('imagenet-inception-v1')
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
            assert inference_schema(1, 0, 'golden retriever', 0.9) == success['data']
