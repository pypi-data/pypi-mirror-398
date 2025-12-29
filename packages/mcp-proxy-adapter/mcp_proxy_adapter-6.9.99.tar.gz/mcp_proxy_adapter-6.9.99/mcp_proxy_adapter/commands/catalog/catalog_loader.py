"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Catalog loading utilities for MCP Proxy Adapter.
"""

import json
from pathlib import Path

from mcp_proxy_adapter.core.logging import get_global_logger
from .command_catalog import CommandCatalog

# Try to import requests, but don't fail if not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    get_global_logger().warning(
        "requests library not available, HTTP/HTTPS functionality will be limited"
    )


class CatalogLoader:
    """Loader for command catalogs from various sources."""

    def __init__(self):
        """Initialize catalog loader."""
        self.logger = get_global_logger()




