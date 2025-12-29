"""
Middleware for request logging.
"""

import time
import json
import uuid
from typing import Callable, Awaitable, Dict, Any

from fastapi import Request, Response

from mcp_proxy_adapter.core.logging import get_global_logger, RequestLogger
from .base import BaseMiddleware


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware for logging requests and responses.
    """

    def __init__(self, app, config: Dict[str, Any] = None):
        """
        Initialize logging middleware.

        Args:
            app: FastAPI application
            config: Application configuration (optional)
        """
        super().__init__(app)
        self.config = config or {}

