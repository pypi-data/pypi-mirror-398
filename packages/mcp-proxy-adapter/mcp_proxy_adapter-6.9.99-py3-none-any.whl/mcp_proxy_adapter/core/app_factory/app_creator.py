"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Application creation functions for app factory.
"""

from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.core.logging import setup_logging
from mcp_proxy_adapter.commands.builtin_commands import register_builtin_commands


def create_application(
    config: Dict[str, Any],
    title: str = "MCP Proxy Adapter",
    description: str = "JSON-RPC API for interacting with MCP Proxy",
    version: str = "1.0.0",
) -> FastAPI:
    """
    Creates and configures FastAPI application.

    Args:
        config: Application configuration dictionary
        title: Application title
        description: Application description
        version: Application version

    Returns:
        Configured FastAPI application
    """
    # Setup logging
    setup_logging()

    # Register built-in commands
    # Pass config to enable automatic queue commands registration
    register_builtin_commands(config_data=config)

    # Create FastAPI application using existing create_app function
    app = create_app(
        title=title,
        description=description,
        version=version,
        app_config=config,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add health endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": version}

    return app

