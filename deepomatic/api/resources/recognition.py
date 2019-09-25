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

from deepomatic.api.resource import Resource, ResourceList
from deepomatic.api.inference import InferenceResource
from deepomatic.api.mixins import CreateableResource, ListableResource, UpdatableResource, DeletableResource
from deepomatic.api.mixins import RequiredArg, OptionnalArg, ImmutableArg, UpdateOnlyArg


###############################################################################

class RecognitionSpec(ListableResource,
                      CreateableResource,
                      UpdatableResource,
                      DeletableResource,
                      InferenceResource,
                      Resource):
    """
    This is an helper to manipulate a 'Recognition Specification' object.
    """
    object_template = {
        'name': RequiredArg(),
        'description': OptionnalArg(),
        'metadata': OptionnalArg(),
        'outputs': ImmutableArg(),
        'current_version_id': UpdateOnlyArg()
    }

    @classmethod
    def get_base_uri(cls, pk, public=False, **kwargs):
        public = public or isinstance(pk, string_types)
        return '/recognition/public/' if public else '/recognition/specs/'

    def versions(self, offset=0, limit=100):
        assert(self._pk is not None)
        return ResourceList(RecognitionVersion, self._helper, self._uri(pk=self._pk, suffix='versions'), offset, limit)


###############################################################################

class RecognitionVersion(CreateableResource,
                         DeletableResource,
                         ListableResource,
                         InferenceResource,
                         Resource):
    """
    This is an helper to manipulate a 'Network' object.
    """
    base_uri = '/recognition/versions/'

    object_template = {
        'spec_id': RequiredArg(),
        'network_id': RequiredArg(),
        'post_processings': RequiredArg(),
    }
