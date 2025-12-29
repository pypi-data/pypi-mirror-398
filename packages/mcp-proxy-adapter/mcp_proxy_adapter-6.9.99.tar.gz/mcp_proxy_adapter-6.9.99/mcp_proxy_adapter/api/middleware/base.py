"""
Base middleware module.
"""

from typing import Callable, Awaitable
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

from mcp_proxy_adapter.core.logging import get_global_logger


class BaseMiddleware(BaseHTTPMiddleware):
    """
    Base class for all middleware.
    """


    async def before_request(self, request: Request) -> None:
        """
        Method for processing request before calling the main handler.

        Args:
            request: Request.
        """
        pass

    async def after_response(self, request: Request, response: Response) -> Response:
        """
        Method for processing response after calling the main handler.

        Args:
            request: Request.
            response: Response.

        Returns:
            Processed response.
        """
        return response

    async def handle_error(self, request: Request, exception: Exception) -> Response:
        """
        Method for handling errors that occurred in middleware.

        Args:
            request: Request.
            exception: Exception.

        Returns:
            Error response.
        """
        # By default, just pass the error further
        raise exception
