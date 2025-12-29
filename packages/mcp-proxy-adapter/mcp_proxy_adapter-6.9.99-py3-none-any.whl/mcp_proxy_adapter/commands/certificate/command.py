"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Certificate management command.
"""

from typing import Dict, Any

from ..base import Command
from ..result import CommandResult, ErrorResult
from ...core.certificate_utils import CertificateUtils
from ...core.auth_validator import AuthValidator
from ...core.role_utils import RoleUtils

from .handlers import (
    handle_create_ca,
    handle_create_server,
    handle_create_client,
    handle_revoke,
    handle_list,
    handle_info,
)
from .result import CertificateResult


class CertificateManagementCommand(Command):
    """
    Command for certificate management.

    Provides methods for creating, managing, and validating certificates.
    """

    # Command metadata
    name = "certificate_management"
    version = "1.0.0"
    descr = "Certificate creation, validation, and management"
    category = "security"
    author = "MCP Proxy Adapter Team"
    email = "team@mcp-proxy-adapter.com"
    source_url = "https://github.com/mcp-proxy-adapter"
    result_class = CertificateResult

    def __init__(self):
        """Initialize certificate management command."""
        super().__init__()
        self.certificate_utils = CertificateUtils()
        self.auth_validator = AuthValidator()
        self.role_utils = RoleUtils()

    async def execute(self, **kwargs) -> CommandResult:
        """
        Execute certificate management command.

        Args:
            **kwargs: Command parameters including:
                - action: Action to perform (cert_create_ca, cert_create_server, cert_create_client, cert_revoke, cert_list, cert_info)
                - common_name: Common name for certificate creation
                - roles: List of roles for certificate creation
                - ca_cert_path: CA certificate path for server/client certificate creation
                - ca_key_path: CA key path for server/client certificate creation
                - output_dir: Output directory for certificate creation
                - validity_days: Certificate validity period in days
                - key_size: Key size in bits for CA certificate creation
                - cert_path: Certificate path for revocation and info
                - cert_dir: Directory for certificate listing

        Returns:
            CommandResult with certificate operation status
        """
        action = kwargs.get("action", "cert_list")

        if action == "cert_create_ca":
            return await handle_create_ca(
                self.certificate_utils,
                kwargs.get("common_name"),
                kwargs.get("output_dir"),
                kwargs.get("validity_days", 365),
                kwargs.get("key_size", 2048),
            )
        elif action == "cert_create_server":
            return await handle_create_server(
                self.certificate_utils,
                self.auth_validator,
                self.role_utils,
                kwargs.get("common_name"),
                kwargs.get("roles", []),
                kwargs.get("ca_cert_path"),
                kwargs.get("ca_key_path"),
                kwargs.get("output_dir"),
                kwargs.get("validity_days", 365),
            )
        elif action == "cert_create_client":
            return await handle_create_client(
                self.certificate_utils,
                self.auth_validator,
                self.role_utils,
                kwargs.get("common_name"),
                kwargs.get("roles", []),
                kwargs.get("ca_cert_path"),
                kwargs.get("ca_key_path"),
                kwargs.get("output_dir"),
                kwargs.get("validity_days", 365),
            )
        elif action == "cert_revoke":
            return await handle_revoke(
                self.certificate_utils, kwargs.get("cert_path")
            )
        elif action == "cert_list":
            return await handle_list(
                self.certificate_utils, kwargs.get("cert_dir", "/tmp")
            )
        elif action == "cert_info":
            return await handle_info(
                self.certificate_utils, self.auth_validator, kwargs.get("cert_path")
            )
        else:
            return ErrorResult(
                message=f"Unknown action: {action}. Supported actions: cert_create_ca, cert_create_server, cert_create_client, cert_revoke, cert_list, cert_info"
            )

