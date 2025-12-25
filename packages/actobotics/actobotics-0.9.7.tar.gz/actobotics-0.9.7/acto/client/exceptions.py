"""
ACTO API Client Exceptions.

Custom exceptions for API client operations.
"""

from __future__ import annotations

from typing import Any


class ACTOClientError(Exception):
    """Base exception for ACTO client errors."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(ACTOClientError):
    """Raised when authentication fails (401)."""

    pass


class AuthorizationError(ACTOClientError):
    """Raised when authorization fails (403) - usually insufficient token balance."""

    pass


class NotFoundError(ACTOClientError):
    """Raised when a resource is not found (404)."""

    pass


class ValidationError(ACTOClientError):
    """Raised when request validation fails (400, 422)."""

    pass


class RateLimitError(ACTOClientError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after


class ServerError(ACTOClientError):
    """Raised when server returns 5xx error."""

    pass


class NetworkError(ACTOClientError):
    """Raised when network connection fails."""

    pass

