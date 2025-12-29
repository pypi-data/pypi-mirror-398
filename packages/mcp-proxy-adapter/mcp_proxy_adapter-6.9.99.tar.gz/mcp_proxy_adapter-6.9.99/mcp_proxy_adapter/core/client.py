"""Universal Client for MCP Proxy Adapter Framework.

This module is kept for backward compatibility.
New code should import from mcp_proxy_adapter.core.client instead.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

# Re-export from new module structure for backward compatibility
from .client import UniversalClient, create_client_from_config

__all__ = ["UniversalClient", "create_client_from_config"]
