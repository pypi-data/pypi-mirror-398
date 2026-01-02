"""Base HTTP client for Lindr API."""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx

from ._exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError as LindrConnectionError,
    LindrError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from ._version import __version__

DEFAULT_BASE_URL = "https://api.lindr.io/api/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 0.5

# Status codes that trigger automatic retry
RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)

# Network exceptions that should trigger retry
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.TimeoutException,
    httpx.NetworkError,
)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay: float = DEFAULT_RETRY_DELAY
    exponential_backoff: bool = True
    retry_on_status: tuple[int, ...] = field(default_factory=lambda: RETRYABLE_STATUS_CODES)

    def get_delay(self, attempt: int, retry_after: float | None = None) -> float:
        """Calculate delay before next retry attempt."""
        if retry_after is not None:
            return retry_after
        if self.exponential_backoff:
            return self.retry_delay * (2 ** attempt)
        return self.retry_delay


class BaseClient:
    """Base HTTP client for Lindr API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.api_key = api_key or os.environ.get("LINDR_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key is required. Set LINDR_API_KEY environment variable or pass api_key."
            )

        self.base_url = (
            base_url or os.environ.get("LINDR_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout
        self.retry_config = RetryConfig(max_retries=max_retries)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"lindr-python/{__version__}",
        }

    def _should_retry(self, response: httpx.Response, attempt: int) -> bool:
        """Determine if request should be retried."""
        if attempt >= self.retry_config.max_retries:
            return False
        return response.status_code in self.retry_config.retry_on_status

    def _get_retry_after(self, response: httpx.Response) -> float | None:
        """Extract Retry-After header value if present."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return None

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key or unauthorized")

        if response.status_code == 404:
            raise NotFoundError("Resource not found")

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code == 400:
            try:
                data = response.json()
                raise ValidationError(
                    data.get("error", "Validation error"), data.get("details")
                )
            except (ValueError, KeyError):
                raise ValidationError("Validation error")

        if response.status_code >= 400:
            try:
                data = response.json()
                raise APIError(
                    data.get("error", f"HTTP {response.status_code}"),
                    status_code=response.status_code,
                )
            except (ValueError, KeyError):
                raise APIError(f"HTTP {response.status_code}", status_code=response.status_code)

        return response.json()


class SyncHTTPClient(BaseClient):
    """Synchronous HTTP client with automatic retry."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self.timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SyncHTTPClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _request_with_retry(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute request with automatic retry on transient failures."""
        last_response: httpx.Response | None = None
        last_error: Exception | None = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                response = self._client.request(method, path, params=params, json=json)
                last_response = response
                last_error = None

                # If successful or non-retryable error, handle immediately
                if not self._should_retry(response, attempt):
                    return self._handle_response(response)

                # Calculate delay and wait before retry
                retry_after = self._get_retry_after(response)
                delay = self.retry_config.get_delay(attempt, retry_after)
                time.sleep(delay)

            except RETRYABLE_EXCEPTIONS as e:
                last_error = e
                # Network error - retry if we have attempts left
                if attempt >= self.retry_config.max_retries:
                    raise LindrConnectionError(
                        f"Connection failed after {self.retry_config.max_retries + 1} attempts: {e}",
                        original_error=e,
                    ) from e

                # Wait before retry
                delay = self.retry_config.get_delay(attempt)
                time.sleep(delay)

        # All retries exhausted
        if last_error is not None:
            raise LindrConnectionError(
                f"Connection failed after {self.retry_config.max_retries + 1} attempts: {last_error}",
                original_error=last_error,
            )

        assert last_response is not None
        return self._handle_response(last_response)

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request_with_retry("GET", path, params=params)

    def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request_with_retry("POST", path, json=json)

    def patch(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request_with_retry("PATCH", path, json=json)

    def delete(self, path: str) -> dict[str, Any]:
        return self._request_with_retry("DELETE", path)


class AsyncHTTPClient(BaseClient):
    """Asynchronous HTTP client with automatic retry."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self.timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHTTPClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute async request with automatic retry on transient failures."""
        last_response: httpx.Response | None = None
        last_error: Exception | None = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                response = await self._client.request(method, path, params=params, json=json)
                last_response = response
                last_error = None

                # If successful or non-retryable error, handle immediately
                if not self._should_retry(response, attempt):
                    return self._handle_response(response)

                # Calculate delay and wait before retry
                retry_after = self._get_retry_after(response)
                delay = self.retry_config.get_delay(attempt, retry_after)
                await asyncio.sleep(delay)

            except RETRYABLE_EXCEPTIONS as e:
                last_error = e
                # Network error - retry if we have attempts left
                if attempt >= self.retry_config.max_retries:
                    raise LindrConnectionError(
                        f"Connection failed after {self.retry_config.max_retries + 1} attempts: {e}",
                        original_error=e,
                    ) from e

                # Wait before retry
                delay = self.retry_config.get_delay(attempt)
                await asyncio.sleep(delay)

        # All retries exhausted
        if last_error is not None:
            raise LindrConnectionError(
                f"Connection failed after {self.retry_config.max_retries + 1} attempts: {last_error}",
                original_error=last_error,
            )

        assert last_response is not None
        return self._handle_response(last_response)

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request_with_retry("GET", path, params=params)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request_with_retry("POST", path, json=json)

    async def patch(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request_with_retry("PATCH", path, json=json)

    async def delete(self, path: str) -> dict[str, Any]:
        return await self._request_with_retry("DELETE", path)
