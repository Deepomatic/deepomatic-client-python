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

import json
from tenacity import RetryError


###############################################################################

class DeepomaticException(Exception):
    def __init__(self, msg):
        super(DeepomaticException, self).__init__(msg)

###############################################################################


class CredentialsNotFound(DeepomaticException):
    pass


###############################################################################

class UnimplementedException(DeepomaticException):
    def __init__(self, msg):
        super(UnimplementedException, self).__init__(msg)


###############################################################################

class NoData(DeepomaticException):
    def __init__(self):
        super(NoData, self).__init__("No data !! You may need to call '.retrieve()' ?")


###############################################################################

class BadStatus(DeepomaticException):
    """
    Thrown when HTTP response status_code < 200 or status_code >= 300.
    """
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


class ClientError(BadStatus):
    """
    Thrown when HTTP response status_code is a 4xx.
    The client sent a bad request.
    """
    pass


class ServerError(BadStatus):
    """
    Thrown when HTTP response status_code is a 5xx.
    The request seems to be valid but the server couldn't handle it for some reason.
    """
    pass


###############################################################################

class TaskError(DeepomaticException):
    def __init__(self, task):
        self.task = task

    def __str__(self):
        return "Error on task: {}".format(json.dumps(self.task))

    def get_task_id(self):
        return self.task['id']


###############################################################################

class TaskTimeout(DeepomaticException):
    def __init__(self, task, retry_error=None):
        self.task = task
        self.retry_error = retry_error

    def __str__(self):
        return "Timeout on task: {}".format(json.dumps(self.task))

    def get_task_id(self):
        return self.task['id']


###############################################################################


class HTTPRetryError(RetryError):
    pass


class TaskRetryError(RetryError):
    pass
