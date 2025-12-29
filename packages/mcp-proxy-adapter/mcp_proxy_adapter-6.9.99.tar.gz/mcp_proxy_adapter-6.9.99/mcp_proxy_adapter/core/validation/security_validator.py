"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Security validation utilities for MCP Proxy Adapter configuration validation.
"""

from typing import Any, Dict, List, Optional

from .proxy_registration_validator import ProxyRegistrationValidator
from .validation_result import ValidationResult


class SecurityValidator:
    """Validator for security-related configuration settings."""

    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize security validator.

        Args:
            config_data: Configuration data dictionary to validate
        """
        self.config_data = config_data
        self.validation_results: List[ValidationResult] = []

    def _reset_results(self) -> None:
        """Reset internal validation buffer."""
        self.validation_results = []

    def _append_result(
        self,
        *,
        level: str,
        message: str,
        section: Optional[str] = None,
        key: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Append a validation result."""
        self.validation_results.append(
            ValidationResult(
                level=level,
                message=message,
                section=section,
                key=key,
                suggestion=suggestion,
            )
        )

    def _has_auth_tokens(
        self, security_config: Dict[str, Any], auth_config: Dict[str, Any]
    ) -> bool:
        """Return True when tokens are configured in legacy or modern sections."""
        for source in (security_config.get("tokens"), auth_config.get("tokens")):
            if isinstance(source, dict) and source:
                return True
        return False

    def _has_role_configuration(
        self, security_config: Dict[str, Any], auth_config: Dict[str, Any]
    ) -> bool:
        """Return True when any roles configuration is present."""
        if isinstance(security_config.get("roles"), dict) and security_config.get(
            "roles"
        ):
            return True
        if security_config.get("roles_file"):
            return True
        if isinstance(auth_config.get("roles"), dict) and auth_config.get("roles"):
            return True
        return bool(self._get_nested_value_safe("roles.enabled", False))

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

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL has valid format."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    def _normalize_protocol(self, protocol_value: Any, default: str = "http") -> str:
        """Normalize protocol strings to lowercase."""
        if isinstance(protocol_value, str):
            return protocol_value.lower()
        return default

    def _get_ssl_config(self, dotted_path: str) -> Dict[str, Any]:
        """Return SSL configuration dictionary for a dotted path."""
        ssl_config = self._get_nested_value_safe(dotted_path) or {}
        return ssl_config if isinstance(ssl_config, dict) else {}

    def _require_field(
        self,
        value: Any,
        *,
        section: str,
        key: str,
        message: str,
        suggestion: Optional[str] = None,
    ) -> None:
        """Ensure that a value is provided."""
        if value:
            return
        self._append_result(
            level="error",
            message=message,
            section=section,
            key=key,
            suggestion=suggestion,
        )

    def validate_security_consistency(self) -> List[ValidationResult]:
        """
        Validate security configuration consistency.

        Returns:
            List of validation results
        """
        self._reset_results()
        security_config = self._get_nested_value_safe("security", {}) or {}
        auth_config = self._get_nested_value_safe("auth", {}) or {}

        if security_config.get("enabled", False):
            tokens_configured = self._has_auth_tokens(security_config, auth_config)
            roles_configured = self._has_role_configuration(
                security_config, auth_config
            )

            if not (tokens_configured or roles_configured):
                self._append_result(
                    level="warning",
                    message="Security is enabled but no authentication methods are configured",
                    section="security",
                    suggestion="Configure tokens or roles or disable security",
                )

        return list(self.validation_results)

    def validate_ssl_configuration(self) -> List[ValidationResult]:
        """
        Validate SSL configuration.

        Returns:
            List of validation results
        """
        self._reset_results()
        self._validate_legacy_ssl_block()
        self._validate_server_ssl_block()
        registration = self._get_nested_value_safe("registration", {}) or {}
        if isinstance(registration, dict):
            self._validate_remote_ssl_block(
                section="registration",
                enabled=registration.get("enabled", False),
                protocol_value=registration.get("protocol"),
                ssl_path="registration.ssl",
            )
        client = self._get_nested_value_safe("client", {}) or {}
        if isinstance(client, dict):
            self._validate_remote_ssl_block(
                section="client",
                enabled=client.get("enabled", False),
                protocol_value=client.get("protocol"),
                ssl_path="client.ssl",
            )
        return list(self.validation_results)

    def _validate_legacy_ssl_block(self) -> None:
        """Validate deprecated top-level ssl.* structure."""
        ssl_config = self._get_nested_value_safe("ssl", {}) or {}
        if not isinstance(ssl_config, dict) or not ssl_config.get("enabled", False):
            return

        self._require_field(
            ssl_config.get("cert_file"),
            section="ssl",
            key="cert_file",
            message="SSL is enabled but cert_file is not specified",
            suggestion="Specify ssl.cert_file when ssl.enabled=true",
        )
        self._require_field(
            ssl_config.get("key_file"),
            section="ssl",
            key="key_file",
            message="SSL is enabled but key_file is not specified",
            suggestion="Specify ssl.key_file when ssl.enabled=true",
        )

    def _validate_server_ssl_block(self) -> None:
        """Validate server SSL configuration."""
        server_protocol = self._normalize_protocol(
            self._get_nested_value_safe("server.protocol")
        )
        if server_protocol not in {"https", "mtls"}:
            return

        cert = (
            self._get_nested_value_safe("server.ssl.cert")
            or self._get_nested_value_safe("server.cert_file")
            or self._get_nested_value_safe("ssl.cert_file")
        )
        key = (
            self._get_nested_value_safe("server.ssl.key")
            or self._get_nested_value_safe("server.key_file")
            or self._get_nested_value_safe("ssl.key_file")
        )
        ca = (
            self._get_nested_value_safe("server.ssl.ca")
            or self._get_nested_value_safe("server.ca_cert_file")
            or self._get_nested_value_safe("ssl.ca_cert")
        )

        self._require_field(
            cert,
            section="server",
            key="ssl.cert",
            message="Server protocol requires server.ssl.cert to be specified",
            suggestion="Provide server.ssl.cert path for HTTPS/mTLS",
        )
        self._require_field(
            key,
            section="server",
            key="ssl.key",
            message="Server protocol requires server.ssl.key to be specified",
            suggestion="Provide server.ssl.key path for HTTPS/mTLS",
        )

        if server_protocol == "mtls":
            self._require_field(
                ca,
                section="server",
                key="ssl.ca",
                message="mTLS server protocol requires server.ssl.ca for client verification",
                suggestion="Provide CA certificate via server.ssl.ca",
            )

    def _validate_remote_ssl_block(
        self,
        *,
        section: str,
        enabled: bool,
        protocol_value: Any,
        ssl_path: str,
    ) -> None:
        """Validate SSL settings for client/registration sections."""
        if not enabled:
            return

        protocol = self._normalize_protocol(protocol_value)
        if protocol not in {"https", "mtls"}:
            return

        ssl_config = self._get_ssl_config(ssl_path)
        if not ssl_config:
            self._append_result(
                level="error",
                message=f"{section}.ssl section is required when {section}.protocol is {protocol}",
                section=section,
                key="ssl",
                suggestion=f"Provide {section}.ssl configuration with certificate paths",
            )
            return

        if protocol == "https":
            if not ssl_config.get("ca"):
                self._append_result(
                    level="warning",
                    message=f"{section}.protocol is https but {section}.ssl.ca is not specified",
                    section=section,
                    key="ssl.ca",
                    suggestion=f"Provide {section}.ssl.ca for TLS verification",
                )
            return

        for field in ("cert", "key", "ca"):
            self._require_field(
                ssl_config.get(field),
                section=section,
                key=f"ssl.{field}",
                message=f"{section}.protocol mtls requires {section}.ssl.{field}",
                suggestion=f"Specify {section}.ssl.{field} for mTLS configuration",
            )

    def validate_roles_configuration(self) -> List[ValidationResult]:
        """
        Validate roles configuration.

        Returns:
            List of validation results
        """
        self._reset_results()
        roles_config = self._get_nested_value_safe("roles", {}) or {}
        if not isinstance(roles_config, dict):
            return list(self.validation_results)

        if roles_config.get("enabled", False) and not roles_config.get("config_file"):
            self._append_result(
                level="error",
                message="Roles are enabled but config_file is not specified",
                section="roles",
                key="config_file",
                suggestion="Specify roles.config_file with role definitions",
            )

        return list(self.validation_results)

    def validate_proxy_registration(self) -> List[ValidationResult]:
        """
        Validate proxy registration configuration.

        Returns:
            List of validation results
        """
        proxy_validator = ProxyRegistrationValidator(self.config_data)
        return proxy_validator.validate()
