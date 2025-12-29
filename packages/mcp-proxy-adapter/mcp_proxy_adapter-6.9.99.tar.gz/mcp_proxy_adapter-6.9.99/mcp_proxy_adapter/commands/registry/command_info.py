"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Command information utilities for MCP Proxy Adapter.
"""

from typing import Any, Dict, List, Optional, Type

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.core.logging import get_global_logger


class CommandInfo:
    """Utilities for getting command information."""

    def __init__(self):
        """Initialize command info utilities."""
        self.logger = get_global_logger()


    def get_command_info(self, command_name: str, command_class: Type[Command], command_types: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific command.

        Args:
            command_name: Name of the command
            command_class: Command class
            command_types: Dictionary mapping command names to types

        Returns:
            Dictionary with command information or None if not found
        """
        try:
            cmd_type = command_types.get(command_name, "unknown")
            
            info = {
                "name": command_name,
                "type": cmd_type,
                "class": command_class.__name__,
                "module": command_class.__module__,
                "file": getattr(command_class, "__file__", None),
                "description": getattr(command_class, "__doc__", None),
                "methods": self._get_command_methods(command_class),
                "attributes": self._get_command_attributes(command_class),
            }

            # Get command-specific information
            if hasattr(command_class, "get_schema"):
                try:
                    info["schema"] = command_class.get_schema()
                except Exception as e:
                    self.logger.warning(f"Failed to get schema for {command_name}: {e}")

            return info

        except Exception as e:
            self.logger.error(f"Failed to get info for command {command_name}: {e}")
            return None

    def _get_command_methods(self, command_class: Type[Command]) -> List[Dict[str, Any]]:
        """
        Get information about command methods.

        Args:
            command_class: Command class

        Returns:
            List of method information
        """
        methods = []
        
        for name, method in command_class.__dict__.items():
            if callable(method) and not name.startswith("_"):
                methods.append({
                    "name": name,
                    "description": getattr(method, "__doc__", None),
                    "is_async": hasattr(method, "__code__") and method.__code__.co_flags & 0x80,  # CO_ITERABLE_COROUTINE
                })
        
        return methods

    def _get_command_attributes(self, command_class: Type[Command]) -> Dict[str, Any]:
        """
        Get information about command attributes.

        Args:
            command_class: Command class

        Returns:
            Dictionary of attribute information
        """
        attributes = {}
        
        for name, value in command_class.__dict__.items():
            if not callable(value) and not name.startswith("_"):
                attributes[name] = {
                    "value": value,
                    "type": type(value).__name__,
                }
        
        return attributes

