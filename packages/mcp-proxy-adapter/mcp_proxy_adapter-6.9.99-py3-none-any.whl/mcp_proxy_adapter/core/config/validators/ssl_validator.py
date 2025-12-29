"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

SSL files validation for certificates and keys.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Any

from .base_validator import BaseValidator, ValidationError


class SSLValidator(BaseValidator):
    """Validator for SSL certificate and key files."""

    def _validate_certificate_file_format(
        self, file_path: Path, label: str
    ) -> List[ValidationError]:
        """
        Validate certificate file format (PEM or DER).
        
        Args:
            file_path: Path to certificate file
            label: Label for error messages
            
        Returns:
            List of validation errors
        """
        errors: List[ValidationError] = []
        try:
            with file_path.open("rb") as f:
                content = f.read()
                # Check if it's PEM format (starts with -----BEGIN)
                if content.startswith(b"-----BEGIN"):
                    # Try to load as PEM using cryptography library
                    try:
                        from cryptography import x509
                        from cryptography.hazmat.backends import default_backend
                        # Try to parse PEM certificate
                        x509.load_pem_x509_certificate(content, default_backend())
                    except Exception:
                        errors.append(
                            ValidationError(
                                f"{label} is not a valid PEM certificate file: {file_path}"
                            )
                        )
                # Check if it's DER format (binary - ASN.1 SEQUENCE)
                elif content.startswith(b"\x30"):
                    # DER format - try to parse
                    try:
                        from cryptography import x509
                        from cryptography.hazmat.backends import default_backend
                        x509.load_der_x509_certificate(content, default_backend())
                    except Exception:
                        errors.append(
                            ValidationError(
                                f"{label} is not a valid DER certificate file: {file_path}"
                            )
                        )
                else:
                    errors.append(
                        ValidationError(
                            f"{label} is not in valid PEM or DER format: {file_path}"
                        )
                    )
        except Exception as e:
            errors.append(
                ValidationError(f"Failed to read {label}: {file_path} - {str(e)}")
            )
        return errors

    def _validate_key_file_format(
        self, file_path: Path, label: str
    ) -> List[ValidationError]:
        """
        Validate key file format (PEM or DER).
        
        Args:
            file_path: Path to key file
            label: Label for error messages
            
        Returns:
            List of validation errors
        """
        errors: List[ValidationError] = []
        try:
            with file_path.open("rb") as f:
                content = f.read()
                # Check if it's PEM format (starts with -----BEGIN)
                if content.startswith(b"-----BEGIN"):
                    # Valid PEM key format
                    pass
                # Check if it's DER format (binary)
                elif content.startswith(b"\x30") or content.startswith(b"\x02"):
                    # DER format - valid
                    pass
                else:
                    errors.append(
                        ValidationError(
                            f"{label} is not in valid PEM or DER format: {file_path}"
                        )
                    )
        except Exception as e:
            errors.append(
                ValidationError(f"Failed to read {label}: {file_path} - {str(e)}")
            )
        return errors

    def validate_ssl_files(
        self, ssl_config: Any, section_name: str, enabled: bool = True
    ) -> List[ValidationError]:
        """
        Validate SSL certificate files existence, accessibility and format.
        
        Args:
            ssl_config: SSL configuration object
            section_name: Name of the section (for error messages)
            enabled: Whether the section is enabled (if False, skip validation)
            
        Returns:
            List of validation errors
        """
        errors: List[ValidationError] = []
        
        # Skip validation if section is disabled
        if not enabled:
            return errors
        
        if not ssl_config:
            return errors
        
        # Validate certificate file
        if ssl_config.cert:
            cert_path = self._resolve_path(ssl_config.cert)
            if cert_path:
                if not cert_path.exists():
                    errors.append(
                        ValidationError(
                            f"{section_name}.ssl.cert file not found: {cert_path}"
                        )
                    )
                elif not os.access(cert_path, os.R_OK):
                    errors.append(
                        ValidationError(
                            f"{section_name}.ssl.cert file is not readable: {cert_path}"
                        )
                    )
                else:
                    # Validate format
                    errors.extend(
                        self._validate_certificate_file_format(
                            cert_path, f"{section_name}.ssl.cert"
                        )
                    )
        
        # Validate key file
        if ssl_config.key:
            key_path = self._resolve_path(ssl_config.key)
            if key_path:
                if not key_path.exists():
                    errors.append(
                        ValidationError(
                            f"{section_name}.ssl.key file not found: {key_path}"
                        )
                    )
                elif not os.access(key_path, os.R_OK):
                    errors.append(
                        ValidationError(
                            f"{section_name}.ssl.key file is not readable: {key_path}"
                        )
                    )
                else:
                    # Validate format
                    errors.extend(
                        self._validate_key_file_format(
                            key_path, f"{section_name}.ssl.key"
                        )
                    )
        
        # Validate CA certificate file
        if ssl_config.ca:
            ca_path = self._resolve_path(ssl_config.ca)
            if ca_path:
                if not ca_path.exists():
                    errors.append(
                        ValidationError(
                            f"{section_name}.ssl.ca file not found: {ca_path}"
                        )
                    )
                elif not os.access(ca_path, os.R_OK):
                    errors.append(
                        ValidationError(
                            f"{section_name}.ssl.ca file is not readable: {ca_path}"
                        )
                    )
                else:
                    # Validate format
                    errors.extend(
                        self._validate_certificate_file_format(
                            ca_path, f"{section_name}.ssl.ca"
                        )
                    )
        
        # Validate CRL file
        if ssl_config.crl:
            crl_path = self._resolve_path(ssl_config.crl)
            if crl_path:
                if not crl_path.exists():
                    errors.append(
                        ValidationError(
                            f"{section_name}.ssl.crl file not found: {crl_path}"
                        )
                    )
                elif not os.access(crl_path, os.R_OK):
                    errors.append(
                        ValidationError(
                            f"{section_name}.ssl.crl file is not readable: {crl_path}"
                        )
                    )
        
        return errors

