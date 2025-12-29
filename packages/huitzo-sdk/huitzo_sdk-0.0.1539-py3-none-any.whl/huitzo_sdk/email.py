"""
Email Service client for Huitzo SDK.

This module provides the EmailClient class for managing email operations:
- send(): Queue an email for delivery
- list(): List sent emails with filtering and pagination
- get(): Get detailed email information
- create_template(): Create a new email template
- list_templates(): List available email templates

All methods are async and handle error responses appropriately.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID

from .exceptions import (
    AuthenticationError,
    HuitzoAPIError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from .models import CreateTemplateRequest, SendEmailRequest

if TYPE_CHECKING:
    from .client import HuitzoTools


class EmailClient:
    """
    Client for Email Service.

    This client provides methods for sending emails and managing email templates
    with Jinja2 variable substitution support.

    Example:
        ```python
        async with HuitzoTools(api_token="your_token") as sdk:
            # Send a simple email
            result = await sdk.email.send(
                recipient_user_id="123e4567-e89b-12d3-a456-426614174000",
                subject="Welcome to Huitzo",
                html_body="<h1>Welcome!</h1>",
                plain_text_body="Welcome!"
            )
            print(f"Message queued: {result['message_id']}")
        ```
    """

    def __init__(self, sdk: "HuitzoTools"):
        """
        Initialize EmailClient.

        Args:
            sdk: Parent HuitzoTools instance
        """
        self._sdk = sdk

    async def send(
        self,
        recipient_user_id: str | UUID,
        subject: str,
        html_body: str | None = None,
        plain_text_body: str | None = None,
        template_id: str | UUID | None = None,
        template_variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Send an email to a user.

        Queues an email for delivery via SendGrid. Emails are sent asynchronously
        by background workers, typically within 1 minute.

        Must provide either:
        - html_body and/or plain_text_body, OR
        - template_id with template_variables

        Args:
            recipient_user_id: UUID of the recipient user
            subject: Email subject line
            html_body: HTML email content (optional if using template)
            plain_text_body: Plain text email content (optional, fallback)
            template_id: UUID of email template to use (optional)
            template_variables: Variables for template rendering (optional)

        Returns:
            Dictionary containing:
            - message_id: Email message UUID
            - status: Email status (typically "queued")
            - estimated_delivery: ISO timestamp of estimated delivery

        Raises:
            ValidationError: Invalid email parameters or missing body
            NotFoundError: Recipient user or template not found
            RateLimitError: Daily email limit exceeded for user's plan
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Rate Limits (per day):
            - FREE: 100 emails
            - PRO: 1000 emails
            - ENTERPRISE: Unlimited

        Example:
            ```python
            # Send with direct content
            result = await sdk.email.send(
                recipient_user_id="123e4567-e89b-12d3-a456-426614174000",
                subject="Weekly Report",
                html_body="<h1>Report</h1><p>Your weekly summary...</p>",
                plain_text_body="Report: Your weekly summary..."
            )

            # Send using template
            result = await sdk.email.send(
                recipient_user_id="123e4567-e89b-12d3-a456-426614174000",
                subject="Weekly Report",
                template_id="template-uuid",
                template_variables={"user_name": "John", "report_date": "2025-10-06"}
            )
            ```
        """
        # Convert string UUIDs to UUID objects
        if isinstance(recipient_user_id, str):
            recipient_user_id = UUID(recipient_user_id)
        if isinstance(template_id, str):
            template_id = UUID(template_id)

        # Validate request using Pydantic model
        request = SendEmailRequest(
            recipient_user_id=recipient_user_id,
            subject=subject,
            html_body=html_body,
            plain_text_body=plain_text_body,
            template_id=template_id,
            template_variables=template_variables,
        )

        # Make API request
        async with self._sdk._session.post(
            f"{self._sdk.base_url}/api/v1/tools/email/send",
            json=request.model_dump(mode="json", exclude_none=True),
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response, expected_status=202)

    async def list(
        self,
        status: str | None = None,
        date_from: str | datetime | None = None,
        date_to: str | datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List sent emails.

        Retrieves a paginated list of emails sent by the authenticated user,
        with optional filtering by status and date range.

        Args:
            status: Optional status filter ("queued", "sending", "sent", "failed", "bounced")
            date_from: Start date for filtering (ISO format string or datetime)
            date_to: End date for filtering (ISO format string or datetime)
            limit: Maximum number of results (1-100, default: 50)
            offset: Pagination offset (default: 0)

        Returns:
            Dictionary containing:
            - messages: List of email objects with details
            - total: Total number of emails matching filter
            - limit: Limit used for this request
            - offset: Offset used for this request

        Raises:
            ValidationError: Invalid date format
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            # Get all sent emails
            result = await sdk.email.list(status="sent", limit=20)
            for email in result["messages"]:
                print(f"{email['subject']}: {email['status']}")

            # Get emails from last week
            from datetime import datetime, timezone, timedelta
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            result = await sdk.email.list(date_from=week_ago)
            ```
        """
        # Build query parameters
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        if status:
            params["status"] = status

        if date_from:
            if isinstance(date_from, datetime):
                params["date_from"] = date_from.isoformat()
            else:
                params["date_from"] = date_from

        if date_to:
            if isinstance(date_to, datetime):
                params["date_to"] = date_to.isoformat()
            else:
                params["date_to"] = date_to

        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/email/messages",
            params=params,
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)

    async def get(self, message_id: str | UUID) -> dict[str, Any]:
        """
        Get detailed email information.

        Retrieves complete email metadata (does not include body content for privacy).

        Args:
            message_id: Email message UUID

        Returns:
            Email details including:
            - id: Message UUID
            - recipient_email: Recipient email address
            - subject: Email subject
            - status: Email status
            - created_at: When email was queued
            - sent_at: When email was sent (if applicable)
            - sendgrid_message_id: SendGrid message ID (if sent)
            - error_message: Error details (if failed)

        Raises:
            NotFoundError: Email not found or belongs to another user
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            email = await sdk.email.get("123e4567-e89b-12d3-a456-426614174000")
            print(f"Status: {email['status']}")
            if email['status'] == 'failed':
                print(f"Error: {email['error_message']}")
            ```
        """
        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/email/messages/{message_id}",
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)

    async def create_template(
        self,
        name: str,
        subject: str,
        html_body: str,
        plain_text_body: str | None = None,
        variables: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new email template.

        Creates a reusable email template with Jinja2 variable substitution support.

        Args:
            name: Unique template name within plugin scope
            subject: Subject line template (supports Jinja2 syntax)
            html_body: HTML body template (supports Jinja2 syntax)
            plain_text_body: Plain text body template (optional)
            variables: List of variable names used in template (for documentation)

        Returns:
            Template details including:
            - id: Template UUID
            - plugin_id: Plugin ID
            - name: Template name
            - subject: Subject template
            - variables: List of variable names
            - created_at: Creation timestamp

        Raises:
            ValidationError: Invalid Jinja2 syntax in template
            HuitzoAPIError: Template name already exists or other errors
            AuthenticationError: Invalid or expired API token

        Example:
            ```python
            template = await sdk.email.create_template(
                name="weekly_report",
                subject="Weekly Report for {{ user_name }}",
                html_body=\"\"\"
                <h1>Hello {{ user_name }}!</h1>
                <p>Your report for {{ week_ending }}:</p>
                <ul>
                    <li>Tasks completed: {{ tasks_completed }}</li>
                    <li>Hours worked: {{ hours_worked }}</li>
                </ul>
                \"\"\",
                variables=["user_name", "week_ending", "tasks_completed", "hours_worked"]
            )
            print(f"Template created: {template['id']}")
            ```
        """
        # Validate request using Pydantic model
        request = CreateTemplateRequest(
            name=name,
            subject=subject,
            html_body=html_body,
            plain_text_body=plain_text_body,
            variables=variables or [],
        )

        # Make API request
        async with self._sdk._session.post(
            f"{self._sdk.base_url}/api/v1/tools/email/templates",
            json=request.model_dump(exclude_none=True),
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response, expected_status=201)

    async def list_templates(self) -> dict[str, Any]:
        """
        List available email templates.

        Retrieves all email templates for the authenticated plugin.

        Returns:
            Dictionary containing:
            - templates: List of template objects with:
                - id: Template UUID
                - name: Template name
                - subject: Subject template
                - variables: List of variable names
                - created_at: Creation timestamp

        Raises:
            AuthenticationError: Invalid or expired API token
            HuitzoAPIError: Other API errors

        Example:
            ```python
            result = await sdk.email.list_templates()
            for template in result["templates"]:
                print(f"{template['name']}: {template['variables']}")
            ```
        """
        # Make API request
        async with self._sdk._session.get(
            f"{self._sdk.base_url}/api/v1/tools/email/templates",
            headers=self._sdk._get_headers(),
        ) as response:
            return await self._sdk._handle_response(response)
