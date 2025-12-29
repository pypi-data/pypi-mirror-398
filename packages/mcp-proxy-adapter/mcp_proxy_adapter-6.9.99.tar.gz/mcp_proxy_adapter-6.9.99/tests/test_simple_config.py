"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Unit tests for SimpleConfig, SimpleConfigValidator and SimpleConfigGenerator.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp_proxy_adapter.core.config.simple_config import SimpleConfig
from mcp_proxy_adapter.core.config.simple_config_generator import (
    SimpleConfigGenerator,
)
from mcp_proxy_adapter.core.config.simple_config_validator import SimpleConfigValidator


def write_temp_config(tmp_path: Path, data: dict, name: str = "config.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_load_and_validate_http_minimal(tmp_path: Path) -> None:
    data = {
        "server": {"host": "0.0.0.0", "port": 8080, "protocol": "http"},
        "proxy_client": {"enabled": False},
        "auth": {"use_token": False, "use_roles": False},
    }
    cfg_path = write_temp_config(tmp_path, data)

    cfg = SimpleConfig(str(cfg_path))
    model = cfg.load()

    validator = SimpleConfigValidator()
    errors = validator.validate(model)
    assert errors == []


def test_generator_creates_valid_https(tmp_path: Path) -> None:
    out_path = tmp_path / "gen.json"
    gen = SimpleConfigGenerator()
    gen.generate(protocol="https", with_proxy=False, out_path=str(out_path))

    cfg = SimpleConfig(str(out_path))
    model = cfg.load()

    # Adjust certificate paths to non-existing is acceptable; validator should flag missing files
    validator = SimpleConfigValidator()
    errors = validator.validate(model)

    # For https without real files, expect at least missing file errors
    # Generator creates paths like ./certs/server.crt which don't exist
    # Validator should flag missing files with server.ssl.cert or server.ssl.key
    assert any(
        "server.ssl.cert" in e.message or "server.ssl.key" in e.message for e in errors
    )


