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

def db_and_indexing(db_name_1, db_name_2) :

	print("--------------------------------------------------------------------------------------------")
	print("--------- DBs and indexing")
	print("--------------------------------------------------------------------------------------------")

	# Delete the dbs if they exists for reproductibily
	print("DELETE db %s if it exists." % db_name_1)
	if db_name_1 in client.getDBs()['dbs'] :
		client.deleteDB(db_name_1, wait = True)

	print("DELETE db %s if it exists." % db_name_2)
	if db_name_2 in client.getDBs()['dbs'] :
		client.deleteDB(db_name_2, wait = True)


	# POST an image into the db. An id is automatically created and returned.
	# A task id is also returned to track the completion of the task
	print("POST a new entry in %s with an auto-assigned id." % db_name_1)
	img = [{"url": "https://s3-eu-west-1.amazonaws.com/deepo-public/Demo/shoes/shoes_0.jpg"}]
	client.saveObject(db_name_1, imgs = img, wait = True)

	# PUT an image into the db with a defined id.
	# A task id is returned to track the completion of the task
	print("PUT a new entry in %s with a predefined id." % db_name_1)
	img = [{"url": "https://s3-eu-west-1.amazonaws.com/deepo-public/Demo/shoes/shoes_1.jpg"}]
	predefined_id = "shoes_1"
	client.saveObject(db_name_1, id = predefined_id, imgs = img, wait = True)

	print("POST a new entry in %s with an auto-assigned id." % db_name_2)

	bbox = deepomatic.Bbox(deepomatic.Point(0,0), deepomatic.Point(1,1))
	poly = deepomatic.Polygon()
	poly.addPoints([deepomatic.Point(0,0), deepomatic.Point(1,1), deepomatic.Point(0,1), deepomatic.Point(1,0)])
	obj = deepomatic.ImgsSend("url", "https://s3-eu-west-1.amazonaws.com/deepo-public/Demo/shoes/shoes_2.jpg", bbox = bbox.corners, polygon = poly.points)
	client.saveObject(db_name_2, imgs = obj.imgs, wait = True)

	print("DBs are %s." % ", ".join(client.getDBs()['dbs']))

	print("CLEAR db %s." % db_name_2)
	client.clearDB(db_name_2, wait = True)

	print("DBs are now %s." % ", ".join(client.getDBs()["dbs"]))

	print("DELETE db %s." % db_name_2)
	delete_task_3 = client.deleteDB(db_name_2, wait = True)

	print("DBs are now just %s." % ", ".join(client.getDBs()["dbs"]))

	print("DB %s has %s element." % (db_name_1, str(client.getCount(db_name_1)["count"])))

	print("GET object with id %s in db %s." % (predefined_id, db_name_1))
	get_result_box = client.getObject(db_name_1, predefined_id)['object']['imgs'][0]['bbox']
	print("Indexation has automatically cropped background color to {xmin: %.3f, ymin: %.3f, xmax: %.3f, ymax: %.3f}" % (get_result_box['xmin'], get_result_box['ymin'], get_result_box['xmax'], get_result_box['ymax']))

	print("DELETE object with id %s in db %s." % (predefined_id, db_name_1))
	object_delete = client.deleteObject(db_name_1, predefined_id, wait = True)

	print("DB %s has now %s element." % (db_name_1, str(client.getCount(db_name_1)["count"])))

# ---------------------------------------------------------------

def indexing_in_batch(db_name) :

	print("--------------------------------------------------------------------------------------------")
	print("--------- Indexing in batch")
	print("--------------------------------------------------------------------------------------------")

	print("DELETE db %s if it exists." % db_name)
	if db_name in client.getDBs()['dbs'] :
		client.deleteDB(db_name, wait = True)

	img = [{"url": "https://s3-eu-west-1.amazonaws.com/deepo-public/Demo/shoes/shoes_1.jpg"}]
	predefined_id = "batchTestClient"
	client.saveObject(db_name, id = predefined_id, imgs = img, wait = True)

	batch = deepomatic.BatchObject(db_name)

	print("PUT a batch of 20 images in %s with predefined ids." % db_name)
	url_base = "https://s3-eu-west-1.amazonaws.com/deepo-public/Demo/shoes/shoes_%s.jpg"
	for i in range(0,20) :
		obj = deepomatic.ImgsSend("url", url_base % i)
		batch.addObject(obj, "shoes_%d" % i)

	batch_response = client.batchRequest(batch, wait = True)


	print("DB %s has now %s element." % (db_name, str(client.getCount(db_name)['count'])))


# ---------------------------------------------------------------

def searching(db_name) :

	if not db_name in client.getDBs()["dbs"] :
		indexing_in_batch()

	print("--------------------------------------------------------------------------------------------")
	print("--------- searching")
	print("--------------------------------------------------------------------------------------------")

	img = [{"url": "https://s3-eu-west-1.amazonaws.com/deepo-public/Demo/shoes/shoes_0.jpg"}]
	client.saveObject(db_name, imgs = img, wait=True)
	image_test_url = {"url" : "https://s3-eu-west-1.amazonaws.com/deepo-public/Demo/shoes/shoes_20.jpg"}
	search_results = client.search(db_name, image_test_url, wait = True)
	print("The id of the image that is the most similar to the query is %s with a score of %.5f" % (search_results['hits'][0]['id'], search_results['hits'][0]['score']))

def perfect_match(db_name) :

	print("--------------------------------------------------------------------------------------------")
	print("--------- Perfect Match")
	print("--------------------------------------------------------------------------------------------")

	print("DELETE db %s if it exists." % db_name)
	if db_name in client.getDBs()['dbs'] :
		client.deleteDB(db_name, wait = True)

	url_base = "https://s3-eu-west-1.amazonaws.com/deepo-public/Demo/perfect_match/%s.jpg"
	poster_names = ['elle', 'jurassic_shark', 'le_chasseur', 'sos_fantome', 'the_dark_night']
	print("PUT 5 movie posters in db %s." % db_name)

	batch = deepomatic.BatchObject(db_name)
	for name in poster_names :
		obj = deepomatic.ImgsSend("url", url_base % name)
		batch.addObject(obj, name)

	batch_response = client.batchRequest(batch, wait = True)

	image_test = "https://s3-eu-west-1.amazonaws.com/deepo-public/Demo/perfect_match/query.jpg"
	search_results = client.search(db_name, {'url' : image_test}, wait = True)
	print("Did we found a perfect match: %s" % str(search_results['hits'][0]['is_perfect_match']))

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

