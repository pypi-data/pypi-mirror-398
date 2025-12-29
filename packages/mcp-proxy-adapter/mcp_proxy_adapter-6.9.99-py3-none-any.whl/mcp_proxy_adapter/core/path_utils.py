"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Utilities for managing Python path in multiprocessing spawn mode.

This module provides functions to ensure that application modules are
available in child processes by automatically extending PYTHONPATH.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Set

from mcp_proxy_adapter.core.logging import get_global_logger


def find_module_path(module_name: str) -> Optional[Path]:
    """
    Find the directory containing a module.

    Args:
        module_name: Full module name (e.g., "embed.commands")

    Returns:
        Path to directory containing the module, or None if not found
    """
    try:
        import importlib.util

        # Try to find the module
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            module_file = Path(spec.origin)
            # Return parent directory (package root)
            return module_file.parent
    except (ImportError, ModuleNotFoundError, AttributeError):
        pass

    # Fallback: try importing and getting __file__
    try:
        import importlib

        module = importlib.import_module(module_name)
        if hasattr(module, "__file__") and module.__file__:
            module_file = Path(module.__file__)
            return module_file.parent
    except (ImportError, ModuleNotFoundError):
        pass

    return None


def ensure_module_path_in_syspath(module_name: str) -> bool:
    """
    Ensure that a module's directory is in sys.path.

    This function finds the module's directory and adds it to sys.path
    if it's not already there. This is useful for spawn mode where
    child processes don't inherit sys.path modifications.

    Args:
        module_name: Full module name (e.g., "embed.commands")

    Returns:
        True if path was added or already present, False if module not found
    """
    module_path = find_module_path(module_name)
    if not module_path:
        return False

    module_path_str = str(module_path.resolve())

    # Check if already in sys.path
    if module_path_str in sys.path:
        return True

    # Add to sys.path
    sys.path.insert(0, module_path_str)
    get_global_logger().debug(
        f"Added module path to sys.path: {module_path_str} (for module: {module_name})"
    )
    return True


def ensure_application_path(config_path: Optional[str] = None) -> Set[str]:
    """
    Ensure application root directory is in PYTHONPATH for spawn mode.

    This function:
    1. Determines the application root directory from config_path or current working directory
    2. Adds it to sys.path in the current process
    3. Updates PYTHONPATH environment variable so child processes inherit it

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        Set of paths that were added to PYTHONPATH
    """
    logger = get_global_logger()
    added_paths: Set[str] = set()

    # Determine application root
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            # Use parent directory of config file as application root
            app_root = config_file.parent.resolve()
        else:
            # Config file doesn't exist, use current working directory
            app_root = Path.cwd().resolve()
    else:
        # No config path, use current working directory
        app_root = Path.cwd().resolve()

    app_root_str = str(app_root)

    # Add to sys.path if not already present
    if app_root_str not in sys.path:
        sys.path.insert(0, app_root_str)
        added_paths.add(app_root_str)
        logger.debug(f"Added application root to sys.path: {app_root_str}")

    # Update PYTHONPATH environment variable for child processes
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    pythonpath_parts = [p for p in current_pythonpath.split(os.pathsep) if p.strip()]

    if app_root_str not in pythonpath_parts:
        pythonpath_parts.insert(0, app_root_str)
        new_pythonpath = os.pathsep.join(pythonpath_parts)
        os.environ["PYTHONPATH"] = new_pythonpath
        added_paths.add(app_root_str)
        logger.debug(
            f"Updated PYTHONPATH environment variable for spawn mode: {app_root_str}"
        )

    return added_paths


def ensure_registered_modules_paths() -> Set[str]:
    """
    Ensure all registered auto-import modules' paths are in sys.path and PYTHONPATH.

    This function:
    1. Gets list of registered modules from hooks
    2. Finds each module's directory
    3. Adds directories to sys.path and PYTHONPATH

    Returns:
        Set of paths that were added
    """
    logger = get_global_logger()
    added_paths: Set[str] = set()

    try:
        from mcp_proxy_adapter.commands.hooks import hooks

        auto_import_modules = hooks.get_auto_import_modules()

        for module_name in auto_import_modules:
            module_path = find_module_path(module_name)
            if module_path:
                module_path_str = str(module_path.resolve())

                # Add to sys.path
                if module_path_str not in sys.path:
                    sys.path.insert(0, module_path_str)
                    added_paths.add(module_path_str)
                    logger.debug(
                        f"Added registered module path to sys.path: {module_path_str} (module: {module_name})"
                    )

                # Update PYTHONPATH
                current_pythonpath = os.environ.get("PYTHONPATH", "")
                pythonpath_parts = [
                    p for p in current_pythonpath.split(os.pathsep) if p.strip()
                ]

                if module_path_str not in pythonpath_parts:
                    pythonpath_parts.insert(0, module_path_str)
                    new_pythonpath = os.pathsep.join(pythonpath_parts)
                    os.environ["PYTHONPATH"] = new_pythonpath
                    added_paths.add(module_path_str)
                    logger.debug(
                        f"Added registered module path to PYTHONPATH: {module_path_str} (module: {module_name})"
                    )
            else:
                logger.warning(
                    f"Could not find path for registered module: {module_name}. "
                    f"Module may not be importable in child processes."
                )
    except Exception as e:
        logger.warning(f"Failed to ensure registered modules paths: {e}")

    return added_paths

