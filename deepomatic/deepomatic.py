# -*- coding: utf-8 -*-
"""
Copyright (c) 2014 Deepomatic SAS
http://www.deepomatic.com/

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import requests
import json
import base64
import urllib

###############################################################################

API_VERSION = 0.6
API_HOST = 'https://api.deepomatic.com'

###############################################################################

class Point(object):
    def __init__(self, x, y):
        self.point = {'x' : x, 'y' : y}
    def __getitem__(self):
        return self.point

class Polygon(object):
    def __init__(self):
        self.points = []

    def addPoint(self, point):
        self.points.append(point.point)

    def addPoints(self, points):
        for pt in points:
            self.points.append(pt.point)

    def __getitem__(self):
        return self.points


class Bbox(object):
    def __init__(self, min, max):
        self.corners = {'xmin' : min.point['x'], 'ymin' : min.point['y'], 'xmax' : max.point['x'], 'ymax' : max.point['y']}

    def __getitem__(self):
        return self.corners

class ImgsSend(object):
    def __init__(self, sourceType, source, polygon = None, bbox = None):
        self.imgs = []
        if sourceType == "file":
            with open(source, "rb") as image_file:
                source = base64.b64encode(image_file.read())
            sourceType = "base64"
        self.imgs.append({sourceType : source})
        if polygon is not None:
            self.imgs[0].update({"polygon" : polygon})
        if bbox is not None:
            self.imgs[0].update({"bbox" : bbox})

    def addImg(self, sourceType, source, polygon = None, bbox = None):
        last = len(self.imgs)
        if sourceType == "file":
            with open(source, "rb") as image_file:
                source = base64.b64encode(image_file.read())
            sourceType = "base64"
        self.imgs.append({sourceType : source})
        if polygon is not None:
            self.imgs[last].update(polygon)
        if bbox is not None:
            self.imgs[last].update(bbox)

    def __getitem__(self):
        return self.imgs

class BatchObject:
    def __init__(self, dbname):
        self.db = dbname
        self.requests = []

    def deleteObject(self, id):
        self.requests.append({"db" : self.db, "id" : id, "method" : "DELETE"})

    def getObject(self, id):
        self.requests.append({"db" : self.db, "id" : id, "method" : "GET"})

    def addObject(self, imgs, id = None):
        if id != None:
            self.requests.append({"db" : self.db, "imgs" : imgs.imgs, "method" : "POST"})
        else :
            self.requests.append({"db" : self.db, "id" : id, "imgs" : imgs.imgs, "method" : "PUT"})

    def __getitem__(self):
        return self.requests



class HTTPHelper(object):

    def __init__(self, app_id, api_key, verify, host):
        """
        Init the HTTP helper with API key and secret
        """
        self.api_key = str(api_key)
        self.app_id = str(app_id)

        self.verify = verify
        if not host is None:
            self.host = host
        if self.host[-1] == '/':
            self.host = self.host[:-1]

    #--------------------------------------------------------------------

    def setupHeaders(self, headers = None):
        """
        Build authentification header
        """
        if headers is None:
            headers = dict([])

        if not 'Accept' in headers:
            headers['Accept'] = 'application/json'
        headers['X-APP-ID'] = self.app_id
        headers['X-API-KEY'] = self.api_key

        return headers

    #--------------------------------------------------------------------

    def response(self, r):
        """
        Decode the response returned by the server
        """
        if r.status_code == 204: #delete
            return "No Content", r.status_code

        if 'application/json' in r.headers['Content-Type']:
            return r.json(), r.status_code
        else:
            return r.content, r.status_code

    #--------------------------------------------------------------------

    def formatParams(self, data):
        if data:
            for key, value in data.items():
                if isinstance(value, bool):
                    data[key] = int(value)
                elif isinstance(value, dict):
                    data[key] = json.dumps(value)
        return data

    #--------------------------------------------------------------------

    def helperGD(self, func, resource, params):
        r = func(self.host + resource,
                    headers = self.setupHeaders(),
                    params  = self.formatParams(params),
                    verify  = self.verify)
        return self.response(r)

    #--------------------------------------------------------------------

    def helperPPP(self, func, resource, params, data, contentType, files):
        if contentType.startswith('application/json') and not isinstance(data, basestring):
            data = json.dumps(data)

        r = func(self.host + resource,
                    params = self.formatParams(params),
                    data = data,
                    files = files,
                    headers = self.setupHeaders({"Content-Type": contentType}),
                    verify = self.verify)
        return self.response(r)

    #--------------------------------------------------------------------

    def get(self, resource, params = None):
        """
        Perform a GET request
        """
        return self.helperGD(requests.get, resource, params)

    #--------------------------------------------------------------------

    def delete(self, resource, params = None):
        """
        Perform a DELETE request
        """
        return self.helperGD(requests.delete, resource, params)

    #--------------------------------------------------------------------

    def put(self, resource, params = None, data = None, contentType = 'application/json', files = None):
        """
        Perform a PUT request
        """
        return self.helperPPP(requests.put, resource, params, data, contentType, files)

    #--------------------------------------------------------------------

    def post(self, resource, params = None, data = None, contentType = 'application/json', files = None):
        """
        Perform a POST request
        """
        return self.helperPPP(requests.post, resource, params, data, contentType, files)

    #--------------------------------------------------------------------

    def patch(self, resource, params = None, data = None, contentType = 'application/json', files = None):
        """
        Perform a PATCH request
        """
        return self.helperPPP(requests.patch, resource, params, data, contentType, files)


###############################################################################

class Client(object):

    def __init__(self, app_id, api_key, verify = True, host = API_HOST, version = API_VERSION):
        if app_id == None or api_key == None:
            raise Exception("Please specify APP_ID and API_KEY.")

        # Until v1.0, we force explicit versioning
        if version is None:
            raise Exception("API version should be explicitly mentionned.")

        if version is not None:
            if not isinstance(version, basestring):
                version = 'v%g' % version
            elif version[0] != 'v':
                version = 'v' + version

            host += '/' + version

        self.helper = HTTPHelper(app_id, api_key, verify, host)

    #--------------------------------------------------------------------

    def _response_(self, response, status, okStatus = [200], getStatus = False):
        if status in okStatus:
            return response if getStatus is False else (response, status)
        else:
            if isinstance(response, basestring):
                raise Exception(response)
            elif "message" in response:
                raise Exception(response['message'])
            else:
                raise Exception(str(response))

    #--------------------------------------------------------------------

    def waitForCompletion(self, response) :
        while True:
            t = self.retrieveTask(response["task_id"])['task']
            status = t['status']
            if status != "pending":
                if status == "error":
                    raise Exception ("Error on task: %s" % t)
                return t

    #--------------------------------------------------------------------

    def getDBs(self):
        response, status = self.helper.get('/search/dbs')
        return self._response_(response, status)

    #--------------------------------------------------------------------

    def clearDB(self, db, wait = False):
        response, status = self.helper.delete('/search/dbs/%s/objects' % db)
        complete_response = self._response_(response, status, [200])
        if wait :
            return self._response_(self.waitForCompletion(complete_response), status)
        return complete_response

    #--------------------------------------------------------------------

    def deleteDB(self, db, wait = False):
        response, status = self.helper.delete('/search/dbs/%s' % db)
        complete_response = self._response_(response, status, [200])
        if wait :
            return self._response_(self.waitForCompletion(complete_response), status)
        return complete_response

    #--------------------------------------------------------------------

    def getCount(self, db):
        response, status = self.helper.get('/search/dbs/%s/count/' % db)
        return self._response_(response, status, [200])

    #--------------------------------------------------------------------

    def saveObject(self, db, id = None, imgs = [], data = {}, wait = False):
        for img in imgs:
            if "file" in img:
                with open(img["file"], "rb") as image_file:
                    img = base64.b64encode(image_file.read())
                img += {"base64" : img}
                del img["file"]

        obj = {
            'imgs' : imgs,
            'data' : data,
        }
        if id is None:
            response, status = self.helper.post('/search/dbs/%s/objects' % db, data = obj)
        else:
            response, status = self.helper.put('/search/dbs/%s/objects/%s' % (db, str(id)), data = obj)
        complete_response = self._response_(response, status)
        if wait:
            return self._response_(self.waitForCompletion(complete_response), status)
        return complete_response

    #--------------------------------------------------------------------

    def retrieveTask(self, task_id):
        response, status = self.helper.get('/tasks/%s/' % task_id)
        return self._response_(response, status)

    #--------------------------------------------------------------------

    def getObject(self, db, id):
        response, status = self.helper.get('/search/dbs/%s/objects/%s' % (db, str(id)))
        return self._response_(response, status)

    #--------------------------------------------------------------------

    def getObjects(self, db, **kwargs):
        response, status = self.helper.get('/search/dbs/%s/objects/' % db, params = kwargs)
        return self._response_(response, status)

    #--------------------------------------------------------------------

    def deleteObject(self, db, id, wait = False):
        response, status = self.helper.delete('/search/dbs/%s/objects/%s' % (db, str(id)))
        complete_response = self._response_(response, status)
        if wait :
            return self._response_(self.waitForCompletion(complete_response), status)
        return complete_response

    #--------------------------------------------------------------------

    def search(self, db, source, wait = False, **kwargs):
        """
        Search for similar images.

        Take:
        - db      : the database name.
        - source  : the url or file.
        - filters : filters under the form of a MongoDB request. The query is
                      performed on the data field of the database object.
        - skip    : number of results to skip. Defaults to 0.
        - limit   : number of results to return. Defaults to 100.

        Give:
        - hits    : list of matching images.
        """

        if "file" in source:
            with open(source["file"], "rb") as image_file:
                img = base64.b64encode(image_file.read())
            source = {"base64" : img}

        params = source
        for k, v in kwargs.items():
            params[k] = v

        response, status = self.helper.get('/search/query/%s/' % db, params = params)
        complete_response = self._response_(response, status)
        if wait:
            return self._response_(self.waitForCompletion(complete_response)["data"], status)
        return complete_response

    #--------------------------------------------------------------------
    # Send Batch request
    def batchRequest(self, requests, wait = False):
        data = {
            "requests" : requests.requests
        }
        response, status = self.helper.post('/search/batch/dbs', data = json.dumps(data))
        if wait :
            return self._response_(self.waitForCompletion(response), status)
        return self._response_(response, status)

    #--------------------------------------------------------------------

    def detect(self, detector_type, data, wait = False):
        response, status = self.helper.post('/detect/%s/' % detector_type, data = json.dumps(data))
        complete_response = self._response_(response, status)
        if wait :
            return self._response_(self.waitForCompletion(complete_response)["data"], status)
        return complete_response

    #--------------------------------------------------------------------

    def classify(self, model_id, img_url, is_public = False, wait = True):
        if is_public:
            url = '/classify/public/models/%d/test' % model_id
        else:
            url = '/classify/models/%d/test' % model_id
        response, status = self.helper.post(url, data = json.dumps({ "img" : { "url" : img_url } }))
        complete_response = self._response_(response, status)
        if wait :
            return self._response_(self.waitForCompletion(complete_response)["data"], status)
        return complete_response


###############################################################################
