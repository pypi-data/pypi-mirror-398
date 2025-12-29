"""
Module for proxy registration functionality with security framework integration.

This module handles automatic registration and unregistration of the server
with the MCP proxy server during startup and shutdown, using mcp_security_framework
for secure connections and authentication.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional

from mcp_proxy_adapter.core.proxy.proxy_registration_manager import (
    ProxyRegistrationManager,
)

# Global registration manager instance
_registration_manager: Optional[ProxyRegistrationManager] = None


def initialize_proxy_registration(config: Dict[str, Any]) -> None:
    """
    Initialize proxy registration with configuration.

    Args:
        config: Application configuration
    """
    global _registration_manager
    _registration_manager = ProxyRegistrationManager(config)


async def register_with_proxy(server_url: str) -> bool:
    """
    Register server with proxy.

    Args:
        server_url: Server URL to register

    Returns:
        True if registration successful, False otherwise
    """
    if not _registration_manager:
        return False
    
    _registration_manager.set_server_url(server_url)
    return await _registration_manager.register()


async def unregister_from_proxy() -> bool:
    """
    Unregister server from proxy.

    Returns:
        True if unregistration successful, False otherwise
    """
    if not _registration_manager:
        return True
    
    return await _registration_manager.unregister()


def get_proxy_registration_status() -> Dict[str, Any]:
    """
    Get current proxy registration status.

    Returns:
        Dictionary with registration status information
    """
    if not _registration_manager:
        return {
            "enabled": False,
            "registered": False,
            "proxy_url": None,
            "server_url": None,
            "registration_time": None,
            "client_security_available": False,
        }
    
    return _registration_manager.get_registration_status()
