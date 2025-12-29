"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Main certificate utilities for MCP Proxy Adapter.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .certificate.certificate_creator import CertificateCreator
from .certificate.certificate_validator import CertificateValidator
from .certificate.certificate_extractor import CertificateExtractor
from .certificate.ssl_context_manager import SSLContextManager

logger = logging.getLogger(__name__)


class CertificateUtils:
    """
    Main utilities for working with certificates.

    Provides methods for creating CA, server, and client certificates,
    as well as validation and role extraction using mcp_security_framework.
    """

    # Default certificate validity period (1 year)
    DEFAULT_VALIDITY_DAYS = 365

    # Default key size
    DEFAULT_KEY_SIZE = 2048

    # Custom OID for roles (same as in RoleUtils)
    ROLE_EXTENSION_OID = "1.3.6.1.4.1.99999.1"

    @staticmethod
    def create_ca_certificate(
        common_name: str,
        output_dir: str,
        validity_days: int = DEFAULT_VALIDITY_DAYS,
        key_size: int = DEFAULT_KEY_SIZE,
    ) -> Dict[str, str]:
        """
        Create a CA certificate and private key.

        Args:
            common_name: Common name for the CA certificate
            output_dir: Directory to save certificate and key files
            validity_days: Certificate validity period in days
            key_size: RSA key size in bits

        Returns:
            Dictionary with paths to created files
        """
        return CertificateCreator.create_ca_certificate(
            common_name, output_dir, validity_days, key_size
        )

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
            roles: List of roles to include in certificate

        Returns:
            Dictionary with paths to created files
        """
        return CertificateCreator.create_server_certificate(
            common_name, output_dir, ca_cert_path, ca_key_path,
            validity_days, key_size, san_dns, san_ip, roles
        )

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
        Create a client certificate signed by CA.

        Args:
            common_name: Common name for the client certificate
            output_dir: Directory to save certificate and key files
            ca_cert_path: Path to CA certificate
            ca_key_path: Path to CA private key
            validity_days: Certificate validity period in days
            key_size: RSA key size in bits
            roles: List of roles to include in certificate

        Returns:
            Dictionary with paths to created files
        """
        return CertificateCreator.create_client_certificate(
            common_name, output_dir, ca_cert_path, ca_key_path,
            validity_days, key_size, roles
        )

    @staticmethod
    def extract_roles_from_certificate(cert_path: str) -> List[str]:
        """
        Extract roles from certificate.

        Args:
            cert_path: Path to certificate file

        Returns:
            List of roles found in certificate
        """
        return CertificateExtractor.extract_roles_from_certificate(cert_path)

    @staticmethod
    def extract_roles_from_certificate_object(cert) -> List[str]:
        """
        Extract roles from certificate object.

        Args:
            cert: Certificate object

        Returns:
            List of roles found in certificate
        """
        return CertificateExtractor.extract_roles_from_certificate_object(cert)

    @staticmethod
    def extract_permissions_from_certificate(cert_path: str) -> List[str]:
        """
        Extract permissions from certificate.

        Args:
            cert_path: Path to certificate file

        Returns:
            List of permissions found in certificate
        """
        return CertificateExtractor.extract_permissions_from_certificate(cert_path)

    @staticmethod
    def validate_certificate_chain(cert_path: str, ca_cert_path: str) -> bool:
        """
        Validate certificate chain.

        Args:
            cert_path: Path to certificate file
            ca_cert_path: Path to CA certificate file

        Returns:
            True if certificate chain is valid, False otherwise
        """
        return CertificateValidator.validate_certificate_chain(cert_path, ca_cert_path)

    @staticmethod
    def get_certificate_expiry(cert_path: str) -> Optional[datetime]:
        """
        Get certificate expiry date.

        Args:
            cert_path: Path to certificate file

        Returns:
            Certificate expiry date or None if error
        """
        return CertificateValidator.get_certificate_expiry(cert_path)

    @staticmethod
    def validate_certificate(cert_path: str) -> bool:
        """
        Validate certificate file.

        Args:
            cert_path: Path to certificate file

        Returns:
            True if certificate is valid, False otherwise
        """
        return CertificateValidator.validate_certificate(cert_path)

    @staticmethod
    def get_certificate_info(cert_path: str) -> Dict[str, Any]:
        """
        Get certificate information.

        Args:
            cert_path: Path to certificate file

        Returns:
            Dictionary with certificate information
        """
        return CertificateValidator.get_certificate_info(cert_path)

    @staticmethod
    def validate_private_key(key_path: str) -> Dict[str, Any]:
        """
        Validate private key file.

        Args:
            key_path: Path to private key file

        Returns:
            Dictionary with validation results
        """
        return CertificateValidator.validate_private_key(key_path)

    @staticmethod
    def create_ssl_context(
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
        verify_mode: int = 0,  # ssl.CERT_NONE
        check_hostname: bool = False,
    ) -> Any:
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
        return SSLContextManager.create_ssl_context(
            cert_file, key_file, ca_cert_file, verify_mode, check_hostname
        )
