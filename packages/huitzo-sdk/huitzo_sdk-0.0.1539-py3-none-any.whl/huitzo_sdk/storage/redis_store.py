"""
Redis-backed volatile storage for plugins with namespace isolation.

Provides fast, ephemeral storage with TTL support for caching, session state,
rate limiting, and temporary data.
"""

import json
from typing import Any

import redis.asyncio as redis

from .exceptions import InvalidDocumentError, StorageError
from .namespace import Namespace, build_redis_key


class VolatileDataStore:
    """
    Redis volatile storage with namespace isolation and TTL support.

    Automatically prefixes all keys with tenant_id:user_id:plugin_id for
    complete data isolation. Ideal for caching, sessions, and temporary state.

    Example:
        ```python
        import redis.asyncio as redis

        redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
        namespace = Namespace(tenant_id, user_id, "my_plugin")
        cache = VolatileDataStore(namespace, redis_client)

        # Cache data with 1-hour expiration
        await cache.set("session_state", {
            "connected": True,
            "last_activity": "2025-11-14T10:00:00Z"
        }, ttl=3600)

        # Retrieve cached data
        state = await cache.get("session_state")
        ```
    """

    def __init__(self, namespace: Namespace, redis_client: redis.Redis):
        """
        Initialize volatile store with namespace and Redis client.

        Args:
            namespace: Namespace for key isolation
            redis_client: Redis client instance (with decode_responses=True)
        """
        self.namespace = namespace
        self._redis = redis_client

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Store value with optional expiration.

        Args:
            key: Storage key (will be namespaced automatically)
            value: Value to store (must be JSON-serializable)
            ttl: Time-to-live in seconds (None = no expiration)

        Returns:
            True if stored successfully

        Raises:
            InvalidDocumentError: If value is not JSON-serializable
            StorageError: If Redis operation fails

        Example:
            ```python
            # Store session with 2-hour TTL
            await cache.set("session", {"user": "alice"}, ttl=7200)

            # Store permanent counter
            await cache.set("total_requests", 1000)
            ```
        """
        try:
            # Serialize value to JSON
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError) as e:
                raise InvalidDocumentError(f"Value must be JSON-serializable: {e}")

            # Build namespaced key
            redis_key = build_redis_key(self.namespace, key)

            # Store with optional TTL
            if ttl:
                await self._redis.setex(redis_key, ttl, serialized)
            else:
                await self._redis.set(redis_key, serialized)

            return True
        except redis.RedisError as e:
            raise StorageError(f"Failed to set value: {e}")

    async def get(self, key: str) -> Any | None:
        """
        Retrieve value by key.

        Args:
            key: Storage key

        Returns:
            Deserialized value or None if not found/expired

        Raises:
            StorageError: If Redis operation fails

        Example:
            ```python
            session = await cache.get("session")
            if session:
                print(f"User: {session['user']}")
            else:
                print("Session expired or not found")
            ```
        """
        try:
            redis_key = build_redis_key(self.namespace, key)
            serialized = await self._redis.get(redis_key)

            if serialized is None:
                return None

            # Deserialize from JSON
            return json.loads(serialized)
        except redis.RedisError as e:
            raise StorageError(f"Failed to get value: {e}")
        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to deserialize value: {e}")

    async def delete(self, key: str) -> bool:
        """
        Delete value by key.

        Args:
            key: Storage key

        Returns:
            True if deleted, False if key didn't exist

        Raises:
            StorageError: If Redis operation fails

        Example:
            ```python
            deleted = await cache.delete("session")
            if deleted:
                print("Session cleared")
            ```
        """
        try:
            redis_key = build_redis_key(self.namespace, key)
            count = await self._redis.delete(redis_key)
            return count > 0
        except redis.RedisError as e:
            raise StorageError(f"Failed to delete value: {e}")

    async def exists(self, key: str) -> bool:
        """
        Check if key exists.

        Args:
            key: Storage key

        Returns:
            True if key exists (not expired), False otherwise

        Raises:
            StorageError: If Redis operation fails

        Example:
            ```python
            if await cache.exists("session"):
                print("Session is active")
            ```
        """
        try:
            redis_key = build_redis_key(self.namespace, key)
            return await self._redis.exists(redis_key) > 0
        except redis.RedisError as e:
            raise StorageError(f"Failed to check existence: {e}")

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration on existing key.

        Args:
            key: Storage key
            ttl: Time-to-live in seconds

        Returns:
            True if expiration set, False if key doesn't exist

        Raises:
            StorageError: If Redis operation fails

        Example:
            ```python
            # Extend session by 1 hour
            await cache.expire("session", 3600)
            ```
        """
        try:
            redis_key = build_redis_key(self.namespace, key)
            return await self._redis.expire(redis_key, ttl)
        except redis.RedisError as e:
            raise StorageError(f"Failed to set expiration: {e}")

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment numeric value atomically.

        Creates key with value=amount if it doesn't exist.

        Args:
            key: Storage key
            amount: Amount to increment (default: 1)

        Returns:
            New value after increment

        Raises:
            StorageError: If Redis operation fails or value is not numeric

        Example:
            ```python
            # Rate limiting
            count = await cache.increment("api_calls")
            if count > 100:
                raise RateLimitError("Too many requests")
            ```
        """
        try:
            redis_key = build_redis_key(self.namespace, key)
            return await self._redis.incrby(redis_key, amount)
        except redis.RedisError as e:
            raise StorageError(f"Failed to increment value: {e}")

    async def decrement(self, key: str, amount: int = 1) -> int:
        """
        Decrement numeric value atomically.

        Args:
            key: Storage key
            amount: Amount to decrement (default: 1)

        Returns:
            New value after decrement

        Raises:
            StorageError: If Redis operation fails or value is not numeric

        Example:
            ```python
            remaining = await cache.decrement("quota_remaining")
            if remaining <= 0:
                raise QuotaExceededError()
            ```
        """
        try:
            redis_key = build_redis_key(self.namespace, key)
            return await self._redis.decrby(redis_key, amount)
        except redis.RedisError as e:
            raise StorageError(f"Failed to decrement value: {e}")

    async def get_ttl(self, key: str) -> int | None:
        """
        Get remaining TTL for a key.

        Args:
            key: Storage key

        Returns:
            Remaining TTL in seconds, -1 if no expiration, None if key doesn't exist

        Raises:
            StorageError: If Redis operation fails

        Example:
            ```python
            ttl = await cache.get_ttl("session")
            if ttl and ttl < 300:  # Less than 5 minutes
                # Extend session
                await cache.expire("session", 3600)
            ```
        """
        try:
            redis_key = build_redis_key(self.namespace, key)
            ttl = await self._redis.ttl(redis_key)

            # Redis returns -2 for non-existent keys
            if ttl == -2:
                return None

            # Redis returns -1 for keys without expiration
            return ttl
        except redis.RedisError as e:
            raise StorageError(f"Failed to get TTL: {e}")

    async def set_many(self, items: dict[str, Any], ttl: int | None = None) -> bool:
        """
        Store multiple key-value pairs.

        Args:
            items: Dictionary of key-value pairs
            ttl: Optional TTL to apply to all keys

        Returns:
            True if all stored successfully

        Raises:
            InvalidDocumentError: If any value is not JSON-serializable
            StorageError: If Redis operation fails

        Example:
            ```python
            await cache.set_many({
                "key1": {"data": 1},
                "key2": {"data": 2}
            }, ttl=600)
            ```
        """
        if not items:
            return True

        try:
            # Build pipeline for atomic operation
            pipeline = self._redis.pipeline()

            for key, value in items.items():
                try:
                    serialized = json.dumps(value)
                except (TypeError, ValueError) as e:
                    raise InvalidDocumentError(
                        f"Value for key '{key}' must be JSON-serializable: {e}"
                    )

                redis_key = build_redis_key(self.namespace, key)

                if ttl:
                    pipeline.setex(redis_key, ttl, serialized)
                else:
                    pipeline.set(redis_key, serialized)

            await pipeline.execute()
            return True
        except redis.RedisError as e:
            raise StorageError(f"Failed to set multiple values: {e}")

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Retrieve multiple values by keys.

        Args:
            keys: List of storage keys

        Returns:
            Dictionary mapping keys to values (excludes non-existent/expired keys)

        Raises:
            StorageError: If Redis operation fails

        Example:
            ```python
            data = await cache.get_many(["key1", "key2", "key3"])
            # Returns: {"key1": {...}, "key3": {...}}  # key2 expired
            ```
        """
        if not keys:
            return {}

        try:
            # Build namespaced keys
            redis_keys = [build_redis_key(self.namespace, key) for key in keys]

            # Fetch all values
            values = await self._redis.mget(redis_keys)

            # Build result dict (exclude None values)
            result = {}
            for key, serialized in zip(keys, values):
                if serialized is not None:
                    try:
                        result[key] = json.loads(serialized)
                    except json.JSONDecodeError:
                        # Skip corrupted values
                        continue

            return result
        except redis.RedisError as e:
            raise StorageError(f"Failed to get multiple values: {e}")

    async def delete_many(self, keys: list[str]) -> int:
        """
        Delete multiple keys.

        Args:
            keys: List of storage keys

        Returns:
            Number of keys actually deleted

        Raises:
            StorageError: If Redis operation fails

        Example:
            ```python
            count = await cache.delete_many(["temp1", "temp2", "temp3"])
            print(f"Deleted {count} keys")
            ```
        """
        if not keys:
            return 0

        try:
            redis_keys = [build_redis_key(self.namespace, key) for key in keys]
            return await self._redis.delete(*redis_keys)
        except redis.RedisError as e:
            raise StorageError(f"Failed to delete multiple values: {e}")

    async def clear_namespace(self) -> int:
        """
        Delete all keys in the current namespace.

        ⚠️ WARNING: This removes ALL data for this tenant/user/plugin combination!

        Returns:
            Number of keys deleted

        Raises:
            StorageError: If Redis operation fails

        Example:
            ```python
            # Clear all plugin data for this user
            count = await cache.clear_namespace()
            print(f"Cleared {count} keys")
            ```
        """
        try:
            pattern = f"{self.namespace.to_redis_prefix()}*"
            keys = []

            # Scan for matching keys (handles large datasets)
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self._redis.delete(*keys)

            return 0
        except redis.RedisError as e:
            raise StorageError(f"Failed to clear namespace: {e}")
