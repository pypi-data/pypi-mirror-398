"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Certificate validation helpers for MCP Proxy Adapter autentcation layer.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Optional, cast

from cryptography import x509

from mcp_proxy_adapter.core.certificate.certificate_validator import CertificateValidator

from .models import AuthValidationResult


class CertificateAuthValidator:
    """
    Validates certificates for different contexts (server, client, CA).
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def validate(self, cert_path: Optional[str], cert_type: str = "server") -> AuthValidationResult:
        """
        Validate certificate path and contents.

        Args:
            cert_path: Certificate path on disk.
            cert_type: One of server/client/ca.
        """
        try:
            if not cert_path:
                return self._missing_cert_result("Certificate path not provided")

            if not os.path.exists(cert_path):
                return self._missing_cert_result(f"Certificate file not found: {cert_path}")

            cert = self._load_certificate(cert_path)
            if not self._is_certificate_valid_now(cert):
                return AuthValidationResult(
                    is_valid=False,
                    error_code=-32008,
                    error_message="Certificate has expired",
                )

            roles = self._extract_roles_from_certificate(cert)

            if cert_type == "server" and not self._validate_server_certificate(cert):
                return self._invalid_cert_result("Invalid server certificate")
            if cert_type == "client" and not self._validate_client_certificate(cert):
                return self._invalid_cert_result("Invalid client certificate")
            if cert_type == "ca":
                # Validate CA certificate using existing validator utilities
                if not CertificateValidator.validate_certificate_not_expired(cert_path):
                    return self._invalid_cert_result("CA certificate expired")

            return AuthValidationResult(is_valid=True, roles=roles)
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("Certificate validation error: %s", exc)
            return AuthValidationResult(
                is_valid=False,
                error_code=-32003,
                error_message=f"Certificate validation failed: {exc}",
            )

    def _load_certificate(self, cert_path: str) -> x509.Certificate:
        with open(cert_path, "rb") as file:
            return x509.load_pem_x509_certificate(file.read())

    def _is_certificate_valid_now(self, cert: x509.Certificate) -> bool:
        now = datetime.utcnow()
        return cert.not_valid_before <= now <= cert.not_valid_after

    def _missing_cert_result(self, message: str) -> AuthValidationResult:
        return AuthValidationResult(
            is_valid=False,
            error_code=-32009,
            error_message=message,
        )

    def _invalid_cert_result(self, message: str) -> AuthValidationResult:
        return AuthValidationResult(
            is_valid=False,
            error_code=-32003,
            error_message=message,
        )

    def _extract_roles_from_certificate(self, cert: x509.Certificate) -> List[str]:
        try:
            from mcp_security_framework.utils.cert_utils import extract_roles_from_certificate
            from cryptography.hazmat.primitives import serialization

            cert_pem = cert.public_bytes(serialization.Encoding.PEM)
            roles = cast(
                List[str],
                extract_roles_from_certificate(cert_pem, validate=True),
            )
            return roles

        except ImportError as exc:
            raise RuntimeError(
                "CRITICAL: mcp_security_framework is required but not available."
            ) from exc
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("Failed to extract roles from certificate: %s", exc)
            from mcp_security_framework.schemas.models import CertificateRole

            return [CertificateRole.get_default_role().value]

    def _validate_server_certificate(self, cert: x509.Certificate) -> bool:
        try:
            for extension in cert.extensions:
                if extension.oid == x509.oid.ExtensionOID.KEY_USAGE:
                    key_usage = extension.value
                    return bool(key_usage.digital_signature and key_usage.key_encipherment)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("Server certificate validation error: %s", exc)
            return False

    def _validate_client_certificate(self, cert: x509.Certificate) -> bool:
        try:
            for extension in cert.extensions:
                if extension.oid == x509.oid.ExtensionOID.EXTENDED_KEY_USAGE:
                    extended_key_usage = extension.value
                    return x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH in extended_key_usage
            return True
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("Client certificate validation error: %s", exc)
            return False
