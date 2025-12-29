"""
Configuration Converter for security framework integration.

This module provides utilities to convert between mcp_proxy_adapter configuration
format and mcp_security_framework configuration format, ensuring backward compatibility.
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from mcp_proxy_adapter.core.logging import get_global_logger


class ConfigConverter:
    """
    Converter for configuration formats.

    Provides methods to convert between mcp_proxy_adapter configuration
    and mcp_security_framework configuration formats.
    """

    @staticmethod
    def to_security_framework_config(mcp_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert mcp_proxy_adapter configuration to SecurityConfig format.

        Args:
            mcp_config: mcp_proxy_adapter configuration dictionary

        Returns:
            SecurityConfig compatible dictionary
        """
        try:
            # Start with default security framework config
            security_config = {
                "auth": {
                    "enabled": True,
                    "methods": ["api_key"],
                    "api_keys": {},
                    "jwt_secret": "",
                    "jwt_algorithm": "HS256",
                },
                "ssl": {
                    "enabled": False,
                    "cert_file": None,
                    "key_file": None,
                    "ca_cert": None,
                    "min_tls_version": "TLSv1.2",
                    "verify_client": False,
                    "client_cert_required": False,
                },
                "permissions": {
                    "enabled": True,
                    "roles_file": "roles.json",
                    "default_role": "user",
                    "deny_by_default": True,
                },
                "rate_limit": {
                    "enabled": True,
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                    "burst_limit": 10,
                    "by_ip": True,
                    "by_user": True,
                },
            }

            # Convert from security section if exists
            if "security" in mcp_config:
                security_section = mcp_config["security"]

                # Convert auth config
                if "auth" in security_section:
                    auth_config = security_section["auth"]
                    security_config["auth"].update(
                        {
                            "enabled": auth_config.get("enabled", True),
                            "methods": auth_config.get("methods", ["api_key"]),
                            "api_keys": auth_config.get("api_keys", {}),
                            "jwt_secret": auth_config.get("jwt_secret", ""),
                            "jwt_algorithm": auth_config.get("jwt_algorithm", "HS256"),
                        }
                    )

                # Convert SSL config
                if "ssl" in security_section:
                    ssl_config = security_section["ssl"]
                    security_config["ssl"].update(
                        {
                            "enabled": ssl_config.get("enabled", False),
                            "cert_file": ssl_config.get("cert_file"),
                            "key_file": ssl_config.get("key_file"),
                            "ca_cert": ssl_config.get("ca_cert"),
                            "min_tls_version": ssl_config.get(
                                "min_tls_version", "TLSv1.2"
                            ),
                            "verify_client": ssl_config.get("verify_client", False),
                            "client_cert_required": ssl_config.get(
                                "client_cert_required", False
                            ),
                        }
                    )

                # Convert permissions config
                if "permissions" in security_section:
                    permissions_config = security_section["permissions"]
                    security_config["permissions"].update(
                        {
                            "enabled": permissions_config.get("enabled", True),
                            "roles_file": permissions_config.get(
                                "roles_file", "roles.json"
                            ),
                            "default_role": permissions_config.get(
                                "default_role", "user"
                            ),
                            "deny_by_default": permissions_config.get(
                                "deny_by_default", True
                            ),
                        }
                    )

                # Convert rate limit config
                if "rate_limit" in security_section:
                    rate_limit_config = security_section["rate_limit"]
                    security_config["rate_limit"].update(
                        {
                            "enabled": rate_limit_config.get("enabled", True),
                            "requests_per_minute": rate_limit_config.get(
                                "requests_per_minute", 60
                            ),
                            "requests_per_hour": rate_limit_config.get(
                                "requests_per_hour", 1000
                            ),
                            "burst_limit": rate_limit_config.get("burst_limit", 10),
                            "by_ip": rate_limit_config.get("by_ip", True),
                            "by_user": rate_limit_config.get("by_user", True),
                        }
                    )

            # Convert from legacy SSL config if security section doesn't exist
            elif "ssl" in mcp_config:
                ssl_config = mcp_config["ssl"]
                security_config["ssl"].update(
                    {
                        "enabled": ssl_config.get("enabled", False),
                        "cert_file": ssl_config.get("cert_file"),
                        "key_file": ssl_config.get("key_file"),
                        "ca_cert": ssl_config.get("ca_cert"),
                        "min_tls_version": ssl_config.get("min_tls_version", "TLSv1.2"),
                        "verify_client": ssl_config.get("verify_client", False),
                        "client_cert_required": ssl_config.get(
                            "client_cert_required", False
                        ),
                    }
                )

                # Extract API keys from legacy SSL config
                if "api_keys" in ssl_config:
                    security_config["auth"]["api_keys"] = ssl_config["api_keys"]

            # Convert from legacy roles config
            if "roles" in mcp_config:
                roles_config = mcp_config["roles"]
                security_config["permissions"].update(
                    {
                        "enabled": roles_config.get("enabled", True),
                        "roles_file": roles_config.get("config_file", "roles.json"),
                        "default_role": "user",
                        "deny_by_default": roles_config.get("default_policy", {}).get(
                            "deny_by_default", True
                        ),
                    }
                )

            get_global_logger().info(
                "Configuration converted to security framework format successfully"
            )
            return security_config

        except Exception as e:
            get_global_logger().error(
                f"Failed to convert configuration to security framework format: {e}"
            )
            return ConfigConverter._get_default_security_config()

    @staticmethod

    @staticmethod

    @staticmethod

    @staticmethod
    def _get_default_security_config() -> Dict[str, Any]:
        """
        Get default security framework configuration.

        Returns:
            Default security framework configuration
        """
        return {
            "auth": {
                "enabled": True,
                "methods": ["api_key"],
                "api_keys": {},
                "jwt_secret": "",
                "jwt_algorithm": "HS256",
            },
            "ssl": {
                "enabled": False,
                "cert_file": None,
                "key_file": None,
                "ca_cert": None,
                "min_tls_version": "TLSv1.2",
                "verify_client": False,
                "client_cert_required": False,
            },
            "permissions": {
                "enabled": True,
                "roles_file": "roles.json",
                "default_role": "user",
                "deny_by_default": True,
            },
            "rate_limit": {
                "enabled": True,
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "burst_limit": 10,
                "by_ip": True,
                "by_user": True,
            },
        }

    @staticmethod
    def _get_default_mcp_config() -> Dict[str, Any]:
        """
        Get default mcp_proxy_adapter configuration.

        Returns:
            Default mcp_proxy_adapter configuration
        """
        return {
            "security": {
                "framework": "mcp_security_framework",
                "enabled": True,
                "auth": {"enabled": True, "methods": ["api_key"], "api_keys": {}},
                "ssl": {"enabled": False, "cert_file": None, "key_file": None},
                "permissions": {"enabled": True, "roles_file": "roles.json"},
                "rate_limit": {"enabled": True, "requests_per_minute": 60},
            }
        }
