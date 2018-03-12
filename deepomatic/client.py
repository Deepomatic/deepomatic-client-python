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

from deepomatic.http_helper import HTTPHelper
from deepomatic.resources.network import Network
from deepomatic.resources.recognition import RecognitionSpec, RecognitionVersion
from deepomatic.resources.task import Task
from deepomatic.resources.account import Account

###############################################################################

API_VERSION = 0.7
API_HOST = 'https://api.deepomatic.com'


###############################################################################

class Client(object):

    def __init__(self, app_id=None, api_key=None, verify_ssl=True, check_query_parameters=True, host=None, version=API_VERSION):
        if host is None:
            host = API_HOST
        helper = HTTPHelper(app_id, api_key, verify_ssl, host, version, check_query_parameters)

        # /accounts

        self.Account = Account(helper)

        # /tasks

        self.Task = Task(helper)

        # /networks

        self.Network = Network(helper)

        # /recognition

        self.RecognitionSpec = RecognitionSpec(helper)

        self.RecognitionVersion = RecognitionVersion(helper)

