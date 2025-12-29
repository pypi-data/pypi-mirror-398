"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

SSL context manager for security testing.
Uses security framework through SSLUtils.
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_proxy_adapter.core.ssl_utils import SSLUtils

if TYPE_CHECKING:
    from ssl import SSLContext


class SSLContextManager:
    """Manager for SSL contexts in security testing."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize SSL context manager.

        Args:
            project_root: Root directory of the project (optional)
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent.parent
        self.project_root = project_root

    def create_server_context(
        self,
        cert_file: str,
        key_file: str,
        ca_cert: Optional[str] = None,
        verify_client: bool = False,
    ) -> "SSLContext":
        """
        Create server SSL context using security framework.

        Args:
            cert_file: Path to server certificate
            key_file: Path to server private key
            ca_cert: Optional CA certificate path
            verify_client: Require client certificates (mTLS)

        Returns:
            SSL context for server
        """
        return SSLUtils.create_ssl_context(
            cert_file=cert_file,
            key_file=key_file,
            ca_cert=ca_cert,
            verify_client=verify_client,
            min_tls_version="TLSv1.2",
        )

    def create_client_context(
        self,
        ca_cert: Optional[str] = None,
        client_cert: Optional[str] = None,
        client_key: Optional[str] = None,
        verify: bool = True,
        check_hostname: bool = True,
    ) -> "SSLContext":
        """
        Create client SSL context using security framework.

        Args:
            ca_cert: Path to CA certificate
            client_cert: Path to client certificate
            client_key: Path to client private key
            verify: Whether to verify server certificate
            check_hostname: Whether to check hostname

        Returns:
            SSL context for client
        """
        return SSLUtils.create_client_ssl_context(
            ca_cert=ca_cert,
            client_cert=client_cert,
            client_key=client_key,
            verify=verify,
            check_hostname=check_hostname,
        )


