"""Command execution-related enumerations."""

from enum import Enum


class ExecutionStatus(str, Enum):
    """
    Command execution status enumeration.

    Tracks the lifecycle state of a command execution.

    Attributes:
        RUNNING: Command is currently executing
        COMPLETED: Command completed successfully
        FAILED: Command failed during execution
        CANCELLED: Command was cancelled by user or system
    """

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
