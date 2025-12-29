"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Configuration factory for creating predefined configurations.
"""

from typing import Dict, Any

from mcp_proxy_adapter.core.logging import get_global_logger


class ConfigFactory:
    """Factory for creating predefined configurations."""

    def __init__(self):
        """Initialize config factory."""
        self.logger = get_global_logger()




