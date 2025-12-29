"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Handler for certificate expiry checking.
"""

from ...result import CommandResult, SuccessResult, ErrorResult
from mcp_proxy_adapter.core.certificate_utils import CertificateUtils
from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.file_utils import validate_file_exists
from mcp_proxy_adapter.core.date_utils import determine_expiry_status, calculate_days_until_expiry
from mcp_proxy_adapter.core.error_handling import handle_command_errors


@handle_command_errors("Certificate expiry check")
async def handle_expiry_check(
    certificate_utils: CertificateUtils,
    cert_path: str,
    warning_days: int = 30,
    critical_days: int = 7,
) -> CommandResult:
    """
    Check certificate expiry date.

    Args:
        certificate_utils: CertificateUtils instance
        cert_path: Path to certificate file
        warning_days: Days before expiry to start warning
        critical_days: Days before expiry for critical status

    Returns:
        CommandResult with expiry check results
    """
    get_global_logger().info(
        f"Performing certificate expiry check for {cert_path}"
    )

    # Check if certificate file exists
    exists, error = validate_file_exists(cert_path, file_type="Certificate")
    if not exists:
        return error

    # Get certificate info
    cert_info = certificate_utils.get_certificate_info(cert_path)
    if not cert_info:
        return ErrorResult(message="Could not read certificate information")

    expiry_date = cert_info.get("expiry_date")
    if not expiry_date:
        return ErrorResult(
            message="Could not determine certificate expiry date"
        )

    # Calculate days until expiry and determine status
    days_until_expiry, error = calculate_days_until_expiry(expiry_date)
    if error:
        return ErrorResult(message=error)

    status, days, error = determine_expiry_status(
        expiry_date, warning_days, critical_days
    )
    if error:
        return ErrorResult(message=error)

    is_expired = days_until_expiry < 0 if days_until_expiry is not None else False

    get_global_logger().info(
        f"Certificate expiry check completed: {status} ({days_until_expiry} days)"
    )

    return SuccessResult(
        data={
            "monitor_result": {
                "is_expired": is_expired,
                "health_status": status,
                "days_until_expiry": days_until_expiry,
                "expiry_date": expiry_date,
                "warning_days": warning_days,
                "critical_days": critical_days,
            }
        }
    )

