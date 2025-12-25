"""
Travrse SDK exceptions.

All exceptions inherit from TravrseError for easy catching.
"""

from __future__ import annotations

from typing import Any


class TravrseError(Exception):
    """Base exception for all Travrse SDK errors."""

    def __init__(self, message: str, *args: Any) -> None:
        self.message = message
        super().__init__(message, *args)


class APIError(TravrseError):
    """Exception raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.status_code:
            return f"APIError({self.status_code}): {self.message}"
        return f"APIError: {self.message}"


class AuthenticationError(APIError):
    """Exception raised when authentication fails (401/403)."""

    pass


class NotFoundError(APIError):
    """Exception raised when a resource is not found (404)."""

    pass


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        **kwargs: Any,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, **kwargs)


class ValidationError(TravrseError):
    """Exception raised when request validation fails."""

    def __init__(
        self,
        message: str,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self.errors = errors or []
        super().__init__(message)


class StreamError(TravrseError):
    """Exception raised during stream processing."""

    pass


class TimeoutError(TravrseError):
    """Exception raised when a request times out."""

    pass


class ConnectionError(TravrseError):
    """Exception raised when a connection error occurs."""

    pass
