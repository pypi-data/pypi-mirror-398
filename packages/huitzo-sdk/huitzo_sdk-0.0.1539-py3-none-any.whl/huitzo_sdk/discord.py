"""
Discord client for Huitzo SDK.

This module provides client methods for Discord webhook messaging.
"""

# Discord module for Huitzo SDK

# This module will handle Discord interactions for the Huitzo SDK.

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .client import HuitzoTools


class DiscordClient:
    """Client for Discord webhook functions."""

    def __init__(self, sdk: "HuitzoTools"):
        """Initialize the DiscordClient.

        Args:
            sdk: The parent HuitzoTools instance
        """
        self._sdk = sdk

    async def send_webhook_message(
        self,
        webhook_url: str,
        content: str,
        username: str | None = None,
        avatar_url: str | None = None,
        tts: bool = False,
        embeds: list[dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """
        Send a message to Discord via incoming webhook.

        Args:
            webhook_url: Discord webhook URL (from channel settings)
            content: Message text (max 2000 chars)
            username: Override webhook username (optional)
            avatar_url: Override webhook avatar URL (optional)
            tts: Text-to-speech flag (default: False)
            embeds: List of embed objects for rich formatting (optional, max 10)

        Returns:
            Dictionary with:
            - status: "sent" or "failed"
            - message_id: Discord message ID (if successful)
            - error_message: Error details (if failed)

        Raises:
            ValidationError: If webhook URL or content is invalid
            RateLimitError: If Discord rate limit exceeded (5 req/2s)
            APIError: If the API request fails

        Example:
            ```python
            # Simple text message
            result = await client.discord.send_webhook_message(
                webhook_url="https://discord.com/api/webhooks/YOUR/WEBHOOK",
                content="Hello from Huitzo! 👋"
            )

            # Rich embed message
            result = await client.discord.send_webhook_message(
                webhook_url="https://discord.com/api/webhooks/YOUR/WEBHOOK",
                content="Deployment notification",
                embeds=[
                    {
                        "title": "Deployment Successful",
                        "description": "Version 1.2.3 deployed to production",
                        "color": 5763719,  # Green color (0x57F287)
                        "fields": [
                            {"name": "Environment", "value": "Production", "inline": True},
                            {"name": "Version", "value": "1.2.3", "inline": True}
                        ]
                    }
                ]
            )
            ```
        """
        if not webhook_url or not webhook_url.startswith("https://discord.com/api/webhooks/"):
            raise ValueError("Invalid Discord webhook URL")

        if not content and not embeds:
            raise ValueError("Message must have content or embeds")

        if content and len(content) > 2000:
            raise ValueError(f"Content too long: {len(content)} chars (max 2000)")

        if embeds and len(embeds) > 10:
            raise ValueError(f"Too many embeds: {len(embeds)} (max 10)")

        args = {
            "webhook_url": webhook_url,
            "content": content,
            "tts": tts,
        }

        if username is not None:
            args["username"] = username

        if avatar_url is not None:
            args["avatar_url"] = avatar_url

        if embeds is not None:
            args["embeds"] = embeds

        payload = {
            "function": "discord.send_webhook_message",
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

    async def send_rich_embed(
        self,
        webhook_url: str,
        title: str,
        description: str,
        color: int | None = None,
        fields: list[dict[str, Any]] | None = None,
        thumbnail_url: str | None = None,
        image_url: str | None = None,
        footer_text: str | None = None,
    ) -> Dict[str, Any]:
        """
        Send a rich embed message to Discord.

        This is a convenience function for sending visually appealing embeds
        without manually constructing embed JSON.

        Args:
            webhook_url: Discord webhook URL
            title: Embed title (max 256 chars)
            description: Embed description (max 4096 chars)
            color: Embed color (decimal, e.g., 5763719 for green)
            fields: List of field dicts with "name", "value", "inline" keys (max 25)
            thumbnail_url: Thumbnail image URL (optional)
            image_url: Large image URL (optional)
            footer_text: Footer text (optional, max 2048 chars)

        Returns:
            Dictionary with status and message_id

        Color Examples:
            - Green (success): 5763719 (0x57F287)
            - Yellow (warning): 16776960 (0xFFFF00)
            - Red (error): 15548997 (0xED4245)
            - Blue (info): 5793266 (0x5865F2)

        Raises:
            ValidationError: If webhook URL or parameters are invalid
            RateLimitError: If Discord rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            result = await client.discord.send_rich_embed(
                webhook_url="https://discord.com/api/webhooks/YOUR/WEBHOOK",
                title="Deployment Notification",
                description="Version 1.2.3 has been deployed successfully",
                color=5763719,  # Green
                fields=[
                    {"name": "Environment", "value": "Production", "inline": True},
                    {"name": "Version", "value": "1.2.3", "inline": True},
                    {"name": "Duration", "value": "2m 34s", "inline": True}
                ],
                footer_text="Huitzo WebCLI"
            )
            ```
        """
        if not webhook_url or not webhook_url.startswith("https://discord.com/api/webhooks/"):
            raise ValueError("Invalid Discord webhook URL")

        if not title or not description:
            raise ValueError("Title and description are required")

        if len(title) > 256:
            raise ValueError(f"Title too long: {len(title)} chars (max 256)")

        if len(description) > 4096:
            raise ValueError(f"Description too long: {len(description)} chars (max 4096)")

        if fields and len(fields) > 25:
            raise ValueError(f"Too many fields: {len(fields)} (max 25)")

        args = {
            "webhook_url": webhook_url,
            "title": title,
            "description": description,
        }

        if color is not None:
            args["color"] = color

        if fields is not None:
            args["fields"] = fields

        if thumbnail_url is not None:
            args["thumbnail_url"] = thumbnail_url

        if image_url is not None:
            args["image_url"] = image_url

        if footer_text is not None:
            args["footer_text"] = footer_text

        payload = {
            "function": "discord.send_rich_embed",
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
