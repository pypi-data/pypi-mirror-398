"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Client configuration section validator.
"""

from __future__ import annotations

from typing import List

from .base_validator import BaseValidator, ValidationError
from .ssl_validator import SSLValidator
from .certificate_validator_helper import validate_certificate_files
from ..simple_config import SimpleConfigModel


class ClientValidator(BaseValidator):
    """Validator for client configuration section."""

    def __init__(self, config_path: str | None = None):
        """Initialize client validator."""
        super().__init__(config_path)
        self.ssl_validator = SSLValidator(config_path)

    def validate(self, model: SimpleConfigModel) -> List[ValidationError]:
        """
        Validate client configuration (for connecting to external servers).
        
        Args:
            model: Configuration model
            
        Returns:
            List of validation errors for client section
        """
        errors: List[ValidationError] = []
        c = model.client
        
        if c.enabled:
            if c.protocol not in ("http", "https", "mtls"):
                errors.append(
                    ValidationError(
                        "client.protocol must be one of: http, https, mtls"
                    )
                )
            
            # Protocol-specific SSL requirements
            if c.protocol in ("https", "mtls"):
                if not c.ssl:
                    errors.append(
                        ValidationError(
                            "client.ssl is required for https/mtls protocols when enabled"
                        )
                    )
                else:
                    if c.protocol == "mtls":
                        if not c.ssl.cert:
                            errors.append(
                                ValidationError(
                                    "client.ssl.cert is required for mtls protocol when enabled"
                                )
                            )
                        if not c.ssl.key:
                            errors.append(
                                ValidationError(
                                    "client.ssl.key is required for mtls protocol when enabled"
                                )
                            )
                    elif c.protocol == "https":
                        if c.ssl.key and not c.ssl.cert:
                            errors.append(
                                ValidationError(
                                    "client.ssl.key is specified but client.ssl.cert is missing for https protocol"
                                )
                            )
                        if c.ssl.cert and not c.ssl.key:
                            errors.append(
                                ValidationError(
                                    "client.ssl.cert is specified but client.ssl.key is missing for https protocol"
                                )
                            )
                    
                    # Validate SSL files (existence, accessibility, format)
                    errors.extend(
                        self.ssl_validator.validate_ssl_files(
                            c.ssl, "client", enabled=c.enabled
                        )
                    )
            
            # Validate certificate validity if files exist
            if c.ssl:
                cert_file = c.ssl.cert
                key_file = c.ssl.key
                ca_cert_file = c.ssl.ca
                crl_file = c.ssl.crl
                
                cert_path = self._resolve_path(cert_file) if cert_file else None
                key_path = self._resolve_path(key_file) if key_file else None
                ca_cert_path = (
                    self._resolve_path(ca_cert_file) if ca_cert_file else None
                )
                crl_path = self._resolve_path(crl_file) if crl_file else None
                
                if cert_path or key_path:
                    errors.extend(
                        validate_certificate_files(
                            cert_path,
                            key_path,
                            ca_cert_path,
                            crl_path,
                            "client.ssl.cert",
                            "client.ssl.key",
                            "client.ssl.ca",
                            "client.ssl.crl",
                            c.protocol,
                        )
                    )
        
        return errors

