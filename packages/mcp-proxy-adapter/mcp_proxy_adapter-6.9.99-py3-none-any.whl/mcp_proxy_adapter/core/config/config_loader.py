"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Configuration loading utilities for MCP Proxy Adapter.
"""

import json
import os
from pathlib import Path
from typing import Any

from mcp_proxy_adapter.core.logging import get_global_logger


class ConfigLoader:
    """Loader for configuration files and environment variables."""

    def __init__(self):
        """Initialize config loader."""
        self.logger = get_global_logger()

    def load_from_file(self, config_path: str | Path) -> dict:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable value to appropriate type.

        Args:
            value: Value as string

        Returns:
            Converted value
        """
        # Try to convert to appropriate type
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        elif value.isdigit():
            return int(value)
        else:
            try:
                return float(value)
            except ValueError:
                return value

