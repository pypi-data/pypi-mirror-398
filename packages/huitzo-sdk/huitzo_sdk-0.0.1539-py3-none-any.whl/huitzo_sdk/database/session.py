"""Database session management for plugins.

This module provides an opaque interface for plugins to access database sessions
without exposing backend implementation details.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Global session factory (injected by backend during startup)
_session_factory: Callable[[], Any] | None = None


def register_session_factory(factory: Callable[[], Any]) -> None:
    """
    Register the database session factory.

    This function is called by the backend during application startup
    to inject the session factory into the SDK. Plugins should never
    call this function directly.

    Args:
        factory: Callable that returns an async context manager for database sessions

    Note:
        This is an internal function used by the backend infrastructure.
        Plugin developers should not call this function.
    """
    global _session_factory
    _session_factory = factory
    logger.debug("Database session factory registered in SDK")


@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session context manager.

    This provides plugins with access to the database through an opaque
    session object. Plugins can use this session to query and persist data
    using SQLAlchemy ORM.

    Yields:
        AsyncSession: Database session for async operations

    Raises:
        RuntimeError: If session factory has not been registered by backend

    Example:
        ```python
        from huitzo_sdk.database import get_async_session_context
        from huitzo_sdk.protocols.command import CommandContext, CommandResult

        async def execute(
            self, args: dict, context: CommandContext
        ) -> CommandResult:
            async with get_async_session_context() as db:
                # Query database
                result = await db.execute(select(MyModel).where(...))
                items = result.scalars().all()

                # Create new record
                new_item = MyModel(name="test")
                db.add(new_item)
                await db.commit()

            return CommandResult(exit_code=0, stdout="Success\\n")
        ```

    Note:
        - Sessions are automatically rolled back on exceptions
        - Sessions are automatically committed if no exceptions occur
        - Always use async/await with this context manager
        - The session is only valid within the context manager scope
    """
    if _session_factory is None:
        raise RuntimeError(
            "Database session factory not registered. "
            "This indicates the backend did not properly initialize the SDK bridge. "
            "Contact your administrator or check backend startup logs."
        )

    # The factory itself is an async context manager
    async with _session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error in plugin: {e}")
            await session.rollback()
            raise
