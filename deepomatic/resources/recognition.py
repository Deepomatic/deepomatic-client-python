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

from deepomatic.core.resource import Resource
from deepomatic.core.utils import InferenceResource
from deepomatic.core.mixins import CreateableResource, ListableResource, UpdatableResource, DeletableResource
from deepomatic.core.mixins import RequiredArg, OptionnalArg, ImmutableArg, EditOnlyArg


###############################################################################

class PublicRecognitionSpec(ListableResource,
                            InferenceResource,
                            Resource):
    """
    This is an helper to manipulate a public 'Recognition Specification' object.
    """
    base_uri = '/recognition/public/'


###############################################################################

class RecognitionSpec(CreateableResource,
                      UpdatableResource,
                      DeletableResource,
                      PublicRecognitionSpec):
    """
    This is an helper to manipulate a 'Network' object.
    """
    base_uri = '/recognition/specs/'

    object_template = {
        'name':        RequiredArg(),
        'description': OptionnalArg(),
        'metadata':    OptionnalArg(),
        'outputs':     ImmutableArg(),
        'current_version_id': EditOnlyArg()
    }

    def versions(self):
        return RecognitionVersion(self._helper, spec_id=self._pk)


###############################################################################

class RecognitionVersion(CreateableResource,
                         DeletableResource,
                         ListableResource,
                         InferenceResource,
                         Resource):
    """
    This is an helper to manipulate a 'Network' object.
    """

    object_template = {
        'spec_id':          RequiredArg(),
        'network_id':       RequiredArg(),
        'post_processings': RequiredArg(),
    }

    def __init__(self, helper, spec_id=None, *args, **kwargs):
        super(RecognitionVersion, self).__init__(helper, *args, **kwargs)
        self._spec_id = spec_id

    def get_base_uri(self):
        is_bound_to_spec = self._pk is None and self._spec_id is not None
        if is_bound_to_spec:
            return '/recognition/specs/{spec_id}/versions'.format(spec_id=self._spec_id)
        else:
            return '/recognition/versions/'

