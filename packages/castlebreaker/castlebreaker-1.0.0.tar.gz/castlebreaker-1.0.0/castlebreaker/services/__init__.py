"""
Services layer for Castle Breaker API.

Each service encapsulates the business logic for a specific
API capability, while relying on the transport layer for HTTP.
"""

from castlebreaker.services.balance import AsyncBalanceService, BalanceService
from castlebreaker.services.base import AsyncBaseService, BaseService
from castlebreaker.services.castle import AsyncCastleService, CastleService
from castlebreaker.services.recaptcha import AsyncRecaptchaService, RecaptchaService
from castlebreaker.services.tls import AsyncTLSService, TLSService

__all__ = [
    # Base
    "BaseService",
    "AsyncBaseService",
    # Castle
    "CastleService",
    "AsyncCastleService",
    # ReCAPTCHA
    "RecaptchaService",
    "AsyncRecaptchaService",
    # TLS
    "TLSService",
    "AsyncTLSService",
    # Balance
    "BalanceService",
    "AsyncBalanceService",
]
