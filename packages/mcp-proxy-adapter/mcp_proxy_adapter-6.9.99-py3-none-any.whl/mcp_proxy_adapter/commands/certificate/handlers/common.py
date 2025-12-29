"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Common utilities for certificate handlers.
"""

from typing import List, Tuple

from ...result import CommandResult, ErrorResult
from mcp_proxy_adapter.core.certificate_utils import CertificateUtils
from mcp_proxy_adapter.core.auth_validator import AuthValidator
from mcp_proxy_adapter.core.role_utils import RoleUtils
from mcp_proxy_adapter.core.validation_utils import validate_non_empty_string
from mcp_proxy_adapter.core.file_utils import validate_file_exists


def validate_certificate_creation_params(
    common_name: str,
    roles: List[str],
    ca_cert_path: str,
    ca_key_path: str,
    role_utils: RoleUtils,
) -> Tuple[bool, ErrorResult]:
    """
    Validate common parameters for certificate creation.

    Args:
        common_name: Common name for certificate
        roles: List of roles
        ca_cert_path: Path to CA certificate
        ca_key_path: Path to CA key
        role_utils: RoleUtils instance

    Returns:
        Tuple of (is_valid, error_result)
    """
    # Validate common name
    error = validate_non_empty_string(common_name, "Common name")
    if error:
        return False, error

    # Normalize and validate roles
    normalized_roles = role_utils.normalize_roles(roles) if roles else []
    if not normalized_roles:
        return False, ErrorResult(
            message="No valid roles specified after normalization"
        )

    # Check CA files
    exists, error = validate_file_exists(ca_cert_path, file_type="CA certificate")
    if not exists:
        return False, error

    exists, error = validate_file_exists(ca_key_path, file_type="CA private key")
    if not exists:
        return False, error

    return True, None


def validate_created_certificate(
    cert_path: str,
    auth_validator: AuthValidator,
) -> Tuple[bool, ErrorResult]:
    """
    Validate created certificate.

    Args:
        cert_path: Path to created certificate
        auth_validator: AuthValidator instance

    Returns:
        Tuple of (is_valid, error_result)
    """
    if not cert_path:
        return True, None  # No validation needed if path not provided

    exists, error = validate_file_exists(cert_path, file_type="Certificate")
    if not exists:
        return True, None  # File doesn't exist yet, skip validation

    validation = auth_validator.validate_certificate(cert_path)
    if not validation.is_valid:
        return False, ErrorResult(
            message=f"Created certificate validation failed: {validation.error_message}"
        )

    return True, None

