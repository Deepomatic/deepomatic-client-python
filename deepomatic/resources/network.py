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

import numpy as np

from deepomatic.core.resource import Resource
from deepomatic.core.utils import InferenceResource
from deepomatic.core.mixins import CreateableResource, ListableResource, UpdatableResource, DeletableResource
from deepomatic.core.mixins import RequiredArg, OptionnalArg, ImmutableArg


###############################################################################

class PublicNetwork(ListableResource,
                    InferenceResource,
                    Resource):
    """
    This is an helper to manipulate a public 'Network' object.
    """
    base_uri = '/networks/public/'

    def inference(self, convert_to_numpy=True, return_task=False, **kwargs):
        if convert_to_numpy:
            return_task = False
        result = super(PublicNetwork, self).inference(return_task=return_task, **kwargs)

        if convert_to_numpy:
            return self._convert_result_to_numpy(result)
        else:
            return result

    @staticmethod
    def _convert_result_to_numpy(result):
        new_result = {}
        for tensor in result['tensors']:
            new_result[tensor['name']] = np.array(tensor['data']).reshape(tensor['dims'])
        return new_result


###############################################################################

class Network(CreateableResource,
              UpdatableResource,
              DeletableResource,
              PublicNetwork):
    """
    This is an helper to manipulate a 'Network' object.
    """
    base_uri = '/networks/'

    object_template = {
        'name':          RequiredArg(),
        'description':   OptionnalArg(),
        'metadata':      OptionnalArg(),
        'framework':     ImmutableArg(),
        'preprocessing': ImmutableArg(),
    }


