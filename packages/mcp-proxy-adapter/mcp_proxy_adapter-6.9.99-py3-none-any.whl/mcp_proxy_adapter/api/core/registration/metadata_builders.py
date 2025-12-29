"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Metadata builders for registration context.
"""

from __future__ import annotations

from typing import Any, Dict


def build_advertised_url(server_config: Dict[str, Any], logger: Any) -> str:
    """
    Build advertised URL for server registration.

    Args:
        server_config: Server configuration dictionary
        logger: Logger instance

    Returns:
        Advertised URL string
    """
    host = server_config.get("host", "127.0.0.1")
    port = server_config.get("port", 8000)
    protocol = server_config.get("protocol", "http")
    advertised_host = server_config.get("advertised_host") or host
    if advertised_host in ("0.0.0.0", "::", "[::]"):
        logger.info(
            "📡 Server host '%s' is not directly reachable; using 'localhost' for advertised URL",
            advertised_host,
        )
        advertised_host = "localhost"
    scheme = "https" if protocol in ("https", "mtls") else "http"
    advertised_url = f"{scheme}://{advertised_host}:{port}"
    return advertised_url


def build_server_metadata(
    config: Dict[str, Any],
    registration_config: Dict[str, Any],
    server_config: Dict[str, Any],
) -> tuple[str, list[str], Dict[str, Any]]:
    """
    Build server name, capabilities, and metadata for registration.

    Args:
        config: Full configuration dictionary
        registration_config: Registration configuration dictionary
        server_config: Server configuration dictionary

    Returns:
        Tuple of (server_name, capabilities, metadata)
    """
    host = server_config.get("host", "127.0.0.1")
    port = server_config.get("port", 8000)
    protocol = server_config.get("protocol", "http")
    
    # Normalize host for server_name (use localhost for 0.0.0.0, ::, [::])
    host_for_name = host
    if host in ("0.0.0.0", "::", "[::]"):
        host_for_name = "localhost"

    server_name = registration_config.get(
        "server_id"
    ) or registration_config.get("server_name")
    server_name = server_name or f"mcp-adapter-{host_for_name}-{port}"
    capabilities = registration_config.get(
        "capabilities", ["jsonrpc", "health"]
    )
    # Extract UUID from registration config (instance_uuid) or fallback to config uuid
    uuid_value = registration_config.get("instance_uuid") or config.get("uuid")
    
    metadata = {
        "protocol": protocol,
        "host": host,
        "port": port,
        **(registration_config.get("metadata") or {}),
    }
    
    # Include UUID in metadata temporarily for extraction by proxy_api.py
    # UUID will be extracted from metadata, removed from metadata, and placed at root level of payload
    if uuid_value:
        metadata["uuid"] = uuid_value

    return server_name, capabilities, metadata
