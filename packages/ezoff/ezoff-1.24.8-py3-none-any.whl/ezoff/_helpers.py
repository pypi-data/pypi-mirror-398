"""
Helper functions for ezoff
"""

import logging
import os

import requests
from tenacity import (
    after_log,
    before_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


def should_retry_http_or_network_error(exception: BaseException) -> bool:
    """
    Determines if an exception warrants a retry.
    Retries on ConnectionError, Timeout, or specific HTTP 5XX errors.
    """
    if isinstance(
        exception, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    ):
        return True
    if isinstance(exception, requests.exceptions.HTTPError):
        # Retry on 5XX server errors
        return 500 <= exception.response.status_code < 600
    return False


_basic_retry = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception(should_retry_http_or_network_error),
    before=before_log(logger, logging.DEBUG),
    after=after_log(logger, logging.DEBUG),
)


@_basic_retry
def _http_request(
    call_method, url: str, title: str, headers: dict = {}, params: dict = {}, payload: dict = {}, timeout: int=60
) -> requests.Response:
    """Generic HTTP request wrapper. Used for making various types of HTTP requests to API endpoints.

    Args:
        call_method (_type_): HTTP Request method to use for call.
        url (str): Endpoint URL
        title (str): Descriptive title of call. Used in error messages.
        headers (dict, optional): HTTP header values of request.
        params (dict, optional): HTTP parameter values of request.
        payload (dict, optional): HTTP body payload of request.
        timeout (int, optional): HTTP timeout value.

    Returns:
        requests.Response: HTTP response object returned by request.
    """    
    
    def _log_request(
    ) -> None:
        """Prints request details to the error log.
        Called if an error occurrs as a result of the HTTP request.
        """

        # Redact bearer token before logging headers.
        if "Authorization" in headers:
            headers["Authorization"] = "REDACTED"

        logger.error('*' * 50)
        logger.error(msg)
        logger.error(f'HTTP Method: {call_method.__name__}')
        logger.error(f"URL: {url}")
        logger.error(f"Headers: {headers}")

        if payload is not None:
            logger.error(f"Payload: {payload}")

        if params is not None:
            logger.error(f"Params: {params}")

        logger.error('*' * 50)

    try:
        response = call_method(
            url,
            headers=headers,
            params=params,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        msg = f"HTTP error calling {title} API endpoint: {e.response.status_code} - {e.response.content}"
        _log_request()
        raise

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        msg = f"Connection error calling {title} API endpoint: {e}"
        _log_request()
        raise

    except requests.exceptions.RequestException as e:
        msg = f"Request error calling {title} API endpoint: {e}"
        _log_request()
        raise

    return response


def http_delete(
    url: str,
    title: str,
    timeout: int = 60,
    headers: dict = None,
    payload: dict = None,
    params: dict = None,
) -> requests.Response:

    if headers is None:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {os.environ['EZO_TOKEN']}",
        }

    return _http_request(
        call_method=requests.delete,
        url=url,
        headers=headers,
        params=params,
        payload=payload,
        title=title,
        timeout=timeout,
    )


def http_get(
    url: str,
    title: str,
    timeout: int = 60,
    headers: dict = None,
    payload: dict = None,
    params: dict = None,
) -> requests.Response:

    if headers is None:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {os.environ['EZO_TOKEN']}",
        }

    return _http_request(
        call_method=requests.get,
        url=url,
        headers=headers,
        params=params,
        payload=payload,
        title=title,
        timeout=timeout,
    )


def http_patch(
    url: str, title: str, timeout: int = 60, headers: dict = None, payload: dict = None
) -> requests.Response:

    if headers is None:
        headers = {
            # "Accept": "application/json",
            "Authorization": f"Bearer {os.environ['EZO_TOKEN']}",
        }

    return _http_request(
        call_method=requests.patch,
        url=url,
        headers=headers,
        payload=payload,
        title=title,
        timeout=timeout,
    )


def http_post(
    url: str, payload: dict, title: str, timeout: int = 60, headers: dict = None
) -> requests.Response:

    if headers is None:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {os.environ['EZO_TOKEN']}",
        }

    return _http_request(
        call_method=requests.post,
        url=url,
        headers=headers,
        payload=payload,
        title=title,
        timeout=timeout,
    )


def http_put(
    url: str, payload: dict, title: str, timeout: int = 60, headers: dict = None
) -> requests.Response:

    if headers is None:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {os.environ['EZO_TOKEN']}",
        }

    return _http_request(
        call_method=requests.put,
        url=url,
        headers=headers,
        payload=payload,
        title=title,
        timeout=timeout,
    )
