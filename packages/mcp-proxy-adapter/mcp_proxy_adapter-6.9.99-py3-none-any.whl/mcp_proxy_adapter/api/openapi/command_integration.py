"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Command integration utilities for OpenAPI generation.
"""

from typing import Dict, Any, Type

from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.core.logging import get_global_logger


class CommandIntegrator:
    """Integrator for adding commands to OpenAPI schema."""

    def __init__(self):
        """Initialize command integrator."""
        self.logger = get_global_logger()


    def _create_params_schema(self, cmd_class: Type[Command]) -> Dict[str, Any]:
        """
        Create a schema for command parameters.

        Args:
            cmd_class: The command class to create schema for.

        Returns:
            Dict containing the parameter schema.
        """
        try:
            # Get the command schema
            schema = cmd_class.get_schema()
            
            if not schema or "properties" not in schema:
                return {"type": "object", "properties": {}}

            # Convert to OpenAPI format
            openapi_schema = {
                "type": "object",
                "properties": {},
                "required": schema.get("required", [])
            }

            # Convert properties
            for prop_name, prop_schema in schema["properties"].items():
                openapi_schema["properties"][prop_name] = self._convert_property_schema(prop_schema)

            return openapi_schema

        except Exception as e:
            self.logger.warning(f"Failed to create params schema for {cmd_class.__name__}: {e}")
            return {"type": "object", "properties": {}}

    def _convert_property_schema(self, prop_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert property schema to OpenAPI format.

        Args:
            prop_schema: Property schema to convert.

        Returns:
            OpenAPI property schema.
        """
        openapi_prop = {}

        # Handle type
        if "type" in prop_schema:
            openapi_prop["type"] = prop_schema["type"]

        # Handle description
        if "description" in prop_schema:
            openapi_prop["description"] = prop_schema["description"]

        # Handle default
        if "default" in prop_schema:
            openapi_prop["default"] = prop_schema["default"]

        # Handle enum
        if "enum" in prop_schema:
            openapi_prop["enum"] = prop_schema["enum"]

        # Handle minimum/maximum
        if "minimum" in prop_schema:
            openapi_prop["minimum"] = prop_schema["minimum"]
        if "maximum" in prop_schema:
            openapi_prop["maximum"] = prop_schema["maximum"]

        # Handle minLength/maxLength
        if "minLength" in prop_schema:
            openapi_prop["minLength"] = prop_schema["minLength"]
        if "maxLength" in prop_schema:
            openapi_prop["maxLength"] = prop_schema["maxLength"]

        # Handle pattern
        if "pattern" in prop_schema:
            openapi_prop["pattern"] = prop_schema["pattern"]

        # Handle items for arrays
        if "items" in prop_schema:
            openapi_prop["items"] = self._convert_property_schema(prop_schema["items"])

        return openapi_prop
