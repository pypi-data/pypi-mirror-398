"""
List command implementation.
"""

from mcp_proxy_adapter.commands.base import BaseCommand
from mcp_proxy_adapter.core.errors import MicroserviceError


class ListCommand(BaseCommand):
    """List command that returns available commands."""

    def __init__(self):
        """
        Initialize list command.
        """
        super().__init__()
        self.name = "list"
        self.description = "List available commands"
        self.version = "1.0.0"

    async def execute(self, params: dict) -> dict:
        """Execute list command."""
        try:
            # This is a simplified list - in a real implementation,
            # this would query the command registry
            commands = [
                {
                    "name": "echo",
                    "description": "Echo command that returns the input message",
                    "version": "1.0.0",
                },
                {
                    "name": "list",
                    "description": "List available commands",
                    "version": "1.0.0",
                },
                {
                    "name": "health",
                    "description": "Health check command",
                    "version": "1.0.0",
                },
                {"name": "help", "description": "Help command", "version": "1.0.0"},
            ]

            return {
                "commands": commands,
                "count": len(commands),
                "timestamp": self._get_timestamp(),
            }
        except Exception as e:
            raise MicroserviceError(f"List command failed: {str(e)}")

    def _get_timestamp(self):
        """Get current timestamp."""
        import time

        return time.time()
