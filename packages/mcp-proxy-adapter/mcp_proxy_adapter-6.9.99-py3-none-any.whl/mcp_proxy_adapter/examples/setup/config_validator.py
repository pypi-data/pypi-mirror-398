"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Configuration validator for MCP Proxy Adapter test environment setup.
"""

from typing import Dict, List, Any, Tuple


class ConfigurationValidator:
    """
    Validates MCP Proxy Adapter configurations for mutually exclusive settings
    and protocol compatibility.
    """

    def __init__(self):
        """
        Initialize configuration validator.
        """
        self.errors: List[str] = []
        self.warnings: List[str] = []


    def _validate_protocol_settings(
        self, config: Dict[str, Any], config_name: str
    ) -> None:
        """Validate protocol configuration settings."""
        protocols = config.get("protocols", {})

        if not protocols.get("enabled", False):
            self.warnings.append(
                f"⚠️ {config_name}: Protocol middleware is disabled - all protocols will be allowed"
            )
            return

        allowed_protocols = protocols.get("allowed_protocols", [])
        if not allowed_protocols:
            self.errors.append(
                f"❌ {config_name}: No allowed protocols specified when protocol middleware is enabled"
            )
            return

        # Check for invalid protocol combinations
        if "http" in allowed_protocols and "https" in allowed_protocols:
            self.warnings.append(
                f"⚠️ {config_name}: Both HTTP and HTTPS protocols are allowed - consider security implications"
            )

        if "mtls" in allowed_protocols and "http" in allowed_protocols:
            self.errors.append(
                f"❌ {config_name}: mTLS and HTTP protocols are mutually exclusive - mTLS requires HTTPS"
            )

    def _validate_ssl_settings(self, config: Dict[str, Any], config_name: str) -> None:
        """Validate SSL/TLS configuration settings."""
        security = config.get("security", {})
        ssl = security.get("ssl", {})

        if not ssl.get("enabled", False):
            return

        # Check certificate file requirements
        cert_file = ssl.get("server_cert_file")
        key_file = ssl.get("server_key_file")

        if not cert_file or not key_file:
            self.errors.append(
                f"❌ {config_name}: SSL enabled but server certificate or key file not specified"
            )

        # Check CA certificate requirements
        ca_cert_file = ssl.get("ca_cert_file")
        verify_server = ssl.get("verify_server", True)

        if verify_server and not ca_cert_file:
            self.warnings.append(
                f"⚠️ {config_name}: Server verification enabled but no CA certificate specified"
            )

    def _validate_mtls_settings(self, config: Dict[str, Any], config_name: str) -> None:
        """Validate mTLS configuration settings."""
        security = config.get("security", {})
        ssl = security.get("ssl", {})

        if not ssl.get("enabled", False):
            return

        # Check if mTLS is configured
        client_cert_file = ssl.get("client_cert_file")
        client_key_file = ssl.get("client_key_file")
        verify_client = ssl.get("verify_client", False)

        if verify_client and (not client_cert_file or not client_key_file):
            self.errors.append(
                f"❌ {config_name}: Client verification enabled but client certificate or key file not specified"
            )

        # Check protocol compatibility
        protocols = config.get("protocols", {})
        if protocols.get("enabled", False):
            allowed_protocols = protocols.get("allowed_protocols", [])
            if verify_client and "mtls" not in allowed_protocols:
                self.warnings.append(
                    f"⚠️ {config_name}: Client verification enabled but 'mtls' not in allowed protocols"
                )

    def _validate_auth_settings(self, config: Dict[str, Any], config_name: str) -> None:
        """Validate authentication configuration settings."""
        security = config.get("security", {})
        auth = security.get("auth", {})

        if not auth.get("enabled", False):
            return

        # Check token requirements
        token_required = auth.get("token_required", False)
        if token_required and not auth.get("token_secret"):
            self.errors.append(
                f"❌ {config_name}: Token authentication enabled but no token secret specified"
            )
