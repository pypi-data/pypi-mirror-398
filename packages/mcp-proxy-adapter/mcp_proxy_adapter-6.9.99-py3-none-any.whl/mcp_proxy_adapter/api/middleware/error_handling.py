"""
Middleware for error handling.
"""

import json
from typing import Optional, Any

from fastapi import Request, Response
from starlette.responses import JSONResponse

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.errors import (
    MicroserviceError,
    CommandError,
    ValidationError,
)
from .base import BaseMiddleware


class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Middleware for handling and formatting errors.
    """

    def __init__(self, app):
        """
        Initialize error handling middleware.

        Args:
            app: FastAPI application
        """
        super().__init__(app)


    def _is_json_rpc_request(self, request: Request) -> bool:
        """
        Checks if request is a JSON-RPC request.

        Args:
            request: Request.

        Returns:
            True if request is JSON-RPC, False otherwise.
        """
        # Only requests to /api/jsonrpc are JSON-RPC requests
        return request.url.path == "/api/jsonrpc"

    async def _get_json_rpc_id(self, request: Request) -> Optional[Any]:
        """
        Gets JSON-RPC request ID.

        Args:
            request: Request.

        Returns:
            JSON-RPC request ID if available, None otherwise.
        """
        try:
            # Use request state to avoid body parsing if already done
            if hasattr(request.state, "json_rpc_id"):
                return request.state.json_rpc_id

            # Parse request body
            body = await request.body()
            if body:
                body_text = body.decode("utf-8")
                body_json = json.loads(body_text)
                request_id = body_json.get("id")

                # Save ID in request state to avoid reparsing
                request.state.json_rpc_id = request_id
                return request_id
        except Exception as e:
            get_global_logger().warning(f"Error parsing JSON-RPC ID: {str(e)}")

        return None
