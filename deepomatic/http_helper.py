# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 Deepomatic SAS
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

import os
import json
import requests
from requests.structures import CaseInsensitiveDict
from six import string_types

from deepomatic.exceptions import DeepomaticException, BadStatus


###############################################################################

class HTTPHelper(object):

    def __init__(self, app_id, api_key, verify, host, version, check_query_parameters):
        """
        Init the HTTP helper with API key and secret
        """
        if app_id is None or api_key is None:
            raise Exception("Please specify APP_ID and API_KEY.")

        if not isinstance(version, string_types):
            version = 'v%g' % version
        elif version[0] != 'v':
            version = 'v' + version

        if not host.endswith('/'):
            host += '/'
        host += version

        self.api_key = str(api_key)
        self.app_id = str(app_id)
        self.verify = verify
        self.host = host
        self.check_query_parameters = check_query_parameters

    def setup_headers(self, headers=None, content_type=None):
        """
        Build authentification header
        """
        if headers is None:
            headers = CaseInsensitiveDict()
        elif isinstance(headers, dict):
            headers = CaseInsensitiveDict(headers)

        if content_type is not None:
            headers['Content-Type'] = content_type
            if 'Accept' not in headers:
                headers['Accept'] = content_type

        headers['X-APP-ID'] = self.app_id
        headers['X-API-KEY'] = self.api_key

        return headers

    def format_params(self, data):
        if data:
            for key, value in data.items():
                if isinstance(value, bool):
                    data[key] = int(value)
                elif isinstance(value, dict):
                    data[key] = json.dumps(value)
        return data

    def dump_json_for_multipart(self, data, files):
        def recursive_json_dump(prefix, obj, data, files, omit_dot=False):
            if isinstance(obj, dict):
                if not omit_dot:  # see comment below
                    prefix += '.'
                for key, value in obj.items():
                    recursive_json_dump(prefix + key, value, data, files)
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    # omit_dot is True as DRF parses list of dictionnaries like this:
                    # {"parent": [{"subfield": 0}]} would be:
                    # 'parent[0]subfield': 0
                    recursive_json_dump(prefix + '[{}]'.format(i), value, data, files, omit_dot=True)
            elif hasattr(obj, 'read'):  # if is file:
                if prefix in files:
                    raise DeepomaticException("Duplicate key: " + prefix)
                files[prefix] = obj
            else:
                data[prefix] = obj

        if files is None:
            files = {}
        new_data = {}

        recursive_json_dump('', data, new_data, files, omit_dot=True)

        if len(files) == 0:
            files = None
        return new_data, files

    def make_request(self, func, resource, params, data=None, content_type=None, files=None):
        if isinstance(data, dict) or isinstance(data, list):
            if content_type.strip() == 'application/json':
                data = json.dumps(data)
            elif content_type.strip() == 'multipart/mixed':
                content_type = None  # will be automatically set to multipart
                data, files = self.dump_json_for_multipart(data, files)
            else:
                raise DeepomaticException("Unsupported Content-Type")

        headers = self.setup_headers(content_type=content_type)
        params = self.format_params(params)

        opened_files = []
        if files is not None:
            new_files = {}
            for key, file in files.items():
                if isinstance(file, string_types):
                    if not os.path.isfile(file):
                        raise DeepomaticException("Does not refer to a file: {}".format(file))
                    file = open(file, 'rb')
                    opened_files.append(file)
                else:
                    file.seek(0)
                new_files[key] = file
            files = new_files

        response = func(self.host + resource, params=params, data=data, files=files, headers=headers, verify=self.verify)

        # Close opened files
        for file in opened_files:
            file.close()

        if response.status_code == 204:  # delete
            return None

        if response.status_code < 200 or response.status_code >= 300:
            raise BadStatus(response)

        if 'application/json' in response.headers['Content-Type']:
            return response.json()
        else:
            return response.content

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

    def post(self, resource, params=None, data=None, content_type='application/json', files=None):
        """
        Perform a POST request
        """
        return self.make_request(requests.post, resource, params, data, content_type, files)

    def put(self, resource, params=None, data=None, content_type='application/json', files=None):
        """
        Perform a PUT request
        """
        return self.make_request(requests.put, resource, params, data, content_type, files)

    def patch(self, resource, params=None, data=None, content_type='application/json', files=None):
        """
        Perform a PATCH request
        """
        return self.make_request(requests.patch, resource, params, data, content_type, files)


###############################################################################
