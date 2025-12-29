"""User-related enumerations."""

from enum import Enum


class UserRole(str, Enum):
    """
    User role enumeration for permission management.

    Roles define the level of access and capabilities a user has
    within the Huitzo WebCLI platform.

    Attributes:
        USER: Standard user with basic command execution privileges
        ADMIN: Administrator with full system access and management capabilities
        DEVELOPER: Developer role with plugin development and deployment privileges
    """

    USER = "user"
    ADMIN = "admin"
    DEVELOPER = "developer"
