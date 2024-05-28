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


import functools
import logging

from deepomatic.api.exceptions import (TaskError, TaskTimeout, HTTPRetryError,
                                       TaskRetryError, DeepomaticException)
from deepomatic.api.mixins import ListableResource
from deepomatic.api.resource import Resource
from deepomatic.api.utils import retry, warn_on_http_retry_error
from tenacity import (RetryError, retry_if_exception_type, retry_if_result,
                      stop_after_delay, wait_chain, wait_fixed, stop_never,
                      wait_random_exponential)

logger = logging.getLogger(__name__)


###############################################################################


def is_pending_status(status):
    return status == 'pending'


def is_error_status(status):
    return status == 'error'


def is_success_status(status):
    return status == 'success'


def has_pending_tasks(pending_tasks):
    return len(pending_tasks) > 0


def retry_get_tasks(apply_func, retry_if, timeout=60,
                    wait_exp_multiplier=0.05, wait_exp_max=1.0):
    if timeout is None:
        stop = stop_never
    else:
        stop = stop_after_delay(timeout)

    wait = wait_chain(wait_fixed(0.05),
                      wait_fixed(0.1) + wait_random_exponential(multiplier=wait_exp_multiplier,
                                                                max=min(timeout, wait_exp_max)))
    return retry(apply_func, retry_if, wait, stop, retry_error_cls=TaskRetryError)


class Task(ListableResource, Resource):
    base_uri = '/tasks/'

    def list(self, task_ids):
        """
        Returns a list of tasks
        """
        assert(isinstance(task_ids, list))
        return super(Task, self).list(task_ids=task_ids)

    def wait(self, **retry_kwargs):
        """
        Wait until task is completed. Expires after 'timeout' seconds.
        """
        try:
            retry_get_tasks(self._refresh_status,
                            retry_if_exception_type(HTTPRetryError)
                            | retry_if_result(is_pending_status),
                            **retry_kwargs)
        except TaskRetryError as retry_error:
            raise TaskTimeout(self._data, retry_error)

        if is_error_status(self._data['status']):
            raise TaskError(self._data)

        return self

    def _refresh_status(self):
        logger.debug("Refreshing Task {}".format(self))
        warn_on_http_retry_error(self.refresh, suffix="Retrying until Task.wait timeouts.", reraise=True)
        return self._data['status']

    def _refresh_tasks_status(self, pending_tasks, success_tasks, error_tasks, positions):
        logger.debug("Refreshing batch of Task {}".format(pending_tasks))
        task_ids = [task.pk for idx, task in pending_tasks]
        functor = functools.partial(self.list, task_ids=task_ids)
        refreshed_tasks = warn_on_http_retry_error(functor, suffix="Retrying until Task.batch_wait timeouts.", reraise=True)

        pending_tasks[:] = []  # clear the list (we have to keep the reference)
        for task in refreshed_tasks:
            status = task['status']
            pos = positions[task.pk]

            if is_pending_status(status):
                pending_tasks.append((pos, task))
            elif is_error_status(status):
                error_tasks.append((pos, task))
            elif is_success_status(status):
                success_tasks.append((pos, task))
            else:
                raise DeepomaticException("Unknown task status %s" % status)

        return pending_tasks

    def batch_wait(self, tasks, **retry_kwargs):
        """
        Wait until a list of task are completed. Expires after 'timeout' seconds.

        Returns a tuple of list (pending_tasks, success_tasks, error_tasks).
        Each list contains a couple (original_position, task) sorted by original_position asc
        original_position gives the original index in the input tasks list parameter. This helps to keep the order.
        """
        retry_kwargs['timeout'] = retry_kwargs.get('timeout', 300)
        try:
            positions = {}
            pending_tasks = []
            for pos, task in enumerate(tasks):
                positions[task.pk] = pos
                pending_tasks.append((pos, task))
            success_tasks = []
            error_tasks = []

            functor = functools.partial(self._refresh_tasks_status, pending_tasks,
                                        success_tasks, error_tasks, positions)
            retry_get_tasks(functor, retry_if_result(has_pending_tasks), **retry_kwargs)

        except RetryError:
            pass

        return (sorted(pending_tasks, key=lambda v: v[0]),
                sorted(success_tasks, key=lambda v: v[0]),
                sorted(error_tasks, key=lambda v: v[0]))


###############################################################################
