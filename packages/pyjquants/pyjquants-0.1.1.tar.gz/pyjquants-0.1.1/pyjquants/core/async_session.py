"""Async session management for J-Quants API using aiohttp."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from pyjquants.core.cache import Cache, NullCache, TTLCache
from pyjquants.core.config import JQuantsConfig
from pyjquants.core.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    RateLimitError,
)

BASE_URL = "https://api.jquants.com/v1"
JST = timezone(timedelta(hours=9))


class AsyncRateLimiter:
    """Async rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self._requests_per_minute = requests_per_minute
        self._min_interval = 60.0 / requests_per_minute
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a request can be made."""
        async with self._lock:
            now = time.time()
            time_since_last = now - self._last_request_time
            if time_since_last < self._min_interval:
                await asyncio.sleep(self._min_interval - time_since_last)
            self._last_request_time = time.time()


class AsyncTokenManager:
    """Async token manager for J-Quants API authentication."""

    def __init__(
        self,
        mail_address: str | None = None,
        password: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        if aiohttp is None:
            raise ImportError(
                "aiohttp is required for async support. "
                "Install with: pip install pyjquants[async]"
            )

        self._mail_address = mail_address
        self._password = password
        self._refresh_token = refresh_token
        self._id_token: str | None = None
        self._id_token_expiry: datetime | None = None
        self._http_session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()
        return self._http_session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()

    @classmethod
    def from_config(cls, config: JQuantsConfig | None = None) -> AsyncTokenManager:
        """Create from config."""
        if config is None:
            config = JQuantsConfig.load()
        return cls(
            mail_address=config.mail_address,
            password=config.password,
            refresh_token=config.refresh_token,
        )

    async def _obtain_refresh_token(self) -> str:
        """Obtain refresh token from email/password."""
        if not self._mail_address or not self._password:
            raise ConfigurationError(
                "No credentials available. Set JQUANTS_MAIL_ADDRESS and JQUANTS_PASSWORD "
                "environment variables, or provide mail_address and password."
            )

        session = await self._get_session()
        async with session.post(
            f"{BASE_URL}/token/auth_user",
            json={"mailaddress": self._mail_address, "password": self._password},
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise AuthenticationError(f"Failed to authenticate: {text}")

            data = await response.json()
            self._refresh_token = data.get("refreshToken")
            if not self._refresh_token:
                raise AuthenticationError("No refresh token in response")

            return self._refresh_token

    async def _obtain_id_token(self) -> str:
        """Obtain ID token from refresh token."""
        if not self._refresh_token:
            await self._obtain_refresh_token()

        session = await self._get_session()
        async with session.post(
            f"{BASE_URL}/token/auth_refresh",
            params={"refreshtoken": self._refresh_token},
        ) as response:
            if response.status != 200:
                # Refresh token might be expired, try to get a new one
                if self._mail_address and self._password:
                    self._refresh_token = None
                    await self._obtain_refresh_token()
                    return await self._obtain_id_token()
                text = await response.text()
                raise AuthenticationError(f"Failed to refresh token: {text}")

            data = await response.json()
            self._id_token = data.get("idToken")
            if not self._id_token:
                raise AuthenticationError("No ID token in response")

            # ID token expires in 24 hours, refresh at 23 hours
            self._id_token_expiry = datetime.now(JST) + timedelta(hours=23)
            return self._id_token

    async def id_token(self) -> str:
        """Get valid ID token, refreshing if necessary."""
        if self._id_token and self._id_token_expiry:
            if datetime.now(JST) < self._id_token_expiry:
                return self._id_token

        return await self._obtain_id_token()


class AsyncSession:
    """Async session for J-Quants API with authentication, caching, and rate limiting."""

    def __init__(
        self,
        config: JQuantsConfig | None = None,
        cache: Cache | None = None,
    ) -> None:
        if aiohttp is None:
            raise ImportError(
                "aiohttp is required for async support. "
                "Install with: pip install pyjquants[async]"
            )

        self._config = config or JQuantsConfig.load()
        self._token_manager = AsyncTokenManager.from_config(self._config)
        self._rate_limiter = AsyncRateLimiter(self._config.requests_per_minute)

        if cache is not None:
            self._cache = cache
        elif self._config.cache_enabled:
            self._cache = TTLCache(default_ttl=self._config.cache_ttl_seconds)
        else:
            self._cache = NullCache()

        self._http_session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()
        return self._http_session

    async def close(self) -> None:
        """Close all sessions."""
        await self._token_manager.close()
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()

    async def __aenter__(self) -> AsyncSession:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def authenticate(self) -> None:
        """Authenticate with the API."""
        await self._token_manager.id_token()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Make an authenticated API request."""
        await self._rate_limiter.acquire()

        # Check cache for GET requests
        if method == "GET" and use_cache:
            cache_key = self._cache.make_key(endpoint, params)
            cached = self._cache.get(cache_key)
            if cached is not None:
                return dict(cached)

        # Get auth token
        token = await self._token_manager.id_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Make request
        url = f"{BASE_URL}{endpoint}"
        session = await self._get_session()

        async with session.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            headers=headers,
        ) as response:
            if response.status == 429:
                raise RateLimitError("Rate limit exceeded")
            if response.status == 401:
                # Try to refresh token once
                self._token_manager._id_token = None
                token = await self._token_manager.id_token()
                headers = {"Authorization": f"Bearer {token}"}
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers,
                ) as retry_response:
                    if retry_response.status == 401:
                        raise AuthenticationError("Authentication failed")
                    if retry_response.status >= 400:
                        text = await retry_response.text()
                        raise APIError(retry_response.status, text)
                    data: dict[str, Any] = await retry_response.json()
            elif response.status >= 400:
                text = await response.text()
                raise APIError(response.status, text)
            else:
                data = await response.json()

        # Cache successful GET responses
        if method == "GET" and use_cache:
            cache_key = self._cache.make_key(endpoint, params)
            self._cache.set(cache_key, data)

        return data

    async def get(
        self, endpoint: str, params: dict[str, Any] | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """Make authenticated GET request."""
        return await self._request("GET", endpoint, params=params, use_cache=use_cache)

    async def post(
        self,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated POST request."""
        return await self._request(
            "POST", endpoint, params=params, json_data=json_data, use_cache=False
        )

    async def get_paginated(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data_key: str = "info",
    ) -> AsyncIterator[dict[str, Any]]:
        """Make paginated GET request, yielding items."""
        params = params.copy() if params else {}

        while True:
            response = await self.get(endpoint, params=params, use_cache=False)

            items = response.get(data_key, [])
            for item in items:
                yield item

            # Check for pagination token
            pagination_key = response.get("pagination_key")
            if not pagination_key:
                break

            params["pagination_key"] = pagination_key
