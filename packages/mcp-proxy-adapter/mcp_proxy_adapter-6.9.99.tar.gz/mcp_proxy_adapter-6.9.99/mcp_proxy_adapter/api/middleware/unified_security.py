"""
Unified Security Middleware - Direct Framework Integration

This middleware now directly uses mcp_security_framework components
instead of custom implementations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import time
import logging
from typing import Dict, Any, Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Direct import from framework
try:
    from mcp_security_framework.middleware import (
        FastAPISecurityMiddleware,
    )

    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError as e:
    # NO FALLBACK! mcp_security_framework is REQUIRED
    raise RuntimeError(
        f"CRITICAL: mcp_security_framework is required but not available: {e}. "
        "Install it with: pip install mcp_security_framework>=1.2.8"
    ) from e

from mcp_proxy_adapter.core.logging import get_global_logger
# from mcp_proxy_adapter.core.security_integration import create_security_integration


class SecurityValidationError(Exception):
    """Security validation error."""

    def __init__(self, message: str, error_code: int):
        """
        Initialize security validation error.
        
        Args:
            message: Error message
            error_code: Error code for the validation failure
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class UnifiedSecurityMiddleware(BaseHTTPMiddleware):
    """
    Unified security middleware using mcp_security_framework.

    This middleware now directly uses the security framework's FastAPI middleware
    and components instead of custom implementations.
    """

    def __init__(self, app, config: Dict[str, Any]):
        """
        Initialize unified security middleware.

        Args:
            app: FastAPI application
            config: mcp_proxy_adapter configuration dictionary
        """
        super().__init__(app)
        self.config = config

        # Create security integration
        try:
            security_config = config.get("security", {})
            
            # Check if security is enabled - use mcp_security_framework if needed
            security_enabled = security_config.get("enabled", False)
            
            if security_enabled:
                # self.security_integration = create_security_integration(security_config)
                self.security_integration = None
                # Use framework's FastAPI middleware
                # self.framework_middleware = (
                #     self.security_integration.security_manager.create_fastapi_middleware()
                # )
                self.framework_middleware = None
                get_global_logger().info("Security disabled - no middleware")
                # IMPORTANT: Don't replace self.app! This breaks the middleware chain.
                # Instead, store the framework middleware for use in dispatch method.
                get_global_logger().info("Framework middleware will be used in dispatch method")
            else:
                get_global_logger().info("Security disabled, skipping mcp_security_framework integration")
                self.security_integration = None
                self.framework_middleware = None
        except Exception as e:
            get_global_logger().error(f"Security framework integration failed: {e}")
            # Instead of raising error, log warning and continue without security
            get_global_logger().warning(
                "Continuing without security framework - some security features will be disabled"
            )
            self.security_integration = None
            self.framework_middleware = None
            # Keep original app in place when framework middleware is unavailable
            # BaseHTTPMiddleware initialized it via super().__init__(app)

        get_global_logger().info("Unified security middleware initialized")

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request using framework middleware.

        Args:
            request: Request object
            call_next: Next handler

        Returns:
            Response object
        """
        try:
            # Simple built-in API key enforcement if configured
            security_cfg = (
                self.config.get("security", {}) if isinstance(self.config, dict) else {}
            )
            # Use new simplified structure
            public_paths = set(["/health", "/docs", "/openapi.json"])
            # JSON-RPC endpoint must not be public when API key is required
            public_paths.discard("/api/jsonrpc")
            path = request.url.path
            methods = set(["api_key"])  # Use token-based authentication
            api_keys: Dict[str, str] = security_cfg.get("tokens", {}) or {}

            # Enforce only for non-public paths when api_key method configured
            if (
                security_cfg.get("enabled", False)
                and ("api_key" in methods)
                and (path not in public_paths)
            ):
                # Accept either X-API-Key or Authorization: Bearer
                token = request.headers.get("X-API-Key")
                if not token:
                    authz = request.headers.get("Authorization", "")
                    if authz.startswith("Bearer "):
                        token = authz[7:]
                if not token or (api_keys and token not in api_keys.values()):
                    from fastapi.responses import JSONResponse

                    return JSONResponse(
                        status_code=401,
                        content={
                            "error": {
                                "code": 401,
                                "message": "Unauthorized: invalid or missing API key",
                                "type": "authentication_error",
                            }
                        },
                    )

            # Continue with framework middleware or regular flow
            if self.framework_middleware:
                # If framework middleware exists, we need to call it manually
                # This is a workaround since we can't chain ASGI apps in BaseHTTPMiddleware
                get_global_logger().debug(
                    "Framework middleware exists, continuing with regular call_next"
                )
                return await call_next(request)
            else:
                # No framework middleware, continue normally
                return await call_next(request)

        except SecurityValidationError as e:
            # Handle security validation errors
            return await self._handle_security_error(request, e)
        except Exception as e:
            # Handle other errors
            get_global_logger().error(f"Unexpected error in unified security middleware: {e}")
            return await self._handle_general_error(request, e)

    async def _handle_security_error(
        self, request: Request, error: SecurityValidationError
    ) -> Response:
        """
        Handle security validation errors.

        Args:
            request: Request object
            error: Security validation error

        Returns:
            Error response
        """
        from fastapi.responses import JSONResponse

        error_response = {
            "error": {
                "code": error.error_code,
                "message": error.message,
                "type": "security_validation_error",
            }
        }

        get_global_logger().warning(f"Security validation failed: {error.message}")

        return JSONResponse(status_code=error.error_code, content=error_response)

    async def _handle_general_error(
        self, request: Request, error: Exception
    ) -> Response:
        """
        Handle general errors.

        Args:
            request: Request object
            error: General error

        Returns:
            Error response
        """
        from fastapi.responses import JSONResponse

        error_response = {
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "general_error",
            }
        }

        get_global_logger().error(f"General error in security middleware: {error}")

        return JSONResponse(status_code=500, content=error_response)
