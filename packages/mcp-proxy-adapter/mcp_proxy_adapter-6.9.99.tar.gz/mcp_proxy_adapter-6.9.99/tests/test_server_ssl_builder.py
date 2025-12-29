"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Tests for server SSL configuration builder.
"""

from pathlib import Path
from typing import Dict

import pytest

from mcp_proxy_adapter.core.app_factory import ssl_config as ssl_module

# Use real test certificates from mtls_certificates
BASE_DIR = Path(__file__).parent.parent
CERTS_DIR = BASE_DIR / "mtls_certificates"
SERVER_CERT = str(CERTS_DIR / "server" / "test-server.crt")
SERVER_KEY = str(CERTS_DIR / "server" / "test-server.key")
SERVER_CA = str(CERTS_DIR / "ca" / "ca.crt")


def test_build_server_ssl_config_https() -> None:
    """Test building HTTPS SSL configuration using real certificates."""
    app_cfg = {
        "server": {
            "protocol": "https",
            "ssl": {
                "cert": SERVER_CERT,
                "key": SERVER_KEY,
                "ca": SERVER_CA,
                "dnscheck": False,
            },
        }
    }

    result = ssl_module.build_server_ssl_config(app_cfg)

    assert result["certfile"] == SERVER_CERT
    assert result["keyfile"] == SERVER_KEY
    assert result["ca_certs"] == SERVER_CA
    assert result["check_hostname"] is False
    assert result["verify_client"] is False
    assert "ssl_context" in result


def test_build_server_ssl_config_http_returns_empty() -> None:
    """Test that HTTP protocol returns empty SSL config."""
    app_cfg = {
        "server": {
            "protocol": "http",
            "ssl": {
                "cert": SERVER_CERT,
                "key": SERVER_KEY,
                "ca": SERVER_CA,
            },
        }
    }

    result = ssl_module.build_server_ssl_config(app_cfg)

    assert result == {}


def test_build_server_ssl_config_fallback_to_legacy_root() -> None:
    """Test fallback to legacy root-level SSL configuration."""
    app_cfg = {
        "server": {
            "protocol": "https",
            "host": "0.0.0.0",
            "port": 8080,
        },
        "ssl": {
            "enabled": True,
            "cert_file": SERVER_CERT,
            "key_file": SERVER_KEY,
            "ca_cert_file": SERVER_CA,
            "dnscheck": False,
        },
    }

    result = ssl_module.build_server_ssl_config(app_cfg)

    assert result["certfile"] == SERVER_CERT
    assert result["verify_client"] is False
    assert "ssl_context" in result


def test_build_server_ssl_config_https_missing_ssl_raises() -> None:
    app_cfg = {"server": {"protocol": "https"}}

    with pytest.raises(ValueError):
        ssl_module.build_server_ssl_config(app_cfg)
