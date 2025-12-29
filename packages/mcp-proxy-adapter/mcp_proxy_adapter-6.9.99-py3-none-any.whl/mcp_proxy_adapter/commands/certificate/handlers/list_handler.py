"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Handler for certificate listing.
"""

from pathlib import Path

from ..result import CertificateResult
from ...result import CommandResult, SuccessResult, ErrorResult
from mcp_proxy_adapter.core.certificate_utils import CertificateUtils
from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.error_handling import handle_command_errors


@handle_command_errors("Certificate listing")
async def handle_list(
    certificate_utils: CertificateUtils, cert_dir: str
) -> CommandResult:
    """
    List all certificates in a directory.

    Args:
        certificate_utils: CertificateUtils instance
        cert_dir: Directory to scan for certificates

    Returns:
        CommandResult with list of certificates
    """
    get_global_logger().info(f"Listing certificates in directory: {cert_dir}")

    # Validate parameters
    path = Path(cert_dir)
    if not path.exists():
        return ErrorResult(message=f"Directory not found: {cert_dir}")

    if not path.is_dir():
        return ErrorResult(message=f"Path is not a directory: {cert_dir}")

    # List certificates
    certificates = []
    cert_extensions = [".crt", ".pem", ".cer", ".der"]

    for file_path in path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in cert_extensions:
            try:
                cert_info = certificate_utils.get_certificate_info(str(file_path))
                if cert_info:
                    cert_result = CertificateResult(
                        cert_path=str(file_path),
                        cert_type=cert_info.get("type", "unknown"),
                        common_name=cert_info.get("common_name", ""),
                        roles=cert_info.get("roles", []),
                        expiry_date=cert_info.get("expiry_date"),
                        serial_number=cert_info.get("serial_number"),
                        status=cert_info.get("status", "valid"),
                    )
                    certificates.append(cert_result.to_dict())
            except Exception as e:
                get_global_logger().warning(
                    f"Could not read certificate {file_path}: {e}"
                )
                cert_result = CertificateResult(
                    cert_path=str(file_path),
                    cert_type="unknown",
                    common_name="",
                    status="error",
                    error=str(e),
                )
                certificates.append(cert_result.to_dict())

    get_global_logger().info(f"Found {len(certificates)} certificates in {cert_dir}")
    return SuccessResult(
        data={
            "certificates": certificates,
            "total_count": len(certificates),
            "directory": cert_dir,
        }
    )

