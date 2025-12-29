"""Caching implementation for API responses."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, TypeVar

T = TypeVar("T")


class Cache(ABC):
    """Abstract base class for cache implementations."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with optional TTL in seconds."""
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values."""
        ...

    def make_key(self, *args: Any, **kwargs: Any) -> str:
        """Generate a cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]


class TTLCache(Cache):
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000) -> None:
        self._cache: dict[str, tuple[Any, float]] = {}  # key -> (value, expiry_time)
        self._lock = threading.Lock()
        self._default_ttl = default_ttl
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry_time = self._cache[key]
            if time.time() > expiry_time:
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl if ttl is not None else self._default_ttl
        expiry_time = time.time() + ttl

        with self._lock:
            # Evict oldest entries if cache is full
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_expired()
                if len(self._cache) >= self._max_size:
                    # Remove oldest entry
                    oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
                    del self._cache[oldest_key]

            self._cache[key] = (value, expiry_time)

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()

    def _evict_expired(self) -> None:
        """Remove all expired entries (must hold lock)."""
        current_time = time.time()
        expired_keys = [k for k, (_, exp) in self._cache.items() if current_time > exp]
        for key in expired_keys:
            del self._cache[key]


class NullCache(Cache):
    """No-op cache implementation (disables caching)."""

    def get(self, key: str) -> Any | None:
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        pass

    def delete(self, key: str) -> None:
        pass

    def clear(self) -> None:
        pass
