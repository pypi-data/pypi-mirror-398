"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Catalog synchronization utilities for MCP Proxy Adapter.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from packaging import version as pkg_version

from mcp_proxy_adapter.core.logging import get_global_logger
from .command_catalog import CommandCatalog
from .catalog_loader import CatalogLoader
from .dependency_manager import DependencyManager

# Try to import requests, but don't fail if not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class CatalogSyncer:
    """Synchronizer for command catalogs."""

    def __init__(self, catalog_dir: str):
        """
        Initialize catalog syncer.

        Args:
            catalog_dir: Directory for catalog storage
        """
        self.catalog_dir = Path(catalog_dir)
        self.logger = get_global_logger()
        self.loader = CatalogLoader()
        self.dependency_manager = DependencyManager()


    def _should_download_command(self, command_name: str, server_cmd: CommandCatalog) -> bool:
        """
        Check if command should be downloaded.

        Args:
            command_name: Name of the command
            server_cmd: Server command catalog entry

        Returns:
            True if command should be downloaded, False otherwise
        """
        # Check if command exists locally
        local_file = self.catalog_dir / f"{command_name}.py"
        if not local_file.exists():
            return True

        # Check version
        try:
            local_version = self._get_local_version(command_name)
            if local_version:
                return pkg_version.parse(server_cmd.version) > pkg_version.parse(local_version)
        except Exception as e:
            self.logger.warning(f"Failed to compare versions for {command_name}: {e}")

        return True

    def _download_command(self, command_name: str, server_cmd: CommandCatalog) -> bool:
        """
        Download command from server.

        Args:
            command_name: Name of the command
            server_cmd: Server command catalog entry

        Returns:
            True if download successful, False otherwise
        """
        if not REQUESTS_AVAILABLE:
            self.logger.error("requests library not available, cannot download command")
            return False

        try:
            # Download command file
            response = requests.get(server_cmd.source_url, timeout=30)
            response.raise_for_status()

            # Save to local file
            local_file = self.catalog_dir / f"{command_name}.py"
            with open(local_file, 'w', encoding='utf-8') as f:
                f.write(response.text)

            # Update local catalog
            server_cmd.file_path = str(local_file)
            self._update_local_catalog(command_name, server_cmd)

            return True

        except Exception as e:
            self.logger.error(f"Failed to download command {command_name}: {e}")
            return False

    def _get_local_version(self, command_name: str) -> Optional[str]:
        """
        Get local version of command.

        Args:
            command_name: Name of the command

        Returns:
            Local version string or None
        """
        try:
            local_file = self.catalog_dir / f"{command_name}.py"
            if local_file.exists():
                with open(local_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract version from file content
                for line in content.split('\n'):
                    if line.strip().startswith('__version__'):
                        return line.split('=')[1].strip().strip('"\'')
        except Exception:
            pass
        
        return None

    def _update_local_catalog(self, command_name: str, command_catalog: CommandCatalog) -> None:
        """
        Update local catalog with command information.

        Args:
            command_name: Name of the command
            command_catalog: Command catalog entry
        """
        try:
            catalog_file = self.catalog_dir / "catalog.json"
            if catalog_file.exists():
                with open(catalog_file, 'r', encoding='utf-8') as f:
                    catalog_data = json.load(f)
            else:
                catalog_data = {}

            catalog_data[command_name] = command_catalog.to_dict()

            with open(catalog_file, 'w', encoding='utf-8') as f:
                json.dump(catalog_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Failed to update local catalog for {command_name}: {e}")
