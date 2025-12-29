"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Feature management utilities for MCP Proxy Adapter configuration.
"""

from typing import Any, Dict, List

from mcp_proxy_adapter.core.logging import get_global_logger


class FeatureManager:
    """Manager for configuration features."""

    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize feature manager.

        Args:
            config_data: Configuration data dictionary
        """
        self.config_data = config_data
        self.logger = get_global_logger()







