"""
Plugin migration framework for managing data schema evolution.

Provides:
- PluginMigrationManager: Base class for plugin migrations
- MigrationTracker: MongoDB-based version tracking
- Migration decorators for declaring upgrade/downgrade functions

Example:
    ```python
    # In plugin: huitzo_plugin_duck/migrations.py
    from huitzo_sdk.migrations import PluginMigrationManager, migration

    class DuckMigrations(PluginMigrationManager):
        plugin_id = "duck"

        @migration(version=1, description="Add quack_count field")
        async def add_quack_count(self, db):
            '''Add quack_count to all duck documents'''
            collection = db["plugin_data"]
            await collection.update_many(
                {"plugin_id": "duck", "data_type": "duck"},
                {"$set": {"data.quack_count": 0}}
            )

        @migration(version=1, direction="down")
        async def remove_quack_count(self, db):
            '''Remove quack_count field'''
            collection = db["plugin_data"]
            await collection.update_many(
                {"plugin_id": "duck", "data_type": "duck"},
                {"$unset": {"data.quack_count": ""}}
            )

    # Entry point registration in pyproject.toml:
    # [project.entry-points."webcli.plugin_migrations"]
    # duck = "huitzo_plugin_duck.migrations:DuckMigrations"
    ```
"""

from .manager import PluginMigrationManager, migration
from .tracker import MigrationTracker
from .exceptions import (
    MigrationError,
    MigrationNotFoundError,
    MigrationVersionError,
)

__all__ = [
    "PluginMigrationManager",
    "migration",
    "MigrationTracker",
    "MigrationError",
    "MigrationNotFoundError",
    "MigrationVersionError",
]
