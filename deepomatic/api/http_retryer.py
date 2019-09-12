import functools

from deepomatic.api.utils import retry
from requests.exceptions import (ProxyError, RequestException,
                                 TooManyRedirects, URLRequired)
from tenacity import (retry_if_exception, retry_if_result, stop_after_delay,
                      wait_chain, wait_fixed, wait_random_exponential)

DEFAULT_REQUESTS_TIMEOUT = (3.05, 10)
DEFAULT_RETRY_EXP_MAX = 10.
DEFAULT_RETRY_EXP_MULTIPLIER = 0.5
DEFAULT_RETRY_STATUS_CODES = [502, 503, 504]
DEFAULT_RETRY_EXCEPTION_TYPES = (RequestException, )
DEFAULT_RETRY_EXCEPTION_TYPES_BLACKLIST = (ValueError, ProxyError, TooManyRedirects, URLRequired)


class retry_if_exception_type(retry_if_exception):
    def __predicate(self, e):
        return (isinstance(e, self.exception_types) and
                not isinstance(e, self.exception_types_blacklist))

    def __init__(self, exception_types=Exception,
                 exception_types_blacklist=()):
        self.exception_types = exception_types
        self.exception_types_blacklist = exception_types_blacklist
        super(retry_if_exception_type, self).__init__(self.__predicate)


class HTTPRetryer(object):
    """
           :param retry_if (optional): predicate to retry on requests errors.
               More details directly in tenacity source code:
                   - https://github.com/jd/tenacity/blob/1d05520276766d8c53fbb35b2b8368cc43a6c52c/tenacity/__init__.py#L179
                   - https://github.com/jd/tenacity/blob/1d05520276766d8c53fbb35b2b8368cc43a6c52c/tenacity/retry.py
               If not provided, the default behavior is:
                   - Retry on status code from DEFAULT_RETRY_STATUS_CODES
                   - Retry on exceptions from DEFAULT_RETRY_EXCEPTION_TYPES excluding those from DEFAULT_RETRY_EXCEPTION_TYPES_BLACKLIST
           :type retry_if: tenacity.retry_base
           :param wait (optional): how to wait between retry
               More details directly in tenacity source code https://github.com/jd/tenacity/blob/1d05520276766d8c53fbb35b2b8368cc43a6c52c/tenacity/wait.py

               if not provided, the default behavior is:
               ```
                   random_wait = wait_random_exponential(multiplier=DEFAULT_RETRY_EXP_MULTIPLIER,
                                                         max=DEFAULT_RETRY_EXP_MAX)
                   wait_chain(wait_fixed(0.05),
                              wait_fixed(0.1),
                              wait_fixed(0.1) + random_wait)
               ```
            :type wait: tenacity.wait_base
            :param stop (optional). Tell when to stop retrying. By default it stops retrying after a delay of 60 seconds. A last retry can be done just before this delay is reached, thus the total amount of elapsed time might be a bit higher. More details in tenacity source code https://github.com/jd/tenacity/blob/1d05520276766d8c53fbb35b2b8368cc43a6c52c/tenacity/stop.py
                Raises tenacity.RetryError when timeout is reached.
            :type timeout: tenacity.stop_base
            :param requests_timeout: timeout of each request. More details in the `requests` documentation: https://2.python-requests.org//en/master/user/advanced/#timeouts
            :param requests_timeout: float or tuple(float, float)

    """
    def __init__(self, retry_if=None, wait=None, stop=None,
                 requests_timeout=DEFAULT_REQUESTS_TIMEOUT):
        self.retry_status_code = {}
        self.retry_if = retry_if
        self.requests_timeout = requests_timeout
        self.wait = wait
        self.stop = stop
        if self.stop is None:
            self.stop = stop_after_delay(60)

        if self.retry_if is None:
            self.retry_status_code = set(DEFAULT_RETRY_STATUS_CODES)
            self.retry_if = (retry_if_result(self.retry_if_status_code) |
                             retry_if_exception_type(DEFAULT_RETRY_EXCEPTION_TYPES,
                                                     DEFAULT_RETRY_EXCEPTION_TYPES_BLACKLIST))
        if self.wait is None:
            random_wait = wait_random_exponential(multiplier=DEFAULT_RETRY_EXP_MULTIPLIER,
                                                  max=DEFAULT_RETRY_EXP_MAX)
            self.wait = wait_chain(wait_fixed(0.05),
                                   wait_fixed(0.1),
                                   wait_fixed(0.1) + random_wait)


    def retry_if_status_code(self, response):
        return response.status_code in self.retry_status_code

    def retry(self, *args, **kwargs):
        try:
            requests_timeout = kwargs.pop('timeout')
        except KeyError:
            requests_timeout = self.requests_timeout

        functor = functools.partial(*args, timeout=requests_timeout, **kwargs)
        return retry(functor, self.retry_if, self.wait, self.stop)
