import asyncio
import aiohttp
import inflection
import requests
import urllib.parse
import logging
import traceback
import urllib3
import warnings
import concurrent.futures as futures
from typing import Union, Dict, List, Tuple
from tenacity import (
    Retrying,
    AsyncRetrying,
    RetryError,
    stop_after_delay,
    retry_if_not_exception_type,
    wait_random,
)

from .settings import get_env_flag
from .keyring import KeyRing


JSON = Union[None, bool, str, float, int, list, dict]


LOCAL_CLUSTER_SERVICES = "svc.cluster.local"

logger = logging.getLogger(__name__)


def make_url(url_base, *path_args, query_args: Union[Dict, List[Tuple]] = None, **path_kwargs):
    path_args = [urllib.parse.quote(v, safe="") for v in path_args]
    path_kwargs = {k: urllib.parse.quote(v, safe="") for k, v in path_kwargs.items()}
    path = url_base.format(*path_args, **path_kwargs)

    if query_args is None or len(query_args) == 0:
        return path
    query_string = urllib.parse.urlencode(query_args, doseq=True, quote_via=urllib.parse.quote)
    return f"{path}?{query_string}"


class APIException(Exception):
    def __init__(
        self,
        url: str,
        status_code: int = 0,
        message: str = None,
        request_body: dict = None,
        response=None,
    ):
        self.url = url
        self.status_code = status_code
        self.request_body = request_body
        self.response = response

        if not message and self.status_code and self.response is not None:
            message = f"API {self.url} returned HTTP {self.status_code}: {self.response.text}"
        elif not message:
            message = f"API Error: {self.url}"

        super().__init__(message)


class InvalidInputException(APIException):
    def __init__(self, message: str = None):
        super().__init__(url=None, message=message, status_code=400)


class APIClientBase:
    SUCCESS_CODES = {
        "GET": [200],
        "POST": [200, 201, 202],
        "PUT": [200, 202],
        "PATCH": [200, 202],
        "DELETE": [200, 202, 204],
    }

    def __init__(self, url_base=None, default_protocol="http", insecure_ssl=None, timeout=5 * 60, api_key=None):
        self.url_base = url_base
        self.timeout = timeout
        protocols = ["http://", "https://"]
        if not any(self.url_base.lower().startswith(p) for p in protocols):
            self.url_base = f"{default_protocol}://{self.url_base}"

        self.url_base = self.url_base.rstrip("/")
        self.headers = {"accept": "application/json"}
        parsed_base_url = urllib.parse.urlparse(self.url_base)
        keyring = KeyRing(parsed_base_url.netloc)
        JWT_TOKEN = keyring.get_token()
        if JWT_TOKEN is not None:
            self.headers.update({"Authorization": f"Bearer {JWT_TOKEN}"})
        if api_key is not None:
            self.headers.update({"X-API-Key": api_key})

        self._verify_ssl_cert = True
        self._force_json = True
        if insecure_ssl is not None:
            self.set_insecure_ssl(insecure_ssl)
        elif get_env_flag("ALLOW_INSECURE_SSL"):
            self.set_insecure_ssl(True)

        self._use_asyncio = False

    def set_async(self, use_async=True):
        self._use_asyncio = use_async

    @property
    def _retry_config(self):
        return dict(
            stop=stop_after_delay(self.timeout),
            wait=wait_random(min=0.2, max=3.0),
            reraise=True,
        )

    def _request(
        self,
        method: str,
        relative_url: str,
        *args,
        query_args: Union[Dict, List[Tuple]] = None,
        body: dict = None,
        success_codes: list = None,
        on_response_callback=None,
        **kwargs,
    ):
        url = self._make_url(relative_url, *args, query_args=query_args, **kwargs)
        error_subject = get_human_readable_entry_point(self)

        if not success_codes:
            success_codes = APIClientBase.SUCCESS_CODES[method]

        if self._use_asyncio and is_event_loop_available():
            return self._async_request(method, url, body, success_codes, error_subject, on_response_callback)
        else:
            return self._sync_request(method, url, body, success_codes, error_subject, on_response_callback)

    async def _async_request(
        self,
        method: str,
        url: str,
        body: dict,
        success_codes: list,
        error_subject: str,
        on_response_callback,
    ):
        try:
            logger.debug(f"Calling {method} {url} with aiohttp lib")
            async for attempt in AsyncRetrying(retry=retry_if_not_exception_type(APIException), **self._retry_config):
                with attempt:
                    return await asyncio.wait_for(
                        self._unsafe_async_request(
                            method,
                            url,
                            body,
                            success_codes,
                            error_subject,
                            on_response_callback,
                        ),
                        timeout=self.timeout,
                    )

        except APIException:
            raise

        except (
            aiohttp.ServerTimeoutError,
            requests.Timeout,
            asyncio.TimeoutError,
            futures.TimeoutError,
            RetryError,
        ) as e:
            logger.warning(f"Failed {method} request to {url}, network timeout: {str(e)}")
            error = self._append_url_if_not_local_service("network timeout")
            raise APIException(
                url=url,
                message=f"{error_subject} has failed ({error})",
                request_body=body,
            ) from e

        except (aiohttp.ClientSSLError, requests.exceptions.SSLError) as e:
            logger.warning(f"Failed {method} request to {url}, ssl error: {str(e)}")
            error = self._append_url_if_not_local_service("ssl error")
            raise APIException(
                url=url,
                message=f"{error_subject} has failed ({error})",
                request_body=body,
            ) from e

        except (aiohttp.ClientConnectionError, requests.ConnectionError) as e:
            logger.warning(f"Failed {method} request to {url}, connect error: {str(e)}")
            error = self._append_url_if_not_local_service("network connect error")
            raise APIException(
                url=url,
                message=f"{error_subject} has failed ({error})",
                request_body=body,
            ) from e

        except (aiohttp.ClientError, requests.RequestException) as e:
            logger.warning(f"Failed {method} request to {url}, network error: {str(e)}")
            error = self._append_url_if_not_local_service("network error")
            raise APIException(
                url=url,
                message=f"{error_subject} has failed ({error})",
                request_body=body,
            ) from e

        except Exception as e:
            logger.warning(f"Failed {method} request to {url}: {str(e)}")
            error = self._append_url_if_not_local_service(str(e) or type(e).__name__)
            raise APIException(
                url=url,
                message=f"{error_subject} has failed ({error})",
                request_body=body,
            ) from e

    async def _unsafe_async_request(
        self,
        method: str,
        url: str,
        body: dict,
        success_codes: list,
        error_subject: str,
        on_response_callback,
    ):
        headers = None
        if self.headers is not None and len(self.headers) > 0:
            headers = self.headers

        method_args = {}
        if not self._verify_ssl_cert:
            method_args["ssl"] = False
        if body is not None:
            method_args["json"] = body

        async with aiohttp.ClientSession(headers=headers) as session:
            request_methods = {
                "GET": session.get,
                "POST": session.post,
                "PUT": session.put,
                "PATCH": session.patch,
                "DELETE": session.delete,
            }
            request_method = request_methods[method]
            async with request_method(url, **method_args) as response:
                is_json = response.headers.get("content-type") == "application/json"
                if response.status in success_codes:
                    logger.debug(f"Received {response.status} from {method} {url}")
                    if is_json or self._force_json:
                        json_response = await response.json()
                        return on_response_callback(json_response) if on_response_callback else json_response
                    else:
                        return await response.read()

                logger.info(f"Received {response.status} from {method} {url}")
                error = get_http_code_error_message(response.status)
                raise APIException(
                    url=url,
                    status_code=response.status,
                    message=f"{error_subject} has failed ({error})",
                    request_body=body,
                    response=response,
                )

    def _sync_request(
        self,
        method: str,
        url: str,
        body: dict,
        success_codes: list,
        error_subject: str,
        on_response_callback,
    ):
        try:
            logger.debug(f"Calling {method} {url} with requests lib")
            for attempt in Retrying(retry=retry_if_not_exception_type(APIException), **self._retry_config):
                with attempt:
                    return self._unsafe_sync_request(
                        method,
                        url,
                        body,
                        success_codes,
                        error_subject,
                        on_response_callback,
                    )

        except APIException:
            raise

        except (
            aiohttp.ServerTimeoutError,
            requests.Timeout,
            futures.TimeoutError,
            RetryError,
        ) as e:
            logger.warning(f"Failed {method} request to {url}, network timeout: {str(e)}")
            error = self._append_url_if_not_local_service("network timeout")
            raise APIException(
                url=url,
                message=f"{error_subject} has failed ({error})",
                request_body=body,
            ) from e

        except (aiohttp.ClientSSLError, requests.exceptions.SSLError) as e:
            logger.warning(f"Failed {method} request to {url}, ssl error: {str(e)}")
            error = self._append_url_if_not_local_service("ssl error")
            raise APIException(
                url=url,
                message=f"{error_subject} has failed ({error})",
                request_body=body,
            ) from e

        except (aiohttp.ClientConnectionError, requests.ConnectionError) as e:
            logger.warning(f"Failed {method} request to {url}, connect error: {str(e)}")
            error = self._append_url_if_not_local_service("network connect error")
            raise APIException(
                url=url,
                message=f"{error_subject} has failed ({error})",
                request_body=body,
            ) from e

        except (aiohttp.ClientError, requests.RequestException) as e:
            logger.warning(f"Failed {method} request to {url}, network error: {str(e)}")
            error = self._append_url_if_not_local_service("network error")
            raise APIException(
                url=url,
                message=f"{error_subject} has failed ({error})",
                request_body=body,
            ) from e

        except Exception as e:
            logger.warning(f"Failed {method} request to {url}: {str(e)}")
            error = self._append_url_if_not_local_service(str(e) or type(e).__name__)
            raise APIException(
                url=url,
                message=f"{error_subject} has failed ({error})",
                request_body=body,
            ) from e

    def _unsafe_sync_request(
        self,
        method: str,
        url: str,
        body: dict,
        success_codes: list,
        error_subject: str,
        on_response_callback,
    ):
        method_func = self._get_method_func(method)
        method_args = {"verify": self._verify_ssl_cert}
        if self.headers is not None and len(self.headers) > 0:
            method_args["headers"] = self.headers

        if body is not None:
            method_args["json"] = body

        with warnings.catch_warnings():
            if not self._verify_ssl_cert:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = method_func(url, timeout=self.timeout, **method_args)

        is_json = "json" in response.headers.get("content-type", "").lower()
        if response.status_code in success_codes:
            logger.debug(f"Received {response.status_code} from {method} {url}")
            if is_json or self._force_json:
                try:
                    json_response = response.json()
                except Exception:
                    json_response = None
                return on_response_callback(json_response) if on_response_callback else json_response
            else:
                return response.content

        logger.info(f"Received {response.status_code} from {method} {url}")
        error = get_http_code_error_message(response.status_code)
        raise APIException(
            url=url,
            status_code=response.status_code,
            message=f"{error_subject} has failed ({error})",
            request_body=body,
            response=response,
        )

    def _make_url(
        self,
        relative_url: str,
        *args,
        query_args: Union[Dict, List[Tuple]] = None,
        **kwargs,
    ):
        relative_url = relative_url.lstrip("/")
        return make_url(self.url_base + "/" + relative_url, *args, query_args=query_args, **kwargs)

    def _is_local_service(self):
        return LOCAL_CLUSTER_SERVICES in self.url_base.lower()

    def _append_url_if_not_local_service(self, message):
        if self._is_local_service():
            return message

        hostname = self._get_hostname()
        if not hostname:
            return f"{message}: <host not specified>"
        else:
            return f"{message}: {hostname.strip()}"

    def _get_hostname(self):
        parsed_uri = urllib.parse.urlparse(self.url_base)
        hostname = parsed_uri.netloc
        if ":" in hostname:
            hostname, port = parsed_uri.netloc.split(":")[:2]
        return hostname.strip() if hostname else hostname

    def _get_method_func(self, method):
        requests_methods = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "PATCH": requests.patch,
            "DELETE": requests.delete,
        }
        return requests_methods[method]

    def get_request(
        self,
        relative_url: str,
        *url_path_args,
        query_args: Union[Dict, List[Tuple]] = None,
        success_codes: list = None,
        **url_path_kwargs,
    ):
        return self._request(
            "GET",
            relative_url,
            *url_path_args,
            query_args=query_args,
            success_codes=success_codes,
            **url_path_kwargs,
        )

    def delete_request(self, *args, **kwargs):
        # Same args as get_request
        return self._request("DELETE", *args, **kwargs)

    def post_request(
        self,
        relative_url: str,
        *url_path_args,
        query_args: Union[Dict, List[Tuple]] = None,
        body: dict = None,
        success_codes: list = None,
        **url_path_kwargs,
    ):
        return self._request(
            "POST",
            relative_url,
            *url_path_args,
            query_args=query_args,
            body=body,
            success_codes=success_codes,
            **url_path_kwargs,
        )

    def put_request(self, *args, **kwargs):
        # Same args as post_request
        return self._request("PUT", *args, **kwargs)

    def patch_request(self, *args, **kwargs):
        # Same args as post_request
        return self._request("PATCH", *args, **kwargs)

    def set_insecure_ssl(self, insecure=True):
        self._verify_ssl_cert = not insecure

    def set_auth_jwt(self, jwt):
        self.headers["Authorization"] = f"Bearer {jwt}"


def get_http_code_error_message(status_code):
    if status_code == 404:
        return "object not found"
    if status_code == 401:
        return "unauthorized"
    if status_code == 403:
        return "forbidden"
    return f"{status_code}"


def get_object_entry_method_name(obj):
    frames = traceback.StackSummary.extract(traceback.walk_stack(f=None), limit=20)
    entry_method_name = None
    for summary, raw_frame in zip(frames[1:], traceback.walk_stack(f=None)):
        frame, line_no = raw_frame
        frame_self = frame.f_locals.get("self")
        if obj == frame_self:
            entry_method_name = summary.name
    return entry_method_name


def get_human_readable_entry_point(obj):
    entry_method_name = get_object_entry_method_name(obj)
    return inflection.humanize(entry_method_name)


def is_event_loop_available():
    try:
        asyncio.get_event_loop()
        return True
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            return False

        logger.debug(f"Failed to get asyncio event loop: {str(ex)}")
        return False
