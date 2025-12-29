"""
Protocol management module for MCP Proxy Adapter.

This module provides functionality for managing and validating protocol configurations,
including HTTP, HTTPS, and MTLS protocols with their respective ports.
"""

from urllib.parse import urlparse
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ssl import SSLContext

from mcp_proxy_adapter.config import config
from mcp_proxy_adapter.core.logging import get_global_logger


class ProtocolManager:
    """
    Manages protocol configurations and validates protocol access.

    This class handles the validation of allowed protocols and their associated ports,
    ensuring that only configured protocols are accessible.
    """

    def __init__(self, app_config: Optional[Dict] = None):
        """
        Initialize the protocol manager.

        Args:
            app_config: Application configuration dictionary (optional)
        """
        self.app_config = app_config
        self._load_config()

    def _load_config(self):
        """Load protocol configuration from config."""
        # Use provided config or fallback to global config; normalize types
        current_config = (
            self.app_config if self.app_config is not None else config.get_all()
        )
        get_global_logger().debug(
            f"ProtocolManager._load_config - current_config type: {type(current_config)}"
        )

        if not hasattr(current_config, "get"):
            # Not a dict-like config, fallback to global
            get_global_logger().debug(
                f"ProtocolManager._load_config - current_config is not dict-like, falling back to global config"
            )
            current_config = config.get_all()

        get_global_logger().debug(
            f"ProtocolManager._load_config - final current_config type: {type(current_config)}"
        )
        if hasattr(current_config, "get"):
            get_global_logger().debug(
                f"ProtocolManager._load_config - current_config keys: {list(current_config.keys()) if hasattr(current_config, 'keys') else 'no keys'}"
            )

        # Get server protocol configuration (new simplified structure)
        get_global_logger().debug(f"ProtocolManager._load_config - before getting server protocol")
        try:
            server_config = current_config.get("server", {})
            server_protocol = server_config.get("protocol", "http")
            get_global_logger().debug(f"ProtocolManager._load_config - server protocol: {server_protocol}")
            
            # Set allowed protocols based on server protocol
            if server_protocol == "http":
                self.allowed_protocols = ["http"]
            elif server_protocol == "https":
                self.allowed_protocols = ["https"]
            elif server_protocol == "mtls":
                self.allowed_protocols = ["mtls", "https"]  # mTLS also supports HTTPS
            else:
                # Fallback to HTTP
                self.allowed_protocols = ["http"]
                get_global_logger().warning(f"Unknown server protocol '{server_protocol}', defaulting to HTTP")
                
            get_global_logger().debug(f"ProtocolManager._load_config - allowed protocols: {self.allowed_protocols}")
            
        except Exception as e:
            get_global_logger().debug(f"ProtocolManager._load_config - ERROR getting server protocol: {e}")
            # Fallback to HTTP
            self.allowed_protocols = ["http"]

        # Protocol management is always enabled in new structure
        self.enabled = True

        get_global_logger().debug(
            f"Protocol manager loaded config: enabled={self.enabled}, allowed_protocols={self.allowed_protocols}"
        )




    def is_protocol_allowed(self, protocol: str) -> bool:
        """
        Check if a protocol is allowed based on configuration.

        Args:
            protocol: Protocol name (http, https, mtls)

        Returns:
            True if protocol is allowed, False otherwise
        """
        get_global_logger().debug(f"🔍 ProtocolManager.is_protocol_allowed - protocol: {protocol}")
        get_global_logger().debug(f"🔍 ProtocolManager.is_protocol_allowed - enabled: {self.enabled}")
        get_global_logger().debug(f"🔍 ProtocolManager.is_protocol_allowed - allowed_protocols: {self.allowed_protocols}")
        
        if not self.enabled:
            get_global_logger().debug("✅ ProtocolManager.is_protocol_allowed - Protocol management is disabled, allowing all protocols")
            return True

        protocol_lower = protocol.lower()
        is_allowed = protocol_lower in self.allowed_protocols

        get_global_logger().debug(f"🔍 ProtocolManager.is_protocol_allowed - Protocol '{protocol}' allowed: {is_allowed}")
        return is_allowed



    def get_protocol_config(self, protocol: str) -> Dict:
        """
        Get full configuration for a specific protocol.

        Args:
            protocol: Protocol name (http, https, mtls)

        Returns:
            Protocol configuration dictionary
        """
        protocol_lower = protocol.lower()
        cfg = self.protocols_config.get(protocol_lower, {})
        # Ensure dict type
        if isinstance(cfg, dict):
            try:
                return cfg.copy()
            except Exception:
                return {}
        return {}


    def get_ssl_context_for_protocol(self, protocol: str) -> Optional["SSLContext"]:
        """
        Get SSL context for HTTPS or MTLS protocol.

        Args:
            protocol: Protocol name (https, mtls)

        Returns:
            SSL context if protocol requires SSL, None otherwise
        """
        if protocol.lower() not in ["https", "mtls"]:
            return None

        # Use provided config or fallback to global config
        current_config = (
            self.app_config if self.app_config is not None else config.get_all()
        )

        # Get SSL configuration
        ssl_config = self._get_ssl_config(current_config)

        if not ssl_config.get("enabled", False):
            get_global_logger().warning(
                f"SSL required for protocol '{protocol}' but SSL is disabled"
            )
            return None

        cert_file = ssl_config.get("cert_file")
        key_file = ssl_config.get("key_file")

        if not cert_file or not key_file:
            get_global_logger().warning(
                f"SSL required for protocol '{protocol}' but certificate files not configured"
            )
            return None

        try:
            from mcp_proxy_adapter.core.ssl_utils import SSLUtils

            ssl_context = SSLUtils.create_ssl_context(
                cert_file=cert_file,
                key_file=key_file,
                ca_cert=ssl_config.get("ca_cert"),
                verify_client=protocol.lower() == "mtls"
                or ssl_config.get("verify_client", False),
                cipher_suites=ssl_config.get("cipher_suites"),
                min_tls_version=ssl_config.get("min_tls_version", "TLSv1.2"),
                max_tls_version=ssl_config.get("max_tls_version", "TLSv1.3"),
            )

            get_global_logger().info(f"SSL context created for protocol '{protocol}'")
            return ssl_context

        except Exception as e:
            get_global_logger().error(f"Failed to create SSL context for protocol '{protocol}': {e}")
            return None

    def _get_ssl_config(self, current_config: Dict) -> Dict:
        """
        Get SSL configuration from config.

        Args:
            current_config: Current configuration dictionary

        Returns:
            SSL configuration dictionary
        """
        # Try security framework SSL config first
        security_config = current_config.get("security", {})
        ssl_config = security_config.get("ssl", {})

        if ssl_config.get("enabled", False):
            get_global_logger().debug("Using security.ssl configuration")
            return ssl_config

        # Fallback to legacy SSL config
        legacy_ssl_config = current_config.get("ssl", {})
        if legacy_ssl_config.get("enabled", False):
            get_global_logger().debug("Using legacy ssl configuration")
            return legacy_ssl_config

        # Return empty config if SSL is disabled
        return {"enabled": False}




# Global protocol manager instance - will be updated with config when needed
protocol_manager = None


