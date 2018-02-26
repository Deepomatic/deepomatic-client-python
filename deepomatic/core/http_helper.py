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
from promise import Promise
from six import string_types

from deepomatic.core.exceptions import DeepomaticException, BadStatus


###############################################################################

class HTTPHelper(object):

    def __init__(self, app_id, api_key, verify, host, version):
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

        def execute_request(resolve, reject):
            try:
                response = func(self.host + resource, params=params, data=data, files=files, headers=headers, verify=self.verify)

                # Close opened files
                for file in opened_files:
                    file.close()

                if response.status_code == 204:  # delete
                    return resolve(None)

                if response.status_code < 200 or response.status_code >= 300:
                    return reject(BadStatus(response))

                if 'application/json' in response.headers['Content-Type']:
                    return resolve(response.json())
                else:
                    return resolve(response.content)
            except Exception as e:
                return reject(e)

        return Promise(execute_request)

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
