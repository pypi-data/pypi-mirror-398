"""
URL Shortener client for Huitzo SDK.

This module provides client methods for URL shortening.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .client import HuitzoTools


class UrlShortenerClient:
    """Client for URL shortening functions."""

    def __init__(self, sdk: "HuitzoTools"):
        """Initialize the UrlShortenerClient.

        Args:
            sdk: The parent HuitzoTools instance
        """
        self._sdk = sdk

    async def shorten_url_tinyurl(
        self,
        long_url: str,
        custom_alias: str | None = None,
    ) -> Dict[str, Any]:
        """
        Shorten a URL using TinyURL (free, no API key required).

        Args:
            long_url: URL to shorten (must be valid HTTP/HTTPS URL)
            custom_alias: Custom alias for the short URL (optional, may not be available)

        Returns:
            Dictionary with:
            - status: "success" or "failed"
            - short_url: Shortened URL (if successful)
            - long_url: Original URL
            - provider: "tinyurl"
            - error_message: Error details (if failed)

        Raises:
            ValidationError: If URL is invalid
            RateLimitError: If rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            # Basic shortening
            result = await client.url_shortener.shorten_url_tinyurl(
                "https://www.example.com/very/long/url"
            )
            print(result["short_url"])  # https://tinyurl.com/abc123

            # With custom alias
            result = await client.url_shortener.shorten_url_tinyurl(
                "https://www.example.com/page",
                custom_alias="mypage"
            )
            print(result["short_url"])  # https://tinyurl.com/mypage
            ```
        """
        if not long_url:
            raise ValueError("URL cannot be empty")

        if not long_url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        args = {"long_url": long_url}

        if custom_alias is not None:
            args["custom_alias"] = custom_alias

        payload = {
            "function": "url_shortener.shorten_url_tinyurl",
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

    async def shorten_url_isgd(
        self,
        long_url: str,
        custom_short: str | None = None,
    ) -> Dict[str, Any]:
        """
        Shorten a URL using is.gd (free, no API key required).

        Args:
            long_url: URL to shorten (must be valid HTTP/HTTPS URL)
            custom_short: Custom shortcode (optional, 5-30 chars, alphanumeric + underscore)

        Returns:
            Dictionary with:
            - status: "success" or "failed"
            - short_url: Shortened URL (if successful)
            - long_url: Original URL
            - provider: "is.gd"
            - error_message: Error details (if failed)

        Raises:
            ValidationError: If URL or custom shortcode is invalid
            RateLimitError: If rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            # Basic shortening
            result = await client.url_shortener.shorten_url_isgd(
                "https://www.example.com/very/long/url"
            )
            print(result["short_url"])  # https://is.gd/abc123

            # With custom shortcode
            result = await client.url_shortener.shorten_url_isgd(
                "https://www.example.com/page",
                custom_short="mypage"
            )
            print(result["short_url"])  # https://is.gd/mypage
            ```
        """
        if not long_url:
            raise ValueError("URL cannot be empty")

        if not long_url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        if custom_short:
            if len(custom_short) < 5 or len(custom_short) > 30:
                raise ValueError("Custom shortcode must be 5-30 characters")

            if not custom_short.replace("_", "").isalnum():
                raise ValueError("Custom shortcode must be alphanumeric (plus underscore)")

        args = {"long_url": long_url}

        if custom_short is not None:
            args["custom_short"] = custom_short

        payload = {
            "function": "url_shortener.shorten_url_isgd",
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
