"""SQLAlchemy declarative base for plugin models.

Plugins should share the backend's DeclarativeBase so foreign keys to
core tables (e.g., users) can be resolved correctly. The backend injects
its Base at startup via `register_base`; until then a lightweight
fallback base is used so unit tests can run in isolation.
"""

import logging

from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


class PluginBase(DeclarativeBase):
    """Fallback base used when the backend does not register one."""

    pass


# Start with the fallback; backend will override via register_base().
_registered_base: type[DeclarativeBase] = PluginBase


def register_base(base_class: type[DeclarativeBase]) -> None:
    """
    Register the backend's declarative base so plugins share metadata.

    This must run before plugin models are imported; otherwise they will
    inherit from the fallback base instead of the backend's Base.
    """
    global _registered_base, Base
    _registered_base = base_class
    # Keep Base alias in sync for downstream imports
    Base = base_class
    logger.debug("SQLAlchemy Base registered in SDK")


def get_base() -> type[DeclarativeBase]:
    """Return the currently registered base (backend or fallback)."""
    return _registered_base


# Export alias used by plugin models
Base = _registered_base
