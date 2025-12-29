"""Command protocol definition for Huitzo WebCLI platform.

This module defines the core protocol that all command plugins must implement.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from redis.asyncio import Redis


@dataclass
class CommandContext:
    """
    Context information for command execution.

    Provides the command with session context, user information,
    environment variables, and other execution metadata.

    Attributes:
        session_id: Unique identifier for the terminal session
        user_id: Unique identifier for the user executing the command
        tenant_id: Unique identifier for the organization/tenant (for multi-tenant isolation)
        user_role: User's role (e.g., "admin", "user", "guest")
        cwd: Current working directory
        env: Environment variables
        terminal_size: Terminal dimensions (cols, rows)
        output_format: Desired output format ("text" or "json")
        correlation_id: Optional correlation ID for request tracing
        internal_auth_token: Optional API token for internal plugin-to-backend authentication
        mongo_db: Optional MongoDB database instance (injected by backend)
        redis_client: Optional Redis client instance (injected by backend)

    Security Note:
        - user_role is INTERNAL ONLY (backend use only)
        - Never expose this context to frontend
        - Frontend gets capabilities, not roles
        - internal_auth_token is for plugin API authentication (internal use only)

    Storage Injection:
        - mongo_db and redis_client are injected by the CommandExecutor
        - Plugins can use these directly or via PluginDataStore/VolatileDataStore
        - If None, plugins should handle gracefully or raise appropriate errors
    """

    session_id: UUID
    user_id: UUID
    tenant_id: UUID
    user_role: str  # String to avoid circular dependency with UserRole enum
    cwd: str
    env: dict[str, str]
    terminal_size: dict[str, int]
    output_format: str = "text"  # "text" or "json"
    correlation_id: str | None = None
    internal_auth_token: str | None = None  # For plugin API authentication
    mongo_db: "AsyncIOMotorDatabase | None" = None  # Injected by backend
    redis_client: "Redis | None" = None  # Injected by backend


@dataclass
class CommandResult:
    """
    Result of command execution.

    Encapsulates the output, exit code, and optional metadata
    from a command execution.

    Attributes:
        exit_code: Exit code (0 for success, non-zero for failure)
        stdout: Standard output text
        stderr: Standard error text (default: "")
        data: Optional structured data for JSON output
        duration_ms: Optional execution duration in milliseconds
        timestamp: Optional execution timestamp
    """

    exit_code: int
    stdout: str
    stderr: str = ""
    data: dict[str, Any] | None = None
    duration_ms: int | None = None
    timestamp: datetime | None = None


class CommandProtocol(Protocol):
    """
    Protocol that all command plugins must implement.

    This protocol defines the interface for creating executable commands
    that can be discovered and loaded by the Huitzo WebCLI platform.

    Example:
        ```python
        from huitzo_sdk.protocols.command import (
            CommandProtocol,
            CommandContext,
            CommandResult,
        )

        class HelloCommand:
            @property
            def name(self) -> str:
                return "hello"

            @property
            def namespace(self) -> str:
                return "demo"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Say hello to someone"

            @property
            def schema(self) -> dict[str, Any]:
                return {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name to greet"}
                    },
                    "required": ["name"],
                }

            @property
            def permissions(self) -> list[str]:
                return []  # No special permissions required

            async def execute(
                self, args: dict[str, Any], context: CommandContext
            ) -> CommandResult:
                name = args.get("name", "World")
                return CommandResult(
                    exit_code=0,
                    stdout=f"Hello, {name}!\\n"
                )

            def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
                # Basic validation
                if "name" in args and not isinstance(args["name"], str):
                    raise ValueError("name must be a string")
                return args

            def get_help(self) -> str:
                return "Usage: hello --name <name>\\n\\nSay hello to someone."
        ```

    Registration:
        Commands are registered via Python entry points in pyproject.toml:

        ```toml
        [project.entry-points."webcli.commands"]
        "demo.hello" = "my_plugin.commands.hello:HelloCommand"
        ```
    """

    @property
    def name(self) -> str:
        """
        Command name (unique within namespace).

        Returns:
            Command name (e.g., "hello", "version", "deploy")
        """
        ...

    @property
    def namespace(self) -> str:
        """
        Command namespace (e.g., 'builtin', 'git', 'docker').

        Namespaces organize commands and prevent naming conflicts.
        Common namespaces:
        - "builtin": Core platform commands
        - "admin": Administrative commands
        - Plugin-specific namespaces (e.g., "finance", "devops")

        Returns:
            Namespace string
        """
        ...

    @property
    def version(self) -> str:
        """
        Command version (semantic versioning).

        Returns:
            Version string (e.g., "1.0.0", "2.1.3")
        """
        ...

    @property
    def description(self) -> str:
        """
        Human-readable description of the command.

        Returns:
            One-line description shown in help listings
        """
        ...

    @property
    def schema(self) -> dict[str, Any]:
        """
        JSON Schema for command arguments.

        Defines the structure, types, and validation rules for
        command arguments. Used for auto-completion and validation.

        Returns:
            JSON Schema dictionary (must be valid JSON Schema Draft 7)
        """
        ...

    @property
    def permissions(self) -> list[str]:
        """
        Required permissions/roles to execute this command.

        Returns:
            List of required permission strings (empty list = no requirements)
        """
        ...

    async def execute(self, args: dict[str, Any], context: CommandContext) -> CommandResult:
        """
        Execute the command with given arguments and context.

        This is the main entry point for command execution. The platform
        calls this method with validated arguments and execution context.

        Args:
            args: Command arguments validated against schema
            context: Execution context (session, user, environment)

        Returns:
            CommandResult with exit code, output, and optional data

        Raises:
            Exception: Any exception will be caught and converted to
                      CommandResult with non-zero exit code
        """
        ...

    def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and normalize command arguments.

        Called before execute() to validate arguments beyond JSON Schema.
        Use this for complex validation logic, type coercion, or
        setting default values.

        Args:
            args: Raw arguments dictionary

        Returns:
            Validated and normalized arguments

        Raises:
            ValueError: If arguments are invalid
        """
        ...

    def get_help(self) -> str:
        """
        Get detailed help text for the command.

        Returns:
            Formatted help text with usage examples and option descriptions
        """
        ...
