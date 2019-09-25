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
from deepomatic.api.http_helper import RequestsTimeout
from deepomatic.api.inference import InferenceResource
from deepomatic.api.mixins import (CreateableResource, DeletableResource,
                                   ImmutableArg, ListableResource,
                                   OptionnalArg, RequiredArg,
                                   UpdatableResource)
from deepomatic.api.resource import Resource
from six import string_types

###############################################################################


class Network(ListableResource,
              CreateableResource,
              UpdatableResource,
              DeletableResource,
              InferenceResource,
              Resource):
    """
    This is an helper to manipulate a 'Network' object.
    """
    object_template = {
        'name': RequiredArg(),
        'description': OptionnalArg(),
        'metadata': OptionnalArg(),
        'framework': ImmutableArg(),
        'preprocessing': ImmutableArg(),
        'postprocessings': OptionnalArg(mutable=False),
    }

    @classmethod
    def get_base_uri(self, pk, public=False, **kwargs):
        public = public or isinstance(pk, string_types)
        return '/networks/public/' if public else '/networks/'

    def inference(self, convert_to_numpy=True, return_task=False, **kwargs):
        if convert_to_numpy:
            return_task = False
        result = super(Network, self).inference(return_task=return_task, **kwargs)

        if convert_to_numpy:
            return self._convert_result_to_numpy(result)
        else:
            return result

    def create(self, *args, **kwargs):
        # No retry on Network.create() errors by default as this is a large request
        kwargs['http_retry'] = kwargs.get('http_retry', None)
        kwargs['timeout'] = kwargs.get('timeout', RequestsTimeout.SLOW)
        return super(Network, self).create(*args, **kwargs)

    @staticmethod
    def _convert_result_to_numpy(result):
        new_result = {}
        for tensor in result['tensors']:
            new_result[tensor['name']] = np.array(tensor['data']).reshape(tensor['dims'])
        return new_result
