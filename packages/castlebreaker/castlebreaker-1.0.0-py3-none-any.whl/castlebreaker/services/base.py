"""
Base service class providing common functionality.

This is the key to reusability - new services simply inherit
from this class and define their endpoints/payloads.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from castlebreaker.transport.async_ import AsyncTransport
    from castlebreaker.transport.sync import SyncTransport


class TransportProtocol(Protocol):
    """Protocol defining what a transport must provide."""

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]: ...


class AsyncTransportProtocol(Protocol):
    """Protocol for async transports."""

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]: ...


class BaseService:
    """
    Base class for all token solving services.
    
    Each service wraps a transport and provides high-level methods
    for specific token types. The transport handles all HTTP details.
    
    Design Pattern:
        Services are thin wrappers that:
        1. Build the appropriate request body for each endpoint
        2. Call the transport with the endpoint and body
        3. Parse and validate the response
        
        This makes adding new endpoints trivial - just add a new method
        that builds the body and calls _call().
        
    Example of adding a new service:
        class NewService(BaseService):
            def solve(self, site_key: str) -> str:
                body = {"site_key": site_key}
                response = self._call("/solve/new", body)
                return response["token"]
    """

    def __init__(self, transport: "SyncTransport") -> None:
        """
        Initialize service with a transport.
        
        Args:
            transport: The HTTP transport to use for requests.
        """
        self._transport = transport

    def _call(
        self,
        endpoint: str,
        body: dict[str, Any] | None = None,
        *,
        method: str = "POST",
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a request through the transport.
        
        This is the core method that all service methods should use.
        It provides a consistent interface for making API calls.
        
        Args:
            endpoint: API endpoint path.
            body: Request body (will be JSON-encoded).
            method: HTTP method (default: POST).
            headers: Additional headers to include.
            
        Returns:
            Parsed JSON response.
        """
        return self._transport.request(method, endpoint, body=body, headers=headers)


class AsyncBaseService:
    """
    Async version of BaseService.
    
    Mirrors the sync API exactly but uses async/await.
    """

    def __init__(self, transport: "AsyncTransport") -> None:
        self._transport = transport

    async def _call(
        self,
        endpoint: str,
        body: dict[str, Any] | None = None,
        *,
        method: str = "POST",
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Execute an async request through the transport."""
        return await self._transport.request(
            method, endpoint, body=body, headers=headers
        )
