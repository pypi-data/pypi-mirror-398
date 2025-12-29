"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Universal Client package for MCP Proxy Adapter Framework.
"""

from .client import UniversalClient
from .factory import create_client_from_config

__all__ = ["UniversalClient", "create_client_from_config"]

