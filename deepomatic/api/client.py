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

from deepomatic.api.http_helper import HTTPHelper
from deepomatic.api.resources.account import Account
from deepomatic.api.resources.network import Network
from deepomatic.api.resources.recognition import (RecognitionSpec,
                                                  RecognitionVersion)
from deepomatic.api.resources.task import Task


class Client(object):

    def __init__(self, *args, **kwargs):
        """
           Constructs a Client to send requests to the Deepomatic API.

            :param app_id: App ID for authentication. Defaults to `None`.
               If `None`, try to retrieve it from the `DEEPOMATIC_APP_ID` environment variable.
               Important: this parameter is deprecated and will be removed in a near future.
           :type app_id: string
           :param api_key: API key for authentication. Defaults to `None`.
               If `None` try to retrieve it from the `DEEPOMATIC_API_KEY` environment variable.
               If it fails raise a `DeepomaticException`.
           :type api_key: string
           :param verify_ssl (optional): whether to ask `requests` to verify the TLS/SSL certificates.
               Defaults to `None`.
               If `None` try to get it from the `DEEPOMATIC_API_VERIFY_TLS` environment variable (`0`: False, `1`: True).
               If not found it is set to True.
           :type verify_ssl: bool
           :param host (optional): API root URL.
           :type host: string
           :param version (optional): API version.
           :type version: string
           :param user_agent_prefix (optional): Prefix the HTTP User-Agent.
               It is recommended to declare your client via this parameter. Example: 'my-app/1.0.0'.
           :type user_agent_prefix: string
           :param pool_maxsize (optional): Set `requests.adapters.HTTPAdapter.pool_maxsize` for concurrent calls.
               Defaults to 20.
           :type pool_maxsize: int
           :param requests_timeout: timeout of each request.
               Defaults to `http_helper.RequestsTimeout.FAST`.
               More details in the `requests` documentation: https://2.python-requests.org/en/master/user/advanced/#timeouts
           :type requests_timeout: float or tuple(float, float)
           :param http_retry (optional): Customize the retry of http errors.
               Defaults to `HTTPRetry()`. See `http_retry.HTTPRetry` documentation for details about parameters and default values.
               If `None`, no retry will be done on errors.
           :type http_retry: http_retry.HTTPRetry

           :return: :class:`Client` object
           :rtype: deepomatic.api.client.Client
        """
        self.http_helper = HTTPHelper(*args, **kwargs)

        # /accounts

        self.Account = Account(self.http_helper)

        # /tasks

        self.Task = Task(self.http_helper)

        # /networks

        self.Network = Network(self.http_helper)

        # /recognition

        self.RecognitionSpec = RecognitionSpec(self.http_helper)

        self.RecognitionVersion = RecognitionVersion(self.http_helper)
