"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Handler for certificate revocation.
"""

from ..result import CertificateResult
from ...result import CommandResult, SuccessResult, ErrorResult
from mcp_proxy_adapter.core.certificate_utils import CertificateUtils
from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.file_utils import validate_file_exists
from mcp_proxy_adapter.core.error_handling import handle_command_errors


@handle_command_errors("Certificate revocation")
async def handle_revoke(
    certificate_utils: CertificateUtils, cert_path: str
) -> CommandResult:
    """
    Revoke a certificate.

    Args:
        certificate_utils: CertificateUtils instance
        cert_path: Path to certificate file to revoke

    Returns:
        CommandResult with revocation status
    """
    get_global_logger().info(f"Revoking certificate: {cert_path}")

    # Validate parameters
    exists, error = validate_file_exists(cert_path, file_type="Certificate")
    if not exists:
        return error

    # Get certificate info before revocation
    cert_info = certificate_utils.get_certificate_info(cert_path)
    if not cert_info:
        return ErrorResult(message="Could not read certificate information")

    # Revoke certificate
    result = certificate_utils.revoke_certificate(cert_path)

    cert_result = CertificateResult(
        cert_path=cert_path,
        cert_type=cert_info.get("type", "unknown"),
        common_name=cert_info.get("common_name", ""),
        roles=cert_info.get("roles", []),
        serial_number=cert_info.get("serial_number"),
        status="revoked",
    )

    get_global_logger().info(f"Certificate revoked successfully: {cert_path}")
    return SuccessResult(
        data={"certificate": cert_result.to_dict(), "revocation_result": result}
    )

