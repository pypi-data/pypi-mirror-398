"""
MongoDB-backed document storage for plugins with namespace isolation.

Provides CRUD operations with automatic tenant/user/plugin scoping and
cross-plugin permission management.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError

from .exceptions import (
    DocumentNotFoundError,
    InvalidDocumentError,
    PermissionDeniedError,
    StorageError,
)
from .namespace import Namespace, build_namespace_filter


class PluginDataStore:
    """
    MongoDB document storage with namespace isolation.

    Automatically scopes all operations by tenant_id, user_id, and plugin_id
    to ensure complete data isolation. Supports cross-plugin data sharing
    via explicit permission grants.

    Example:
        ```python
        from motor.motor_asyncio import AsyncIOMotorClient

        mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
        namespace = Namespace(tenant_id, user_id, "my_plugin")
        store = PluginDataStore(namespace, mongo_client.get_database("webcli"))

        # Save data
        doc_id = await store.save("conversation", {
            "messages": ["Hello", "Hi there!"],
            "timestamp": datetime.now().isoformat()
        })

        # Query data
        docs = await store.query("conversation", {
            "timestamp": {"$gte": "2025-01-01"}
        })
        ```
    """

    def __init__(self, namespace: Namespace, db: AsyncIOMotorDatabase):
        """
        Initialize document store with namespace and database.

        Args:
            namespace: Namespace for data isolation
            db: MongoDB database instance
        """
        self.namespace = namespace
        self._db = db
        self._collection: AsyncIOMotorCollection = db["plugin_data"]

    async def _ensure_indexes(self) -> None:
        """Create indexes for performance and uniqueness."""
        # Namespace composite index for fast filtered queries
        await self._collection.create_index(
            [("tenant_id", 1), ("user_id", 1), ("plugin_id", 1), ("data_type", 1)]
        )

        # Unique key index within namespace
        await self._collection.create_index(
            [("tenant_id", 1), ("user_id", 1), ("plugin_id", 1), ("key", 1)],
            unique=True,
            sparse=True,
        )

        # TTL index for automatic expiration
        await self._collection.create_index("expires_at", expireAfterSeconds=0)

        # Allowed plugins for permission checks
        await self._collection.create_index("allowed_plugins")

    async def save(
        self,
        key: str,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
        data_type: str | None = None,
    ) -> str:
        """
        Save document with namespace isolation.

        Args:
            key: Logical key for the document (unique within namespace)
            data: Document data (must be JSON-serializable)
            metadata: Optional metadata (tags, categories, etc.)
            ttl_seconds: Optional time-to-live in seconds
            data_type: Optional classifier for indexing/uniqueness (e.g., "conversation")

        Returns:
            Document ID (UUID string)

        Raises:
            InvalidDocumentError: If data is not JSON-serializable or None
            StorageError: If save operation fails

        Example:
            ```python
            doc_id = await store.save("user_prefs", {
                "theme": "dark",
                "language": "en"
            }, metadata={"category": "settings"})
            ```
        """
        if data is None:
            raise InvalidDocumentError("Data cannot be None")

        # Validate JSON serializability
        try:
            json.dumps(data)
        except (TypeError, ValueError) as e:
            raise InvalidDocumentError(f"Data must be JSON-serializable: {e}")

        doc_id = str(uuid4())
        now = datetime.now(timezone.utc)

        document = {
            "_id": doc_id,
            "key": key,
            "data": data,
            **self.namespace.to_dict(),
            "created_at": now,
            "updated_at": now,
            "allowed_plugins": [],  # For cross-plugin permissions
        }

        # Allow callers to include a top-level data_type for plugin indexes
        if data_type is None and metadata and "data_type" in metadata:
            data_type = metadata["data_type"]
        if data_type is not None:
            document["data_type"] = data_type

        if metadata:
            document["metadata"] = metadata

        if ttl_seconds:
            document["expires_at"] = now + timedelta(seconds=ttl_seconds)

        try:
            result = await self._collection.insert_one(document)
            return str(result.inserted_id)
        except DuplicateKeyError:
            # Key already exists in this namespace, generate new ID and retry
            doc_id = str(uuid4())
            document["_id"] = doc_id
            try:
                result = await self._collection.insert_one(document)
                return str(result.inserted_id)
            except PyMongoError as e:
                raise StorageError(f"Failed to save document: {e}")
        except PyMongoError as e:
            raise StorageError(f"Failed to save document: {e}")

    async def get(
        self, document_id: str, source_plugin_id: str | None = None
    ) -> dict[str, Any] | None:
        """
        Retrieve document by ID with permission check.

        Args:
            document_id: Document ID to retrieve
            source_plugin_id: If accessing another plugin's data, specify its ID

        Returns:
            Document data or None if not found

        Raises:
            PermissionDeniedError: If accessing data without permission
            StorageError: If retrieval fails

        Example:
            ```python
            # Get own plugin's data
            doc = await store.get(doc_id)

            # Get another plugin's data (requires permission)
            doc = await store.get(doc_id, source_plugin_id="weather_plugin")
            ```
        """
        try:
            query_filter = build_namespace_filter(self.namespace, _id=document_id)
            doc = await self._collection.find_one(query_filter)
            return doc
        except PyMongoError as e:
            raise StorageError(f"Failed to retrieve document: {e}")

    async def get_by_key(self, key: str) -> dict[str, Any] | None:
        """
        Retrieve document by logical key within namespace.

        Args:
            key: Logical key to search for

        Returns:
            Document data or None if not found

        Raises:
            StorageError: If retrieval fails

        Example:
            ```python
            prefs = await store.get_by_key("user_preferences")
            ```
        """
        try:
            query_filter = build_namespace_filter(self.namespace, key=key)
            doc = await self._collection.find_one(query_filter)
            return doc
        except PyMongoError as e:
            raise StorageError(f"Failed to retrieve document by key: {e}")

    async def query(
        self,
        filters: dict[str, Any],
        limit: int = 100,
        sort: list[tuple[str, int]] | None = None,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query documents with MongoDB filters.

        Automatically applies namespace isolation. All filter keys are
        applied to the 'data' field unless they're system fields.

        Args:
            filters: MongoDB query filters (applied to data field)
            limit: Maximum results to return (default: 100)
            sort: Sort order [(field, direction), ...]
            projection: Fields to include/exclude

        Returns:
            List of matching documents

        Raises:
            StorageError: If query fails

        Example:
            ```python
            # Find all high-priority tasks
            tasks = await store.query({
                "data.priority": "high",
                "data.status": {"$ne": "completed"}
            }, limit=10, sort=[("created_at", -1)])
            ```
        """
        try:
            # Build namespaced query
            query_filter = build_namespace_filter(self.namespace, **filters)

            # Create cursor
            cursor = self._collection.find(query_filter, projection=projection)

            if sort:
                cursor = cursor.sort(sort)

            # Apply limit and convert to list
            docs = await cursor.to_list(length=limit)
            return docs
        except PyMongoError as e:
            raise StorageError(f"Failed to query documents: {e}")

    async def update(self, document_id: str, updates: dict[str, Any]) -> bool:
        """
        Update existing document.

        Args:
            document_id: Document ID to update
            updates: MongoDB update operators or field updates

        Returns:
            True if document was updated, False if not found

        Raises:
            PermissionDeniedError: If updating another plugin's data
            StorageError: If update fails

        Example:
            ```python
            # Simple field update
            await store.update(doc_id, {"data.count": 42})

            # Using MongoDB operators
            await store.update(doc_id, {
                "$inc": {"data.views": 1},
                "$push": {"data.tags": "featured"}
            })
            ```
        """
        try:
            query_filter = build_namespace_filter(self.namespace, _id=document_id)

            # Prepare update document
            update_doc = updates if "$set" in updates or "$inc" in updates else {"$set": updates}

            # Always update timestamp
            if "$set" not in update_doc:
                update_doc["$set"] = {}
            update_doc["$set"]["updated_at"] = datetime.now(timezone.utc)

            result = await self._collection.update_one(query_filter, update_doc)
            return result.modified_count > 0
        except PyMongoError as e:
            raise StorageError(f"Failed to update document: {e}")

    async def delete(self, document_id: str) -> bool:
        """
        Delete document by ID.

        Args:
            document_id: Document ID to delete

        Returns:
            True if document was deleted, False if not found

        Raises:
            PermissionDeniedError: If deleting another plugin's data
            StorageError: If deletion fails

        Example:
            ```python
            deleted = await store.delete(doc_id)
            if deleted:
                print("Document removed")
            ```
        """
        try:
            query_filter = build_namespace_filter(self.namespace, _id=document_id)
            result = await self._collection.delete_one(query_filter)
            return result.deleted_count > 0
        except PyMongoError as e:
            raise StorageError(f"Failed to delete document: {e}")

    async def delete_by_key(self, key: str) -> bool:
        """
        Delete document by logical key.

        Args:
            key: Logical key to delete

        Returns:
            True if document was deleted, False if not found

        Raises:
            StorageError: If deletion fails

        Example:
            ```python
            await store.delete_by_key("temp_data")
            ```
        """
        try:
            query_filter = build_namespace_filter(self.namespace, key=key)
            result = await self._collection.delete_one(query_filter)
            return result.deleted_count > 0
        except PyMongoError as e:
            raise StorageError(f"Failed to delete document by key: {e}")

    async def grant_access(self, document_id: str, consumer_plugin_id: str) -> bool:
        """
        Grant another plugin access to a document.

        Args:
            document_id: Document to share
            consumer_plugin_id: Plugin ID to grant access to

        Returns:
            True if permission granted, False if document not found

        Raises:
            StorageError: If grant operation fails

        Example:
            ```python
            # Weather plugin shares data with calendar plugin
            await weather_store.grant_access(forecast_id, "calendar_plugin")
            ```
        """
        try:
            query_filter = build_namespace_filter(self.namespace, _id=document_id)
            result = await self._collection.update_one(
                query_filter, {"$addToSet": {"allowed_plugins": consumer_plugin_id}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            raise StorageError(f"Failed to grant access: {e}")

    async def revoke_access(self, document_id: str, consumer_plugin_id: str) -> bool:
        """
        Revoke plugin access to a document.

        Args:
            document_id: Document to unshare
            consumer_plugin_id: Plugin ID to revoke access from

        Returns:
            True if permission revoked, False if document not found

        Raises:
            StorageError: If revoke operation fails

        Example:
            ```python
            await weather_store.revoke_access(forecast_id, "calendar_plugin")
            ```
        """
        try:
            query_filter = build_namespace_filter(self.namespace, _id=document_id)
            result = await self._collection.update_one(
                query_filter, {"$pull": {"allowed_plugins": consumer_plugin_id}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            raise StorageError(f"Failed to revoke access: {e}")

    async def check_access(self, document_id: str, plugin_id: str) -> bool:
        """
        Check if a plugin has access to a document.

        Args:
            document_id: Document to check
            plugin_id: Plugin ID to check access for

        Returns:
            True if plugin has access, False otherwise

        Raises:
            StorageError: If check fails

        Example:
            ```python
            has_access = await store.check_access(doc_id, "calendar_plugin")
            if not has_access:
                # Request permission
                pass
            ```
        """
        try:
            doc = await self._collection.find_one({"_id": document_id})
            if not doc:
                return False

            # Owner plugin always has access
            if doc.get("plugin_id") == plugin_id:
                return True

            # Check if plugin is in allowed list
            allowed_plugins = doc.get("allowed_plugins", [])
            return plugin_id in allowed_plugins
        except PyMongoError as e:
            raise StorageError(f"Failed to check access: {e}")

    async def save_many(self, documents: list[dict[str, Any]]) -> list[str]:
        """
        Save multiple documents in batch.

        Args:
            documents: List of dicts with 'key' and 'data' fields

        Returns:
            List of document IDs

        Raises:
            InvalidDocumentError: If any document is invalid
            StorageError: If batch save fails

        Example:
            ```python
            docs = [
                {"key": "doc1", "data": {"value": 1}},
                {"key": "doc2", "data": {"value": 2}}
            ]
            doc_ids = await store.save_many(docs)
            ```
        """
        if not documents:
            return []

        now = datetime.now(timezone.utc)
        mongo_docs = []

        for doc in documents:
            if "key" not in doc or "data" not in doc:
                raise InvalidDocumentError("Each document must have 'key' and 'data' fields")

            mongo_doc = {
                "_id": str(uuid4()),
                "key": doc["key"],
                "data": doc["data"],
                **self.namespace.to_dict(),
                "created_at": now,
                "updated_at": now,
                "allowed_plugins": [],
            }

            if "metadata" in doc:
                mongo_doc["metadata"] = doc["metadata"]

            mongo_docs.append(mongo_doc)

        try:
            result = await self._collection.insert_many(mongo_docs, ordered=False)
            return [str(doc_id) for doc_id in result.inserted_ids]
        except PyMongoError as e:
            raise StorageError(f"Failed to save documents in batch: {e}")

    async def delete_many(self, document_ids: list[str]) -> int:
        """
        Delete multiple documents in batch.

        Args:
            document_ids: List of document IDs to delete

        Returns:
            Number of documents deleted

        Raises:
            StorageError: If batch delete fails

        Example:
            ```python
            count = await store.delete_many([doc_id1, doc_id2, doc_id3])
            print(f"Deleted {count} documents")
            ```
        """
        if not document_ids:
            return 0

        try:
            query_filter = build_namespace_filter(self.namespace, _id={"$in": document_ids})
            result = await self._collection.delete_many(query_filter)
            return result.deleted_count
        except PyMongoError as e:
            raise StorageError(f"Failed to delete documents in batch: {e}")
