import os
import sys
import json

import deepomatic

app_id = os.environ['DEEPOMATIC_APP_ID']
api_key = os.environ['DEEPOMATIC_API_KEY']
client = deepomatic.Client(app_id, api_key)

###########
# Helpers #
###########

if sys.version_info >= (3, 0):
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve


def download(url, local_path):
    if not os.path.isfile(local_path):
        print("Downloading {} to {}".format(url, local_path))
        urlretrieve(url, local_path)
    else:
        print("Skipping download of {} to {}: file already exist".format(url, local_path))
    return local_path


def pretty_print_json(data):
    print(json.dumps(data, indent=4, separators=(',', ': ')))


################################################
# Example functions specific to classification #
################################################


def example_infere_network_from_source_classif(network_id):
    r = client.infere_network_from_source(network_id, ["output"], "http://cache.marieclaire.fr/data/photo/w700_c17/15y/kim-kardashian.jpg", wait=True)
    return r


def example_add_network_classif():
    preprocessing = {
        "inputs": [{
            "tensor_name": "data",
            "image": {
                "dimension_order": "NCHW",
                "target_size": "224x224",
                "resize_type": "SQUASH",
                "mean_file": "mean.proto.bin",
                "color_channels": "BGR"
            }
        }],
        "batched_output": True
    }

    home_dir = os.path.expanduser("~/")

    deploy_path = os.path.join(home_dir, "network_classification/deploy.prototxt")
    weights_path = os.path.join(home_dir, "network_classification/snapshot.caffemodel")
    mean_path = os.path.join(home_dir, "network_classification/mean.binaryproto")

    with open(deploy_path) as graph, open(weights_path, "rb") as weights, open(mean_path, "rb") as mean:
        r = client.add_network("test_network_classif", "test1", preprocessing, graph, weights, extra_files={"mean.proto.bin": mean}, wait=True)
        return r


def example_add_recognition_spec_classif():
    r = client.add_recognition_spec("classif", "my classifier", [{
        "roi": "NONE",
        "labels": {
            "labels": [{
                "id": 0,
                "name": "good"
            }, {
                "id": 1,
                "name": "bad"
            }],
            "exclusive": True
        }
    }])
    return r


def example_add_recognition_version_classif(spec_id, network_id):
    post_processings = [{
        "classification": {
            "output_tensor": "output",
            "thresholds": [0.2, 0.5]
        }
    }]
    r = client.add_recognition_version(spec_id, network_id, post_processings)
    return r


###########################################
# Example functions specific to detection #
###########################################


def example_infere_network_from_source_detect(network_id):
    r = client.infere_network_from_source(network_id,
                                          ["cls_prob"],
                                          "http://cache.marieclaire.fr/data/photo/w700_c17/15y/kim-kardashian.jpg",
                                          wait=True)
    return r


def example_add_network_detect():
    preprocessing = {
        "inputs": [{
            "tensor_name": "data",
            "image": {
                "mean_file": "mean.proto.bin",
                "color_channels": "BGR",
                "dimension_order": "NCHW",
                "resize_type": "NETWORK",
                "target_size": "600"
            }
        }, {
            "tensor_name": "im_info",
            "constant": {
                "shape": [3],
                "data": ["data.1", "data.2", 1.0]
            }
        }],
        "batched_output": False
    }

    home_dir = os.path.expanduser("~/")

    deploy_path = os.path.join(home_dir, "network_detection/deploy.prototxt")
    weights_path = os.path.join(home_dir, "network_detection/snapshot.caffemodel")
    mean_path = os.path.join(home_dir, "network_detection/mean.binaryproto")

    with open(deploy_path) as graph, open(weights_path, "rb") as weights, open(mean_path, "rb") as mean:
        r = client.add_network("test_network_detect", "test1", preprocessing, graph, weights, extra_files={"mean.proto.bin": mean}, wait=True)
        return r


def example_add_recognition_spec_detect():
    r = client.add_recognition_spec("detect", "my fashion detector", [{
        "roi": "BBOX",
        "labels": {
            "labels": [{
                "id": 0,
                "name": "sweater"
            }, {
                "id": 1,
                "name": "hat"
            }, {
                "id": 2,
                "name": "dress"
            }, {
                "id": 3,
                "name": "bag"
            }, {
                "id": 4,
                "name": "jacket-coat"
            }, {
                "id": 5,
                "name": "shoe"
            }, {
                "id": 6,
                "name": "pants"
            }, {
                "id": 7,
                "name": "suit"
            }, {
                "id": 8,
                "name": "skirt"
            }, {
                "id": 9,
                "name": "sunglasses"
            }, {
                "id": 10,
                "name": "romper"
            }, {
                "id": 11,
                "name": "top-shirt"
            }, {
                "id": 12,
                "name": "jumpsuit"
            }, {
                "id": 13,
                "name": "shorts"
            }, {
                "id": 14,
                "name": "swimwear"
            }],
            "exclusive": True
        }
    }])
    return r


def example_add_recognition_version_detect(spec_id, network_id):
    post_processings = [{
        "detection": {
            "faster_rcnn_tensors": {
                "bbox_anchors": "rois",
                "bbox_offsets": "bbox_pred",
                "class_probs": "cls_prob"
            },
            "thresholds": [0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6],
            "nms_threshold": 0.5
        }
    }]
    r = client.add_recognition_version(spec_id, network_id, post_processings)
    return r


###################################
# Demo function (test everything) #
###################################


def demo(add_network_func,
         infere_network_from_source_func,
         add_recognition_spec_func,
         add_recognition_version_func):

    #####################
    # Handling networks #
    #####################

    print("Adding network")
    # network_id = add_network_func()["id"]

    # print("Editing network")
    # network = client.network(network_id).edit(name="test2", description="test2", metadata={}).result()

    #########################
    # Handling recognitions #
    #########################

    # print("Listing specs")
    # print(client.list_recognition_specs())

    # print("Adding a spec")
    # spec = add_recognition_spec_func()

    # print("Getting a spec")
    # print(client.get_recognition_spec(spec["id"]))

    # print("Adding a version")
    # first_version = add_recognition_version_func(spec["id"], network["id"])

    # print("Getting a version")
    # print(client.get_recognition_version(first_version["id"]))

    # print("Adding another version")
    # second_version = add_recognition_version_func(spec["id"], network["id"])

    # print("Listing all versions")
    # print(client.list_recognition_versions())

    # print("Listing versions of a spec")
    # print(client.list_recognition_spec_versions(spec["id"]))

    # print("Changing the current version of the recognition")
    # client.recognition_model(spec["id"]).edit(name="test", description="test", metadata={}, current_version_id=second_version).result()

    # print("Infering with the current version")
    # client.recognition_model(spec["id"]).infere(input_image)

    # print("Infering with a specific version")
    # client.recognition_version(first_version["id"]).infere(input_image)

    # print("Deleting first version")
    # client.delete_recognition_version(first_version["id"])

    # print("Deleting spec")
    # client.delete_recognition_spec(spec["id"])

    # ###########################

    # print("Deleting the network we depend on")
    # client.delete_network(network["id"])



#################################
# Manipulation public resources #
#################################

# ###################
# # Public networks #
# ###################

# print("Listing public networks")
# for network in client.public_networks().list():
#     print("- {network_id}: {name}".format(network_id=network['id'], name=network['name']))

# network = client.network('imagenet-inception-v1')

# print("Getting network:")
# pretty_print_json(network.get().result())

# print("Infering an image on network:")
# input_image = deepomatic.ImageInput("https://static.deepomatic.com/resources/demos/api-clients/dog1.jpg")
# result = network.inference(input_image, ["prob", "pool2/3x3_s2", "pool5/7x7_s1"]).result()
# for t in result['tensors']:
#     print("- tensor '{name}', dimensions: {dims}".format(name=t['name'], dims='x'.join(map(str, t['dims']))))

# #############################
# # Public recognition models #
# #############################

# print("Listing public recognition models")
# for spec in client.public_recognition_specs().list():
#     print("- {spec_id}: {name}".format(spec_id=spec['id'], name=spec['name']))

# spec = client.recognition_spec('imagenet-inception-v1')

# print("Getting spec:")
# pretty_print_json(spec.get().result())

# print("Infering an image on recognition spec current version:")
# result = spec.inference(input_image, show_discarded=True, max_predictions=3).result()
# pretty_print_json(result)

#################
# Custom models #
#################

# Download tradionnal Caffe GoogLeNet model
deploy_prototxt = download('https://raw.githubusercontent.com/BVLC/caffe/master/models/bvlc_googlenet/deploy.prototxt', '/tmp/deploy.prototxt')
snapshot_caffemodel = download('http://dl.caffe.berkeleyvision.org/bvlc_googlenet.caffemodel', '/tmp/snapshot.caffemodel')
preprocessing = client.network('imagenet-inception-v1').get().result()['preprocessing']

print("Adding a network (it may take some time to upload)...")
files = {
    'deploy.prototxt': deploy_prototxt,
    'snapshot.caffemodel': snapshot_caffemodel,
}
network = client.networks().add(name="My first network",
                                framework='nv-caffe-0.x-mod',
                                preprocessing=preprocessing,
                                files=files)

print()


labels = client.recognition_spec('imagenet-inception-v1').get().result()['outputs']


# print("Demo for classification")
# demo(example_add_network_classif,
#      example_infere_network_from_source_classif,
#      example_add_recognition_spec_classif,
#      example_add_recognition_version_classif)

# print("-----------------------")

# print("Demo for detection")
# demo(example_add_network_detect,
#      example_infere_network_from_source_detect,
#      example_add_recognition_spec_detect,
#      example_add_recognition_version_detect)
