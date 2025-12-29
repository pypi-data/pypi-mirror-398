"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Configuration loading and validation for app factory.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

from .ssl_config import build_server_ssl_config


def load_and_validate_config(config_path: Optional[str]) -> Dict[str, Any]:
    """
    Load and validate configuration file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        SystemExit: If configuration validation fails
    """
    app_config = None
    if config_path:
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"❌ Configuration file not found: {config_path}")
            print("   Please provide a valid path to config.json")
            sys.exit(1)

        try:
            from mcp_proxy_adapter.config import Config

            config_instance = Config(config_path=str(config_file))
            app_config = config_instance.config_data
            print(f"✅ Configuration loaded from: {config_path}")

            # Validate UUID configuration (mandatory)
            from mcp_proxy_adapter.core.config_validator import ConfigValidator

            validator = ConfigValidator()
            validator.config_data = app_config
            validation_results = validator.validate_config()
            errors = [r for r in validation_results if r.level == "error"]
            if errors:
                print("❌ Configuration validation failed:")
                for error in errors:
                    print(f"   - {error}")
                sys.exit(1)
            print("✅ Configuration validation passed")

            # Validate SSL configuration
            validate_ssl_config(app_config)

            # Validate security framework configuration
            validate_security_config(app_config)

        except Exception as e:
            print(f"❌ Failed to load configuration from {config_path}: {e}")
            sys.exit(1)
    else:
        print("⚠️  No configuration file provided, using defaults")
        from mcp_proxy_adapter.config import config

        app_config = config.config_data

    return app_config


def validate_ssl_config(app_config: Dict[str, Any]) -> None:
    """
    Validate SSL configuration.

    Args:
        app_config: Application configuration dictionary

    Raises:
        ValueError: If SSL configuration is invalid
    """
    server_cfg = (app_config or {}).get("server", {}) or {}
    protocol = str(server_cfg.get("protocol", "http")).lower()

    legacy_ssl = (
        (app_config or {}).get("ssl", {}) if isinstance(app_config, dict) else {}
    )
    legacy_enabled = isinstance(legacy_ssl, dict) and legacy_ssl.get("enabled", False)

    if legacy_enabled and protocol not in ("https", "mtls"):
        raise ValueError(
            "CRITICAL CONFIG ERROR: Legacy root-level SSL is enabled but server protocol "
            f"is '{protocol}'. Set server.protocol to 'https' or 'mtls' and migrate to "
            "server.ssl section."
        )

    if protocol not in ("https", "mtls"):
        return

    try:
        build_server_ssl_config(app_config)
        print("✅ SSL configuration validated via mcp_security_framework")
    except ValueError as exc:
        raise ValueError(str(exc)) from exc


def validate_security_config(app_config: Dict[str, Any]) -> None:
    """
    Validate security framework configuration.

    Args:
        app_config: Application configuration dictionary

    Raises:
        SystemExit: If security configuration validation fails
    """
    security_config = app_config.get("security", {})
    if security_config.get("enabled", False):
        framework = security_config.get("framework", "mcp_security_framework")
        print(f"🔒 Security framework: {framework}")

        # Validate security configuration
        from mcp_proxy_adapter.core.unified_config_adapter import (
            UnifiedConfigAdapter,
        )

        adapter = UnifiedConfigAdapter()
        validation_result = adapter.validate_configuration(app_config)

        if not validation_result.is_valid:
            print("❌ Security configuration validation failed:")
            for error in validation_result.errors:
                print(f"   - {error}")
            sys.exit(1)

        if validation_result.warnings:
            print("⚠️  Security configuration warnings:")
            for warning in validation_result.warnings:
                print(f"   - {warning}")

        print("✅ Security configuration validated successfully")
    else:
        print("🔓 Security framework disabled")
