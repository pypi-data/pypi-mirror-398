"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Protocol validation utilities for MCP Proxy Adapter configuration validation.
"""

import re
from typing import Dict, List, Any

from .validation_result import ValidationResult


class ProtocolValidator:
    """Validator for protocol-related configuration settings."""

    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize protocol validator.

        Args:
            config_data: Configuration data dictionary to validate
        """
        self.config_data = config_data
        self.validation_results: List[ValidationResult] = []

    def validate_required_sections(self) -> List[ValidationResult]:
        """
        Validate that required configuration sections are present and consistent.

        Returns:
            List of validation results produced during validation
        """
        self.validation_results = []
        self._validate_server_section()
        self._validate_feature_flags()
        return list(self.validation_results)

    def validate_protocol_requirements(self) -> List[ValidationResult]:
        """
        Validate protocol-specific requirements based on selected protocol.

        Returns:
            List of validation results produced during validation
        """
        self.validation_results = []
        protocol = str(self._get_nested_value_safe("server.protocol", "http")).lower()

        if protocol == "https":
            self._validate_https_requirements()
        elif protocol == "mtls":
            self._validate_mtls_requirements()

        return list(self.validation_results)

    def _validate_https_requirements(self) -> None:
        """Validate HTTPS-specific requirements."""
        # Check server section for certificates (SimpleConfig format)
        server_config = self._get_nested_value_safe("server", {})

        # Check for required SSL files in server section (new ssl structure)
        ssl_config = server_config.get("ssl", {})
        cert_file = (
            ssl_config.get("cert") if ssl_config else server_config.get("cert_file")
        )
        key_file = (
            ssl_config.get("key") if ssl_config else server_config.get("key_file")
        )

        if not cert_file:
            self.validation_results.append(
                ValidationResult(
                    level="error",
                    message="HTTPS protocol requires SSL certificate file",
                    section="server",
                    key="ssl.cert",
                    suggestion="Specify server.ssl.cert",
                )
            )

        if not key_file:
            self.validation_results.append(
                ValidationResult(
                    level="error",
                    message="HTTPS protocol requires SSL key file",
                    section="server",
                    key="ssl.key",
                    suggestion="Specify server.ssl.key",
                )
            )

    def _validate_mtls_requirements(self) -> None:
        """Validate mTLS-specific requirements."""
        # mTLS requires HTTPS
        self._validate_https_requirements()

        # Check server section for certificates (SimpleConfig format)
        server_config = self._get_nested_value_safe("server", {})
        transport_config = self._get_nested_value_safe("transport", {})

        # For mTLS server, we need:
        # - Server cert/key (already checked by _validate_https_requirements)
        # - CA cert for verifying client certificates
        # - verify_client enabled

        # Check for CA certificate (needed for client certificate verification) - new ssl structure
        ssl_config = server_config.get("ssl", {})
        ca_cert_file = (
            ssl_config.get("ca") if ssl_config else server_config.get("ca_cert_file")
        )

        if not ca_cert_file:
            self.validation_results.append(
                ValidationResult(
                    level="error",
                    message="mTLS protocol requires CA certificate for client verification",
                    section="server",
                    key="ssl.ca",
                    suggestion="Specify server.ssl.ca for client certificate verification",
                )
            )

        # Check for client verification
        if not transport_config.get("verify_client", False):
            self.validation_results.append(
                ValidationResult(
                    level="warning",
                    message="mTLS protocol should have client verification enabled",
                    section="transport",
                    key="verify_client",
                    suggestion="Set transport.verify_client to true",
                )
            )

        # Note: client_cert and client_key are NOT required for mTLS server
        # They are only needed for client/registration configuration when connecting TO a proxy

    def _validate_feature_flags(self) -> None:
        """Validate feature flags based on protocol."""
        protocol = self._get_nested_value_safe("server.protocol", "http")
        server_config = self._get_nested_value_safe("server", {})

        # Check if features are compatible with protocol
        if protocol == "http":
            # HTTP doesn't support SSL features
            if server_config.get("cert_file") or server_config.get("key_file"):
                self.validation_results.append(
                    ValidationResult(
                        level="warning",
                        message="SSL certificates are configured but protocol is HTTP. Consider using HTTPS",
                        section="server",
                        suggestion="Change protocol to https or remove certificate configuration",
                    )
                )

        # Check transport configuration
        transport_config = self._get_nested_value_safe("transport", {})
        if transport_config:
            verify_client = transport_config.get("verify_client", False)
            if verify_client and protocol == "http":
                self.validation_results.append(
                    ValidationResult(
                        level="warning",
                        message="Client verification is enabled but protocol is HTTP",
                        section="transport",
                        key="verify_client",
                        suggestion="Change protocol to https or mtls, or disable client verification",
                    )
                )

    def _validate_server_section(self) -> None:
        """Validate server section requirements."""
        server_config = self.config_data.get("server", {})

        # Check required fields
        if "host" not in server_config:
            self.validation_results.append(
                ValidationResult(
                    level="error",
                    message="Server host is required",
                    section="server",
                    key="host",
                    suggestion="Add host field to server section",
                )
            )

        if "port" not in server_config:
            self.validation_results.append(
                ValidationResult(
                    level="error",
                    message="Server port is required",
                    section="server",
                    key="port",
                    suggestion="Add port field to server section",
                )
            )

        if "protocol" not in server_config:
            self.validation_results.append(
                ValidationResult(
                    level="error",
                    message="Server protocol is required",
                    section="server",
                    key="protocol",
                    suggestion="Add protocol field to server section",
                )
            )

        for required_key in ("debug", "log_level"):
            if required_key not in server_config:
                self.validation_results.append(
                    ValidationResult(
                        level="error",
                        message=f"Server {required_key} is required",
                        section="server",
                        key=required_key,
                        suggestion=f"Add {required_key} field to server section",
                    )
                )

        # Validate port number
        port = server_config.get("port")
        if port is not None:
            if not isinstance(port, int) or not (1 <= port <= 65535):
                self.validation_results.append(
                    ValidationResult(
                        level="error",
                        message=f"Invalid port number: {port}. Must be between 1 and 65535",
                        section="server",
                        key="port",
                    )
                )

        # Validate host format
        host = server_config.get("host")
        if host is not None:
            if not self._is_valid_host(host):
                self.validation_results.append(
                    ValidationResult(
                        level="error",
                        message=f"Invalid host format: {host}",
                        section="server",
                        key="host",
                        suggestion="Use a valid hostname or IP address",
                    )
                )

    def _is_valid_host(self, host: str) -> bool:
        """Check if host has valid format."""
        # Check for localhost
        if host in ["localhost", "127.0.0.1", "::1", "0.0.0.0"]:
            return True

        # Check for IP address
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if re.match(ip_pattern, host):
            # Validate IP address ranges
            parts = host.split(".")
            return all(0 <= int(part) <= 255 for part in parts)

        # Check for hostname (basic validation)
        hostname_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
        return bool(re.match(hostname_pattern, host))

    def _get_nested_value_safe(self, key: str, default: Any = None) -> Any:
        """Safely get a nested value from configuration."""
        keys = key.split(".")
        value = self.config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value
