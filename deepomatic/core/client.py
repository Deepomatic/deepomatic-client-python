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

from deepomatic.core.http_helper import HTTPHelper
from deepomatic.resources.network import NetworkList, Network
from deepomatic.resources.recognition import RecognitionSpecList, RecognitionSpec, RecognitionVersionList, RecognitionVersion
from deepomatic.resources.task import Task

###############################################################################

API_VERSION = 0.7
API_HOST = 'https://api.deepomatic.com'


###############################################################################

class Client(object):

    def __init__(self, app_id, api_key, verify=True, host=API_HOST, version=API_VERSION):
        self.helper = HTTPHelper(app_id, api_key, verify, host, version)

    # /tasks

    def task(self, task_id):
        return Task(self.helper, task_id)

    # /networks

    def public_networks(self):
        return NetworkList(self.helper, True)

    def networks(self):
        return NetworkList(self.helper, False)

    def network(self, network_id):
        return Network(self.helper, network_id)

    # /recognition

    def public_recognition_specs(self):
        return RecognitionSpecList(self.helper, True)

    def recognition_specs(self):
        return RecognitionSpecList(self.helper, False)

    def recognition_spec(self, spec_id):
        return RecognitionSpec(self.helper, spec_id)

    def recognition_versions(self):
        return RecognitionVersionList(self.helper)

    def recognition_version(self, version_id):
        return RecognitionVersion(self.helper, version_id)



