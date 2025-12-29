"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Command loading utilities for MCP Proxy Adapter.
"""

import importlib
import importlib.util
import inspect
import os
import tempfile
import urllib.parse
from pathlib import Path

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.core.logging import get_global_logger

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    get_global_logger().warning("requests library not available, HTTP/HTTPS loading will not work")


class CommandLoader:
    """Loader for commands from various sources."""

    def __init__(self):
        """Initialize command loader."""
        self.logger = get_global_logger()


    def _load_command_with_registry_check(self, source: str) -> Dict[str, Any]:
        """
        Load command with remote registry check.

        Args:
            source: Local path or command name

        Returns:
            Dictionary with loading result information
        """
        try:
            from mcp_proxy_adapter.commands.catalog_manager import CatalogManager
            from mcp_proxy_adapter.config import get_config

            # Get configuration
            config_obj = get_config()

            # Get remote registry
            plugin_servers = config_obj.get("commands.plugin_servers", [])
            catalog_dir = "./catalog"

            if plugin_servers:
                # Initialize catalog manager
                catalog_manager = CatalogManager(catalog_dir)

                # Check if source is a command name in registry
                if not os.path.exists(source) and not source.endswith("_command.py"):
                    # Try to find in remote registry
                    for server_url in plugin_servers:
                        try:
                            server_catalog = catalog_manager.get_catalog_from_server(
                                server_url
                            )
                            if source in server_catalog:
                                server_cmd = server_catalog[source]
                                # Download from registry
                                if catalog_manager._download_command(
                                    source, server_cmd
                                ):
                                    source = str(
                                        catalog_manager.commands_dir
                                        / f"{source}_command.py"
                                    )
                                    break
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to check registry {server_url}: {e}"
                            )

            # Load from local file
            return self._load_command_from_file(source)

        except Exception as e:
            self.logger.error(f"Failed to load command with registry check: {e}")
            return {"success": False, "commands_loaded": 0, "error": str(e)}

    def _load_command_from_url(self, url: str) -> Dict[str, Any]:
        """
        Load command from HTTP/HTTPS URL.

        Args:
            url: URL to load command from

        Returns:
            Dictionary with loading result information
        """
        if not REQUESTS_AVAILABLE:
            error_msg = "requests library not available, cannot load from URL"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "commands_loaded": 0,
                "source": url,
            }

        try:
            # Download command file
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix="_command.py", delete=False
            ) as temp_file:
                temp_file.write(response.text)
                temp_file_path = temp_file.name

            try:
                # Load from temporary file
                result = self._load_command_from_file(temp_file_path)
                result["source"] = url
                return result
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)

        except Exception as e:
            self.logger.error(f"Failed to load command from URL {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "commands_loaded": 0,
                "source": url,
            }

    def _load_command_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load command from local file.

        Args:
            file_path: Path to command file

        Returns:
            Dictionary with loading result information
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "commands_loaded": 0,
                    "source": file_path,
                }

            # Load module from file
            spec = importlib.util.spec_from_file_location(
                f"command_{Path(file_path).stem}", file_path
            )
            if spec is None or spec.loader is None:
                return {
                    "success": False,
                    "error": f"Could not load module from {file_path}",
                    "commands_loaded": 0,
                    "source": file_path,
                }

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find command classes in module
            commands = []
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Command)
                    and obj != Command
                ):
                    commands.append(obj)

            if not commands:
                return {
                    "success": False,
                    "error": f"No command classes found in {file_path}",
                    "commands_loaded": 0,
                    "source": file_path,
                }

            return {
                "success": True,
                "commands": commands,
                "commands_loaded": len(commands),
                "source": file_path,
            }

        except Exception as e:
            self.logger.error(f"Failed to load command from file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "commands_loaded": 0,
                "source": file_path,
            }
