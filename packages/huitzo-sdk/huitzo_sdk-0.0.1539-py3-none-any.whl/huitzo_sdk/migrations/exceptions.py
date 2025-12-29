"""Exceptions for plugin migration system."""


class MigrationError(Exception):
    """Base exception for migration errors."""

    pass


class MigrationNotFoundError(MigrationError):
    """Raised when a migration version is not found."""

    pass


class MigrationVersionError(MigrationError):
    """Raised when migration version is invalid or out of order."""

    pass


class MigrationExecutionError(MigrationError):
    """Raised when migration execution fails."""

    pass
