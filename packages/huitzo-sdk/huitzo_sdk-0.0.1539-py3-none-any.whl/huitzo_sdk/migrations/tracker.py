"""MongoDB-based migration version tracking."""

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


class MigrationTracker:
    """
    Tracks plugin migration state in MongoDB.

    Stores migration history in a dedicated collection with per-plugin versioning.
    Ensures idempotent migration runs and provides rollback capability.

    Schema:
        {
            "_id": ObjectId,
            "plugin_id": str,           # Plugin identifier
            "version": int,             # Migration version number
            "description": str,         # Migration description
            "applied_at": datetime,     # When migration was applied
            "execution_time_ms": float, # Migration duration
            "success": bool,            # Whether migration succeeded
            "error": str | None,        # Error message if failed
        }
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize migration tracker.

        Args:
            db: MongoDB database instance
        """
        self._db = db
        self._collection = db["plugin_migrations"]

    async def ensure_indexes(self) -> None:
        """Create indexes for migration tracking."""
        # Unique index on plugin_id + version
        await self._collection.create_index([("plugin_id", 1), ("version", 1)], unique=True)

        # Index for querying by plugin_id
        await self._collection.create_index([("plugin_id", 1), ("applied_at", -1)])

    async def get_current_version(self, plugin_id: str) -> int:
        """
        Get current migration version for a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Current version number (0 if no migrations applied)
        """
        result = await self._collection.find_one(
            {"plugin_id": plugin_id, "success": True},
            sort=[("version", -1)],
        )

        return result["version"] if result else 0

    async def record_migration(
        self,
        plugin_id: str,
        version: int,
        description: str,
        execution_time_ms: float,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """
        Record a migration execution.

        Args:
            plugin_id: Plugin identifier
            version: Migration version
            description: Migration description
            execution_time_ms: Execution time in milliseconds
            success: Whether migration succeeded
            error: Optional error message if failed
        """
        await self._collection.insert_one(
            {
                "plugin_id": plugin_id,
                "version": version,
                "description": description,
                "applied_at": datetime.now(timezone.utc),
                "execution_time_ms": execution_time_ms,
                "success": success,
                "error": error,
            }
        )

    async def get_migration_history(self, plugin_id: str) -> list[dict[str, Any]]:
        """
        Get migration history for a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            List of migration records, ordered by version
        """
        cursor = self._collection.find({"plugin_id": plugin_id}, sort=[("version", 1)])

        return await cursor.to_list(length=None)

    async def is_version_applied(self, plugin_id: str, version: int) -> bool:
        """
        Check if a migration version has been applied successfully.

        Args:
            plugin_id: Plugin identifier
            version: Migration version

        Returns:
            True if migration was applied successfully
        """
        result = await self._collection.find_one(
            {"plugin_id": plugin_id, "version": version, "success": True}
        )

        return result is not None

    async def remove_version(self, plugin_id: str, version: int) -> bool:
        """
        Remove a migration version record (used during rollback).

        Args:
            plugin_id: Plugin identifier
            version: Migration version

        Returns:
            True if record was removed
        """
        result = await self._collection.delete_one({"plugin_id": plugin_id, "version": version})

        return result.deleted_count > 0

    async def get_failed_migrations(self, plugin_id: str) -> list[dict[str, Any]]:
        """
        Get all failed migration attempts for a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            List of failed migration records
        """
        cursor = self._collection.find(
            {"plugin_id": plugin_id, "success": False}, sort=[("applied_at", -1)]
        )

        return await cursor.to_list(length=None)

    async def clear_history(self, plugin_id: str) -> int:
        """
        Clear all migration history for a plugin (use with caution).

        Args:
            plugin_id: Plugin identifier

        Returns:
            Number of records deleted
        """
        result = await self._collection.delete_many({"plugin_id": plugin_id})

        return result.deleted_count
