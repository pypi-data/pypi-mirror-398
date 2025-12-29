"""Core infrastructure for pyjquants."""

from pyjquants.core.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    PyJQuantsError,
    RateLimitError,
    TokenExpiredError,
    ValidationError,
)
from pyjquants.core.session import Session, TokenManager

__all__ = [
    "PyJQuantsError",
    "AuthenticationError",
    "TokenExpiredError",
    "APIError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "Session",
    "TokenManager",
]

# Optional async support
try:
    from pyjquants.core.async_session import (  # noqa: F401
        AsyncSession,
        AsyncTokenManager,
    )

    __all__.extend(["AsyncSession", "AsyncTokenManager"])
except ImportError:
    pass  # aiohttp not installed
