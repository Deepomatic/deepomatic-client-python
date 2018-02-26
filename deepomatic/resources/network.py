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

from deepomatic.core.resource import Empty, ResourceList, ResourceObject
from deepomatic.core.helpers import ResourceInferenceMixin, get_data_from_taked_promise


###############################################################################

class NetworkList(ResourceList):
    """
    This is an helper to access the 'Network' resources.
    """
    def __init__(self, helper, is_public):
        if is_public:
            uri = '/networks/public'
        else:
            uri = '/networks'
        super(NetworkList, self).__init__(helper, uri, is_public)

    def add(self, name, framework, preprocessing, files, description=Empty(), metadata=Empty(), return_task=False):
        data = {
            'name': name,
            'description': description,
            'metadata': metadata,
            'framework': framework,
            'preprocessing': preprocessing
        }
        return super(NetworkList, self).add(data=data, files=files)


###############################################################################

class Network(ResourceInferenceMixin, ResourceObject):
    """
    This is an helper to manipulate a 'Network' object.
    """
    def __init__(self, helper, network_id):
        is_public = isinstance(network_id, string_types)
        if is_public:
            uri = '/networks/public/{network_id}'
        else:
            uri = '/networks/{network_id}'
        uri = uri.format(network_id=network_id)
        super(Network, self).__init__(helper, uri, is_public)

    def edit(self, name=Empty(), description=Empty(), metadata=Empty()):
        data = {
            'name': name,
            'description': description,
            'metadata': metadata
        }
        return super(Network, self).edit(data=data)

    def inference(self, inputs, output_layers, return_task=False):
        return super(Network, self).inference(inputs, {"output_layers": output_layers}, return_task)

