"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Main configuration class for MCP Proxy Adapter.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_proxy_adapter.core.logging import get_global_logger
from .config_loader import ConfigLoader
from .feature_manager import FeatureManager
from .config_factory import ConfigFactory

# Import validation if available
try:
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False

# Import configuration errors
from ..errors import ConfigError, ValidationResult


class Config:
    """
    Configuration management class for the microservice.
    Allows loading settings from configuration file and environment variables.
    Supports optional features that can be enabled/disabled.
    """

    def __init__(
        self, config_path: Optional[str] = None, validate_on_load: bool = False
    ):
        """
        Initialize configuration.

        Args:
            config_path: Path to configuration file. If not specified,
                        "./config.json" is used.
            validate_on_load: Whether to validate configuration on load (default: False)

        Raises:
            ConfigError: If configuration validation fails
        """
        self._user_provided_path = config_path is not None
        self.config_path = config_path or "./config.json"
        self.config_data: Dict[str, Any] = {}
        self.validate_on_load = validate_on_load
        self.validation_results: List[ValidationResult] = []
        self.validator = None

        # Initialize components
        self.logger = get_global_logger()
        self.loader = ConfigLoader()
        self.feature_manager = FeatureManager(self.config_data)
        self.factory = ConfigFactory()

        # Load configuration
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file and environment variables."""
        try:
            config_path_obj = Path(self.config_path)
            if config_path_obj.exists():
                file_config = self.loader.load_from_file(self.config_path)
                self.config_data.update(file_config)
            elif self._user_provided_path:
                raise ConfigError(
                    f"Configuration file '{self.config_path}' does not exist. "
                    "Use the configuration generator to create a valid configuration."
                )

            # Load from environment variables
            try:
                env_config = self.loader.load_from_env()
                self._merge_config(env_config)
            except AttributeError:
                # load_from_env doesn't exist yet, skip
                pass

            # Validate if required
            if self.validate_on_load and VALIDATION_AVAILABLE:
                self.validate()
                if not self.is_valid():
                    raise ConfigError(
                        "Configuration validation failed",
                        validation_results=self.validation_results,
                    )

        except ConfigError:
            raise
        except json.JSONDecodeError as e:
            self.logger.error(
                "Invalid JSON in configuration file %s: %s", self.config_path, e
            )
            raise ConfigError(
                f"invalid JSON configuration file '{self.config_path}': {e}"
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise ConfigError(f"Configuration loading failed: {e}")

    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """
        Merge new configuration into existing configuration.

        Args:
            new_config: New configuration to merge
        """
        for section, values in new_config.items():
            if section in self.config_data:
                if isinstance(self.config_data[section], dict) and isinstance(
                    values, dict
                ):
                    self.config_data[section].update(values)
                else:
                    self.config_data[section] = values
            else:
                self.config_data[section] = values

    def enable_feature(self, feature: str) -> None:
        """
        Enable a feature.

        Args:
            feature: Feature name
        """
        self.feature_manager.enable_feature(feature)

    def disable_feature(self, feature: str) -> None:
        """
        Disable a feature.

        Args:
            feature: Feature name
        """
        self.feature_manager.disable_feature(feature)

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if feature is enabled.

        Args:
            feature: Feature name

        Returns:
            True if enabled, False otherwise
        """
        return self.feature_manager.is_feature_enabled(feature)

    def get_enabled_features(self) -> List[str]:
        """
        Get list of enabled features.

        Returns:
            List of enabled feature names
        """
        return self.feature_manager.get_enabled_features()

    def validate(self) -> List[ValidationResult]:
        """
        Validate configuration.

        Returns:
            List of validation results
        """
        if not VALIDATION_AVAILABLE:
            self.logger.warning("Configuration validation not available")
            return []

        try:
            from ..config_validator import ConfigValidator

            self.validator = ConfigValidator()
            self.validator.config_data = self.config_data
            self.validation_results = self.validator.validate_config()
            return self.validation_results
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise ConfigError(
                f"Configuration validation failed: {e}",
                validation_results=getattr(self, "validation_results", []),
            ) from e

    def get_validation_errors(self) -> List[ValidationResult]:
        """Get validation errors."""
        return [result for result in self.validation_results if result.level == "error"]

    def get_validation_warnings(self) -> List[ValidationResult]:
        """Get validation warnings."""
        return [
            result for result in self.validation_results if result.level == "warning"
        ]

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        errors = self.get_validation_errors()
        warnings = self.get_validation_warnings()

        return {
            "total": len(self.validation_results),
            "errors": len(errors),
            "warnings": len(warnings),
            "is_valid": len(errors) == 0,
        }

    def is_valid(self) -> bool:
        """
        Check whether the current configuration is valid.

        Returns:
            True if there are no validation errors, False otherwise.
        """
        return self.get_validation_summary()["is_valid"]

    def check_feature_requirements(self, feature: str) -> List[ValidationResult]:
        """
        Check feature requirements.

        Args:
            feature: Feature name

        Returns:
            List of validation results
        """
        return self.feature_manager.check_feature_requirements(feature)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Supports nested dictionary access using dot notation.
        For example: "transport.cert_file" will access config_data["transport"]["cert_file"]

        Args:
            key: Configuration key, can use dot notation (e.g., "transport.cert_file")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Examples:
            >>> config.get("server.host", "0.0.0.0")
            >>> config.get("transport.ssl.cert_file")
        """
        keys = key.split(".")
        value = self.config_data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration data.

        Returns:
            Complete configuration dictionary
        """
        return self.config_data
