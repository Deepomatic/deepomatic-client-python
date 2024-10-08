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
    # Public networks #
    ###################

    print_header("Getting network")
    """
    Let's start by getting some public neural network.
    You can get an object resource using the client with the '.retrieve(id)' method. It will
    return an object resource which may have '.update(...)' and '.delete()' methods. They
    respectively modifiy it or delete the object. You may also invoke special actions like '.inference()'
    (see below). Here, we retrieve a public network named 'imagenet-inception-v3'
    """
    network = client.Network.retrieve('imagenet-inception-v3')
    logger.info(network)

    #############################
    # Public recognition models #
    #############################

    print_header("Listing public recognition models")
    """
    A network by itself is not very usefull. It's more interesting when it's tied to some output labels !
    This is the role of a recognition specification: precisely describing some expected output.
    Those specifications will then be matched to a network via "specification versions".
    Lets first see the list of public recognition models with 'client.RecognitionSpec.list(public=True)'
    Here, public recognition models are read only so you can only call '.list()'.
    The '.list()' method returns a paginated list of objects, i.e. an API call may not return all objects.
    By default, it returns 100 objects and gives your the URI at which you will find the next page.
    It takes two optionnal arguments:
      - 'offset': the index at which we should start iterating (defaut: 0)
      - 'limit': the number of element per page (default: 100)
    """
    for spec in client.RecognitionSpec.list(public=True):
        print_comment("- {spec_id}: {name}".format(spec_id=spec['id'], name=spec['name']))

    """
    You may also query the list of object with '.data()' but it will only return the JSON associated with
    the current page, unlike the iterator version above that will loop trough all the data.
    """
    result = client.RecognitionSpec.list(public=True).data()
    pretty_print_json(result)

    print_header("Getting spec")
    """
    Let's now focus on what we can do with a recognition models.
    We get the output specifications of the Imagenet Inception v3 model with client.recognition_spec('imagenet-inception-v3')
    We can see its spec with 'spec.data()'
    """
    spec = client.RecognitionSpec.retrieve('imagenet-inception-v3')
    pretty_print_json(spec.data())

    print_header("Inference from a URL")
    """
    You can call '.inference()' on a spec, which will give you access on raw tensor output.
    Inference requests may take input image in various forms.
    Here, it take an url as input via 'ImageInput(demo_url)'.
    Also we have used the generic form of inference which might take multiple inputs if your networks has multiple ones.
    """
    result = spec.inference(inputs=[ImageInput(demo_url)], show_discarded=True, max_predictions=3)
    pretty_print_json(result)

    print_header("Inference from a file")
    """
    '.inference()' also support when you pass a single input instead of a list of inputs.
    Here, it takes a file pointer as input.
    """
    file = open(download_file(demo_url), 'rb')
    result = spec.inference(inputs=[ImageInput(file)], show_discarded=True, max_predictions=3)
    pretty_print_json(result)

    print_header("Inference from binary data")
    """
    It also support raw data, in which case you must specify how it is encoded.
    'binary' means you are passing raw binary data.
    """
    file.seek(0)
    binary_data = file.read()
    result = spec.inference(inputs=[ImageInput(binary_data, encoding="binary")], show_discarded=True, max_predictions=3)
    pretty_print_json(result)

    print_header("Inference from base64 data")
    """
    If for some reasons you want to work with base64 encoded data, you also can ! Just specify base64 as encoding !
    """
    b64 = base64.b64encode(binary_data)
    result = spec.inference(inputs=[ImageInput(b64, encoding="base64")], show_discarded=True, max_predictions=3)
    pretty_print_json(result)

    """
    This model can recognize the 1000 official categories of imagenet, so it might not fit your use case.
    In the following, we will learn how to deploy your custom models in deepomatic's API.
    """

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
    """

    extract_dir = tempfile.gettempdir()
    net_zip = download_file('https://s3-eu-west-1.amazonaws.com/deepo-public/run-demo-networks/imagenet-inception-v3/network.zip')

    model_file_name = 'saved_model.pb'
    variables_file_name = 'variables.index'
    variables_data_file_name = 'variables.data-00000-of-00001'

    model_file = os.path.join(extract_dir, model_file_name)
    variables_file = os.path.join(extract_dir + '/variables/', variables_file_name)
    variables_data_file = os.path.join(extract_dir + '/variables/', variables_data_file_name)

    if not os.path.exists(model_file):
        with zipfile.ZipFile(net_zip) as f:
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
    outputs = client.RecognitionSpec.retrieve('imagenet-inception-v3')['outputs']

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

    #########################
    # Batched wait on tasks #
    #########################

    print_header("Run multiple inferences and wait for them per batch")
    spec = client.RecognitionSpec.retrieve('imagenet-inception-v3')
    tasks = []
    timeout = 30
    nb_inference = 20

    logger.info("Pushing %d inferences" % nb_inference)
    for _ in range(nb_inference):
        task = spec.inference(inputs=[ImageInput(demo_url)], return_task=True, wait_task=False)
        tasks.append(task)

    logger.info("Waiting for the results")
    pending_tasks, success_tasks, error_tasks = client.Task.batch_wait(tasks=tasks, timeout=timeout)
    if pending_tasks:
        logger.warning("%d tasks are still pending after %s seconds" % (len(pending_tasks), timeout))
    if error_tasks:
        logger.warning("%d tasks are in error" % len(error_tasks))
    logger.info(pending_tasks)
    logger.info(error_tasks)
    logger.info(success_tasks)

    # pending_tasks, error_tasks and success_tasks contains the original offset of the input parameter tasks
    for pos, pending in pending_tasks:
        assert (tasks[pos].pk == pending.pk)
    for pos, err in error_tasks:
        assert (tasks[pos].pk == err.pk)
    for pos, success in success_tasks:
        assert (tasks[pos].pk == success.pk)

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
        shape_str = 'x'.join(map(str, numpy_array.shape))
        print_comment(f"tensor '{tensor_name}', shape: {shape_str}")


if __name__ == '__main__':
    demo()
