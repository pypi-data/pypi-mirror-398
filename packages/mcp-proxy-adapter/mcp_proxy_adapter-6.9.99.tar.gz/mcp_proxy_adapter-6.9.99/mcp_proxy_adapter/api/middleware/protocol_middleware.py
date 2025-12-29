"""
Protocol middleware module.

This module provides middleware for validating protocol access based on configuration.
"""

from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from mcp_proxy_adapter.core.protocol_manager import ProtocolManager
from mcp_proxy_adapter.core.logging import get_global_logger


class ProtocolMiddleware(BaseHTTPMiddleware):
    """
    Middleware for protocol validation.

    This middleware checks if the incoming request protocol is allowed
    based on the protocol configuration.
    """

    def __init__(self, app, app_config: Optional[Dict[str, Any]] = None):
        """
        Initialize protocol middleware.

        Args:
            app: FastAPI application
            app_config: Application configuration dictionary (optional)
        """
        super().__init__(app)
        # Normalize config to dictionary
        normalized_config: Optional[Dict[str, Any]]
        if app_config is None:
            normalized_config = None
        elif hasattr(app_config, "get_all"):
            try:
                normalized_config = app_config.get_all()
            except Exception as e:
                get_global_logger().debug(
                    f"ProtocolMiddleware - Error calling get_all(): {e}, type: {type(app_config)}"
                )
                normalized_config = None
        elif hasattr(app_config, "keys"):
            normalized_config = app_config  # Already dict-like
        else:
            get_global_logger().debug(
                f"ProtocolMiddleware - app_config is not dict-like, type: {type(app_config)}, value: {repr(app_config)}"
            )
            normalized_config = None

        get_global_logger().debug(
            f"ProtocolMiddleware - normalized_config type: {type(normalized_config)}"
        )
        if normalized_config:
            get_global_logger().debug(
                f"ProtocolMiddleware - protocols in config: {'protocols' in normalized_config}"
            )
            if "protocols" in normalized_config:
                get_global_logger().debug(
                    f"ProtocolMiddleware - protocols type: {type(normalized_config['protocols'])}"
                )

        self.app_config = normalized_config
        # Get protocol manager with current configuration
        self.protocol_manager = ProtocolManager(normalized_config)



    def _get_request_protocol(self, request: Request) -> str:
        """
        Extract protocol from request.

        Args:
            request: FastAPI request object

        Returns:
            Protocol name (http, https, mtls)
        """
        try:
            # Check if request is secure (HTTPS)
            if request.url.scheme:
                scheme = request.url.scheme.lower()

                # If HTTPS, check if client certificate is provided (MTLS)
                if scheme == "https":
                    # Check for client certificate in ASGI scope
                    try:
                        # Method 1: Check transport info in ASGI scope
                        if hasattr(request, "scope") and request.scope:
                            transport = request.scope.get("transport")
                            if transport and hasattr(transport, "get_extra_info"):
                                try:
                                    ssl_object = transport.get_extra_info("ssl_object")
                                    if ssl_object:
                                        try:
                                            cert = ssl_object.getpeercert()
                                            if cert:
                                                get_global_logger().debug(f"mTLS client certificate detected: {cert.get('subject', 'unknown')}")
                                                return "mtls"
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    # Check for client certificate in headers (proxy forwarded)
                    try:
                        mtls_headers = [
                            request.headers.get("ssl-client-cert"),
                            request.headers.get("x-client-cert"),
                            request.headers.get("x-ssl-cert"),
                            request.headers.get("x-forwarded-client-cert")
                        ]
                        if any(mtls_headers):
                            get_global_logger().debug("mTLS client certificate detected in headers")
                            return "mtls"
                    except Exception:
                        pass

                    return "https"

                return scheme

            # Fallback to checking headers
            x_forwarded_proto = request.headers.get("x-forwarded-proto")
            if x_forwarded_proto:
                return x_forwarded_proto.lower()

            # Default to HTTP
            return "http"
            
        except Exception as e:
            get_global_logger().error(f"Error extracting protocol from request: {e}", exc_info=True)
            # Fallback to HTTP if there's any error
            return "http"


