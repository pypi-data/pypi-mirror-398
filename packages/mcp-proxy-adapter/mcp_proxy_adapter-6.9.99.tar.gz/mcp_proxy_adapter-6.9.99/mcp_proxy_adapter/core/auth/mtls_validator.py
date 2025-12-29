"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

mTLS validation helpers for MCP Proxy Adapter.
"""

from __future__ import annotations

import logging
from typing import Optional

from mcp_proxy_adapter.core.certificate.certificate_validator import CertificateValidator

from .certificate_validator import CertificateAuthValidator
from .models import AuthValidationResult


class MTLSValidator:
    """Encapsulates mTLS validation logic."""

    def __init__(
        self,
        certificate_validator: Optional[CertificateAuthValidator] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._certificate_validator = certificate_validator or CertificateAuthValidator(
            logger=self._logger
        )

    def validate(self, client_cert: Optional[str], ca_cert: Optional[str]) -> AuthValidationResult:
        """
        Validate mTLS inputs.

        Args:
            client_cert: Path to client certificate.
            ca_cert: Path to CA certificate.
        """
        try:
            if not client_cert or not ca_cert:
                return AuthValidationResult(
                    is_valid=False,
                    error_code=-32005,
                    error_message="Client certificate and CA certificate required for mTLS",
                )

            client_result = self._certificate_validator.validate(client_cert, "client")
            if not client_result.is_valid:
                return client_result

            ca_result = self._certificate_validator.validate(ca_cert, "ca")
            if not ca_result.is_valid:
                return ca_result

            if not CertificateValidator.validate_certificate_chain(client_cert, ca_cert):
                return AuthValidationResult(
                    is_valid=False,
                    error_code=-32005,
                    error_message="Client certificate not signed by provided CA",
                )

            return AuthValidationResult(is_valid=True, roles=client_result.roles)

        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("mTLS validation error: %s", exc)
            return AuthValidationResult(
                is_valid=False,
                error_code=-32005,
                error_message=f"mTLS validation failed: {exc}",
            )
