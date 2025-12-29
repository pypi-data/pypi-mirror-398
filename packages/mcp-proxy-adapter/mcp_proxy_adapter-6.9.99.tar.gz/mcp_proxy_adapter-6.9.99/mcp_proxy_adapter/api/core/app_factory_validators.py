"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Validation helpers for API AppFactory.
"""

from typing import Any, Dict, List


def validate_configuration(current_config: Dict[str, Any], logger) -> None:
    """
    Validate configuration at startup using ConfigValidator.

    Args:
        current_config: Configuration dictionary.
        logger: Logger instance for reporting errors.

    Raises:
        SystemExit: If validation fails.
    """
    try:
        from mcp_proxy_adapter.core.validation.config_validator import ConfigValidator

        validator = ConfigValidator()
        validator.config_data = current_config
        validation_results = validator.validate_config()
        errors = [r for r in validation_results if r.level == "error"]
        warnings = [r for r in validation_results if r.level == "warning"]

        if errors:
            logger.critical("CRITICAL CONFIG ERROR: Invalid configuration at startup:")
            for error in errors:
                logger.critical(f"  - {error.message}")
            raise SystemExit(1)

        for warning in warnings:
            logger.warning(f"Config warning: {warning.message}")
    except SystemExit:
        raise
    except Exception as ex:
        logger.error(f"Failed to run startup configuration validation: {ex}")


def validate_security_configuration(current_config: Dict[str, Any], logger) -> None:
    """
    Validate security configuration at startup.

    Args:
        current_config: Configuration dictionary.
        logger: Logger instance.

    Raises:
        SystemExit: If security configuration is invalid.
    """
    security_errors: List[str] = []

    print(f"🔍 Debug: current_config keys: {list(current_config.keys())}")
    if "security" in current_config:
        print(f"🔍 Debug: security config: {current_config['security']}")
    if "roles" in current_config:
        print(f"🔍 Debug: roles config: {current_config['roles']}")

    security_config = current_config.get("security", {})
    if security_config.get("enabled", False):
        from mcp_proxy_adapter.core.unified_config_adapter import UnifiedConfigAdapter

        adapter = UnifiedConfigAdapter()
        validation_result = adapter.validate_configuration(current_config)
        if not validation_result.is_valid:
            security_errors.extend(validation_result.errors)

    if security_errors:
        logger.critical(
            "CRITICAL SECURITY ERROR: Invalid security configuration at startup:"
        )
        for error in security_errors:
            logger.critical(f"  - {error}")
        raise SystemExit(1)


