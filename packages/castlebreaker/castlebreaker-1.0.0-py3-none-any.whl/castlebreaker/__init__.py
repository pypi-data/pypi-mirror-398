"""
Castle Breaker - Your 1-stop shop for Castle.io tokens.

A Python SDK for Castle Breaker API services:
- Castle.io token solving (proxyless)
- ReCAPTCHA v3 solving
- TLS bypass requests (Cloudflare, Akamai, etc.)
- Account balance checking

Website: https://castlebreaker.cc

Basic Usage:
    from castlebreaker import Castle
    
    with Castle(api_key="your-key") as client:
        # Castle.io token
        result = client.solve_castle()
        token = result["token"]
        
        # ReCAPTCHA v3
        token = client.solve_recaptcha()
        
        # TLS bypass
        response = client.tls_request("https://example.com")

Async Usage:
    from castlebreaker import CastleAsync
    
    async with CastleAsync(api_key="your-key") as client:
        result = await client.solve_castle()
"""

from castlebreaker.client import Castle, CastleAsync
from castlebreaker.exceptions import (
    AuthenticationError,
    CastleBreakerError,
    InvalidRequestError,
    NetworkError,
    RateLimitError,
    ServiceUnavailableError,
    TaskError,
)
from castlebreaker.types import Balance, CastleToken, CastleTokenBatch, TLSResult

__version__ = "1.0.0"
__author__ = "Castle Breaker"
__url__ = "https://castlebreaker.cc"

__all__ = [
    # Clients
    "Castle",
    "CastleAsync",
    # Types
    "CastleToken",
    "CastleTokenBatch",
    "TLSResult",
    "Balance",
    # Exceptions
    "CastleBreakerError",
    "AuthenticationError",
    "RateLimitError",
    "InvalidRequestError",
    "ServiceUnavailableError",
    "NetworkError",
    "TaskError",
    # Metadata
    "__version__",
]
