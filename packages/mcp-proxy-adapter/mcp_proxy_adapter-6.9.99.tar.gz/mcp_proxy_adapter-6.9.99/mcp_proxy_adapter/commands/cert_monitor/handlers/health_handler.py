"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Handler for certificate health checking.
"""

from ...result import CommandResult, SuccessResult, ErrorResult
from mcp_proxy_adapter.core.certificate_utils import CertificateUtils
from mcp_proxy_adapter.core.auth_validator import AuthValidator
from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.file_utils import validate_file_exists
from mcp_proxy_adapter.core.date_utils import calculate_days_until_expiry
from mcp_proxy_adapter.core.error_handling import handle_command_errors


@handle_command_errors("Certificate health check")
async def handle_health_check(
    certificate_utils: CertificateUtils,
    auth_validator: AuthValidator,
    cert_path: str,
) -> CommandResult:
    """
    Perform comprehensive health check on certificate.

    Args:
        certificate_utils: CertificateUtils instance
        auth_validator: AuthValidator instance
        cert_path: Path to certificate file

    Returns:
        CommandResult with health check results
    """
    get_global_logger().info(
        f"Performing certificate health check for {cert_path}"
    )

    # Check if certificate file exists
    exists, error = validate_file_exists(cert_path, file_type="Certificate")
    if not exists:
        return error

    # Get certificate info
    cert_info = certificate_utils.get_certificate_info(cert_path)
    if not cert_info:
        return ErrorResult(message="Could not read certificate information")

    # Validate certificate
    validation = auth_validator.validate_certificate(cert_path)

    # Calculate health score
    health_score = 100
    alerts = []

    # Check if certificate is valid
    if not validation.is_valid:
        health_score -= 50
        alerts.append(
            f"Certificate validation failed: {validation.error_message}"
        )

    # Check expiry
    expiry_date = cert_info.get("expiry_date")
    if expiry_date:
        days_until_expiry, error = calculate_days_until_expiry(expiry_date)
        if error:
            health_score -= 10
            alerts.append("Invalid expiry date format")
        elif days_until_expiry is not None:
            if days_until_expiry < 0:
                health_score -= 30
                alerts.append("Certificate has expired")
            elif days_until_expiry <= 7:
                health_score -= 20
                alerts.append(
                    f"Certificate expires in {days_until_expiry} days"
                )
            elif days_until_expiry <= 30:
                health_score -= 10
                alerts.append(
                    f"Certificate expires in {days_until_expiry} days"
                )

    # Check key strength
    key_size = cert_info.get("key_size", 0)
    if key_size < 2048:
        health_score -= 15
        alerts.append(
            f"Key size {key_size} bits is below recommended 2048 bits"
        )

    # Determine overall status
    if health_score >= 80:
        overall_status = "healthy"
    elif health_score >= 50:
        overall_status = "warning"
    else:
        overall_status = "critical"

    get_global_logger().info(
        f"Certificate health check completed: {overall_status} (score: {health_score})"
    )

    return SuccessResult(
        data={
            "monitor_result": {
                "health_score": health_score,
                "alerts": alerts,
                "expiry_date": expiry_date,
            },
            "health_checks": {"validation": {"passed": validation.is_valid}},
            "overall_status": overall_status,
        }
    )

