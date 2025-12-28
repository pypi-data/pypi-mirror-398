"""
Type definitions for Castle Breaker API responses.

Using TypedDict for API responses provides IDE autocompletion
and static type checking without runtime overhead.
"""

from __future__ import annotations

from typing import Any, TypedDict


# ============================================================================
# Base Response Types
# ============================================================================


class BaseResponse(TypedDict, total=False):
    """Base response structure for most endpoints."""

    status: str  # "success" or "error"
    data: dict[str, Any]
    credits: float


# ============================================================================
# ReCAPTCHA Types
# ============================================================================


class RecaptchaData(TypedDict):
    """Data from ReCAPTCHA v3 solve."""

    token: str


class RecaptchaResponse(TypedDict):
    """Response from /getRecapToken endpoint."""

    status: str
    data: RecaptchaData
    credits: float


# ============================================================================
# Castle Token Types
# ============================================================================


class CastleTokenData(TypedDict):
    """Data from single Castle token solve."""

    accept_lang: str
    castle_token: str
    cid: str  # The __cuid cookie value
    user_agent: str


class CastleTokenResponse(TypedDict):
    """Response from /getCastleTokenProxyless endpoint."""

    status: str
    data: CastleTokenData
    credits: float


class ManyCastleTokenData(TypedDict):
    """Data from multiple Castle tokens solve."""

    tokens: list[str]
    accept_lang: str
    sec_ch_ua: str
    user_agent: str
    cid: str


class ManyCastleTokenResponse(TypedDict):
    """Response from /getManyCastleTokenProxyless endpoint."""

    status: str
    data: ManyCastleTokenData
    credits: float


# ============================================================================
# TLS Bypass Types
# ============================================================================


class TLSInfo(TypedDict):
    """TLS fingerprint information."""

    ja3: str
    ja3_hash: str


class TLSResponseData(TypedDict):
    """Inner response data for TLS requests."""

    status: bool
    text: str
    tls: TLSInfo
    cookies: str


class TLSData(TypedDict):
    """Data wrapper for TLS response."""

    response: TLSResponseData


class TLSResponse(TypedDict, total=False):
    """Response from /tls endpoint."""

    status: bool
    msg: str
    id: str
    ms: str
    credits: float
    truncated: bool
    data: TLSData


class TLSRequestBody(TypedDict, total=False):
    """Request body for /tls endpoint."""

    url: str
    method: str
    headers: dict[str, str]
    tls_config: str  # "CLOUDFLARE", "AKAMAI", or "CUSTOM"
    cookies: str
    proxy: str
    timeout: int
    json: dict[str, Any]
    data: str  # For x-www-form-urlencoded


# ============================================================================
# Balance Types
# ============================================================================


class BalanceData(TypedDict):
    """Account balance information."""

    credits: float
    requests_count: int
    total_spent: float


class BalanceResponse(TypedDict):
    """Response from /balance endpoint."""

    status: str
    data: BalanceData
    credits: float


# ============================================================================
# Result Objects (User-facing)
# ============================================================================


class CastleToken(TypedDict):
    """
    Solved Castle token with all necessary data.
    
    Usage:
        result = client.solve_castle()
        # Set cookie: __cuid = result["cid"]
        # Set headers: User-Agent = result["user_agent"]
        # Use token: result["token"]
    """

    token: str
    cid: str  # __cuid cookie value
    user_agent: str
    accept_lang: str


class CastleTokenBatch(TypedDict):
    """
    Multiple Castle tokens with shared fingerprint data.
    
    All tokens share the same user_agent, accept_lang, sec_ch_ua, and cid.
    """

    tokens: list[str]
    cid: str
    user_agent: str
    accept_lang: str
    sec_ch_ua: str


class TLSResult(TypedDict, total=False):
    """
    Result from TLS bypass request.
    
    Attributes:
        success: Whether the request succeeded.
        text: Response body text.
        cookies: Response cookies.
        ja3: JA3 fingerprint used.
        ja3_hash: Hash of JA3 fingerprint.
        request_id: Unique request identifier.
        duration_ms: Request duration.
    """

    success: bool
    text: str
    cookies: str
    ja3: str
    ja3_hash: str
    request_id: str
    duration_ms: str


class Balance(TypedDict):
    """Account balance information."""

    credits: float
    requests_count: int
    total_spent: float
