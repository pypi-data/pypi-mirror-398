"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Configuration parsers for registration context building.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def parse_simple_config_format(
    proxy_registration_config: Dict[str, Any], logger: Any
) -> Optional[Any]:
    """
    Parse SimpleConfig format from registration configuration dict.

    Args:
        proxy_registration_config: Registration configuration dictionary
        logger: Logger instance

    Returns:
        RegistrationConfig object or None if not SimpleConfig format
    """
    if not proxy_registration_config or "heartbeat" not in proxy_registration_config:
        return None

    heartbeat_config = proxy_registration_config.get("heartbeat", {})
    if not isinstance(heartbeat_config, dict) or not heartbeat_config.get("url"):
        return None

    try:
        from mcp_proxy_adapter.core.config.simple_config import (
            HeartbeatConfig,
            SSLConfig,
        )

        # Create HeartbeatConfig object
        heartbeat_obj = HeartbeatConfig(
            url=heartbeat_config.get("url"),
            interval=heartbeat_config.get("interval", 30),
        )

        # Extract certificates from ssl sub-section (new format)
        ssl_config_dict = proxy_registration_config.get("ssl", {})
        cert_file = (
            ssl_config_dict.get("cert")
            if ssl_config_dict and isinstance(ssl_config_dict, dict)
            else None
        )
        key_file = (
            ssl_config_dict.get("key")
            if ssl_config_dict and isinstance(ssl_config_dict, dict)
            else None
        )
        ca_cert_file = (
            ssl_config_dict.get("ca")
            if ssl_config_dict and isinstance(ssl_config_dict, dict)
            else None
        )
        crl_file = (
            ssl_config_dict.get("crl")
            if ssl_config_dict and isinstance(ssl_config_dict, dict)
            else None
        )

        # Create SSLConfig object if we have ssl data
        ssl_obj = None
        if ssl_config_dict and isinstance(ssl_config_dict, dict):
            ssl_obj = SSLConfig(
                cert=cert_file,
                key=key_file,
                ca=ca_cert_file,
                crl=crl_file,
                dnscheck=ssl_config_dict.get("dnscheck", False),
            )

        registration_config = type(
            "RegistrationConfig",
            (),
            {
                "enabled": proxy_registration_config.get("enabled", False),
                "protocol": proxy_registration_config.get("protocol", "http"),
                "register_url": proxy_registration_config.get("register_url"),
                "unregister_url": proxy_registration_config.get("unregister_url"),
                "server_id": proxy_registration_config.get("server_id"),
                "server_name": proxy_registration_config.get("server_name"),
                "instance_uuid": proxy_registration_config.get("instance_uuid"),  # CRITICAL: Preserve UUID
                "ssl": ssl_obj,
                "cert_file": cert_file,
                "key_file": key_file,
                "ca_cert_file": ca_cert_file,
                "crl_file": crl_file,
                "check_hostname": proxy_registration_config.get("check_hostname", True),
                "use_system_ca": proxy_registration_config.get("use_system_ca", False),
                "auto_on_startup": proxy_registration_config.get(
                    "auto_on_startup", True
                ),
                "heartbeat": heartbeat_obj,
            },
        )()
        logger.debug("Using registration section from SimpleConfig format (dict)")
        return registration_config
    except Exception as e:
        logger.debug(f"Could not create RegistrationConfig from dict: {e}")
        return None


def extract_ssl_config_from_model(
    registration_config_from_model: Any,
) -> Optional[Dict[str, Any]]:
    """
    Extract SSL configuration from RegistrationConfig model.

    Args:
        registration_config_from_model: RegistrationConfig model instance

    Returns:
        SSL configuration dictionary or None
    """
    ssl_config = None
    if (
        hasattr(registration_config_from_model, "ssl")
        and registration_config_from_model.ssl
    ):
        ssl_config = {
            "cert": (
                registration_config_from_model.ssl.cert
                if hasattr(registration_config_from_model.ssl, "cert")
                else None
            ),
            "key": (
                registration_config_from_model.ssl.key
                if hasattr(registration_config_from_model.ssl, "key")
                else None
            ),
            "ca": (
                registration_config_from_model.ssl.ca
                if hasattr(registration_config_from_model.ssl, "ca")
                else None
            ),
            "crl": (
                registration_config_from_model.ssl.crl
                if hasattr(registration_config_from_model.ssl, "crl")
                else None
            ),
            "dnscheck": (
                registration_config_from_model.ssl.dnscheck
                if hasattr(registration_config_from_model.ssl, "dnscheck")
                else False
            ),
        }

    return ssl_config


def convert_model_to_dict_config(
    registration_config_from_model: Any, logger: Any
) -> Tuple[Dict[str, Any], str]:
    """
    Convert RegistrationConfig model to dictionary format.

    Args:
        registration_config_from_model: RegistrationConfig model instance
        logger: Logger instance

    Returns:
        Tuple of (proxy_registration_config dict, heartbeat_url)
    """
    heartbeat_url = registration_config_from_model.heartbeat.url
    if not heartbeat_url:
        error_msg = (
            "registration.heartbeat.url is required when registration.enabled=true. "
            "It must be a full URL (e.g., http://localhost:3005/proxy/heartbeat)"
        )
        logger.error(f"❌ Configuration error: {error_msg}")
        raise ValueError(error_msg)

    ssl_config = extract_ssl_config_from_model(registration_config_from_model)

    proxy_registration_config = {
        "enabled": registration_config_from_model.enabled,
        "protocol": registration_config_from_model.protocol,
        "register_url": registration_config_from_model.register_url,
        "unregister_url": registration_config_from_model.unregister_url,
        "server_id": registration_config_from_model.server_id,
        "server_name": getattr(registration_config_from_model, "server_name", None),
        "instance_uuid": getattr(registration_config_from_model, "instance_uuid", None),  # CRITICAL: Preserve UUID
        "ssl": ssl_config,
        "check_hostname": getattr(
            registration_config_from_model, "check_hostname", True
        ),
        "use_system_ca": getattr(
            registration_config_from_model, "use_system_ca", False
        ),
        "auto_on_startup": registration_config_from_model.auto_on_startup,
        "heartbeat": {
            "url": heartbeat_url,
            "interval": registration_config_from_model.heartbeat.interval,
        },
    }
    logger.debug(f"🔍 Created proxy_registration_config with ssl: {ssl_config}")

    return proxy_registration_config, heartbeat_url


def extract_ssl_config_from_dict(
    proxy_registration_config: Dict[str, Any],
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract SSL certificate paths from registration configuration.

    Args:
        proxy_registration_config: Registration configuration dictionary

    Returns:
        Tuple of (cert_file, key_file, ca_cert_file)
    """
    ssl_config = proxy_registration_config.get("ssl", {})
    cert_file = (
        ssl_config.get("cert") if ssl_config and isinstance(ssl_config, dict) else None
    )
    key_file = (
        ssl_config.get("key") if ssl_config and isinstance(ssl_config, dict) else None
    )
    ca_cert_file = (
        ssl_config.get("ca") if ssl_config and isinstance(ssl_config, dict) else None
    )

    return cert_file, key_file, ca_cert_file
