"""
Echo command implementation.
"""

from mcp_proxy_adapter.commands.base import BaseCommand
from mcp_proxy_adapter.core.errors import MicroserviceError


class EchoCommand(BaseCommand):
    """Echo command that returns the input message."""

    def __init__(self):
        """
        Initialize echo command.
        """
        super().__init__()
        self.name = "echo"
        self.description = "Echo command that returns the input message"
        self.version = "1.0.0"

    async def execute(self, params: dict) -> dict:
        """Execute echo command."""
        try:
            message = params.get("message", "")
            return {"echo": message, "timestamp": self._get_timestamp()}
        except Exception as e:
            raise MicroserviceError(f"Echo command failed: {str(e)}")

    def _get_timestamp(self):
        """Get current timestamp."""
        import time

        return time.time()
