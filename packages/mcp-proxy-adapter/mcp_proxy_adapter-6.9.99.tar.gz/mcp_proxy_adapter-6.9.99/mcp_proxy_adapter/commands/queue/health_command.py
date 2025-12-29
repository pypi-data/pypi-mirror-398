"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Command to check queue system health.
"""

from typing import Dict, Any, cast

from mcp_proxy_adapter.commands.base import Command, CommandResult
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    get_global_queue_manager,
)


class QueueHealthCommand(Command):
    """Command to check queue system health."""

    name = "queue_health"
    descr = "Check the health status of the queue system"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> CommandResult:
        """Execute queue health command."""
        try:
            # Get global queue manager
            queue_manager = await get_global_queue_manager()

            # Get health information
            health = await queue_manager.get_queue_health()

            return cast(CommandResult, SuccessResult(data=health))

        except Exception as e:
            return cast(
                CommandResult,
                ErrorResult(
                    message=f"Failed to check queue health: {str(e)}",
                    code=-32603,
                ),
            )
