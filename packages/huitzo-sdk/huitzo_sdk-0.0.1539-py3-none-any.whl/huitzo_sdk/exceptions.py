"""
Custom exceptions for Huitzo SDK.

This module defines exception classes for handling API errors:
- HuitzoAPIError: Base exception for all API-related errors
- AuthenticationError: 401/403 authentication/authorization failures
- NotFoundError: 404 resource not found errors
- RateLimitError: 429 rate limit exceeded errors
- ValidationError: 400 validation/bad request errors
"""

from __future__ import annotations


class HuitzoAPIError(Exception):
    """
    Base exception for all Huitzo API errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (if applicable)
        response_data: Raw response data from API
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(HuitzoAPIError):
    """
    Raised when authentication or authorization fails (401/403).

    This typically indicates:
    - Invalid or expired API token
    - Missing authentication credentials
    - Insufficient permissions for the requested operation
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int = 401,
        response_data: dict | None = None,
    ):
        super().__init__(message, status_code, response_data)


class NotFoundError(HuitzoAPIError):
    """
    Raised when a requested resource is not found (404).

    This indicates:
    - Job ID does not exist
    - Message ID does not exist
    - Template ID does not exist
    - Resource belongs to another user
    """

    def __init__(
        self,
        message: str = "Resource not found",
        response_data: dict | None = None,
    ):
        super().__init__(message, status_code=404, response_data=response_data)


class RateLimitError(HuitzoAPIError):
    """
    Raised when API rate limits are exceeded (429).

    This indicates:
    - Job quota exceeded for user's plan
    - Daily email limit reached
    - Too many concurrent requests
    - Telegram rate limit exceeded

    Users should wait before retrying or upgrade their plan.

    Attributes:
        retry_after: Optional seconds to wait before retry (for Telegram rate limits)
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        response_data: dict | None = None,
        retry_after: int | None = None,
    ):
        super().__init__(message, status_code=429, response_data=response_data)
        self.retry_after = retry_after


class ValidationError(HuitzoAPIError):
    """
    Raised when request validation fails (400).

    This indicates:
    - Invalid CRON expression
    - Invalid timezone
    - Missing required fields
    - Invalid field values
    """

    def __init__(
        self,
        message: str = "Validation error",
        response_data: dict | None = None,
    ):
        super().__init__(message, status_code=400, response_data=response_data)


class QuotaExceededError(HuitzoAPIError):
    """
    Raised when user quota limits are exceeded (403).

    This indicates:
    - Maximum number of sites reached (5 sites per user)
    - Total storage limit exceeded (200MB per user)
    - User needs to delete existing sites or upgrade plan

    Users should clean up unused sites or upgrade their plan.
    """

    def __init__(
        self,
        message: str = "Quota exceeded",
        response_data: dict | None = None,
    ):
        super().__init__(message, status_code=403, response_data=response_data)
