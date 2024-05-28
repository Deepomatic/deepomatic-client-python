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
from deepomatic.api.resource import ResourceList


###############################################################################

class Arg(object):
    def __init__(self, required, mutable):
        self._shoud_be_present_when_adding = required
        self._mutable = mutable


class RequiredArg(Arg):
    def __init__(self, mutable=True):
        super(RequiredArg, self).__init__(True, mutable)


class OptionnalArg(Arg):
    def __init__(self, mutable=True):
        super(OptionnalArg, self).__init__(None, mutable)


class ImmutableArg(Arg):
    def __init__(self):
        super(ImmutableArg, self).__init__(True, False)


class UpdateOnlyArg(Arg):
    def __init__(self):
        super(UpdateOnlyArg, self).__init__(False, True)


###############################################################################

class UpdatableResource(object):
    def update(self, replace=False, content_type='application/json', files=None, **kwargs):
        assert(self._pk is not None)

        if self._helper.check_query_parameters:
            for arg_name in kwargs:
                if arg_name not in self.object_template:
                    raise DeepomaticException("Unexpected keyword argument: " + arg_name)
            for arg_name, arg in self.object_template.items():
                if not arg._mutable and arg_name in kwargs:
                    raise DeepomaticException("Immutable keyword argument: " + arg_name)

        if replace:
            self._data = self._helper.put(self._uri(pk=self._pk), data=kwargs, content_type=content_type, files=files)
        else:
            self._data = self._helper.patch(self._uri(pk=self._pk), data=kwargs, content_type=content_type, files=files)


###############################################################################

class DeletableResource(object):
    def delete(self):
        assert(self._pk is not None)
        return self._helper.delete(self._uri(pk=self._pk))


###############################################################################

class CreateableResource(object):
    def create(self, content_type='application/json', files=None, **kwargs):
        post_kwargs = {}
        # TODO: this is a hack, kwargs shouldn't be the data to post
        # it should be the requests kwargs
        # the fix will be a breaking change, so for now we just pop them
        for key in ['http_retry', 'timeout']:
            try:
                post_kwargs[key] = kwargs.pop(key)
            except KeyError:
                pass

        if self._helper.check_query_parameters:
            for arg_name in kwargs:
                if arg_name not in self.object_template or self.object_template[arg_name]._shoud_be_present_when_adding is False:
                    raise DeepomaticException("Unexpected keyword argument: " + arg_name)
            for arg_name, arg in self.object_template.items():
                if arg._shoud_be_present_when_adding and arg_name not in kwargs:
                    raise DeepomaticException("Missing keyword argument: " + arg_name)

        if files is not None:
            content_type = 'multipart/mixed'

        data = self._helper.post(self._uri(), data=kwargs,
                                 content_type=content_type,
                                 files=files, **post_kwargs)
        return self.__class__(self._helper, pk=data['id'], data=data)


###############################################################################

class ListableResource(object):
    def list(self, offset=0, limit=100, **kwargs):
        return ResourceList(self.__class__, self._helper, self._uri(**kwargs), offset, limit, **kwargs)


###############################################################################
