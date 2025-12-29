"""
Transport manager module.

This module provides transport management functionality for the MCP Proxy Adapter.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from mcp_proxy_adapter.core.logging import get_global_logger


class TransportType(Enum):
    """Transport types enumeration."""

    HTTP = "http"
    HTTPS = "https"
    MTLS = "mtls"


@dataclass
class TransportConfig:
    """Transport configuration data class."""

    type: TransportType
    port: Optional[int]
    ssl_enabled: bool
    cert_file: Optional[str]
    key_file: Optional[str]
    ca_cert: Optional[str]
    verify_client: bool
    client_cert_required: bool


class TransportManager:
    """
    Transport manager for handling different transport types.

    This class manages transport configuration and provides utilities
    for determining ports and SSL settings based on transport type.
    """

    # Default ports for transport types
    DEFAULT_PORTS = {
        TransportType.HTTP: 8000,
        TransportType.HTTPS: 8443,
        TransportType.MTLS: 9443,
    }

    def __init__(self):
        """Initialize transport manager."""
        self._config: Optional[TransportConfig] = None
        self._current_transport: Optional[TransportType] = None



    def get_port(self) -> Optional[int]:
        """
        Get configured port.

        Returns:
            Port number or None if not configured
        """
        return self._config.port if self._config else None

    def is_ssl_enabled(self) -> bool:
        """
        Check if SSL is enabled.

        Returns:
            True if SSL is enabled, False otherwise
        """
        return self._config.ssl_enabled if self._config else False

    def get_ssl_config(self) -> Optional[Dict[str, Any]]:
        """
        Get SSL configuration.

        Returns:
            SSL configuration dict or None if SSL not enabled
        """
        if not self._config or not self._config.ssl_enabled:
            return None

        return {
            "cert_file": self._config.cert_file,
            "key_file": self._config.key_file,
            "ca_cert": self._config.ca_cert,
            "verify_client": self._config.verify_client,
            "client_cert_required": self._config.client_cert_required,
        }

    def get_transport_info(self) -> Dict[str, Any]:
        """
        Get comprehensive transport information.

        Returns:
            Dictionary with transport information
        """
        info: Dict[str, Any] = {
            "type": self._current_transport.value if self._current_transport else None,
            "port": self.get_port(),
            "ssl_enabled": self.is_ssl_enabled(),
            "ssl_config": self.get_ssl_config(),
            "is_mtls": self.is_mtls(),
            "is_https": self.is_https(),
            "is_http": self.is_http(),
        }
        return info

    def is_mtls(self) -> bool:
        """
        Check if current transport is MTLS.

        Returns:
            True if MTLS transport, False otherwise
        """
        return self._current_transport == TransportType.MTLS

    def is_https(self) -> bool:
        """
        Check if current transport is HTTPS.

        Returns:
            True if HTTPS transport, False otherwise
        """
        return self._current_transport == TransportType.HTTPS

    def is_http(self) -> bool:
        """
        Check if current transport is HTTP.

        Returns:
            True if HTTP transport, False otherwise
        """
        return self._current_transport == TransportType.HTTP



    def validate_ssl_files(self) -> bool:
        """
        Check if SSL files exist.

        Returns:
            True if all SSL files exist, False otherwise
        """
        if not self._config or not self._config.ssl_enabled:
            return True

        files_to_check = []
        if self._config.cert_file:
            files_to_check.append(self._config.cert_file)
        if self._config.key_file:
            files_to_check.append(self._config.key_file)
        if self._config.ca_cert:
            files_to_check.append(self._config.ca_cert)

        for file_path in files_to_check:
            if not Path(file_path).exists():
                get_global_logger().error(f"SSL file not found: {file_path}")
                return False

        get_global_logger().info(f"All SSL files validated successfully: {files_to_check}")
        return True



# Global transport manager instance
transport_manager = TransportManager()
