"""
Castle Breaker API Tests

Tests all endpoints for both sync and async clients.
Set your API key via environment variable: CASTLE_API_KEY

Usage:
    export CASTLE_API_KEY="your-api-key"
    pytest tests/test_api.py -v
"""

import asyncio
import os

import pytest

from castlebreaker import Castle, CastleAsync
from castlebreaker.exceptions import AuthenticationError, CastleBreakerError


# Get API key from environment
API_KEY = os.environ.get("CASTLE_API_KEY", "")

# Skip all tests if no API key
pytestmark = pytest.mark.skipif(not API_KEY, reason="CASTLE_API_KEY not set")


# ============================================================================
# Sync Client Tests
# ============================================================================


class TestSyncClient:
    """Tests for synchronous Castle client."""

    @pytest.fixture
    def client(self):
        """Create a sync client for testing."""
        with Castle(api_key=API_KEY) as client:
            yield client

    def test_solve_castle(self, client):
        """Test single Castle.io token generation."""
        result = client.solve_castle()

        assert "token" in result
        assert "cid" in result
        assert "user_agent" in result
        assert "accept_lang" in result

        assert len(result["token"]) > 10
        assert len(result["cid"]) > 5

        print(f"✅ Castle token: {result['token'][:50]}...")
        print(f"   CID: {result['cid']}")

    def test_solve_castle_many(self, client):
        """Test multiple Castle.io token generation."""
        count = 3
        result = client.solve_castle_many(count=count)

        assert "tokens" in result
        assert "cid" in result
        assert "user_agent" in result

        assert len(result["tokens"]) == count

        print(f"✅ Got {len(result['tokens'])} Castle tokens")
        for i, token in enumerate(result["tokens"]):
            print(f"   Token {i+1}: {token[:40]}...")

    def test_solve_recaptcha(self, client):
        """Test ReCAPTCHA v3 token generation."""
        token = client.solve_recaptcha()

        assert isinstance(token, str)
        assert len(token) > 50

        print(f"✅ ReCAPTCHA token: {token[:50]}...")

    def test_tls_request(self, client):
        """Test TLS bypass request using httpbin.org."""
        result = client.tls_request(
            url="https://httpbin.org/get",
            method="GET",
            tls_config="CUSTOM",
        )

        assert result["success"] is True
        assert len(result["text"]) > 0
        assert "httpbin" in result["text"].lower() or "origin" in result["text"].lower()

        print(f"✅ TLS request succeeded")
        print(f"   JA3 hash: {result['ja3_hash']}")
        print(f"   Duration: {result['duration_ms']}")

    def test_tls_request_post(self, client):
        """Test TLS bypass POST request."""
        result = client.tls_request(
            url="https://httpbin.org/post",
            method="POST",
            json={"test": "data", "foo": "bar"},
            tls_config="CUSTOM",
        )

        assert result["success"] is True
        assert "test" in result["text"]

        print(f"✅ TLS POST request succeeded")

    def test_get_balance(self, client):
        """Test balance check."""
        balance = client.get_balance()

        assert "credits" in balance
        assert "requests_count" in balance
        assert "total_spent" in balance

        assert isinstance(balance["credits"], (int, float))
        assert isinstance(balance["requests_count"], int)

        print(f"✅ Balance: {balance['credits']} credits")
        print(f"   Requests: {balance['requests_count']}")
        print(f"   Total spent: ${balance['total_spent']:.4f}")


# ============================================================================
# Async Client Tests
# ============================================================================


class TestAsyncClient:
    """Tests for asynchronous Castle client."""

    @pytest.fixture
    async def client(self):
        """Create an async client for testing."""
        async with CastleAsync(api_key=API_KEY) as client:
            yield client

    @pytest.mark.asyncio
    async def test_solve_castle(self, client):
        """Test single Castle.io token generation (async)."""
        result = await client.solve_castle()

        assert "token" in result
        assert "cid" in result
        assert "user_agent" in result

        assert len(result["token"]) > 10

        print(f"✅ [Async] Castle token: {result['token'][:50]}...")

    @pytest.mark.asyncio
    async def test_solve_castle_many(self, client):
        """Test multiple Castle.io token generation (async)."""
        count = 2
        result = await client.solve_castle_many(count=count)

        assert len(result["tokens"]) == count

        print(f"✅ [Async] Got {len(result['tokens'])} Castle tokens")

    @pytest.mark.asyncio
    async def test_solve_recaptcha(self, client):
        """Test ReCAPTCHA v3 token generation (async)."""
        token = await client.solve_recaptcha()

        assert isinstance(token, str)
        assert len(token) > 50

        print(f"✅ [Async] ReCAPTCHA token: {token[:50]}...")

    @pytest.mark.asyncio
    async def test_tls_request(self, client):
        """Test TLS bypass request (async)."""
        result = await client.tls_request(
            url="https://httpbin.org/get",
            method="GET",
            tls_config="CUSTOM",
        )

        assert result["success"] is True
        assert len(result["text"]) > 0

        print(f"✅ [Async] TLS request succeeded")
        print(f"   JA3 hash: {result['ja3_hash']}")

    @pytest.mark.asyncio
    async def test_get_balance(self, client):
        """Test balance check (async)."""
        balance = await client.get_balance()

        assert "credits" in balance
        assert isinstance(balance["credits"], (int, float))

        print(f"✅ [Async] Balance: {balance['credits']} credits")

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """Test multiple concurrent requests."""
        tasks = [
            client.get_balance(),
            client.get_balance(),
            client.get_balance(),
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        for result in results:
            assert "credits" in result

        print(f"✅ [Async] {len(results)} concurrent requests succeeded")


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_api_key(self):
        """Test that invalid API key raises AuthenticationError."""
        with Castle(api_key="invalid-key-12345") as client:
            with pytest.raises((AuthenticationError, CastleBreakerError)):
                client.get_balance()

        print("✅ Invalid API key correctly raises error")

    def test_empty_api_key_raises(self):
        """Test that empty API key raises ValueError."""
        with pytest.raises(ValueError):
            Castle(api_key="")

        print("✅ Empty API key correctly raises ValueError")


# ============================================================================
# Run directly
# ============================================================================


if __name__ == "__main__":
    # Quick manual test
    if not API_KEY:
        print("❌ Set CASTLE_API_KEY environment variable first")
        print("   export CASTLE_API_KEY='your-api-key'")
        exit(1)

    print("=" * 60)
    print("Castle Breaker API Tests")
    print("=" * 60)

    with Castle(api_key=API_KEY) as client:
        print("\n📋 Testing Balance...")
        balance = client.get_balance()
        print(f"   Credits: {balance['credits']}")

        print("\n🏰 Testing Castle Token...")
        castle = client.solve_castle()
        print(f"   Token: {castle['token'][:50]}...")

        print("\n🤖 Testing ReCAPTCHA v3...")
        recap = client.solve_recaptcha()
        print(f"   Token: {recap[:50]}...")

        print("\n🔐 Testing TLS Bypass...")
        tls = client.tls_request("https://httpbin.org/get")
        print(f"   Success: {tls['success']}")
        print(f"   JA3: {tls['ja3_hash']}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
