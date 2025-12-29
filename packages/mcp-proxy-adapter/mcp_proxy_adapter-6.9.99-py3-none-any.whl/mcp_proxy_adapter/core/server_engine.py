"""
Server Engine Abstraction

This module provides an abstraction layer for the hypercorn ASGI server engine,
providing full mTLS support and SSL capabilities.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any

from .logging import get_global_logger

logger = logging.getLogger(__name__)


class ServerEngine(ABC):
    """
    Abstract base class for server engines.

    This class defines the interface that all server engines must implement,
    allowing the framework to work with different ASGI servers transparently.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the server engine."""
        pass

    @abstractmethod
    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get supported features of this server engine.

        Returns:
            Dictionary mapping feature names to boolean support status
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration for this engine.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        # Default implementation: always valid
        return True

    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get configuration schema for this engine.

        Returns:
            Dictionary describing the configuration schema
        """
        # Default implementation: empty schema
        return {}

    @abstractmethod
    def run_server(self, app: Any, config: Dict[str, Any]) -> None:
        """
        Run the server with the given application and configuration.

        Args:
            app: ASGI application
            config: Server configuration

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("run_server must be implemented by subclasses")


class HypercornEngine(ServerEngine):
    """
    Hypercorn server engine implementation.

    Provides full mTLS support and better SSL capabilities.
    """

    def get_name(self) -> str:
        """
        Get engine name.

        Returns:
            Engine name string
        """
        return "hypercorn"

    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get supported features of the engine.

        Returns:
            Dictionary mapping feature names to support status
        """
        return {
            "ssl_tls": True,
            "mtls_client_certs": True,  # Full support
            "ssl_scope_info": True,  # SSL info in request scope
            "client_cert_verification": True,
            "websockets": True,
            "http2": True,
            "reload": True,
        }

    def run_server(self, app: Any, config: Dict[str, Any]) -> None:
        """
        Run the server with the given application and configuration.

        Args:
            app: ASGI application
            config: Server configuration dictionary containing:
                - host: Server host (default: "127.0.0.1")
                - port: Server port (default: 8000)
                - certfile: SSL certificate file (optional)
                - keyfile: SSL key file (optional)
                - ca_certs: CA certificate file (optional)
                - verify_mode: SSL verification mode (optional)
                - check_hostname: Enable hostname checking (optional)
                - log_level: Logging level (optional)
                - reload: Enable auto-reload (optional)
        """
        import asyncio
        import hypercorn.asyncio
        from hypercorn.config import Config as HypercornConfig

        # Create hypercorn configuration
        hypercorn_config = HypercornConfig()
        hypercorn_config.bind = [
            f"{config.get('host', '127.0.0.1')}:{config.get('port', 8000)}"
        ]

        # Apply SSL configuration if present
        if "certfile" in config:
            hypercorn_config.certfile = config["certfile"]
        if "keyfile" in config:
            hypercorn_config.keyfile = config["keyfile"]
        if "ca_certs" in config:
            hypercorn_config.ca_certs = config["ca_certs"]
        if "verify_mode" in config:
            hypercorn_config.verify_mode = config["verify_mode"]
        if "check_hostname" in config:
            hypercorn_config.check_hostname = config["check_hostname"]

        # Apply other settings
        if "log_level" in config:
            hypercorn_config.loglevel = config["log_level"].upper()
        if "reload" in config:
            hypercorn_config.reload = config["reload"]

        # Try to set ALPN protocols for HTTP/2 support
        try:
            hypercorn_config.alpn_protocols = ["h2", "http/1.1"]
        except Exception:
            pass

        # Configure shutdown timeout if provided (helps reduce SSL shutdown timeout errors)
        if "shutdown_timeout" in config:
            try:
                hypercorn_config.shutdown_timeout = float(config["shutdown_timeout"])
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
            await hypercorn.asyncio.serve(app, hypercorn_config)

        # Run the server (blocking call)
        # Note: This uses asyncio.run internally, so it will block until server stops
        asyncio.run(_run_server_with_handler())


class ServerEngineFactory:
    """
    Factory for creating server engines.

    This class manages the creation and configuration of different server engines.
    """

    _engines: Dict[str, ServerEngine] = {}

    @classmethod
    def register_engine(cls, engine: ServerEngine) -> None:
        """
        Register a server engine.

        Args:
            engine: Server engine instance to register
        """
        cls._engines[engine.get_name()] = engine
        get_global_logger().info(f"Registered server engine: {engine.get_name()}")

    @classmethod
    def get_engine(cls, engine_name: str) -> Optional[ServerEngine]:
        """
        Get a registered server engine by name.

        Args:
            engine_name: Name of the engine to retrieve

        Returns:
            ServerEngine instance if found, None otherwise
        """
        return cls._engines.get(engine_name)

    @classmethod
    def get_available_engines(cls) -> Dict[str, ServerEngine]:
        """
        Get all registered server engines.

        Returns:
            Dictionary mapping engine names to ServerEngine instances
        """
        return cls._engines.copy()

    @classmethod
    def initialize_default_engines(cls) -> None:
        """Initialize default server engines."""
        # Register hypercorn engine (only supported engine)
        try:
            import hypercorn  # noqa: F401

            cls.register_engine(HypercornEngine())
            get_global_logger().info(
                "Hypercorn engine registered (full mTLS support available)"
            )
        except ImportError:
            get_global_logger().error(
                "Hypercorn not available - this is required for the framework"
            )
            raise


# Initialize default engines
ServerEngineFactory.initialize_default_engines()
