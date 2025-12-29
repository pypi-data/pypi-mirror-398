"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Main command registry for MCP Proxy Adapter.
"""


from typing import Dict, List, Type, Union, Any, Optional

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.core.logging import get_global_logger
# from .command_loader import CommandLoader
# from .command_manager import CommandManager
# from .command_info import CommandInfo


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
        # self._loader = CommandLoader()
        self._loader = None
        # self._manager = CommandManager()
        # self._info = CommandInfo()
        self._manager = None
        self._info = None
        
        # Register built-in echo command
        self._register_echo_command()
        self._register_long_task_commands()

    def _register_echo_command(self) -> None:
        """Register built-in echo command."""
        from mcp_proxy_adapter.commands.base import Command, CommandResult
        
        class EchoCommand(Command):
            """
            Built-in echo command for testing purposes.
            Returns the provided message.
            """
            name = "echo"
            descr = "Echo command for testing"
            
            async def execute(self, message: str = "Hello", **kwargs) -> CommandResult:
                """
                Execute echo command.

                Args:
                    message: Message to echo
                    **kwargs: Additional parameters

                Returns:
                    CommandResult with echoed message
                """
                return CommandResult(success=True, data={"message": message})
            
            @classmethod
            def get_schema(cls) -> Dict[str, Any]:
                """
                Get JSON schema for echo command parameters.
                
                Returns:
                    Dictionary with JSON schema
                """
                return {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "default": "Hello"}
                    }
                }
        
        self._commands["echo"] = EchoCommand
        self._command_types["echo"] = "builtin"

    def _register_long_task_commands(self) -> None:
        """Register demo long-running task commands (enqueue/status)."""
        from mcp_proxy_adapter.commands.base import Command, CommandResult
        from mcp_proxy_adapter.core.job_manager import enqueue_coroutine, get_job_status
        import asyncio

        class LongTaskCommand(Command):
            """
            Built-in command for enqueueing long-running tasks.
            Creates a background job that sleeps for the specified duration.
            """
            name = "long_task"
            descr = "Enqueue a long-running task that sleeps for given seconds"

            async def execute(self, seconds: float = 5.0, **kwargs) -> CommandResult:
                """
                Execute long task command.

                Args:
                    seconds: Number of seconds to sleep
                    **kwargs: Additional parameters

                Returns:
                    CommandResult with job ID
                """
                async def _work():
                    """Internal work function for long task."""
                    await asyncio.sleep(max(0.0, float(seconds)))
                    return {"slept": float(seconds)}

                job_id = enqueue_coroutine(_work())
                return CommandResult(success=True, data={"job_id": job_id, "status": "queued"})

            @classmethod
            def get_schema(cls) -> Dict[str, Any]:
                """
                Get JSON schema for long_task command parameters.
                
                Returns:
                    Dictionary with JSON schema
                """
                return {
                    "type": "object",
                    "properties": {"seconds": {"type": "number", "default": 5.0}},
                    "description": "Start a demo long-running job"
                }

        class JobStatusCommand(Command):
            """
            Built-in command for checking job status.
            Returns the current status and result of a previously enqueued job.
            """
            name = "job_status"
            descr = "Get status of a previously enqueued job"

            async def execute(self, job_id: str, **kwargs) -> CommandResult:
                """
                Execute job status command.

                Args:
                    job_id: Job ID to check status for
                    **kwargs: Additional parameters

                Returns:
                    CommandResult with job status
                """
                status = get_job_status(job_id)
                return CommandResult(success=True, data=status)

            @classmethod
            def get_schema(cls) -> Dict[str, Any]:
                """
                Get JSON schema for job_status command parameters.
                
                Returns:
                    Dictionary with JSON schema
                """
                return {
                    "type": "object",
                    "properties": {"job_id": {"type": "string"}},
                    "required": ["job_id"],
                    "description": "Check job status"
                }

        self._commands["long_task"] = LongTaskCommand
        self._command_types["long_task"] = "builtin"
        self._commands["job_status"] = JobStatusCommand
        self._command_types["job_status"] = "builtin"


    def register_loaded(self, command: Union[Type[Command], Command]) -> None:
        """
        Register a loaded command.

        Args:
            command: Command class or instance to register
        """
        self._register_command(command, "loaded")

    def _get_command_name(self, command: Union[Type[Command], Command]) -> str:
        """Get command name from class or instance."""
        if isinstance(command, Command):
            command = command.__class__
        return getattr(command, "name", command.__name__.lower())

    def register(self, command: Union[Type[Command], Command], cmd_type: str = "builtin") -> None:
        """
        Register a command (alias for _register_command for backward compatibility).

        Args:
            command: Command class or instance to register
            cmd_type: Type of command ("builtin", "custom", "loaded")
        """
        self._register_command(command, cmd_type)

    def _register_command(self, command: Union[Type[Command], Command], cmd_type: str) -> None:
        """
        Register a command.

        Args:
            command: Command class or instance to register
            cmd_type: Type of command ("builtin", "custom", "loaded")
        """
        command_name = self._get_command_name(command)
        
        if isinstance(command, Command):
            # Register instance
            self._instances[command_name] = command
            self._commands[command_name] = command.__class__
        else:
            # Register class
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
        if command_name not in self._commands:
            raise KeyError(f"Command '{command_name}' not found")
        return self._commands[command_name]

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
        return self._commands

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

    async def reload_system(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Reload system configuration and commands.

        Args:
            config_path: Optional path to configuration file to reload

        Returns:
            Dictionary with reload information
        """
        result: Dict[str, Any] = {
            "config_reloaded": False,
            "builtin_commands": 0,
            "custom_commands": 0,
            "loaded_commands": 0,
            "remote_commands": 0,
            "total_commands": 0,
        }

        try:
            # Reload config if path provided
            if config_path:
                from mcp_proxy_adapter.config import get_config
                try:
                    config = get_config()
                    config.config_path = config_path
                    config.load_config()
                    result["config_reloaded"] = True
                    self.logger.info(f"✅ Configuration reloaded from: {config_path}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to reload config: {e}")
                    result["config_error"] = str(e)

            # Count current commands by type
            for cmd_name, cmd_type in self._command_types.items():
                if cmd_type == "builtin":
                    result["builtin_commands"] += 1
                elif cmd_type == "custom":
                    result["custom_commands"] += 1
                elif cmd_type == "loaded":
                    result["loaded_commands"] += 1
                else:
                    result["remote_commands"] += 1

            result["total_commands"] = len(self._commands)

            self.logger.info(
                f"✅ System reload completed: {result['total_commands']} commands "
                f"(builtin: {result['builtin_commands']}, "
                f"custom: {result['custom_commands']}, "
                f"loaded: {result['loaded_commands']})"
            )

        except Exception as e:
            self.logger.error(f"❌ System reload failed: {e}")
            result["error"] = str(e)

        return result

    def get_all_commands_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about all commands.

        Returns:
            Dictionary with command information
        """
        if self._info is None:
            # Simple implementation when CommandInfo is not available
            commands_info = {}
            for name, command_class in self._commands.items():
                try:
                    schema = command_class.get_schema() if hasattr(command_class, "get_schema") else {}
                    descr = getattr(command_class, "descr", "")
                    commands_info[name] = {
                        "metadata": {
                            "name": name,
                            "summary": descr,
                            "type": self._command_types.get(name, "unknown"),
                        },
                        "schema": schema,
                    }
                except Exception as e:
                    self.logger.warning(f"Error getting info for command {name}: {e}")
                    continue
            return {"commands": commands_info}
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
        
        if self._info is None:
            # Simple implementation when CommandInfo is not available
            command_class = self._commands[command_name]
            try:
                schema = command_class.get_schema() if hasattr(command_class, "get_schema") else {}
                descr = getattr(command_class, "descr", "")
                return {
                    "metadata": {
                        "name": command_name,
                        "summary": descr,
                        "type": self._command_types.get(command_name, "unknown"),
                    },
                    "schema": schema,
                }
            except Exception as e:
                self.logger.warning(f"Error getting info for command {command_name}: {e}")
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
