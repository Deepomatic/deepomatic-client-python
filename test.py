# export DEEPOMATIC_API_KEY="7a90cd34c66548c99503a5e4ed6e9786"

###

import sys
sys.path.append('/home/kent/deepo/deepomatic-client-python')

# essayer dmake shell client

###

from deepomatic.api.http_helper import HTTPHelper
http_helper = HTTPHelper()
http_helper.dump_json_for_multipart({})
http_helper.dump_json_for_multipart({'level_0': {'level_1': {'level_2': "niveau 2"}, 'level_1_bis': {'level_a': 'nouvelle orleans'}}, 'level_0_bis': 'niveau 0'})
# => returns {'level_0.level_1.level_2': 'niveau 2', 'level_0_bis': 'niveau 0'}

http_helper.dump_json_for_multipart({'level_0': [{'bbox': {'xmin': 0.1, 'xmax': 0.9, 'ymin': 0.3}}], 'level_0_bis': 'niveau 0'})
http_helper.dump_json_for_multipart_new({'level_0': [{'image': {'bbox': "{'xmin': 0.1, 'xmax': 0.9, 'ymin': 0.3}"}}], 'level_0_bis': 'niveau 0'})

from deepomatic.api.http_helper import HTTPHelper
http_helper = HTTPHelper()
http_helper.dump_json_for_multipart_new({'level_0': [{'image': {'bbox': {'xmin': 0.1, 'xmax': 0.9, 'ymin': 0.3}}}], 'level_0_bis': 'niveau 0'})




########

import json
import requests
from io import BytesIO
from deepomatic.api.inputs import ImageInput
from deepomatic.api.client import Client

# client = Client()
# client.RecognitionVersion.list()

# staging
app_id = '396170490728'
api_key = 'a9b3d24b8a68401f8f4bf582d7dd12e8'
host = 'https://api-staging.deepomatic.com'

client = Client(app_id, api_key, host=host)
version = client.RecognitionVersion.retrieve("40771")
# version = client.RecognitionVersion.create(network_id="47299", spec_id=49832, post_processings=[{'detection': {'direct_output': {'boxes_tensor': 'detection_boxes:0', 'scores_tensor': 'detection_scores:0', 'classes_tensor': 'detection_classes:0'}, 'thresholds': [0.0, 0.0, 0.0], 'nms_threshold': 0.3, 'discard_threshold': 0.0, 'normalize_wrt_tensor': ''}}])

bbox = {'xmin': 0.1, 'xmax': 0.9, 'ymin': 0.3, 'ymax': 0.5}

url = "https://www.illicoveto.com/wp-content/uploads/berger-australien-768x988.jpg"

response = requests.get(url)
img_data = BytesIO(response.content)

img = {
    'encoding': 'binary',
    'bbox': json.dumps(bbox),
    'source': img_data
}
data_input = ImageInput(**img)

version.inference(inputs=[data_input])
