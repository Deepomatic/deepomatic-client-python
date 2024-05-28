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

import sys
import copy
import base64

from deepomatic.api.exceptions import DeepomaticException


###############################################################################

def format_inputs(inputs, data):
    assert(isinstance(inputs, list))

    data = copy.deepcopy(data)
    files = {}
    need_multipart = any([input_data.need_multipart() for input_data in inputs])
    inputs_data = [input_data.get_input() for input_data in inputs]
    if need_multipart:
        files['inputs'] = inputs_data
    else:
        data['inputs'] = inputs_data

    content_type = 'multipart/mixed' if need_multipart else 'application/json'
    return content_type, data, files


###############################################################################

class AbstractInput(object):
    """
    Do not instantiate this class directly, use type specific classes instead
    """
    supported_protocols = ['http://', 'https://']
    supported_encodings = ['binary', 'base64']

    def __init__(self, source, encoding=None):
        is_file = hasattr(source, 'read')
        is_raw = False
        if not is_file:
            is_raw = ((sys.version_info >= (3, 0) and isinstance(source, bytes))
                      or not any([source.startswith(p) for p in self.supported_protocols]))
            if is_raw:
                if encoding is None:
                    raise DeepomaticException("You must specify 'encoding' when passing raw data")
                if encoding not in self.supported_encodings:
                    raise DeepomaticException("Unknown 'encoding' type.")

                # Send binary directly to minimize load
                if encoding == 'base64':
                    source = base64.b64decode(source)
                    encoding = 'binary'

        self._source = source
        self._need_multipart = is_file or (is_raw and encoding == 'binary')

    def get_input(self):
        raise NotImplementedError()

    def need_multipart(self):
        return self._need_multipart


###############################################################################

class ImageInput(AbstractInput):
    content_type = r'image/*'
    key = u'image'

    def __init__(self, source, encoding=None, bbox=None, polygon=None, crop_uniform_background=False):
        super(ImageInput, self).__init__(source, encoding)
        self.bbox = bbox
        self.polygon = polygon
        self.crop_uniform_background = crop_uniform_background

    def get_input(self):
        image = {
            'source': self._source,
            'crop_uniform_background': self.crop_uniform_background
        }
        if self.bbox is not None:
            image['bbox'] = self.bbox
        if self.polygon is not None:
            image['polygon'] = self.polygon
        return {
            'image': image
        }


###############################################################################
