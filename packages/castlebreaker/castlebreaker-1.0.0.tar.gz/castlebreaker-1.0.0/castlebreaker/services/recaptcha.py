"""
ReCAPTCHA v3 token solving service.

Provides methods to generate ReCAPTCHA v3 tokens.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from castlebreaker.services.base import AsyncBaseService, BaseService

if TYPE_CHECKING:
    from castlebreaker.transport.async_ import AsyncTransport
    from castlebreaker.transport.sync import SyncTransport


class RecaptchaService(BaseService):
    """
    Service for solving ReCAPTCHA v3 tokens.
    
    Usage:
        service = RecaptchaService(transport)
        token = service.solve()
    """

    def __init__(self, transport: "SyncTransport") -> None:
        super().__init__(transport)

    def solve(self) -> str:
        """
        Generate a ReCAPTCHA v3 token.
        
        Returns:
            The solved ReCAPTCHA v3 token.
            
        Raises:
            AuthenticationError: If API key is invalid.
            RateLimitError: If rate limit exceeded.
        """
        response = self._call("/getRecapToken", method="GET")
        
        if response.get("status") != "success":
            from castlebreaker.exceptions import CastleBreakerError
            raise CastleBreakerError(
                f"Failed to solve ReCAPTCHA: {response}",
                details=response,
            )
        
        return response["data"]["token"]


class AsyncRecaptchaService(AsyncBaseService):
    """Async version of RecaptchaService."""

    def __init__(self, transport: "AsyncTransport") -> None:
        super().__init__(transport)

    async def solve(self) -> str:
        """Generate a ReCAPTCHA v3 token asynchronously."""
        response = await self._call("/getRecapToken", method="GET")
        
        if response.get("status") != "success":
            from castlebreaker.exceptions import CastleBreakerError
            raise CastleBreakerError(
                f"Failed to solve ReCAPTCHA: {response}",
                details=response,
            )
        
        return response["data"]["token"]
