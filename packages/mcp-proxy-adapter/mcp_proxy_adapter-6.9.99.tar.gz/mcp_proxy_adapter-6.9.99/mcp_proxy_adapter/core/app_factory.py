"""Application Factory for MCP Proxy Adapter

This module is kept for backward compatibility.
New code should import from mcp_proxy_adapter.core.app_factory instead.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

# Re-export from new module structure for backward compatibility
from .app_factory import (
    create_and_run_server,
    validate_config_file,
    validate_log_config_file,
    create_application,
)

__all__ = [
    "create_and_run_server",
    "validate_config_file",
    "validate_log_config_file",
    "create_application",
]
