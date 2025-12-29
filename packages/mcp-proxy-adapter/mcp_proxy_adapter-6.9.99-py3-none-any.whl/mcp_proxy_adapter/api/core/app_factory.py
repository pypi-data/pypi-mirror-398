"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Application factory for MCP Proxy Adapter API.
"""

from typing import Optional, Dict, Any

from fastapi import FastAPI

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.custom_openapi import custom_openapi_with_fallback

from .lifespan_manager import LifespanManager
from .app_factory_config import debug_config_info, resolve_current_config
from .app_factory_validators import (
    validate_configuration,
    validate_security_configuration,
)
from .app_factory_certificates import validate_certificates
from .app_factory_routes import setup_routes
from mcp_proxy_adapter.commands.builtin_commands import register_builtin_commands
from mcp_proxy_adapter.commands.help_command import set_app_metadata


class AppFactory:
    """Factory for creating FastAPI applications."""

    def __init__(self) -> None:
        """Initialize app factory."""
        self.logger = get_global_logger()
        self.lifespan_manager = LifespanManager()
        self._config_path: Optional[str] = None

    def create_app(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[str] = None,
        app_config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
    ) -> FastAPI:
        """Create and configure FastAPI application."""
        self._config_path = config_path
        current_config = resolve_current_config(app_config)
        debug_config_info(app_config)

        validate_configuration(current_config, self.logger)
        validate_security_configuration(current_config, self.logger)
        validate_certificates(current_config, self._config_path, self.logger)

        title = title or "MCP Proxy Adapter"
        description = description or "JSON-RPC API for interacting with MCP Proxy"
        version = version or "1.0.0"

        self.logger.info(
            "🔍 AppFactory: Creating lifespan with current_config keys: %s",
            list(current_config.keys()) if hasattr(current_config, "keys") else "None",
        )
        lifespan = self.lifespan_manager.create_lifespan(config_path, current_config)
        self.logger.info(
            "🔍 AppFactory: lifespan created, callable=%s", callable(lifespan)
        )

        app = FastAPI(
            title=title,
            description=description,
            version=version,
            lifespan=lifespan,
        )
        self.logger.info("🔍 AppFactory: FastAPI app created")

        # Register built-in commands automatically
        # Pass current_config to enable automatic queue commands registration
        register_builtin_commands(config_data=current_config)
        self.logger.info("✅ Built-in commands registered")

        # Store app metadata for help command
        set_app_metadata(title, description, version)
        self.logger.info(f"✅ App metadata stored: {title} v{version}")

        setup_routes(app)
        app.openapi = lambda: custom_openapi_with_fallback(app)
        return app
