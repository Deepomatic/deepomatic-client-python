import os
import sys
import json
import base64
import tarfile

import deepomatic
from deepomatic.exceptions import DeepomaticException

if sys.version_info >= (3, 0):
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve

app_id = os.environ['DEEPOMATIC_APP_ID']
api_key = os.environ['DEEPOMATIC_API_KEY']
client = deepomatic.Client(app_id, api_key)

demo_url = "https://static.deepomatic.com/resources/demos/api-clients/dog1.jpg"


def demo():
    """
    Our REST client works by exposing resources. The responses of the client methods are either
    (i) an object resource, e.g. when you call 'client.network(id)'. This resource type usually has the
        following methods:
            - get(): allow to retrieve the JSON data representing the object.
            - edit(...): allow to change so fields of the resource. Depending on the resource you may or
                         may not be able to modify all the fields. Please refere to documentation for a list
                         of arguments of each object resource.
            - delete(): allow to delete the object.
    (ii) a *set* of objects, e.g. when you call 'client.networks()'. This resource exposes the following
        methods:
            - create(...): allow to create a new object. Please refere to documentation for a list
                         of arguments of each object resource.
            - list(offset=0, limit=100): return the list of objects, paginated by group of 'limit' objects.

    Each of those 5 methods get/edit/delete/create/list is asynchronous. To actually block until the API query
    finished, you must call '.result()' on their returned value.
    You can also chain API queries by calling '.then(lamba result: ...)'. The function passed as argument of
    '.then(function)' will be called with the result of the previous query as soon as it is available.
    """

    ###################
    # Public networks #
    ###################

    print_header("Listing public networks")
    """
    You can access the list of public networks with: 'client.public_networks().list()'
    'public_networks()' returns a resource set that usually have two methods: '.list()' and '.create()'.
    Here, public networks are read only so you can only call '.list()'.
    The '.list()' method returns a paginated list of objects, i.e. an API call may not return all objects.
    By default, it return 100 object and gives your the URI at which you will find the next page.
    It takes two optionnal arguments:
      - 'offset': the index at which we should start iterating (defaut: 0)
      - 'limit': the number of element per page (default: 100)
    """
    for network in client.public_networks().list():
        print_comment("{network_id}: {name}".format(network_id=network['id'], name=network['name']))

    """
    You may also query the list of object with '.result()' but it will only return the JSON associated with
    the current page, unlike the iterator version above that will loop trough all the data.
    """
    pretty_print_json(client.public_networks().list().result())

    print_header("Getting network")
    """
    You can get an object resource using the client. An object resource may have '.get()', '.edit()' or '.delete()'
    methods. They respectively retrieve the object data, modifiy it or delete the object.
    Depending of the object type, you may also invoke special actions like '.inference()' (see below).
    Here, we retrieve a public network named 'imagenet-inception-v1'
    """
    network = client.network('imagenet-inception-v1')
    pretty_print_json(network.get().result())

    """
    We do no have access to edit() or delete() on this object as it is read-only:
    """
    try:
        network.delete().result()
        raise Exception("This won't get to this point !")
    except DeepomaticException as e:
        print_comment(str(e))

    print_header("Inference from a URL")
    """
    As said above, you can call '.inference()' on a network, which will give you access on raw tensor output.
    Inference requests may take input image in various forms.
    Here, it take an url as input via 'deepomatic.ImageInput(demo_url)'.
    Also we have used the generic form of inference which might take multiple inputs if your networks has multiple ones.
    """
    result = network.inference(inputs=[deepomatic.ImageInput(demo_url)], output_tensors=["prob", "pool2/3x3_s2", "pool5/7x7_s1"]).result()
    display_inference_tensor(result)

    print_header("Inference from a file")
    """
    '.inference()' also support when you pass a single input instead of a list of inputs.
    Here, it takes a file pointer as input.
    """
    file = open(download(demo_url, '/tmp/img.jpg'), 'rb')
    result = network.inference(inputs=deepomatic.ImageInput(file), output_tensors=["prob"]).result()
    display_inference_tensor(result)

    print_header("Inference from binary data")
    """
    It also support raw data, in which case you must specify how it is encoded.
    'binary' means you are passing raw binary data.
    """
    file.seek(0)
    binary_data = file.read()
    result = network.inference(inputs=deepomatic.ImageInput(binary_data, encoding="binary"), output_tensors=["prob"]).result()
    display_inference_tensor(result)

    print_header("Inference from base64 data")
    """
    If for some reasons you want to work with base64 encoded data, you also can ! Just specify base64 as encoding !
    """
    b64 = base64.b64encode(binary_data)
    result = network.inference(inputs=deepomatic.ImageInput(b64, encoding="base64"), output_tensors=["prob"]).result()
    display_inference_tensor(result)

    #############################
    # Public recognition models #
    #############################

    print_header("Listing public recognition models")
    """
    A network by itself is not very usefull. It's more interesting when it's tied to some output labels !
    This is the role of a recognition specification: precisely describing some expected output.
    Those specifications will then be matched to a network via "specification versions".
    Lets first see the list of public recognition models with 'client.public_recognition_specs()'
    """
    for spec in client.public_recognition_specs().list():
        print_comment("- {spec_id}: {name}".format(spec_id=spec['id'], name=spec['name']))

    print_header("Getting spec")
    """
    Let's now focus on what we can do with a recognition models.
    We get the output specifications of the Inception v1 (GoogLeNet) model with client.recognition_spec('imagenet-inception-v1')
    We can see its spec with 'spec.get().result()'
    """
    spec = client.recognition_spec('imagenet-inception-v1')
    pretty_print_json(spec.get().result())

    print_header("Infering an image on recognition spec current version")
    """
    This recognition model is already tied to a specific version managed by deepomatic, so we can directly perform
    inference on it and use it to tag the content of images with their main category.
    """
    result = spec.inference(inputs=deepomatic.ImageInput(demo_url), show_discarded=True, max_predictions=3).result()
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
    Here, we specfic the network preprocessing. Please refer to the documentation to see what each
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
                    "dimension_order": "NCHW"
                }
            }
        ],
        "batched_output": True
    }

    """
    We now register the three file needed by our network
    """
    files = {
        'deploy.prototxt': deploy_prototxt,
        'snapshot.caffemodel': snapshot_caffemodel,
        'mean.binaryproto': mean_file
    }

    """
    We now upload our new network via the 'client.networks().create()' network.
    Please refere to the documentation for a description of each parameter.
    """
    network = client.networks().create(name="My first network",
                                       framework='nv-caffe-0.x-mod',
                                       preprocessing=preprocessing,
                                       files=files)

    """
    We get the network JSON data via `network.get().result()`
    """
    network_data = network.get().result()
    network_id = network_data['id']
    print_comment("Network ID = {}".format(network_id))

    print_header("Wait for network deployment")
    """
    When creating a new network, a worker will be created in our back-end to serve your request.
    Let's wait a few seconds until it boots.
    """
    client.task(network_data['task_id']).wait().result()

    print_header("Editing network")
    """
    If you realized you did a mistake on some object parameters, you may modify it with '.edit()'.
    This function takes some named parameters and sets their value. The name of parameters of course
    depends on the type of resource you are editing. Please refer to documentation to find out each
    which are the field of a given resource.
    """
    descr = network_data['description']
    print_comment("Decription before (empty): '{}'".format(descr))
    descr = network.edit(description="I had forgotten the description").result()['description']
    print_comment("Decription after: '{}'".format(descr))

    #############################
    # Custom recognition models #
    #############################

    print_header("Adding a recognition model")
    """
    Now that we have setup our new custom network, let's indicate which are the labels it is
    able to recognize. Here we retrieve the list of labels of imagenet from the public imagenet model.
    Please refere to the documentation for the description of 'outputs'
    """
    outputs = client.recognition_spec('imagenet-inception-v1').get().result()['outputs']

    """
    We now create a recogntion specification with client.recognition_specs().create(...)
    """
    spec = client.recognition_specs().create(name="My recognition model", outputs=outputs)

    print_header("Getting the spec result")
    # Good to know: when you use create(), its return value behave at the same time:
    # - as a result: you can call 'spec.resut()'
    # - as a resource: you can call 'spec.get().resut()' or 'spec.inference()'
    spec_id = spec.result()['id']
    print_comment("Spec ID = {}".format(spec_id))

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
    version = client.recognition_versions().create(network_id=network_id, spec_id=spec_id, post_processings=[
        {
            "classification": {
                "output_tensor": "prob",
            }
        }
    ])
    print_comment("Version ID = {}".format(version.result()['id']))
    """
    After attaching a first version to a spec, the current_version_id of the spec is automatically set
    """
    print_comment("Current version ID = {}".format(spec.get().result()['current_version_id']))

    print_header("Run inference on spec (using the current version)")
    """
    And this current version can be used to run inference for the spec directly
    """
    result = spec.inference(inputs=deepomatic.ImageInput(demo_url), show_discarded=True, max_predictions=3).result()

    print_header("Delete networks and recognition models")
    """
    And finally, we delete the network, which will delete the recognition version and recognition spec in cascade.
    """
    network.delete().result()


###########
# Helpers #
###########

def print_header(text):
    print("\n{}".format(text))


def print_comment(text):
    print("--> " + text)


def download(url, local_path):
    if not os.path.isfile(local_path):
        print_comment("Downloading {} to {}".format(url, local_path))
        urlretrieve(url, local_path)
    else:
        print_comment("Skipping download of {} to {}: file already exist".format(url, local_path))
    return local_path


def pretty_print_json(data):
    print(json.dumps(data, indent=4, separators=(',', ': ')))


def display_inference_tensor(result):
    for t in result['tensors']:
        print_comment("tensor '{name}', dimensions: {dims}".format(name=t['name'], dims='x'.join(map(str, t['dims']))))


if __name__ == '__main__':
    demo()
