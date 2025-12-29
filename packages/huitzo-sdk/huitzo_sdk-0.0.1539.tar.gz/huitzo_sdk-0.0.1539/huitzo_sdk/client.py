"""
Main Huitzo SDK client.

This module provides the HuitzoTools class, the main entry point for the SDK.
It manages the HTTP session and provides access to CRON and Email service clients.

Usage:
    ```python
    from huitzo_sdk import HuitzoTools

    async with HuitzoTools(api_token="your_token") as sdk:
        # Use CRON service
        job = await sdk.cron.schedule(...)

        # Use Email service
        result = await sdk.email.send(...)
    ```
"""

# Client module for Huitzo SDK

# This module will handle client interactions for the Huitzo SDK.

from __future__ import annotations

import logging
import os
from types import TracebackType
from typing import Any, Type

import aiohttp

from .cron import CronClient
from .discord import DiscordClient
from .email import EmailClient
from .files import FilesClient
from .formatters import FormattersClient
from .llm import LLMClient
from .pdf_generator import PdfGeneratorClient
from .qrcode import QrCodeClient
from .sites import SitesClient
from .slack import SlackClient
from .telegram import TelegramClient
from .url_shortener import UrlShortenerClient
from .validators import ValidatorsClient
from .exceptions import (
    AuthenticationError,
    HuitzoAPIError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    ValidationError,
)
from .protocols.command import CommandContext

logger = logging.getLogger(__name__)


class HuitzoTools:
    """
    Main SDK client for Huitzo Developer Tools platform.

    This class provides access to all Huitzo services through a unified interface.
    It manages HTTP sessions and authentication automatically.

    Attributes:
        cron: CronClient for CRON Scheduling Service
        discord: DiscordClient for Discord Webhook Service
        email: EmailClient for Email Service
        files: FilesClient for File Upload Service
        formatters: FormattersClient for Text Formatting Service
        llm: LLMClient for LLM Completions Service
        pdf_generator: PdfGeneratorClient for PDF Generation Service
        qrcode: QrCodeClient for QR Code Generation Service
        sites: SitesClient for Static Site Hosting Service
        slack: SlackClient for Slack Webhook Service
        telegram: TelegramClient for Telegram Messaging Service
        url_shortener: UrlShortenerClient for URL Shortening Service
        validators: ValidatorsClient for Email/URL Validation Service
        base_url: Base URL for API requests
        api_token: API token for authentication

    Example:
        ```python
        async with HuitzoTools(api_token="your_token") as sdk:
            # Schedule a job
            job = await sdk.cron.schedule(
                name="daily_report",
                command="finance.report.generate",
                schedule="0 9 * * *",
                timezone="UTC"
            )

            # Send email
            await sdk.email.send(
                recipient_user_id="user-uuid",
                subject="Daily Report Ready",
                html_body="<p>Your report is ready!</p>"
            )
        ```
    """

    def __init__(
        self,
        api_token: str,
        base_url: str = "http://localhost:8010",
        timeout: int = 30,
        user_id: str | None = None,
    ):
        """
        Initialize HuitzoTools SDK client.

        Args:
            api_token: API token for authentication (required)
            base_url: Base URL for API requests (default: http://localhost:8010)
            timeout: Request timeout in seconds (default: 30)
            user_id: Optional user ID for plugin API authentication (X-User-ID header)

        Raises:
            ValueError: If api_token is not provided
        """
        if not api_token:
            raise ValueError("api_token is required")

        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._user_id = user_id  # Store user_id for X-User-ID header
        self._session: aiohttp.ClientSession | None = None

        # Initialize service clients (they will use the session from __aenter__)
        self.cron = CronClient(self)
        self.discord = DiscordClient(self)
        self.email = EmailClient(self)
        self.files = FilesClient(self)
        self.formatters = FormattersClient(self)
        self.llm = LLMClient(self)
        self.pdf_generator = PdfGeneratorClient(self)
        self.qrcode = QrCodeClient(self)
        self.sites = SitesClient(self)
        self.slack = SlackClient(self)
        self.telegram = TelegramClient(self)
        self.url_shortener = UrlShortenerClient(self)
        self.validators = ValidatorsClient(self)

    @classmethod
    def from_command_context(
        cls,
        context: CommandContext,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> "HuitzoTools":
        """
        Create HuitzoTools from CommandContext for plugin use.

        This is a convenience method for plugins that receive a CommandContext
        during command execution and need to call backend APIs.

        Args:
            context: Command execution context containing internal_auth_token
            base_url: Optional base URL override (default: from WEBCLI_API_URL env var
                     or http://localhost:8010)
            timeout: Request timeout in seconds (default: 30)

        Returns:
            HuitzoTools instance configured for internal plugin-to-backend communication

        Raises:
            ValueError: If context.internal_auth_token is missing

        Example:
            ```python
            from huitzo_sdk import HuitzoTools, CommandContext, CommandResult

            class MyCommand:
                async def execute(self, args: dict, context: CommandContext) -> CommandResult:
                    # Create SDK client from context
                    async with HuitzoTools.from_command_context(context) as sdk:
                        # Use LLM service
                        response = await sdk.llm.complete(
                            prompt="Hello world",
                            user_id=context.user_id
                        )
                        return CommandResult(exit_code=0, stdout=response.content)
            ```
        """
        api_token = context.internal_auth_token or os.getenv("WEBCLI_PLUGIN_API_KEY")
        if not api_token:
            raise ValueError(
                "CommandContext.internal_auth_token is required for plugin API authentication. "
                "Ensure the backend is passing the plugin API key in the context "
                "or set WEBCLI_PLUGIN_API_KEY in the environment."
            )

        # Default to localhost for internal calls
        url = base_url or os.getenv("WEBCLI_API_URL", "http://localhost:8010")

        return cls(
            api_token=api_token,
            base_url=url,
            timeout=timeout,
            user_id=str(context.user_id),  # Pass user_id for X-User-ID header
        )

    async def __aenter__(self) -> "HuitzoTools":
        """
        Enter async context manager.

        Creates the aiohttp ClientSession for making HTTP requests.

        Returns:
            Self for use in async with statement
        """
        # Create aiohttp session with timeout
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)

        logger.debug(f"HuitzoTools session initialized (base_url={self.base_url})")
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit async context manager.

        Properly closes the aiohttp ClientSession to clean up resources.

        Args:
            exc_type: Exception type (if exception occurred)
            exc_val: Exception value (if exception occurred)
            exc_tb: Exception traceback (if exception occurred)
        """
        if self._session:
            await self._session.close()
            self._session = None
            logger.debug("HuitzoTools session closed")

    def _get_headers(self) -> dict[str, str]:
        """
        Get HTTP headers for API requests.

        Returns:
            Dictionary of HTTP headers including authentication

        Raises:
            RuntimeError: If called outside async context manager
        """
        if not self._session:
            raise RuntimeError(
                "HuitzoTools must be used within async context manager: "
                "async with HuitzoTools(...) as sdk:"
            )

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "User-Agent": "huitzo-sdk/2.1.0",
        }

        # Add X-User-ID header for plugin API authentication
        if self._user_id:
            headers["X-User-ID"] = self._user_id

        return headers

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
        expected_status: int = 200,
    ) -> Any:
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: aiohttp ClientResponse object
            expected_status: Expected HTTP status code (default: 200)

        Returns:
            Parsed JSON response (if applicable)

        Raises:
            AuthenticationError: 401/403 authentication failures
            NotFoundError: 404 resource not found
            RateLimitError: 429 rate limit exceeded
            ValidationError: 400 validation errors
            HuitzoAPIError: Other API errors
        """
        status = response.status

        # Handle successful responses
        if status == expected_status:
            # 204 No Content has no response body
            if status == 204:
                return None

            # Parse JSON response
            try:
                return await response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise HuitzoAPIError(
                    f"Invalid JSON response from API",
                    status_code=status,
                )

        # Handle error responses
        try:
            error_data = await response.json()
            error_message = error_data.get("detail", f"HTTP {status}")
        except Exception:
            # If JSON parsing fails, use text response
            try:
                error_message = await response.text()
            except Exception:
                error_message = f"HTTP {status}"
            error_data = {}

        # Map status codes to exceptions
        if status in (401, 403):
            raise AuthenticationError(
                message=error_message,
                status_code=status,
                response_data=error_data,
            )
        elif status == 404:
            raise NotFoundError(
                message=error_message,
                response_data=error_data,
            )
        elif status == 429:
            raise RateLimitError(
                message=error_message,
                response_data=error_data,
            )
        elif status == 400:
            raise ValidationError(
                message=error_message,
                response_data=error_data,
            )
        else:
            # Generic API error for other status codes
            raise HuitzoAPIError(
                message=error_message,
                status_code=status,
                response_data=error_data,
            )

    async def close(self) -> None:
        """
        Explicitly close the HTTP session.

        This method is provided for cases where the context manager
        cannot be used. Prefer using the async context manager when possible.

        Example:
            ```python
            sdk = HuitzoTools(api_token="your_token")
            await sdk.__aenter__()
            try:
                job = await sdk.cron.list()
            finally:
                await sdk.close()
            ```
        """
        if self._session:
            await self._session.close()
            self._session = None
            logger.debug("HuitzoTools session closed (explicit)")
