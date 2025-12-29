"""Configuration-related enumerations."""

from enum import Enum


class ConfigScope(str, Enum):
    """
    Configuration scope enumeration.

    Defines the scope at which configuration values are stored and applied.

    Attributes:
        SYSTEM: System-wide configuration (applies to all users)
        USER: User-specific configuration (applies to specific user across all sessions)
        SESSION: Session-specific configuration (applies only to current session)
    """

    SYSTEM = "system"
    USER = "user"
    SESSION = "session"
