"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Handler for certificate auto-renewal setup.
"""

from datetime import datetime
from typing import Dict, Any

from ...result import CommandResult, SuccessResult, ErrorResult
from mcp_proxy_adapter.core.certificate_utils import CertificateUtils
from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.file_utils import validate_file_exists, ensure_directory_exists
from mcp_proxy_adapter.core.validation_utils import (
    validate_dict_not_empty,
    validate_positive_integer,
    validate_file_path,
)
from mcp_proxy_adapter.core.json_utils import save_json_file
from mcp_proxy_adapter.core.error_handling import handle_command_errors


@handle_command_errors("Auto-renewal setup")
async def handle_auto_renew(
    certificate_utils: CertificateUtils,
    cert_path: str,
    auto_renew_config: Dict[str, Any],
) -> CommandResult:
    """
    Set up certificate auto-renewal.

    Args:
        certificate_utils: CertificateUtils instance
        cert_path: Path to certificate file
        auto_renew_config: Auto-renewal configuration dictionary

    Returns:
        CommandResult with auto-renewal setup status
    """
    get_global_logger().info(
        f"Setting up certificate auto-renewal for {cert_path}"
    )

    # Check if certificate file exists
    exists, error = validate_file_exists(cert_path, file_type="Certificate")
    if not exists:
        return error

    # Validate auto-renewal configuration
    error = validate_dict_not_empty(auto_renew_config, "Auto-renewal configuration")
    if error:
        return error

    # Check if auto-renewal is disabled
    if not auto_renew_config.get("enabled", True):
        return SuccessResult(
            data={
                "monitor_result": {"auto_renewal_enabled": False},
                "message": "Auto-renewal disabled",
            }
        )

    # Validate required fields
    required_fields = ["renew_before_days", "ca_cert_path", "ca_key_path"]
    for field in required_fields:
        if field not in auto_renew_config:
            return ErrorResult(
                message=f"Missing required field in auto-renewal config: {field}"
            )

    error = validate_positive_integer(
        auto_renew_config["renew_before_days"], "Renew before days"
    )
    if error:
        return error

    # Check CA files
    ca_cert_path = auto_renew_config["ca_cert_path"]
    ca_key_path = auto_renew_config["ca_key_path"]

    exists, error = validate_file_exists(ca_cert_path, file_type="CA certificate")
    if not exists:
        return error

    exists, error = validate_file_exists(ca_key_path, file_type="CA private key")
    if not exists:
        return error

    # Check output directory
    output_dir = auto_renew_config.get("output_dir")
    error = validate_file_path(output_dir, "Output directory")
    if error:
        return error

    # Ensure output directory exists
    success, error = ensure_directory_exists(output_dir)
    if not success:
        return error

    # Test renewal configuration
    test_result = _test_renewal_config(certificate_utils, cert_path, auto_renew_config)
    if not test_result["success"]:
        return ErrorResult(
            message=f"Renewal configuration test failed: {test_result['error']}"
        )

    # Save auto-renewal configuration
    config_path = "/tmp/cert_auto_renew_config.json"
    success, error = save_json_file(auto_renew_config, config_path)
    if not success:
        return error

    get_global_logger().info(
        f"Auto-renewal configuration saved to {config_path}"
    )

    return SuccessResult(
        data={
            "monitor_result": {"auto_renewal_enabled": True},
            "auto_renew_config": auto_renew_config,
            "config_path": config_path,
            "setup_date": datetime.now().isoformat(),
            "message": "Auto-renewal configured successfully",
        }
    )


def _test_renewal_config(
    certificate_utils: CertificateUtils,
    cert_path: str,
    renewal_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Test renewal configuration.

    Args:
        certificate_utils: CertificateUtils instance
        cert_path: Path to certificate file
        renewal_config: Renewal configuration to test

    Returns:
        Test result dictionary
    """
    try:
        # Get certificate info
        cert_info = certificate_utils.get_certificate_info(cert_path)
        if not cert_info:
            return {
                "success": False,
                "error": "Could not read certificate information",
            }

        # Check CA certificate
        ca_cert_path = renewal_config.get("ca_cert_path")
        exists, _ = validate_file_exists(ca_cert_path, file_type="CA certificate", return_error=False)
        if not exists:
            return {"success": False, "error": "CA certificate not found"}

        # Check CA key
        ca_key_path = renewal_config.get("ca_key_path")
        exists, _ = validate_file_exists(ca_key_path, file_type="CA private key", return_error=False)
        if not exists:
            return {"success": False, "error": "CA private key not found"}

        # Check output directory
        output_dir = renewal_config.get("output_dir")
        if not output_dir:
            return {"success": False, "error": "Output directory must be specified"}

        # Try to ensure directory exists (will create if needed)
        success, error = ensure_directory_exists(output_dir)
        if not success:
            return {"success": False, "error": error.message if error else "Output directory not accessible"}

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}

