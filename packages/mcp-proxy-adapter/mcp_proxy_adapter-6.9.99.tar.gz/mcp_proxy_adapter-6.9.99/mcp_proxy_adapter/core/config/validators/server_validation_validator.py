"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Server validation configuration section validator.
"""

from __future__ import annotations

from typing import List

from .base_validator import BaseValidator, ValidationError
from .ssl_validator import SSLValidator
from .certificate_validator_helper import validate_certificate_files
from ..simple_config import SimpleConfigModel


class ServerValidationValidator(BaseValidator):
    """Validator for server_validation configuration section."""

    def __init__(self, config_path: str | None = None):
        """Initialize server validation validator."""
        super().__init__(config_path)
        self.ssl_validator = SSLValidator(config_path)

    def validate(self, model: SimpleConfigModel) -> List[ValidationError]:
        """
        Validate server_validation configuration (used by proxy to verify adapter).
        
        Args:
            model: Configuration model
            
        Returns:
            List of validation errors for server_validation section
        """
        errors: List[ValidationError] = []
        sv = model.server_validation
        
        if not isinstance(sv.check_hostname, bool):
            errors.append(
                ValidationError("server_validation.check_hostname must be boolean")
            )
        
        # Validate SSL files if server_validation is enabled
        if sv.enabled:
            if sv.protocol not in ("http", "https", "mtls"):
                errors.append(
                    ValidationError(
                        "server_validation.protocol must be one of: http, https, mtls"
                    )
                )
            
            # Protocol-specific SSL requirements
            if sv.protocol in ("https", "mtls"):
                if not sv.ssl:
                    errors.append(
                        ValidationError(
                            "server_validation.ssl is required for https/mtls protocols when enabled"
                        )
                    )
                else:
                    if sv.protocol == "mtls":
                        if not sv.ssl.cert:
                            errors.append(
                                ValidationError(
                                    "server_validation.ssl.cert is required for mtls protocol when enabled"
                                )
                            )
                        if not sv.ssl.key:
                            errors.append(
                                ValidationError(
                                    "server_validation.ssl.key is required for mtls protocol when enabled"
                                )
                            )
                        if not sv.ssl.ca:
                            errors.append(
                                ValidationError(
                                    "server_validation.ssl.ca is required for mtls protocol when enabled"
                                )
                            )
                    elif sv.protocol == "https":
                        if sv.ssl.key and not sv.ssl.cert:
                            errors.append(
                                ValidationError(
                                    "server_validation.ssl.key is specified but server_validation.ssl.cert is missing for https protocol"
                                )
                            )
                        if sv.ssl.cert and not sv.ssl.key:
                            errors.append(
                                ValidationError(
                                    "server_validation.ssl.cert is specified but server_validation.ssl.key is missing for https protocol"
                                )
                            )
                    
                    # Validate SSL files (existence, accessibility, format)
                    errors.extend(
                        self.ssl_validator.validate_ssl_files(
                            sv.ssl, "server_validation", enabled=sv.enabled
                        )
                    )
                    
                    # Validate certificate validity if files exist
                    if sv.ssl and sv.ssl.cert and sv.ssl.key:
                        cert_file = sv.ssl.cert
                        key_file = sv.ssl.key
                        ca_cert_file = sv.ssl.ca
                        crl_file = sv.ssl.crl
                        
                        cert_path = (
                            self._resolve_path(cert_file) if cert_file else None
                        )
                        key_path = self._resolve_path(key_file) if key_file else None
                        ca_cert_path = (
                            self._resolve_path(ca_cert_file) if ca_cert_file else None
                        )
                        crl_path = (
                            self._resolve_path(crl_file) if crl_file else None
                        )
                        
                        if cert_path or key_path:
                            errors.extend(
                                validate_certificate_files(
                                    cert_path,
                                    key_path,
                                    ca_cert_path,
                                    crl_path,
                                    "server_validation.ssl.cert",
                                    "server_validation.ssl.key",
                                    "server_validation.ssl.ca",
                                    "server_validation.ssl.crl",
                                    sv.protocol,
                                )
                            )
        
        return errors

