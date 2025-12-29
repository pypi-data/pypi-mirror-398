"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Configuration validation functions for app factory.
"""

from pathlib import Path


def validate_config_file(config_path: str) -> bool:
    """
    Validate configuration file exists and is readable.

    Args:
        config_path: Path to configuration file

    Returns:
        True if valid, False otherwise
    """
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"❌ Configuration file not found: {config_path}")
            return False

        # Try to load configuration to validate JSON format
        from mcp_proxy_adapter.config import Config

        Config(config_path=str(config_file))
        return True

    except Exception as e:
        print(f"❌ Configuration file validation failed: {e}")
        return False


def validate_log_config_file(log_config_path: str) -> bool:
    """
    Validate logging configuration file exists and is readable.

    Args:
        log_config_path: Path to logging configuration file

    Returns:
        True if valid, False otherwise
    """
    try:
        log_config_file = Path(log_config_path)
        if not log_config_file.exists():
            print(f"❌ Log configuration file not found: {log_config_path}")
            return False
        return True

    except Exception as e:
        print(f"❌ Log configuration file validation failed: {e}")
        return False

