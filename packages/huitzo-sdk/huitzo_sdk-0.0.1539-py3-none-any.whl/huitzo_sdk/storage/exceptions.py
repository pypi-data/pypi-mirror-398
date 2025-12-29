"""
Storage-specific exceptions for plugin data operations.

Provides granular error handling for MongoDB and Redis storage operations.
"""


class StorageError(Exception):
    """
    Base exception for all storage operations.

    Raised when a storage operation fails due to database errors,
    connection issues, or other infrastructure problems.
    """

    pass


class DocumentNotFoundError(StorageError):
    """
    Raised when attempting to access a document that doesn't exist.

    Example:
        ```python
        try:
            doc = await store.get("nonexistent_id")
        except DocumentNotFoundError:
            # Handle missing document
            pass
        ```
    """

    pass


class PermissionDeniedError(StorageError):
    """
    Raised when attempting to access data without proper permissions.

    This occurs when:
    - Trying to access another plugin's data without grant_access()
    - Attempting cross-tenant access
    - Trying to modify data owned by different user

    Example:
        ```python
        try:
            # Plugin B trying to access Plugin A's data
            doc = await plugin_b_store.get(
                doc_id,
                source_plugin_id="plugin_a"
            )
        except PermissionDeniedError:
            # Request permission via grant_access()
            pass
        ```
    """

    pass


class InvalidDocumentError(StorageError):
    """
    Raised when document data is invalid or malformed.

    This occurs when:
    - Data is not JSON-serializable
    - Required fields are missing
    - Data violates schema constraints

    Example:
        ```python
        try:
            # Attempting to save non-serializable data
            await store.save("key", {"func": lambda x: x})
        except InvalidDocumentError:
            # Ensure data is JSON-serializable
            pass
        ```
    """

    pass


class NamespaceError(StorageError):
    """
    Raised when namespace configuration is invalid.

    This occurs when:
    - Tenant ID, user ID, or plugin ID are invalid
    - Namespace isolation is violated
    - Cross-namespace operation attempted

    Example:
        ```python
        try:
            namespace = Namespace(
                tenant_id="invalid",  # Should be UUID
                user_id=uuid4(),
                plugin_id="my_plugin"
            )
        except NamespaceError:
            # Fix namespace configuration
            pass
        ```
    """

    pass


class QuotaExceededError(StorageError):
    """
    Raised when storage quota limits are exceeded.

    This occurs when:
    - Document count exceeds quota
    - Storage size exceeds quota
    - Rate limits exceeded

    Example:
        ```python
        try:
            await store.save("key", large_data)
        except QuotaExceededError:
            # Clean up old data or request quota increase
            pass
        ```
    """

    pass


class ConnectionError(StorageError):
    """
    Raised when unable to connect to storage backend.

    This occurs when:
    - MongoDB/Redis server is unreachable
    - Network timeout
    - Authentication failure

    Example:
        ```python
        try:
            doc = await store.get("doc_id")
        except ConnectionError:
            # Retry with exponential backoff
            pass
        ```
    """

    pass
