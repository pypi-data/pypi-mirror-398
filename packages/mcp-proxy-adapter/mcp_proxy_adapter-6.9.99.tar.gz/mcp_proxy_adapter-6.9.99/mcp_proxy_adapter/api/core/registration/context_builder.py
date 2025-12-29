"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Context builder for registration with proxy server.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .models import RegistrationContext
from .resolvers import resolve_registration_credentials
from .config_parsers import (
    parse_simple_config_format,
    convert_model_to_dict_config,
)
from .url_builders import (
    build_proxy_url_from_registration_config,
)
from .metadata_builders import build_advertised_url, build_server_metadata


def prepare_registration_context(
    config: Dict[str, Any], logger: Any
) -> Optional[RegistrationContext]:
    """Build registration context from configuration.

    Uses registration section from SimpleConfigModel (independent from server section).
    Only supports the new "registration" format.

    Returns ``None`` when registration should not be performed.
    """
    # Only use "registration" key from config
    registration_config = dict(config.get("registration") or {})
    
    if not registration_config:
        logger.info("No registration section found in configuration")
        return None

    # Try to parse SimpleConfig format
    registration_config_from_model = parse_simple_config_format(
        registration_config, logger
    )

    # Initialize registration_enabled
    registration_enabled = False

    # Use registration from SimpleConfigModel if available
    if registration_config_from_model:
        registration_config, _ = convert_model_to_dict_config(
            registration_config_from_model, logger
        )
        # CRITICAL: Preserve instance_uuid from original config if it was lost
        if "instance_uuid" not in registration_config or not registration_config.get("instance_uuid"):
            original_uuid = config.get("registration", {}).get("instance_uuid")
            if original_uuid:
                registration_config["instance_uuid"] = original_uuid
                logger.debug(f"🔍 Restored instance_uuid from original config: {original_uuid}")
        registration_enabled = (
            registration_config_from_model.enabled
            and registration_config_from_model.auto_on_startup
        )
    elif registration_config and "heartbeat" in registration_config:
        # registration_config already has heartbeat - use it directly (SimpleConfig format)
        heartbeat_config = registration_config.get("heartbeat", {})
        if isinstance(heartbeat_config, dict) and heartbeat_config.get("url"):
            # heartbeat.url exists - this is SimpleConfig format
            registration_enabled = registration_config.get(
                "enabled", False
            ) and registration_config.get("auto_on_startup", True)
            logger.debug(
                f"Using SimpleConfig format: enabled={registration_enabled}, "
                f"heartbeat.url={heartbeat_config.get('url')}"
            )
        else:
            # heartbeat exists but url is missing - error
            error_msg = (
                "registration.heartbeat.url is required when registration.enabled=true. "
                "It must be a full URL (e.g., http://localhost:3005/proxy/heartbeat)"
            )
            logger.error(f"❌ Configuration error: {error_msg}")
            raise ValueError(error_msg)
    else:
        # Invalid format - registration section must have heartbeat.url
        error_msg = (
            "registration.heartbeat.url is required when registration.enabled=true. "
            "It must be a full URL (e.g., http://localhost:3005/proxy/heartbeat)"
        )
        logger.error(f"❌ Configuration error: {error_msg}")
        raise ValueError(error_msg)

    if not registration_enabled:
        logger.info(
            "Proxy registration disabled (auto_on_startup=false or enabled=false)"
        )
        return None

    # Build proxy URL and register endpoint
    result = build_proxy_url_from_registration_config(
        registration_config, logger
    )
    if result[0] is None:
        return None
    proxy_url, register_endpoint, _, _, _, _ = result

    # Build server metadata
    server_config = dict(config.get("server") or {})
    advertised_url = build_advertised_url(server_config, logger)
    server_name, capabilities, metadata = build_server_metadata(
        config,
        registration_config,
        server_config,
    )

    # Resolve credentials
    credentials = resolve_registration_credentials(
        registration_config
    )

    return RegistrationContext(
        server_name=server_name,
        advertised_url=advertised_url,
        proxy_url=proxy_url,
        register_endpoint=register_endpoint,
        capabilities=capabilities,
        metadata=metadata,
        proxy_registration_config=registration_config,
        credentials=credentials,
    )
