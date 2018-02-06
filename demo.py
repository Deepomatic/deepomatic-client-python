import os
from deepomatic import deepomatic

appID = os.environ['DEEPOMATIC_APP_ID']
apiKey = os.environ['DEEPOMATIC_API_KEY']


client = deepomatic.Client(appID, apiKey)


# Example of ids
NETWORK_ID = 111
RECOGNITION_SPEC_ID = 222
RECOGNITION_VERSION_ID = 333
RECOGNITION_VERSION_ID_2 = 444


def example_list_networks():
    r = client.list_networks()
    print r


def example_delete_network():
    r = client.delete_network(NETWORK_ID)
    print r


def example_edit_network():
    r = client.edit_network(NETWORK_ID, "test1", "test1", {})
    print r


def example_get_network():
    r = client.get_network(NETWORK_ID)
    print r


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

    with open("~/network/deploy.prototxt") as graph, open("~/network/snapshot.caffemodel","rb") as weights, open("~/network/mean.binaryproto","rb") as mean:
        r = client.add_network("test_network", "test1", preprocessing, graph, weights, extra_files={"mean.proto.bin": mean})
        print r

def example_infere_network_from_source():
    r = client.infere_network_from_source(NETWORK_ID, ["prob"], "http://static1.puretrend.com/articles/4/12/06/94/@/1392954-kim-kardashian-dans-les-rues-de-los-580x0-3.jpg", wait=True)
    print r

def example_infere_network():
    r = client.infere_network(NETWORK_ID, ["prob"], [
        {"image": {"source": "http://static1.puretrend.com/articles/4/12/06/94/@/1392954-kim-kardashian-dans-les-rues-de-los-580x0-3.jpg"}},
        {"image": {"source": "http://cdn-img.instyle.com/sites/default/files/styles/684xflex/public/images/2017/11/112817-kim-kardashian-photo-shoot-lead.jpg?itok=5g1AiPP3.jpg"}}
    ], wait=True)
    print r

#----------------------------------------------------------

def example_list_recognition_specs():
    r = client.list_recognition_specs()
    print r


def example_get_recognition_spec():
    r = client.get_recognition_spec(RECOGNITION_SPEC_ID)
    print r


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
    print r


def example_add_recognition_spec_classif():
    r = client.add_recognition_spec("classif", "my classifier", [{"roi": "NONE", "labels": [{"id": 0, "name": "tench Tinca tinca"},{"id": 1, "name": "goldfish Carassius auratus"}]}])
    print r


def example_delete_recognition_spec():
    r = client.delete_recognition_spec(RECOGNITION_SPEC_ID)
    print r


def example_edit_recognition_spec():
    r = client.edit_recognition_spec(RECOGNITION_SPEC_ID, "test", "test", {}, RECOGNITION_VERSION_ID)
    print r


def example_infere_recognition_spec():
    r = client.infere_recognition_spec(RECOGNITION_SPEC_ID, "https://www.what-dog.net/Images/faces2/scroll0015.jpg")
    print r


def example_list_recognition_versions():
    r = client.list_recognition_versions()
    print r


def example_get_recognition_version():
    r = client.get_recognition_version(RECOGNITION_VERSION_ID)
    print r


def example_add_recognition_version():
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
    r = client.add_recognition_version(RECOGNITION_SPEC_ID, NETWORK_ID, post_processings)
    print r


def example_delete_recognition_version():
    r = client.delete_recognition_version(RECOGNITION_VERSION_ID)
    print r
