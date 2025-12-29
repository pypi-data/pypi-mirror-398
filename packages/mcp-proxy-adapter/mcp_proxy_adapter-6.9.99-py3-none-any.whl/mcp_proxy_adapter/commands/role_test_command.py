"""
Role Test Command

This command tests role-based access control by checking user permissions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import logging
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult


from mcp_proxy_adapter.core.logging import get_global_logger
logger = logging.getLogger(__name__)


class RoleTestCommandResult(SuccessResult):
    """Result for role test command."""

    def __init__(self, user_role: str, permissions: list, action: str, allowed: bool):
        """
        Initialize role test result.

        Args:
            user_role: User's role
            permissions: User's permissions
            action: Action being tested
            allowed: Whether action is allowed
        """
        super().__init__()
        self.user_role = user_role
        self.permissions = permissions
        self.action = action
        self.allowed = allowed


class RoleTestCommand(Command):
    """Test role-based access control."""

    name = "roletest"
    descr = "Test role-based access control"
    category = "security"
    author = "Vasiliy Zdanovskiy"
    email = "vasilyvz@gmail.com"

    async def execute(self, **kwargs) -> RoleTestCommandResult:
        """
        Execute role test command.

        Args:
            **kwargs: Command parameters including context

        Returns:
            RoleTestCommandResult
        """
        # Extract parameters
        action = kwargs.get("action", "read")
        context = kwargs.get("context", {})

        # Get user info from context
        user_role = "guest"  # Default
        permissions = ["read"]  # Default

        if context:
            user_info = context.get("user", {})
            user_role = user_info.get("role", "guest")
            permissions = user_info.get("permissions", ["read"])

        # Check if action is allowed
        allowed = self._check_permission(action, permissions)

        get_global_logger().info(f"Role test: user={user_role}, action={action}, allowed={allowed}")

        return RoleTestCommandResult(user_role, permissions, action, allowed)

    def _check_permission(self, action: str, permissions: list) -> bool:
        """
        Check if action is allowed for given permissions.

        Args:
            action: Action to check
            permissions: User permissions

        Returns:
            True if allowed, False otherwise
        """
        # Admin has all permissions
        if "*" in permissions:
            return True

        # Check specific permission
        return action in permissions
