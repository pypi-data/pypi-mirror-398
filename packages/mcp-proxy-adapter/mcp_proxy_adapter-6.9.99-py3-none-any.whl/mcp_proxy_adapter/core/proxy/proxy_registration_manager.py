"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Main proxy registration manager for MCP Proxy Adapter.
"""

import time
from typing import Dict, Any

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.client_security import create_client_security_manager
from .registration_client import RegistrationClient


class ProxyRegistrationError(Exception):
    """Exception raised when proxy registration fails."""

    pass


class ProxyRegistrationManager:
    """
    Manager for proxy registration functionality with security framework integration.

    Handles automatic registration and unregistration of the server
    with the MCP proxy server using secure authentication methods.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the proxy registration manager.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = get_global_logger()
        
        # Get registration configuration
        self.registration_config = config.get("registration", {})
        
        # Initialize client security
        self.client_security = create_client_security_manager(config)
        
        # Registration state
        # Extract proxy URL from register_url
        register_url = self.registration_config.get("register_url")
        if register_url:
            from urllib.parse import urlparse
            parsed = urlparse(register_url)
            self.proxy_url = f"{parsed.scheme}://{parsed.netloc}"
        else:
            self.proxy_url = None
        self.server_url = None
        self.registered = False
        self.registration_time = None
        
        # Initialize registration client
        self.registration_client = RegistrationClient(
            self.client_security, self.registration_config, config, self.proxy_url
        )

    def is_enabled(self) -> bool:
        """
        Check if proxy registration is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self.registration_config.get("enabled", False)

    async def register(self) -> bool:
        """
        Register server with proxy.

        Returns:
            True if registration successful, False otherwise
        """
        if not self.is_enabled():
            self.logger.info("Proxy registration is disabled")
            return True

        if not self.server_url:
            self.logger.error("Server URL not set for registration")
            return False

        if not self.proxy_url:
            self.logger.error("Proxy URL not configured")
            return False

        try:
            self.logger.info(f"Registering with proxy: {self.proxy_url}")
            
            success = await self.registration_client.register(self.server_url)
            
            if success:
                self.registered = True
                self.registration_time = time.time()
                self.logger.info("✅ Proxy registration completed successfully")
            else:
                self.logger.error("❌ Proxy registration failed")
            
            return success

        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            return False

    async def unregister(self) -> bool:
        """
        Unregister server from proxy.

        Returns:
            True if unregistration successful, False otherwise
        """
        if not self.is_enabled():
            self.logger.info("Proxy registration is disabled")
            return True

        if not self.registered:
            self.logger.info("Server not registered, skipping unregistration")
            return True

        try:
            self.logger.info("Unregistering from proxy")
            
            success = await self.registration_client.unregister()
            
            if success:
                self.registered = False
                self.registration_time = None
                self.logger.info("✅ Proxy unregistration completed successfully")
            else:
                self.logger.warning("⚠️ Proxy unregistration failed")
            
            return success

        except Exception as e:
            self.logger.error(f"Unregistration error: {e}")
            return False

    def set_server_url(self, server_url: str) -> None:
        """
        Set server URL for registration.

        Args:
            server_url: Server URL to register
        """
        self.server_url = server_url
        self.logger.info(f"Server URL set: {server_url}")

    def get_registration_status(self) -> Dict[str, Any]:
        """
        Get current registration status.

        Returns:
            Dictionary with registration status information
        """
        return {
            "enabled": self.is_enabled(),
            "registered": self.registered,
            "proxy_url": self.proxy_url,
            "server_url": self.server_url,
            "registration_time": self.registration_time,
            "client_security_available": self.client_security is not None,
        }
