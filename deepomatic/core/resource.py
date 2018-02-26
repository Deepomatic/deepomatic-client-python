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

from deepomatic.core.result import Result, ResultList
from deepomatic.core.exceptions import DeepomaticException


###############################################################################

class Empty(object):
    pass


def filter_empty(data):
    if data is not None:
        return dict(filter(lambda x: not isinstance(x[1], Empty), data.items()))
    return None


###############################################################################

class Resource(object):
    def __init__(self, helper, uri, read_only=False):
        self._helper = helper
        self._uri = uri
        self._read_only = read_only

    def _make_uri(self, suffix):
        if suffix is None:
            return self._uri
        else:
            return self._uri + suffix

    def _get(self, suffix=None, *args, **kwargs):
        return Result(self._helper.get(self._make_uri(suffix), *args, **kwargs))

    def _delete(self, suffix=None, *args, **kwargs):
        return Result(self._helper.delete(self._make_uri(suffix), *args, **kwargs))

    def _post(self, suffix=None, *args, **kwargs):
        return Result(self._helper.post(self._make_uri(suffix), *args, **kwargs))

    def _put(self, suffix=None, *args, **kwargs):
        return Result(self._helper.put(self._make_uri(suffix), *args, **kwargs))

    def _patch(self, suffix=None, *args, **kwargs):
        return Result(self._helper.patch(self._make_uri(suffix), *args, **kwargs))


###############################################################################

class AddResultResource(Result, Resource):
    def __init__(self, promise, helper, uri_root):
        super(AddResultResource, self).__init__(promise)
        self._helper = helper
        if not uri_root.endswith('/'):
            uri_root += '/'
        self._uri_root = uri_root

    @property
    def _uri(self):
        obj = self._promise.get()
        return self._uri_root + obj['id']


###############################################################################

class ResourceGetMixin(object):
    def get(self):
        return self._get()


###############################################################################

class ResourceEditMixin(object):
    def edit(self, replace=False, params=None, data=None, content_type='application/json', files=None):
        if self._read_only:
            raise DeepomaticException("You cannot modify this resource")
        data = filter_empty(data)
        files = filter_empty(files)
        if replace:
            return self._put(params=params, data=data, content_type=content_type, files=files)
        else:
            return self._patch(params=params, data=data, content_type=content_type, files=files)


###############################################################################

class ResourceDeleteMixin(object):
    def delete(self):
        if self._read_only:
            raise DeepomaticException("You cannot delete this resource")
        return self._delete()


###############################################################################

class ResourceAddMixin(object):
    def add(self, params=None, data=None, content_type='application/json', files=None):
        if self._read_only:
            raise DeepomaticException("You cannot create such resource")
        data = filter_empty(data)
        files = filter_empty(files)
        if files is not None:
            content_type = 'multipart/mixed'
        promise = self._post(params=params, data=data, content_type=content_type, files=files)
        return AddResultResource(promise, self._helper, self._uri)


###############################################################################

class ResourceListMixin(object):
    def list(self, offset=0, limit=None):
        return ResultList(self._helper, self._uri, offset, limit)


###############################################################################


class ResourceObject(ResourceGetMixin,
                     ResourceEditMixin,
                     ResourceDeleteMixin,
                     Resource):
    pass


class ResourceList(ResourceAddMixin,
                   ResourceListMixin,
                   Resource):
    pass


###############################################################################

