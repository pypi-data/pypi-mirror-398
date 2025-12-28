"""
Asynchronous HTTP transport using httpx.AsyncClient.

Mirrors the synchronous transport API but uses async/await,
making it suitable for asyncio-based applications.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx

from castlebreaker.exceptions import (
    AuthenticationError,
    CastleBreakerError,
    InvalidRequestError,
    NetworkError,
    RateLimitError,
    ServiceUnavailableError,
)
from castlebreaker.transport.base import BaseTransport


class AsyncTransport(BaseTransport):
    """
    Asynchronous HTTP transport with connection pooling.
    
    Usage:
        async with AsyncTransport(base_url, api_key) as transport:
            result = await transport.request("POST", "/solve", body={...})
    
    Or without context manager (remember to call close()):
        transport = AsyncTransport(base_url, api_key)
        try:
            result = await transport.request("POST", "/solve", body={...})
        finally:
            await transport.close()
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        super().__init__(base_url, api_key, timeout=timeout, max_retries=max_retries)
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazily initialize the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncTransport":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def request(  # type: ignore[override]
        self,
        method: str,
        endpoint: str,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute an asynchronous HTTP request with retry logic.
        
        Retry behavior mirrors the synchronous transport exactly,
        using asyncio.sleep instead of time.sleep.
        """
        url = self._build_url(endpoint)
        request_headers = self._build_headers(headers)

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(
                    method=method.upper(),
                    url=url,
                    json=body,
                    headers=request_headers,
                )
                return self._handle_response(response)

            except httpx.TimeoutException as e:
                last_error = NetworkError(
                    f"Request timed out after {self.timeout}s",
                    details={"endpoint": endpoint, "attempt": attempt + 1},
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self._backoff_delay(attempt))
                    continue
                raise last_error from e

            except httpx.RequestError as e:
                last_error = NetworkError(
                    f"Network error: {e}",
                    details={"endpoint": endpoint, "attempt": attempt + 1},
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self._backoff_delay(attempt))
                    continue
                raise last_error from e

            except RateLimitError as e:
                wait_time = e.retry_after or self._backoff_delay(attempt)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
                    continue
                raise

            except ServiceUnavailableError:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self._backoff_delay(attempt))
                    continue
                raise

        if last_error:
            raise last_error
        raise CastleBreakerError("Request failed after all retries")

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse response and raise appropriate exceptions for error status codes."""
        try:
            data = response.json()
        except (ValueError, TypeError):
            data = {"raw": response.text}

        if response.is_success:
            return data

        status = response.status_code
        message = data.get("error") or data.get("message") or response.reason_phrase

        if status == 401 or status == 403:
            raise AuthenticationError(
                f"Authentication failed: {message}",
                details={"status_code": status, "response": data},
            )

        if status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                f"Rate limit exceeded: {message}",
                retry_after=float(retry_after) if retry_after else None,
                details={"status_code": status, "response": data},
            )

        if 400 <= status < 500:
            raise InvalidRequestError(
                f"Invalid request: {message}",
                details={"status_code": status, "response": data},
            )

        if status >= 500:
            raise ServiceUnavailableError(
                f"Service unavailable: {message}",
                details={"status_code": status, "response": data},
            )

        raise CastleBreakerError(
            f"Unexpected response: {status} {message}",
            details={"status_code": status, "response": data},
        )

    def _backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        base_delay = 1.0
        max_delay = 30.0
        delay = min(base_delay * (2**attempt), max_delay)
        return delay * (0.5 + random.random() * 0.5)
