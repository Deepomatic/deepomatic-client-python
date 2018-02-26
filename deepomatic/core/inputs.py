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

import copy

from deepomatic.core.exceptions import DeepomaticException


###############################################################################

def format_inputs(inputs, data):
    if not isinstance(inputs, list):
        inputs = [inputs]

    data = copy.deepcopy(data)
    data['inputs'] = [input_data.get_input() for input_data in inputs]

    if any([input_data.is_file() for input_data in inputs]):
        def make_fields(prefix, obj, data, files):
            for key, value in obj.items():
                p = prefix + key
                if isinstance(value, dict):
                    make_fields(p, value, data, files)
                elif isinstance(value, list):
                    for i, v in enumerate(value):
                        make_fields(p + '[{}]'.format(i), v, data, files)
                else:
                    is_file = hasattr(value, 'read')
                    if is_file:
                        files[p] = value
                    else:
                        data[p] = value

        new_data = {}
        files = {}
        make_fields('', data, new_data, files)
        return None, new_data, files
    else:
        return 'application/json', data, None


###############################################################################

class AbstractInput(object):
    """
    Do not instantiate this class directly, use type specific classes instead
    """
    supported_protocols = ['http://', 'https://']
    supported_encodings = ['binary', 'base64']

    def __init__(self, source, encoding=None):
        self._is_file = hasattr(source, 'read')
        is_raw = not self._is_file and not any([source.startswith(p) for p in self.supported_protocols])
        if is_raw:
            if encoding is None:
                raise DeepomaticException("You must specify 'encoding' when passing raw data")
            if encoding not in self.supported_encodings:
                raise DeepomaticException("Unknown 'encoding' type.")

            prefix = 'data:{content_type};{encoding},'.format(
                content_type=self.content_type,
                encoding=encoding)
            source = prefix + source
        self._source = source

    def get_input(self):
        raise Exception("Unimplemented")

    def is_file(self):
        return self._is_file


###############################################################################

class ImageInput(AbstractInput):
    content_type = 'image/*'
    key = 'image'

    def __init__(self, source, encoding=None, bbox=None, polygon=None, crop_uniform_background=False):
        super(ImageInput, self).__init__(source, encoding)
        self.bbox = bbox
        self.polygon = polygon
        self.crop_uniform_background = crop_uniform_background

    def get_input(self):
        data = {
            'image': {
                'source': self._source,
                'crop_uniform_background': self.crop_uniform_background
            }
        }
        if self.bbox is not None:
            data['bbox'] = self.bbox
        if self.polygon is not None:
            data['polygon'] = self.polygon
        return data


###############################################################################

