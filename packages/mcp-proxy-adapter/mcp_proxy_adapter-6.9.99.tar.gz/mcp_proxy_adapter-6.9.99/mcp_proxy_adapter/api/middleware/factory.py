"""
Middleware Factory for creating and managing middleware components.

This module provides a factory for creating middleware components with proper
configuration and dependency management.
"""

import logging
from typing import Dict, Any, List, Optional, Type

from fastapi import FastAPI

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.security_factory import SecurityFactory
from .base import BaseMiddleware
from .unified_security import UnifiedSecurityMiddleware
from .error_handling import ErrorHandlingMiddleware
from .logging import LoggingMiddleware
from .user_info_middleware import UserInfoMiddleware


class MiddlewareFactory:
    """
    Factory for creating and managing middleware components.

    Provides methods to create middleware components with proper configuration
    and dependency management.
    """

    def __init__(self, app: FastAPI, config: Dict[str, Any]):
        """
        Initialize middleware factory.

        Args:
            app: FastAPI application
            config: Application configuration
        """
        self.app = app
        self.config = config
        self.middleware_stack: List[BaseMiddleware] = []

        get_global_logger().info("Middleware factory initialized")

    def create_security_middleware(self) -> Optional[UnifiedSecurityMiddleware]:
        """
        Create unified security middleware.

        Returns:
            UnifiedSecurityMiddleware instance or None if creation failed
        """
        try:
            security_config = self.config.get("security", {})

            if not security_config.get("enabled", True):
                get_global_logger().info("Security middleware disabled by configuration")
                return None

            middleware = UnifiedSecurityMiddleware(self.app, self.config)
            self.middleware_stack.append(middleware)

            get_global_logger().info("Unified security middleware created successfully")
            return middleware

        except Exception as e:
            get_global_logger().error(f"Failed to create unified security middleware: {e}")
            return None

    def create_error_handling_middleware(self) -> Optional[ErrorHandlingMiddleware]:
        """
        Create error handling middleware.

        Returns:
            ErrorHandlingMiddleware instance or None if creation failed
        """
        try:
            # Import here to avoid circular imports
            from .error_handling import ErrorHandlingMiddleware

            middleware = ErrorHandlingMiddleware(self.app)
            self.middleware_stack.append(middleware)

            get_global_logger().info("Error handling middleware created successfully")
            return middleware

        except Exception as e:
            get_global_logger().error(f"Failed to create error handling middleware: {e}")
            return None

    def create_logging_middleware(self) -> Optional[LoggingMiddleware]:
        """
        Create logging middleware.

        Returns:
            LoggingMiddleware instance or None if creation failed
        """
        try:
            # Import here to avoid circular imports
            from .logging import LoggingMiddleware

            middleware = LoggingMiddleware(self.app, self.config)
            self.middleware_stack.append(middleware)

            get_global_logger().info("Logging middleware created successfully")
            return middleware

        except Exception as e:
            get_global_logger().error(f"Failed to create logging middleware: {e}")
            return None

    def create_user_info_middleware(self) -> Optional[UserInfoMiddleware]:
        """
        Create user info middleware.

        Returns:
            UserInfoMiddleware instance or None if creation failed
        """
        try:
            middleware = UserInfoMiddleware(self.app, self.config)
            self.middleware_stack.append(middleware)

            get_global_logger().info("User info middleware created successfully")
            return middleware

        except Exception as e:
            get_global_logger().error(f"Failed to create user info middleware: {e}")
            return None


    def get_middleware_by_type(
        self, middleware_type: Type[BaseMiddleware]
    ) -> Optional[BaseMiddleware]:
        """
        Get middleware instance by type.

        Args:
            middleware_type: Type of middleware to find

        Returns:
            Middleware instance or None if not found
        """
        for middleware in self.middleware_stack:
            if isinstance(middleware, middleware_type):
                return middleware
        return None



