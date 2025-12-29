"""
Module for registering built-in framework commands.

This module contains the procedure for adding predefined commands
that are part of the framework.
"""

from typing import List, Optional, Dict, Any
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.hooks import hooks
from mcp_proxy_adapter.commands.help_command import HelpCommand
from mcp_proxy_adapter.commands.health_command import HealthCommand
from mcp_proxy_adapter.commands.config_command import ConfigCommand
from mcp_proxy_adapter.commands.reload_command import ReloadCommand
from mcp_proxy_adapter.commands.settings_command import SettingsCommand
from mcp_proxy_adapter.commands.load_command import LoadCommand
from mcp_proxy_adapter.commands.unload_command import UnloadCommand
from mcp_proxy_adapter.commands.plugins_command import PluginsCommand
from mcp_proxy_adapter.commands.transport_management_command import (
    TransportManagementCommand,
)
from mcp_proxy_adapter.commands.proxy_registration_command import (
    ProxyRegistrationCommand,
)
from mcp_proxy_adapter.commands.echo_command import EchoCommand
from mcp_proxy_adapter.commands.role_test_command import RoleTestCommand
from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.config import get_config


def register_builtin_commands(config_data: Optional[Dict[str, Any]] = None) -> int:
    """
    Register all built-in framework commands.

    Args:
        config_data: Optional configuration data dictionary. If provided, will be used
                    to check if queue_manager is enabled. If not provided, will try
                    to get configuration from global config instance.

    Returns:
        Number of built-in commands registered.
    """
    get_global_logger().debug("Registering built-in framework commands...")

    builtin_commands = [
        HelpCommand,
        HealthCommand,
        ConfigCommand,
        ReloadCommand,
        SettingsCommand,
        LoadCommand,
        UnloadCommand,
        PluginsCommand,
        TransportManagementCommand,
        ProxyRegistrationCommand,
        EchoCommand,
        RoleTestCommand,
    ]

    registered_count = 0

    for command_class in builtin_commands:
        try:
            # Get command name for logging
            command_name = getattr(
                command_class, "name", command_class.__name__.lower()
            )
            registry.register(command_class)
            registered_count += 1
            get_global_logger().debug(f"Registered built-in command: {command_name}")
        except Exception as e:
            get_global_logger().error(
                f"Failed to register built-in command {command_class.__name__}: {e}"
            )

    # Automatically register queue commands if queue_manager is enabled
    queue_commands_count = _register_queue_commands_if_enabled(config_data)
    registered_count += queue_commands_count

    # Execute custom commands hooks to register user-defined commands
    hooks_executed = hooks.execute_custom_commands_hooks(registry)
    if hooks_executed > 0:
        get_global_logger().info(
            f"Executed {hooks_executed} custom commands hooks"
        )

    get_global_logger().info(
        f"Registered {registered_count} built-in framework commands"
    )
    return registered_count


def _register_queue_commands_if_enabled(config_data: Optional[Dict[str, Any]] = None) -> int:
    """
    Automatically register queue management commands if queue_manager is enabled in configuration.

    Args:
        config_data: Optional configuration data dictionary. If provided, will be used
                    to check if queue_manager is enabled. If not provided, will try
                    to get configuration from global config instance.

    Returns:
        Number of queue commands registered (0 if queue_manager is disabled)
    """
    try:
        # Try to get config_data from parameter first, then from global config
        if config_data is None:
            cfg = get_config()
            config_data = getattr(cfg, "config_data", {})
        
        queue_manager_config = config_data.get("queue_manager", {}) if config_data else {}
        
        # Check if queue_manager is enabled
        if not queue_manager_config.get("enabled", False):
            get_global_logger().debug("Queue manager is disabled, skipping queue commands registration")
            return 0

        # Import queue commands
        from mcp_proxy_adapter.commands.queue_commands import (
            QueueAddJobCommand,
            QueueStartJobCommand,
            QueueStopJobCommand,
            QueueDeleteJobCommand,
            QueueGetJobStatusCommand,
            QueueListJobsCommand,
            QueueHealthCommand,
        )

        queue_commands = [
            QueueAddJobCommand,
            QueueStartJobCommand,
            QueueStopJobCommand,
            QueueDeleteJobCommand,
            QueueGetJobStatusCommand,
            QueueListJobsCommand,
            QueueHealthCommand,
        ]

        registered_count = 0
        for command_class in queue_commands:
            try:
                command_name = getattr(
                    command_class, "name", command_class.__name__.lower()
                )
                registry.register(command_class)
                registered_count += 1
                get_global_logger().debug(f"Auto-registered queue command: {command_name}")
            except Exception as e:
                get_global_logger().error(
                    f"Failed to register queue command {command_class.__name__}: {e}"
                )

        if registered_count > 0:
            get_global_logger().info(
                f"Auto-registered {registered_count} queue management commands"
            )
        
        return registered_count
    except Exception as e:
        get_global_logger().warning(
            f"Failed to auto-register queue commands (queue_manager may be disabled): {e}"
        )
        return 0

