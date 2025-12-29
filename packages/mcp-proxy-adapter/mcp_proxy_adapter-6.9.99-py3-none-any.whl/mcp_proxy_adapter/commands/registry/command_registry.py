"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Main command registry for MCP Proxy Adapter.
"""


from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.core.logging import get_global_logger
from .command_loader import CommandLoader
from .command_manager import CommandManager
from .command_info import CommandInfo


class CommandRegistry:
    """
    Registry for registering and finding commands.

    Supports three types of commands:
    - Builtin: Core commands that come with the framework
    - Custom: User-defined commands
    - Loaded: Commands loaded from external sources
    """

    def __init__(self):
        """Initialize command registry."""
        self.logger = get_global_logger()
        
        # Command storage
        self._commands: Dict[str, Type[Command]] = {}
        self._instances: Dict[str, Command] = {}
        self._command_types: Dict[str, str] = {}  # "builtin", "custom", "loaded"
        
        # Initialize components
        self._loader = CommandLoader()
        self._manager = CommandManager()
        self._info = CommandInfo()



    def register_loaded(self, command: Union[Type[Command], Command]) -> None:
        """
        Register a loaded command.

        Args:
            command: Command class or instance to register
        """
        self._register_command(command, "loaded")

    def _register_command(self, command: Union[Type[Command], Command], cmd_type: str) -> None:
        """
        Register a command.

        Args:
            command: Command class or instance to register
            cmd_type: Type of command ("builtin", "custom", "loaded")
        """
        if isinstance(command, Command):
            # Register instance
            command_name = self._manager._get_command_name(command.__class__)
            self._instances[command_name] = command
            self._commands[command_name] = command.__class__
        else:
            # Register class
            command_name = self._manager._get_command_name(command)
            self._commands[command_name] = command
        
        self._command_types[command_name] = cmd_type
        self.logger.info(f"Registered {cmd_type} command: {command_name}")

    def load_command_from_source(self, source: str) -> Dict[str, Any]:
        """
        Load command from source.

        Args:
            source: Source string - local path, URL, or command name from registry

        Returns:
            Dictionary with loading result information
        """
        result = self._loader.load_command_from_source(source)
        
        if result["success"]:
            # Register loaded commands
            for command_class in result["commands"]:
                self.register_loaded(command_class)
        
        return result


    def command_exists(self, command_name: str) -> bool:
        """
        Check if command exists.

        Args:
            command_name: Name of the command

        Returns:
            True if command exists, False otherwise
        """
        return self._manager.command_exists(command_name, self._commands)

    def get_command(self, command_name: str) -> Type[Command]:
        """
        Get command class by name.

        Args:
            command_name: Name of the command

        Returns:
            Command class

        Raises:
            NotFoundError: If command not found
        """
        return self._manager.get_command(command_name, self._commands)

    def get_command_instance(self, command_name: str) -> Command:
        """
        Get command instance by name.

        Args:
            command_name: Name of the command

        Returns:
            Command instance

        Raises:
            NotFoundError: If command not found
        """
        return self._manager.get_command_instance(command_name, self._commands, self._instances)

    def has_instance(self, command_name: str) -> bool:
        """
        Check if command has instance.

        Args:
            command_name: Name of the command

        Returns:
            True if command has instance, False otherwise
        """
        return self._manager.has_instance(command_name, self._instances)

    def get_all_commands(self) -> Dict[str, Type[Command]]:
        """
        Get all registered commands.

        Returns:
            Dictionary of all commands
        """
        return self._manager.get_all_commands(self._commands)

    def get_commands_by_type(self) -> Dict[str, Dict[str, Type[Command]]]:
        """
        Get commands grouped by type.

        Returns:
            Dictionary of commands grouped by type
        """
        return self._manager.get_commands_by_type(self._commands, self._command_types)

    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata for all commands.

        Returns:
            Dictionary of command metadata
        """
        return self._manager.get_all_metadata(self._commands, self._command_types)

    def clear(self) -> None:
        """Clear all commands and instances."""
        self._manager.clear(self._commands, self._instances, self._command_types)
        self.logger.info("Cleared all commands")

    def get_all_commands_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about all commands.

        Returns:
            Dictionary with command information
        """
        return self._info.get_all_commands_info(self._commands, self._command_types)

    def get_command_info(self, command_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific command.

        Args:
            command_name: Name of the command

        Returns:
            Dictionary with command information or None if not found
        """
        if command_name not in self._commands:
            return None
        
        return self._info.get_command_info(
            command_name, 
            self._commands[command_name], 
            self._command_types
        )

    def _load_all_commands(self) -> Dict[str, int]:
        """
        Load all commands from configured directories.

        Returns:
            Dictionary with loading statistics
        """
        return self._manager._load_all_commands(self._commands, self._command_types)


# Global registry instance
registry = CommandRegistry()
