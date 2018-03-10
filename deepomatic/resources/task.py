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
import time

from deepomatic.resource import Resource
from deepomatic.mixins import ListableResource
from deepomatic.exceptions import TaskError, TaskTimeout


###############################################################################

class Task(ListableResource, Resource):
    base_uri = '/tasks/'

    def list(self, task_ids):
        """
        Returns a list of tasks
        """
        assert(isinstance(task_ids, list))
        return super(Task, self).list(task_ids=task_ids)

    def wait(self, timeout=60):
        """
        Wait until task is completed. Expires after 'timeout' seconds.
        """
        self._wait_result(timeout)
        return self

    def _wait_result(self, timeout):
        start_time = time.time()
        last_time = start_time
        sleep_time = 0.2
        while self['status'] == "pending":
            # Check for timeout
            if time.time() > start_time + timeout:
                raise TaskTimeout(self.data())

            # Wait 'sleep_time' second before re-querying
            sleep_time = time.time() - (last_time + sleep_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.refresh()

        if self['status'] == "error":
            raise TaskError(self.data())


###############################################################################
