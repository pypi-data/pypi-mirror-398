"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Proxy registration validation helper for MCP Proxy Adapter configuration.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .validation_result import ValidationResult


class ProxyRegistrationValidator:
    """
    Dedicated validator for proxy registration configuration blocks.
    """

    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize validator with raw configuration data.
        """
        self.config_data = config_data
        self._results: List[ValidationResult] = []

    def validate(self) -> List[ValidationResult]:
        """
        Execute validation workflow.
        """
        self._results = []

        registration_config = self._get_nested_value_safe("registration", {}) or {}
        if not isinstance(registration_config, dict) or not registration_config.get(
            "enabled", False
        ):
            return list(self._results)

        protocol = registration_config.get("protocol")
        normalized_protocol = self._normalize_protocol(protocol)
        if not protocol:
            self._append_result(
                level="error",
                message="registration.protocol is required when registration.enabled=true",
                section="registration",
                key="protocol",
                suggestion="Specify registration.protocol (http, https, or mtls)",
            )
        elif protocol not in ("http", "https", "mtls"):
            self._append_result(
                level="error",
                message=f"Invalid registration.protocol value: {protocol}. Must be http, https, or mtls",
                section="registration",
                key="protocol",
                suggestion="Use one of the supported values: http, https, mtls",
            )
            normalized_protocol = "http"

        self._validate_url_field(
            value=registration_config.get("register_url"),
            section="registration",
            key="register_url",
            protocol=normalized_protocol,
            required=True,
            missing_message="registration.register_url is required when registration.enabled=true",
            suggestion="Specify registration.register_url (e.g., http://host:port/register)",
            scheme_example="https://host:port/register",
        )
        self._validate_url_field(
            value=registration_config.get("unregister_url"),
            section="registration",
            key="unregister_url",
            protocol=normalized_protocol,
            required=False,
            suggestion="Use a valid unregister URL (e.g., http://host:port/unregister)",
            scheme_example="https://host:port/unregister",
        )

        self._validate_ssl_block(registration_config, normalized_protocol)
        self._validate_misc_settings(registration_config, normalized_protocol)

        return list(self._results)

    def _append_result(
        self,
        *,
        level: str,
        message: str,
        section: Optional[str] = None,
        key: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Append validation result to internal list."""
        self._results.append(
            ValidationResult(
                level=level,
                message=message,
                section=section,
                key=key,
                suggestion=suggestion,
            )
        )

    def _get_nested_value_safe(self, key: str, default: Any = None) -> Any:
        """Retrieve nested configuration value safely."""
        keys = key.split(".")
        value: Any = self.config_data
        for part in keys:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def _normalize_protocol(self, protocol_value: Any) -> str:
        """Normalize protocol representation to lowercase name."""
        if isinstance(protocol_value, str):
            return protocol_value.lower()
        return "http"

    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation helper."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    def _validate_url_field(
        self,
        *,
        value: Optional[str],
        section: str,
        key: str,
        protocol: str,
        required: bool,
        missing_message: Optional[str] = None,
        suggestion: Optional[str] = None,
        scheme_example: Optional[str] = None,
    ) -> None:
        """Validate a URL field including protocol-specific scheme."""
        label = f"{section}.{key}"
        if not value:
            if required:
                self._append_result(
                    level="error",
                    message=missing_message or f"{label} is required",
                    section=section,
                    key=key,
                    suggestion=suggestion,
                )
            return

        if not self._is_valid_url(value):
            self._append_result(
                level="error",
                message=f"Invalid {key} format: {value}",
                section=section,
                key=key,
                suggestion=suggestion,
            )
            return

        if protocol in {"https", "mtls"} and not value.startswith("https://"):
            hint = scheme_example or "https://host:port/path"
            self._append_result(
                level="error",
                message=f"{label} must use https:// scheme when registration.protocol is {protocol}",
                section=section,
                key=key,
                suggestion=f"Change {label} to use https:// scheme (e.g., {hint})",
            )
        elif protocol == "http" and not value.startswith("http://"):
            hint = scheme_example or "http://host:port/path"
            self._append_result(
                level="error",
                message=f"{label} must use http:// scheme when registration.protocol is http",
                section=section,
                key=key,
                suggestion=f"Change {label} to use http:// scheme (e.g., {hint})",
            )

    def _get_ssl_config(self) -> Dict[str, Any]:
        """Return registration SSL block."""
        ssl_config = self._get_nested_value_safe("registration.ssl") or {}
        return ssl_config if isinstance(ssl_config, dict) else {}

    def _validate_ssl_block(
        self, registration_config: Dict[str, Any], protocol: str
    ) -> None:
        """Validate registration SSL requirements."""
        ssl_config = self._get_ssl_config()
        if protocol in {"https", "mtls"} and not ssl_config:
            self._append_result(
                level="error",
                message=f"registration.ssl section is required when registration.protocol is {protocol}",
                section="registration",
                key="ssl",
                suggestion="Provide registration.ssl with certificate details",
            )
            return

        if protocol == "mtls":
            for field in ("cert", "key", "ca"):
                value = ssl_config.get(field) if ssl_config else None
                self._append_result_if_missing(
                    value=value,
                    section="registration",
                    key=f"ssl.{field}",
                    message=f"registration.protocol mtls requires registration.ssl.{field}",
                )
        elif protocol == "https" and ssl_config and not ssl_config.get("ca"):
            self._append_result(
                level="warning",
                message="registration.protocol is https but registration.ssl.ca is not specified",
                section="registration",
                key="ssl.ca",
                suggestion="Provide CA certificate for secure proxy registration",
            )

    def _append_result_if_missing(
        self, *, value: Optional[str], section: str, key: str, message: str
    ) -> None:
        """Append error when expected field is missing."""
        if value:
            return
        self._append_result(
            level="error",
            message=message,
            section=section,
            key=key,
            suggestion=f"Specify {section}.{key}",
        )

    def _validate_misc_settings(
        self, registration_config: Dict[str, Any], protocol: str
    ) -> None:
        """Validate CRL, hostname and heartbeat settings."""
        crl_file = registration_config.get("crl_file")
        if crl_file and protocol not in {"mtls", "https"}:
            self._append_result(
                level="warning",
                message="registration.crl_file is specified but registration.protocol is not mtls or https",
                section="registration",
                key="crl_file",
                suggestion="CRL file is only used for TLS-based protocols",
            )

        check_hostname = registration_config.get("check_hostname", True)
        if not isinstance(check_hostname, bool):
            self._append_result(
                level="error",
                message="registration.check_hostname must be a boolean value",
                section="registration",
                key="check_hostname",
                suggestion="Use true or false for registration.check_hostname",
            )

        heartbeat_config = registration_config.get("heartbeat", {}) or {}
        heartbeat_url = (
            heartbeat_config.get("url") if isinstance(heartbeat_config, dict) else None
        )
        self._validate_url_field(
            value=heartbeat_url,
            section="registration.heartbeat",
            key="url",
            protocol=protocol,
            required=True,
            missing_message="registration.heartbeat.url is required when registration.enabled=true",
            suggestion="Specify registration.heartbeat.url (e.g., http://host:port/proxy/heartbeat)",
            scheme_example="https://host:port/proxy/heartbeat",
        )

        heartbeat_interval = (
            heartbeat_config.get("interval")
            if isinstance(heartbeat_config, dict)
            else None
        )
        if heartbeat_interval is None:
            self._append_result(
                level="warning",
                message="registration.heartbeat.interval is not specified; default scheduler may misbehave",
                section="registration.heartbeat",
                key="interval",
                suggestion="Provide heartbeat.interval in seconds",
            )
        elif not isinstance(heartbeat_interval, int) or heartbeat_interval <= 0:
            self._append_result(
                level="error",
                message="registration.heartbeat.interval must be a positive integer",
                section="registration.heartbeat",
                key="interval",
                suggestion="Set heartbeat.interval to a positive number of seconds",
            )

