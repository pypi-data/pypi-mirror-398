"""
Module with unload command implementation.
"""

from typing import Dict, Any, Optional, List

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.result import SuccessResult


class UnloadResult(SuccessResult):
    """
    Result of the unload command execution.
    """

    def __init__(
        self,
        success: bool,
        command_name: str,
        message: str,
        error: Optional[str] = None,
    ):
        """
        Initialize unload command result.

        Args:
            success: Whether unloading was successful
            command_name: Name of the command that was unloaded
            message: Result message
            error: Error message if unloading failed
        """
        data = {"success": success, "command_name": command_name}
        if error:
            data["error"] = error

        super().__init__(data=data, message=message)



class UnloadCommand(Command):
    """
    Command that unloads loaded commands from registry.

    This command allows removal of dynamically loaded commands from the command registry.
    Only commands that were loaded via the 'load' command or from the commands directory
    can be unloaded. Built-in commands and custom commands registered with higher priority
    cannot be unloaded using this command.

    When a command is unloaded:
    - The command class is removed from the loaded commands registry
    - Any command instances are also removed
    - The command becomes unavailable for execution
    - Built-in and custom commands with the same name remain unaffected

    This is useful for:
    - Removing outdated or problematic commands
    - Managing memory usage by unloading unused commands
    - Testing different versions of commands
    - Cleaning up temporary commands loaded for testing

    Note: Unloading a command does not affect other commands and does not require
    a system restart. The command can be reloaded later if needed.
    """

    name = "unload"
    result_class = UnloadResult

    async def execute(self, command_name: str, **kwargs) -> UnloadResult:
        """
        Execute unload command.

        Args:
            command_name: Name of the command to unload
            **kwargs: Additional parameters

        Returns:
            UnloadResult: Unload command result
        """
        # Unload command from registry
        result = registry.unload_command(command_name)

        return UnloadResult(
            success=result.get("success", False),
            command_name=result.get("command_name", command_name),
            message=result.get("message", "Unknown result"),
            error=result.get("error"),
        )
