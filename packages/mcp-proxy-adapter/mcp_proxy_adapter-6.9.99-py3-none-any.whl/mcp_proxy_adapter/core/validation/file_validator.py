"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

File validation utilities for MCP Proxy Adapter configuration validation.
"""

import os
from typing import Any, Dict, List, Optional, Set

from .validation_result import ValidationResult


class FileValidator:
    """Validator for file-related configuration settings."""

    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize file validator.

        Args:
            config_data: Configuration data dictionary to validate
        """
        self.config_data = config_data
        self.validation_results: List[ValidationResult] = []
        self._validated_paths: Set[str] = set()

    def _reset(self) -> None:
        """Reset validation state."""
        self.validation_results = []
        self._validated_paths = set()

    def _normalize_path(self, path: str) -> str:
        """Return absolute normalized path for consistent comparisons."""
        return os.path.abspath(os.path.expanduser(path))

    def _record_missing_path(
        self,
        *,
        path: str,
        section: str,
        key: str,
        level: str = "error",
        expect_directory: bool = False,
    ) -> None:
        """Append validation result about missing path."""
        path_type = "directory" if expect_directory else "file"
        self.validation_results.append(
            ValidationResult(
                level=level,
                message=f"Referenced {path_type} not found: {path}",
                section=section,
                key=key,
                suggestion=f"Create or update the {path_type} path",
            )
        )

    def _validate_path(
        self,
        path: Optional[str],
        *,
        section: str,
        key: str,
        level: str = "error",
        expect_directory: bool = False,
    ) -> None:
        """Validate that a file or directory exists."""
        if not path:
            return

        normalized = self._normalize_path(path)
        if normalized in self._validated_paths:
            return
        self._validated_paths.add(normalized)

        exists = (
            os.path.isdir(normalized)
            if expect_directory
            else os.path.isfile(normalized)
        )
        if not exists:
            self._record_missing_path(
                path=path,
                section=section,
                key=key,
                level=level,
                expect_directory=expect_directory,
            )

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

    def _collect_ssl_paths(self, base_key: str) -> Dict[str, Optional[str]]:
        """Collect SSL related paths for provided section."""
        ssl_config = self._get_nested_value_safe(base_key) or {}
        if not isinstance(ssl_config, dict):
            return {}
        return {
            "cert": ssl_config.get("cert"),
            "key": ssl_config.get("key"),
            "ca": ssl_config.get("ca"),
            "crl": ssl_config.get("crl"),
        }

    def validate_file_existence(self) -> List[ValidationResult]:
        """
        Validate that referenced files exist.

        Returns:
            List of validation results
        """
        self._reset()

        # Legacy top-level SSL configuration
        if self._get_nested_value_safe("ssl.enabled", False):
            self._validate_path(
                self._get_nested_value_safe("ssl.cert_file"),
                section="ssl",
                key="cert_file",
            )
            self._validate_path(
                self._get_nested_value_safe("ssl.key_file"),
                section="ssl",
                key="key_file",
            )
            self._validate_path(
                self._get_nested_value_safe("ssl.ca_cert"),
                section="ssl",
                key="ca_cert",
                level="warning",
            )

        # Server SSL assets
        server_paths = self._collect_ssl_paths("server.ssl")
        self._validate_path(
            server_paths.get("cert") or self._get_nested_value_safe("server.cert_file"),
            section="server",
            key="ssl.cert",
        )
        self._validate_path(
            server_paths.get("key") or self._get_nested_value_safe("server.key_file"),
            section="server",
            key="ssl.key",
        )
        self._validate_path(
            server_paths.get("ca")
            or self._get_nested_value_safe("server.ca_cert_file"),
            section="server",
            key="ssl.ca",
            level="warning",
        )
        self._validate_path(
            server_paths.get("crl"),
            section="server",
            key="ssl.crl",
            level="warning",
        )

        # Registration SSL assets
        registration_paths = self._collect_ssl_paths("registration.ssl")
        for field in ("cert", "key", "ca", "crl"):
            self._validate_path(
                registration_paths.get(field),
                section="registration.ssl",
                key=field,
                level="error" if field in {"cert", "key"} else "warning",
            )

        # Client SSL assets
        client_paths = self._collect_ssl_paths("client.ssl")
        for field in ("cert", "key", "ca", "crl"):
            self._validate_path(
                client_paths.get(field),
                section="client.ssl",
                key=field,
                level="error" if field in {"cert", "key"} else "warning",
            )

        # Roles configuration
        self._validate_path(
            self._get_nested_value_safe("roles.config_file")
            or self._get_nested_value_safe("security.roles_file"),
            section="roles",
            key="config_file",
        )

        # Commands catalog directory
        self._validate_path(
            self._get_nested_value_safe("commands.catalog_directory"),
            section="commands",
            key="catalog_directory",
            expect_directory=True,
        )

        # Logging directory
        self._validate_path(
            self._get_nested_value_safe("logging.log_dir")
            or self._get_nested_value_safe("server.log_dir"),
            section="logging",
            key="log_dir",
            expect_directory=True,
            level="warning",
        )

        # Legacy proxy registration certificates
        if self._get_nested_value_safe("proxy_registration.enabled", False):
            self._validate_path(
                self._get_nested_value_safe("proxy_registration.certificate.cert_file"),
                section="proxy_registration.certificate",
                key="cert_file",
                level="warning",
            )
            self._validate_path(
                self._get_nested_value_safe("proxy_registration.certificate.key_file"),
                section="proxy_registration.certificate",
                key="key_file",
                level="warning",
            )

        return list(self.validation_results)
