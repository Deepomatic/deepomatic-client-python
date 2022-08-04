import os
import json
import base64
import logging
import tempfile
import shutil
import hashlib
import requests
import zipfile

from deepomatic.api.version import __title__, __version__
from deepomatic.api.client import Client
from deepomatic.api.inputs import ImageInput

demo_url = "https://deepo-tests.s3-eu-west-1.amazonaws.com/api-clients/dog1.jpg"

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'),
                    format='[%(levelname)s %(name)s %(asctime)s %(process)d %(thread)d %(filename)s:%(lineno)s] %(message)s')
logger = logging.getLogger(__name__)


def demo(client=None):
    """
    Our REST client works by exposing resources. A resource usually has the following synchronous methods:

        - create(...): allow to create a new object. Please refere to documentation for a list
                     of arguments of each object resource.
        - list(offset=0, limit=100): return the list of objects, paginated by group of 'limit' objects.
        - retrieve(id):  allow to retrieve the JSON data representing the resource with given ID.
        - update(...): allow to change so fields of the resource. Depending on the resource you may or
                       may not be able to modify all the fields. Please refere to documentation for a list
                       of arguments of each object resource.
        - delete():    allow to delete the object.
    """

    #########
    # Setup #
    #########

    # You can create a client in two ways:
    # i) explicitly: you pass your APP_ID and API_KEY by calling `client = Client(app_id, api_key, user_agent_prefix='my-app/1.0.0')`
    # ii) implicitly: you define environment variables `DEEPOMATIC_APP_ID` and `DEEPOMATIC_API_KEY`
    #                 and just call `client = Client(user_agent_prefix='my-app/1.0.0')`
    #
    # In both ways `user_agent_prefix` parameter is optional but recommended to identify your app to the API
    # Here we actually use a mix of those two methods to illustrate:
    if client is None:
        api_key = os.getenv('DEEPOMATIC_API_KEY')
        client = Client(api_key=api_key, user_agent_prefix='{}-demo/{}'.format(__title__, __version__))


    ###################
    # Custom networks #
    ###################

    print_header("Adding a network (it may take some time to upload)...")
    """
    To starting playing with custom networks, let's first create a custom network.
    Here we will download a Tensorflow Inception v3 model but it would work the same for your own custom model !
    Below, we download:
    - saved_model.pb:  the network architecture
    - variables.*: the files that describe the learned parameters of the model (they might be included in the saved_model.pb).
    - mean_file: the file that stores the mean image that needs to be substracted from the input (optional)
    """

    extract_dir = tempfile.gettempdir()
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

    """
    Here, we specify the network preprocessing. Please refer to the documentation to see what each
    field is used for.
    """
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

    """
    We now register the three files needed by our network
    """
    files = {
        model_file_name: open(model_file, 'rb'),
        variables_file_name: open(variables_file, 'rb'),
        variables_data_file_name: open(variables_data_file, 'rb'),
        mean_file_name: open(mean_file, 'rb')
    }

    """
    We now upload our new network via the 'client.Network().create(...)' network.
    Please refere to the documentation for a description of each parameter.
    """
    network = client.Network.create(name="My first network",
                                    framework='tensorflow-1.x',
                                    preprocessing=preprocessing,
                                    files=files)
    network_id = network['id']
    print_comment("Network ID = {}".format(network_id))

    print_header("Editing network")
    """
    If you realized you did a mistake on some object parameters, you may modify it with '.update()'.
    This function takes some named parameters and sets their value. The name of parameters of course
    depends on the type of resource you are editing. Please refer to documentation to find out each
    which are the field of a given resource.
    """
    print_comment("Decription before (empty): '{}'".format(network['description']))
    network.update(description="I had forgotten the description")
    print_comment("Decription after: '{}'".format(network['description']))

    #############################
    # Custom recognition models #
    #############################

    print_header("Adding a recognition model")
    """
    Now that we have setup our new custom network, let's indicate which are the labels it is
    able to recognize. Here we retrieve the list of labels of imagenet from the public imagenet model.
    Please refere to the documentation for the description of 'outputs'
    """
    import json
    outputs = json.loads(open('outputs.imagenet-inception-v3.json').read())

    """
    We now create a recogntion specification with client.recognition_specs().create(...)
    """
    spec = client.RecognitionSpec.create(name="My recognition model", outputs=outputs)

    print_header("Getting the spec result")
    # Good to know: when you use create(), its return value is a resource object:
    # you can for example call 'spec.inference()' on it.
    print_comment("Spec ID = {}".format(spec['id']))

    print_header("Adding a version on a spec")
    """
    So far, we just specified the outputs of our recognition model. Each specification can hold
    a set of versions that might apply to different networks but produce the same output.
    Those versions are actually the link between:
    - a specification: that just decribe the output "format"
    - a network: that produce the actual computation
    - a post-processing: some network dependant parameters, for example to specify the output tensor
                         or some thresholds. The post_processings depends on what you want to do and
                        must match the number of 'outputs' specified when creating the 'spec'. Here,
                        it is a classification network so we create a 'classification' post-processing.
    """
    version = client.RecognitionVersion.create(network_id=network_id, spec_id=spec['id'], post_processings=[
        {
            "classification": {
                "output_tensor": "inception_v3/logits/predictions",
            }
        }
    ])
    print_comment("Version ID = {}".format(version['id']))
    """
    After attaching a first version to a spec, the current_version_id of the spec is automatically set
    """
    print_comment("Current version ID = {}".format(spec['current_version_id']))

    print_header("Wait for network deployment")
    """
    When creating a new recognition version, a worker will be created in our back-end to serve your request.
    Let's wait a few seconds until it boots.
    """
    client.Task.retrieve(network['task_id']).wait()

    print_header("Run inference on spec (using the current version)")
    """
    And this current version can be used to run inference for the spec directly
    """
    result = spec.inference(inputs=[ImageInput(demo_url)], show_discarded=True, max_predictions=3)
    logger.info(result)

    print_header("Run inference on specific version with a bounding box")
    result = version.inference(inputs=[ImageInput(demo_url, bbox={"xmin": 0.1, "ymin": 0.1, "xmax": 0.9, "ymax": 0.9})],
                               show_discarded=True,
                               max_predictions=3)
    logger.info(result)

    """
    Show all versions of a spec
    """
    logger.info(spec.versions())

    """
    Test the possibility of getting multiple tasks at the same time
    """
    task = spec.inference(inputs=[ImageInput(demo_url)], return_task=True, wait_task=False)
    task_id = task.pk
    tasks = client.Task.list(task_ids=[task_id])
    logger.info(tasks)

    print_header("Delete networks and recognition models")
    """
    And finally, we delete the network, which will delete the recognition version in cascade.
    """
    network.delete()




###########
# Helpers #
###########


def download_file(url):
    _, ext = os.path.splitext(url)
    filename = os.path.join(tempfile.gettempdir(),
                            hashlib.sha1(url.encode()).hexdigest() + ext)
    if os.path.exists(filename):  # avoid redownloading
        logger.info("Skipping download of {}: file already exist in {}".format(url, filename))
        return filename
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(filename, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)
    return filename


def print_header(text):
    logger.info("**** {} ****".format(text))


def print_comment(text):
    logger.info("--> " + text)


def pretty_print_json(data):
    logger.info(json.dumps(data, indent=4, separators=(',', ': ')))


def display_inference_tensor(result):
    for tensor_name, numpy_array in result.items():
        print_comment("tensor '{name}', dimensions: {dims}".format(name=tensor_name, dims='x'.join(map(str, numpy_array.shape))))


if __name__ == '__main__':
    demo()
