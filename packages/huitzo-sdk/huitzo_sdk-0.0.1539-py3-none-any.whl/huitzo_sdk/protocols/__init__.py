"""Protocol definitions for plugin development."""

from .command import CommandContext, CommandProtocol, CommandResult

__all__ = ["CommandProtocol", "CommandContext", "CommandResult"]
