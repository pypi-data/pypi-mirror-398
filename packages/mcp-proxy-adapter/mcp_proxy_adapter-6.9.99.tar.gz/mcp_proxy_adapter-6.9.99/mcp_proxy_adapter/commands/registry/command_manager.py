"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Command management utilities for MCP Proxy Adapter.
"""

import os

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.core.logging import get_global_logger


class CommandManager:
    """Manager for command operations."""

    def __init__(self):
        """Initialize command manager."""
        self.logger = get_global_logger()

    def _get_command_name(self, command_class: Type[Command]) -> str:
        """
        Get command name from command class.

        Args:
            command_class: Command class

        Returns:
            Command name
        """
        # Try to get name from class attribute
        if hasattr(command_class, "name") and command_class.name:
            return command_class.name

        # Fallback to class name
        class_name = command_class.__name__
        if class_name.endswith("Command"):
            return class_name[:-7].lower()  # Remove "Command" suffix
        return class_name.lower()


    def get_command(self, command_name: str, commands: Dict[str, Type[Command]]) -> Type[Command]:
        """
        Get command class by name.

        Args:
            command_name: Name of the command
            commands: Dictionary of registered commands

        Returns:
            Command class

        Raises:
            NotFoundError: If command not found
        """
        if command_name not in commands:
            from mcp_proxy_adapter.core.errors import NotFoundError
            raise NotFoundError(f"Command '{command_name}' not found")
        return commands[command_name]






    def clear(self, commands: Dict[str, Type[Command]], instances: Dict[str, Command], command_types: Dict[str, str]) -> None:
        """
        Clear all commands and instances.

        Args:
            commands: Dictionary of registered commands
            instances: Dictionary of command instances
            command_types: Dictionary mapping command names to types
        """
        commands.clear()
        instances.clear()
        command_types.clear()


    def _load_commands_from_directory(self, directory: str, commands: Dict[str, Type[Command]], command_types: Dict[str, str], cmd_type: str) -> int:
        """
        Load commands from directory.

        Args:
            directory: Directory to load commands from
            commands: Dictionary of registered commands
            command_types: Dictionary mapping command names to types
            cmd_type: Type of commands being loaded

        Returns:
            Number of commands loaded
        """
        loaded_count = 0
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith("_command.py"):
                        file_path = os.path.join(root, file)
                        try:
                            # Load command from file
                            from .command_loader import CommandLoader
                            loader = CommandLoader()
                            result = loader._load_command_from_file(file_path)
                            
                            if result["success"]:
                                for command_class in result["commands"]:
                                    command_name = self._get_command_name(command_class)
                                    commands[command_name] = command_class
                                    command_types[command_name] = cmd_type
                                    loaded_count += 1
                                    
                        except Exception as e:
                            self.logger.warning(f"Failed to load command from {file_path}: {e}")
                            
        except Exception as e:
            self.logger.error(f"Failed to load commands from directory {directory}: {e}")
            
        return loaded_count
