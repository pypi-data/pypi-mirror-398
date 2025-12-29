"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Handler for client certificate creation.
"""

from typing import List

from ..result import CertificateResult
from ...result import CommandResult, SuccessResult, ErrorResult
from mcp_proxy_adapter.core.certificate_utils import CertificateUtils
from mcp_proxy_adapter.core.auth_validator import AuthValidator
from mcp_proxy_adapter.core.role_utils import RoleUtils
from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.error_handling import handle_command_errors
from .common import (
    validate_certificate_creation_params,
    validate_created_certificate,
)


@handle_command_errors("Client certificate creation")
async def handle_create_client(
    certificate_utils: CertificateUtils,
    auth_validator: AuthValidator,
    role_utils: RoleUtils,
    common_name: str,
    roles: List[str],
    ca_cert_path: str,
    ca_key_path: str,
    output_dir: str,
    validity_days: int = 365,
) -> CommandResult:
    """
    Create a client certificate signed by CA.

    Args:
        certificate_utils: CertificateUtils instance
        auth_validator: AuthValidator instance
        role_utils: RoleUtils instance
        common_name: Common name for the client certificate
        roles: List of roles to assign to the certificate
        ca_cert_path: Path to CA certificate file
        ca_key_path: Path to CA private key file
        output_dir: Directory to save certificate and key files
        validity_days: Certificate validity period in days

    Returns:
        CommandResult with client certificate creation status
    """
    get_global_logger().info(f"Creating client certificate: {common_name}")

    # Validate common parameters
    is_valid, error = validate_certificate_creation_params(
        common_name, roles, ca_cert_path, ca_key_path, role_utils
    )
    if not is_valid:
        return error

    # Get normalized roles
    normalized_roles = role_utils.normalize_roles(roles) if roles else []

    # Create client certificate with roles
    result = certificate_utils.create_client_certificate(
        common_name=common_name,
        output_dir=output_dir,
        ca_cert_path=ca_cert_path,
        ca_key_path=ca_key_path,
        validity_days=validity_days,
        roles=normalized_roles,
    )

    # Validate created certificate
    cert_path = result.get("cert_path")
    is_valid, error = validate_created_certificate(cert_path, auth_validator)
    if not is_valid:
        return error

    cert_result = CertificateResult(
        cert_path=result.get("cert_path", ""),
        cert_type="client",
        common_name=common_name,
        roles=normalized_roles,
        status="valid",
    )

    get_global_logger().info(
        f"Client certificate created successfully: {result.get('cert_path')}"
    )
    return SuccessResult(
        data={"certificate": cert_result.to_dict(), "files": result}
    )

