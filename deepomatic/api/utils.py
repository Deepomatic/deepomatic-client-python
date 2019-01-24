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

from deepomatic.api.exceptions import DeepomaticException
from deepomatic.api.resources.task import Task
from deepomatic.api.inputs import format_inputs


###############################################################################

class InferenceResource(object):
    def inference(self, return_task=False, wait_task=True, **kwargs):
        assert(self._pk is not None)

        inputs = kwargs.pop('inputs', None)
        if inputs is None:
            raise DeepomaticException("Missing keyword argument: inputs")
        content_type, data, files = format_inputs(inputs, kwargs)
        result = self._helper.post(self._uri(pk=self._pk, suffix='/inference'), content_type=content_type, data=data, files=files)
        task_id = result['task_id']
        task = Task(self._helper, pk=task_id)
        if wait_task:
            task.wait()

        if return_task:
            return task
        else:
            return task['data']


###############################################################################
