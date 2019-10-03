from deepomatic.api import utils
from deepomatic.api.exceptions import HTTPRetryError
from requests.exceptions import (ProxyError, RequestException,
                                 TooManyRedirects, URLRequired)
from tenacity import (retry_if_exception, retry_if_result, stop_after_delay,
                      wait_chain, wait_fixed, wait_random_exponential)


class retry_if_exception_type(retry_if_exception):
    # Taken from https://github.com/jd/tenacity/blob/2775f13b34b3ec67a774061a77fcd4e1e9b4157c/tenacity/retry.py#L72
    # Extented to support blacklist types
    def __predicate(self, e):
        return (isinstance(e, self.exception_types)
                and not isinstance(e, self.exception_types_blacklist))

    def __init__(self, exception_types=Exception,
                 exception_types_blacklist=()):
        self.exception_types = exception_types
        self.exception_types_blacklist = exception_types_blacklist
        super(retry_if_exception_type, self).__init__(self.__predicate)


class HTTPRetry(object):

    """
           :param retry_if (optional): predicate to retry on requests errors.
               More details directly in tenacity source code:

                   - https://github.com/jd/tenacity/blob/5.1.1/tenacity/__init__.py#L179
                   - https://github.com/jd/tenacity/blob/5.1.1/tenacity/retry.py
               If not provided, the default behavior is:
                   - Retry on status code from Default.RETRY_STATUS_CODES
                   - Retry on exceptions from Default.RETRY_EXCEPTION_TYPES excluding those from Default.RETRY_EXCEPTION_TYPES_BLACKLIST
           :type retry_if: tenacity.retry_base
           :param wait (optional): how to wait between retry
               More details directly in tenacity source code https://github.com/jd/tenacity/blob/5.1.1/tenacity/wait.py

               if not provided, the default behavior is:
               ```
                   random_wait = wait_random_exponential(multiplier=Default.RETRY_EXP_MULTIPLIER,
                                                         max=Default.RETRY_EXP_MAX)
                   wait_chain(wait_fixed(0.05),
                              wait_fixed(0.1),
                              wait_fixed(0.1) + random_wait)
               ```
            :type wait: tenacity.wait_base
            :param stop (optional). Tell when to stop retrying. By default it stops retrying after 60s (Default.RETRY_TIMEOUT).
                A last retry can be done just before this delay is reached, thus the total amount of elapsed time might be a bit higher.
                More details in tenacity source code https://github.com/jd/tenacity/blob/5.1.1/tenacity/stop.py
                Raises tenacity.RetryError when timeout is reached.
            :type timeout: tenacity.stop_base
    """

    class Default(object):
        RETRY_TIMEOUT = 60
        RETRY_EXP_MAX = 10.
        RETRY_EXP_MULTIPLIER = 0.5
        RETRY_STATUS_CODES = [500, 502, 503, 504]
        RETRY_EXCEPTION_TYPES = (RequestException, )
        RETRY_EXCEPTION_TYPES_BLACKLIST = (ValueError, ProxyError, TooManyRedirects, URLRequired)

    def __init__(self, retry_if=None, wait=None, stop=None):
        self.retry_status_code = {}
        self.retry_if = retry_if
        self.wait = wait
        self.stop = stop

        if self.stop is None:
            self.stop = stop_after_delay(HTTPRetry.Default.RETRY_TIMEOUT)

        if self.retry_if is None:
            self.retry_status_code = set(HTTPRetry.Default.RETRY_STATUS_CODES)
            self.retry_if = (retry_if_result(self.retry_if_status_code)
                             | retry_if_exception_type(HTTPRetry.Default.RETRY_EXCEPTION_TYPES,
                                                       HTTPRetry.Default.RETRY_EXCEPTION_TYPES_BLACKLIST))

        if self.wait is None:
            random_wait = wait_random_exponential(multiplier=HTTPRetry.Default.RETRY_EXP_MULTIPLIER,
                                                  max=HTTPRetry.Default.RETRY_EXP_MAX)
            self.wait = wait_chain(wait_fixed(0.05),
                                   wait_fixed(0.1),
                                   wait_fixed(0.1) + random_wait)

    def retry(self, functor):
        return utils.retry(functor, self.retry_if, self.wait, self.stop, retry_error_cls=HTTPRetryError)

    def retry_if_status_code(self, response):
        return response.status_code in self.retry_status_code
