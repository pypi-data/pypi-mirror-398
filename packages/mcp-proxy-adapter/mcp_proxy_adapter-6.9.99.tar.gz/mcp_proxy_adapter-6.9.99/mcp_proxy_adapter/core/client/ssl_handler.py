"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

SSL context handler for UniversalClient.
"""

from typing import Dict, Optional, TYPE_CHECKING

from mcp_proxy_adapter.core.ssl_utils import SSLUtils

if TYPE_CHECKING:
    from ssl import SSLContext

try:
    from mcp_security_framework import SecurityManager

    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False
    SecurityManager = None


class SSLHandler:
    """Handler for SSL context creation."""

    def __init__(self, security_config: Dict, security_manager=None):
        """
        Initialize SSL handler.
        
        Args:
            security_config: Security configuration dictionary
            security_manager: Optional security manager instance
        """
        self.security_config = security_config
        self.security_manager = security_manager

    def create_ssl_context(self) -> Optional["SSLContext"]:
        """
        Create SSL context for secure connections.
        
        Returns:
            SSL context or None if SSL is not enabled
        """
        ssl_config = self.security_config.get("ssl", {})
        if not ssl_config.get("enabled", False):
            return None

        try:
            context: Optional["SSLContext"] = None

            # Try security framework first
            if self.security_manager:
                try:
                    context = self.security_manager.create_client_ssl_context()
                except Exception:
                    context = None

            if context is None:
                cert_config = self.security_config.get("certificate", {})
                cert_file = cert_config.get("cert_file") or ssl_config.get("cert_file")
                key_file = cert_config.get("key_file") or ssl_config.get("key_file")
                ca_cert_file = ssl_config.get("ca_cert_file") or ssl_config.get("ca_cert")

                context = SSLUtils.create_client_ssl_context(
                    ca_cert=ca_cert_file,
                    client_cert=cert_file,
                    client_key=key_file,
                    verify=ssl_config.get("check_hostname", True),
                    min_tls_version=ssl_config.get("min_tls_version", "TLSv1.2"),
                    max_tls_version=ssl_config.get("max_tls_version"),
                    check_hostname=ssl_config.get("check_hostname", True),
                )

            return context
        except Exception as e:  # noqa: BLE001
            print(f"Warning: Failed to create SSL context: {e}")
            return None

