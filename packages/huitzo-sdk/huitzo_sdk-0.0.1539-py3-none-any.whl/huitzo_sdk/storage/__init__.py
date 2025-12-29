"""
Plugin storage layer with namespace isolation.

Provides MongoDB document storage (PluginDataStore) and Redis volatile storage
(VolatileDataStore) with automatic tenant/user/plugin scoping.

Example:
    ```python
    from uuid import UUID
    from motor.motor_asyncio import AsyncIOMotorClient
    import redis.asyncio as redis
    from huitzo_sdk.storage import Namespace, PluginDataStore, VolatileDataStore

    # Create namespace for isolation
    namespace = Namespace(
        tenant_id=UUID("..."),
        user_id=UUID("..."),
        plugin_id="my_plugin"
    )

    # MongoDB document storage
    mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
    doc_store = PluginDataStore(namespace, mongo_client.get_database("webcli"))

    # Save persistent data
    doc_id = await doc_store.save("config", {"theme": "dark"})

    # Redis volatile storage
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    cache = VolatileDataStore(namespace, redis_client)

    # Cache temporary data
    await cache.set("session_state", {"connected": True}, ttl=3600)
    ```
"""

from .document_store import PluginDataStore
from .exceptions import (
    ConnectionError,
    DocumentNotFoundError,
    InvalidDocumentError,
    NamespaceError,
    PermissionDeniedError,
    QuotaExceededError,
    StorageError,
)
from .namespace import Namespace, build_namespace_filter, build_redis_key
from .redis_store import VolatileDataStore

__all__ = [
    # Storage Classes
    "PluginDataStore",
    "VolatileDataStore",
    # Namespace
    "Namespace",
    "build_namespace_filter",
    "build_redis_key",
    # Exceptions
    "StorageError",
    "DocumentNotFoundError",
    "PermissionDeniedError",
    "InvalidDocumentError",
    "NamespaceError",
    "QuotaExceededError",
    "ConnectionError",
]
