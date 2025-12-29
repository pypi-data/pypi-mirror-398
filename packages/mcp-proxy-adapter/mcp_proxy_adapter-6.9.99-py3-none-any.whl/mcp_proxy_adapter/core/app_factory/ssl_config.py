"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

SSL configuration handling for app factory.
"""

from typing import Any, Dict, Optional

from pydantic import ValidationError

from mcp_security_framework.core.ssl_manager import SSLConfigurationError, SSLManager
from mcp_security_framework.schemas.config import SSLConfig as FrameworkSSLConfig

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.server_adapter import ServerConfigAdapter


logger = get_global_logger()


def build_server_ssl_config(app_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build SSL configuration for server from app_config.

    Args:
        app_config: Application configuration dictionary

    Returns:
        Dictionary with SSL configuration for server (hypercorn-ready format)
    """
    server_cfg = (app_config or {}).get("server", {}) or {}
    protocol = str(server_cfg.get("protocol", "http")).lower()
    ssl_section: Optional[Dict[str, Any]] = (
        server_cfg.get("ssl") if isinstance(server_cfg.get("ssl"), dict) else None
    )

    if protocol not in ("https", "mtls"):
        return {}

    if not ssl_section:
        legacy_root = (
            (app_config or {}).get("ssl") if isinstance(app_config, dict) else None
        )
        if isinstance(legacy_root, dict) and legacy_root.get("enabled", False):
            logger.warning(
                "Legacy root-level SSL configuration detected. Migrate to server.ssl."
            )
            ssl_section = {
                "cert": legacy_root.get("cert") or legacy_root.get("cert_file"),
                "key": legacy_root.get("key") or legacy_root.get("key_file"),
                "ca": legacy_root.get("ca")
                or legacy_root.get("ca_cert")
                or legacy_root.get("ca_cert_file"),
                "dnscheck": legacy_root.get("dnscheck", False),
                "verify_client": legacy_root.get("verify_client", False),
            }

    if not ssl_section:
        raise ValueError(
            "CRITICAL CONFIG ERROR: server.ssl section is required when protocol is "
            f"'{protocol}'."
        )

    framework_ssl = _create_framework_ssl_config(ssl_section, protocol)

    try:
        ssl_manager = SSLManager(framework_ssl)
        ssl_context = ssl_manager.create_server_context()
    except (ValidationError, ValueError, SSLConfigurationError) as exc:
        raise ValueError(f"SSL configuration invalid: {exc}") from exc

    logger.info(
        "Server SSL validated via mcp_security_framework",
        extra={
            "cert_file": framework_ssl.cert_file,
            "key_file": framework_ssl.key_file,
            "ca_cert_file": framework_ssl.ca_cert_file,
            "protocol": protocol,
        },
    )

    engine_ssl_dict = {
        "cert": framework_ssl.cert_file,
        "key": framework_ssl.key_file,
        "ca": framework_ssl.ca_cert_file,
        "dnscheck": bool(ssl_section.get("dnscheck", False)),
        "verify_client": protocol == "mtls"
        or bool(ssl_section.get("verify_client", False)),
    }

    converted = ServerConfigAdapter.convert_ssl_config_for_engine(
        engine_ssl_dict, "hypercorn"
    )
    converted["verify_client"] = engine_ssl_dict["verify_client"]
    converted["ssl_context"] = ssl_context
    return converted


def _create_framework_ssl_config(
    ssl_section: Dict[str, Any], protocol: str
) -> FrameworkSSLConfig:
    """
    Convert server.ssl section into framework SSLConfig and validate via SSLManager.
    """
    enabled = protocol in ("https", "mtls")
    verify_client = protocol == "mtls"

    framework_ssl = FrameworkSSLConfig(
        enabled=enabled,
        cert_file=ssl_section.get("cert"),
        key_file=ssl_section.get("key"),
        ca_cert_file=ssl_section.get("ca"),
        verify=verify_client,
        verify_mode="CERT_REQUIRED" if verify_client else "CERT_NONE",
        check_hostname=bool(ssl_section.get("dnscheck", False)),
    )

    return framework_ssl


def is_mtls_enabled(app_config: Dict[str, Any]) -> bool:
    """
    Check if mTLS is enabled in configuration.

    Args:
        app_config: Application configuration dictionary

    Returns:
        True if mTLS is enabled, False otherwise
    """
    server_cfg = (app_config or {}).get("server", {}) or {}
    protocol = str(server_cfg.get("protocol", "http")).lower()
    return protocol == "mtls"
