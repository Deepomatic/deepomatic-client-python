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

import time
import urlparse

from deepomatic.core.exceptions import TaskError


###############################################################################

class Result(object):
    def __init__(self, promise):
        self._start_time = time.time()
        self._promise = promise

    def then(self, did_fulfill, did_reject=None):
        return self._promise.then(did_fulfill, did_reject)

    def result(self):
        def did_fulfill(result):
            return result

        def did_reject(result):
            if not isinstance(result, Exception):
                raise Exception("Unexpected error: result should be an Exception in can of error")
            raise result

        return self.then(did_fulfill, did_reject).get()


###############################################################################

class ResultList(Result):
    """
    This is an helper to access a resource list.
    """
    default_limit = 100

    def __init__(self, helper, uri, offset=0, limit=None):
        self._helper = helper
        params = {'offset': offset, 'limit': limit if limit is not None else self.default_limit}
        super(ResultList, self).__init__(promise=self._helper.get(uri, params))

    def __iter__(self):
        results = self.result()
        next_results = self.next()

        while True:
            for r in results:
                yield r
            if next_results is None:
                break
            results = next_results.results()
            next_results = next_results.next()

    def result(self):
        result = super(ResultList, self).result()
        return result['results']

    def count(self):
        result = super(ResultList, self).result()
        return result['count']

    def next(self):
        result = super(ResultList, self).result()
        return self._handle_prev_next(result['next'])

    def prev(self):
        result = super(ResultList, self).result()
        return self._handle_prev_next(result['prev'])

    def _handle_prev_next(self, url):
        if url is None:
            return None
        else:
            o = urlparse.urlparse(url)
            params = urlparse.parse_qs(o.query)
            offset = params.get('offset', 0)
            limit = params.get('limit', None)
            uri = urlparse.urlunparse(o.scheme, o.netloc, o.path, o.params, '', o.fragment)
            return ResultList(self.helper, uri, offset, limit)


###############################################################################

class TaskResult(Result):
    """
    This is an helper to wait for a task result.
    """
    def __init__(self, helper, uri):
        self._helper = helper
        self._uri = uri
        super(TaskResult, self).__init__(promise=self._helper.get(self._uri))

    def result(self):
        last_time = self._start_time
        while True:
            result = super(TaskResult, self).result()
            result = result['task']  # HACK until new deployment
            status = result['status']
            if status != "pending":
                if status == "error":
                    raise TaskError(result)
                return result

            # Wait 0.2s before re-querying
            sleep_time = time.time() - (last_time + 0.2)
            if sleep_time > 0:
                time.sleep(sleep_time)
            self._promise = self._helper.get(self._uri)


###############################################################################

class TaskDataResult(TaskResult):
    def result(self):
        result = super(TaskDataResult, self).result()
        return result['data']
