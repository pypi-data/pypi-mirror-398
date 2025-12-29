"""
Command Permission Middleware

This middleware checks permissions for specific commands based on user roles.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import logging
from typing import Any, Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from mcp_proxy_adapter.core.logging import get_global_logger


class CommandPermissionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for checking command permissions.

    This middleware checks if the authenticated user has the required
    permissions to execute specific commands.
    """

    def __init__(self, app, config: Dict[str, Any]):
        """
        Initialize command permission middleware.

        Args:
            app: FastAPI application
            config: Configuration dictionary
        """
        super().__init__(app)
        self.config = config

        # Define command permissions
        self.command_permissions = {
            "echo": ["read"],
            "health": ["read"],
            "role_test": ["read"],
            "config": ["read"],
            "help": ["read"],
            # Add more commands as needed
        }

        get_global_logger().info("Command permission middleware initialized")


    def _check_permissions(
        self, user_roles: list, user_permissions: list, required_permissions: list
    ) -> bool:
        """
        Check if user has required permissions.

        Args:
            user_roles: User roles
            user_permissions: User permissions
            required_permissions: Required permissions

        Returns:
            True if user has required permissions
        """
        # Admin has all permissions
        if "admin" in user_roles or "*" in user_permissions:
            return True

        # Check if user has all required permissions
        for required in required_permissions:
            if required not in user_permissions:
                return False

        return True
