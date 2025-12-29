"""
Help command implementation.
"""

from mcp_proxy_adapter.commands.base import BaseCommand
from mcp_proxy_adapter.core.errors import MicroserviceError


class HelpCommand(BaseCommand):
    """Help command that provides usage information."""

    def __init__(self):
        """
        Initialize help command.
        """
        super().__init__()
        self.name = "help"
        self.description = "Get help information"
        self.version = "1.0.0"

    async def execute(self, params: dict) -> dict:
        """Execute help command."""
        try:
            command = params.get("command")

            if command:
                # Get help for specific command
                help_info = self._get_command_help(command)
                return {
                    "command": command,
                    "help": help_info,
                    "timestamp": self._get_timestamp(),
                }
            else:
                # Get general help
                return {
                    "help": "MCP Proxy Adapter - Available commands: echo, list, health, help",
                    "usage": "Use 'help' with a command name to get specific help",
                    "timestamp": self._get_timestamp(),
                }
        except Exception as e:
            raise MicroserviceError(f"Help command failed: {str(e)}")

    def _get_command_help(self, command: str) -> str:
        """Get help for specific command."""
        help_map = {
            "echo": "Echo command - returns the input message. Usage: {'message': 'your message'}",
            "list": "List command - returns available commands. Usage: {}",
            "health": "Health command - returns server health status. Usage: {}",
            "help": "Help command - provides usage information. Usage: {'command': 'command_name'} (optional)",
        }
        return help_map.get(command, f"No help available for command '{command}'")

    def _get_timestamp(self):
        """Get current timestamp."""
        import time

        return time.time()
