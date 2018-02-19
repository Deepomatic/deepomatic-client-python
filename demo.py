import os
from deepomatic import deepomatic

appID = os.environ['DEEPOMATIC_APP_ID']
apiKey = os.environ['DEEPOMATIC_API_KEY']


client = deepomatic.Client(appID, apiKey)


#############################################################
# Example functions (doesn't depend on the type of network) #
#############################################################


def example_edit_network(network_id):
    return client.edit_network(network_id, "test2", "test2", {})


def example_edit_recognition_spec(spec_id, version_id):
    r = client.edit_recognition_spec(spec_id, "test", "test", {}, version_id)
    return r


def example_infere_recognition_spec_from_source(spec_id):
    r = client.infere_recognition_spec_from_source(spec_id, "https://www.what-dog.net/Images/faces2/scroll0015.jpg")
    return r


def example_infere_recognition_version_from_source(version_id):
    r = client.infere_recognition_version_from_source(version_id, "https://www.what-dog.net/Images/faces2/scroll0015.jpg")
    return r


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

    print ("Listing networks")
    print (client.list_networks())

    print ("Adding network")
    network = add_network_func()

    print ("Editing network")
    example_edit_network(network["id"])

    print ("Getting network")
    print (client.get_network(network["id"]))

    print ("Infering an image on network")
    infere_network_from_source_func(network["id"])

    #########################
    # Handling recognitions #
    #########################

    print ("Listing specs")
    print (client.list_recognition_specs())

    print ("Adding a spec")
    spec = add_recognition_spec_func()

    print ("Getting a spec")
    print (client.get_recognition_spec(spec["id"]))

    print ("Adding a version")
    first_version = add_recognition_version_func(spec["id"], network["id"])

    print ("Getting a version")
    print (client.get_recognition_version(first_version["id"]))

    print ("Adding another version")
    second_version = add_recognition_version_func(spec["id"], network["id"])

    print ("Listing all versions")
    print (client.list_recognition_versions())

    print ("Listing versions of a spec")
    print (client.list_recognition_spec_versions(spec["id"]))

    print ("Changing the current version of the recognition")
    example_edit_recognition_spec(spec["id"], second_version["id"])

    print ("Infering with the current version")
    example_infere_recognition_spec_from_source(spec["id"])

    print ("Infering with a specific version")
    example_infere_recognition_version_from_source(first_version["id"])

    print ("Deleting first version")
    client.delete_recognition_version(first_version["id"])

    print ("Deleting spec")
    client.delete_recognition_spec(spec["id"])

    ###########################

    print ("Deleting the network we depend on")
    client.delete_network(network["id"])


if __name__ == "__main__":
    print ("Demo for classification")
    demo(example_add_network_classif,
         example_infere_network_from_source_classif,
         example_add_recognition_spec_classif,
         example_add_recognition_version_classif)

    print ("-----------------------")

    print ("Demo for detection")
    demo(example_add_network_detect,
         example_infere_network_from_source_detect,
         example_add_recognition_spec_detect,
         example_add_recognition_version_detect)
