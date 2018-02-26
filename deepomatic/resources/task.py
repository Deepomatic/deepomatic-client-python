# -*- coding: utf-8 -*-
"""
Copyright (c) 2017 Deepomatic SAS
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

from deepomatic.core.resource import Resource, ResourceGetMixin
from deepomatic.core.result import TaskResult, TaskDataResult


###############################################################################

class Task(ResourceGetMixin, Resource):
    def __init__(self, helper, task_id):
        uri = '/tasks/{task_id}'.format(task_id=task_id)
        super(Task, self).__init__(helper, uri, True)

    def wait(self):
        return TaskResult(self._helper, self._uri)

    def wait_data(self):
        return TaskDataResult(self._helper, self._uri)

###############################################################################
