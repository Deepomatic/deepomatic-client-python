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
import sys
import platform
from requests.structures import CaseInsensitiveDict
from six import string_types

from deepomatic.exceptions import DeepomaticException, BadStatus
from deepomatic.version import __VERSION__

###############################################################################


class HTTPHelper(object):
    def __init__(self, app_id, api_key, verify, host, version, check_query_parameters, user_agent_suffix='', pool_maxsize=100):
        """
        Init the HTTP helper with API key and secret
        """
        if app_id is None:
            app_id = os.getenv('DEEPOMATIC_APP_ID')
        if api_key is None:
            api_key = os.getenv('DEEPOMATIC_API_KEY')
        if app_id is None or api_key is None:
            raise DeepomaticException("Please specify 'app_id' and 'api_key' either by passing those values to the client or by defining the DEEPOMATIC_APP_ID and DEEPOMATIC_API_KEY environment variables.")

        if not isinstance(version, string_types):
            version = 'v%g' % version
        elif version[0] != 'v':
            version = 'v' + version

        if not host.endswith('/'):
            host += '/'

        python_version = "{0}.{1}.{2}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)

        user_agent_params = {
            'package_version': __VERSION__,
            'requests_version': requests.__version__,
            'python_version': python_version,
            'platform': platform.platform()
        }

        self.user_agent = 'deepomatic-client-python/{package_version} requests/{requests_version} python/{python_version} platform/{platform}\
            '.format(**user_agent_params)
        if user_agent_suffix:
            self.user_agent += ' ' + user_agent_suffix

        self.api_key = str(api_key)
        self.app_id = str(app_id)
        self.verify = verify
        self.host = host
        self.resource_prefix = host + version
        self.check_query_parameters = check_query_parameters

        headers = {
            'User-Agent': self.user_agent,
            'X-APP-ID': self.app_id,
            'X-API-KEY': self.api_key,
        }
        self.session = requests.session()
        self.session.headers.update(headers)
        # Use pool_maxsize to cache connections for the same host
        adapter = requests.adapters.HTTPAdapter(pool_maxsize=pool_maxsize)
        self.session.mount('http', adapter)

    def setup_headers(self, headers=None, content_type=None):
        """
        Build additional headers
        """
        if headers is None:
            headers = CaseInsensitiveDict()
        elif isinstance(headers, dict):
            headers = CaseInsensitiveDict(headers)

        if content_type is not None:
            headers['Content-Type'] = content_type
            if 'Accept' not in headers:
                headers['Accept'] = content_type

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

    def make_request(self, func, resource, params, data=None, content_type=None, files=None, stream=False, *args, **kwargs):
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

        if not resource.startswith('http'):
            resource = self.resource_prefix + resource
        response = func(resource, params=params, data=data, files=files, headers=headers, verify=self.verify, *args, **kwargs)

        # Close opened files
        for file in opened_files:
            file.close()

        if response.status_code == 204:  # delete
            return None

        if response.status_code < 200 or response.status_code >= 300:
            raise BadStatus(response)

        if stream:
            # we asked for a stream, we let the user download it as he wants or it will load everything in RAM
            # not good for big files
            return response
        elif 'application/json' in response.headers['Content-Type']:
            return response.json()
        else:
            return response.content

    def get(self, resource, params=None):
        """
        Perform a GET request
        """
        return self.make_request(self.session.get, resource, params)

    def delete(self, resource, params=None):
        """
        Perform a DELETE request
        """
        return self.make_request(self.session.delete, resource, params)

    def post(self, resource, params=None, data=None, content_type='application/json', files=None):
        """
        Perform a POST request
        """
        return self.make_request(self.session.post, resource, params, data, content_type, files)

    def put(self, resource, params=None, data=None, content_type='application/json', files=None):
        """
        Perform a PUT request
        """
        return self.make_request(self.session.put, resource, params, data, content_type, files)

    def patch(self, resource, params=None, data=None, content_type='application/json', files=None):
        """
        Perform a PATCH request
        """
        return self.make_request(self.session.patch, resource, params, data, content_type, files)


###############################################################################
