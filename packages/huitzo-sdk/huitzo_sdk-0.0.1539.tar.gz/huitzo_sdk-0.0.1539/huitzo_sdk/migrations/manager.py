"""Base class for plugin migrations."""

import inspect
import time
from functools import wraps
from typing import Any, Callable

from motor.motor_asyncio import AsyncIOMotorDatabase

from .exceptions import (
    MigrationError,
    MigrationExecutionError,
    MigrationNotFoundError,
    MigrationVersionError,
)
from .tracker import MigrationTracker


def migration(version: int, direction: str = "up", description: str = "") -> Callable:
    """
    Decorator to mark a method as a migration.

    Args:
        version: Migration version number (must be positive integer)
        direction: "up" for upgrade, "down" for downgrade
        description: Human-readable description of the migration

    Returns:
        Decorated function with migration metadata

    Example:
        ```python
        @migration(version=1, description="Add user preferences")
        async def add_preferences(self, db):
            # Migration code
            pass

        @migration(version=1, direction="down")
        async def remove_preferences(self, db):
            # Rollback code
            pass
        ```
    """
    if version <= 0:
        raise MigrationVersionError(f"Migration version must be positive, got {version}")

    if direction not in ("up", "down"):
        raise MigrationError(f"Direction must be 'up' or 'down', got {direction}")

    def decorator(func: Callable) -> Callable:
        # Attach metadata to function
        func._migration_version = version  # type: ignore
        func._migration_direction = direction  # type: ignore
        func._migration_description = description or func.__doc__ or ""  # type: ignore

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        # Copy metadata to wrapper
        wrapper._migration_version = version  # type: ignore
        wrapper._migration_direction = direction  # type: ignore
        wrapper._migration_description = description or func.__doc__ or ""  # type: ignore

        return wrapper

    return decorator


class PluginMigrationManager:
    """
    Base class for plugin migration management.

    Plugins should subclass this and define migration methods using the
    @migration decorator. The manager handles version tracking, execution
    order, and rollback.

    Attributes:
        plugin_id: Unique plugin identifier (must be set by subclass)

    Example:
        ```python
        class MyPluginMigrations(PluginMigrationManager):
            plugin_id = "my_plugin"

            @migration(version=1, description="Initial schema")
            async def create_initial_collections(self, db):
                collection = db["plugin_data"]
                await collection.create_index([("tenant_id", 1), ("key", 1)])

            @migration(version=1, direction="down")
            async def drop_initial_collections(self, db):
                await db["plugin_data"].drop()

            @migration(version=2, description="Add metadata field")
            async def add_metadata(self, db):
                await db["plugin_data"].update_many(
                    {"plugin_id": self.plugin_id},
                    {"$set": {"metadata": {}}}
                )
        ```
    """

    plugin_id: str = ""  # Must be set by subclass

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize migration manager.

        Args:
            db: MongoDB database instance

        Raises:
            MigrationError: If plugin_id is not set
        """
        if not self.plugin_id:
            raise MigrationError(f"{self.__class__.__name__} must define plugin_id attribute")

        self._db = db
        self._tracker = MigrationTracker(db)
        self._migrations: dict[int, dict[str, Any]] = {}
        self._discover_migrations()

    def _discover_migrations(self) -> None:
        """Discover all migration methods defined in the class."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, "_migration_version"):
                version = method._migration_version
                direction = method._migration_direction
                description = method._migration_description

                if version not in self._migrations:
                    self._migrations[version] = {}

                self._migrations[version][direction] = {
                    "method": method,
                    "description": description,
                }

    async def get_current_version(self) -> int:
        """
        Get current migration version for this plugin.

        Returns:
            Current version number (0 if no migrations applied)
        """
        return await self._tracker.get_current_version(self.plugin_id)

    async def get_target_version(self) -> int:
        """
        Get the latest available migration version.

        Returns:
            Highest migration version defined in the class
        """
        return max(self._migrations.keys()) if self._migrations else 0

    async def upgrade(self, target_version: int | None = None) -> None:
        """
        Run upgrade migrations to target version.

        Args:
            target_version: Version to upgrade to (None = latest)

        Raises:
            MigrationNotFoundError: If target version doesn't exist
            MigrationExecutionError: If migration fails
        """
        await self._tracker.ensure_indexes()

        current = await self.get_current_version()
        target = target_version if target_version is not None else await self.get_target_version()

        if target < current:
            raise MigrationVersionError(
                f"Target version {target} is lower than current {current}. Use downgrade()."
            )

        if target == current:
            return  # Already at target version

        # Get versions to apply
        versions_to_apply = sorted([v for v in self._migrations.keys() if current < v <= target])

        for version in versions_to_apply:
            if "up" not in self._migrations[version]:
                raise MigrationNotFoundError(f"No upgrade migration found for version {version}")

            migration_info = self._migrations[version]["up"]
            await self._execute_migration(version, migration_info, direction="up")

    async def downgrade(self, target_version: int) -> None:
        """
        Run downgrade migrations to target version.

        Args:
            target_version: Version to downgrade to

        Raises:
            MigrationNotFoundError: If migration doesn't exist
            MigrationExecutionError: If migration fails
        """
        await self._tracker.ensure_indexes()

        current = await self.get_current_version()

        if target >= current:
            raise MigrationVersionError(
                f"Target version {target} is higher than or equal to current {current}. Use upgrade()."
            )

        # Get versions to rollback (in reverse order)
        versions_to_rollback = sorted(
            [v for v in self._migrations.keys() if target < v <= current], reverse=True
        )

        for version in versions_to_rollback:
            if "down" not in self._migrations[version]:
                raise MigrationNotFoundError(f"No downgrade migration found for version {version}")

            migration_info = self._migrations[version]["down"]
            await self._execute_migration(version, migration_info, direction="down")

            # Remove version from tracker after successful rollback
            await self._tracker.remove_version(self.plugin_id, version)

    async def _execute_migration(
        self, version: int, migration_info: dict[str, Any], direction: str
    ) -> None:
        """
        Execute a single migration.

        Args:
            version: Migration version
            migration_info: Migration metadata and method
            direction: "up" or "down"

        Raises:
            MigrationExecutionError: If migration fails
        """
        method = migration_info["method"]
        description = migration_info["description"]

        start_time = time.time()
        success = False
        error_msg = None

        try:
            # Execute the migration
            await method(self._db)
            success = True

        except Exception as e:
            error_msg = str(e)
            raise MigrationExecutionError(f"Migration {version} ({direction}) failed: {e}") from e

        finally:
            execution_time_ms = (time.time() - start_time) * 1000

            # Record migration only for upgrades (downgrades remove the record)
            if direction == "up":
                await self._tracker.record_migration(
                    plugin_id=self.plugin_id,
                    version=version,
                    description=description,
                    execution_time_ms=execution_time_ms,
                    success=success,
                    error=error_msg,
                )

    async def get_migration_history(self) -> list[dict[str, Any]]:
        """
        Get migration history for this plugin.

        Returns:
            List of migration records
        """
        return await self._tracker.get_migration_history(self.plugin_id)

    async def get_pending_migrations(self) -> list[int]:
        """
        Get list of pending migration versions.

        Returns:
            List of version numbers that haven't been applied
        """
        current = await self.get_current_version()
        target = await self.get_target_version()

        return sorted([v for v in self._migrations.keys() if current < v <= target])

    def get_migration_info(self, version: int) -> dict[str, Any] | None:
        """
        Get information about a specific migration version.

        Args:
            version: Migration version

        Returns:
            Migration info dict or None if not found
        """
        return self._migrations.get(version)

    async def validate_migrations(self) -> dict[str, Any]:
        """
        Validate migration definitions for completeness.

        Returns:
            Validation report with warnings and errors

        Example result:
            {
                "valid": True,
                "warnings": ["Version 2 has no downgrade migration"],
                "errors": [],
                "versions": [1, 2, 3],
            }
        """
        warnings = []
        errors = []

        # Check for gaps in version numbers
        versions = sorted(self._migrations.keys())
        for i in range(len(versions) - 1):
            if versions[i + 1] != versions[i] + 1:
                warnings.append(f"Version gap detected: {versions[i]} -> {versions[i + 1]}")

        # Check for missing downgrade migrations
        for version, migrations in self._migrations.items():
            if "up" in migrations and "down" not in migrations:
                warnings.append(f"Version {version} has no downgrade migration")

            if "down" in migrations and "up" not in migrations:
                errors.append(f"Version {version} has downgrade but no upgrade")

        return {
            "valid": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "versions": versions,
        }
