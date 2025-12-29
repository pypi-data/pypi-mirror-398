"""
Module for FastAPI application setup.
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI

from .core import AppFactory, SSLContextFactory, RegistrationManager, LifespanManager




def create_lifespan(config_path: Optional[str] = None, current_config: Optional[Dict[str, Any]] = None):
    """
    Create lifespan manager for the FastAPI application.

    Args:
        config_path: Path to configuration file (optional)
        current_config: Current configuration data (optional)

    Returns:
        Lifespan context manager
    """
    lifespan_manager = LifespanManager()
    return lifespan_manager.create_lifespan(config_path, current_config)


def create_ssl_context(
    app_config: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
    Create SSL context based on configuration.

    Args:
        app_config: Application configuration dictionary (optional)

    Returns:
        SSL context if SSL is enabled and properly configured, None otherwise
    """
    ssl_factory = SSLContextFactory()
    return ssl_factory.create_ssl_context(app_config)


def create_app(
    title: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    app_config: Optional[Dict[str, Any]] = None,
    config_path: Optional[str] = None,
) -> FastAPI:
    """
    Creates and configures FastAPI application.

    Args:
        title: Application title (default: "MCP Proxy Adapter")
        description: Application description (default: "JSON-RPC API for interacting with MCP Proxy")
        version: Application version (default: "1.0.0")
        app_config: Application configuration dictionary (optional)
        config_path: Path to configuration file (optional)

    Returns:
        Configured FastAPI application.
    """
    app_factory = AppFactory()
    return app_factory.create_app(title, description, version, app_config, config_path)
