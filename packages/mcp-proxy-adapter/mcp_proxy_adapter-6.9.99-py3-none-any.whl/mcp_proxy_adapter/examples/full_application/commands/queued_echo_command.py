"""
Example command that uses queue for execution.

This command demonstrates transparent queue usage - client doesn't need to know
that command is executed via queue. Server automatically queues the command
and returns job_id instead of result.
"""

import asyncio
from typing import Any, Dict

from mcp_proxy_adapter.commands.base import Command, CommandResult


class QueuedEchoCommand(Command):
    """
    Example echo command that executes via queue.

    When client calls this command, server automatically:
    1. Creates a job in the queue
    2. Returns job_id instead of result
    3. Client can check job status and get result later
    """

    name = "queued_echo"
    version = "1.0.0"
    descr = "Echo command that executes via queue"
    category = "testing"
    author = "Vasiliy Zdanovskiy"
    email = "vasilyvz@gmail.com"
    result_class = CommandResult
    use_queue = True  # Enable automatic queue execution

    async def execute(
        self, message: str = "Hello from queue!", **kwargs
    ) -> CommandResult:
        """
        Execute queued echo command.

        This command will be executed in background via queue.
        Client receives job_id and can check status later.

        Args:
            message: Message to echo
            **kwargs: Additional parameters including optional 'context'

        Returns:
            CommandResult with echoed message
        """
        # Simulate some processing time
        await asyncio.sleep(2)

        return CommandResult(
            success=True,
            data={
                "message": message,
                "processed_via_queue": True,
            },
        )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "default": "Hello from queue!",
                    "description": "Message to echo",
                }
            },
            "additionalProperties": False,
        }
