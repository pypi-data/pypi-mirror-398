"""
Main client classes for Castle Breaker.

These are the primary user-facing classes that wrap all
the internal complexity into a clean, simple API.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any

from castlebreaker.services.balance import AsyncBalanceService, BalanceService
from castlebreaker.services.castle import AsyncCastleService, CastleService
from castlebreaker.services.recaptcha import AsyncRecaptchaService, RecaptchaService
from castlebreaker.services.tls import AsyncTLSService, TLSService
from castlebreaker.transport.async_ import AsyncTransport
from castlebreaker.transport.sync import SyncTransport
from castlebreaker.types import Balance, CastleToken, CastleTokenBatch, TLSResult


# Default API endpoint
DEFAULT_BASE_URL = "https://castlebreaker.cc"


class Castle:
    """
    Synchronous Castle Breaker client.
    
    Your 1-stop shop for Castle.io tokens, ReCAPTCHA v3, and TLS bypass.
    
    Usage:
        from castlebreaker import Castle
        
        with Castle(api_key="your-api-key") as client:
            # Castle.io token
            result = client.solve_castle()
            print(result["token"])
            
            # ReCAPTCHA v3
            token = client.solve_recaptcha()
            
            # TLS bypass request
            response = client.tls_request("https://example.com")
            
            # Check balance
            balance = client.get_balance()
    
    Args:
        api_key: Your Castle Breaker API key from the dashboard.
        base_url: Optional custom API base URL.
        timeout: Request timeout in seconds (default: 120).
        max_retries: Max retry attempts for failures (default: 3).
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")

        self._transport = SyncTransport(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        
        # Initialize services
        self._castle = CastleService(self._transport)
        self._recaptcha = RecaptchaService(self._transport)
        self._tls = TLSService(self._transport)
        self._balance = BalanceService(self._transport)

    def close(self) -> None:
        """Close the client and release resources."""
        self._transport.close()

    def __enter__(self) -> "Castle":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    # ========================================================================
    # Castle.io Methods
    # ========================================================================

    def solve_castle(self) -> CastleToken:
        """
        Solve a single Castle.io token (proxyless).
        
        Response includes:
        - token: The Castle token to use
        - cid: The __cuid cookie value to set
        - user_agent: User-Agent header to use
        - accept_lang: Accept-Language header to use
        
        Returns:
            CastleToken dict with token and fingerprint data.
            
        Example:
            result = client.solve_castle()
            # Set cookie: __cuid = result["cid"]
            # Set header: User-Agent = result["user_agent"]
            # Use result["token"] in your request
        """
        return self._castle.solve()

    def solve_castle_many(self, count: int = 2) -> CastleTokenBatch:
        """
        Solve multiple Castle.io tokens (proxyless).
        
        All tokens share the same fingerprint data.
        
        Args:
            count: Number of tokens to generate.
            
        Returns:
            CastleTokenBatch with tokens list and shared fingerprint.
        """
        return self._castle.solve_many(count)

    # ========================================================================
    # ReCAPTCHA v3 Methods
    # ========================================================================

    def solve_recaptcha(self) -> str:
        """
        Solve a ReCAPTCHA v3 token.
        
        Returns:
            The solved ReCAPTCHA v3 token string.
        """
        return self._recaptcha.solve()

    # ========================================================================
    # TLS Bypass Methods
    # ========================================================================

    def tls_request(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        tls_config: str = "CUSTOM",
        cookies: str | None = None,
        proxy: str | None = None,
        timeout: int = 30,
        json: dict[str, Any] | None = None,
        data: str | None = None,
    ) -> TLSResult:
        """
        Perform HTTP request with TLS fingerprinting.
        
        Ideal for bypassing Cloudflare, Akamai, or other TLS-based WAFs.
        
        Args:
            url: Target URL.
            method: HTTP method (GET, POST, etc.).
            headers: Request headers.
            tls_config: "CLOUDFLARE", "AKAMAI", or "CUSTOM".
            cookies: Cookie string to send.
            proxy: Proxy URL. If omitted, auto-provided.
            timeout: Request timeout in seconds.
            json: JSON body for POST requests.
            data: Form data string for POST requests.
            
        Returns:
            TLSResult with response text, cookies, and JA3 info.
        """
        return self._tls.request(
            url,
            method=method,
            headers=headers,
            tls_config=tls_config,  # type: ignore
            cookies=cookies,
            proxy=proxy,
            timeout=timeout,
            json=json,
            data=data,
        )

    # ========================================================================
    # Account Methods
    # ========================================================================

    def get_balance(self) -> Balance:
        """
        Get current account balance and usage statistics.
        
        Returns:
            Balance with credits, requests_count, total_spent.
        """
        return self._balance.get()


class CastleAsync:
    """
    Asynchronous Castle Breaker client.
    
    Same API as Castle but with async/await support.
    
    Usage:
        from castlebreaker import CastleAsync
        
        async with CastleAsync(api_key="your-api-key") as client:
            # Castle.io token
            result = await client.solve_castle()
            
            # ReCAPTCHA v3
            token = await client.solve_recaptcha()
            
            # TLS bypass
            response = await client.tls_request("https://example.com")
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")

        self._transport = AsyncTransport(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        
        self._castle = AsyncCastleService(self._transport)
        self._recaptcha = AsyncRecaptchaService(self._transport)
        self._tls = AsyncTLSService(self._transport)
        self._balance = AsyncBalanceService(self._transport)

    async def close(self) -> None:
        """Close the client and release resources."""
        await self._transport.close()

    async def __aenter__(self) -> "CastleAsync":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    # ========================================================================
    # Castle.io Methods
    # ========================================================================

    async def solve_castle(self) -> CastleToken:
        """Solve a single Castle.io token (proxyless)."""
        return await self._castle.solve()

    async def solve_castle_many(self, count: int = 2) -> CastleTokenBatch:
        """Solve multiple Castle.io tokens (proxyless)."""
        return await self._castle.solve_many(count)

    # ========================================================================
    # ReCAPTCHA v3 Methods
    # ========================================================================

    async def solve_recaptcha(self) -> str:
        """Solve a ReCAPTCHA v3 token."""
        return await self._recaptcha.solve()

    # ========================================================================
    # TLS Bypass Methods
    # ========================================================================

    async def tls_request(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        tls_config: str = "CUSTOM",
        cookies: str | None = None,
        proxy: str | None = None,
        timeout: int = 30,
        json: dict[str, Any] | None = None,
        data: str | None = None,
    ) -> TLSResult:
        """Perform HTTP request with TLS fingerprinting."""
        return await self._tls.request(
            url,
            method=method,
            headers=headers,
            tls_config=tls_config,  # type: ignore
            cookies=cookies,
            proxy=proxy,
            timeout=timeout,
            json=json,
            data=data,
        )

    # ========================================================================
    # Account Methods
    # ========================================================================

    async def get_balance(self) -> Balance:
        """Get current account balance and usage statistics."""
        return await self._balance.get()
