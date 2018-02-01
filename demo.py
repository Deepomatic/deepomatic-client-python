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
'''
def detection() :

	print("--------------------------------------------------------------------------------------------")
	print("--------- detection")
	print("--------------------------------------------------------------------------------------------")

	response = client.detect("fashion", { "url": "http://static1.puretrend.com/articles/4/12/06/94/@/1392954-kim-kardashian-dans-les-rues-de-los-580x0-3.jpg" }, wait=True)

	print("Here is what we have deteted:")
	print(json.dumps(response['boxes'], indent=2, sort_keys=True))

detection()
'''


def list():
	r = client.list_networks()
	print(json.dumps(r))

def delete():
	r = client.delete_network("12132")
	print(json.dumps(r))

def edit():
	r = client.edit_network(network_id, inputs, output_layers)
	print(json.dumps(r))

def get():
	r = client.get_network(128)
	print(json.dumps(r))

def add():
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

def infere():
    r = client.infere_network(128, ["prob"], "http://static1.puretrend.com/articles/4/12/06/94/@/1392954-kim-kardashian-dans-les-rues-de-los-580x0-3.jpg", wait=True)
    print(json.dumps(r))


infere()
#lister()
#afficher()
#ajouter()
#modifier()
