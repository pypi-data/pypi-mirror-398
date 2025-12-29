"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Dependency management for command catalogs.
"""

import subprocess
import sys

from mcp_proxy_adapter.core.logging import get_global_logger


class DependencyManager:
    """Manager for command dependencies."""

    def __init__(self):
        """Initialize dependency manager."""
        self.logger = get_global_logger()



    def _is_package_installed(self, package_name: str) -> bool:
        """
        Check if a package is installed.

        Args:
            package_name: Name of the package to check

        Returns:
            True if package is installed, False otherwise
        """
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
