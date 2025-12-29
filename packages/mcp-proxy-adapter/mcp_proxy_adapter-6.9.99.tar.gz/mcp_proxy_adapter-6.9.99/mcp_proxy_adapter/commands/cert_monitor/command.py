"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Certificate monitoring command.
"""

from typing import Dict, Any

from ..base import Command
from ..result import CommandResult, ErrorResult
from ...core.certificate_utils import CertificateUtils
from ...core.auth_validator import AuthValidator

from .handlers import (
    handle_expiry_check,
    handle_health_check,
    handle_alert_setup,
    handle_auto_renew,
)
from .result import CertMonitorResult


class CertMonitorCommand(Command):
    """
    Command for certificate monitoring.

    Provides methods for monitoring certificate expiry, health, alerts, and auto-renewal.
    """

    # Command metadata
    name = "cert_monitor"
    version = "1.0.0"
    descr = "Certificate expiry monitoring and health checks"
    category = "security"
    author = "MCP Proxy Adapter Team"
    email = "team@mcp-proxy-adapter.com"
    source_url = "https://github.com/mcp-proxy-adapter"
    result_class = CertMonitorResult

    def __init__(self):
        """Initialize certificate monitor command."""
        super().__init__()
        self.certificate_utils = CertificateUtils()
        self.auth_validator = AuthValidator()

    async def execute(self, **kwargs) -> CommandResult:
        """
        Execute certificate monitor command.

        Args:
            **kwargs: Command parameters including:
                - action: Action to perform (cert_expiry_check, cert_health_check, cert_alert_setup, cert_auto_renew)
                - cert_path: Certificate file path for individual checks
                - warning_days: Days before expiry to start warning
                - critical_days: Days before expiry for critical status
                - alert_config: Alert configuration for setup
                - auto_renew_config: Auto-renewal configuration

        Returns:
            CommandResult with monitoring operation status
        """
        action = kwargs.get("action", "cert_expiry_check")

        if action == "cert_expiry_check":
            return await handle_expiry_check(
                self.certificate_utils,
                kwargs.get("cert_path"),
                kwargs.get("warning_days", 30),
                kwargs.get("critical_days", 7),
            )
        elif action == "cert_health_check":
            return await handle_health_check(
                self.certificate_utils,
                self.auth_validator,
                kwargs.get("cert_path"),
            )
        elif action == "cert_alert_setup":
            return await handle_alert_setup(
                kwargs.get("cert_path"), kwargs.get("alert_config", {})
            )
        elif action == "cert_auto_renew":
            return await handle_auto_renew(
                self.certificate_utils,
                kwargs.get("cert_path"),
                kwargs.get("auto_renew_config", {}),
            )
        else:
            return ErrorResult(
                message=f"Unknown action: {action}. Supported actions: cert_expiry_check, cert_health_check, cert_alert_setup, cert_auto_renew"
            )

