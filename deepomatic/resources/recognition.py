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

from six import string_types

from deepomatic.core.resource import Resource
import deepomatic.core.helpers as helpers
import deepomatic.core.mixins as mixins
from deepomatic.core.mixins import RequiredArg, OptionnalArg, ImmutableArg, EditOnlyArg


###############################################################################

class RecognitionSpec(mixins.Get,
                      mixins.Edit,
                      mixins.Delete,
                      mixins.Create,
                      mixins.List,
                      helpers.Inference,
                      Resource):
    """
    This is an helper to manipulate a 'Network' object.
    """
    object_template = {
        'name':        RequiredArg(),

        'description': OptionnalArg(),
        'metadata':    OptionnalArg(),

        'outputs':     ImmutableArg(),

        'current_version_id': EditOnlyArg()
    }

    object_functions = ['versions', 'inference']

    def get_base_uri(self):
        is_public = isinstance(self._pk, string_types) or self._read_only
        return '/recognition/public/' if is_public else '/recognition/specs/'

    def versions(self):
        if self._read_only:
            raise Exception("You cannot call 'versions' on a public recognition spec")
        return RecognitionVersion.as_list_of_resources(self._helper, self._get_pk(), read_only=True)


###############################################################################

class RecognitionVersion(mixins.Get,
                         mixins.Delete,
                         mixins.Create,
                         mixins.List,
                         helpers.Inference,
                         Resource):
    """
    This is an helper to manipulate a 'Network' object.
    """

    object_template = {
        'spec_id':          RequiredArg(),
        'network_id':       RequiredArg(),
        'post_processings': RequiredArg(),
    }

    def get_base_uri(self):
        is_bound_to_spec = hasattr(self, '_spec_id') and self._spec_id is not None
        if is_bound_to_spec:
            return '/recognition/specs/{spec_id}/versions'.format(spec_id=self._spec_id)
        else:
            return '/recognition/versions/'
        return '/recognition/public/' if is_bound_to_spec else '/recognition/specs/'

    @classmethod
    def as_list_of_resources(cls, helper, spec_id=None, read_only=False):
        resource = super(RecognitionVersion, cls).as_list_of_resources(helper, read_only=read_only)
        resource._spec_id = spec_id
        return resource
