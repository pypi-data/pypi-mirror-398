"""
Huitzo SDK - Developer SDK for Huitzo WebCLI Platform Tools.

This package provides a Python SDK for:

1. **HTTP Clients** (External API Access):
   - CRON Scheduling Service: Schedule and manage recurring command executions
   - Discord Webhook Service: Send messages to Discord channels
   - Email Service: Send emails and manage templates
   - Files Service: Upload files for use in command workflows
   - Formatters Service: Convert between Markdown, HTML, and plain text
   - LLM Completions Service: Generate text completions using various LLM providers
   - PDF Generator Service: Generate PDFs from HTML or Markdown
   - QR Code Service: Generate QR codes and WiFi QR codes
   - Slack Webhook Service: Send messages to Slack channels
   - Static Site Hosting Service: Deploy temporary static sites from .zip archives
   - Telegram Service: Send Telegram messages
   - URL Shortener Service: Shorten URLs via TinyURL or is.gd
   - Validators Service: Validate email addresses and URLs

2. **Plugin Development** (Command Implementation):
   - Command Protocol: Interface for creating executable commands
   - Database Access: ORM and session management
   - Shared Enums: UserRole, ConfigScope, ExecutionStatus
   - Model Base: SQLAlchemy declarative base for plugin models

HTTP Client Usage:
    ```python
    from huitzo_sdk import HuitzoTools

    async with HuitzoTools(api_token="your_token") as sdk:
        # Schedule a CRON job
        job = await sdk.cron.schedule(
            name="daily_report",
            command="finance.report.generate",
            schedule="0 9 * * *",
            timezone="UTC"
        )

        # Send an email
        await sdk.email.send(
            recipient_user_id="user-uuid",
            subject="Report Ready",
            html_body="<p>Your report is ready!</p>"
        )
    ```

Plugin Development Usage:
    ```python
    from huitzo_sdk import CommandProtocol, CommandContext, CommandResult
    from huitzo_sdk.database import get_async_session_context
    from huitzo_sdk.orm import Base

    class MyCommand:
        @property
        def name(self) -> str:
            return "mycommand"

        async def execute(
            self, args: dict, context: CommandContext
        ) -> CommandResult:
            async with get_async_session_context() as db:
                # Database operations...
                pass
            return CommandResult(exit_code=0, stdout="Success!\\n")
    ```

Main Classes:
    HTTP Clients:
    - HuitzoTools: Main SDK client with async context manager support
    - CronClient: CRON Scheduling Service client
    - DiscordClient: Discord Webhook Service client
    - EmailClient: Email Service client
    - FilesClient: File Upload Service client
    - FormattersClient: Text Formatting Service client
    - LLMClient: LLM Completions Service client
    - PdfGeneratorClient: PDF Generation Service client
    - QrCodeClient: QR Code Generation Service client
    - SitesClient: Static Site Hosting Service client
    - SlackClient: Slack Webhook Service client
    - TelegramClient: Telegram Messaging Service client
    - UrlShortenerClient: URL Shortening Service client
    - ValidatorsClient: Email/URL Validation Service client

    Plugin Development:
    - CommandProtocol: Protocol for command implementations
    - CommandContext: Execution context passed to commands
    - CommandResult: Result returned by command execution
    - Base: SQLAlchemy declarative base for plugin models

Exceptions:
    - HuitzoAPIError: Base exception for all API errors
    - AuthenticationError: 401/403 authentication failures
    - NotFoundError: 404 resource not found
    - RateLimitError: 429 rate limit exceeded
    - ValidationError: 400 validation errors
    - QuotaExceededError: 403 quota limits exceeded
"""

__version__ = "2.0.0"

# HTTP Clients (for external API consumers)
from .client import HuitzoTools
from .cron import CronClient
from .discord import DiscordClient
from .email import EmailClient
from .files import FilesClient, FileUploadResult
from .formatters import FormattersClient
from .llm import LLMClient
from .pdf_generator import PdfGeneratorClient
from .qrcode import QrCodeClient
from .sites import SitesClient
from .slack import SlackClient
from .telegram import TelegramClient
from .url_shortener import UrlShortenerClient
from .validators import ValidatorsClient

# Plugin Development Interfaces
from .protocols.command import CommandContext, CommandProtocol, CommandResult
from .enums import ConfigScope, ExecutionStatus, UserRole
from .orm import Base
from .database import get_async_session_context, register_session_factory

# Storage Layer (MongoDB + Redis)
from .storage import (
    Namespace,
    PluginDataStore,
    VolatileDataStore,
    StorageError,
    DocumentNotFoundError,
    PermissionDeniedError,
    InvalidDocumentError,
)

# Migration Framework
from .migrations import (
    PluginMigrationManager,
    migration,
    MigrationTracker,
    MigrationError,
    MigrationNotFoundError,
    MigrationVersionError,
)

# Manifest Parser and Dependency Checker
from .manifest import (
    PackManifest,
    PackInfo,
    CommandDef,
    DataTypeDef,
    ServiceRequirement,
    DashboardConfig,
    load_manifest,
    validate_manifest,
    validate_manifest_file,
)
from .dependency_checker import (
    check_dependency_conflicts,
    validate_pack_dependencies,
    parse_requirement,
    Requirement,
)

# Exceptions
from .exceptions import (
    AuthenticationError,
    HuitzoAPIError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    ValidationError,
)

__all__ = [
    # HTTP Clients
    "HuitzoTools",
    "CronClient",
    "DiscordClient",
    "EmailClient",
    "FilesClient",
    "FileUploadResult",
    "FormattersClient",
    "LLMClient",
    "PdfGeneratorClient",
    "QrCodeClient",
    "SitesClient",
    "SlackClient",
    "TelegramClient",
    "UrlShortenerClient",
    "ValidatorsClient",
    # Plugin Development - Protocols
    "CommandProtocol",
    "CommandContext",
    "CommandResult",
    # Plugin Development - Enums
    "UserRole",
    "ConfigScope",
    "ExecutionStatus",
    # Plugin Development - ORM
    "Base",
    # Plugin Development - Database
    "get_async_session_context",
    "register_session_factory",
    # Plugin Development - Storage
    "Namespace",
    "PluginDataStore",
    "VolatileDataStore",
    "StorageError",
    "DocumentNotFoundError",
    "PermissionDeniedError",
    "InvalidDocumentError",
    # Plugin Development - Migrations
    "PluginMigrationManager",
    "migration",
    "MigrationTracker",
    "MigrationError",
    "MigrationNotFoundError",
    "MigrationVersionError",
    # Plugin Development - Manifest and Dependencies
    "PackManifest",
    "PackInfo",
    "CommandDef",
    "DataTypeDef",
    "ServiceRequirement",
    "DashboardConfig",
    "load_manifest",
    "validate_manifest",
    "validate_manifest_file",
    "check_dependency_conflicts",
    "validate_pack_dependencies",
    "parse_requirement",
    "Requirement",
    # Exceptions
    "HuitzoAPIError",
    "AuthenticationError",
    "NotFoundError",
    "QuotaExceededError",
    "RateLimitError",
    "ValidationError",
    # Version
    "__version__",
]

# huitzo_sdk

# This module will contain the SDK functionalities for the Huitzo project.
