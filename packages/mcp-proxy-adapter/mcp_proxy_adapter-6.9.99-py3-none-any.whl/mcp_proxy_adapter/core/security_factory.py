"""
Security Factory for creating security components.

This module provides factory methods for creating security adapters, managers,
and middleware components with proper configuration and error handling.
"""

import logging
from typing import Dict, Any

from mcp_proxy_adapter.core.logging import get_global_logger
from .security_adapter import SecurityAdapter


class SecurityFactory:
    """
    Factory for creating security components.

    Provides static methods to create security adapters, managers,
    and middleware components with proper configuration handling.
    """

    @staticmethod
    def create_security_adapter(config: Dict[str, Any]) -> SecurityAdapter:
        """
        Create SecurityAdapter from configuration.

        Args:
            config: mcp_proxy_adapter configuration dictionary

        Returns:
            SecurityAdapter instance
        """
        try:
            adapter = SecurityAdapter(config)
            get_global_logger().info("Security adapter created successfully")
            return adapter
        except Exception as e:
            get_global_logger().error(f"Failed to create security adapter: {e}")
            raise

    @staticmethod

    @staticmethod
    def create_middleware(config: Dict[str, Any], framework: str = "fastapi"):
        """
        Create framework-specific security middleware.

        Args:
            config: mcp_proxy_adapter configuration dictionary
            framework: Framework type (fastapi, flask, etc.)

        Returns:
            Middleware instance or None if creation failed
        """
        try:
            adapter = SecurityFactory.create_security_adapter(config)
            middleware = adapter.create_middleware(framework)

            if middleware:
                get_global_logger().info(f"Security middleware created for {framework}")
            else:
                get_global_logger().warning(f"Failed to create security middleware for {framework}")

            return middleware

        except Exception as e:
            get_global_logger().error(f"Failed to create security middleware: {e}")
            return None

    @staticmethod

    @staticmethod

    @staticmethod

    @staticmethod

    @staticmethod
    def _deep_merge(base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """
        Deep merge two dictionaries.

        Args:
            base_dict: Base dictionary to update
            update_dict: Dictionary with updates
        """
        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                SecurityFactory._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
