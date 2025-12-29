"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Main OpenAPI generator for MCP Proxy Adapter.
"""

from typing import Any, Dict

from fastapi import FastAPI

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.commands.command_registry import registry
from .schema_loader import SchemaLoader
from .command_integration import CommandIntegrator


class CustomOpenAPIGenerator:
    """
    Custom OpenAPI schema generator for compatibility with MCP-Proxy.

    EN:
    This generator creates an OpenAPI schema that matches the format expected by MCP-Proxy,
    enabling dynamic command loading and proper tool representation in AI models.
    Allows overriding title, description, and version for schema customization.

    RU:
    Кастомный генератор схемы OpenAPI для совместимости с MCP-Proxy.
    Позволяет создавать схему OpenAPI в формате, ожидаемом MCP-Proxy,
    с возможностью динамической подгрузки команд и корректного отображения инструментов для AI-моделей.
    Поддерживает переопределение title, description и version для кастомизации схемы.
    """

    def __init__(self) -> None:
        """Initialize the generator."""
        self.logger = get_global_logger()
        self.schema_loader = SchemaLoader()
        self.command_integrator = CommandIntegrator()

    def generate(self, app: FastAPI) -> Dict[str, Any]:
        """
        Generate complete OpenAPI schema with command descriptions.

        Args:
            app: FastAPI application instance

        Returns:
            Complete OpenAPI schema dictionary
        """
        # Get base schema from FastAPI
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add /cmd endpoint with detailed command schemas
        self._add_cmd_endpoint(schema)
        self._add_cmd_models(schema)
        self._add_command_schemas(schema)
        self._add_cmd_examples(schema)

        return schema

    def _add_cmd_endpoint(self, schema: Dict[str, Any]) -> None:
        """
        Add /cmd endpoint to OpenAPI schema.

        Args:
            schema: OpenAPI schema to update
        """
        schema["paths"]["/cmd"] = {
            "post": {
                "summary": "Execute command",
                "description": "Universal endpoint for executing any command. Supports all registered commands with their specific parameters.",
                "operationId": "execute_command",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CommandRequest"}
                        }
                    },
                    "required": True,
                },
                "responses": {
                    "200": {
                        "description": "Command execution result",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "oneOf": [
                                        {
                                            "$ref": "#/components/schemas/CommandSuccessResponse"
                                        },
                                        {
                                            "$ref": "#/components/schemas/CommandErrorResponse"
                                        },
                                    ]
                                }
                            }
                        },
                    }
                },
            }
        }

    def _add_cmd_models(self, schema: Dict[str, Any]) -> None:
        """
        Add models for /cmd endpoint to OpenAPI schema.

        Args:
            schema: OpenAPI schema to update
        """
        # Ensure components/schemas exists
        if "components" not in schema:
            schema["components"] = {}
        if "schemas" not in schema["components"]:
            schema["components"]["schemas"] = {}

        # Add command request model with oneOf for all commands
        command_names = list(registry.get_all_commands().keys())
        self.logger.info(
            f"🔍 OpenAPI Generator: Found {len(command_names)} commands: {sorted(command_names)}"
        )
        command_one_of = []

        for cmd_name in command_names:
            try:
                cmd_class = registry.get_command(cmd_name)
                if cmd_class is None:
                    self.logger.warning(
                        f"⚠️ Command '{cmd_name}' not found in registry, skipping OpenAPI schema generation"
                    )
                    continue

                params_schema = self.command_integrator._create_params_schema(cmd_class)

                # Create schema name for this command
                schema_name = f"CommandRequest_{cmd_name}"
                schema["components"]["schemas"][schema_name] = {
                    "type": "object",
                    "required": ["command"],
                    "properties": {
                        "command": {
                            "type": "string",
                            "enum": [cmd_name],
                            "description": f"Command name: {cmd_name}",
                        },
                        "params": {
                            **params_schema,
                            "description": f"Parameters for {cmd_name} command",
                        },
                    },
                }
                command_one_of.append({"$ref": f"#/components/schemas/{schema_name}"})
            except Exception as e:
                self.logger.error(
                    f"❌ Failed to add command '{cmd_name}' to OpenAPI schema: {e}",
                    exc_info=True,
                )
                continue

        # Add main CommandRequest schema
        schema["components"]["schemas"]["CommandRequest"] = {
            "oneOf": (
                command_one_of
                if command_one_of
                else [
                    {
                        "type": "object",
                        "required": ["command"],
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Command name to execute",
                            },
                            "params": {
                                "type": "object",
                                "description": "Command parameters (specific to command)",
                                "additionalProperties": True,
                            },
                        },
                    }
                ]
            ),
            "discriminator": {
                "propertyName": "command",
                "mapping": {
                    cmd_name: f"#/components/schemas/CommandRequest_{cmd_name}"
                    for cmd_name in command_names
                },
            },
        }

        # Add command success response model
        schema["components"]["schemas"]["CommandSuccessResponse"] = {
            "type": "object",
            "required": ["result"],
            "properties": {
                "result": {
                    "type": "object",
                    "description": "Command execution result",
                    "additionalProperties": True,
                }
            },
        }

        # Add command error response model
        schema["components"]["schemas"]["CommandErrorResponse"] = {
            "type": "object",
            "required": ["error"],
            "properties": {
                "error": {
                    "type": "object",
                    "required": ["code", "message"],
                    "properties": {
                        "code": {"type": "integer", "description": "Error code"},
                        "message": {"type": "string", "description": "Error message"},
                        "data": {
                            "type": "object",
                            "description": "Additional error data",
                            "additionalProperties": True,
                        },
                    },
                }
            },
        }

    def _add_command_schemas(self, schema: Dict[str, Any]) -> None:
        """
        Add detailed schemas for each command with parameter descriptions.

        Args:
            schema: OpenAPI schema to update
        """
        if "components" not in schema:
            schema["components"] = {}
        if "schemas" not in schema["components"]:
            schema["components"]["schemas"] = {}

        for cmd_name, cmd_class in registry.get_all_commands().items():
            try:
                # Get command schema
                cmd_schema = cmd_class.get_schema()
                if not cmd_schema:
                    continue

                # Create detailed schema for this command
                params_schema = self.command_integrator._create_params_schema(cmd_class)

                # Add description from command class
                description = (
                    getattr(cmd_class, "descr", None)
                    or getattr(cmd_class, "__doc__", None)
                    or f"Execute {cmd_name} command"
                )

                # Store command schema with full description
                schema["components"]["schemas"][f"Command_{cmd_name}"] = {
                    "type": "object",
                    "description": description,
                    "properties": {
                        "command": {
                            "type": "string",
                            "enum": [cmd_name],
                            "description": f"Command name: {cmd_name}",
                        },
                        "params": {
                            **params_schema,
                            "description": f"Parameters for {cmd_name} command. See properties below for details.",
                        },
                    },
                    "required": ["command"] + params_schema.get("required", []),
                }
            except Exception as e:
                self.logger.warning(f"Failed to add schema for command {cmd_name}: {e}")

    def _add_cmd_examples(self, schema: Dict[str, Any]) -> None:
        """
        Add examples for /cmd endpoint to OpenAPI schema.

        Args:
            schema: OpenAPI schema to update
        """
        # Create examples section if it doesn't exist
        if "components" not in schema:
            schema["components"] = {}
        if "examples" not in schema["components"]:
            schema["components"]["examples"] = {}

        # Get first available command for example
        commands = list(registry.get_all_commands().keys())
        example_cmd = commands[0] if commands else "echo"

        # Add echo command example request
        schema["components"]["examples"]["echo_request"] = {
            "summary": f"Execute {example_cmd} command",
            "value": {
                "command": example_cmd,
                "params": {"message": "Hello from OpenAPI"},
            },
        }

        # Add echo command example response
        schema["components"]["examples"]["echo_response"] = {
            "summary": f"Response from {example_cmd} command",
            "value": {
                "result": {"success": True, "data": {"message": "Hello from OpenAPI"}}
            },
        }

        # Add error example
        schema["components"]["examples"]["command_error"] = {
            "summary": "Command not found error",
            "value": {
                "error": {
                    "code": -32601,
                    "message": "Command 'unknown_command' not found",
                }
            },
        }

        # Link examples to endpoint if it exists
        if "/cmd" in schema.get("paths", {}):
            cmd_path = schema["paths"]["/cmd"]["post"]
            if "requestBody" in cmd_path:
                cmd_path["requestBody"]["content"]["application/json"]["examples"] = {
                    "echo": {"$ref": "#/components/examples/echo_request"}
                }
            if "responses" in cmd_path and "200" in cmd_path["responses"]:
                cmd_path["responses"]["200"]["content"]["application/json"][
                    "examples"
                ] = {
                    "success": {"$ref": "#/components/examples/echo_response"},
                    "error": {"$ref": "#/components/examples/command_error"},
                }
