"""
Server Configuration Adapter

This module provides adapters for converting configuration between different
server engines and handling SSL configuration mapping.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import logging
from typing import Dict, Any, Optional

from .server_engine import ServerEngineFactory, ServerEngine
from .logging import get_global_logger

logger = logging.getLogger(__name__)


class ServerConfigAdapter:
    """
    Adapter for converting server configurations between different engines.

    This class handles the mapping of configuration parameters between
    different server engines and provides unified configuration management.
    """

    @staticmethod
    def convert_ssl_config_for_engine(
        ssl_config: Dict[str, Any], target_engine: str
    ) -> Dict[str, Any]:
        """
        Convert SSL configuration for a specific server engine.

        Args:
            ssl_config: Source SSL configuration
            target_engine: Target engine name (hypercorn)

        Returns:
            Converted SSL configuration for the target engine
        """
        engine = ServerEngineFactory.get_engine(target_engine)
        if not engine:
            get_global_logger().error(f"Unknown server engine: {target_engine}")
            return {}

        if target_engine == "hypercorn":
            return ServerConfigAdapter._convert_to_hypercorn_ssl(ssl_config)
        else:
            get_global_logger().warning(f"No SSL conversion available for engine: {target_engine}")
            return {}

    @staticmethod
    def _convert_to_hypercorn_ssl(ssl_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert SSL configuration to hypercorn format."""
        hypercorn_ssl = {}

        # Map SSL parameters - support both new (cert, key, ca) and old (cert_file, key_file, ca_cert) formats
        cert_file = ssl_config.get("cert") or ssl_config.get("cert_file")
        key_file = ssl_config.get("key") or ssl_config.get("key_file")
        ca_cert = ssl_config.get("ca") or ssl_config.get("ca_cert")
        
        if cert_file:
            hypercorn_ssl["certfile"] = cert_file
        if key_file:
            hypercorn_ssl["keyfile"] = key_file
        if ca_cert:
            hypercorn_ssl["ca_certs"] = ca_cert

        # Map verification mode
        # Map hostname checking - support both new (dnscheck) and old (chk_hostname) formats
        dnscheck = ssl_config.get("dnscheck")
        if dnscheck is not None:
            hypercorn_ssl["check_hostname"] = dnscheck
        elif "chk_hostname" in ssl_config:
            hypercorn_ssl["check_hostname"] = ssl_config["chk_hostname"]

        get_global_logger().debug(f"Converted SSL config to hypercorn: {hypercorn_ssl}")
        return hypercorn_ssl

    @staticmethod
    def validate_engine_compatibility(config: Dict[str, Any], engine_name: str) -> bool:
        """
        Validate if a configuration is compatible with a specific engine.

        Args:
            config: Server configuration
            engine_name: Name of the server engine

        Returns:
            True if compatible, False otherwise
        """
        engine = ServerEngineFactory.get_engine(engine_name)
        if not engine:
            get_global_logger().error(f"Unknown engine: {engine_name}")
            return False

        # Check SSL requirements
        ssl_config = config.get("ssl", {})
        if not ssl_config:
            # Try to get SSL config from security section
            ssl_config = config.get("security", {}).get("ssl", {})

        if ssl_config.get("verify_client", False):
            if not engine.get_supported_features().get("mtls_client_certs", False):
                get_global_logger().error(
                    f"Engine {engine_name} doesn't support mTLS client certificates"
                )
                return False

        # Validate engine-specific configuration
        return engine.validate_config(config)

    @staticmethod
    def get_engine_capabilities(engine_name: str) -> Dict[str, Any]:
        """
        Get capabilities of a specific server engine.

        Args:
            engine_name: Name of the server engine

        Returns:
            Dictionary of engine capabilities
        """
        engine = ServerEngineFactory.get_engine(engine_name)
        if not engine:
            return {}

        return {
            "name": engine.get_name(),
            "features": engine.get_supported_features(),
            "config_schema": engine.get_config_schema(),
        }


class UnifiedServerRunner:
    """
    Unified server runner that uses hypercorn as the default engine.

    This class provides a unified interface for running servers using hypercorn
    as the underlying engine.
    """

    def __init__(self, default_engine: str = "hypercorn"):
        """
        Initialize the unified server runner.

        Args:
            default_engine: Default engine to use (currently only hypercorn is supported)
        """
        self.default_engine = default_engine
        self.available_engines = ServerEngineFactory.get_available_engines()

        get_global_logger().info(f"Available engines: {list(self.available_engines.keys())}")
        get_global_logger().info(f"Default engine: {default_engine}")

    def run_server(
        self, app: Any, config: Dict[str, Any], engine_name: Optional[str] = None
    ) -> None:
        """
        Run server with hypercorn engine.

        Args:
            app: ASGI application
            config: Server configuration
            engine_name: Engine to use (currently only hypercorn is supported)
        """
        # Use hypercorn as the only supported engine
        selected_engine = "hypercorn"
        get_global_logger().info(f"Using hypercorn engine")

        # Validate compatibility
        if not ServerConfigAdapter.validate_engine_compatibility(
            config, selected_engine
        ):
            raise ValueError(
                f"Configuration not compatible with engine: {selected_engine}"
            )

        # Get engine instance
        engine = ServerEngineFactory.get_engine(selected_engine)
        if not engine:
            raise ValueError(f"Engine not available: {selected_engine}")

        # Convert configuration if needed
        converted_config = self._prepare_config_for_engine(config, selected_engine)

        # Run server
        get_global_logger().info(f"Starting server with {selected_engine} engine")
        engine.run_server(app, converted_config)

    def _prepare_config_for_engine(
        self, config: Dict[str, Any], engine_name: str
    ) -> Dict[str, Any]:
        """
        Prepare configuration for specific server engine.
        
        Args:
            config: Original configuration dictionary
            engine_name: Name of the server engine
            
        Returns:
            Converted configuration dictionary for the engine
        """
        get_global_logger().info(
            f"🔍 Debug: _prepare_config_for_engine called with config keys: {list(config.keys())}"
        )
        get_global_logger().info(f"🔍 Debug: SSL config in input: {config.get('ssl', 'NOT_FOUND')}")
        # Start with basic config
        engine_config = {
            "host": config.get("host", "127.0.0.1"),
            "port": config.get("port", 8000),
            "log_level": config.get("log_level", "info"),
            "reload": config.get("reload", False),
        }

        # Add SSL configuration if present
        # First check for direct SSL parameters (from app_factory.py)
        if (
            "certfile" in config
            or "keyfile" in config
            or "ca_certs" in config
            or "verify_mode" in config
        ):
            get_global_logger().info(f"🔍 DEBUG: Direct SSL parameters found in config")
            if "certfile" in config:
                engine_config["certfile"] = config["certfile"]
            if "keyfile" in config:
                engine_config["keyfile"] = config["keyfile"]
            if "ca_certs" in config:
                engine_config["ca_certs"] = config["ca_certs"]
            if "verify_mode" in config:
                engine_config["verify_mode"] = config["verify_mode"]
        else:
            # Try to get SSL config from ssl section
            ssl_config = config.get("ssl", {})
            if not ssl_config:
                # Try to get SSL config from security section
                ssl_config = config.get("security", {}).get("ssl", {})

            if ssl_config:
                converted_ssl = ServerConfigAdapter.convert_ssl_config_for_engine(
                    ssl_config, engine_name
                )
                engine_config.update(converted_ssl)

        # Add engine-specific configuration
        if "workers" in config:
            engine_config["workers"] = config["workers"]

        return engine_config


