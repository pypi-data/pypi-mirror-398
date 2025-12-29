#!/usr/bin/env python3
"""
mTLS Server implementation using built-in http.server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import threading
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any
import os

from .ssl_utils import SSLUtils

logger = logging.getLogger(__name__)


class mTLSHandler(BaseHTTPRequestHandler):
    """Handler for mTLS connections."""

    def __init__(self, *args, main_app=None, **kwargs):
        """
        Initialize mTLS handler.
        
        Args:
            *args: Positional arguments for BaseHTTPRequestHandler
            main_app: Main FastAPI application instance
            **kwargs: Keyword arguments for BaseHTTPRequestHandler
        """
        self.main_app = main_app
        super().__init__(*args, **kwargs)




    def _forward_to_main_app(
        self,
        method: str,
        path: str,
        client_cert: Optional[Dict],
        post_data: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Forward request to main FastAPI application."""
        try:
            # This is a simplified forwarding - in real implementation
            # you would use httpx or similar to make internal HTTP calls
            # to the main FastAPI app running on different port

            return {
                "status": "ok",
                "message": f"mTLS {method} forwarded to main app",
                "client_cert": client_cert,
                "path": path,
                "forwarded": True,
            }
        except Exception as e:
            get_global_logger().error(f"Error forwarding to main app: {e}")
            return {
                "status": "error",
                "message": f"Forwarding failed: {e}",
                "client_cert": client_cert,
                "path": path,
            }


class mTLSServer:
    """mTLS Server using built-in http.server."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8443,
        cert_file: str = None,
        key_file: str = None,
        ca_cert_file: str = None,
        main_app=None,
    ):
        """
        Initialize mTLS server.

        Args:
            host: Server host
            port: Server port
            cert_file: Server certificate file
            key_file: Server private key file
            ca_cert_file: CA certificate file for client verification
            main_app: Main FastAPI application for forwarding requests
        """
        self.host = host
        self.port = port
        self.cert_file = cert_file
        self.key_file = key_file
        self.ca_cert_file = ca_cert_file
        self.main_app = main_app

        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.running = False

        get_global_logger().info(f"mTLS Server initialized: {host}:{port}")

    def _create_handler(self):
        """Create handler with main app reference."""


        return handler

    def start(self) -> bool:
        """Start mTLS server in separate thread."""
        try:
            # Check if certificate files exist
            if not os.path.exists(self.cert_file):
                get_global_logger().error(f"Certificate file not found: {self.cert_file}")
                return False

            if not os.path.exists(self.key_file):
                get_global_logger().error(f"Key file not found: {self.key_file}")
                return False

            if not os.path.exists(self.ca_cert_file):
                get_global_logger().error(
                    f"CA certificate file not found: {self.ca_cert_file}"
                )
                return False

            # Create server
            handler_class = self._create_handler()
            self.server = HTTPServer((self.host, self.port), handler_class)

            # Configure SSL context
            context = SSLUtils.create_ssl_context(
                cert_file=self.cert_file,
                key_file=self.key_file,
                ca_cert=self.ca_cert_file,
                verify_client=True,
                min_tls_version="TLSv1.2",
            )

            # Wrap socket with SSL
            self.server.socket = context.wrap_socket(
                self.server.socket, server_side=True
            )

            # Start server in separate thread
            self.server_thread = threading.Thread(
                target=self._run_server, daemon=True
            )
            self.server_thread.start()

            self.running = True
            get_global_logger().info(
                f"✅ mTLS Server started on https://{self.host}:{self.port}"
            )
            return True

        except Exception as e:
            get_global_logger().error(f"Failed to start mTLS server: {e}")
            return False





