"""
SSL Utilities Module

This module provides integration helpers that proxy every SSL/TLS operation
through the mcp_security_framework. No direct usage of Python's ssl module
is allowed inside the project codebase.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
Version: 2.0.0
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from mcp_security_framework.core.ssl_manager import (
    SSLConfigurationError,
    SSLManager,
)
from mcp_security_framework.schemas.config import (
    SSLConfig as FrameworkSSLConfig,
    TLSVersion,
)

logger = logging.getLogger(__name__)


class SSLUtils:
    """
    Utility helpers that wrap mcp_security_framework SSLManager.

    The helpers return ready-to-use SSL contexts created by the framework
    so that the rest of the project never instantiates ssl.SSLContext directly.
    """

    @staticmethod
    def create_ssl_context(
        *,
        cert_file: str,
        key_file: str,
        ca_cert: Optional[str] = None,
        verify_client: bool = False,
        cipher_suites: Optional[List[str]] = None,
        min_tls_version: Optional[str] = None,
        max_tls_version: Optional[str] = None,
        check_hostname: bool = True,
    ) -> Any:
        """
        Create server-side SSL context via the security framework.

        Args:
            cert_file: Path to server certificate
            key_file: Path to server private key
            ca_cert: Optional CA certificate path
            verify_client: Require client certificates (mTLS)
            cipher_suites: Optional list of cipher suite names
            min_tls_version: Minimum TLS version (e.g. "1.2" or "TLSv1.2")
            max_tls_version: Maximum TLS version
            check_hostname: Whether to enforce hostname validation

        Returns:
            SSL context object produced by SSLManager
        """
        manager = SSLUtils._build_manager(
            cert_file=cert_file,
            key_file=key_file,
            ca_cert=ca_cert,
            verify_client=verify_client,
            cipher_suites=cipher_suites,
            min_tls_version=min_tls_version,
            max_tls_version=max_tls_version,
            check_hostname=check_hostname,
        )
        return manager.create_server_context()

    @staticmethod
    def create_client_ssl_context(
        *,
        ca_cert: Optional[str] = None,
        client_cert: Optional[str] = None,
        client_key: Optional[str] = None,
        verify: bool = True,
        min_tls_version: Optional[str] = None,
        max_tls_version: Optional[str] = None,
        check_hostname: bool = True,
    ) -> Any:
        """
        Create client-side SSL context via the security framework.
        """
        config = FrameworkSSLConfig(
            enabled=True,
            cert_file=client_cert,
            key_file=client_key,
            ca_cert_file=ca_cert,
            client_cert_file=client_cert,
            client_key_file=client_key,
            verify=verify,
            verify_mode="CERT_REQUIRED" if verify else "CERT_NONE",
            min_tls_version=SSLUtils._normalize_tls_version(
                min_tls_version, TLSVersion.TLS_1_2
            ),
            max_tls_version=SSLUtils._normalize_optional_tls_version(max_tls_version),
            check_hostname=check_hostname,
        )

        try:
            manager = SSLManager(config)
            return manager.create_client_context()
        except (ValueError, SSLConfigurationError) as exc:
            logger.error("Failed to build client SSL context: %s", exc)
            raise

    @staticmethod
    def validate_certificate(
        cert_file: str,
        *,
        ca_cert: Optional[str] = None,
        crl_path: Optional[str] = None,
        allow_roles: Optional[List[str]] = None,
        deny_roles: Optional[List[str]] = None,
    ) -> bool:
        """
        Validate certificate through the security framework.
        """
        config = FrameworkSSLConfig(
            enabled=False,
            cert_file=None,
            key_file=None,
            ca_cert_file=ca_cert,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False,
        )

        try:
            manager = SSLManager(config)
            return manager.validate_certificate(
                cert_file,
                crl_path=crl_path,
                allow_roles=allow_roles,
                deny_roles=deny_roles,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Certificate validation failed: %s", exc)
            return False

    @staticmethod
    def _build_manager(
        *,
        cert_file: str,
        key_file: str,
        ca_cert: Optional[str],
        verify_client: bool,
        cipher_suites: Optional[List[str]],
        min_tls_version: Optional[str],
        max_tls_version: Optional[str],
        check_hostname: bool,
    ) -> SSLManager:
        if not cert_file or not key_file:
            raise ValueError("cert_file and key_file are required for SSL contexts")

        config = FrameworkSSLConfig(
            enabled=True,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert,
            verify=verify_client,
            verify_mode="CERT_REQUIRED" if verify_client else "CERT_NONE",
            min_tls_version=SSLUtils._normalize_tls_version(
                min_tls_version, TLSVersion.TLS_1_2
            ),
            max_tls_version=SSLUtils._normalize_optional_tls_version(max_tls_version),
            cipher_suite=SSLUtils._build_cipher_suite(cipher_suites),
            check_hostname=check_hostname,
        )

        try:
            return SSLManager(config)
        except (ValueError, SSLConfigurationError) as exc:
            logger.error("Failed to initialize SSLManager: %s", exc)
            raise

    @staticmethod
    def _build_cipher_suite(cipher_suites: Optional[List[str]]) -> Optional[str]:
        if not cipher_suites:
            return None
        cleaned = [suite.strip() for suite in cipher_suites if suite and suite.strip()]
        return ":".join(cleaned) if cleaned else None

    @staticmethod
    def _normalize_tls_version(
        value: Optional[str], default: TLSVersion
    ) -> TLSVersion:
        if not value:
            return default

        normalized = value.strip().upper()
        if normalized.startswith("TLS"):
            key = normalized
        else:
            # Accept formats like "1.2" or "TLS1.2"
            normalized = normalized.replace("V", "")
            if not normalized.startswith("TLS"):
                normalized = f"TLS{normalized}"
            key = f"TLSV{normalized.split('TLS')[-1]}"

        mapping = {
            "TLSV1.0": TLSVersion.TLS_1_0,
            "TLSV1.1": TLSVersion.TLS_1_1,
            "TLSV1.2": TLSVersion.TLS_1_2,
            "TLSV1.3": TLSVersion.TLS_1_3,
        }
        return mapping.get(key, default)

    @staticmethod
    def _normalize_optional_tls_version(
        value: Optional[str],
    ) -> Optional[TLSVersion]:
        if not value:
            return None
        return SSLUtils._normalize_tls_version(value, TLSVersion.TLS_1_2)
