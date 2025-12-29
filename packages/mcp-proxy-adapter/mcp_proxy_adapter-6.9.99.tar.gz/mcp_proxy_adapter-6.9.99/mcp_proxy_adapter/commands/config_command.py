"""
Config command implementation for managing service configuration.
"""

from typing import Dict, Any, Optional

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.config import get_config


class ConfigResult(SuccessResult):
    """
    Config operation result.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        operation: str,
        message: Optional[str] = None,
    ):
        """
        Initialize config result.

        Args:
            config: Configuration values
            operation: Operation performed
            message: Optional message
        """
        super().__init__(
            data={"config": config, "operation": operation}, message=message
        )


class ConfigCommand(Command):
    """
    Command for managing service configuration.
    """

    name = "config"
    description = "Get or set configuration values"
    result_class = ConfigResult

    async def execute(
        self,
        operation: str = "get",
        path: Optional[str] = None,
        value: Any = None,
        context: Optional[Dict] = None,
        **kwargs,
    ) -> ConfigResult:
        """
        Execute the command.

        Args:
            operation: Operation to perform (get, set)
            path: Configuration path (dot notation)
            value: Value to set (for set operation)
            context: Optional context parameter passed by framework
            **kwargs: Additional parameters

        Returns:
            Config operation result
        """
        message = None
        result_config = {}

        if operation == "get":
            config_instance = get_config()
            if path:
                # Get specific config value
                result_config = {path: config_instance.get(path)}
            else:
                # Get all config
                result_config = config_instance.get_all()
            message = "Configuration retrieved successfully"

        elif operation == "set":
            if path and value is not None:
                # Set config value
                config_instance = get_config()
                config_instance.set(path, value)
                # Save config
                config_instance.save()
                result_config = {path: value}
                message = "Configuration updated successfully"
            else:
                # Error - missing required parameters
                raise ValueError(
                    "Both 'path' and 'value' are required for 'set' operation"
                )

        else:
            # Invalid operation
            raise ValueError(
                f"Invalid operation: {operation}. Valid operations: get, set"
            )

        return ConfigResult(config=result_config, operation=operation, message=message)

