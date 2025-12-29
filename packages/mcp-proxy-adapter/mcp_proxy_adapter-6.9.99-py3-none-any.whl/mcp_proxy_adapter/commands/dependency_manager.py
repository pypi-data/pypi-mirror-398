"""
Dependency management system for remote plugins.

This module handles automatic installation and verification of plugin dependencies
using pip and other package management tools.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import sys
import importlib
from typing import List, Dict, Any, Tuple

try:  # Python 3.8+
    from importlib import metadata as importlib_metadata  # type: ignore
except Exception:  # pragma: no cover - very old Python fallback
    import importlib_metadata  # type: ignore

from packaging.requirements import Requirement
from packaging.version import Version, InvalidVersion

from mcp_proxy_adapter.core.logging import get_global_logger


class DependencyManager:
    """
    Manages plugin dependencies installation and verification.
    """

    def __init__(self):
        """Initialize dependency manager."""
        self._installed_packages: Dict[str, str] = {}
        self._load_installed_packages()

    def _load_installed_packages(self) -> None:
        """Load list of currently installed packages."""
        try:
            self._installed_packages.clear()
            for dist in importlib_metadata.distributions():
                try:
                    name = dist.metadata.get("Name") or dist.metadata.get("name")
                    version = dist.version
                    if name and version:
                        self._installed_packages[name.lower()] = version
                except Exception:
                    continue
        except Exception as e:
            get_global_logger().warning(f"Failed to load installed packages: {e}")


    def _is_dependency_satisfied(self, dependency: str) -> bool:
        """
        Check if a single dependency is satisfied.

        Args:
            dependency: Dependency name or spec

        Returns:
            True if dependency is satisfied, False otherwise
        """
        # Parse requirement (handles version specifiers)
        try:
            req = Requirement(dependency)
        except Exception:
            # Fallback: treat as importable module name
            try:
                importlib.import_module(dependency)
                return True
            except ImportError:
                return False

        # Check installation by distribution name
        try:
            installed_version = importlib_metadata.version(req.name)
        except importlib_metadata.PackageNotFoundError:
            return False

        # If no specifier, any installed version satisfies
        if not req.specifier:
            return True

        try:
            return Version(installed_version) in req.specifier
        except InvalidVersion:
            # If version parsing fails, fallback to string comparison via specifier
            return req.specifier.contains(installed_version, prereleases=True)


    def _install_single_dependency(
        self, dependency: str, user_install: bool = False
    ) -> bool:
        """
        Install a single dependency using pip.

        Args:
            dependency: Dependency name or spec
            user_install: Whether to install for current user only

        Returns:
            True if installation successful, False otherwise
        """
        try:
            # Build pip command
            cmd = [sys.executable, "-m", "pip", "install"]

            if user_install:
                cmd.append("--user")

            # Add quiet flag to reduce output
            cmd.append("--quiet")

            # Add dependency
            cmd.append(dependency)

            get_global_logger().debug(f"Installing dependency: {' '.join(cmd)}")

            # Run pip install
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                get_global_logger().debug(f"Successfully installed {dependency}")
                return True
            else:
                get_global_logger().error(f"Failed to install {dependency}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            get_global_logger().error(f"Timeout while installing {dependency}")
            return False
        except Exception as e:
            get_global_logger().error(f"Error installing {dependency}: {e}")
            return False





# Global instance
dependency_manager = DependencyManager()
