# deepomatic-client-python

Deepomatic API Client for Python.

This client have been made in order to help you integrating our services within your apps in python.

A demo code can be run in demo.py. It will explain you how to :
- Play with dbs.
- Make batched queries.
- Searching based on similarity into your dbs.
- Find a perfect match.
- Use our fashion detection API.
<br/>

# API Documentation

https://api.deepomatic.com/
<br/>

# Requirements

```
sudo pip install -r requirements.txt
```
<br/>

# Client

Initialize a client.
Does not make any call to the server.
```python
# You should find your appID and apiKey in your account on developpers.deepomatic.com
client = deepomatic.Client(appID, apiKey)
```
## Tasks

Since most of server calls need some processing time, you will often receive a Task (json dictionary).
Task are very simple to use.

Fields:
* id
* data
* status
* error
* date_created
* date_updated

When the task ```"status"``` is equal to ```"succes"``` you can find the request result in the ```"data"``` field.


## Models
### Point

```python
    pt = deepomatic.Point(0,0)
```

### Polygons
You can create a polygon with the Polygon class :

```python
    poly = deepomatic.Polygon()
```

To add points to the polygon, just use the addPoint method :

```python
    poly.addPoint(deepomatic.Point(1,2))
```

If you want to add multiple points at once, just use the addPoints methode:
```python
    poly.addPoints([deepomatic.Point(1,2), deepomatic.Point(2,2), deepomatic.Point(1,1)])
```

For a polygon to be valid, it must have at least 3 points.

### Bbox
The bbox class takes 2 points, min and max.

```python
    bbox = deepomatic.Bbox(deepomatic.Point(1,2), deepomatic.Point(2,3))
```

### Images
The class ImageSend, allows you to crate an image with multiple fields :

```python
    imgs = deepomatic.ImageSend(sourceType, source, polygon = None, bbox = None)
```
You can add images by using the addObject method with the same parameters:
```python
    imgs.addObject(sourceType, source, polygon = None, bbox = None)
```
You can use ```url```, ```base64``` or ```file``` for the sourceType.


### Batch
You can send multiple request type on a batch : PUT, POST, GET, DELETE.
```python
batch = deepomatic.BatchObject(dbname)
batch.deleteObject(id)
batch.getObject(id)
batch.addObject(imgs, id = None)
```
To send the batch to the API, just use the client batchRequest() methode :

```python
client.batchRequest(batch, true)
```

## Database commands

The database is created when the first object is indexed

### List all databases

```python
response = client.getDBs()
```

### Add an object

## With url
```python
imgs = deepomatic.ImageSend("url", "my_url", polygon = None, bbox = None)
data = { "myData": "beautiful shoes" }
id = "myID"
# if id is not specified the server will generate an id returned it in the response
# if the id already exists on the server side, it will be overwritten
response = client.saveObject("db_name", imgs, data = data, id = id)
```

## With file
```python
imgs = deepomatic.ImageSend("file", "my_file.jpg", polygon = None, bbox = None)
data = { "myData": "beautiful shoes" }
id = "myID"
# if id is not specified the server will generate an id returned it in the response
# if the id already exists on the server side, it will be overwritten
response = client.saveObject("db_name", imgs, data = data, id = id)
```

### Get an object

```python
response = client.getObject("db_name", "myObjectID")
```

### Delete an object

```python
# if wait = True it will wait until the task is completed
response = client.deleteObject("db_name", "myObjectID", wait = True)
```

### Clear a database (delete all objects)

```python
# if wait = True it will wait until the task is completed else, it will return the task id
response = client.clearDB("db_name", wait = True)
```

### Delete a database (delete the db and all the objects)

```python
# if wait = True it will wait until the task is completed
response = client.deleteDB("db_name", wait = True)
```

### Search in a database
# Perform a visual Search

```python
# if wait = True it will wait until the task is completed else it will return the task id
img_url = {"url" : "url_img"}
response = client.search("db_name", img_url)

# you can also use file upload
img_file = {"file" : "path_to_file"}
response = client.search("db_name", img_file)
```
You can use ```url```, ```base64``` or ```file``` as source.

### Count number of objects in a database

```python
img = "url_img"
response = client.getCount("db_name")
```

### Batch operations

```python
requests = deepomatic.BatchObject(dbname)
url_base = "http://example.com/image_%d.jpg"
for i in range(10):
    # refer to https://api.deepomatic.com for the content of the requests
    imgs = deepomatic.ImageSend(url, url_base % i)
    requests.addObject(imgs, name)
# if wait = True it will wait until the task is completed
response = client.batchRequest(requests, wait = True)
```

### Fashion detection

```python
# if wait = True it will wait until the task is completed else it will send you back a task id
response = client.detect("fashion", "img_url", wait = True)
```

### Retrieve the task status

```python
task = client.retrieveTask(task_id)
```

# Bugs

### support@deepomatic.com
