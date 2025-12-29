"""
Custom Echo Command
This module demonstrates a custom command implementation for the full application example.
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult


class CustomEchoResult(SuccessResult):
    """Result class for custom echo command."""

    def __init__(self, message: str, timestamp: str, echo_count: int):
        """
        Initialize custom echo result.

        Args:
            message: Echoed message
            timestamp: Timestamp of the echo operation
            echo_count: Number of times message was echoed
        """
        data = {
            "message": message,
            "timestamp": timestamp,
            "echo_count": echo_count,
        }
        super().__init__(data=data)


class CustomEchoCommand(Command):
    """Custom echo command implementation."""

    name = "custom_echo"
    descr = "Custom echo command that repeats message multiple times"

    def __init__(self):
        """
        Initialize custom echo command.
        """
        super().__init__()
        self.echo_count = 0

    async def execute(
        self, message: str = "Hello from custom echo!", repeat: int = 1, **kwargs
    ) -> CustomEchoResult:
        """Execute the custom echo command."""
        repeat = min(max(repeat, 1), 10)
        self.echo_count += 1
        from datetime import datetime

        timestamp = datetime.now().isoformat()
        # Repeat the message
        echoed_message = " ".join([message] * repeat)
        return CustomEchoResult(
            message=echoed_message, timestamp=timestamp, echo_count=self.echo_count
        )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string", "default": "Hello from custom echo!"},
                "repeat": {
                    "type": "integer",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "additionalProperties": False,
        }
