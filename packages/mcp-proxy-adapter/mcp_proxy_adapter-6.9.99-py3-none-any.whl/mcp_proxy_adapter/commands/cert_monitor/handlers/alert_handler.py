"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Handler for certificate alert setup.
"""

from datetime import datetime
from typing import Dict, Any

from ...result import CommandResult, SuccessResult, ErrorResult
from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.file_utils import validate_file_exists
from mcp_proxy_adapter.core.validation_utils import (
    validate_dict_not_empty,
    validate_positive_integer,
    validate_days_comparison,
    validate_list_not_empty,
)
from mcp_proxy_adapter.core.json_utils import save_json_file
from mcp_proxy_adapter.core.error_handling import handle_command_errors


@handle_command_errors("Alert setup")
async def handle_alert_setup(
    cert_path: str, alert_config: Dict[str, Any]
) -> CommandResult:
    """
    Set up certificate monitoring alerts.

    Args:
        cert_path: Path to certificate file
        alert_config: Alert configuration dictionary

    Returns:
        CommandResult with alert setup status
    """
    get_global_logger().info(
        f"Setting up certificate monitoring alerts for {cert_path}"
    )

    # Check if certificate file exists
    exists, error = validate_file_exists(cert_path, file_type="Certificate")
    if not exists:
        return error

    # Validate alert configuration
    error = validate_dict_not_empty(alert_config, "Alert configuration")
    if error:
        return error

    # Check if alerts are disabled
    if not alert_config.get("enabled", True):
        return SuccessResult(
            data={
                "monitor_result": {"alerts_enabled": False},
                "message": "Alerts disabled",
            }
        )

    # Validate required fields
    required_fields = ["warning_days", "critical_days"]
    for field in required_fields:
        if field not in alert_config:
            return ErrorResult(
                message=f"Missing required field in alert config: {field}"
            )

    error = validate_positive_integer(
        alert_config["warning_days"], "Warning days"
    )
    if error:
        return error

    error = validate_positive_integer(
        alert_config["critical_days"], "Critical days"
    )
    if error:
        return error

    error = validate_days_comparison(
        alert_config["warning_days"], alert_config["critical_days"]
    )
    if error:
        return error

    # Check notification channels
    notification_channels = alert_config.get("notification_channels", [])
    error = validate_list_not_empty(
        notification_channels, "Notification channels"
    )
    if error:
        return error

    # Test alert configuration
    test_result = _test_alert_config(alert_config)
    if not test_result["success"]:
        return ErrorResult(
            message=f"Alert configuration test failed: {test_result['error']}"
        )

    # Save alert configuration
    config_path = "/tmp/cert_alert_config.json"
    success, error = save_json_file(alert_config, config_path)
    if not success:
        return error

    get_global_logger().info(f"Alert configuration saved to {config_path}")

    return SuccessResult(
        data={
            "monitor_result": {"alerts_enabled": True},
            "alert_config": alert_config,
            "config_path": config_path,
            "setup_date": datetime.now().isoformat(),
            "message": "Alerts configured successfully",
        }
    )


def _test_alert_config(alert_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test alert configuration.

    Args:
        alert_config: Alert configuration to test

    Returns:
        Test result dictionary
    """
    try:
        # Test email configuration if present
        if "email_recipients" in alert_config:
            recipients = alert_config["email_recipients"]
            if not isinstance(recipients, list) or not recipients:
                return {"success": False, "error": "Invalid email recipients"}

        # Test webhook configuration if present
        if "webhook_url" in alert_config:
            webhook_url = alert_config["webhook_url"]
            if not isinstance(webhook_url, str) or not webhook_url:
                return {"success": False, "error": "Invalid webhook URL"}

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}

