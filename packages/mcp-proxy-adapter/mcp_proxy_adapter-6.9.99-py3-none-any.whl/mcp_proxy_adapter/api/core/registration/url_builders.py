"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

URL builders for proxy registration context.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from .helpers import build_cert_tuple
from .config_parsers import extract_ssl_config_from_dict


def build_proxy_url_from_registration_config(
    registration_config: Dict[str, Any], logger: Any
) -> Tuple[str, str, str, Optional[str], Optional[str], Optional[str]]:
    """
    Build proxy URL and extract protocol from registration configuration.

    Args:
        registration_config: Registration configuration dictionary
        logger: Logger instance

    Returns:
        Tuple of (proxy_url, register_endpoint, proxy_protocol, cert_file, key_file, ca_cert_file)
    """
    # Check for register_url
    proxy_url_candidate = registration_config.get("register_url")
    if not proxy_url_candidate:
        logger.warning("No proxy server URL configured")
        return None, None, None, None, None, None

    # If register_url is provided (new format), extract base URL from it
    if registration_config.get("register_url"):
        parsed_register_url = urlparse(registration_config.get("register_url"))
        # Extract base URL (scheme://host:port) from register_url
        proxy_url_candidate = (
            f"{parsed_register_url.scheme}://{parsed_register_url.netloc}"
        )
        logger.debug(f"Extracted proxy URL from register_url: {proxy_url_candidate}")

    # Extract certificates
    cert_file, key_file, ca_cert_file = extract_ssl_config_from_dict(
        registration_config
    )

    cert_tuple = build_cert_tuple(cert_file, key_file)

    # Parse proxy_url to extract components
    proxy_url_str = str(proxy_url_candidate)
    parsed_candidate = urlparse(proxy_url_str)

    # Extract host and port first
    proxy_host = parsed_candidate.hostname or (
        proxy_url_str.split("://")[-1].split(":")[0]
        if "://" in proxy_url_str
        else proxy_url_str.split(":")[0]
    )
    proxy_port = parsed_candidate.port or (
        int(proxy_url_str.split(":")[-1].split("/")[0])
        if ":" in proxy_url_str and proxy_url_str.split(":")[-1].split("/")[0].isdigit()
        else 3005
    )

    # Determine protocol: distinguish between HTTPS and mTLS
    url_scheme = parsed_candidate.scheme
    if not url_scheme:
        error_msg = (
            "registration.proxy_url must include protocol scheme (http:// or https://). "
            f"Got: {proxy_url_candidate}"
        )
        logger.error(f"❌ Configuration error: {error_msg}")
        raise ValueError(error_msg)

    if url_scheme not in ("http", "https"):
        error_msg = (
            f"Invalid protocol scheme in registration.proxy_url: {url_scheme}. "
            "Must be http:// or https://"
        )
        logger.error(f"❌ Configuration error: {error_msg}")
        raise ValueError(error_msg)

    # Determine if it's mTLS: https:// scheme + all certificates present
    if url_scheme == "https" and cert_tuple and ca_cert_file:
        # All conditions for mTLS met: https:// + client certs + CA cert
        proxy_protocol = "mtls"
        logger.debug(
            "Detected mTLS protocol: https:// scheme with client certificates and CA cert"
        )
    elif url_scheme == "https":
        # HTTPS: https:// scheme, but not all mTLS requirements met
        proxy_protocol = "https"
        logger.debug("Detected HTTPS protocol: https:// scheme")
    else:
        # HTTP
        proxy_protocol = "http"
        logger.debug("Detected HTTP protocol")

    # Build final URL with correct protocol (always use https:// for mTLS)
    proxy_scheme = "https" if proxy_protocol in ("https", "mtls") else "http"
    proxy_url = f"{proxy_scheme}://{proxy_host}:{proxy_port}"

    register_endpoint = "/register"

    return (
        proxy_url,
        register_endpoint,
        proxy_protocol,
        cert_file,
        key_file,
        ca_cert_file,
    )
