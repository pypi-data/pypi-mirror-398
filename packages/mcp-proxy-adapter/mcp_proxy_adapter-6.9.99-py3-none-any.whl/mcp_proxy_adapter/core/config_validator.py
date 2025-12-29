"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Main configuration validator for MCP Proxy Adapter.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .validation.file_validator import FileValidator
from .validation.security_validator import SecurityValidator
from .validation.protocol_validator import ProtocolValidator
from .validation.validation_result import ValidationResult

logger = logging.getLogger(__name__)


class ConfigValidator:
    """
    Comprehensive configuration validator for MCP Proxy Adapter.

    Validates:
    - Required sections and keys
    - File existence for referenced files
    - Feature flag dependencies
    - Protocol-specific requirements
    - Security configuration consistency
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration validator.

        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path
        self.config_data: Dict[str, Any] = {}
        self.validation_results: List[ValidationResult] = []

    def load_config(self, config_path: Optional[str] = None) -> None:
        """
        Load configuration from file.

        Args:
            config_path: Path to configuration file
        """
        if config_path:
            self.config_path = config_path

        if not self.config_path:
            raise ValueError("No configuration path provided")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config_data = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")

    def validate_config(
        self, config_data: Optional[Dict[str, Any]] = None
    ) -> List[ValidationResult]:
        """
        Validate configuration data.

        Args:
            config_data: Configuration data to validate (optional)

        Returns:
            List of validation results
        """
        if config_data is not None:
            self.config_data = config_data

        if not self.config_data:
            raise ValueError("No configuration data to validate")

        self.validation_results = []
        self._validate_required_sections_present()

        # Initialize validators
        file_validator = FileValidator(self.config_data)
        security_validator = SecurityValidator(self.config_data)
        protocol_validator = ProtocolValidator(self.config_data)

        # Run all validations
        self.validation_results.extend(protocol_validator.validate_required_sections())
        self.validation_results.extend(
            protocol_validator.validate_protocol_requirements()
        )
        self.validation_results.extend(file_validator.validate_file_existence())
        self.validation_results.extend(
            security_validator.validate_security_consistency()
        )
        self.validation_results.extend(security_validator.validate_ssl_configuration())
        self.validation_results.extend(
            security_validator.validate_roles_configuration()
        )
        self.validation_results.extend(security_validator.validate_proxy_registration())

        # Additional validations
        self._validate_unknown_fields()
        self._validate_uuid_format()

        return self.validation_results

    def validate_all(
        self, config_data: Optional[Dict[str, Any]] = None
    ) -> List[ValidationResult]:
        """
        Validate all aspects of the configuration.

        Args:
            config_data: Configuration data to validate (optional)

        Returns:
            List of validation results
        """
        return self.validate_config(config_data)

    def _validate_unknown_fields(self) -> None:
        """Validate for unknown configuration fields."""
        known_sections = {
            "server",
            "protocols",
            "security",
            "ssl",
            "auth",
            "roles",
            "logging",
            "commands",
            "proxy_registration",
            "transport",
        }

        for section in self.config_data.keys():
            if section not in known_sections:
                self.validation_results.append(
                    ValidationResult(
                        level="warning",
                        message=f"Unknown configuration section: {section}",
                        section=section,
                        suggestion="Check if this section is needed or if it's a typo",
                    )
                )

    def _validate_uuid_format(self) -> None:
        """Validate UUID format in configuration."""
        uuid_fields = ["server.server_id", "proxy_registration.server_id"]

        for field in uuid_fields:
            value = self._get_nested_value_safe(field)
            if value and not self._is_valid_uuid4(str(value)):
                self.validation_results.append(
                    ValidationResult(
                        level="warning",
                        message=f"Invalid UUID format in {field}: {value}",
                        section=field.split(".")[0],
                        key=field.split(".")[1],
                        suggestion="Use a valid UUID4 format",
                    )
                )

    def _is_valid_uuid4(self, uuid_str: str) -> bool:
        """Check if string is a valid UUID4."""
        import re

        uuid_pattern = (
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )
        return bool(re.match(uuid_pattern, uuid_str, re.IGNORECASE))

    def _get_nested_value_safe(self, key: str, default: Any = None) -> Any:
        """Safely get a nested value from configuration."""
        keys = key.split(".")
        value = self.config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def _validate_required_sections_present(self) -> None:
        """Ensure mandatory configuration sections exist."""
        required_sections = ("server", "logging", "commands", "transport")
        for section in required_sections:
            if section not in self.config_data:
                self.validation_results.append(
                    ValidationResult(
                        level="error",
                        message=f"Required section '{section}' is missing from configuration",
                        section=section,
                        suggestion=f"Add the '{section}' section to the configuration file",
                    )
                )

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of validation results.

        Returns:
            Dictionary with validation summary
        """
        error_count = sum(1 for r in self.validation_results if r.level == "error")
        warning_count = sum(1 for r in self.validation_results if r.level == "warning")
        info_count = sum(1 for r in self.validation_results if r.level == "info")

        return {
            "total_issues": len(self.validation_results),
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count,
            "is_valid": error_count == 0,
        }

    def print_validation_report(self) -> None:
        """Print a formatted validation report."""
        summary = self.get_validation_summary()

        print("\n📋 Configuration Validation Report")
        print(f"{'=' * 40}")
        print(f"Total issues: {summary['total_issues']}")
        print(f"Errors: {summary['errors']}")
        print(f"Warnings: {summary['warnings']}")
        print(f"Info: {summary['info']}")
        print(f"Valid: {'✅ Yes' if summary['is_valid'] else '❌ No'}")

        if self.validation_results:
            print("\n📝 Issues:")
            for i, result in enumerate(self.validation_results, 1):
                level_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[result.level]
                print(f"{i:2d}. {level_icon} {result.message}")
                if result.section:
                    print(f"    Section: {result.section}")
                if result.key:
                    print(f"    Key: {result.key}")
                if result.suggestion:
                    print(f"    Suggestion: {result.suggestion}")
                print()
