"""
Castle.io token solving service.

Provides methods to generate Castle tokens (proxyless).
The response includes necessary headers and the __cuid cookie.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from castlebreaker.exceptions import CastleBreakerError
from castlebreaker.services.base import AsyncBaseService, BaseService
from castlebreaker.types import CastleToken, CastleTokenBatch

if TYPE_CHECKING:
    from castlebreaker.transport.async_ import AsyncTransport
    from castlebreaker.transport.sync import SyncTransport


class CastleService(BaseService):
    """
    Service for solving Castle.io tokens.
    
    All tokens are generated proxyless. The response includes:
    - castle_token: The token to use
    - cid: The __cuid cookie value you must set
    - user_agent: The User-Agent header to use
    - accept_lang: The Accept-Language header to use
    
    Usage:
        service = CastleService(transport)
        
        # Single token
        result = service.solve()
        print(result["token"])
        
        # Multiple tokens
        results = service.solve_many(count=5)
        for token in results["tokens"]:
            print(token)
    """

    def __init__(self, transport: "SyncTransport") -> None:
        super().__init__(transport)

    def solve(self) -> CastleToken:
        """
        Generate a single Castle.io token.
        
        Returns:
            CastleToken with token, cid, user_agent, and accept_lang.
            
        Example:
            result = service.solve()
            # Set cookie: __cuid = result["cid"]
            # Set header: User-Agent = result["user_agent"]
            # Use token: result["token"]
        """
        response = self._call("/getCastleTokenProxyless", method="GET")
        
        if response.get("status") != "success":
            raise CastleBreakerError(
                f"Failed to solve Castle token: {response}",
                details=response,
            )
        
        data = response["data"]
        return CastleToken(
            token=data["castle_token"],
            cid=data["cid"],
            user_agent=data["user_agent"],
            accept_lang=data["accept_lang"],
        )

    def solve_many(self, count: int = 2) -> CastleTokenBatch:
        """
        Generate multiple Castle.io tokens.
        
        All tokens share the same fingerprint data (user_agent, cid, etc.).
        
        Args:
            count: Number of tokens to generate (default: 2).
            
        Returns:
            CastleTokenBatch with tokens list and shared fingerprint data.
        """
        response = self._call(
            f"/getManyCastleTokenProxyless?count={count}",
            method="GET",
        )
        
        if response.get("status") != "success":
            raise CastleBreakerError(
                f"Failed to solve Castle tokens: {response}",
                details=response,
            )
        
        data = response["data"]
        return CastleTokenBatch(
            tokens=data["tokens"],
            cid=data["cid"],
            user_agent=data["user_agent"],
            accept_lang=data["accept_lang"],
            sec_ch_ua=data.get("sec_ch_ua", ""),
        )


class AsyncCastleService(AsyncBaseService):
    """Async version of CastleService."""

    def __init__(self, transport: "AsyncTransport") -> None:
        super().__init__(transport)

    async def solve(self) -> CastleToken:
        """Generate a single Castle.io token asynchronously."""
        response = await self._call("/getCastleTokenProxyless", method="GET")
        
        if response.get("status") != "success":
            raise CastleBreakerError(
                f"Failed to solve Castle token: {response}",
                details=response,
            )
        
        data = response["data"]
        return CastleToken(
            token=data["castle_token"],
            cid=data["cid"],
            user_agent=data["user_agent"],
            accept_lang=data["accept_lang"],
        )

    async def solve_many(self, count: int = 2) -> CastleTokenBatch:
        """Generate multiple Castle.io tokens asynchronously."""
        response = await self._call(
            f"/getManyCastleTokenProxyless?count={count}",
            method="GET",
        )
        
        if response.get("status") != "success":
            raise CastleBreakerError(
                f"Failed to solve Castle tokens: {response}",
                details=response,
            )
        
        data = response["data"]
        return CastleTokenBatch(
            tokens=data["tokens"],
            cid=data["cid"],
            user_agent=data["user_agent"],
            accept_lang=data["accept_lang"],
            sec_ch_ua=data.get("sec_ch_ua", ""),
        )
