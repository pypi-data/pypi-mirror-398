"""
Pydantic models for Huitzo SDK request validation.

This module defines request models with comprehensive validation:
- CreateJobRequest: Validate job creation parameters
- UpdateJobRequest: Validate job update parameters
- SendEmailRequest: Validate email sending parameters
- CreateTemplateRequest: Validate template creation parameters

All models use Pydantic v2 with strict validation and extra="forbid" to catch typos.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateJobRequest(BaseModel):
    """
    Request model for creating a scheduled CRON job.

    Attributes:
        name: Unique job name within user+plugin scope
        command: Full command path (e.g., "finance.report.generate")
        schedule: CRON expression (5 fields: minute hour day month weekday)
        timezone: IANA timezone (e.g., "America/New_York", "UTC")
        arguments: Command arguments as dictionary
        enabled: Whether job should be active immediately
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Job name (unique per user+plugin)",
    )
    command: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Command to execute (e.g., 'finance.report.generate')",
    )
    schedule: str = Field(
        ...,
        description="CRON expression (5 fields: minute hour day month weekday)",
    )
    timezone: str = Field(
        default="UTC",
        description="IANA timezone (e.g., 'America/New_York')",
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Command arguments as JSON",
    )
    enabled: bool = Field(
        default=True,
        description="Whether job is active",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "weekly_report",
                "command": "finance.report.generate",
                "schedule": "0 10 * * 1",
                "timezone": "America/New_York",
                "arguments": {"format": "pdf", "include_charts": True},
                "enabled": True,
            }
        },
    )


class UpdateJobRequest(BaseModel):
    """
    Request model for updating a scheduled job.

    All fields are optional - only provided fields will be updated.

    Attributes:
        schedule: New CRON expression
        timezone: New IANA timezone
        arguments: New command arguments
        enabled: New enabled status
    """

    schedule: str | None = Field(
        default=None,
        description="CRON expression",
    )
    timezone: str | None = Field(
        default=None,
        description="IANA timezone",
    )
    arguments: dict[str, Any] | None = Field(
        default=None,
        description="Command arguments",
    )
    enabled: bool | None = Field(
        default=None,
        description="Whether job is active",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "schedule": "30 14 * * 5",
                "enabled": False,
            }
        },
    )


class SendEmailRequest(BaseModel):
    """
    Request model for sending an email.

    Must provide either:
    - html_body and/or plain_text_body, OR
    - template_id with template_variables

    Attributes:
        recipient_user_id: UUID of the recipient user
        subject: Email subject line
        html_body: HTML email content
        plain_text_body: Plain text email content (fallback)
        template_id: UUID of email template to use
        template_variables: Variables for template rendering
    """

    recipient_user_id: UUID = Field(
        ...,
        description="User ID of recipient",
    )
    subject: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Email subject",
    )
    html_body: str | None = Field(
        default=None,
        max_length=50000,
        description="HTML email body",
    )
    plain_text_body: str | None = Field(
        default=None,
        max_length=50000,
        description="Plain text email body",
    )
    template_id: UUID | None = Field(
        default=None,
        description="Template ID (optional)",
    )
    template_variables: dict[str, str] | None = Field(
        default=None,
        description="Template variables",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "recipient_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "subject": "Welcome to Huitzo",
                "html_body": "<h1>Welcome!</h1><p>Thank you for joining.</p>",
                "plain_text_body": "Welcome! Thank you for joining.",
            }
        },
    )


class CreateTemplateRequest(BaseModel):
    """
    Request model for creating an email template.

    Templates use Jinja2 syntax for variable substitution.

    Attributes:
        name: Unique template name within plugin scope
        subject: Subject line template (supports Jinja2)
        html_body: HTML body template (supports Jinja2)
        plain_text_body: Plain text body template (optional)
        variables: List of variable names used in template
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Template name",
    )
    subject: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Subject template (Jinja2)",
    )
    html_body: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="HTML body template (Jinja2)",
    )
    plain_text_body: str | None = Field(
        default=None,
        max_length=50000,
        description="Plain text body template",
    )
    variables: list[str] = Field(
        default_factory=list,
        description="Template variable names",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "welcome_email",
                "subject": "Welcome to {{ product_name }}",
                "html_body": "<h1>Hello {{ user_name }}!</h1><p>Welcome to {{ product_name }}.</p>",
                "variables": ["user_name", "product_name"],
            }
        },
    )


class CompleteRequest(BaseModel):
    """
    Request model for LLM completion.

    Attributes:
        user_id: User ID making the request
        plugin_id: Plugin identifier
        prompt: Input prompt text
        model: Model name (e.g., gpt-4o-mini, claude-sonnet-4.5)
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate
        stream: Enable streaming response
        use_cache: Use cached responses if available
    """

    user_id: UUID = Field(
        ...,
        description="User ID",
    )
    plugin_id: str = Field(
        default="llm",
        description="Plugin identifier",
    )
    prompt: str = Field(
        ...,
        min_length=1,
        description="Input prompt text",
    )
    model: str = Field(
        default="gpt-4o-mini",
        description="Model name",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    max_tokens: int = Field(
        default=1000,
        gt=0,
        description="Maximum tokens to generate",
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming response",
    )
    use_cache: bool = Field(
        default=True,
        description="Use cached responses",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "plugin_id": "llm",
                "prompt": "Explain quantum computing in 2 sentences",
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": False,
                "use_cache": True,
            }
        },
    )


class CompleteTemplateRequest(BaseModel):
    """
    Request model for template-based completion.

    Attributes:
        user_id: User ID making the request
        plugin_id: Plugin identifier
        template_name: Template name
        variables: Template variables
        model: Override model (uses template default if None)
        temperature: Override temperature
        max_tokens: Override max tokens
        stream: Enable streaming response
        use_cache: Use cached responses if available
    """

    user_id: UUID = Field(
        ...,
        description="User ID",
    )
    plugin_id: str = Field(
        default="llm",
        description="Plugin identifier",
    )
    template_name: str = Field(
        ...,
        min_length=1,
        description="Template name",
    )
    variables: dict[str, str] = Field(
        ...,
        description="Template variables",
    )
    model: str | None = Field(
        default=None,
        description="Override model",
    )
    temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Override temperature",
    )
    max_tokens: int | None = Field(
        default=None,
        gt=0,
        description="Override max tokens",
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming response",
    )
    use_cache: bool = Field(
        default=True,
        description="Use cached responses",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "plugin_id": "llm",
                "template_name": "summarize",
                "variables": {"text": "Long article text...", "max_sentences": "3"},
            }
        },
    )


class CreateLLMTemplateRequest(BaseModel):
    """
    Request model for creating an LLM prompt template.

    Templates use Jinja2 syntax for variable substitution.

    Attributes:
        plugin_id: Plugin identifier
        name: Unique template name within plugin scope
        template: Jinja2 template string
        variables: List of required variable names
        provider_preference: Preferred provider (openai, claude, auto)
        model_preference: Preferred model
        temperature: Default temperature
        max_tokens: Default max tokens
    """

    plugin_id: str = Field(
        ...,
        min_length=1,
        description="Plugin identifier",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Template name",
    )
    template: str = Field(
        ...,
        min_length=1,
        description="Jinja2 template string",
    )
    variables: list[str] = Field(
        default_factory=list,
        description="Required variable names",
    )
    provider_preference: str = Field(
        default="auto",
        description="Preferred provider",
    )
    model_preference: str | None = Field(
        default=None,
        description="Preferred model",
    )
    temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Default temperature",
    )
    max_tokens: int | None = Field(
        default=None,
        gt=0,
        description="Default max tokens",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "plugin_id": "llm",
                "name": "code_review",
                "template": "Review this {{language}} code:\\n\\n{{code}}",
                "variables": ["language", "code"],
                "provider_preference": "auto",
                "model_preference": "gpt-4o",
                "temperature": 0.3,
            }
        },
    )
