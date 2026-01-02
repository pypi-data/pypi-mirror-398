import logging
from http import HTTPStatus
from importlib.metadata import version
from typing import Any, AsyncGenerator, Dict, Optional
from urllib.parse import urlencode

import httpx
from tenacity import (
    AsyncRetrying,
    before_sleep_log,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from aiq_platform_api.core.logger import AttackIQLogger

logger = AttackIQLogger.get_logger(__name__)

SDK_VERSION = version("aiq-platform-api")
DEFAULT_USER_AGENT = f"aiq-platform-api-python/{SDK_VERSION}"

DEFAULT_TIMEOUT = httpx.Timeout(30.0)
RETRYABLE_STATUSES = {
    HTTPStatus.BAD_GATEWAY,
    HTTPStatus.SERVICE_UNAVAILABLE,
    HTTPStatus.GATEWAY_TIMEOUT,
}


class AttackIQClient:
    """Async REST client for interacting with the AttackIQ platform."""

    def __init__(
        self,
        platform_url: str,
        platform_api_token: str,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
        user_agent: Optional[str] = None,
    ):
        self.platform_url = platform_url.rstrip("/")
        is_jwt = "." in platform_api_token
        auth_prefix = "Bearer" if is_jwt else "Token"
        logger.debug(f"Token type detection: is_jwt={is_jwt}, using auth_prefix='{auth_prefix}'")
        logger.debug(f"Token preview: {platform_api_token[:10]}... (length: {len(platform_api_token)})")
        self.headers = {
            "Authorization": f"{auth_prefix} {platform_api_token}",
            "User-Agent": user_agent or DEFAULT_USER_AGENT,
        }
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=self.headers,
            follow_redirects=True,
        )

    @property
    def http_client(self) -> httpx.AsyncClient:
        return self._client

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AttackIQClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    def _build_url(self, endpoint: str, params: dict = None) -> str:
        if not endpoint.startswith(self.platform_url):
            endpoint = endpoint.lstrip("/")
            url = f"{self.platform_url}/{endpoint}"
        else:
            url = endpoint
        if params:
            url += f"?{urlencode(params)}"
        return url

    @staticmethod
    def _parse_response(response: httpx.Response, url: str) -> Dict[str, Any]:
        if response.status_code == HTTPStatus.NOT_FOUND:
            logger.error(f"Resource not found: {url}")
            return {}

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Request failed \n"
                f"\turl: {url} \n"
                f"\tstatus: {response.status_code} \n"
                f"\tcontent: {response.text} \n"
                f"\theaders: {response.headers}"
            )
            raise exc

        if response.status_code in [HTTPStatus.NO_CONTENT, HTTPStatus.RESET_CONTENT]:
            logger.info(f"Request successful: {response.status_code} {response.reason_phrase}")
            return {"status_code": response.status_code}

        if response.content:
            return response.json()

        logger.info(f"Request successful but no content returned: {response.status_code} {response.reason_phrase}")
        return {"status_code": response.status_code}

    @staticmethod
    def _is_retryable_exception(exception: Exception) -> bool:
        status_code = None
        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
        elif isinstance(exception, httpx.RequestError) and exception.response is not None:
            status_code = exception.response.status_code
        return status_code in RETRYABLE_STATUSES

    def _retrying(self) -> AsyncRetrying:
        return AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception(self._is_retryable_exception),
            reraise=True,
            before_sleep=before_sleep_log(logger, logging.DEBUG),
        )

    async def _request(
        self,
        url: str,
        method: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        method = method.lower()
        if method not in ["get", "post", "delete", "put", "patch"]:
            raise ValueError(f"Unsupported method: {method}")

        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        return await self._client.request(
            method,
            url,
            json=json,
            headers=request_headers,
            files=files,
            data=data,
        )

    async def _make_request(self, url: str, method: str, json: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        async for attempt in self._retrying():
            with attempt:
                try:
                    logger.debug(f"Request method: {method.upper()} for URL: {url}")
                    if method == "post" and json:
                        logger.info(f"Request data: {json}")
                    response = await self._request(url, method, json=json)
                    return self._parse_response(response, url)
                except Exception as exc:  # noqa: BLE001
                    self._log_request_error(url, method, exc, json=json)
                    raise

    def _log_request_error(
        self,
        url: str,
        method: str,
        exc: Exception,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        request_headers = headers or self.headers
        if isinstance(exc, httpx.HTTPStatusError):
            logger.error(
                f"_make_request failed method: {method} \n"
                f"\turl: {url} \n"
                f"\tstatus: {exc.response.status_code} \n"
                f"\tcontent: {exc.response.text} \n"
                f"\tjson: {json} \n"
                f"\theaders: {request_headers} \n"
                f"\texception: {exc}"
            )
        elif isinstance(exc, httpx.RequestError):
            logger.error(
                f"_make_request failed method: {method} \n"
                f"\turl: {url} \n"
                f"\tjson: {json} \n"
                f"\theaders: {request_headers} \n"
                f"\texception: {exc}"
            )
        else:
            logger.error(f"_make_request failed with unexpected error: {exc}", exc_info=True)

    async def get_object(self, endpoint: str, params: dict = None) -> Optional[Dict[str, Any]]:
        url = self._build_url(endpoint, params)
        logger.debug(f"Fetching object from {url}")
        return await self._make_request(url, method="get", json=None)

    async def get_all_objects(self, endpoint: str, params: dict = None) -> AsyncGenerator[Dict[str, Any], None]:
        url = self._build_url(endpoint, params)
        logger.info(f"Fetching objects from {url}")
        total_count = None
        objects_yielded = 0
        while url:
            try:
                data = await self._make_request(url, method="get", json=None)
                if not data:
                    logger.info("Received empty data, stopping pagination.")
                    break
                if isinstance(data, dict):
                    results = data.get("results", [])
                    if total_count is None:
                        total_count = data.get("count")
                    url = data.get("next")
                    if total_count is not None:
                        objects_left = total_count - objects_yielded
                        logger.info(f"Objects left: {objects_left}")
                    else:
                        logger.info("Total count not available in response.")
                elif isinstance(data, list):
                    logger.info("Received a direct list response (non-paginated).")
                    results = data
                    total_count = len(results)
                    url = None
                    logger.info(f"Yielding {total_count} objects from the list.")
                else:
                    logger.error(f"Unexpected data type received: {type(data)}. Stopping.")
                    break
                if not results:
                    logger.info("No results found in the current batch.")
                    if url is None:
                        break
                    continue
                for result in results:
                    yield result
                    objects_yielded += 1
            except httpx.RequestError as e:
                logger.error(f"Failed to fetch objects during pagination: {e}")
                break
            except Exception as e:  # noqa: BLE001
                logger.error(f"Unexpected error during pagination: {e}", exc_info=True)
                break

    async def get_total_objects_count(self, endpoint: str, params: dict = None) -> Optional[int]:
        url = self._build_url(endpoint, params)
        data = await self._make_request(url, method="get", json=None)
        return data.get("count") if data else None

    async def post_object(self, endpoint: str, data: dict) -> Optional[Dict[str, Any]]:
        url = self._build_url(endpoint)
        logger.info(f"Posting object to {url} with data: {data}")
        return await self._make_request(url, method="post", json=data)

    async def patch_object(self, endpoint: str, data: dict) -> Optional[Dict[str, Any]]:
        url = self._build_url(endpoint)
        logger.info(f"Patching object at {url} with data: {data}")
        return await self._make_request(url, method="patch", json=data)

    async def delete_object(self, endpoint: str) -> Optional[Dict[str, Any]]:
        url = self._build_url(endpoint)
        logger.info(f"Deleting object at {url}")
        return await self._make_request(url, method="delete", json=None)

    async def upload_file(
        self,
        endpoint: str,
        file_name: str,
        file_content: bytes,
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Upload a single file (field name 'file') via multipart/form-data."""
        url = self._build_url(endpoint)
        logger.info(f"Uploading file to {url} with filename: {file_name}")
        resolved_headers = {k: v for k, v in self.headers.items() if k.lower() != "content-type"}
        if headers:
            resolved_headers.update(headers)

        files = {"file": (file_name, file_content, content_type or "application/octet-stream")}

        async for attempt in self._retrying():
            with attempt:
                try:
                    response = await self._request(
                        url,
                        method="post",
                        headers=resolved_headers,
                        files=files,
                        data=data,
                    )
                    return self._parse_response(response, url)
                except Exception as exc:  # noqa: BLE001
                    self._log_request_error(url, "post", exc, headers=resolved_headers)
                    raise

    async def download_bytes(self, endpoint: str) -> bytes:
        url = self._build_url(endpoint)
        logger.debug(f"Downloading bytes from {url}")
        async for attempt in self._retrying():
            with attempt:
                async with self._client.stream("GET", url, headers=self.headers) as response:
                    try:
                        response.raise_for_status()
                    except httpx.RequestError as e:
                        logger.error(
                            f"download_bytes failed \n"
                            f"\turl: {url} \n"
                            f"\tstatus: {response.status_code if response else 'n/a'} \n"
                            f"\tcontent: {response.text if response and response.content else 'n/a'} \n"
                            f"\texception: {e}"
                        )
                        raise
                    return await response.aread()
