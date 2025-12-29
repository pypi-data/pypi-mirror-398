"""
Slack client for Huitzo SDK.

This module provides client methods for Slack webhook messaging.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .client import HuitzoTools


class SlackClient:
    """Client for Slack webhook functions."""

    def __init__(self, sdk: "HuitzoTools"):
        """Initialize the SlackClient.

        Args:
            sdk: The parent HuitzoTools instance
        """
        self._sdk = sdk

    async def send_webhook_message(
        self,
        webhook_url: str,
        text: str,
        username: str | None = None,
        icon_emoji: str | None = None,
        icon_url: str | None = None,
        blocks: list[dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """
        Send a message to Slack via incoming webhook.

        Args:
            webhook_url: Slack webhook URL (from Incoming Webhooks app)
            text: Message text (fallback text if blocks provided)
            username: Override webhook username (optional)
            icon_emoji: Emoji icon (e.g., ":robot_face:") (optional)
            icon_url: Icon image URL (optional)
            blocks: List of Block Kit blocks for rich formatting (optional)

        Returns:
            Dictionary with:
            - status: "sent" or "failed"
            - error_message: Error details (if failed)

        Raises:
            ValidationError: If webhook URL or text is invalid
            RateLimitError: If Slack rate limit exceeded (1 msg/sec)
            APIError: If the API request fails

        Example:
            ```python
            # Simple text message
            result = await client.slack.send_webhook_message(
                webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                text="Hello from Huitzo! :wave:"
            )

            # With custom username and emoji
            result = await client.slack.send_webhook_message(
                webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                text="Deployment successful!",
                username="Deploy Bot",
                icon_emoji=":rocket:"
            )

            # With Block Kit blocks
            result = await client.slack.send_webhook_message(
                webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                text="Deployment notification",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Deployment Successful* :white_check_mark:"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": "*Environment:*\nProduction"},
                            {"type": "mrkdwn", "text": "*Version:*\n1.2.3"}
                        ]
                    }
                ]
            )
            ```
        """
        if not webhook_url or not webhook_url.startswith("https://hooks.slack.com/"):
            raise ValueError("Invalid Slack webhook URL")

        if not text:
            raise ValueError("Message text is required")

        args = {
            "webhook_url": webhook_url,
            "text": text,
        }

        if username is not None:
            args["username"] = username

        if icon_emoji is not None:
            args["icon_emoji"] = icon_emoji

        if icon_url is not None:
            args["icon_url"] = icon_url

        if blocks is not None:
            args["blocks"] = blocks

        payload = {
            "function": "slack.send_webhook_message",
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

    async def send_rich_message(
        self,
        webhook_url: str,
        title: str,
        text: str,
        color: str = "good",
        fields: list[dict[str, Any]] | None = None,
        footer: str | None = None,
    ) -> Dict[str, Any]:
        """
        Send a rich message to Slack using attachments.

        This is a convenience function for sending visually appealing
        messages without manually constructing Block Kit JSON.

        Args:
            webhook_url: Slack webhook URL
            title: Message title
            text: Message text
            color: Sidebar color: "good", "warning", "danger", or hex code (default: "good")
            fields: List of field dicts with "title" and "value" keys (optional)
            footer: Footer text (optional)

        Returns:
            Dictionary with status

        Color Options:
            - "good": Green (success)
            - "warning": Yellow (warning)
            - "danger": Red (error)
            - Hex code: e.g., "#36a64f"

        Raises:
            ValidationError: If webhook URL or parameters are invalid
            RateLimitError: If Slack rate limit exceeded
            APIError: If the API request fails

        Example:
            ```python
            result = await client.slack.send_rich_message(
                webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                title="Deployment Notification",
                text="Version 1.2.3 has been deployed successfully",
                color="good",
                fields=[
                    {"title": "Environment", "value": "Production", "short": True},
                    {"title": "Version", "value": "1.2.3", "short": True},
                    {"title": "Duration", "value": "2m 34s", "short": True}
                ],
                footer="Huitzo WebCLI"
            )
            ```
        """
        if not webhook_url or not webhook_url.startswith("https://hooks.slack.com/"):
            raise ValueError("Invalid Slack webhook URL")

        if not title or not text:
            raise ValueError("Title and text are required")

        args = {
            "webhook_url": webhook_url,
            "title": title,
            "text": text,
            "color": color,
        }

        if fields is not None:
            args["fields"] = fields

        if footer is not None:
            args["footer"] = footer

        payload = {
            "function": "slack.send_rich_message",
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
