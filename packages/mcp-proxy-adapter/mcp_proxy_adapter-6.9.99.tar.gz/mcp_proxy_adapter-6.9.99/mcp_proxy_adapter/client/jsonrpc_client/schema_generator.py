"""
OpenAPI schema-based request generator for client.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
from dataclasses import dataclass, field
from enum import Enum

from .exceptions import (
    SchemaGeneratorError,
    MethodNotFoundError,
    RequiredParameterMissingError,
    InvalidParameterTypeError,
    InvalidParameterValueError,
)


class ParameterType(Enum):
    """Parameter type enumeration."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"


@dataclass
class ParameterInfo:
    """Information about a command parameter."""
    name: str
    param_type: ParameterType
    description: Optional[str] = None
    default_value: Optional[Any] = None
    required: bool = False
    enum_values: Optional[List[Any]] = None
    format: Optional[str] = None  # e.g., "int64", "float", "date-time"
    items_type: Optional[ParameterType] = None  # For array types
    properties: Optional[Dict[str, "ParameterInfo"]] = None  # For object types


@dataclass
class MethodInfo:
    """Information about a command method."""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, ParameterInfo] = field(default_factory=dict)
    return_type: Optional[str] = None
    return_description: Optional[str] = None


class SchemaRequestGenerator:
    """
    Generator for creating typed method calls based on OpenAPI schema.
    
    This class parses the OpenAPI schema and generates method information
    that can be used to execute commands with proper validation.
    """

    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize generator with OpenAPI schema.
        
        Args:
            schema: OpenAPI schema dictionary
        """
        self.schema = schema
        self._methods: Dict[str, MethodInfo] = {}
        self._load_methods()

    def _load_methods(self) -> None:
        """Load method information from OpenAPI schema."""
        components = self.schema.get("components", {})
        schemas = components.get("schemas", {})
        
        # Get CommandRequest schema
        cmd_request = schemas.get("CommandRequest", {})
        discriminator = cmd_request.get("discriminator", {})
        mapping = discriminator.get("mapping", {})
        
        # Load each command schema
        for cmd_name, schema_ref in mapping.items():
            schema_name = schema_ref.split("/")[-1]
            if schema_name in schemas:
                cmd_schema = schemas[schema_name]
                method_info = self._parse_command_schema(cmd_name, cmd_schema)
                self._methods[cmd_name] = method_info

    def _parse_command_schema(self, command_name: str, schema: Dict[str, Any]) -> MethodInfo:
        """
        Parse command schema into MethodInfo.
        
        Args:
            command_name: Name of the command
            schema: Command schema dictionary
            
        Returns:
            MethodInfo object
        """
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Get description from schema or use default
        description = schema.get("description") or f"Execute {command_name} command"
        
        # Parse params schema
        params_schema = properties.get("params", {})
        params_properties = params_schema.get("properties", {})
        params_required = params_schema.get("required", [])
        
        parameters: Dict[str, ParameterInfo] = {}
        
        for param_name, param_schema in params_properties.items():
            param_info = self._parse_parameter_schema(
                param_name, param_schema, param_name in params_required
            )
            parameters[param_name] = param_info
        
        return MethodInfo(
            name=command_name,
            description=description,
            parameters=parameters,
            return_type="Dict[str, Any]",
            return_description="Command execution result"
        )

    def _parse_parameter_schema(
        self, param_name: str, param_schema: Dict[str, Any], required: bool
    ) -> ParameterInfo:
        """
        Parse parameter schema into ParameterInfo.
        
        Args:
            param_name: Parameter name
            param_schema: Parameter schema dictionary
            required: Whether parameter is required
            
        Returns:
            ParameterInfo object
        """
        param_type_str = param_schema.get("type", "object")
        param_type = self._map_type(param_type_str)
        
        # Handle array types
        items_type = None
        if param_type == ParameterType.ARRAY:
            items = param_schema.get("items", {})
            items_type_str = items.get("type", "object")
            items_type = self._map_type(items_type_str)
        
        # Handle object types with properties
        properties = None
        if param_type == ParameterType.OBJECT:
            obj_properties = param_schema.get("properties", {})
            if obj_properties:
                properties = {}
                obj_required = param_schema.get("required", [])
                for prop_name, prop_schema in obj_properties.items():
                    properties[prop_name] = self._parse_parameter_schema(
                        prop_name, prop_schema, prop_name in obj_required
                    )
        
        return ParameterInfo(
            name=param_name,
            param_type=param_type,
            description=param_schema.get("description"),
            default_value=param_schema.get("default"),
            required=required,
            enum_values=param_schema.get("enum"),
            format=param_schema.get("format"),
            items_type=items_type,
            properties=properties
        )

    def _map_type(self, type_str: str) -> ParameterType:
        """
        Map OpenAPI type string to ParameterType enum.
        
        Args:
            type_str: OpenAPI type string
            
        Returns:
            ParameterType enum value
        """
        type_mapping = {
            "string": ParameterType.STRING,
            "integer": ParameterType.INTEGER,
            "number": ParameterType.NUMBER,
            "boolean": ParameterType.BOOLEAN,
            "array": ParameterType.ARRAY,
            "object": ParameterType.OBJECT,
            "null": ParameterType.NULL,
        }
        return type_mapping.get(type_str, ParameterType.OBJECT)

    def get_methods(self) -> Dict[str, MethodInfo]:
        """
        Get all available methods.
        
        Returns:
            Dictionary mapping method names to MethodInfo objects
        """
        return self._methods.copy()

    def get_method_info(self, method_name: str) -> MethodInfo:
        """
        Get information about a specific method.
        
        Args:
            method_name: Name of the method
            
        Returns:
            MethodInfo object
            
        Raises:
            MethodNotFoundError: If method is not found
        """
        if method_name not in self._methods:
            raise MethodNotFoundError(method_name)
        return self._methods[method_name]

    def validate_and_prepare_params(
        self, method_name: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate and prepare parameters for method execution.
        
        This method:
        - Checks for required parameters
        - Sets default values for missing optional parameters
        - Validates parameter types
        - Validates enum values
        
        Args:
            method_name: Name of the method
            params: Provided parameters
            
        Returns:
            Validated and prepared parameters dictionary
            
        Raises:
            MethodNotFoundError: If method is not found
            RequiredParameterMissingError: If required parameter is missing
            InvalidParameterTypeError: If parameter type is invalid
            InvalidParameterValueError: If parameter value is invalid
        """
        if method_name not in self._methods:
            raise MethodNotFoundError(method_name)
        
        method_info = self._methods[method_name]
        params = params or {}
        prepared_params: Dict[str, Any] = {}
        
        # Check required parameters
        for param_name, param_info in method_info.parameters.items():
            if param_info.required and param_name not in params:
                raise RequiredParameterMissingError(method_name, param_name)
        
        # Process all parameters (provided and defaults)
        all_param_names = set(method_info.parameters.keys()) | set(params.keys())
        
        for param_name in all_param_names:
            param_info = method_info.parameters.get(param_name)
            
            # Use provided value or default
            if param_name in params:
                value = params[param_name]
            elif param_info and param_info.default_value is not None:
                value = param_info.default_value
            else:
                continue  # Skip if not provided and no default
            
            # Validate type
            if param_info:
                self._validate_parameter_type(
                    method_name, param_name, value, param_info
                )
            
            prepared_params[param_name] = value
        
        return prepared_params

    def _validate_parameter_type(
        self, method_name: str, param_name: str, value: Any, param_info: ParameterInfo
    ) -> None:
        """
        Validate parameter type and value.
        
        Args:
            method_name: Name of the method
            param_name: Name of the parameter
            value: Parameter value
            param_info: Parameter information
            
        Raises:
            InvalidParameterTypeError: If type is invalid
            InvalidParameterValueError: If value is invalid
        """
        # Check enum values
        if param_info.enum_values and value not in param_info.enum_values:
            raise InvalidParameterValueError(
                method_name, param_name,
                f"Value must be one of: {param_info.enum_values}"
            )
        
        # Validate type
        expected_type = param_info.param_type
        actual_type = self._get_value_type(value)
        
        if expected_type == ParameterType.STRING and not isinstance(value, str):
            raise InvalidParameterTypeError(
                method_name, param_name, "string", actual_type
            )
        elif expected_type == ParameterType.INTEGER and not isinstance(value, int):
            raise InvalidParameterTypeError(
                method_name, param_name, "integer", actual_type
            )
        elif expected_type == ParameterType.NUMBER and not isinstance(value, (int, float)):
            raise InvalidParameterTypeError(
                method_name, param_name, "number", actual_type
            )
        elif expected_type == ParameterType.BOOLEAN and not isinstance(value, bool):
            raise InvalidParameterTypeError(
                method_name, param_name, "boolean", actual_type
            )
        elif expected_type == ParameterType.ARRAY and not isinstance(value, list):
            raise InvalidParameterTypeError(
                method_name, param_name, "array", actual_type
            )
        elif expected_type == ParameterType.OBJECT and not isinstance(value, dict):
            raise InvalidParameterTypeError(
                method_name, param_name, "object", actual_type
            )

    def _get_value_type(self, value: Any) -> str:
        """Get type name of a value."""
        # Check bool before int because bool is a subclass of int in Python
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        elif value is None:
            return "null"
        else:
            return type(value).__name__

    def get_method_description(self, method_name: str) -> str:
        """
        Get detailed description of a method.
        
        Args:
            method_name: Name of the method
            
        Returns:
            Detailed description string
            
        Raises:
            MethodNotFoundError: If method is not found
        """
        method_info = self.get_method_info(method_name)
        
        lines = [
            f"Method: {method_info.name}",
            f"Description: {method_info.description or 'No description available'}",
            f"Return Type: {method_info.return_type or 'Unknown'}",
            f"Return Description: {method_info.return_description or 'No description available'}",
            "",
            "Parameters:"
        ]
        
        if not method_info.parameters:
            lines.append("  No parameters")
        else:
            for param_name, param_info in method_info.parameters.items():
                required_mark = " (required)" if param_info.required else " (optional)"
                lines.append(f"  - {param_name}{required_mark}:")
                lines.append(f"    Type: {param_info.param_type.value}")
                if param_info.description:
                    lines.append(f"    Description: {param_info.description}")
                if param_info.default_value is not None:
                    lines.append(f"    Default: {json.dumps(param_info.default_value)}")
                if param_info.enum_values:
                    lines.append(f"    Allowed values: {param_info.enum_values}")
                if param_info.format:
                    lines.append(f"    Format: {param_info.format}")
        
        return "\n".join(lines)

    def schema_example(self) -> str:
        """
        Generate schema example with detailed descriptions.
        
        Returns:
            JSON string containing schema and detailed field descriptions
        """
        result = {
            "schema": self.schema,
            "description": {
                "standard": "OpenAPI 3.0.2",
                "standard_description": (
                    "OpenAPI Specification (OAS) defines a standard, language-agnostic interface "
                    "to RESTful APIs which allows both humans and computers to discover and understand "
                    "the capabilities of the service without access to source code, documentation, "
                    "or through network traffic inspection."
                ),
                "fields": {
                    "openapi": {
                        "description": "OpenAPI specification version",
                        "type": "string",
                        "example": "3.0.2"
                    },
                    "info": {
                        "description": "Metadata about the API",
                        "type": "object",
                        "fields": {
                            "title": "API title",
                            "version": "API version",
                            "description": "API description"
                        }
                    },
                    "paths": {
                        "description": "Available API endpoints",
                        "type": "object",
                        "note": "Each key is a path, each value contains HTTP methods"
                    },
                    "components": {
                        "description": "Reusable components (schemas, parameters, etc.)",
                        "type": "object",
                        "fields": {
                            "schemas": {
                                "description": "Data models and types",
                                "type": "object",
                                "note": "Contains CommandRequest with oneOf discriminator for command validation"
                            }
                        }
                    }
                }
            },
            "methods": {}
        }
        
        # Add method descriptions
        for method_name, method_info in self._methods.items():
            result["methods"][method_name] = {
                "name": method_info.name,
                "description": method_info.description,
                "return_type": method_info.return_type,
                "return_description": method_info.return_description,
                "parameters": {}
            }
            
            for param_name, param_info in method_info.parameters.items():
                result["methods"][method_name]["parameters"][param_name] = {
                    "name": param_info.name,
                    "type": param_info.param_type.value,
                    "description": param_info.description,
                    "required": param_info.required,
                    "default": param_info.default_value,
                    "enum": param_info.enum_values,
                    "format": param_info.format
                }
        
        return json.dumps(result, indent=2, ensure_ascii=False)

