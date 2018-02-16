import os
from deepomatic import deepomatic

appID = os.environ['DEEPOMATIC_APP_ID']
apiKey = os.environ['DEEPOMATIC_API_KEY']


client = deepomatic.Client(appID, apiKey)


def example_add_network():
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

    deploy_path = os.path.join(home_dir, "network/deploy.prototxt")
    weights_path = os.path.join(home_dir, "network/snapshot.caffemodel")
    mean_path = os.path.join(home_dir, "network/mean.binaryproto")

    with open(deploy_path) as graph, open(weights_path, "rb") as weights, open(mean_path, "rb") as mean:
        r = client.add_network("test_network", "test1", preprocessing, graph, weights, extra_files={"mean.proto.bin": mean}, wait=True)
        return r


def example_edit_network(network_id):
    return client.edit_network(network_id, "test2", "test2", {})


def example_infere_network_from_source(network_id):
    r = client.infere_network_from_source(network_id, ["output"], "http://static1.puretrend.com/articles/4/12/06/94/@/1392954-kim-kardashian-dans-les-rues-de-los-580x0-3.jpg", wait=True)
    return r


def example_infere_network(network_id):
    r = client.infere_network(network_id, ["output"], [
        {"image": {"source": "http://static1.puretrend.com/articles/4/12/06/94/@/1392954-kim-kardashian-dans-les-rues-de-los-580x0-3.jpg"}},
        {"image": {"source": "http://cdn-img.instyle.com/sites/default/files/styles/684xflex/public/images/2017/11/112817-kim-kardashian-photo-shoot-lead.jpg?itok=5g1AiPP3.jpg"}}
    ], wait=True)
    return r


def example_add_recognition_spec_detect():
    r = client.add_recognition_spec("detect", "my fashion detector", [{
        "roi": "BBOX",
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
        }]
    }])
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


def example_edit_recognition_spec(spec_id, version_id):
    r = client.edit_recognition_spec(spec_id, "test", "test", {}, version_id)
    return r


def example_infere_recognition_spec_from_source(spec_id):
    r = client.infere_recognition_spec_from_source(spec_id, "https://www.what-dog.net/Images/faces2/scroll0015.jpg")
    return r


def example_infere_recognition_version_from_source(version_id):
    r = client.infere_recognition_version_from_source(version_id, "https://www.what-dog.net/Images/faces2/scroll0015.jpg")
    return r


def example_add_recognition_version_detect(spec_id, network_id):
    post_processings = [{
        "detection": {
            "faster_rcnn_tensors": {
                "bbox_anchors": "rois",
                "bbox_offsets": "bbox_pred",
                "class_probs": "cls_prob"
            },
            "thresholds": [0.611, 0.810, 0.595, 0.907, 0.678, 0.689, 0.535, 0.504, 0.658, 0.347, 0.779, 0.647, 0.771, 0.320, 0.323],
            "nms_threshold": 0.5
        }
    }]
    r = client.add_recognition_version(spec_id, network_id, post_processings)
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


if __name__ == "__main__":

    #####################
    # Handling networks #
    #####################

    print "Listing networks"
    print client.list_networks()

    print "Adding network"
    network = example_add_network()

    print "Editing network"
    example_edit_network(network["id"])

    print "Getting network"
    print client.get_network(network["id"])

    print "Infering an image on network"
    example_infere_network_from_source(network["id"])

    #########################
    # Handling recognitions #
    #########################

    print "Listing specs"
    print client.list_recognition_specs()

    print "Adding a classification spec"
    spec = example_add_recognition_spec_classif()

    print "Get a spec"
    print client.get_recognition_spec(spec["id"])

    print "Adding a classification version"
    first_version = example_add_recognition_version_classif(spec["id"], network["id"])

    print "Getting a version"
    print client.get_recognition_version(first_version["id"])

    print "Adding another classification version"
    second_version = example_add_recognition_version_classif(spec["id"], network["id"])

    print "Listing all versions"
    print client.list_recognition_versions()

    print "Listing versions of a spec"
    print client.list_recognition_spec_versions(spec["id"])

    print "Changing the current version of the recognition"
    example_edit_recognition_spec(spec["id"], second_version["id"])

    print "Infering with the current version"
    example_infere_recognition_spec_from_source(spec["id"])

    print "Infering with a specific version"
    example_infere_recognition_version_from_source(first_version["id"])

    print "Deleting first version"
    client.delete_recognition_version(first_version["id"])

    print "Deleting spec"
    client.delete_recognition_spec(spec["id"])

    ###########################

    print "Deleting the network we depend on"
    client.delete_network(network["id"])
