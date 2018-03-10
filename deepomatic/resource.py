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

from deepomatic.exceptions import DeepomaticException, NoData

import json
import sys
if sys.version_info >= (3, 0):
    import urllib.parse as urlparse
else:
    import urlparse


###############################################################################

class Resource(object):
    # Specify this template to define the list of arguments to create an object
    object_template = {}

    # Specify this for your resource, it must be the base resource URI (without ID)
    base_uri = None

    # Alternatively, you can implement get_base_uri(pk) to dynamically return the URI
    def get_base_uri(self, pk=None):
        raise DeepomaticException('Unimplemented')

    def retrieve(self, pk):
        result = self.__class__(self._helper, pk=pk)
        return result.refresh()

    def refresh(self):
        assert(self._pk is not None)
        self._data = self._helper.get(self._uri())
        return self

    def data(self, no_raise=False):
        if self._data is None:
            if self._pk is None:
                if no_raise:
                    return None
                else:
                    raise NoData()
            else:
                self.refresh()
        return self._data

    def __init__(self, helper, pk=None, data=None):
        self._helper = helper
        self._pk = pk
        self._data = data

    def __getitem__(self, key):
        return self.data()[key]

    def __str__(self):
        pk = 'id={pk} '.format(pk=self._pk) if self._pk else ''
        string = '<{classname} object {pk}at {addr}>'.format(classname=self.__class__.__name__, pk=pk, addr=hex(id(self)))
        if self.data() is not None:
            string += ' JSON: ' + json.dumps(self.data(), indent=4, separators=(',', ': '))
        return string

    def _uri(self, suffix=None):
        base_uri = self.base_uri
        if base_uri is None:
            base_uri = self.get_base_uri()

        if not base_uri.endswith('/'):
            base_uri += '/'

        if self._pk is not None:
            base_uri += str(self._pk) + '/'

        if suffix is None:
            return base_uri
        else:
            if suffix.startswith('/'):
                suffix = suffix[1:]
            return base_uri + suffix


###############################################################################

class ResourceList(Resource):
    """
    This is an helper to access a resource list.
    """
    def __init__(self, helper, uri, offset, limit):
        params = {'offset': offset, 'limit': limit}
        super(ResourceList, self).__init__(helper, data=helper.get(uri, params))

    def __iter__(self):
        results = self['results']
        next_results = self.next()

        while True:
            for r in results:
                yield r
            if next_results is None:
                break
            results = next_results['results']
            next_results = next_results.next()

    def count(self):
        return self['count']

    def next(self):
        return self._handle_prev_next(self['next'])

    def prev(self):
        return self._handle_prev_next(self['prev'])

    def _handle_prev_next(self, url):
        if url is None:
            return None
        else:
            o = urlparse.urlparse(url)
            params = urlparse.parse_qs(o.query)
            offset = params.get('offset', 0)
            limit = params.get('limit', 100)
            uri = urlparse.urlunparse(o.scheme, o.netloc, o.path, o.params, '', o.fragment)
            return ResourceList(self.helper, uri, offset, limit)
