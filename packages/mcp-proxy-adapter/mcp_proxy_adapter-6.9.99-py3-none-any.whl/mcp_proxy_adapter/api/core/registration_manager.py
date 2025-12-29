"""Registration management utilities for MCP Proxy Adapter API.

This module is kept for backward compatibility.
New code should import from mcp_proxy_adapter.api.core.registration_manager instead.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

# Re-export from new module structure for backward compatibility
from .registration_manager import (
    RegistrationManager,
    get_registration_status,
    set_registration_status,
    get_stop_flag,
    set_stop_flag,
    set_stop_flag_sync,
)

__all__ = [
    "RegistrationManager",
    "get_registration_status",
    "set_registration_status",
    "get_stop_flag",
    "set_stop_flag",
    "set_stop_flag_sync",
]
