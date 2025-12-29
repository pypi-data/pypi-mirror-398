"""Session management for J-Quants API authentication and HTTP requests."""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from pyjquants.core.cache import Cache, NullCache, TTLCache
from pyjquants.core.config import JQuantsConfig
from pyjquants.core.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    RateLimitError,
    TokenExpiredError,
)

BASE_URL = "https://api.jquants.com/v1"

# Global session instance for transparent authentication
_global_session: Session | None = None
_global_session_lock = threading.Lock()


def _get_global_session() -> Session:
    """Get or create the global session instance."""
    global _global_session
    with _global_session_lock:
        if _global_session is None:
            _global_session = Session()
            _global_session.authenticate()
        return _global_session


def set_global_session(session: Session) -> None:
    """Set the global session instance."""
    global _global_session
    with _global_session_lock:
        _global_session = session


class RateLimiter:
    """Thread-safe rate limiter for API calls."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self._requests_per_minute = requests_per_minute
        self._request_timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until rate limit allows request."""
        with self._lock:
            current_time = time.time()

            # Remove timestamps older than 1 minute
            while self._request_timestamps and current_time - self._request_timestamps[0] > 60:
                self._request_timestamps.popleft()

            # Wait if at rate limit
            if len(self._request_timestamps) >= self._requests_per_minute:
                wait_time = 60 - (current_time - self._request_timestamps[0])
                if wait_time > 0:
                    time.sleep(wait_time)
                    # Re-check after waiting
                    current_time = time.time()
                    while (
                        self._request_timestamps and current_time - self._request_timestamps[0] > 60
                    ):
                        self._request_timestamps.popleft()

            self._request_timestamps.append(time.time())

    def wait_time(self) -> float:
        """Returns seconds until next request allowed."""
        with self._lock:
            if len(self._request_timestamps) < self._requests_per_minute:
                return 0.0

            current_time = time.time()
            oldest = self._request_timestamps[0]
            return max(0.0, 60 - (current_time - oldest))


class TokenManager:
    """Manages J-Quants API token lifecycle with auto-refresh."""

    def __init__(
        self,
        mail_address: str | None = None,
        password: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self._mail_address = mail_address
        self._password = password
        self._refresh_token = refresh_token
        self._id_token: str | None = None
        self._id_token_expiry: datetime | None = None
        self._http_session = requests.Session()

    @classmethod
    def from_credentials(cls, mail_address: str, password: str) -> TokenManager:
        """Create TokenManager from email and password."""
        return cls(mail_address=mail_address, password=password)

    @classmethod
    def from_refresh_token(cls, refresh_token: str) -> TokenManager:
        """Create TokenManager from refresh token."""
        return cls(refresh_token=refresh_token)

    @classmethod
    def from_environment(cls) -> TokenManager:
        """Create TokenManager from environment variables."""
        config = JQuantsConfig.from_environment()
        return cls(
            mail_address=config.mail_address,
            password=config.password,
            refresh_token=config.refresh_token,
        )

    @classmethod
    def from_config(cls, config: JQuantsConfig) -> TokenManager:
        """Create TokenManager from config object."""
        return cls(
            mail_address=config.mail_address,
            password=config.password,
            refresh_token=config.refresh_token,
        )

    def _obtain_refresh_token(self) -> str:
        """Obtain refresh token from email/password."""
        if not self._mail_address or not self._password:
            raise ConfigurationError(
                "No credentials available. Set JQUANTS_MAIL_ADDRESS and JQUANTS_PASSWORD "
                "environment variables, or provide mail_address and password."
            )

        response = self._http_session.post(
            f"{BASE_URL}/token/auth_user",
            json={"mailaddress": self._mail_address, "password": self._password},
        )

        if response.status_code != 200:
            raise AuthenticationError(f"Failed to authenticate: {response.text}")

        data = response.json()
        self._refresh_token = data.get("refreshToken")
        if not self._refresh_token:
            raise AuthenticationError("No refresh token in response")

        return self._refresh_token

    def _obtain_id_token(self) -> str:
        """Obtain ID token from refresh token."""
        if not self._refresh_token:
            self._obtain_refresh_token()

        response = self._http_session.post(
            f"{BASE_URL}/token/auth_refresh",
            params={"refreshtoken": self._refresh_token},
        )

        if response.status_code != 200:
            # Refresh token might be expired, try to get a new one
            if self._mail_address and self._password:
                self._refresh_token = None
                self._obtain_refresh_token()
                return self._obtain_id_token()
            raise TokenExpiredError(f"Failed to refresh token: {response.text}")

        data = response.json()
        self._id_token = data.get("idToken")
        if not self._id_token:
            raise AuthenticationError("No ID token in response")

        # ID token is valid for 24 hours, but refresh earlier for safety
        self._id_token_expiry = datetime.now(timezone.utc) + timedelta(hours=23)

        return self._id_token

    def id_token(self) -> str:
        """Get valid ID token, refreshing if necessary."""
        if self._id_token and self._id_token_expiry:
            if datetime.now(timezone.utc) < self._id_token_expiry:
                return self._id_token

        return self._obtain_id_token()

    def is_authenticated(self) -> bool:
        """Check if we have valid credentials."""
        return bool(self._refresh_token) or bool(self._mail_address and self._password)


class Session:
    """HTTP session with authentication, caching, and rate limiting."""

    def __init__(
        self,
        mail_address: str | None = None,
        password: str | None = None,
        refresh_token: str | None = None,
        config: JQuantsConfig | None = None,
        cache: Cache | None = None,
    ) -> None:
        # Load config
        if config is None:
            config = JQuantsConfig.load()

        # Override config with explicit parameters
        if mail_address:
            config.mail_address = mail_address
        if password:
            config.password = password
        if refresh_token:
            config.refresh_token = refresh_token

        self._config = config
        self._token_manager = TokenManager.from_config(config)
        self._rate_limiter = RateLimiter(config.requests_per_minute)
        self._http_session = requests.Session()

        # Setup cache
        if cache is not None:
            self._cache = cache
        elif config.cache_enabled:
            self._cache = TTLCache(default_ttl=config.cache_ttl_seconds)
        else:
            self._cache = NullCache()

    def authenticate(self) -> Session:
        """Authenticate and obtain tokens. Returns self for chaining."""
        if not self._config.has_credentials():
            raise ConfigurationError(
                "No credentials available. Set JQUANTS_MAIL_ADDRESS and JQUANTS_PASSWORD "
                "environment variables, or provide credentials when creating Session."
            )
        # Force token refresh
        self._token_manager.id_token()
        return self

    @property
    def is_authenticated(self) -> bool:
        """Check if session is authenticated."""
        return self._token_manager.is_authenticated()

    @property
    def cache(self) -> Cache:
        """Get the cache instance."""
        return self._cache

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Make an authenticated API request."""
        # Rate limiting
        self._rate_limiter.acquire()

        # Check cache for GET requests
        if method == "GET" and use_cache:
            cache_key = self._cache.make_key(endpoint, params)
            cached = self._cache.get(cache_key)
            if cached is not None:
                return dict(cached)

        # Get auth token
        token = self._token_manager.id_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Make request
        url = f"{BASE_URL}{endpoint}"
        response = self._http_session.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            headers=headers,
        )

        # Handle errors
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        if response.status_code == 401:
            # Try to refresh token once
            self._token_manager._id_token = None
            token = self._token_manager.id_token()
            headers = {"Authorization": f"Bearer {token}"}
            response = self._http_session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
            )
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed")

        if response.status_code >= 400:
            raise APIError(response.status_code, response.text)

        data: dict[str, Any] = response.json()

        # Cache successful GET responses
        if method == "GET" and use_cache:
            cache_key = self._cache.make_key(endpoint, params)
            self._cache.set(cache_key, data)

        return data

    def get(
        self, endpoint: str, params: dict[str, Any] | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """Make authenticated GET request."""
        return self._request("GET", endpoint, params=params, use_cache=use_cache)

    def post(
        self, endpoint: str, json_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make authenticated POST request."""
        return self._request("POST", endpoint, json_data=json_data, use_cache=False)

    def get_paginated(
        self, endpoint: str, params: dict[str, Any] | None = None, data_key: str = "list"
    ) -> Iterator[dict[str, Any]]:
        """
        Iterate through paginated API responses.

        Yields individual items from the response list.
        """
        params = params.copy() if params else {}

        while True:
            response = self.get(endpoint, params, use_cache=False)

            # Yield items from this page
            items = response.get(data_key, [])
            yield from items

            # Check for next page
            pagination_key = response.get("pagination_key")
            if not pagination_key:
                break

            params["pagination_key"] = pagination_key

    def close(self) -> None:
        """Close the HTTP session."""
        self._http_session.close()

    def __enter__(self) -> Session:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
