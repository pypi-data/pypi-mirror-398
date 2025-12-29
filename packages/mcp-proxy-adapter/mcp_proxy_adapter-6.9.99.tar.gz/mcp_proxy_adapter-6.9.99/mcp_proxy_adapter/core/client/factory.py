"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Factory functions for creating UniversalClient instances.
"""

import json
import os
from typing import Dict, Any

from .client import UniversalClient


def create_client_from_config(config_file: str) -> UniversalClient:
    """
    Create a UniversalClient instance from a configuration file.

    Args:
        config_file: Path to configuration file

    Returns:
        UniversalClient instance
    """
    try:
        with open(config_file, "r") as f:
            config_data = json.load(f)

        # Extract server configuration
        server_config = config_data.get("server", {})
        host = server_config.get("host", "127.0.0.1")
        port = server_config.get("port", 8000)

        # Determine protocol
        ssl_config = config_data.get("ssl", {})
        ssl_enabled = ssl_config.get("enabled", False)
        protocol = "https" if ssl_enabled else "http"

        server_url = f"{protocol}://{host}:{port}"

        # Create client configuration
        client_config = {
            "server_url": server_url,
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1,
            "security": {"auth_method": "none"},
        }

        # Add SSL configuration if needed
        if ssl_enabled:
            client_config["security"]["ssl"] = {
                "enabled": True,
                "check_hostname": False,
                "verify": False,
            }

            # Add CA certificate if available
            ca_cert = ssl_config.get("ca_cert")
            if ca_cert and os.path.exists(ca_cert):
                client_config["security"]["ssl"]["ca_cert_file"] = ca_cert

        return UniversalClient(client_config)

    except Exception as e:
        raise ValueError(f"Failed to create client from config: {e}")

