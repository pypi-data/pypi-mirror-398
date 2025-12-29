"""Tests for pyjquants core modules."""

from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from pyjquants.core.cache import TTLCache, NullCache
from pyjquants.core.config import JQuantsConfig
from pyjquants.core.exceptions import (
    PyJQuantsError,
    AuthenticationError,
    TokenExpiredError,
    APIError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ConfigurationError,
)


class TestTTLCache:
    """Tests for TTLCache."""

    def test_set_and_get(self) -> None:
        """Test basic set and get operations."""
        cache = TTLCache(default_ttl=60)
        cache.set("key1", "value1")

        assert cache.get("key1") == "value1"

    def test_get_missing_key(self) -> None:
        """Test getting a non-existent key returns None."""
        cache = TTLCache()

        assert cache.get("missing") is None

    def test_ttl_expiration(self) -> None:
        """Test that values expire after TTL."""
        cache = TTLCache(default_ttl=1)
        cache.set("key1", "value1", ttl=1)

        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_custom_ttl(self) -> None:
        """Test custom TTL per key."""
        cache = TTLCache(default_ttl=100)
        cache.set("short", "value", ttl=1)
        cache.set("long", "value", ttl=100)

        time.sleep(1.1)
        assert cache.get("short") is None
        assert cache.get("long") == "value"

    def test_delete(self) -> None:
        """Test deleting a cached value."""
        cache = TTLCache()
        cache.set("key1", "value1")

        cache.delete("key1")
        assert cache.get("key1") is None

    def test_delete_missing_key(self) -> None:
        """Test deleting a non-existent key doesn't raise."""
        cache = TTLCache()
        cache.delete("missing")  # Should not raise

    def test_clear(self) -> None:
        """Test clearing all cached values."""
        cache = TTLCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_max_size_eviction(self) -> None:
        """Test that cache evicts oldest entries when full."""
        cache = TTLCache(default_ttl=100, max_size=2)
        cache.set("key1", "value1")
        time.sleep(0.01)
        cache.set("key2", "value2")
        time.sleep(0.01)
        cache.set("key3", "value3")  # Should evict key1

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_make_key(self) -> None:
        """Test cache key generation."""
        cache = TTLCache()
        key1 = cache.make_key("arg1", "arg2", kwarg1="value")
        key2 = cache.make_key("arg1", "arg2", kwarg1="value")
        key3 = cache.make_key("different", "args")

        assert key1 == key2  # Same args produce same key
        assert key1 != key3  # Different args produce different key
        assert len(key1) == 32  # Key is a 32-char hex string


class TestNullCache:
    """Tests for NullCache (no-op cache)."""

    def test_get_always_returns_none(self) -> None:
        """Test that get always returns None."""
        cache = NullCache()
        cache.set("key", "value")

        assert cache.get("key") is None

    def test_operations_dont_raise(self) -> None:
        """Test that all operations complete without error."""
        cache = NullCache()
        cache.set("key", "value")
        cache.delete("key")
        cache.clear()


class TestJQuantsConfig:
    """Tests for JQuantsConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = JQuantsConfig()

        assert config.mail_address is None
        assert config.password is None
        assert config.cache_enabled is True
        assert config.cache_ttl_seconds == 3600
        assert config.requests_per_minute == 60

    def test_from_environment(self) -> None:
        """Test loading config from environment variables."""
        env_vars = {
            "JQUANTS_MAIL_ADDRESS": "test@example.com",
            "JQUANTS_PASSWORD": "testpass",
            "JQUANTS_REFRESH_TOKEN": "token123",
            "JQUANTS_CACHE_ENABLED": "false",
            "JQUANTS_CACHE_TTL": "7200",
            "JQUANTS_RATE_LIMIT": "30",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = JQuantsConfig.from_environment()

        assert config.mail_address == "test@example.com"
        assert config.password == "testpass"
        assert config.refresh_token == "token123"
        assert config.cache_enabled is False
        assert config.cache_ttl_seconds == 7200
        assert config.requests_per_minute == 30

    def test_from_environment_defaults(self) -> None:
        """Test environment config with missing variables uses defaults."""
        with patch.dict(os.environ, {}, clear=True):
            config = JQuantsConfig.from_environment()

        assert config.mail_address is None
        assert config.cache_enabled is True
        assert config.cache_ttl_seconds == 3600

    def test_has_credentials_with_email_password(self) -> None:
        """Test has_credentials with email and password."""
        config = JQuantsConfig(mail_address="test@example.com", password="pass")

        assert config.has_credentials() is True

    def test_has_credentials_with_refresh_token(self) -> None:
        """Test has_credentials with refresh token."""
        config = JQuantsConfig(refresh_token="token123")

        assert config.has_credentials() is True

    def test_has_credentials_false(self) -> None:
        """Test has_credentials returns False when no credentials."""
        config = JQuantsConfig()

        assert config.has_credentials() is False

    def test_has_credentials_partial(self) -> None:
        """Test has_credentials with only email (no password)."""
        config = JQuantsConfig(mail_address="test@example.com")

        assert config.has_credentials() is False


class TestExceptions:
    """Tests for exception classes."""

    def test_pyjquants_error(self) -> None:
        """Test base PyJQuantsError."""
        error = PyJQuantsError("test error")
        assert str(error) == "test error"
        assert isinstance(error, Exception)

    def test_authentication_error(self) -> None:
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid credentials")
        assert isinstance(error, PyJQuantsError)
        assert str(error) == "Invalid credentials"

    def test_token_expired_error(self) -> None:
        """Test TokenExpiredError."""
        error = TokenExpiredError("Token expired")
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, PyJQuantsError)

    def test_api_error(self) -> None:
        """Test APIError with status code and message."""
        error = APIError(500, "Internal server error")

        assert error.status_code == 500
        assert error.message == "Internal server error"
        assert "500" in str(error)
        assert "Internal server error" in str(error)

    def test_rate_limit_error(self) -> None:
        """Test RateLimitError."""
        error = RateLimitError()

        assert error.status_code == 429
        assert isinstance(error, APIError)

    def test_rate_limit_error_custom_message(self) -> None:
        """Test RateLimitError with custom message."""
        error = RateLimitError("Too many requests, retry after 60s")

        assert error.status_code == 429
        assert "retry after" in str(error)

    def test_not_found_error(self) -> None:
        """Test NotFoundError."""
        error = NotFoundError()

        assert error.status_code == 404
        assert isinstance(error, APIError)

    def test_validation_error(self) -> None:
        """Test ValidationError."""
        error = ValidationError("Invalid date format")

        assert isinstance(error, PyJQuantsError)
        assert str(error) == "Invalid date format"

    def test_configuration_error(self) -> None:
        """Test ConfigurationError."""
        error = ConfigurationError("Missing API key")

        assert isinstance(error, PyJQuantsError)
        assert str(error) == "Missing API key"

    def test_exception_hierarchy(self) -> None:
        """Test exception inheritance hierarchy."""
        # All errors should be catchable as PyJQuantsError
        errors = [
            AuthenticationError("test"),
            TokenExpiredError("test"),
            APIError(400, "test"),
            RateLimitError(),
            NotFoundError(),
            ValidationError("test"),
            ConfigurationError("test"),
        ]

        for error in errors:
            assert isinstance(error, PyJQuantsError)
