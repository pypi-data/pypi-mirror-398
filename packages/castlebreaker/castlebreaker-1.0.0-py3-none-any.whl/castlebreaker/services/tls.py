"""
TLS Bypass service.

Perform HTTP requests with realistic TLS fingerprints (JA3/JA4).
Ideal for scraping sites protected by Cloudflare, Akamai, or other TLS-based WAFs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from castlebreaker.exceptions import CastleBreakerError
from castlebreaker.services.base import AsyncBaseService, BaseService
from castlebreaker.types import TLSResult

if TYPE_CHECKING:
    from castlebreaker.transport.async_ import AsyncTransport
    from castlebreaker.transport.sync import SyncTransport


# TLS configuration presets
TLSConfig = Literal["CLOUDFLARE", "AKAMAI", "CUSTOM"]


class TLSService(BaseService):
    """
    Service for TLS bypass requests.
    
    Perform HTTP requests with realistic TLS fingerprints.
    
    TLS Configs:
    - CLOUDFLARE: Auto-retry blocked requests
    - AKAMAI: Handles access denied responses
    - CUSTOM: Default/generic fingerprint
    
    Usage:
        service = TLSService(transport)
        
        # Simple GET request
        result = service.request("https://example.com")
        
        # POST with JSON body
        result = service.request(
            url="https://api.example.com/login",
            method="POST",
            json={"username": "user", "password": "pass"},
            tls_config="CLOUDFLARE",
        )
    """

    def __init__(self, transport: "SyncTransport") -> None:
        super().__init__(transport)

    def request(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        tls_config: TLSConfig = "CUSTOM",
        cookies: str | None = None,
        proxy: str | None = None,
        timeout: int = 30,
        json: dict[str, Any] | None = None,
        data: str | None = None,
    ) -> TLSResult:
        """
        Perform an HTTP request with TLS fingerprinting.
        
        Args:
            url: Target URL.
            method: HTTP method (GET, POST, etc.).
            headers: Request headers.
            tls_config: TLS fingerprint preset (CLOUDFLARE, AKAMAI, CUSTOM).
            cookies: Cookie string to send.
            proxy: Proxy URL (http:// or socks5://). If omitted, auto-provided.
            timeout: Request timeout in seconds.
            json: JSON body for POST/PUT requests.
            data: Form-urlencoded data string for POST requests.
            
        Returns:
            TLSResult with response text, cookies, and TLS fingerprint info.
        """
        body: dict[str, Any] = {
            "url": url,
            "method": method,
            "tls_config": tls_config,
            "timeout": timeout,
        }
        
        if headers:
            body["headers"] = headers
        if cookies:
            body["cookies"] = cookies
        if proxy:
            body["proxy"] = proxy
        if json:
            body["json"] = json
        if data:
            body["data"] = data
        
        response = self._call("/tls", body, method="POST")
        
        # TLS endpoint uses boolean status instead of string
        if not response.get("status"):
            raise CastleBreakerError(
                response.get("msg", "TLS request failed"),
                details=response,
            )
        
        resp_data = response.get("data", {}).get("response", {})
        tls_info = resp_data.get("tls", {})
        
        return TLSResult(
            success=resp_data.get("status", False),
            text=resp_data.get("text", ""),
            cookies=resp_data.get("cookies", ""),
            ja3=tls_info.get("ja3", ""),
            ja3_hash=tls_info.get("ja3_hash", ""),
            request_id=response.get("id", ""),
            duration_ms=response.get("ms", ""),
        )


class AsyncTLSService(AsyncBaseService):
    """Async version of TLSService."""

    def __init__(self, transport: "AsyncTransport") -> None:
        super().__init__(transport)

    async def request(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        tls_config: TLSConfig = "CUSTOM",
        cookies: str | None = None,
        proxy: str | None = None,
        timeout: int = 30,
        json: dict[str, Any] | None = None,
        data: str | None = None,
    ) -> TLSResult:
        """Perform an HTTP request with TLS fingerprinting asynchronously."""
        body: dict[str, Any] = {
            "url": url,
            "method": method,
            "tls_config": tls_config,
            "timeout": timeout,
        }
        
        if headers:
            body["headers"] = headers
        if cookies:
            body["cookies"] = cookies
        if proxy:
            body["proxy"] = proxy
        if json:
            body["json"] = json
        if data:
            body["data"] = data
        
        response = await self._call("/tls", body, method="POST")
        
        if not response.get("status"):
            raise CastleBreakerError(
                response.get("msg", "TLS request failed"),
                details=response,
            )
        
        resp_data = response.get("data", {}).get("response", {})
        tls_info = resp_data.get("tls", {})
        
        return TLSResult(
            success=resp_data.get("status", False),
            text=resp_data.get("text", ""),
            cookies=resp_data.get("cookies", ""),
            ja3=tls_info.get("ja3", ""),
            ja3_hash=tls_info.get("ja3_hash", ""),
            request_id=response.get("id", ""),
            duration_ms=response.get("ms", ""),
        )
