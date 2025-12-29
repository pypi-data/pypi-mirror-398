"""
Module for defining errors and exceptions for the microservice.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class MicroserviceError(Exception):
    """
    Base class for all microservice exceptions.

    Attributes:
        message: Error message.
        code: Error code.
        data: Additional error data.
    """

    def __init__(
        self, message: str, code: int = -32000, data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the error.

        Args:
            message: Error message.
            code: Error code according to JSON-RPC standard.
            data: Additional error data.
        """
        self.message = message
        self.code = code
        self.data = data or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        result = {"code": self.code, "message": self.message}
        if self.data:
            result["data"] = self.data
        return result


class ParseError(MicroserviceError):
    """
    Error while parsing JSON request.
    JSON-RPC Error code: -32700
    """

    def __init__(
        self, message: str = "Parse error", data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize parse error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32700, data=data)


class InvalidRequestError(MicroserviceError):
    """
    Invalid JSON-RPC request format.
    JSON-RPC Error code: -32600
    """

    def __init__(
        self, message: str = "Invalid Request", data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize invalid request error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32600, data=data)


class MethodNotFoundError(MicroserviceError):
    """
    Method not found error.
    JSON-RPC Error code: -32601
    """

    def __init__(
        self, message: str = "Method not found", data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize method not found error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32601, data=data)


class InvalidParamsError(MicroserviceError):
    """
    Invalid method parameters.
    JSON-RPC Error code: -32602
    """

    def __init__(
        self, message: str = "Invalid params", data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize invalid params error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32602, data=data)


class InternalError(MicroserviceError):
    """
    Internal server error.
    JSON-RPC Error code: -32603
    """

    def __init__(
        self, message: str = "Internal error", data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize internal error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32603, data=data)


class ValidationError(MicroserviceError):
    """
    Input data validation error.
    JSON-RPC Error code: -32602 (using Invalid params code)
    """

    def __init__(
        self, message: str = "Validation error", data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32602, data=data)


class CommandError(MicroserviceError):
    """
    Command execution error.
    JSON-RPC Error code: -32000 (server error)
    """

    def __init__(
        self,
        message: str = "Command execution error",
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize command execution error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32000, data=data)


class NotFoundError(MicroserviceError):
    """
    "Not found" error.
    JSON-RPC Error code: -32601 (using Method not found code)
    """

    def __init__(
        self, message: str = "Resource not found", data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize not found error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32601, data=data)


class ConfigurationError(MicroserviceError):
    """
    Configuration error.
    JSON-RPC Error code: -32603 (using Internal error code)
    """

    def __init__(
        self,
        message: str = "Configuration error",
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize configuration error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32603, data=data)


class AuthenticationError(MicroserviceError):
    """
    Authentication error.
    JSON-RPC Error code: -32001 (server error)
    """

    def __init__(
        self,
        message: str = "Authentication error",
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize authentication error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32001, data=data)


class AuthorizationError(MicroserviceError):
    """
    Authorization error.
    JSON-RPC Error code: -32002 (server error)
    """

    def __init__(
        self,
        message: str = "Authorization error",
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize authorization error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32002, data=data)


class TimeoutError(MicroserviceError):
    """
    Timeout error.
    JSON-RPC Error code: -32003 (server error)
    """

    def __init__(
        self, message: str = "Timeout error", data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize timeout error.

        Args:
            message: Error message
            data: Additional error data
        """
        super().__init__(message, code=-32003, data=data)


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    level: str  # "error", "warning", "info"
    message: str
    section: Optional[str] = None
    key: Optional[str] = None
    suggestion: Optional[str] = None


class ConfigError(MicroserviceError):
    """Configuration validation error."""

    def __init__(
        self, message: str, validation_results: Optional[List[ValidationResult]] = None
    ):
        """
        Initialize configuration error.

        Args:
            message: Error message
            validation_results: List of validation results that caused the error
        """
        super().__init__(message, code=-32001, data={"type": "configuration_error"})
        self.validation_results = validation_results or []

    def get_error_summary(self) -> str:
        """
        Build a human-readable summary of validation issues associated with this error.
        """
        if not self.validation_results:
            return self.message

        lines = []
        for result in self.validation_results:
            parts = [result.level.upper(), result.message]
            if result.section:
                parts.append(f"section={result.section}")
            if result.key:
                parts.append(f"key={result.key}")
            if result.suggestion:
                parts.append(f"suggestion={result.suggestion}")
            lines.append(" | ".join(parts))
        return "\n".join(lines)


class MissingConfigKeyError(ConfigError):
    """Missing required configuration key."""

    def __init__(self, key: str, section: str = None):
        """
        Initialize missing config key error.

        Args:
            key: Missing configuration key name
            section: Optional section name where key should be located
        """
        location = f"{section}.{key}" if section else key
        message = f"Required configuration key '{location}' is missing"
        super().__init__(message)
        self.key = key
        self.section = section


class InvalidConfigValueError(ConfigError):
    """Invalid configuration value."""

    def __init__(self, key: str, value: Any, expected_type: str, section: str = None):
        """
        Initialize invalid config value error.

        Args:
            key: Configuration key name
            value: Invalid value that was provided
            expected_type: Expected type name
            section: Optional section name where key is located
        """
        location = f"{section}.{key}" if section else key
        message = f"Invalid value for '{location}': got {type(value).__name__}, expected {expected_type}"
        super().__init__(message)
        self.key = key
        self.section = section
        self.value = value
        self.expected_type = expected_type


class MissingConfigSectionError(ConfigError):
    """Missing required configuration section."""

    def __init__(self, section: str):
        """
        Initialize missing config section error.

        Args:
            section: Missing configuration section name
        """
        message = f"Required configuration section '{section}' is missing"
        super().__init__(message)
        self.section = section


class MissingConfigFileError(ConfigError):
    """Missing configuration file."""

    def __init__(self, file_path: str):
        """
        Initialize missing config file error.

        Args:
            file_path: Path to the missing configuration file
        """
        message = f"Configuration file '{file_path}' does not exist"
        super().__init__(message)
        self.file_path = file_path


class InvalidConfigFileError(ConfigError):
    """Invalid configuration file format."""

    def __init__(self, file_path: str, reason: str):
        """
        Initialize invalid config file error.

        Args:
            file_path: Path to the invalid configuration file
            reason: Reason why the file is invalid
        """
        message = f"Invalid configuration file '{file_path}': {reason}"
        super().__init__(message)
        self.file_path = file_path
        self.reason = reason
