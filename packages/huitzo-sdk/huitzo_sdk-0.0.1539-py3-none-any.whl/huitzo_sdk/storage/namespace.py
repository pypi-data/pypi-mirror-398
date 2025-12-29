"""
Namespace isolation utilities for multi-tenant plugin storage.

Provides automatic scoping of storage operations by tenant_id, user_id, and plugin_id
to ensure complete data isolation between tenants, users, and plugins.
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class Namespace:
    """
    Immutable namespace identifier for scoping plugin storage operations.

    All storage operations are automatically isolated by this three-part key:
    - tenant_id: Organization/workspace isolation
    - user_id: User-specific data isolation
    - plugin_id: Plugin-specific data isolation

    Example:
        ```python
        namespace = Namespace(
            tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
            user_id=UUID("00000000-0000-0000-0000-000000000002"),
            plugin_id="weather_plugin"
        )
        ```
    """

    tenant_id: UUID
    user_id: UUID
    plugin_id: str

    def __post_init__(self) -> None:
        """Validate namespace components."""
        if not isinstance(self.tenant_id, UUID):
            raise TypeError(f"tenant_id must be UUID, got {type(self.tenant_id)}")
        if not isinstance(self.user_id, UUID):
            raise TypeError(f"user_id must be UUID, got {type(self.user_id)}")
        if not isinstance(self.plugin_id, str) or not self.plugin_id:
            raise ValueError("plugin_id must be non-empty string")

    def to_dict(self) -> dict[str, Any]:
        """
        Convert namespace to dictionary for MongoDB queries.

        Returns:
            dict with tenant_id, user_id (as strings), and plugin_id
        """
        return {
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id),
            "plugin_id": self.plugin_id,
        }

    def to_redis_prefix(self) -> str:
        """
        Generate Redis key prefix for namespace isolation.

        Returns:
            String in format: {tenant_id}:{user_id}:{plugin_id}:

        Example:
            >>> namespace.to_redis_prefix()
            'abc-123:def-456:weather_plugin:'
        """
        return f"{self.tenant_id}:{self.user_id}:{self.plugin_id}:"

    def __str__(self) -> str:
        """String representation showing namespace components."""
        return f"Namespace(tenant={self.tenant_id}, user={self.user_id}, plugin={self.plugin_id})"


def build_namespace_filter(namespace: Namespace, **additional_filters: Any) -> dict[str, Any]:
    """
    Build MongoDB query filter with namespace isolation.

    Combines namespace components with additional filters for safe querying.

    Args:
        namespace: Namespace to filter by
        **additional_filters: Additional MongoDB query filters

    Returns:
        Combined filter dictionary

    Example:
        ```python
        filter_dict = build_namespace_filter(
            namespace,
            data_type="conversation",
            created_at={"$gte": datetime.now()}
        )
        # Returns: {
        #     "tenant_id": "...",
        #     "user_id": "...",
        #     "plugin_id": "...",
        #     "data_type": "conversation",
        #     "created_at": {"$gte": ...}
        # }
        ```
    """
    return {**namespace.to_dict(), **additional_filters}


def build_redis_key(namespace: Namespace, key: str) -> str:
    """
    Build namespaced Redis key.

    Args:
        namespace: Namespace for isolation
        key: Logical key name

    Returns:
        Full Redis key with namespace prefix

    Example:
        ```python
        redis_key = build_redis_key(namespace, "session_state")
        # Returns: 'abc-123:def-456:weather_plugin:session_state'
        ```
    """
    if not key:
        raise ValueError("key cannot be empty")
    return f"{namespace.to_redis_prefix()}{key}"
