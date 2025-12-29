"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Configuration helpers for API AppFactory.
"""

from typing import Any, Dict, Optional


def resolve_current_config(app_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Resolve application configuration from provided source or global config.

    Args:
        app_config: Configuration dict or config object.

    Returns:
        Dictionary with resolved configuration.
    """
    if app_config is not None:
        if hasattr(app_config, "get_all"):
            return app_config.get_all()
        if hasattr(app_config, "keys"):
            return app_config
        return app_config

    try:
        from mcp_proxy_adapter.config import get_config

        return get_config().get_all()
    except Exception:
        return {}


def debug_config_info(app_config: Optional[Dict[str, Any]]) -> None:
    """
    Print debug information about provided configuration.

    Args:
        app_config: Configuration dict or config object.
    """
    if not app_config:
        print("🔍 Debug: create_app received no app_config, using global config")
        return

    if hasattr(app_config, "keys"):
        keys = list(app_config.keys())
        print(f"🔍 Debug: create_app received app_config keys: {keys}")
        protocol = app_config.get("server", {}).get("protocol", "http")  # type: ignore[arg-type]
        verify_client = app_config.get("transport", {}).get("verify_client", False)  # type: ignore[arg-type]
        ssl_enabled = protocol in ["https", "mtls"] or verify_client
        print(f"🔍 Debug: create_app SSL config: enabled={ssl_enabled}")
        print(f"🔍 Debug: create_app protocol: {protocol}")
        print(f"🔍 Debug: create_app verify_client: {verify_client}")
    else:
        print(f"🔍 Debug: create_app received app_config type: {type(app_config)}")


