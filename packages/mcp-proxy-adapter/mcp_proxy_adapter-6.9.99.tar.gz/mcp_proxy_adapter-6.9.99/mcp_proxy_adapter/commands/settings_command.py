"""
Settings command for demonstrating configuration management.
"""

from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.core.settings import (
    Settings,
    get_setting,
    set_setting,
    reload_settings,
)


class SettingsResult:
    """Result class for settings command."""

    def __init__(
        self,
        success: bool,
        operation: str,
        key: Optional[str] = None,
        value: Any = None,
        all_settings: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ):
        """
        Initialize settings command result.

        Args:
            success: Whether operation was successful
            operation: Operation name (get, set, get_all, reload)
            key: Configuration key (for get/set operations)
            value: Configuration value (for set operation)
            all_settings: All settings dictionary (for get_all operation)
            error_message: Error message if operation failed
        """
        self.success = success
        self.operation = operation
        self.key = key
        self.value = value
        self.all_settings = all_settings
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary for JSON serialization.

        Returns:
            Dictionary with result data
        """
        result = {
            "success": self.success,
            "operation": self.operation,
        }
        if self.key:
            result["key"] = self.key
        if self.value is not None:
            result["value"] = self.value
        if self.all_settings:
            result["all_settings"] = self.all_settings
        if self.error_message:
            result["error_message"] = self.error_message
        return result


class SettingsCommand(Command):
    """Command for managing framework settings."""

    name = "settings"
    description = "Manage framework settings and configuration"

    async def execute(self, **params) -> SettingsResult:
        """
        Execute settings command.

        Args:
            operation: Operation to perform (get, set, get_all, reload)
            key: Configuration key (for get/set operations)
            value: Configuration value (for set operation)

        Returns:
            SettingsResult with operation result
        """
        try:
            operation = params.get("operation", "get_all")

            if operation == "get":
                key = params.get("key")
                if not key:
                    return SettingsResult(
                        success=False,
                        operation=operation,
                        error_message="Key is required for 'get' operation",
                    )

                value = get_setting(key)
                return SettingsResult(
                    success=True, operation=operation, key=key, value=value
                )

            elif operation == "set":
                key = params.get("key")
                value = params.get("value")

                if not key:
                    return SettingsResult(
                        success=False,
                        operation=operation,
                        error_message="Key is required for 'set' operation",
                    )

                set_setting(key, value)
                return SettingsResult(
                    success=True, operation=operation, key=key, value=value
                )

            elif operation == "get_all":
                all_settings = Settings.get_all_settings()
                return SettingsResult(
                    success=True, operation=operation, all_settings=all_settings
                )

            elif operation == "reload":
                reload_settings()
                return SettingsResult(success=True, operation=operation)

            else:
                return SettingsResult(
                    success=False,
                    operation=operation,
                    error_message=f"Unknown operation: {operation}. Supported operations: get, set, get_all, reload",
                )

        except Exception as e:
            return SettingsResult(
                success=False,
                operation=params.get("operation", "unknown"),
                error_message=str(e),
            )
