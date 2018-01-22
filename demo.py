import os
import time
import json
from deepomatic import deepomatic

appID  = os.environ['DEEPOMATIC_APP_ID']
apiKey = os.environ['DEEPOMATIC_API_KEY']

client = deepomatic.Client(appID, apiKey)

# ---------------------------------------------------------------------------------------------------
# For the sake of reproducibility, we always wait for the tasks to complete via a check on the taskID
# ---------------------------------------------------------------------------------------------------


def detection() :

	print("--------------------------------------------------------------------------------------------")
	print("--------- detection")
	print("--------------------------------------------------------------------------------------------")

	response = client.detect("fashion", { "url": "http://static1.puretrend.com/articles/4/12/06/94/@/1392954-kim-kardashian-dans-les-rues-de-los-580x0-3.jpg" }, wait = True)

	print("Here is what we have deteted:")
	print(json.dumps(response['boxes'], indent=2, sort_keys=True))


# db_and_indexing("demo_1", "demo_2")
# indexing_in_batch("batch_indexing")
# searching("batch_indexing")
# perfect_match("perfect_match")
detection()

