"""
Account balance service.

Check remaining credits and usage statistics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from castlebreaker.exceptions import CastleBreakerError
from castlebreaker.services.base import AsyncBaseService, BaseService
from castlebreaker.types import Balance

if TYPE_CHECKING:
    from castlebreaker.transport.async_ import AsyncTransport
    from castlebreaker.transport.sync import SyncTransport


class BalanceService(BaseService):
    """
    Service for checking account balance.
    
    Usage:
        service = BalanceService(transport)
        balance = service.get()
        print(f"Credits: {balance['credits']}")
    """

    def __init__(self, transport: "SyncTransport") -> None:
        super().__init__(transport)

    def get(self) -> Balance:
        """
        Get current account balance and usage statistics.
        
        Returns:
            Balance with credits, requests_count, and total_spent.
        """
        response = self._call("/balance", method="GET")
        
        if response.get("status") != "success":
            raise CastleBreakerError(
                f"Failed to get balance: {response}",
                details=response,
            )
        
        data = response["data"]
        return Balance(
            credits=data["credits"],
            requests_count=data["requests_count"],
            total_spent=data["total_spent"],
        )


class AsyncBalanceService(AsyncBaseService):
    """Async version of BalanceService."""

    def __init__(self, transport: "AsyncTransport") -> None:
        super().__init__(transport)

    async def get(self) -> Balance:
        """Get current account balance asynchronously."""
        response = await self._call("/balance", method="GET")
        
        if response.get("status") != "success":
            raise CastleBreakerError(
                f"Failed to get balance: {response}",
                details=response,
            )
        
        data = response["data"]
        return Balance(
            credits=data["credits"],
            requests_count=data["requests_count"],
            total_spent=data["total_spent"],
        )
