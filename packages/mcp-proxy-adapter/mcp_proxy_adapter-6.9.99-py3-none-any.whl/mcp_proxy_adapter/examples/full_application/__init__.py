"""Full Application Example.

This example demonstrates advanced usage of MCP Proxy Adapter including:
- Proxy registration endpoints
- Custom command hooks
- Advanced security configurations
- Role-based access control
"""

# Note: main.py doesn't export get_app, it's a standalone script
# Import proxy router for use in other modules if needed
from .proxy_endpoints import router as proxy_router
