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

import functools
import json
import os
import platform
import sys

import requests
from deepomatic.api.exceptions import (BadStatus, ServerError,
                                       ClientError, DeepomaticException)
from deepomatic.api.http_retry import HTTPRetry
from deepomatic.api.version import __title__, __version__
from requests.structures import CaseInsensitiveDict
from six import string_types

API_HOST = 'https://api.deepomatic.com'
API_VERSION = 0.7

###############################################################################


class RequestsTimeout(object):
    FAST = 8.
    MEDIUM = 60.
    SLOW = 600.


class HTTPHelper(object):
    def __init__(self, app_id=None, api_key=None, verify_ssl=None,
                 host=None, version=API_VERSION, check_query_parameters=True,
                 user_agent_prefix='', pool_maxsize=20,
                 requests_timeout=RequestsTimeout.FAST, **kwargs):
        """
        Init the HTTP helper with API key and secret.
        Check out the `client.Client` documentation for more details about the parameters.
        """

        # `http_retry` is retrieved from `kwargs` because a default parameter `http_retry=HTTPRetry()` is dangerous
        # If the rest of the code mutates `self.http_retry`, it would change the default parameter for all other `Client` instances
        self.http_retry = kwargs.pop('http_retry', HTTPRetry())

        if len(kwargs) > 0:
            raise TypeError("Too many parameters. HTTPHelper does not handle kwargs: {}".format(kwargs))

        self.requests_timeout = requests_timeout

        if host is None:
            host = os.getenv('DEEPOMATIC_API_URL', API_HOST)
        if verify_ssl is None:
            verify_ssl = os.getenv('DEEPOMATIC_API_VERIFY_TLS', '1') == '1'
        if app_id is None:
            app_id = os.getenv('DEEPOMATIC_APP_ID')
        if api_key is None:
            api_key = os.getenv('DEEPOMATIC_API_KEY')
        if api_key is None:
            raise DeepomaticException("Please specify 'api_key' either by passing it to the client"
                                      " or by defining the DEEPOMATIC_API_KEY environment variable.")

        if version is None or version == '':
            version = ''
        elif not isinstance(version, string_types):
            version = 'v%g' % version
        elif version[0] != 'v':
            version = 'v' + version

        if not host.endswith('/'):
            host += '/'

        python_version = "{0}.{1}.{2}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)

        user_agent_params = {
            'package_title': __title__,
            'package_version': __version__,
            'requests_version': requests.__version__,
            'python_version': python_version,
            'platform': platform.platform()
        }

        user_agent_list = []

        if user_agent_prefix:
            user_agent_list.append(user_agent_prefix)

        user_agent_list += [
            '{package_title}-python-client/{package_version}',
            'requests/{requests_version}',
            'python/{python_version} platform/{platform}',
        ]

        self.user_agent = ' '.join(user_agent_list).format(**user_agent_params)

        self.api_key = str(api_key)
        self.app_id = str(app_id) if app_id else None
        self.verify_ssl = verify_ssl
        self.host = host
        self.resource_prefix = host + version

        # This is only used in mixins, this should not stay here
        self.check_query_parameters = check_query_parameters

        self.session = requests.Session()
        self.session.headers.update(self.default_headers())
        # Use pool_maxsize to cache connections for the same host
        adapter = requests.adapters.HTTPAdapter(pool_maxsize=pool_maxsize)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def default_headers(self):
        """
        Return the default headers, can be overridden
        """
        headers = {
            'User-Agent': self.user_agent,
            'X-API-KEY': self.api_key,
        }
        if self.app_id:
            headers['X-APP-ID'] = self.app_id
        return headers

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

    def dump_json_for_multipart(self, data_dict):
        if data_dict is None:
            return None

        def recursive_json_dump(prefix, obj, data_dict, omit_dot=False):
            if isinstance(obj, dict):
                if not omit_dot:  # see comment below
                    prefix += '.'
                for key, value in obj.items():
                    recursive_json_dump(prefix + key, value, data_dict)
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    # omit_dot is True as DRF parses list of dictionnaries like this:
                    # {"parent": [{"subfield": 0}]} would be:
                    # 'parent[0]subfield': 0
                    recursive_json_dump(prefix + '[{}]'.format(i), value, data_dict, omit_dot=True)
            else:
                if prefix in data_dict:
                    raise DeepomaticException("Duplicate key: " + prefix)
                data_dict[prefix] = obj

        new_dict = {}

        recursive_json_dump('', data_dict, new_dict, omit_dot=True)

        return new_dict

    def send_request(self, requests_callable, *args, **kwargs):
        # requests_callable must be a method from the requests module

        # this is the timeout of requests module
        requests_timeout = kwargs.pop('timeout', self.requests_timeout)
        http_retry = kwargs.pop('http_retry', self.http_retry)

        functor = functools.partial(requests_callable, *args,
                                    verify=self.verify_ssl,
                                    timeout=requests_timeout, **kwargs)

        if http_retry is not None:
            return http_retry.retry(functor)

        return functor()

    def make_request(self, func, resource, params=None, data=None,
                     content_type='application/json', files=None,
                     stream=False, *args, **kwargs):

        if content_type is not None:
            if content_type.strip() == 'application/json':
                if data is not None:
                    data = json.dumps(data)
            elif content_type.strip() == 'multipart/mixed':
                # If no files are provided, requests will default to form-urlencoded content type
                # But the API doesn't support it.
                if not files:
                    raise Exception("Cannot send the request as multipart without files provided.")
                # requests will build the good multipart content types with the boundaries
                content_type = None
                data = self.dump_json_for_multipart(data)
                files = self.dump_json_for_multipart(files)
            else:
                raise DeepomaticException("Unsupported Content-Type")

        headers = self.setup_headers(content_type=content_type)
        params = self.format_params(params)

        opened_files = []
        if files is not None:
            new_files = {}
            for key, file in files.items():
                if isinstance(file, string_types):
                    try:
                        # this may raise if file is a string containing bytes
                        if os.path.exists(file):
                            file = open(file, 'rb')
                            opened_files.append(file)
                    except TypeError:
                        pass
                elif hasattr(file, 'seek'):
                    file.seek(0)

                if hasattr(file, 'read') or \
                   isinstance(file, bytes) or \
                   (isinstance(file, tuple) and len(file) == 3):
                    new_files[key] = file
                else:
                    new_files[key] = (None, file, 'application/json')

            files = new_files

        if not resource.startswith('http'):
            resource = self.resource_prefix + resource

        response = self.send_request(func, resource, *args,
                                     params=params, data=data,
                                     files=files, headers=headers,
                                     stream=stream, **kwargs)

        # Close opened files
        for file in opened_files:
            file.close()

        status_code = response.status_code
        if status_code == 204:  # delete
            return None

        if status_code < 200 or status_code >= 300:
            if status_code >= 400 and status_code < 500:
                raise ClientError(response)
            elif status_code >= 500 and status_code < 600:
                raise ServerError(response)
            else:
                raise BadStatus(response)

        if stream:
            # we asked for a stream, we let the user download it as he wants or it will load everything in RAM
            # not good for big files
            return response
        elif 'application/json' in response.headers['Content-Type']:
            return response.json()
        else:
            return response.content

    def get(self, resource, *args, **kwargs):
        """
        Perform a GET request
        """
        return self.make_request(self.session.get, resource, *args, **kwargs)

    def delete(self, resource, *args, **kwargs):
        """
        Perform a DELETE request
        """
        return self.make_request(self.session.delete, resource, *args, **kwargs)

    def post(self, resource, *args, **kwargs):
        """
        Perform a POST request
        """
        return self.make_request(self.session.post, resource, *args, **kwargs)

    def put(self, resource, *args, **kwargs):
        """
        Perform a PUT request
        """
        return self.make_request(self.session.put, resource, *args, **kwargs)

    def patch(self, resource, *args, **kwargs):
        """
        Perform a PATCH request
        """
        return self.make_request(self.session.patch, resource, *args, **kwargs)


###############################################################################
