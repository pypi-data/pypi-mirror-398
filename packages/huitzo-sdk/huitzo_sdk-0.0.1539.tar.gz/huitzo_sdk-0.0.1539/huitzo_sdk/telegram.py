"""
Telegram Service client for Huitzo SDK.

This module provides the TelegramClient class for sending Telegram messages:
- send(): Send a message via Telegram Bot API

All methods are async and handle error responses appropriately.

**Security:**
- Bot tokens are plugin-owned secrets (never persisted by platform)
- Tokens must be provided for each request
- Tokens are masked in backend logs

**Rate Limits:**
- Per chat: ≤1 msg/second (short bursts tolerated)
- Groups: ≤20 msgs/minute
- Global: ~30 msgs/second (free tier)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .exceptions import (
    AuthenticationError,
    HuitzoAPIError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

if TYPE_CHECKING:
    from .client import HuitzoTools


class TelegramClient:
    """
    Client for Telegram Service.

    This client provides methods for sending Telegram messages using
    plugin-owned bot tokens. The platform does not store or persist tokens.

    Example:
        ```python
        async with HuitzoTools(api_token="your_token") as sdk:
            # Send a simple message
            result = await sdk.telegram.send(
                bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
                chat_id="123456789",
                message="Hello from Huitzo!",
                parse_mode="HTML"
            )
            print(f"Message sent: {result['message_id']}")
        ```
    """

    def __init__(self, sdk: "HuitzoTools"):
        """
        Initialize TelegramClient.

        Args:
            sdk: Parent HuitzoTools instance
        """
        self._sdk = sdk

    async def send(
        self,
        bot_token: str,
        chat_id: str | int,
        message: str,
        parse_mode: str | None = None,
        disable_notification: bool = False,
        protect_content: bool = False,
        link_preview_options: dict[str, Any] | None = None,
        message_thread_id: int | None = None,
        reply_parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send a Telegram message via Bot API.

        Sends a message to a chat using the provided bot token. The token
        is plugin-owned and is not stored by the platform.

        Args:
            bot_token: Telegram Bot API token (from @BotFather)
            chat_id: Target chat ID (numeric) or @username
            message: Message text (1-4096 chars)
            parse_mode: Message formatting ("MarkdownV2", "HTML", or None)
            disable_notification: Send silently without notification
            protect_content: Protect content from forwarding/saving
            link_preview_options: Link preview configuration
            message_thread_id: Forum topic thread ID (for forum groups)
            reply_parameters: Reply message parameters

        Returns:
            Dictionary containing:
            - message_id: Telegram message ID (if sent successfully)
            - chat_id: Target chat ID
            - date: Unix timestamp of message
            - status: "sent", "queued", or "failed"
            - error_message: Error details (if failed)
            - retry_after: Seconds to wait before retry (if rate limited)

        Raises:
            ValidationError: Invalid parameters (message too long, invalid parse_mode, etc.)
            NotFoundError: Chat not found
            RateLimitError: Rate limit exceeded (includes retry_after)
            AuthenticationError: Invalid API token (platform auth, not bot token)
            HuitzoAPIError: Other API errors (bot blocked, forbidden, upstream errors)

        Rate Limits:
            - Per chat: ≤1 msg/second (short bursts tolerated)
            - Groups: ≤20 msgs/minute
            - Global: ~30 msgs/second (free tier)
            - When rate limited (429), retry_after indicates seconds to wait

        Message Constraints:
            - Length: 1-4096 characters (after entity parsing)
            - parse_mode: "MarkdownV2", "HTML", or None (legacy "Markdown" is deprecated)
            - Messages >4096 chars should be split manually

        Example:
            ```python
            # Send simple text message
            result = await sdk.telegram.send(
                bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
                chat_id="123456789",
                message="Hello! This is a test message."
            )

            # Send HTML formatted message
            result = await sdk.telegram.send(
                bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
                chat_id="@mychannel",
                message="<b>Bold text</b> and <i>italic text</i>",
                parse_mode="HTML",
                disable_notification=True
            )

            # Send to forum topic
            result = await sdk.telegram.send(
                bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
                chat_id="-1001234567890",
                message="Message to forum topic",
                message_thread_id=42
            )

            # Handle rate limiting
            try:
                result = await sdk.telegram.send(...)
            except RateLimitError as e:
                retry_after = e.retry_after or 60
                print(f"Rate limited! Retry after {retry_after} seconds")
            ```
        """
        # Client-side validation
        if not bot_token or len(bot_token) < 10:
            raise ValidationError(
                "Invalid bot_token: must be a valid Telegram Bot API token from @BotFather"
            )

        if not message or len(message) < 1:
            raise ValidationError("Message cannot be empty")

        if len(message) > 4096:
            raise ValidationError(
                f"Message too long: {len(message)} chars (max 4096). "
                "Consider splitting into multiple messages."
            )

        if parse_mode and parse_mode not in ["MarkdownV2", "HTML"]:
            raise ValidationError(
                f"Invalid parse_mode: {parse_mode}. Supported values: 'MarkdownV2', 'HTML', or None. "
                "Legacy 'Markdown' is deprecated by Telegram."
            )

        # Build function arguments
        args: dict[str, Any] = {
            "bot_token": bot_token,
            "chat_id": chat_id,
            "message": message,
        }

        if parse_mode:
            args["parse_mode"] = parse_mode

        if disable_notification:
            args["disable_notification"] = disable_notification

        if protect_content:
            args["protect_content"] = protect_content

        if link_preview_options:
            args["link_preview_options"] = link_preview_options

        if message_thread_id:
            args["message_thread_id"] = message_thread_id

        if reply_parameters:
            args["reply_parameters"] = reply_parameters

        # Build request payload for Executor service
        payload = {
            "function": "telegram.send_message",
            "args": args,
        }

        # Make API request to Executor endpoint
        async with self._sdk._session.post(
            f"{self._sdk.base_url}/api/v1/executor/run",
            json=payload,
            headers=self._sdk._get_headers(),
        ) as response:
            # Handle rate limit errors specially to include retry_after
            if response.status == 429:
                data = await response.json()
                retry_after = None
                if isinstance(data, dict):
                    # Extract retry_after from error detail
                    detail = data.get("detail", {})
                    if isinstance(detail, dict):
                        retry_after = detail.get("retry_after")

                raise RateLimitError(
                    "Telegram rate limit exceeded. "
                    f"Retry after {retry_after or 'unknown'} seconds.",
                    retry_after=retry_after,
                )

            # Handle executor response
            result = await self._sdk._handle_response(response, expected_status=200)

            # Extract the actual function result from the executor response
            # Executor returns: {"function": "...", "status": "success", "result": {...}}
            if isinstance(result, dict) and result.get("status") == "success":
                return result.get("result", {})
            else:
                # If execution failed, the error is already raised by _handle_response
                return result
