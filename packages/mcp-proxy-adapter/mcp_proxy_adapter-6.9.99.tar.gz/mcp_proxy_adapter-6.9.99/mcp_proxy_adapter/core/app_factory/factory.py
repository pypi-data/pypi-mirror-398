"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Main factory function for creating and running MCP Proxy Adapter server.
"""

import sys
from pathlib import Path
from typing import Optional

from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.core.logging import setup_logging

from .config_loader import load_and_validate_config
from .ssl_config import build_server_ssl_config, is_mtls_enabled
from .server_runner import run_server


async def create_and_run_server(
    config_path: Optional[str] = None,
    log_config_path: Optional[str] = None,
    title: str = "MCP Proxy Adapter Server",
    description: str = "Model Context Protocol Proxy Adapter with Security Framework",
    version: str = "1.0.0",
    host: str = "0.0.0.0",
    log_level: str = "info",
    engine: Optional[str] = None,
) -> None:
    """
    Create and run MCP Proxy Adapter server with proper validation.

    This factory function validates all configuration files, sets up logging,
    initializes the application, and starts the server with optimal settings.

    Args:
        config_path: Path to configuration file (JSON)
        log_config_path: Path to logging configuration file (optional)
        title: Application title for OpenAPI schema
        description: Application description for OpenAPI schema
        version: Application version
        host: Server host address
        log_level: Logging level
        engine: Specific server engine to use (optional)

    Raises:
        SystemExit: If configuration validation fails or server cannot start
    """
    print("🚀 MCP Proxy Adapter Server Factory")
    print("=" * 60)
    print(f"📋 Title: {title}")
    print(f"📝 Description: {description}")
    print(f"🔢 Version: {version}")
    print(f"🌐 Host: {host}")
    print(f"📊 Log Level: {log_level}")
    print("=" * 60)
    print()

    # 1. Validate and load configuration file
    app_config = load_and_validate_config(config_path)

    # 2. Setup logging
    try:
        if log_config_path:
            log_config_file = Path(log_config_path)
            if not log_config_file.exists():
                print(f"❌ Log configuration file not found: {log_config_path}")
                sys.exit(1)
            print(
                "⚠️ Custom log configuration files are not supported yet. "
                "Using default logging configuration."
            )
        setup_logging()
        print("✅ Logging configured with defaults")
    except Exception as e:
        print(f"❌ Failed to setup logging: {e}")
        sys.exit(1)

    # 3. Register built-in commands (disabled)
    print("⚠️  Built-in command registration disabled for simplified startup")

    # 4. Create FastAPI application with configuration
    try:
        app = create_app(
            title=title,
            description=description,
            version=version,
            app_config=app_config,
            config_path=config_path,
        )
        print("✅ FastAPI application created successfully")
    except Exception as e:
        print(f"❌ Failed to create FastAPI application: {e}")
        sys.exit(1)

    # 5. Create server configuration
    server_port = app_config.get("server", {}).get("port", 8000) if app_config else 8000
    print(f"🔌 Port: {server_port}")

    server_config = {
        "host": host,
        "port": server_port,
        "log_level": log_level,
        "reload": False,
    }

    # Add SSL configuration if present
    try:
        ssl_config = build_server_ssl_config(app_config)
        server_config.update(ssl_config)
    except ValueError as exc:
        print(f"❌ SSL configuration invalid: {exc}")
        sys.exit(1)

    # 6. Inform about mTLS mode (handled by hypercorn SSL context)
    if is_mtls_enabled(app_config):
        print(
            "🔐 mTLS enabled - Hypercorn will enforce mutual TLS on the external port"
        )
    else:
        print("🔓 mTLS disabled - using regular HTTPS/HTTP based on protocol")

    # 7. Start main server
    await run_server(app, server_config, mtls_server=None)
