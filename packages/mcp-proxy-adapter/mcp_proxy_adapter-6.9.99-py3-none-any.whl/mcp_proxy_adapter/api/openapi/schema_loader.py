"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Schema loading utilities for OpenAPI generation.
"""

import json
from pathlib import Path
from typing import Dict, Any

from mcp_proxy_adapter.core.logging import get_global_logger


class SchemaLoader:
    """Loader for OpenAPI base schemas."""

    def __init__(self):
        """Initialize schema loader."""
        self.logger = get_global_logger()
        self.base_schema_path = (
            Path(__file__).parent.parent.parent / "schemas" / "openapi_schema.json"
        )


    def get_fallback_schema(self) -> Dict[str, Any]:
        """
        Get a fallback OpenAPI schema when the base schema file is not available.

        Returns:
            Dict containing a basic OpenAPI schema.
        """
        return {
            "openapi": "3.0.2",
            "info": {
                "title": "MCP Microservice API",
                "description": "API для выполнения команд микросервиса",
                "version": "1.0.0"
            },
            "paths": {
                "/cmd": {
                    "post": {
                        "summary": "Execute Command",
                        "description": "Executes a command via JSON-RPC protocol.",
                        "operationId": "execute_command",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "oneOf": [
                                            { "$ref": "#/components/schemas/CommandRequest" },
                                            { "$ref": "#/components/schemas/JsonRpcRequest" }
                                        ]
                                    }
                                }
                            },
                            "required": True
                        },
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "oneOf": [
                                                { "$ref": "#/components/schemas/CommandResponse" },
                                                { "$ref": "#/components/schemas/JsonRpcResponse" }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "CommandRequest": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "params": {"type": "object"}
                        },
                        "required": ["command"]
                    },
                    "CommandResponse": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "data": {"type": "object"},
                            "error": {"type": "string"}
                        }
                    },
                    "JsonRpcRequest": {
                        "type": "object",
                        "properties": {
                            "jsonrpc": {"type": "string", "enum": ["2.0"]},
                            "method": {"type": "string"},
                            "params": {"type": "object"},
                            "id": {"type": "string"}
                        },
                        "required": ["jsonrpc", "method", "id"]
                    },
                    "JsonRpcResponse": {
                        "type": "object",
                        "properties": {
                            "jsonrpc": {"type": "string", "enum": ["2.0"]},
                            "result": {"type": "object"},
                            "error": {"type": "object"},
                            "id": {"type": "string"}
                        }
                    }
                }
            }
        }
