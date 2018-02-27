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
from deepomatic.core.result import Result, ResultList


###############################################################################

class Arg(object):
    def __init__(self, required, mutable):
        self._shoud_be_present_when_adding = required
        self._mutable = mutable


class RequiredArg(Arg):
    def __init__(self, mutable=True):
        super(RequiredArg, self).__init__(True, mutable)


class OptionnalArg(Arg):
    def __init__(self):
        super(OptionnalArg, self).__init__(None, True)


class ImmutableArg(Arg):
    def __init__(self):
        super(ImmutableArg, self).__init__(True, False)


class EditOnlyArg(Arg):
    def __init__(self):
        super(EditOnlyArg, self).__init__(False, True)


###############################################################################

class Get(object):
    def get(self):
        return self._get()


###############################################################################

class Edit(object):
    def edit(self, replace=False, content_type='application/json', files=None, check_args=True, **kwargs):
        if check_args:
            for arg_name in kwargs:
                if arg_name not in self.object_template:
                    raise DeepomaticException("Unexpected keyword argument: " + arg_name)
            for arg_name, arg in self.object_template.items():
                if not arg._mutable and arg_name in kwargs:
                    raise DeepomaticException("Immutable keyword argument: " + arg_name)

        if replace:
            return self._put(data=kwargs, content_type=content_type, files=files)
        else:
            return self._patch(data=kwargs, content_type=content_type, files=files)


###############################################################################

class Delete(object):
    def delete(self):
        return self._delete()


###############################################################################

class Add(object):
    def add(self, content_type='application/json', files=None, check_args=True, **kwargs):
        if check_args:
            for arg_name in kwargs:
                if arg_name not in self.object_template or self.object_template[arg_name]._shoud_be_present_when_adding is False:
                    raise DeepomaticException("Unexpected keyword argument: " + arg_name)
            for arg_name, arg in self.object_template.items():
                if arg._shoud_be_present_when_adding and arg_name not in kwargs:
                    raise DeepomaticException("Missing keyword argument: " + arg_name)

        if files is not None:
            content_type = 'multipart/mixed'
        promise = self._post(data=kwargs, content_type=content_type, files=files)
        class AddResult(self.__class__, Result):
            pass
        return AddResult.as_object_ressource(self._helper, promise=promise, read_only=self._read_only)


###############################################################################

class List(object):
    def list(self, offset=0, limit=100):
        return ResultList(self._helper, self._uri(), offset, limit)


###############################################################################
