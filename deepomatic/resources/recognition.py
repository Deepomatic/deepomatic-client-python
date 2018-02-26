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

from deepomatic.core.resource import Empty, ResourceList, ResourceObject, ResourceGetMixin, ResourceDeleteMixin, Resource
from deepomatic.core.helpers import ResourceInferenceMixin


###############################################################################

class RecognitionSpecList(ResourceList):
    """
    This is an helper to access the 'Network' resources.
    """
    def __init__(self, helper, is_public):
        if is_public:
            uri = '/recognition/public'
        else:
            uri = '/recognition/specs'
        super(RecognitionSpecList, self).__init__(helper, uri, is_public)

    def add(self, name, outputs, description=Empty(), metadata=Empty()):
        data = {
            'name': name,
            'description': description,
            'metadata': metadata,
            'outputs': outputs
        }
        return super(RecognitionSpecList, self).add(data=data)


###############################################################################

class RecognitionSpec(ResourceInferenceMixin, ResourceObject):
    """
    This is an helper to manipulate a 'Network' object.
    """
    def __init__(self, helper, spec_id):
        is_public = isinstance(spec_id, string_types)
        if is_public:
            uri = '/recognition/public/{spec_id}'
        else:
            uri = '/recognition/specs/{spec_id}'
        uri = uri.format(spec_id=spec_id)
        self._spec_id = spec_id
        super(RecognitionSpec, self).__init__(helper, uri, is_public)

    def edit(self, name=Empty(), description=Empty(), metadata=Empty(), current_version_id=Empty()):
        data = {
            'name': name,
            'description': description,
            'metadata': metadata,
            'current_version_id': current_version_id
        }
        return super(RecognitionSpec, self).edit(data=data)

    def versions(self):
        return RecognitionVersionList(self._helper, self._spec_id)

    def inference(self, inputs, show_discarded=False, max_predictions=100, return_task=False):
        data = {
            'show_discarded': show_discarded,
            'max_predictions': max_predictions,
        }
        return super(RecognitionSpec, self).inference(inputs, data, return_task)


###############################################################################

class RecognitionVersionList(ResourceList):
    """
    This is an helper to access the 'Network' resources.
    """
    def __init__(self, helper, spec_id=None):
        if spec_id is None:
            uri = '/recognition/versions'
        else:
            uri = '/recognition/specs/{spec_id}/versions'.format(spec_id=spec_id)
        super(RecognitionSpecList, self).__init__(helper, uri)

    def add(self, spec_id, network_id, post_processings):
        data = {
            'spec_id': spec_id,
            'network_id': network_id,
            'post_processings': post_processings
        }
        return super(RecognitionVersionList, self).add(data=data)


###############################################################################

class RecognitionVersion(ResourceInferenceMixin, ResourceGetMixin, ResourceDeleteMixin, Resource):
    """
    This is an helper to manipulate a 'Network' object.
    """
    def __init__(self, helper, version_id):
        uri = '/recognition/versions/{version_id}'.format(version_id=version_id)
        super(RecognitionVersion, self).__init__(helper, uri)

    def inference(self, inputs, show_discarded=False, max_predictions=100, return_task=False):
        data = {
            'show_discarded': show_discarded,
            'max_predictions': max_predictions,
        }
        return super(RecognitionVersion, self).inference(inputs, data, return_task)

