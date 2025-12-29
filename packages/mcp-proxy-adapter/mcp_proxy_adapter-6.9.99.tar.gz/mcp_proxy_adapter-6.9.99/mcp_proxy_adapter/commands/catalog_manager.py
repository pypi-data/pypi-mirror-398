"""
Command catalog management system.

This module handles the command catalog, including:
- Loading commands from remote plugin servers
- Version comparison and updates
- Local command storage and management
- Automatic dependency installation

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, List, Optional, Any

from .catalog import CommandCatalog, CatalogManager


# Global catalog manager instance
_catalog_manager: Optional[CatalogManager] = None


def get_catalog_manager() -> CatalogManager:
    """
    Get the global catalog manager instance.

    Returns:
        Catalog manager instance
    """
    global _catalog_manager
    if _catalog_manager is None:
        from mcp_proxy_adapter.config import config
        catalog_dir = config.get("catalog", {}).get("directory", "catalog")
        _catalog_manager = CatalogManager(catalog_dir)
    return _catalog_manager


def get_catalog_from_server(server_url: str) -> Dict[str, CommandCatalog]:
    """
    Get catalog from remote server.

    Args:
        server_url: Server URL to load catalog from

    Returns:
        Dictionary of command catalogs
    """
    return get_catalog_manager().get_catalog_from_server(server_url)


def sync_with_servers(server_urls: List[str]) -> Dict[str, Any]:
    """
    Synchronize catalog with remote servers.

    Args:
        server_urls: List of server URLs to sync with

    Returns:
        Dictionary with sync results
    """
    return get_catalog_manager().sync_with_servers(server_urls)


def get_local_commands() -> List[str]:
    """
    Get list of locally available commands.

    Returns:
        List of command names
    """
    return get_catalog_manager().get_local_commands()


def get_command_info(command_name: str) -> Optional[CommandCatalog]:
    """
    Get information about a specific command.

    Args:
        command_name: Name of the command

    Returns:
        Command catalog entry or None if not found
    """
    return get_catalog_manager().get_command_info(command_name)


def remove_command(command_name: str) -> bool:
    """
    Remove command from catalog.

    Args:
        command_name: Name of the command to remove

    Returns:
        True if successful, False otherwise
    """
    return get_catalog_manager().remove_command(command_name)
