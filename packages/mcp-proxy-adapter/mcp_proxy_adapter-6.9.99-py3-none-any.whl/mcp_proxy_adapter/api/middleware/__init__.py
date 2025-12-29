"""
Middleware package for API.
This package contains middleware components for request processing.
"""

from typing import Dict, Any, Optional
from fastapi import FastAPI

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.config import config
from .factory import MiddlewareFactory
# from .protocol_middleware import setup_protocol_middleware

# Export mcp_security_framework availability
try:
    from .user_info_middleware import _MCP_SECURITY_AVAILABLE
    mcp_security_framework = _MCP_SECURITY_AVAILABLE
except ImportError:
    mcp_security_framework = False


