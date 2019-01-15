import os
import sys
import json
import base64
import tarfile

import deepomatic
from deepomatic import ImageInput

if sys.version_info >= (3, 0):
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve

if len(sys.argv) < 2:
    api_host = None
else:
    api_host = sys.argv[1]

app_id = os.getenv('DEEPOMATIC_APP_ID')
api_key = os.getenv('DEEPOMATIC_API_KEY')
client = deepomatic.Client(app_id, api_key, host=api_host)

demo_url = "https://static.deepomatic.com/resources/demos/api-clients/dog1.jpg"


def demo():
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

    ###################
    # Public networks #
    ###################

    print_header("Listing public networks")
    """
    You can access the list of public networks with: 'client.Network.list(public=True)'
    Here, public networks are read only so you can only call '.list()'.
    The '.list()' method returns a paginated list of objects, i.e. an API call may not return all objects.
    By default, it returns 100 objects and gives your the URI at which you will find the next page.
    It takes two optionnal arguments:
      - 'offset': the index at which we should start iterating (defaut: 0)
      - 'limit': the number of element per page (default: 100)
    """
    for network in client.Network.list(public=True):
        print_comment("{network_id}: {name}".format(network_id=network['id'], name=network['name']))

    """
    You may also query the list of object with '.data()' but it will only return the JSON associated with
    the current page, unlike the iterator version above that will loop trough all the data.
    """
    result = client.Network.list(public=True).data()
    pretty_print_json(result)

    print_header("Getting network")
    """
    You can get an object resource using the client with the '.retrieve(id)' method. It will
    return an object resource which may have '.update(...)' and '.delete()' methods. They
    respectively modifiy it or delete the object. You may also invoke special actions like '.inference()'
    (see below). Here, we retrieve a public network named 'imagenet-inception-v1'
    """
    network = client.Network.retrieve('imagenet-inception-v1')
    print(network)

    #############################
    # Public recognition models #
    #############################

    print_header("Listing public recognition models")
    """
    A network by itself is not very usefull. It's more interesting when it's tied to some output labels !
    This is the role of a recognition specification: precisely describing some expected output.
    Those specifications will then be matched to a network via "specification versions".
    Lets first see the list of public recognition models with 'client.RecognitionSpec.list(public=True)'
    """
    for spec in client.RecognitionSpec.list(public=True):
        print_comment("- {spec_id}: {name}".format(spec_id=spec['id'], name=spec['name']))

    print_header("Getting spec")
    """
    Let's now focus on what we can do with a recognition models.
    We get the output specifications of the Inception v1 (GoogLeNet) model with client.recognition_spec('imagenet-inception-v1')
    We can see its spec with 'spec.data()'
    """
    spec = client.RecognitionSpec.retrieve('imagenet-inception-v1')
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
    file = open(download(demo_url, '/tmp/img.jpg'), 'rb')
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
    We will download the tradionnal Caffe GoogLeNet model but it would work the same for your own custom model !
    Below, we download:
    - deploy_prototxt: the file that describe the network architecture
    - snapshot_caffemodel: the file that describe the learned parameters of the model
    - mean_file: the file that stores the mean image that needs to be substracted from the input
    """
    deploy_prototxt = download('https://raw.githubusercontent.com/BVLC/caffe/master/models/bvlc_googlenet/deploy.prototxt', '/tmp/deploy.prototxt')
    snapshot_caffemodel = download('http://dl.caffe.berkeleyvision.org/bvlc_googlenet.caffemodel', '/tmp/snapshot.caffemodel')
    mean_file = '/tmp/imagenet_mean.binaryproto'
    if not os.path.exists(mean_file):
        archive = download('http://dl.caffe.berkeleyvision.org/caffe_ilsvrc12.tar.gz', '/tmp/caffe_ilsvrc12.tar.gz')
        tar = tarfile.open(archive, "r:gz")
        tar.extractall(path='/tmp/')
        tar.close()
    else:
        print_comment("Skipping download of mean file: {}".format(mean_file))
    """
    Here, we specify the network preprocessing. Please refer to the documentation to see what each
    field is used for.
    """
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

    """
    We now register the three files needed by our network
    """
    files = {
        'deploy.prototxt': deploy_prototxt,
        'snapshot.caffemodel': snapshot_caffemodel,
        'mean.binaryproto': mean_file
    }

    """
    We now upload our new network via the 'client.Network().create(...)' network.
    Please refere to the documentation for a description of each parameter.
    """
    network = client.Network.create(name="My first network",
                                    framework='nv-caffe-0.x-mod',
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
    outputs = client.RecognitionSpec.retrieve('imagenet-inception-v1')['outputs']

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
                "output_tensor": "prob",
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
    print(result)

    print_header("Run inference on specific version with a bounding box")
    result = version.inference(inputs=[ImageInput(demo_url, bbox={"xmin": 0.1, "ymin": 0.1, "xmax": 0.9, "ymax": 0.9})], show_discarded=True, max_predictions=3)
    print(result)

    """
    Show all versions of a spec
    """
    print(spec.versions())

    """
    Test the possibility of getting multiple tasks at the same time
    """
    task = spec.inference(inputs=[ImageInput(demo_url)], return_task=True, wait_task=False)
    task_id = task.pk
    tasks = client.Task.list(task_ids=[task_id])
    print(tasks)

    print_header("Delete networks and recognition models")
    """
    And finally, we delete the network, which will delete the recognition version and recognition spec in cascade.
    """
    network.delete()


def demo_batch_tasks():
    """
    Wait tasks per batch
    """
    print_header("Run multiple inferences and wait for them per batch")
    spec = client.RecognitionSpec.retrieve('imagenet-inception-v1')
    tasks = []
    timeout = 30
    nb_inference = 20
    print("Pushing %d inferences" % nb_inference)
    for i in range(nb_inference):
        task = spec.inference(inputs=[ImageInput(demo_url)], return_task=True, wait_task=False)
        tasks.append(task)
    print("Waiting for the results")
    pending_tasks, success_tasks, error_tasks = client.Task.batch_wait(tasks=tasks, timeout=timeout)
    if pending_tasks:
        print("Warning: %d tasks are still pending after %s seconds" % (len(pending_tasks), timeout))
    if error_tasks:
        print("Warning: %d tasks are in error" % len(error_tasks))
    print(pending_tasks)
    print(error_tasks)
    print(success_tasks)

    # pending_tasks, error_tasks and success_tasks contains the original offset of the input parameter tasks
    for pos, pending in pending_tasks:
        assert(tasks[pos].pk == pending.pk)
    for pos, err in error_tasks:
        assert(tasks[pos].pk == err.pk)
    for pos, success in success_tasks:
        assert(tasks[pos].pk == success.pk)




###########
# Helpers #
###########

def download(url, local_path):
    if not os.path.isfile(local_path):
        print("Downloading {} to {}".format(url, local_path))
        urlretrieve(url, local_path)
        if url.endswith('.tar.gz'):
            tar = tarfile.open(local_path, "r:gz")
            tar.extractall(path='/tmp/')
            tar.close()
    else:
        print("Skipping download of {} to {}: file already exist".format(url, local_path))
    return local_path


def print_header(text):
    print("\n{}".format(text))


def print_comment(text):
    print("--> " + text)


def pretty_print_json(data):
    print(json.dumps(data, indent=4, separators=(',', ': ')))


def display_inference_tensor(result):
    for tensor_name, numpy_array in result.items():
        print_comment("tensor '{name}', dimensions: {dims}".format(name=tensor_name, dims='x'.join(map(str, numpy_array.shape))))


if __name__ == '__main__':
    demo()
    demo_batch_tasks()
