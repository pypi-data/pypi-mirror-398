"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Main catalog manager for MCP Proxy Adapter.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from packaging import version as pkg_version

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.commands.dependency_manager import dependency_manager
from mcp_proxy_adapter.config import config
from .command_catalog import CommandCatalog
from .catalog_loader import CatalogLoader
from .catalog_syncer import CatalogSyncer
from .dependency_manager import DependencyManager

# Try to import requests, but don't fail if not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    get_global_logger().warning(
        "requests library not available, HTTP/HTTPS functionality will be limited"
    )


class CatalogManager:
    """
    Manager for command catalog operations.

    Handles loading, syncing, and managing command catalogs from various sources.
    """

    def __init__(self, catalog_dir: str):
        """
        Initialize catalog manager.

        Args:
            catalog_dir: Directory for catalog storage
        """
        self.catalog_dir = Path(catalog_dir)
        self.logger = get_global_logger()
        
        # Initialize components
        self.loader = CatalogLoader()
        self.syncer = CatalogSyncer(catalog_dir)
        self.dependency_manager = DependencyManager()
        
        # Load existing catalog
        self.catalog: Dict[str, CommandCatalog] = {}
        self._load_catalog()

    def _load_catalog(self) -> None:
        """Load catalog from local storage."""
        catalog_file = self.catalog_dir / "catalog.json"
        self.catalog = self.loader.load_catalog_from_file(catalog_file)

    def _save_catalog(self) -> None:
        """Save catalog to local storage."""
        catalog_file = self.catalog_dir / "catalog.json"
        self.loader.save_catalog_to_file(self.catalog, catalog_file)


    def sync_with_servers(self, server_urls: List[str]) -> Dict[str, Any]:
        """
        Synchronize catalog with remote servers.

        Args:
            server_urls: List of server URLs to sync with

        Returns:
            Dictionary with sync results
        """
        return self.syncer.sync_with_servers(server_urls)





    def _extract_metadata_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from command file.

        Args:
            file_path: Path to command file

        Returns:
            Dictionary of extracted metadata
        """
        metadata = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract basic metadata
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('__version__'):
                    metadata['version'] = line.split('=')[1].strip().strip('"\'')
                elif line.startswith('__author__'):
                    metadata['author'] = line.split('=')[1].strip().strip('"\'')
                elif line.startswith('__description__'):
                    metadata['description'] = line.split('=')[1].strip().strip('"\'')
                elif line.startswith('__category__'):
                    metadata['category'] = line.split('=')[1].strip().strip('"\'')
                elif line.startswith('__email__'):
                    metadata['email'] = line.split('=')[1].strip().strip('"\'')
                elif line.startswith('__depends__'):
                    deps_str = line.split('=')[1].strip().strip('[]"\'')
                    if deps_str:
                        metadata['depends'] = [dep.strip().strip('"\'') for dep in deps_str.split(',')]

        except Exception as e:
            self.logger.error(f"Failed to extract metadata from {file_path}: {e}")

        return metadata
