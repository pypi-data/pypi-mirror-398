"""
Synchronous HTTP transport using httpx.

This transport uses connection pooling for efficiency and
implements automatic retry logic for transient failures.
"""

from __future__ import annotations

import time
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


class SyncTransport(BaseTransport):
    """
    Synchronous HTTP transport with connection pooling.
    
    Usage:
        with SyncTransport(base_url, api_key) as transport:
            result = transport.request("POST", "/solve", body={...})
    
    Or without context manager (remember to call close()):
        transport = SyncTransport(base_url, api_key)
        try:
            result = transport.request("POST", "/solve", body={...})
        finally:
            transport.close()
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
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Lazily initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._client

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "SyncTransport":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a synchronous HTTP request with retry logic.
        
        Retries are attempted for:
        - Network errors (connection issues, timeouts)
        - 5xx server errors
        - 429 rate limit (respects Retry-After header)
        
        No retries for:
        - 4xx client errors (except 429)
        - Successful responses
        """
        url = self._build_url(endpoint)
        request_headers = self._build_headers(headers)

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.request(
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
                # Retry on timeout
                if attempt < self.max_retries - 1:
                    time.sleep(self._backoff_delay(attempt))
                    continue
                raise last_error from e

            except httpx.RequestError as e:
                last_error = NetworkError(
                    f"Network error: {e}",
                    details={"endpoint": endpoint, "attempt": attempt + 1},
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self._backoff_delay(attempt))
                    continue
                raise last_error from e

            except RateLimitError as e:
                # Respect Retry-After if provided
                wait_time = e.retry_after or self._backoff_delay(attempt)
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                    continue
                raise

            except ServiceUnavailableError:
                # Retry on 5xx
                if attempt < self.max_retries - 1:
                    time.sleep(self._backoff_delay(attempt))
                    continue
                raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise CastleBreakerError("Request failed after all retries")

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """
        Parse response and raise appropriate exceptions for error status codes.
        
        This centralizes all HTTP status code handling, making it easy to
        add new error types or modify behavior.
        """
        # Try to parse JSON regardless of status code
        try:
            data = response.json()
        except (ValueError, TypeError):
            data = {"raw": response.text}

        if response.is_success:
            return data

        # Map status codes to exceptions
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

        # Catch-all for unexpected status codes
        raise CastleBreakerError(
            f"Unexpected response: {status} {message}",
            details={"status_code": status, "response": data},
        )

    def _backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        import random

        base_delay = 1.0
        max_delay = 30.0
        delay = min(base_delay * (2**attempt), max_delay)
        # Add jitter to prevent thundering herd
        return delay * (0.5 + random.random() * 0.5)
