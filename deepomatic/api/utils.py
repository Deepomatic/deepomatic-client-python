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

import logging

from deepomatic.api.exceptions import HTTPRetryError
from tenacity import (Retrying, after_log, before_log)

logger = logging.getLogger(__name__)


def retry(apply_func, retry_if, wait, stop, **kwargs):
    retryer = Retrying(retry=retry_if,
                       wait=wait,
                       stop=stop,
                       before=before_log(logger, logging.DEBUG),
                       after=after_log(logger, logging.DEBUG),
                       **kwargs)
    return retryer(apply_func)


def warn_on_http_retry_error(http_func, suffix='', reraise=True):
    # http helper can raise a HTTPRetryError
    try:
        # this should be an http_helper call
        return http_func()
    except HTTPRetryError as e:
        last_attempt = e.last_attempt
        last_exception = last_attempt.exception(timeout=0)
        msg = "HTTPHelper failed to refresh task status. In the last attempt, "
        if last_exception is None:
            last_response = last_attempt.result()
            msg += 'the status code was {}.'.format(last_response.status_code)
        else:
            msg += 'an exception occured: {}.'.format(last_exception)
        if suffix:
            msg += ' ' + suffix
        logger.warning(msg)
        if reraise:
            raise
        return None
