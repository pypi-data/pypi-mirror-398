"""Tests for async session."""

from __future__ import annotations

import pytest

# Skip all tests if aiohttp is not installed
aiohttp = pytest.importorskip("aiohttp")

from unittest.mock import AsyncMock, MagicMock, patch

from pyjquants.core.async_session import AsyncSession, AsyncTokenManager, AsyncRateLimiter


class TestAsyncRateLimiter:
    """Tests for AsyncRateLimiter."""

    @pytest.mark.asyncio
    async def test_acquire(self) -> None:
        """Test rate limiter allows requests."""
        limiter = AsyncRateLimiter(requests_per_minute=60)
        await limiter.acquire()
        # Should complete without error

    @pytest.mark.asyncio
    async def test_rate_limiting(self) -> None:
        """Test rate limiter delays rapid requests."""
        limiter = AsyncRateLimiter(requests_per_minute=6000)  # Fast for testing

        import time
        start = time.time()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.time() - start

        # Should have some delay between requests
        assert elapsed >= 0.01  # At least 10ms


class TestAsyncTokenManager:
    """Tests for AsyncTokenManager."""

    def test_init_requires_aiohttp(self) -> None:
        """Test that AsyncTokenManager requires aiohttp."""
        # This should work since we imported aiohttp above
        manager = AsyncTokenManager(
            mail_address="test@example.com",
            password="password123",
        )
        assert manager._mail_address == "test@example.com"

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Test closing the token manager."""
        manager = AsyncTokenManager()
        await manager.close()  # Should not raise


class TestAsyncSession:
    """Tests for AsyncSession."""

    def test_init(self) -> None:
        """Test AsyncSession initialization."""
        with patch("pyjquants.core.async_session.JQuantsConfig") as mock_config:
            mock_config.load.return_value = MagicMock(
                mail_address="test@example.com",
                password="password",
                refresh_token=None,
                cache_enabled=True,
                cache_ttl_seconds=3600,
                requests_per_minute=60,
            )
            session = AsyncSession()
            assert session._config is not None

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test AsyncSession as context manager."""
        with patch("pyjquants.core.async_session.JQuantsConfig") as mock_config:
            mock_config.load.return_value = MagicMock(
                mail_address="test@example.com",
                password="password",
                refresh_token=None,
                cache_enabled=False,
                cache_ttl_seconds=3600,
                requests_per_minute=60,
            )
            async with AsyncSession() as session:
                assert session is not None
