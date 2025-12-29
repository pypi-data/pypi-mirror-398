"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Resolver functions for registration credentials, heartbeat settings, and endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

from .models import ProxyCredentials, HeartbeatSettings
from .helpers import build_cert_tuple


def resolve_runtime_credentials(
    registration_config: Dict[str, Any],
) -> ProxyCredentials:
    """Return credentials for runtime interactions (heartbeat, unregister)."""
    return resolve_registration_credentials(registration_config)


def resolve_heartbeat_settings(
    registration_config: Dict[str, Any],
    proxy_url: str,
) -> HeartbeatSettings:
    """Compute heartbeat interval and full URL from configuration only.

    Args:
        registration_config: Registration configuration dict
        proxy_url: Base proxy URL (e.g., "http://localhost:3005") - not used, kept for compatibility

    Returns:
        HeartbeatSettings with interval and full URL from config
    """
    heartbeat_config = registration_config.get("heartbeat") or {}
    interval = int(
        heartbeat_config.get(
            "interval",
            registration_config.get("heartbeat_interval", 30),
        )
    )
    # URL must be provided in config - no auto-generation
    heartbeat_url = heartbeat_config.get("url")
    if not heartbeat_url:
        # Debug: log what we have
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"❌ heartbeat.url is missing. registration_config keys: {list(registration_config.keys())}"
        )
        logger.error(f"❌ heartbeat_config: {heartbeat_config}")
        raise ValueError(
            "heartbeat.url is required in registration.heartbeat configuration"
        )

    return HeartbeatSettings(interval=interval, url=heartbeat_url)


def resolve_unregister_endpoint(
    registration_config: Dict[str, Any],
) -> str:
    """Get unregister endpoint path."""
    endpoint = registration_config.get("unregister_endpoint")
    if endpoint:
        return str(endpoint)
    return "/unregister"


def resolve_registration_credentials(
    registration_config: Dict[str, Any],
) -> ProxyCredentials:
    """
    Resolve registration credentials from configuration.

    Args:
        registration_config: Registration configuration dictionary

    Returns:
        ProxyCredentials instance with resolved certificate and verification settings

    Raises:
        ValueError: If required configuration is missing
    """
    # SimpleConfig format stores URLs in register_url
    proxy_url_candidate: Optional[str] = registration_config.get("register_url")

    register_url = registration_config.get("register_url")
    if register_url:
        parsed_register = urlparse(str(register_url))
        proxy_url_candidate = f"{parsed_register.scheme}://{parsed_register.netloc}"

    if proxy_url_candidate:
        parsed = urlparse(str(proxy_url_candidate))
        url_scheme = parsed.scheme or "http"
    else:
        url_scheme = "http"

    # New SimpleConfig format: certificates are in ssl sub-section
    ssl_config = registration_config.get("ssl")
    if ssl_config is None:
        ssl_config = {}
    elif not isinstance(ssl_config, dict):
        # ssl_config might be SSLConfig object - convert to dict
        ssl_config = {
            "cert": getattr(ssl_config, "cert", None),
            "key": getattr(ssl_config, "key", None),
            "ca": getattr(ssl_config, "ca", None),
            "crl": getattr(ssl_config, "crl", None),
            "dnscheck": getattr(ssl_config, "dnscheck", False),
        }
    cert_file = ssl_config.get("cert") if isinstance(ssl_config, dict) else None
    key_file = ssl_config.get("key") if isinstance(ssl_config, dict) else None
    ca_cert = ssl_config.get("ca") if isinstance(ssl_config, dict) else None
    crl_file = ssl_config.get("crl") if isinstance(ssl_config, dict) else None


    # Determine verify_mode (legacy ssl.verify_mode or new field)
    verify_mode = "CERT_REQUIRED"
    if isinstance(ssl_config, dict):
        verify_mode = ssl_config.get("verify_mode", verify_mode)
    verify_mode = registration_config.get("verify_mode", verify_mode)

    cert_tuple = build_cert_tuple(cert_file, key_file)

    # Determine protocol: distinguish between HTTPS and mTLS (same logic as prepare_registration_context)
    if url_scheme == "https" and cert_tuple and ca_cert:
        # All conditions for mTLS met: https:// + client certs + CA cert
        proxy_protocol = "mtls"
    elif url_scheme == "https":
        # HTTPS: https:// scheme, but not all mTLS requirements met
        proxy_protocol = "https"
    else:
        # HTTP
        proxy_protocol = "http"

    # For mTLS, certificates are required
    if proxy_protocol == "mtls":
        if not cert_tuple:
            error_msg = (
                "registration.certificate.cert_file and registration.certificate.key_file "
                "are required when using mTLS (https:// scheme with CA cert)"
            )
            raise ValueError(error_msg)
        if not ca_cert:
            error_msg = (
                "registration.ssl.ca_cert is required when using mTLS "
                "(https:// scheme with client certs)"
            )
            raise ValueError(error_msg)

    verify: Union[bool, str] = True
    if verify_mode == "CERT_NONE":
        verify = False
    elif ca_cert:
        verify = ca_cert
    elif proxy_protocol == "mtls":
        # mTLS requires CA cert - should have been checked above
        verify = True  # Will fail if no CA, but that's expected
    elif proxy_protocol == "https":
        # HTTPS can use system CA store
        verify = True
    else:
        # HTTP
        verify = False

    # Extract check_hostname from ssl config
    check_hostname = True  # Default: verify hostname
    if isinstance(ssl_config, dict):
        check_hostname = ssl_config.get("check_hostname", ssl_config.get("dnscheck", True))
    # For HTTP, always disable hostname check
    if proxy_protocol == "http":
        check_hostname = False

    return ProxyCredentials(cert=cert_tuple, verify=verify, check_hostname=check_hostname)

