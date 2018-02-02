import os
import time
import json
from deepomatic import deepomatic

appID  = os.environ['DEEPOMATIC_APP_ID']
apiKey = os.environ['DEEPOMATIC_API_KEY']


client = deepomatic.Client(appID, apiKey, host = "https://api-staging.deepomatic.com")


# ---------------------------------------------------------------------------------------------------
# For the sake of reproducibility, we always wait for the tasks to complete via a check on the taskID
# ---------------------------------------------------------------------------------------------------

def example_list_network():
    r = client.list_networks()
    print(json.dumps(r))

def example_delete_network():
    r = client.delete_network(12132)
    print(json.dumps(r))

def example_edit_network():
    r = client.edit_network(network_id, inputs, output_layers)
    print(json.dumps(r))

def example_get_network():
    r = client.get_network(128)
    print(json.dumps(r))

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

    with open("/home/chloe/network/deploy.prototxt") as graph, open("/home/chloe/network/snapshot.caffemodel","rb") as weights, open("/home/chloe/network/mean.binaryproto","rb") as mean:
        r = client.add_network("test_network", "test1", preprocessing, graph, weights, extra_files={"mean.proto.bin": mean})
    print(json.dumps(r))

def example_infere_network_from_source():
    r = client.infere_network_from_source(128, ["prob"], "http://static1.puretrend.com/articles/4/12/06/94/@/1392954-kim-kardashian-dans-les-rues-de-los-580x0-3.jpg", wait=True)
    print(json.dumps(r))

def example_infere_network():
    r = client.infere_network(128, ["prob"], [{"image": {"source": "http://static1.puretrend.com/articles/4/12/06/94/@/1392954-kim-kardashian-dans-les-rues-de-los-580x0-3.jpg"}}, 
        {"image": {"source": "http://cdn-img.instyle.com/sites/default/files/styles/684xflex/public/images/2017/11/112817-kim-kardashian-photo-shoot-lead.jpg?itok=5g1AiPP3.jpg"}}], wait=True)
    print(json.dumps(r))

#----------------------------------------------------------

def example_list_recognition_specs():
    r = client.list_recognition_specs()
    print(json.dumps(r))

def example_get_recognition_spec():
    r = client.get_recognition_spec(4594)
    print(json.dumps(r))

def example_add_recognition_spec():
    r = client.add_recognition_spec("detect", "", [
        {
            "roi": "BBOX",
            "labels": [{
                "id": 0,
                "name": "sweater"
            },{
                "id": 1,
                "name": "hat"
            },{
                "id": 2,
                "name": "dress"
            },{
                "id": 3,
                "name": "bag"
            },{
                "id": 4,
                "name": "jacket-coat"
            },{
                "id": 5,
                "name": "shoe"
            },{
                "id": 6,
                "name": "pants"
            },{
                "id": 7,
                "name": "suit"
            },{
                "id": 8,
                "name": "skirt"
            },{
                "id": 9,
                "name": "sunglasses"
            },{
                "id": 10,
                "name": "romper"
            },{
                "id": 11,
                "name": "top-shirt"
            },{
                "id": 12,
                "name": "jumpsuit"
            },{
                "id": 13,
                "name": "shorts"
            },{
                "id": 14,
                "name": "swimwear"
            }
        ]
        }
    ]
)
    print(json.dumps(r))

def example_delete_recognition_spec():
    r = client.delete_recognition_spec(4473)
    print(json.dumps(r))

def example_edit_recognition_spec():
    r = client.edit_recognition_spec(4473, "test")
    print(json.dumps(r))

#----------------------------------------------------------

def example_list_versions():
    r = client.list_versions()
    print(json.dumps(r))

def example_get_version():
    r = client.get_version(4753)
    print(json.dumps(r))

def example_add_version():
    post_processings = [{
    "detection": {
      "faster_rcnn_tensors": {
        "bbox_anchors": "rois",
        "bbox_offsets": "bbox_pred",
        "class_probs":  "cls_prob"
      },
      "thresholds": [0.611, 0.810, 0.595, 0.907, 0.678, 0.689, 0.535, 0.504, 0.658, 0.347, 0.779, 0.647, 0.771, 0.320, 0.323],
      "nms_threshold": 0.5
    }
  }]
    r = client.add_version(4594, 52, post_processings)
    print(json.dumps(r))

def example_delete_version():
    r = client.delete_version(4753)
    print(json.dumps(r))

def example_change_current_version():
    r = client.change_current_version(4594, 4753)
    print(json.dumps(r))
