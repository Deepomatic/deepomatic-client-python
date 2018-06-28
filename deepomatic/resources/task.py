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
from tenacity import Retrying, wait_random_exponential, stop_after_delay, retry_if_result, before_log, after_log, RetryError

from deepomatic.resource import Resource
from deepomatic.mixins import ListableResource
from deepomatic.exceptions import TaskError, TaskTimeout
import logging


logger = logging.getLogger(__name__)


###############################################################################


def is_pending_status(status):
    return status == 'pending'


class Task(ListableResource, Resource):
    base_uri = '/tasks/'

    def list(self, task_ids):
        """
        Returns a list of tasks
        """
        assert(isinstance(task_ids, list))
        return super(Task, self).list(task_ids=task_ids)

    def wait(self, timeout=60, wait_exp_multiplier=0.1, wait_exp_max=1.0):
        """
        Wait until task is completed. Expires after 'timeout' seconds.
        """
        try:
            retryer = Retrying(wait=wait_random_exponential(multiplier=wait_exp_multiplier, max=wait_exp_max),
                               stop=stop_after_delay(timeout),
                               retry=retry_if_result(is_pending_status),
                               before=before_log(logger, logging.DEBUG),
                               after=after_log(logger, logging.DEBUG))
            retryer(self._refresh_status)
        except RetryError:
            if self['status'] == 'pending':
                raise TaskTimeout(self.data())
            elif self['status'] == 'error':
                raise TaskError(self.data())

        return self

    def _refresh_status(self):
        logger.debug("Refreshing Task {}".format(self))
        self.refresh()
        return self['status']


###############################################################################
