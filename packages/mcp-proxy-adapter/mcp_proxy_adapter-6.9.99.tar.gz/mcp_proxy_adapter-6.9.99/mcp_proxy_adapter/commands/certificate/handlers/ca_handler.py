"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Handler for CA certificate creation.
"""

from ..result import CertificateResult
from ...result import CommandResult, SuccessResult, ErrorResult
from mcp_proxy_adapter.core.certificate_utils import CertificateUtils
from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.validation_utils import (
    validate_non_empty_string,
    validate_positive_integer,
    validate_key_size,
)
from mcp_proxy_adapter.core.file_utils import validate_file_not_empty
from mcp_proxy_adapter.core.error_handling import handle_command_errors


@handle_command_errors("CA certificate creation")
async def handle_create_ca(
    certificate_utils: CertificateUtils,
    common_name: str,
    output_dir: str,
    validity_days: int = 365,
    key_size: int = 2048,
) -> CommandResult:
    """
    Create a CA certificate and private key.

    Args:
        certificate_utils: CertificateUtils instance
        common_name: Common name for the CA certificate
        output_dir: Directory to save certificate and key files
        validity_days: Certificate validity period in days
        key_size: RSA key size in bits

    Returns:
        CommandResult with CA certificate creation status
    """
    get_global_logger().info(f"Creating CA certificate: {common_name}")

    # Validate parameters
    error = validate_non_empty_string(common_name, "Common name")
    if error:
        return error

    error = validate_positive_integer(validity_days, "Validity days")
    if error:
        return error

    error = validate_key_size(key_size)
    if error:
        return error

    # Create CA certificate
    result = certificate_utils.create_ca_certificate(
        common_name, output_dir, validity_days, key_size
    )

    # Validate created certificate
    cert_path = result.get("cert_path")
    if cert_path:
        is_valid, error = validate_file_not_empty(cert_path)
        if not is_valid:
            return error or ErrorResult(
                message="Created CA certificate file validation failed"
            )

    cert_result = CertificateResult(
        cert_path=result.get("cert_path", ""),
        cert_type="CA",
        common_name=common_name,
        status="valid",
    )

    get_global_logger().info(
        f"CA certificate created successfully: {result.get('cert_path')}"
    )
    return SuccessResult(
        data={"certificate": cert_result.to_dict(), "files": result}
    )

