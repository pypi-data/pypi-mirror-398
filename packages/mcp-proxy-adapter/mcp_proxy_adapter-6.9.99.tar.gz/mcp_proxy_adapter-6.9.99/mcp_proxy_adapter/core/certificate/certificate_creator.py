"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Certificate creation utilities for MCP Proxy Adapter.
All operations MUST use mcp_security_framework - no direct cryptography calls.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

# Import mcp_security_framework - REQUIRED, no fallback
try:
    from mcp_security_framework.core.cert_manager import (
        CertificateManager,
        CertificateConfig,
        CAConfig,
        ClientCertConfig,
        ServerCertConfig,
    )
except ImportError as e:
    raise RuntimeError(
        f"CRITICAL: mcp_security_framework is required but not available: {e}. "
        "Install it with: pip install mcp_security_framework>=1.2.8"
    ) from e

logger = logging.getLogger(__name__)


class CertificateCreator:
    """Creator for various types of certificates."""

    # Default certificate validity period (1 year)
    DEFAULT_VALIDITY_DAYS = 365

    # Default key size
    DEFAULT_KEY_SIZE = 2048

    @staticmethod
    def create_ca_certificate(
        common_name: str,
        output_dir: str,
        validity_days: int = DEFAULT_VALIDITY_DAYS,
        key_size: int = DEFAULT_KEY_SIZE,
    ) -> Dict[str, str]:
        """
        Create a CA certificate and private key using mcp_security_framework.

        Args:
            common_name: Common name for the CA certificate
            output_dir: Directory to save certificate and key files
            validity_days: Certificate validity period in days
            key_size: RSA key size in bits

        Returns:
            Dictionary with paths to created files

        Raises:
            ValueError: If parameters are invalid
            OSError: If files cannot be created
        """
        try:
            # Validate parameters
            if not common_name or not common_name.strip():
                raise ValueError("Common name cannot be empty")

            if validity_days <= 0:
                raise ValueError("Validity days must be positive")

            if key_size < 1024:
                raise ValueError("Key size must be at least 1024 bits")

            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Configure CA using mcp_security_framework
            ca_config = CAConfig(
                common_name=common_name,
                organization="MCP Proxy Adapter CA",
                organizational_unit="Certificate Authority",
                country="US",
                state="Default State",
                locality="Default City",
                validity_years=validity_days // 365,  # Convert days to years
                key_size=key_size,
            )

            # Create certificate manager (CA creation mode - no CA paths needed)
            cert_config = CertificateConfig(
                enabled=True,
                ca_creation_mode=True,  # Enable CA creation mode
                cert_storage_path=output_dir,
                key_storage_path=output_dir,
            )

            cert_manager = CertificateManager(cert_config)

            # Generate CA certificate
            ca_pair = cert_manager.create_root_ca(ca_config)

            return {
                "cert_path": str(ca_pair.cert_path),
                "key_path": str(ca_pair.key_path),
            }

        except Exception as e:
            logger.error(f"Failed to create CA certificate: {e}")
            raise

    @staticmethod
    def create_server_certificate(
        common_name: str,
        output_dir: str,
        ca_cert_path: str,
        ca_key_path: str,
        validity_days: int = DEFAULT_VALIDITY_DAYS,
        key_size: int = DEFAULT_KEY_SIZE,
        san_dns: Optional[List[str]] = None,
        san_ip: Optional[List[str]] = None,
        roles: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Create a server certificate signed by CA.

        Args:
            common_name: Common name for the server certificate
            output_dir: Directory to save certificate and key files
            ca_cert_path: Path to CA certificate
            ca_key_path: Path to CA private key
            validity_days: Certificate validity period in days
            key_size: RSA key size in bits
            san_dns: List of DNS names for SAN extension
            san_ip: List of IP addresses for SAN extension

        Returns:
            Dictionary with paths to created files

        Raises:
            RuntimeError: If mcp_security_framework is not available
        """
        try:
            # Validate parameters
            if not common_name or not common_name.strip():
                raise ValueError("Common name cannot be empty")

            if not Path(ca_cert_path).exists():
                raise FileNotFoundError(f"CA certificate not found: {ca_cert_path}")

            if not Path(ca_key_path).exists():
                raise FileNotFoundError(f"CA key not found: {ca_key_path}")

            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Normalize and validate roles using RoleUtils
            from ..role_utils import RoleUtils
            normalized_roles = RoleUtils.normalize_roles(roles or [])

            # Configure server certificate using mcp_security_framework
            server_config = ServerCertConfig(
                common_name=common_name,
                organization="MCP Proxy Adapter",
                organizational_unit="Server",
                country="US",
                state="Default State",
                locality="Default City",
                validity_days=validity_days,
                key_size=key_size,
                subject_alt_names=san_dns or [],
                roles=normalized_roles,  # Roles are validated and normalized by CertificateManager
                ca_cert_path=ca_cert_path,
                ca_key_path=ca_key_path,
            )

            # Create certificate manager
            cert_config = CertificateConfig(
                enabled=True,
                ca_cert_path=ca_cert_path,
                ca_key_path=ca_key_path,
                cert_storage_path=output_dir,
                key_storage_path=output_dir,
            )

            cert_manager = CertificateManager(cert_config)

            # Generate server certificate
            server_pair = cert_manager.create_server_certificate(server_config)

            return {
                "cert_path": str(server_pair.cert_path),
                "key_path": str(server_pair.key_path),
            }

        except Exception as e:
            logger.error(f"Failed to create server certificate: {e}")
            raise

    @staticmethod
    def create_client_certificate(
        common_name: str,
        output_dir: str,
        ca_cert_path: str,
        ca_key_path: str,
        validity_days: int = DEFAULT_VALIDITY_DAYS,
        key_size: int = DEFAULT_KEY_SIZE,
        roles: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Create a client certificate signed by CA using mcp_security_framework.

        Args:
            common_name: Common name for the client certificate
            output_dir: Directory to save certificate and key files
            ca_cert_path: Path to CA certificate
            ca_key_path: Path to CA private key
            validity_days: Certificate validity period in days
            key_size: RSA key size in bits
            roles: List of roles to include in certificate (validated against CertificateRole enum)

        Returns:
            Dictionary with paths to created files

        Raises:
            RuntimeError: If mcp_security_framework is not available
        """
        try:
            # Validate parameters
            if not common_name or not common_name.strip():
                raise ValueError("Common name cannot be empty")

            if not Path(ca_cert_path).exists():
                raise FileNotFoundError(f"CA certificate not found: {ca_cert_path}")

            if not Path(ca_key_path).exists():
                raise FileNotFoundError(f"CA key not found: {ca_key_path}")

            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Normalize and validate roles using RoleUtils
            from ..role_utils import RoleUtils
            normalized_roles = RoleUtils.normalize_roles(roles or [])

            # Configure client certificate using mcp_security_framework
            client_config = ClientCertConfig(
                common_name=common_name,
                organization="MCP Proxy Adapter",
                organizational_unit="Client",
                country="US",
                state="Default State",
                locality="Default City",
                validity_days=validity_days,
                key_size=key_size,
                roles=normalized_roles,  # Roles are validated and normalized by CertificateManager
                ca_cert_path=ca_cert_path,
                ca_key_path=ca_key_path,
            )

            # Create certificate manager
            cert_config = CertificateConfig(
                enabled=True,
                ca_cert_path=ca_cert_path,
                ca_key_path=ca_key_path,
                cert_storage_path=output_dir,
                key_storage_path=output_dir,
            )

            cert_manager = CertificateManager(cert_config)

            # Generate client certificate
            client_pair = cert_manager.create_client_certificate(client_config)

            return {
                "cert_path": str(client_pair.certificate_path),
                "key_path": str(client_pair.private_key_path),
            }

        except Exception as e:
            logger.error(f"Failed to create client certificate: {e}")
            raise
