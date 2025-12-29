"""
Модуль для интеграции метаданных команд с внешними API инструментами.

Этот модуль обеспечивает преобразование метаданных команд микросервиса 
в форматы, понятные для внешних систем, таких как OpenAPI, JSON-RPC,
и других API интерфейсов.
"""

import json
import logging
from typing import Any, Dict, Optional

from mcp_proxy_adapter.api.schemas import APIToolDescription
from mcp_proxy_adapter.commands.command_registry import CommandRegistry

from mcp_proxy_adapter.core.logging import get_global_logger
logger = logging.getLogger(__name__)


class ToolIntegration:
    """
    Класс для интеграции метаданных команд с внешними инструментами API.

    Обеспечивает генерацию описаний инструментов API для различных систем
    на основе метаданных команд микросервиса.
    """

    @classmethod
    def generate_tool_schema(
        cls,
        tool_name: str,
        registry: CommandRegistry,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Генерирует схему инструмента API для использования в OpenAPI и других системах.

        Args:
            tool_name: Имя инструмента API
            registry: Реестр команд
            description: Дополнительное описание инструмента (опционально)

        Returns:
            Словарь с описанием инструмента в формате OpenAPI
        """
        # Получаем базовое описание инструмента
        base_description = APIToolDescription.generate_tool_description(
            tool_name, registry
        )

        # Получаем типы параметров
        parameter_types = cls._extract_parameter_types(
            base_description["supported_commands"]
        )

        # Формируем схему инструмента
        schema = {
            "name": tool_name,
            "description": description or base_description["description"],
            "parameters": {
                "properties": {
                    "command": {
                        "description": "Команда для выполнения",
                        "type": "string",
                        "enum": list(base_description["supported_commands"].keys()),
                    },
                    "params": {
                        "description": "Параметры команды",
                        "type": "object",
                        "additionalProperties": True,
                        "properties": parameter_types,
                    },
                },
                "required": ["command"],
                "type": "object",
            },
        }

        return schema

    @classmethod

    @classmethod

    @classmethod
    def _extract_parameter_types(
        cls, commands: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Извлекает типы параметров из описания команд для формирования схемы.

        Args:
            commands: Словарь с описанием команд

        Returns:
            Словарь с типами параметров для схемы OpenAPI
        """
        parameter_types = {}

        # Формируем словарь типов для всех параметров всех команд
        for cmd_name, cmd_info in commands.items():
            params = cmd_info.get("params", {})
            if params is None:
                continue
            for param_name, param_info in params.items():
                param_type = param_info.get("type", "значение")

                # Преобразуем русские типы в типы JSON Schema
                if param_type == "строка":
                    json_type = "string"
                elif param_type == "целое число":
                    json_type = "integer"
                elif param_type == "число":
                    json_type = "number"
                elif param_type == "логическое значение":
                    json_type = "boolean"
                elif param_type == "список":
                    json_type = "array"
                elif param_type == "объект":
                    json_type = "object"
                else:
                    json_type = "string"

                # Добавляем тип в общий словарь
                parameter_types[param_name] = {
                    "type": json_type,
                    "description": param_info.get("description", ""),
                }

        return parameter_types


