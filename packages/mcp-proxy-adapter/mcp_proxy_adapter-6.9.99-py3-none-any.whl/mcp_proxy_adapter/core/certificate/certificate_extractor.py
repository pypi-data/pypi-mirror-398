"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Certificate information extraction utilities for MCP Proxy Adapter.
All operations MUST use mcp_security_framework - no direct cryptography calls.
"""

import logging
from typing import List

# Import mcp_security_framework - REQUIRED, no fallback
try:
    from mcp_security_framework.utils.cert_utils import (
        extract_roles_from_certificate,
        extract_permissions_from_certificate,
    )
except ImportError as e:
    raise RuntimeError(
        f"CRITICAL: mcp_security_framework is required but not available: {e}. "
        "Install it with: pip install mcp_security_framework>=1.2.8"
    ) from e

logger = logging.getLogger(__name__)


class CertificateExtractor:
    """Extractor for certificate information."""

    # Custom OID for roles (matches mcp_security_framework)
    ROLE_EXTENSION_OID = "1.3.6.1.4.1.99999.1.1"

    @staticmethod
    def extract_roles_from_certificate(cert_path: str, validate: bool = True) -> List[str]:
        """
        Extract roles from certificate using mcp_security_framework.

        Args:
            cert_path: Path to certificate file
            validate: Whether to validate roles against CertificateRole enum (default: True)

        Returns:
            List of roles found in certificate (validated and normalized if validate=True)

        Raises:
            RuntimeError: If mcp_security_framework is not available
        """
        try:
            # Use framework method with validation enabled by default
            return extract_roles_from_certificate(cert_path, validate=validate)
        except Exception as e:
            logger.error(f"Failed to extract roles from certificate: {e}")
            # Return default role if validation is enabled and extraction failed
            if validate:
                from mcp_security_framework.schemas.models import CertificateRole
                return [CertificateRole.get_default_role().value]
            return []

    @staticmethod
    def extract_roles_from_certificate_object(cert, validate: bool = True) -> List[str]:
        """
        Extract roles from certificate object using mcp_security_framework.

        Args:
            cert: Certificate object (must have public_bytes method)
            validate: Whether to validate roles against CertificateRole enum (default: True)

        Returns:
            List of roles found in certificate (validated and normalized if validate=True)

        Raises:
            RuntimeError: If mcp_security_framework is not available
        """
        try:
            # Convert certificate object to bytes for framework method
            # Note: cert must be a cryptography x509.Certificate object
            from cryptography.hazmat.primitives import serialization
            cert_pem = cert.public_bytes(serialization.Encoding.PEM)
            # Use framework method with validation
            return extract_roles_from_certificate(cert_pem, validate=validate)
        except Exception as e:
            logger.error(f"Failed to extract roles from certificate object: {e}")
            # Return default role if validation is enabled and extraction failed
            if validate:
                from mcp_security_framework.schemas.models import CertificateRole
                return [CertificateRole.get_default_role().value]
            return []

    @staticmethod
    def extract_permissions_from_certificate(cert_path: str) -> List[str]:
        """
        Extract permissions from certificate using mcp_security_framework.

        Args:
            cert_path: Path to certificate file

        Returns:
            List of permissions found in certificate

        Raises:
            RuntimeError: If mcp_security_framework is not available
        """
        try:
            return extract_permissions_from_certificate(cert_path)
        except Exception as e:
            logger.error(f"Failed to extract permissions from certificate: {e}")
            return []
