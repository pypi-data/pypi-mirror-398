"""
OpenAPI schema validator for client requests.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Set


class OpenAPIValidator:
    """
    Validator for command requests based on OpenAPI schema.
    
    This validator uses the CommandRequest schema with oneOf discriminator
    to validate command requests before sending them to the server.
    """

    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize validator with OpenAPI schema.
        
        Args:
            schema: OpenAPI schema dictionary
        """
        self.schema = schema
        self._command_schemas: Dict[str, Dict[str, Any]] = {}
        self._load_command_schemas()

    def _load_command_schemas(self) -> None:
        """Load command schemas from OpenAPI schema."""
        components = self.schema.get("components", {})
        schemas = components.get("schemas", {})
        
        # Get CommandRequest schema
        cmd_request = schemas.get("CommandRequest", {})
        discriminator = cmd_request.get("discriminator", {})
        mapping = discriminator.get("mapping", {})
        
        # Load each command schema
        for cmd_name, schema_ref in mapping.items():
            # Extract schema name from reference
            schema_name = schema_ref.split("/")[-1]
            if schema_name in schemas:
                self._command_schemas[cmd_name] = schemas[schema_name]

    def validate_command_request(
        self, command: str, params: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate command request against OpenAPI schema.
        
        Args:
            command: Command name
            params: Command parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if command not in self._command_schemas:
            return False, f"Command '{command}' not found in schema"
        
        cmd_schema = self._command_schemas[command]
        properties = cmd_schema.get("properties", {})
        required = cmd_schema.get("required", [])
        
        # Check required fields
        if "command" not in required:
            return False, "Command field is required"
        
        # Validate params if provided
        if params is not None:
            params_schema = properties.get("params", {})
            if params_schema:
                params_properties = params_schema.get("properties", {})
                params_required = params_schema.get("required", [])
                
                # Check required params
                for param_name in params_required:
                    if param_name not in params:
                        return False, f"Required parameter '{param_name}' is missing"
                
                # Validate param types (basic validation)
                for param_name, param_value in params.items():
                    if param_name in params_properties:
                        param_schema = params_properties[param_name]
                        param_type = param_schema.get("type")
                        
                        if param_type == "string" and not isinstance(param_value, str):
                            return False, f"Parameter '{param_name}' must be a string"
                        elif param_type == "integer" and not isinstance(param_value, int):
                            return False, f"Parameter '{param_name}' must be an integer"
                        elif param_type == "number" and not isinstance(param_value, (int, float)):
                            return False, f"Parameter '{param_name}' must be a number"
                        elif param_type == "boolean" and not isinstance(param_value, bool):
                            return False, f"Parameter '{param_name}' must be a boolean"
        
        return True, None

    def get_command_schema(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Get OpenAPI schema for a specific command.
        
        Args:
            command: Command name
            
        Returns:
            Command schema or None if not found
        """
        return self._command_schemas.get(command)

    def list_commands(self) -> Set[str]:
        """
        Get list of available commands from schema.
        
        Returns:
            Set of command names
        """
        return set(self._command_schemas.keys())

