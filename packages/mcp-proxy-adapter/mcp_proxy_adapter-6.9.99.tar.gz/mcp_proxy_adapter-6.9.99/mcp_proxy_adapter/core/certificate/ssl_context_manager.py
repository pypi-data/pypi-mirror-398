"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

SSL context management utilities for MCP Proxy Adapter.
"""

import logging
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from mcp_proxy_adapter.core.ssl_utils import SSLUtils

if TYPE_CHECKING:
    from ssl import SSLContext

logger = logging.getLogger(__name__)


class SSLContextManager:
    """Manager for SSL contexts."""

    @staticmethod
    def create_ssl_context(
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        verify_mode: str = "CERT_NONE",
        check_hostname: bool = False,
    ) -> "SSLContext":
        """
        Create SSL context for server or client.

        Args:
            cert_file: Path to certificate file
            key_file: Path to private key file
            ca_cert_file: Path to CA certificate file
            verify_mode: SSL verification mode
            check_hostname: Whether to check hostname

        Returns:
            SSL context
        """
        try:
            # Create SSL context
            if cert_file and not Path(cert_file).exists():
                raise FileNotFoundError(f"Certificate file not found: {cert_file}")
            if key_file and not Path(key_file).exists():
                raise FileNotFoundError(f"Key file not found: {key_file}")
            if ca_cert_file and not Path(ca_cert_file).exists():
                raise FileNotFoundError(f"CA certificate file not found: {ca_cert_file}")

            return SSLUtils.create_client_ssl_context(
                ca_cert=ca_cert_file,
                client_cert=cert_file,
                client_key=key_file,
                verify=verify_mode != "CERT_NONE",
                check_hostname=check_hostname,
            )

        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            raise
