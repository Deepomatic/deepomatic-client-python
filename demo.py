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
client = deepomatic.Client(app_id, api_key, host='https://api-staging.deepomatic.com')


def demo():
    #################################
    # Manipulation public resources #
    #################################

    url = "https://static.deepomatic.com/resources/demos/api-clients/dog1.jpg"

    ###################
    # Public networks #
    ###################

    print_header("Listing public networks")
    """
    You can access the list of public networks with: 'client.public_networks().list()'
    'public_networks()' returns a resource set that usually have two methods: '.list()' and '.add()'.
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
    Here, it take an url as input via 'deepomatic.ImageInput(url)'.
    Also we have used the generic form of inference which might take multiple inputs if your networks has multiple ones.
    """
    result = network.inference(inputs=[deepomatic.ImageInput(url)], output_tensors=["prob", "pool2/3x3_s2", "pool5/7x7_s1"]).result()
    display_inference_tensor(result)

    print_header("Inference from a file")
    """
    '.inference()' also support when you pass a single input instead of a list of inputs.
    Here, it takes a file pointer as input.
    """
    file = open(download(url, '/tmp/img.jpg'), 'rb')
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
    A network by itself is not very usefull. It's more interesting when it's tied
    """
    for spec in client.public_recognition_specs().list():
        print_comment("- {spec_id}: {name}".format(spec_id=spec['id'], name=spec['name']))

    spec = client.recognition_spec('imagenet-inception-v1')

    print_header("Getting spec")
    pretty_print_json(spec.get().result())

    print_header("Infering an image on recognition spec current version")
    result = spec.inference(inputs=deepomatic.ImageInput(url), show_discarded=True, max_predictions=3).result()
    pretty_print_json(result)

    ###################
    # Custom networks #
    ###################

    # Download tradionnal Caffe GoogLeNet model
    deploy_prototxt = download('https://raw.githubusercontent.com/BVLC/caffe/master/models/bvlc_googlenet/deploy.prototxt', '/tmp/deploy.prototxt')
    snapshot_caffemodel = download('http://dl.caffe.berkeleyvision.org/bvlc_googlenet.caffemodel', '/tmp/snapshot.caffemodel')
    if not os.path.exists('/tmp/mean.binaryproto'):
        archive = download('http://dl.caffe.berkeleyvision.org/caffe_ilsvrc12.tar.gz', '/tmp/caffe_ilsvrc12.tar.gz')
        tar = tarfile.open(archive, "r:")
        tar.extractall()
        tar.close()

    preprocessing = client.network('imagenet-inception-v1').get().result()['preprocessing']

    print_header("Adding a network (it may take some time to upload)...")
    files = {
        'deploy.prototxt': deploy_prototxt,
        'snapshot.caffemodel': snapshot_caffemodel,
    }
    network = client.networks().add(name="My first network",
                                    framework='nv-caffe-0.x-mod',
                                    preprocessing=preprocessing,
                                    files=files)
    network_id = network.get().result()['id']
    print_comment("Network ID = {}".format(network_id))

    print_header("Wait for network deployment")
    # We wait until the network is deployed and ready
    client.task(network.get().result()['task_id']).wait().result()

    print_header("Editing network")
    descr = network.get().result()['description']
    print_comment("Decription before (empty): '{}'".format(descr))
    descr = network.edit(description="I forgot the description").result()['description']
    print_comment("Decription after: '{}'".format(descr))

    #############################
    # Custom recognition models #
    #############################

    print_header("Adding a recognition model")
    outputs = client.recognition_spec('imagenet-inception-v1').get().result()['outputs']
    spec = client.recognition_specs().add(name="My recognition model", outputs=outputs)

    print_header("Getting the spec result")
    # When you use add(), its result behave at the same time:
    # - as a result: you can call 'spec.resut()'
    # - as a resource: you can call 'spec.get().resut()' and it gives the same result
    spec_id = spec.result()['id']
    print_comment("Spec ID = {}".format(spec_id))

    print_header("Adding a version on a spec")
    # The post_processings depends on what you want to do and must match the number of 'outputs'
    # specified when creating the 'spec'. Here, it is a classification network so we create a
    # 'classification' post-processing.
    version = client.recognition_versions().add(network_id=network_id, spec_id=spec_id, post_processings=[
        {
            "classification": {
                "output_tensor": "prob",
            }
        }
    ])
    print_comment("Version ID = {}".format(version.result()['id']))
    # After attaching a first version to a spec, the current_version_id of the spec is automatically set
    print_comment("Current version ID = {}".format(spec.get().result()['current_version_id']))

    print_header("Run inference on spec (using the current version)")
    # And this current version can be used to run inference for the spec directly
    result = spec.inference(inputs=deepomatic.ImageInput(url), show_discarded=True, max_predictions=3).result()

    print_header("Delete networks and recognition models")
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
