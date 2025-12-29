"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Application Runner for MCP Proxy Adapter

This module provides the ApplicationRunner class for running applications
with full configuration validation and error handling.
"""

import socket
import sys
from pathlib import Path
from typing import Any, Dict, List, cast

from fastapi import FastAPI
from hypercorn.typing import ASGIFramework

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.signal_handler import (
    setup_signal_handling,
    is_shutdown_requested,
)

logger = get_global_logger().getChild("app_runner")


class ApplicationRunner:
    """
    Class for running applications with configuration validation.
    """

    def __init__(self, app: FastAPI, config: Dict[str, Any]):
        """
        Initialize ApplicationRunner.

        Args:
            app: FastAPI application instance
            config: Application configuration dictionary
        """
        self.app = app
        self.config = config
        self.errors: List[str] = []

    def validate_configuration(self) -> List[str]:
        """
        Validates configuration and returns list of errors.

        Returns:
            List of validation error messages
        """
        self.errors = []

        # Validate server configuration
        self._validate_server_config()

        # Validate SSL configuration
        self._validate_ssl_config()

        # Validate security configuration
        self._validate_security_config()

        # Validate file paths
        self._validate_file_paths()

        # Validate port availability
        self._validate_port_availability()

        # Validate configuration compatibility
        self._validate_compatibility()

        return self.errors

    def _validate_server_config(self) -> None:
        """Validate server configuration."""
        server_config = self.config.get("server", {})

        if not server_config:
            self.errors.append("Server configuration is missing")
            return

        host = server_config.get("host")
        port = server_config.get("port")

        if not host:
            self.errors.append("Server host is not specified")

        if not port:
            self.errors.append("Server port is not specified")
        elif not isinstance(port, int) or port < 1 or port > 65535:
            self.errors.append(f"Invalid server port: {port}")

    def _validate_ssl_config(self) -> None:
        """Validate SSL configuration based on protocol."""
        server_config = self.config.get("server", {})
        protocol = server_config.get("protocol", "http")

        # SSL is automatically enabled for https and mtls protocols
        if protocol in ("https", "mtls"):
            ssl_config = self.config.get("ssl", {})
            cert_file = ssl_config.get("cert_file")
            key_file = ssl_config.get("key_file")

            # Only validate if certificates are specified
            if cert_file and key_file:
                if not Path(cert_file).exists():
                    self.errors.append(f"Certificate file not found: {cert_file}")

                if not Path(key_file).exists():
                    self.errors.append(f"Private key file not found: {key_file}")

            # Validate mTLS configuration
            if protocol == "mtls" or ssl_config.get("verify_client", False):
                ca_cert = ssl_config.get("ca_cert")
                if not ca_cert:
                    self.errors.append(
                        f"{protocol.upper()} requires CA certificate to be specified"
                    )
                elif not Path(ca_cert).exists():
                    self.errors.append(f"CA certificate file not found: {ca_cert}")

    def _validate_security_config(self) -> None:
        """Validate security configuration."""
        security_config = self.config.get("security", {})

        if security_config.get("enabled", False):
            auth_config = security_config.get("auth", {})
            permissions_config = security_config.get("permissions", {})

            # Validate authentication configuration
            if auth_config.get("enabled", False):
                methods = auth_config.get("methods", [])
                if not methods:
                    self.errors.append(
                        "Authentication enabled but no methods specified"
                    )

                # Validate API key configuration
                if "api_key" in methods:
                    # Check if roles file exists for API key auth
                    if permissions_config.get("enabled", False):
                        roles_file = permissions_config.get("roles_file")
                        if not roles_file:
                            self.errors.append(
                                "Permissions enabled but roles file not specified"
                            )
                        elif not Path(roles_file).exists():
                            self.errors.append(f"Roles file not found: {roles_file}")

                # Validate certificate configuration
                if "certificate" in methods:
                    server_config = self.config.get("server", {})
                    protocol = server_config.get("protocol", "http")
                    if protocol not in ("https", "mtls"):
                        self.errors.append(
                            "Certificate authentication requires https or mtls protocol"
                        )
                    ssl_config = self.config.get("ssl", {})
                    if not ssl_config.get("verify_client", False):
                        self.errors.append(
                            "Certificate authentication requires client verification to be enabled"
                        )

    def _validate_file_paths(self) -> None:
        """Validate all file paths in configuration."""
        # Check SSL certificate files based on protocol
        server_config = self.config.get("server", {})
        protocol = server_config.get("protocol", "http")

        if protocol in ("https", "mtls"):
            ssl_config = self.config.get("ssl", {})
            cert_file = ssl_config.get("cert_file")
            key_file = ssl_config.get("key_file")
            ca_cert = ssl_config.get("ca_cert")

            # Only validate if certificates are specified
            if cert_file and not Path(cert_file).is_file():
                self.errors.append(
                    f"Certificate file is not a regular file: {cert_file}"
                )

            if key_file and not Path(key_file).is_file():
                self.errors.append(
                    f"Private key file is not a regular file: {key_file}"
                )

            if ca_cert and not Path(ca_cert).is_file():
                self.errors.append(
                    f"CA certificate file is not a regular file: {ca_cert}"
                )

        # Check roles file
        security_config = self.config.get("security", {})
        permissions_config = security_config.get("permissions", {})
        if permissions_config.get("enabled", False):
            roles_file = permissions_config.get("roles_file")
            if roles_file and not Path(roles_file).is_file():
                self.errors.append(f"Roles file is not a regular file: {roles_file}")

    def _validate_port_availability(self) -> None:
        """Validate that the configured port is available."""
        server_config = self.config.get("server", {})
        port = server_config.get("port")

        if port:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
            except OSError:
                self.errors.append(f"Port {port} is already in use")

    def _validate_compatibility(self) -> None:
        """Validate configuration compatibility."""
        server_config = self.config.get("server", {})
        protocol = server_config.get("protocol", "http")
        security_config = self.config.get("security", {})
        protocols_config = self.config.get("protocols", {})

        # Check protocol compatibility
        if protocol in ("https", "mtls"):
            allowed_protocols = protocols_config.get("allowed_protocols", [])
            if allowed_protocols and protocol not in allowed_protocols:
                self.errors.append(
                    f"Protocol {protocol} is not in allowed protocols: {allowed_protocols}"
                )

        # Check security and protocol compatibility
        if security_config.get("enabled", False):
            auth_config = security_config.get("auth", {})
            if auth_config.get("enabled", False):
                methods = auth_config.get("methods", [])
                if "certificate" in methods and protocol not in ("https", "mtls"):
                    self.errors.append(
                        "Certificate authentication requires https or mtls protocol"
                    )

    def setup_hooks(self) -> None:
        """
        Setup application hooks.
        """

        # Add startup event
        @self.app.on_event("startup")
        def startup() -> None:
            """Initialize resources when application starts."""
            pass

        # Add shutdown event
        @self.app.on_event("shutdown")
        def shutdown() -> None:
            """Release resources when application stops."""
            pass

    def run(self) -> None:
        """
        Run application with full validation.
        """
        # Validate configuration
        errors = self.validate_configuration()

        if errors:
            print("ERROR: Configuration validation failed:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            sys.exit(1)

        # Setup signal handling for graceful shutdown
        def shutdown_callback() -> None:
            """Callback for graceful shutdown."""
            logger.info("Graceful shutdown requested")

        setup_signal_handling(shutdown_callback)
        print("🔧 Signal handling configured for graceful shutdown")

        # Setup hooks
        self.setup_hooks()

        # Get server configuration
        server_config = self.config.get("server", {})
        host = server_config.get("host", "127.0.0.1")
        port = server_config.get("port", 8000)

        # Prepare server configuration for hypercorn
        server_kwargs = {"host": host, "port": port, "log_level": "info"}

        # Add SSL configuration based on protocol
        protocol = server_config.get("protocol", "http")
        if protocol in ("https", "mtls"):
            ssl_config = self.config.get("ssl", {})
            cert_file = ssl_config.get("cert_file")
            key_file = ssl_config.get("key_file")

            # Only add SSL config if certificates are specified
            if cert_file and key_file:
                server_kwargs["certfile"] = cert_file
                server_kwargs["keyfile"] = key_file

            # Add mTLS configuration
            if protocol == "mtls" or ssl_config.get("verify_client", False):
                ca_cert = ssl_config.get("ca_cert")
                if ca_cert:
                    server_kwargs["ca_certs"] = ca_cert

        try:
            import hypercorn.asyncio
            import asyncio
            from hypercorn.config import Config as HypercornConfig

            print(f"🚀 Starting server on {host}:{port}")
            print("🛑 Use Ctrl+C or send SIGTERM for graceful shutdown")
            print("=" * 60)

            # Convert server_kwargs to HypercornConfig for better control
            hypercorn_config = HypercornConfig()
            hypercorn_config.bind = [f"{host}:{port}"]
            hypercorn_config.loglevel = server_kwargs.get("log_level", "info").upper()
            
            # Copy SSL configuration if present
            if "certfile" in server_kwargs:
                hypercorn_config.certfile = server_kwargs["certfile"]
            if "keyfile" in server_kwargs:
                hypercorn_config.keyfile = server_kwargs["keyfile"]
            if "ca_certs" in server_kwargs:
                hypercorn_config.ca_certs = server_kwargs["ca_certs"]

            # Configure shutdown timeout if provided (helps reduce SSL shutdown timeout errors)
            server_config = self.config.get("server", {})
            if "shutdown_timeout" in server_config:
                try:
                    hypercorn_config.shutdown_timeout = float(server_config["shutdown_timeout"])
                    logger.debug(f"SSL shutdown timeout set to {hypercorn_config.shutdown_timeout}s")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid shutdown_timeout value: {e}")

            # Setup event loop exception handler to suppress SSL shutdown timeout noise
            async def _run_server_with_handler() -> None:
                """Run server with exception handler configured."""
                # Setup exception handler inside async function to use get_running_loop()
                loop = asyncio.get_running_loop()
                original_handler = loop.get_exception_handler()

                def exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any]) -> None:
                    """
                    Custom exception handler that suppresses SSL shutdown timeout noise.
                    
                    This handler catches TimeoutError("SSL shutdown timed out") exceptions
                    that occur during connection close/heartbeat cycles and logs them at
                    DEBUG level instead of ERROR to reduce log pollution.
                    """
                    exception = context.get("exception")
                    message = context.get("message", "")

                    # Check if this is the SSL shutdown timeout error
                    # This is a benign error that occurs when clients disconnect during SSL shutdown
                    if (
                        isinstance(exception, TimeoutError)
                        and "SSL shutdown timed out" in str(exception)
                    ) or "SSL shutdown timed out" in message:
                        # Log only at DEBUG level to avoid log pollution
                        logger.debug(
                            "SSL shutdown timeout during connection close (benign, suppressing noise): %s",
                            message,
                            exc_info=exception,
                        )
                        return

                    # For all other exceptions, use original handler or default logging
                    if original_handler:
                        original_handler(loop, context)
                    else:
                        # Default behavior: log error
                        logger.error(
                            "Unhandled exception in event loop: %s",
                            message,
                            exc_info=exception,
                        )

                loop.set_exception_handler(exception_handler)
                asgi_app = cast(ASGIFramework, self.app)
                await hypercorn.asyncio.serve(asgi_app, hypercorn_config)

            # Run with hypercorn
            asyncio.run(_run_server_with_handler())

        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user (Ctrl+C)")
            if is_shutdown_requested():
                print("✅ Graceful shutdown completed")
        except Exception as e:
            print(f"\n❌ Failed to start server: {e}", file=sys.stderr)
            sys.exit(1)
