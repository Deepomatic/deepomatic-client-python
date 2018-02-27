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

from deepomatic.exceptions import DeepomaticException
from deepomatic.core.result import Result


###############################################################################

class Resource(object):
    # Specify this template to define the list of arguments to create an object
    object_template = {}

    # Specify here the list of function accesible to an object resource:
    object_functions = []

    # Specify here the list of function accesible to an object set resource:
    object_set_functions = []

    # Specify this for your resource, it must be the base resource URI (without ID)
    base_uri = None

    # Alternatively, you can implement get_base_uri(pk) to dynamically return the URI
    def get_base_uri(self, pk=None):
        raise DeepomaticException('Unimplemented')

    def __init__(self, helper, pk=None, promise=None, read_only=False):
        self._helper = helper
        self._pk = pk
        self._promise = promise
        self._read_only = read_only

    def _uri(self, suffix=None):
        base_uri = self.base_uri
        if base_uri is None:
            base_uri = self.get_base_uri()

        if not base_uri.endswith('/'):
            base_uri += '/'

        pk = self._get_pk()
        if pk is not None:
            base_uri += str(pk) + '/'

        if suffix is None:
            return base_uri
        else:
            if suffix.startswith('/'):
                suffix = suffix[1:]
            return base_uri + suffix

    def _get_pk(self):
        if self._pk is not None:
            return self._pk
        elif self._promise is not None:
            obj = self._promise.result()
            return obj['id']
        return None

    def _get(self, suffix=None, *args, **kwargs):
        return Result(self._helper.get(self._uri(suffix), *args, **kwargs))

    def _delete(self, suffix=None, *args, **kwargs):
        return Result(self._helper.delete(self._uri(suffix), *args, **kwargs))

    def _post(self, suffix=None, *args, **kwargs):
        return Result(self._helper.post(self._uri(suffix), *args, **kwargs))

    def _put(self, suffix=None, *args, **kwargs):
        return Result(self._helper.put(self._uri(suffix), *args, **kwargs))

    def _patch(self, suffix=None, *args, **kwargs):
        return Result(self._helper.patch(self._uri(suffix), *args, **kwargs))

    @staticmethod
    def _forbidden_on_object(*args, **kwargs):
        raise DeepomaticException("You cannot call this method on this object resource.")

    @staticmethod
    def _forbidden_on_set(*args, **kwargs):
        raise DeepomaticException("You cannot call this method on this object set resource.")

    @classmethod
    def as_object_ressource(cls, helper, pk=None, promise=None, read_only=False):
        if pk is None and promise is None:
            raise DeepomaticException("Both pk and promise cannot be None.")

        resource = cls(helper, pk, promise, read_only=read_only)
        function_to_forbid = ['create', 'list'] + cls.object_set_functions
        if read_only:
            function_to_forbid += ['edit', 'delete']
        for attr in function_to_forbid:
            if hasattr(resource, attr):
                setattr(resource, attr, cls._forbidden_on_object)
        return resource

    @classmethod
    def as_set_ressource(cls, helper, read_only=False):
        resource = cls(helper, read_only=read_only)
        function_to_forbid = ['get', 'edit', 'delete'] + cls.object_functions
        if read_only:
            function_to_forbid = ['create']
        for attr in function_to_forbid:
            if hasattr(resource, attr):
                setattr(resource, attr, cls._forbidden_on_set)
        return resource

###############################################################################
