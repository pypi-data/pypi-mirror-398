"""Exception hierarchy for pyjquants."""

from __future__ import annotations


class PyJQuantsError(Exception):
    """Base exception for all pyjquants errors."""

    pass


class AuthenticationError(PyJQuantsError):
    """Authentication failed."""

    pass


class TokenExpiredError(AuthenticationError):
    """Token has expired and refresh failed."""

    pass


class APIError(PyJQuantsError):
    """API request failed."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


class RateLimitError(APIError):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(status_code=429, message=message)


class NotFoundError(APIError):
    """Requested resource not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(status_code=404, message=message)


class ValidationError(PyJQuantsError):
    """Invalid input parameters."""

    pass


class ConfigurationError(PyJQuantsError):
    """Configuration error (missing credentials, invalid config file, etc.)."""

    pass
