"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Universal authentication validator that proxies requests to specialized helpers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from mcp_proxy_adapter.core.auth import (
    AuthValidationResult,
    CertificateAuthValidator,
    MTLSValidator,
    TokenValidator,
)


class AuthValidator:
    """
    High level authentication validator used across the project.

    Delegates certificate, token and mTLS logic to dedicated helper classes.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize authentication validator with optional configuration.

        Args:
            config: Configuration dictionary controlling available modes.
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._certificate_validator = CertificateAuthValidator(logger=self.logger)
        self._token_validator = TokenValidator(logger=self.logger)
        self._mtls_validator = MTLSValidator(
            certificate_validator=self._certificate_validator,
            logger=self.logger,
        )

    def validate_certificate(
        self, cert_path: Optional[str], cert_type: str = "server"
    ) -> AuthValidationResult:
        """
        Validate certificate file.

        Args:
            cert_path: Certificate path.
            cert_type: Expected certificate type (server/client/ca).
        """
        return self._certificate_validator.validate(cert_path, cert_type)

    def validate_token(
        self, token: Optional[str], token_type: str = "jwt"
    ) -> AuthValidationResult:
        """
        Validate token input.

        Args:
            token: Token string.
            token_type: Token type (jwt/api).
        """
        return self._token_validator.validate(token, token_type)

    def validate_mtls(
        self, client_cert: Optional[str], ca_cert: Optional[str]
    ) -> AuthValidationResult:
        """
        Validate mTLS configuration.

        Args:
            client_cert: Path to client certificate.
            ca_cert: Path to CA certificate.
        """
        return self._mtls_validator.validate(client_cert, ca_cert)

    def validate_ssl(self, server_cert: Optional[str]) -> AuthValidationResult:
        """
        Validate SSL server certificate.

        Args:
            server_cert: Path to server certificate.
        """
        if not server_cert:
            return AuthValidationResult(
                is_valid=False,
                error_code=-32006,
                error_message="Server certificate required for SSL validation",
            )

        return self.validate_certificate(server_cert, "server")

    def get_validation_mode(self) -> str:
        """
        Derive validation mode from configuration.

        Returns:
            One of token/mtls/ssl/none.
        """
        ssl_config = self.config.get("ssl", {})

        if ssl_config.get("token_auth", {}).get("enabled", False):
            return "token"
        if ssl_config.get("mtls", {}).get("enabled", False):
            return "mtls"
        if ssl_config.get("enabled", False):
            return "ssl"

        return "none"

    def _get_validation_mode(self) -> str:
        """
        Backwards compatible alias for legacy callers.
        """
        return self.get_validation_mode()

    def _check_config(self, auth_type: str) -> bool:
        """
        Backwards compatible configuration guard.
        """
        ssl_config = self.config.get("ssl", {})
        if not ssl_config.get("enabled", False):
            return False

        if auth_type == "token":
            return bool(ssl_config.get("token_auth", {}).get("enabled", False))
        if auth_type == "mtls":
            return bool(ssl_config.get("mtls", {}).get("enabled", False))
        if auth_type in {"ssl", "certificate"}:
            return True

        return False
