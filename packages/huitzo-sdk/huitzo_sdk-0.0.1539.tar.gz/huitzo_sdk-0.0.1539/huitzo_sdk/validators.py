"""
Validators client for Huitzo SDK.

This module provides client methods for email and URL validation functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .client import HuitzoTools


class ValidatorsClient:
    """Client for email and URL validation functions."""

    def __init__(self, sdk: "HuitzoTools"):
        """Initialize the ValidatorsClient.

        Args:
            sdk: The parent HuitzoTools instance
        """
        self._sdk = sdk

    async def validate_email(
        self,
        email: str,
        check_dns: bool = True,
        check_disposable: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate an email address with syntax, DNS, and disposable domain checks.

        Args:
            email: Email address to validate
            check_dns: Check DNS MX records (default: True)
            check_disposable: Check if domain is disposable (default: True)

        Returns:
            Dictionary with:
            - valid: True if email is valid
            - email: Normalized email address
            - domain: Email domain
            - mx_records: List of MX records (if check_dns=True)
            - is_disposable: True if disposable domain (if check_disposable=True)
            - error_message: Error details (if invalid)
            - warning: Warning message (if applicable)

        Raises:
            ValidationError: If email format is invalid
            RateLimitError: If rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            # Basic validation
            result = await client.validators.validate_email("user@example.com")
            if result["valid"]:
                print(f"Valid email: {result['email']}")
            else:
                print(f"Invalid: {result['error_message']}")

            # Skip DNS check
            result = await client.validators.validate_email(
                "test@example.com",
                check_dns=False
            )

            # Check for disposable domains
            result = await client.validators.validate_email(
                "temp@tempmail.com",
                check_disposable=True
            )
            if result.get("is_disposable"):
                print("Warning: Disposable email domain")
            ```
        """
        if not email:
            raise ValueError("Email address cannot be empty")

        payload = {
            "function": "validators.validate_email",
            "args": {
                "email": email,
                "check_dns": check_dns,
                "check_disposable": check_disposable,
            },
        }

        response = await self._sdk._client.post(
            f"{self._sdk._base_url}/api/v1/executor/run",
            json=payload,
        )

        result = await self._sdk._handle_response(response, expected_status=200)

        # Extract result from executor envelope
        if result.get("status") == "success":
            return result.get("result", {})
        else:
            raise Exception(result.get("error", "Unknown error"))

    async def validate_url(
        self,
        url: str,
        check_dns: bool = False,
        allowed_schemes: list[str] | None = None,
    ) -> Dict[str, Any]:
        """
        Validate a URL with syntax and optional DNS checks.

        Args:
            url: URL to validate
            check_dns: Check if domain resolves (default: False)
            allowed_schemes: List of allowed schemes (default: ["http", "https"])

        Returns:
            Dictionary with:
            - valid: True if URL is valid
            - url: Normalized URL
            - scheme: URL scheme (http, https, etc.)
            - domain: Domain name
            - path: URL path
            - is_ip: True if domain is IP address
            - error_message: Error details (if invalid)

        Raises:
            ValidationError: If URL format is invalid
            RateLimitError: If rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            # Basic validation
            result = await client.validators.validate_url("https://example.com")
            if result["valid"]:
                print(f"Valid URL: {result['url']}")

            # With DNS check
            result = await client.validators.validate_url(
                "https://example.com",
                check_dns=True
            )

            # Custom allowed schemes
            result = await client.validators.validate_url(
                "ftp://files.example.com",
                allowed_schemes=["ftp", "ftps"]
            )
            ```
        """
        if not url:
            raise ValueError("URL cannot be empty")

        args = {
            "url": url,
            "check_dns": check_dns,
        }

        if allowed_schemes is not None:
            args["allowed_schemes"] = allowed_schemes

        payload = {
            "function": "validators.validate_url",
            "args": args,
        }

        response = await self._sdk._client.post(
            f"{self._sdk._base_url}/api/v1/executor/run",
            json=payload,
        )

        result = await self._sdk._handle_response(response, expected_status=200)

        # Extract result from executor envelope
        if result.get("status") == "success":
            return result.get("result", {})
        else:
            raise Exception(result.get("error", "Unknown error"))
