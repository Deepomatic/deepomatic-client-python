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

import json
import copy

from deepomatic.api.exceptions import DeepomaticException, NoData


###############################################################################

class Resource(object):
    # Specify this template to define the list of arguments to create an object
    object_template = {}

    # Specify this for your resource, it must be the base resource URI (without ID)
    base_uri = None

    # Alternatively, you can implement `get_base_uri(pk, **kwargs)` to dynamically return the URI
    # The `kwargs` is any additionnal argument you pass to the `.list()` method
    @classmethod
    def get_base_uri(self, pk, **kwargs):
        raise DeepomaticException('Unimplemented')

    def retrieve(self, pk):
        return self.__class__(self._helper, pk=pk)

    def refresh(self):
        assert(self._pk is not None)
        self._data = self._helper.get(self._uri(pk=self._pk))
        return self

    def data(self, no_raise=False, no_refresh=False):
        if self._data is None:
            if self._pk is None:
                if no_raise:
                    return None
                else:
                    raise NoData()
            else:
                if not no_refresh:
                    self.refresh()
        return self._data

    @property
    def pk(self):
        return self._pk

    def __init__(self, helper, pk=None, data=None):
        self._helper = helper
        self._pk = pk
        self._data = data

    def __getitem__(self, key):
        return self.data()[key]

    def __repr__(self):
        pk = 'id={pk} '.format(pk=self._pk) if self._pk else ''
        string = '<{classname} object {pk}at {addr}>'.format(classname=self.__class__.__name__, pk=pk, addr=hex(id(self)))
        if self._data is not None:
            string += ' JSON: ' + json.dumps(self._data)
        return string

    @classmethod
    def _uri(cls, pk=None, suffix=None, **kwargs):
        base_uri = cls.base_uri
        if base_uri is None:
            base_uri = cls.get_base_uri(pk=pk, **kwargs)

        if not base_uri.endswith('/'):
            base_uri += '/'

        if pk is not None:
            base_uri += str(pk) + '/'

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

    def __init__(self, resource_class, helper, uri, offset=None, limit=None, **kwargs):
        params = copy.deepcopy(kwargs)
        if offset is not None:
            params['offset'] = offset
        if limit is not None:
            params['limit'] = limit
        data = helper.get(uri, params=params)
        super(ResourceList, self).__init__(helper, data=data)
        self._resource_class = resource_class

    def __iter__(self):
        results = self['results']
        next_results = self.next()

        while True:
            for resource in results:
                yield self._resource_class(self._helper, resource['id'], resource)
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

    def _handle_prev_next(self, uri):
        if uri is None:
            return None
        else:
            return ResourceList(self._resource_class, self._helper, uri)
