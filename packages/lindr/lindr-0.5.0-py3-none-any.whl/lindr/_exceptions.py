"""Lindr SDK exceptions."""

from __future__ import annotations


class LindrError(Exception):
    """Base exception for Lindr SDK."""

    pass


class AuthenticationError(LindrError):
    """API key is missing or invalid."""

    pass


class NotFoundError(LindrError):
    """Requested resource was not found."""

    pass


class ValidationError(LindrError):
    """Request validation failed."""

    def __init__(self, message: str, details: list | None = None):
        super().__init__(message)
        self.details = details


class RateLimitError(LindrError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class APIError(LindrError):
    """General API error."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class ConnectionError(LindrError):
    """Network connection error (connection failed, timeout, etc.)."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error
