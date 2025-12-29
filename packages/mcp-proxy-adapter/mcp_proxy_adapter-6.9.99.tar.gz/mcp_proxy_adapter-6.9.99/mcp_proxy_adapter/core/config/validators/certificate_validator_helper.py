"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Helper functions for certificate validation in config validators.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from mcp_proxy_adapter.core.certificate.certificate_validator import (
    CertificateValidator,
)
from .base_validator import ValidationError


def validate_certificate_files(
    cert_path: Optional[Path],
    key_path: Optional[Path],
    ca_cert_path: Optional[Path],
    crl_path: Optional[Path],
    cert_label: str,
    key_label: str,
    ca_label: str,
    crl_label: str,
    protocol: str,
) -> List[ValidationError]:
    """
    Validate certificate files (match, expiry, CRL, chain).
    
    Args:
        cert_path: Path to certificate file
        key_path: Path to key file
        ca_cert_path: Path to CA certificate file
        crl_path: Path to CRL file
        cert_label: Label for certificate in error messages
        key_label: Label for key in error messages
        ca_label: Label for CA in error messages
        crl_label: Label for CRL in error messages
        protocol: Protocol (http, https, mtls)
        
    Returns:
        List of validation errors
    """
    errors: List[ValidationError] = []
    
    if cert_path and key_path and cert_path.exists() and key_path.exists():
        # Check certificate-key match
        if not CertificateValidator.validate_certificate_key_match(
            str(cert_path), str(key_path)
        ):
            errors.append(
                ValidationError(f"{cert_label} does not match {key_label}")
            )
        
        # Check certificate expiry
        if not CertificateValidator.validate_certificate_not_expired(str(cert_path)):
            errors.append(ValidationError(f"{cert_label} is expired"))
        
        # Validate CRL if specified
        if crl_path and crl_path.exists():
            crl_valid, crl_error = CertificateValidator.validate_crl_file(
                str(crl_path)
            )
            if not crl_valid:
                errors.append(
                    ValidationError(f"{crl_label} validation failed: {crl_error}")
                )
            else:
                # Check if certificate is revoked according to CRL
                if not CertificateValidator.validate_certificate_not_revoked(
                    str(cert_path), str(crl_path)
                ):
                    errors.append(
                        ValidationError(
                            f"{cert_label} is revoked according to {crl_label}"
                        )
                    )
    
    # Validate certificate chain
    if cert_path and cert_path.exists():
        if ca_cert_path and ca_cert_path.exists():
            if not CertificateValidator.validate_certificate_chain(
                str(cert_path), str(ca_cert_path)
            ):
                errors.append(
                    ValidationError(f"{cert_label} is not signed by {ca_label}")
                )
        else:
            # CA not provided - for mTLS it's required
            if protocol == "mtls":
                errors.append(
                    ValidationError(f"{ca_label} is required for mtls protocol")
                )
    
    return errors

