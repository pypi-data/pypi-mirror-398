"""
Module with help command implementation.
"""

from typing import Dict, Any, Optional
import logging
import traceback

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import CommandResult
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.core.errors import NotFoundError
from mcp_proxy_adapter.core.logging import get_global_logger

# Добавляем логирование
logger = logging.getLogger("mcp_proxy_adapter.commands.help_command")

# Global storage for app metadata
_app_metadata: Dict[str, str] = {
    "name": "MCP-Proxy API Service",
    "description": "JSON-RPC API for microservice command execution",
    "version": "1.0.0",
}


def set_app_metadata(name: str, description: str, version: str) -> None:
    """
    Set application metadata for help command.

    Args:
        name: Application name/title
        description: Application description
        version: Application version
    """
    global _app_metadata
    _app_metadata = {
        "name": name,
        "description": description,
        "version": version,
    }
    get_global_logger().debug(
        f"App metadata set: {name} v{version} - {description[:50]}..."
    )


def get_app_metadata() -> Dict[str, str]:
    """
    Get stored application metadata.

    Returns:
        Dictionary with app metadata (name, description, version)
    """
    return _app_metadata.copy()


class HelpResult(CommandResult):
    """
    Result of the help command execution.
    """

    def __init__(
        self,
        commands_info: Optional[Dict[str, Any]] = None,
        command_info: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize help command result.

        Args:
            commands_info: Information about all commands (for request without parameters)
            command_info: Information about a specific command (for request with cmdname parameter)
        """
        get_global_logger().debug(
            f"HelpResult.__init__: commands_info={commands_info is not None}, command_info={command_info is not None}"
        )
        self.commands_info = commands_info
        self.command_info = command_info

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary for serialization.

        Returns:
            Dictionary with result data.
        """
        result = {"success": True}
        if self.commands_info:
            result["data"] = self.commands_info
        elif self.command_info:
            result["data"] = self.command_info
        else:
            result["data"] = {}
        return result

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for help result."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "const": True},
                "data": {
                    "type": "object",
                    "properties": {
                        "tool_info": {"type": "object"},
                        "commands": {"type": "object"},
                        "help_usage": {"type": "object"},
                    }
                }
            }
        }


class HelpCommand(Command):
    """
    Command for getting help information about available commands.
    """

    name = "help"
    result_class = HelpResult

    async def execute(self, cmdname: Optional[str] = None, **kwargs) -> HelpResult:
        """
        Execute help command.

        Args:
            cmdname: Name of the command to get information about (optional)
            **kwargs: Any additional parameters (will be ignored)

        Returns:
            HelpResult: Help command result

        Raises:
            NotFoundError: If specified command not found
        """
        get_global_logger().debug(f"HelpCommand.execute начало: cmdname={cmdname}, kwargs={kwargs}")

        try:
            # Handle case when cmdname is provided
            if cmdname is not None and cmdname != "":
                get_global_logger().debug(f"Обработка запроса для конкретной команды: {cmdname}")
                try:
                    # Get command info from registry
                    command_info = registry.get_command_info(cmdname)
                    if command_info is None:
                        raise NotFoundError(f"Command '{cmdname}' not found")
                    get_global_logger().debug(f"Получены метаданные для команды {cmdname}")
                    return HelpResult(command_info=command_info)
                except NotFoundError:
                    get_global_logger().warning(f"Команда '{cmdname}' не найдена")
                    # Получаем список всех команд
                    all_commands = list(registry.get_all_commands().keys())
                    if all_commands:
                        example_cmd = all_commands[0]
                        example = {
                            "command": "help",
                            "params": {"cmdname": example_cmd},
                        }
                        note = f"Use help with an existing command name to get detailed info. For example: help with cmdname '{example_cmd}'. To list all commands: call help without parameters."
                    else:
                        example = {"command": "help"}
                        note = "No commands registered. To list all commands: call help without parameters."
                    return HelpResult(
                        commands_info={
                            "commands": {},
                            "error": f"Command '{cmdname}' not found",
                            "example": example,
                            "note": note,
                        }
                    )

            # Otherwise, return information about all available commands
            get_global_logger().debug("Обработка запроса для всех команд")

            # Get info for all commands
            all_commands_info = registry.get_all_commands_info()
            get_global_logger().debug(
                f"Получены метаданные для {len(all_commands_info.get('commands', {}))} команд"
            )

            # Get app metadata (set during app creation)
            app_metadata = get_app_metadata()

            # Prepare response format with tool metadata
            result = {
                "tool_info": {
                    "name": app_metadata["name"],
                    "description": app_metadata["description"],
                    "version": app_metadata["version"],
                },
                "help_usage": {
                    "description": "Get information about commands",
                    "examples": [
                        {
                            "command": "help",
                            "description": "List of all available commands",
                        },
                        {
                            "command": "help",
                            "params": {"cmdname": "command_name"},
                            "description": "Get detailed information about a specific command",
                        },
                    ],
                },
                "commands": {},
            }

            # Add full information about commands including schemas
            commands_data = all_commands_info.get("commands", {})
            for name, command_info in commands_data.items():
                try:
                    get_global_logger().debug(f"Обработка метаданных команды {name}")
                    # Безопасное получение параметров с проверкой на наличие ключей
                    metadata = command_info.get("metadata", {})
                    schema = command_info.get("schema", {})
                    result["commands"][name] = {
                        "name": name,
                        "description": metadata.get("summary", ""),
                        "type": metadata.get("type", "unknown"),
                        "schema": schema,
                        "params_count": len(schema.get("properties", {})),
                    }
                except Exception as e:
                    get_global_logger().error(f"Ошибка при обработке метаданных команды {name}: {e}")
                    get_global_logger().debug(f"Метаданные команды {name}: {command_info}")
                    # Пропускаем проблемную команду
                    continue

            get_global_logger().debug(
                f"HelpCommand.execute завершение: возвращаем результат с {len(result['commands'])} командами"
            )
            return HelpResult(commands_info=result)
        except Exception as e:
            get_global_logger().error(f"Неожиданная ошибка в HelpCommand.execute: {e}")
            get_global_logger().debug(f"Трассировка: {traceback.format_exc()}")
            # В случае неожиданной ошибки возвращаем пустой результат вместо ошибки
            return HelpResult(
                commands_info={
                    "tool_info": {
                        "name": "MCP-Proxy API Service",
                        "description": "JSON-RPC API for microservice command execution",
                        "version": "1.0.0",
                    },
                    "commands": {},
                    "error": str(e),
                }
            )
