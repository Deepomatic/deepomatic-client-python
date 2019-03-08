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
from deepomatic.api.resources.network import Network
from deepomatic.api.resources.recognition import RecognitionSpec, RecognitionVersion
from deepomatic.api.resources.task import Task
from deepomatic.api.resources.account import Account

###############################################################################

API_VERSION = 0.7

###############################################################################

class Client(object):

    def __init__(self, app_id=None, api_key=None, verify_ssl=None, check_query_parameters=True, host=None, version=API_VERSION, user_agent_suffix='', pool_maxsize=20):
        self.http_helper = HTTPHelper(app_id, api_key, verify_ssl, host, version, check_query_parameters, user_agent_suffix, pool_maxsize)

        # /accounts

        self.Account = Account(self.http_helper)

        # /tasks

        self.Task = Task(self.http_helper)

        # /networks

        self.Network = Network(self.http_helper)

        # /recognition

        self.RecognitionSpec = RecognitionSpec(self.http_helper)

        self.RecognitionVersion = RecognitionVersion(self.http_helper)
