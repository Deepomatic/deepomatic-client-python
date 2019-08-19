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

from tenacity import (Retrying, after_log, before_log, stop_after_delay,
                      stop_never, wait_random_exponential)

logger = logging.getLogger(__name__)


def retry(apply_func, retry,
          timeout=60, wait_exp_multiplier=0.05, wait_exp_max=1.0):

    if timeout is None:
        stop = stop_never
    else:
        stop = stop_after_delay(timeout)

    retryer = Retrying(wait=wait_random_exponential(multiplier=wait_exp_multiplier,
                                                    max=wait_exp_max),
                       stop=stop,
                       retry=retry,
                       before=before_log(logger, logging.DEBUG),
                       after=after_log(logger, logging.DEBUG))
    return retryer(apply_func)
