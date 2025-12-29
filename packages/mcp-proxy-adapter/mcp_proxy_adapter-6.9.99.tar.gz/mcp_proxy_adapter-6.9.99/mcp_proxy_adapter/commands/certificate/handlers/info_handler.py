"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Handler for certificate information retrieval.
"""

from ..result import CertificateResult
from ...result import CommandResult, SuccessResult, ErrorResult
from mcp_proxy_adapter.core.certificate_utils import CertificateUtils
from mcp_proxy_adapter.core.auth_validator import AuthValidator
from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.file_utils import validate_file_exists
from mcp_proxy_adapter.core.error_handling import handle_command_errors


@handle_command_errors("Certificate info retrieval")
async def handle_info(
    certificate_utils: CertificateUtils,
    auth_validator: AuthValidator,
    cert_path: str,
) -> CommandResult:
    """
    Get detailed information about a certificate.

    Args:
        certificate_utils: CertificateUtils instance
        auth_validator: AuthValidator instance
        cert_path: Path to certificate file

    Returns:
        CommandResult with certificate information
    """
    get_global_logger().info(f"Getting certificate info: {cert_path}")

    # Validate parameters
    exists, error = validate_file_exists(cert_path, file_type="Certificate")
    if not exists:
        return error

    # Get certificate information
    cert_info = certificate_utils.get_certificate_info(cert_path)
    if not cert_info:
        return ErrorResult(message="Could not read certificate information")

    # Validate certificate
    validation = auth_validator.validate_certificate(cert_path)
    status = "valid" if validation.is_valid else "error"

    cert_result = CertificateResult(
        cert_path=cert_path,
        cert_type=cert_info.get("type", "unknown"),
        common_name=cert_info.get("common_name", ""),
        roles=cert_info.get("roles", []),
        expiry_date=cert_info.get("expiry_date"),
        serial_number=cert_info.get("serial_number"),
        status=status,
        error=None if validation.is_valid else validation.error_message,
    )

    get_global_logger().info(
        f"Certificate info retrieved successfully: {cert_path}"
    )
    return SuccessResult(
        data={
            "certificate": cert_result.to_dict(),
            "validation": {
                "is_valid": validation.is_valid,
                "error_code": validation.error_code,
                "error_message": validation.error_message,
                "roles": validation.roles,
            },
            "details": cert_info,
        }
    )

