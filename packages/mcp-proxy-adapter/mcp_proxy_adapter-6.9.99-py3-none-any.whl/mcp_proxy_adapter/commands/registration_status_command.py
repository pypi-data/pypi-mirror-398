"""
Registration Status Command

This command provides information about the current proxy registration status,
including async registration state, heartbeat status, and statistics.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any
from dataclasses import dataclass

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.logging import get_global_logger


@dataclass
class RegistrationStatusCommandResult(SuccessResult):
    """Result of registration status command."""

    status: Dict[str, Any]
    message: str = "Registration status retrieved successfully"


class RegistrationStatusCommand(Command):
    """Command to get proxy registration status."""

    name = "registration_status"
    descr = "Get current proxy registration status and statistics"
    category = "proxy"
    author = "Vasiliy Zdanovskiy"
    email = "vasilyvz@gmail.com"

    async def execute(self, **kwargs) -> RegistrationStatusCommandResult:
        """
        Execute registration status command.

        Returns:
            RegistrationStatusCommandResult with current status
        """
        get_global_logger().info("Executing registration status command")

        try:
            from mcp_proxy_adapter.core.async_proxy_registration import (
                get_registration_status,
            )

            status = get_registration_status()
            
            get_global_logger().info(f"Registration status retrieved: {status}")

            return RegistrationStatusCommandResult(
                status=status,
                message="Registration status retrieved successfully"
            )

        except Exception as e:
            get_global_logger().error(f"Failed to get registration status: {e}")
            
            error_status = {
                "state": "error",
                "error": str(e),
                "thread_alive": False
            }
            
            return RegistrationStatusCommandResult(
                status=error_status,
                message=f"Failed to get registration status: {e}"
            )
