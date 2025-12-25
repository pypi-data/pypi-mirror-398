"""Lightweight HTTP client for RealtimeX API communication."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Mapping
from typing import Any
from urllib.parse import urljoin

import aiohttp
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from realtimex_toolkit.api.error_mapping import DefaultErrorMapper, ErrorMapper
from realtimex_toolkit.exceptions import (
    ApiError,
    ConnectionError,
)

logger = logging.getLogger(__name__)


class ApiClient:
    """Asynchronous HTTP client for JSON-based API communication.

    This client handles retries, error mapping, and session management for
    HTTP requests. All responses are expected to be JSON-encoded.

    For non-JSON responses or streaming, use aiohttp.ClientSession directly.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: int = 30,
        max_retries: int = 3,
        session: aiohttp.ClientSession | None = None,
        user_agent: str | None = None,
        error_mapper: ErrorMapper | None = None,
    ) -> None:
        """Initialize ApiClient.

        Args:
            base_url: Base URL for all API requests
            api_key: API authentication key
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for transient failures
            session: Optional pre-configured aiohttp session. If None, creates own session.
            user_agent: Custom user agent string
            error_mapper: Strategy for mapping HTTP errors to exceptions.
                         Defaults to DefaultErrorMapper which raises ResourceNotFoundError for 404s.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = session
        self._owned_session = session is None
        self._user_agent = user_agent or "realtimex-python"
        self._error_mapper = error_mapper or DefaultErrorMapper()

    async def __aenter__(self) -> ApiClient:
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP session if this client created it."""
        if self._owned_session and self._session and not self._session.closed:
            await self._session.close()

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any | None = None,
        data: Any | None = None,
        headers: Mapping[str, str] | None = None,
        content_type: str | None = None,
    ) -> Any:
        """Execute an HTTP request and return the parsed JSON payload.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path (relative to base_url)
            params: URL query parameters
            json_body: Request body to be JSON-encoded. Automatically sets Content-Type.
            data: Raw request body data (for non-JSON payloads)
            headers: Additional HTTP headers. These override default headers.
            content_type: Explicit Content-Type header. If not set and json_body is provided,
                         defaults to "application/json". Can be any valid MIME type string.

        Returns:
            Parsed JSON response, or None for 204/empty responses

        Raises:
            ConnectionError: If connection fails after max_retries
            ApiError: For HTTP error responses (mapped via error_mapper)

        Notes:
            - Authorization header is automatically included
            - Responses are expected to be JSON. For other formats, use aiohttp directly.
            - Custom headers override defaults (Authorization, User-Agent, Content-Type)
        """
        session = await self._ensure_session()
        url = self._build_url(endpoint)

        request_headers = self._build_headers(
            custom_headers=headers,
            content_type=content_type,
            has_json_body=json_body is not None,
        )

        logger.debug("Sending HTTP request: %s %s", method.upper(), url)

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
            ):
                with attempt:
                    try:
                        async with session.request(
                            method,
                            url,
                            params=params,
                            json=json_body,
                            data=data,
                            headers=request_headers,
                            timeout=aiohttp.ClientTimeout(total=self.timeout),
                        ) as response:
                            payload = await self._parse_response(response)
                            logger.debug(
                                "Received HTTP response: %s %s (status=%d)",
                                method.upper(),
                                url,
                                response.status,
                            )
                            return payload
                    except (TimeoutError, aiohttp.ClientError) as exc:
                        logger.warning(
                            "Retrying HTTP request after error: %s %s (attempt=%d, error=%s)",
                            method.upper(),
                            url,
                            attempt.retry_state.attempt_number,
                            str(exc),
                        )
                        raise
        except RetryError as exc:
            raise ConnectionError(
                f"Failed to connect to API after {self.max_retries} attempts: {exc}"
            ) from exc

    def _build_url(self, endpoint: str) -> str:
        """Construct full URL from base and endpoint."""
        return urljoin(f"{self.base_url}/", endpoint.lstrip("/"))

    def _build_headers(
        self,
        *,
        custom_headers: Mapping[str, str] | None,
        content_type: str | None,
        has_json_body: bool,
    ) -> dict[str, str]:
        """Build request headers with appropriate defaults.

        Priority (highest to lowest):
        1. custom_headers (overrides everything)
        2. explicit content_type parameter
        3. auto-detect (application/json if has_json_body)
        4. Authorization and User-Agent defaults
        """
        headers: dict[str, str] = {}

        headers["Authorization"] = f"Bearer {self.api_key}"
        headers["User-Agent"] = self._user_agent

        if content_type is not None:
            headers["Content-Type"] = content_type
        elif has_json_body:
            headers["Content-Type"] = "application/json"

        if custom_headers:
            headers.update(custom_headers)

        return headers

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout, raise_for_status=False)
        return self._session

    async def _parse_response(self, response: aiohttp.ClientResponse) -> Any:
        """Parse HTTP response and handle errors."""
        if response.status >= 400:
            response_text = await response.text()
            error = self._error_mapper.map_error(response.status, response_text)
            logger.error(
                "HTTP request failed: %s (status=%d, error=%s)",
                str(response.url),
                response.status,
                str(error),
            )
            raise error

        if response.status == 204:
            return None

        text = await response.text()
        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON response from %s: %s", str(response.url), str(exc))
            raise ApiError(
                f"Invalid JSON response: {exc}",
                status_code=response.status,
                response_body=text,
            ) from exc
