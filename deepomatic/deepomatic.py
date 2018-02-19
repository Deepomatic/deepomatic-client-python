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
from six import string_types
from requests.structures import CaseInsensitiveDict

###############################################################################

API_VERSION = 0.7
API_HOST = 'https://api.deepomatic.com'

###############################################################################


class BadStatus(Exception):
    def __init__(self, response):
        self.response = response

    def json(self):
        return self.response.json()

    @property
    def content(self):
        return self.response.content

    @property
    def status_code(self):
        return self.response.status_code

    def __str__(self):
        return "Bad status code %s with body %s" % (self.response.status_code, self.response.content)


class TaskError(Exception):
    def __init__(self, task):
        self.task = task

    def __str__(self):
        return "Error on task: %s" % self.task


###############################################################################

class HTTPHelper(object):

    def __init__(self, app_id, api_key, verify, host):
        """
        Init the HTTP helper with API key and secret
        """
        self.api_key = str(api_key)
        self.app_id = str(app_id)

        self.verify = verify
        if host is not None:
            self.host = host
        if self.host[-1] == '/':
            self.host = self.host[:-1]

    def setup_headers(self, headers=None, content_type=None):
        """
        Build authentification header
        """
        if headers is None:
            headers = CaseInsensitiveDict()
        elif isinstance(headers, dict):
            headers = CaseInsensitiveDict(headers)

        if content_type is not None:
            headers['Content-type'] = content_type
            if 'Accept' not in headers:
                headers['Accept'] = content_type

        headers['X-APP-ID'] = self.app_id
        headers['X-API-KEY'] = self.api_key

        return headers

    def response(self, r, check_status=True):
        """
        Decode the response returned by the server
        """
        if r.status_code == 204:  # delete
            return "No Content"

        if check_status:
            if r.status_code < 200 or r.status_code >= 300:
                raise BadStatus(r)

        if 'application/json' in r.headers['Content-Type']:
            return r.json()
        else:
            return r.content

    def format_params(self, data):
        if data:
            for key, value in data.items():
                if isinstance(value, bool):
                    data[key] = int(value)
                elif isinstance(value, dict):
                    data[key] = json.dumps(value)
        return data

    def make_request(self, func, resource, params, data=None, content_type=None, files=None):
        if content_type is not None and content_type.strip() == 'application/json' and not isinstance(data, string_types):
            data = json.dumps(data)

        headers = self.setup_headers(content_type=content_type)
        params = self.format_params(params)
        r = func(self.host + resource, params=params, data=data, files=files, headers=headers, verify=self.verify)
        return self.response(r)

    def get(self, resource, params=None):
        """
        Perform a GET request
        """
        return self.make_request(requests.get, resource, params)

    def delete(self, resource, params=None):
        """
        Perform a DELETE request
        """
        return self.make_request(requests.delete, resource, params)

    def put(self, resource, params=None, data=None, content_type='application/json', files=None):
        """
        Perform a PUT request
        """
        return self.make_request(requests.put, resource, params, data, content_type, files)

    def post(self, resource, params=None, data=None, content_type='application/json', files=None):
        """
        Perform a POST request
        """
        return self.make_request(requests.post, resource, params, data, content_type, files)

    def patch(self, resource, params=None, data=None, content_type='application/json', files=None):
        """
        Perform a PATCH request
        """
        return self.make_request(requests.patch, resource, params, data, content_type, files)


###############################################################################

class Client(object):

    def __init__(self, app_id, api_key, verify=True, host=API_HOST, version=API_VERSION):
        if app_id is None or api_key is None:
            raise Exception("Please specify APP_ID and API_KEY.")

        # Until v1.0, we force explicit versioning
        if version is None:
            raise Exception("API version should be explicitly mentionned.")

        if version is not None:
            if not isinstance(version, string_types):
                version = 'v%g' % version
            elif version[0] != 'v':
                version = 'v' + version

            host += '/' + version

        self.helper = HTTPHelper(app_id, api_key, verify, host)

    # task endpoints

    def waitForCompletion(self, response):
        while True:
            t = self.retrieveTask(response["task_id"])['task']
            status = t['status']
            if status != "pending":
                if status == "error":
                    raise TaskError(t)
                return t

    def _waitTaskOrNot(self, response, wait=False):
        if wait:
            task = self.waitForCompletion(response)
            if task["data"]:
                return task["data"]
        return response

    def retrieveTask(self, task_id):
        return self.helper.get('/tasks/%s/' % task_id)

    # networks endpoints

    def list_networks(self):
        return self.helper.get("/networks")

    def get_network(self, network_id):
        return self.helper.get("/networks/%s" % network_id)

    def delete_network(self, network_id):
        return self.helper.delete("/networks/%s" % network_id)

    def edit_network(self, network_id, name, description, metadata):
        return self.helper.patch("/networks/%s" % network_id, data={"name": name, "description": description, "metadata": metadata})

    def infere_network(self, network_id, output_layers, inputs, wait=False):
        response = self.helper.post("/networks/{network_id}/inference".format(network_id=network_id), data={
            "inputs": inputs,
            "output_layers": output_layers
        })
        return self._waitTaskOrNot(response, wait=wait)

    def infere_network_from_source(self, network_id, output_layers, source, wait=False):
        return self.infere_network(network_id, output_layers, [{"image": {"source": source}}], wait=wait)

    def add_network(self, name, description, preprocessing, graph, weights, extra_files=None, wait=False):
        data = {"name": name, "description": description, "preprocessing": json.dumps(preprocessing)}
        files = {"graph": graph, "weights": weights}
        if extra_files is not None:
            files.update(extra_files)
        response = self.helper.post("/networks", data=data, content_type=None, files=files)
        return self._waitTaskOrNot(response, wait=wait)

    # recognition endpoints

    def list_recognition_specs(self):
        return self.helper.get("/recognition/specs")

    def get_recognition_spec(self, spec_id):
        return self.helper.get("/recognition/specs/%s" % spec_id)

    def delete_recognition_spec(self, spec_id):
        return self.helper.delete("/recognition/specs/%s" % spec_id)

    def edit_recognition_spec(self, spec_id, name, description, metadata, current_version_id):
        data = {"name": name, "description": description, "metadata": metadata, "current_version_id": current_version_id}
        return self.helper.patch("/recognition/specs/%s" % spec_id, data=data)

    def add_recognition_spec(self, name, description, outputs):
        return self.helper.post("/recognition/specs", data={"name": name, "description": description, "outputs": outputs})

    def infere_recognition_spec(self, spec_id, inputs, wait=False):
        response = self.helper.post("/recognition/specs/%s/inference" % spec_id, data={"inputs": inputs})
        return self._waitTaskOrNot(response, wait=wait)

    def infere_recognition_spec_from_source(self, spec_id, source, wait=False):
        return self.infere_recognition_spec(spec_id, [{"image": {"source": source}}], wait=wait)

    # versions endpoints

    def list_recognition_versions(self):
        return self.helper.get("/recognition/versions")

    def list_recognition_spec_versions(self, spec_id):
        return self.helper.get("/recognition/specs/%s/versions" % spec_id)

    def get_recognition_version(self, version_id):
        return self.helper.get("/recognition/versions/%s" % version_id)

    def add_recognition_version(self, spec_id, network_id, post_processings):
        return self.helper.post("/recognition/versions", data={"spec_id": spec_id, "network_id": network_id, "post_processings": post_processings})

    def delete_recognition_version(self, version_id):
        return self.helper.delete("/recognition/versions/%s" % version_id)

    def infere_recognition_version(self, version_id, inputs, wait=False):
        response = self.helper.post("/recognition/versions/%s/inference" % version_id, data={"inputs": inputs})
        return self._waitTaskOrNot(response, wait=wait)

    def infere_recognition_version_from_source(self, version_id, source, wait=False):
        return self.infere_recognition_version(version_id, [{"image": {"source": source}}], wait=wait)
