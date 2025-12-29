"""
Client exceptions for JSON-RPC client and schema generator.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations


class ClientError(Exception):
    """Base exception for all client errors."""
    pass


class SchemaGeneratorError(ClientError):
    """Base exception for schema generator errors."""
    pass


class MethodNotFoundError(SchemaGeneratorError):
    """Raised when a method is not found in the schema."""
    
    def __init__(self, method_name: str):
        """
        Initialize method not found error.
        
        Args:
            method_name: Name of the method that was not found
        """
        self.method_name = method_name
        super().__init__(f"Method '{method_name}' not found in schema")


class RequiredParameterMissingError(SchemaGeneratorError):
    """Raised when a required parameter is missing."""
    
    def __init__(self, method_name: str, parameter_name: str):
        """
        Initialize required parameter missing error.
        
        Args:
            method_name: Name of the method
            parameter_name: Name of the missing parameter
        """
        self.method_name = method_name
        self.parameter_name = parameter_name
        super().__init__(
            f"Required parameter '{parameter_name}' is missing for method '{method_name}'"
        )


class InvalidParameterTypeError(SchemaGeneratorError):
    """Raised when a parameter has an invalid type."""
    
    def __init__(self, method_name: str, parameter_name: str, expected_type: str, actual_type: str):
        """
        Initialize invalid parameter type error.
        
        Args:
            method_name: Name of the method
            parameter_name: Name of the parameter with invalid type
            expected_type: Expected parameter type
            actual_type: Actual parameter type
        """
        self.method_name = method_name
        self.parameter_name = parameter_name
        self.expected_type = expected_type
        self.actual_type = actual_type
        super().__init__(
            f"Invalid type for parameter '{parameter_name}' in method '{method_name}': "
            f"expected {expected_type}, got {actual_type}"
        )


class InvalidParameterValueError(SchemaGeneratorError):
    """Raised when a parameter has an invalid value."""
    
    def __init__(self, method_name: str, parameter_name: str, reason: str):
        """
        Initialize invalid parameter value error.
        
        Args:
            method_name: Name of the method
            parameter_name: Name of the parameter with invalid value
            reason: Reason why the value is invalid
        """
        self.method_name = method_name
        self.parameter_name = parameter_name
        self.reason = reason
        super().__init__(
            f"Invalid value for parameter '{parameter_name}' in method '{method_name}': {reason}"
        )


class ClientConnectionError(ClientError):
    """Raised when client cannot connect to server."""
    
    def __init__(self, message: str, url: str = None):
        """
        Initialize client connection error.
        
        Args:
            message: Error message
            url: Optional URL that failed to connect
        """
        self.url = url
        super().__init__(message)


class ClientRequestError(ClientError):
    """Raised when client request fails."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        """
        Initialize client request error.
        
        Args:
            message: Error message
            status_code: Optional HTTP status code
            response: Optional response dictionary
        """
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class SchemaValidationError(ClientError):
    """Raised when schema validation fails."""
    
    def __init__(self, message: str, validation_details: dict = None):
        """
        Initialize schema validation error.
        
        Args:
            message: Error message
            validation_details: Optional validation details dictionary
        """
        self.validation_details = validation_details
        super().__init__(message)


