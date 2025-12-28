"""
Abstract base transport defining the HTTP interface contract.

The transport layer is intentionally generic - it knows nothing about
Castle.io or any specific API. This makes it trivially reusable for
any HTTP-based service.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTransport(ABC):
    """
    Abstract HTTP transport interface.
    
    Implementations handle the actual HTTP communication while
    the service layer handles business logic and response parsing.
    
    Design Note:
        The transport is endpoint-agnostic. You pass in the full
        endpoint path and body - the transport just sends it.
        This allows the same transport to be reused across different
        API services without modification.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize transport with base configuration.
        
        Args:
            base_url: Base URL for all API requests (e.g., 'https://api.castlebreaker.cc').
            api_key: API key for authentication.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts for transient failures.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    def request(
        self,
        method: str,
        endpoint: str,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute an HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path (e.g., '/solve/castle').
            body: Optional JSON body for POST/PUT requests.
            headers: Optional additional headers.
            
        Returns:
            Parsed JSON response as a dictionary.
            
        Raises:
            CastleBreakerError: On any API or network error.
        """
        ...

    def _build_url(self, endpoint: str) -> str:
        """Construct full URL from endpoint path."""
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/{endpoint}"

    def _build_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        """Build request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "User-Agent": "castlebreaker-python/1.0.0",
        }
        if extra:
            headers.update(extra)
        return headers
