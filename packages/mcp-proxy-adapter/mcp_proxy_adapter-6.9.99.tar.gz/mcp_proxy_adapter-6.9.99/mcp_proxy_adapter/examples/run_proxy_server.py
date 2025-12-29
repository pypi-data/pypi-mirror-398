#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Proxy server built on MCP Proxy Adapter framework.
This server provides proxy registration endpoints via JSON-RPC commands.
"""

import argparse
import asyncio
import json
import signal
import sys
from pathlib import Path

from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.core.server_engine import ServerEngineFactory
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.core.config.simple_config import SimpleConfig
from mcp_proxy_adapter.config import get_config
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

# Register proxy commands
from mcp_proxy_adapter.examples.full_application.proxy_commands import (
    ProxyRegisterCommand,
    ProxyUnregisterCommand,
    ProxyHeartbeatCommand,
    ProxyListCommand,
)


def register_proxy_commands():
    """
    Register proxy-specific commands in the command registry.
    
    Registers the following commands:
    - proxy_register: Register a server with the proxy
    - proxy_unregister: Unregister a server from the proxy
    - proxy_heartbeat: Send heartbeat to the proxy
    - proxy_list: List all registered servers
    """
    registry.register(ProxyRegisterCommand, "builtin")
    registry.register(ProxyUnregisterCommand, "builtin")
    registry.register(ProxyHeartbeatCommand, "builtin")
    registry.register(ProxyListCommand, "builtin")
    print("✅ Proxy commands registered")


def main() -> None:
    """
    Main entry point for proxy server.
    
    This function:
    1. Parses command line arguments
    2. Loads and validates configuration
    3. Registers proxy-specific commands
    4. Creates FastAPI application
    5. Adds compatibility REST endpoints
    6. Starts the server using the adapter framework
    """
    parser = argparse.ArgumentParser(
        description="Run proxy server built on MCP Proxy Adapter"
    )
    parser.add_argument(
        "--config",
        default="mcp_proxy_adapter/examples/full_application/configs/proxy_server.json",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=3004, help="Port to bind to (default: 3004)"
    )

    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)

    try:
        with config_path.open("r", encoding="utf-8") as f:
            app_config = json.load(f)
    except Exception as exc:
        print(f"❌ Failed to load configuration: {exc}")
        sys.exit(1)

    # Override host and port from command line
    if args.host:
        app_config.setdefault("server", {}).update({"host": args.host})
    if args.port:
        app_config.setdefault("server", {}).update({"port": args.port})

    # Load SimpleConfig model (for adapter internals)
    simple_config = SimpleConfig(str(config_path))
    model = simple_config.load()

    # Apply CLI overrides to SimpleConfig model
    if args.host:
        model.server.host = args.host
    if args.port:
        model.server.port = args.port

    # Merge SimpleConfig sections back into raw config (preserve custom sections)
    simple_config.model = model
    model_dict = simple_config.to_dict()
    for section, value in model_dict.items():
        app_config[section] = value

    # Update global configuration instance for adapter internals
    cfg = get_config()
    cfg.config_path = str(config_path)
    cfg.model = model
    cfg.config_data = app_config
    if hasattr(cfg, "feature_manager"):
        cfg.feature_manager.config_data = cfg.config_data

    # Register proxy commands
    register_proxy_commands()

    # Create app using adapter
    app = create_app(
        title="MCP Proxy Server",
        description="Proxy server built on MCP Proxy Adapter",
        version="1.0.0",
        app_config=app_config,
        config_path=str(config_path),
    )

    # Add compatibility REST endpoints for backward compatibility
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse
    from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
    from mcp_proxy_adapter.examples.full_application.proxy_commands import _registry

    compatibility_router = APIRouter()

    @compatibility_router.post("/register")
    async def register_rest(request: dict):  # type: ignore[name-defined]
        """
        REST endpoint for server registration (backward compatibility).
        
        Args:
            request: Registration request dictionary with server information
            
        Returns:
            JSONResponse with registration status
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"🔍 [PROXY] Received registration request: {request}")

        from mcp_proxy_adapter.examples.full_application.proxy_commands import (
            ProxyRegisterCommand,
        )

        try:
            cmd = ProxyRegisterCommand()
            logger.info("🔍 [PROXY] Created command, executing...")
            result = await cmd.execute(**request)
            logger.info(
                f"🔍 [PROXY] Command executed, result type: {type(result).__name__}"
            )
            if isinstance(result, ErrorResult):
                logger.error(f"🔍 [PROXY] Registration failed: {result.message}")
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "detail": result.message},
                )
            logger.info(
                f"🔍 [PROXY] Registration successful, server_id={result.server_id}"
            )
        except Exception as e:
            logger.error(f"🔍 [PROXY] Error executing command: {e}", exc_info=True)
            raise

        # result is SuccessResult (ProxyRegisterResult)
        if isinstance(result, SuccessResult):
            return JSONResponse(
                content={"status": "ok", "registered": result.server_id}
            )
        return JSONResponse(
            status_code=400, content={"status": "error", "detail": result.error}
        )

    @compatibility_router.post("/unregister")
    async def unregister_rest(request: dict):  # type: ignore[name-defined]
        """
        REST endpoint for server unregistration (backward compatibility).
        
        Args:
            request: Unregistration request dictionary with server_id
            
        Returns:
            JSONResponse with unregistration status
        """
        from mcp_proxy_adapter.examples.full_application.proxy_commands import (
            ProxyUnregisterCommand,
        )

        cmd = ProxyUnregisterCommand()
        result = await cmd.execute(**request)
        if isinstance(result, ErrorResult):
            return JSONResponse(
                status_code=400, content={"status": "error", "detail": result.message}
            )
        if isinstance(result, SuccessResult):
            return JSONResponse(
                content={"status": "ok", "unregistered": result.server_id}
            )
        return JSONResponse(
            status_code=400, content={"status": "error", "detail": result.error}
        )

    @compatibility_router.post("/proxy/heartbeat")
    async def heartbeat_rest(request: dict):  # type: ignore[name-defined]
        """
        REST endpoint for server heartbeat (backward compatibility).
        
        Args:
            request: Heartbeat request dictionary with server_id
            
        Returns:
            JSONResponse with heartbeat status
        """
        from mcp_proxy_adapter.examples.full_application.proxy_commands import (
            ProxyHeartbeatCommand,
        )

        cmd = ProxyHeartbeatCommand()
        result = await cmd.execute(**request)
        if isinstance(result, ErrorResult):
            return JSONResponse(
                status_code=404, content={"status": "error", "detail": result.message}
            )
        if isinstance(result, SuccessResult):
            return JSONResponse(content={"status": "ok", "heartbeat": result.server_id})
        return JSONResponse(
            status_code=404, content={"status": "error", "detail": result.error}
        )

    @compatibility_router.get("/servers")
    async def servers_rest():  # type: ignore[name-defined]
        """
        REST endpoint for listing all registered servers (backward compatibility).
        
        Returns:
            JSONResponse with list of registered servers and their metadata
        """
        servers = []
        for server_id, instances in _registry.items():
            for instance_key, server_data in instances.items():
                server_entry = {
                    "server_id": server_data.get("server_id", server_id),
                    "server_url": server_data.get("server_url", ""),
                    "capabilities": server_data.get("capabilities", []),
                    "metadata": server_data.get("metadata", {}),
                    "registered_at": server_data.get("registered_at", 0),
                    "last_heartbeat": server_data.get("last_heartbeat", 0),
                }
                # UUID must be at root level, not in metadata
                if "uuid" in server_data:
                    server_entry["uuid"] = server_data["uuid"]
                servers.append(server_entry)
        return JSONResponse(content=servers)

    app.include_router(compatibility_router)

    port = int(app_config.get("server", {}).get("port", 3004))
    host = app_config.get("server", {}).get("host", args.host)

    # Setup graceful shutdown
    def signal_handler(signum, frame):  # type: ignore[no-redef]
        """
        Handle shutdown signals gracefully.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        print("\n🛑 Proxy server stopping...")
        # Set stop flag for heartbeat loop (if running)
        from mcp_proxy_adapter.api.core.registration_manager import set_stop_flag_sync

        set_stop_flag_sync(True)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Determine protocol from server config
    server_cfg = app_config.get("server", {})
    proto = server_cfg.get("protocol", "http")
    scheme = "https" if proto in ("https", "mtls") else "http"

    print("🚀 Starting MCP Proxy Server (built on adapter)...")
    print(f"📡 Server URL: {scheme}://{host}:{port}")
    print("📋 Supported endpoints:")
    print("   JSON-RPC: proxy_register, proxy_unregister, proxy_heartbeat, proxy_list")
    print(
        "   REST (compatibility): POST /register, POST /unregister, POST /proxy/heartbeat, GET /servers"
    )
    print("⚡ Press Ctrl+C to stop\n")

    # Get server configuration for SSL setup
    server_cfg = app_config.get("server", {})
    transport = app_config.get("transport", {}) or {}
    proto = server_cfg.get("protocol", "http")
    
    # Prepare server configuration for adapter
    server_config = {
        "host": host,
        "port": port,
        "log_level": "info",
        "reload": False,
    }
    
    # Add SSL configuration using new ssl structure
    ssl_config = server_cfg.get("ssl", {})
    if ssl_config:
        # Use ServerConfigAdapter to convert SSL config
        from mcp_proxy_adapter.core.server_adapter import ServerConfigAdapter
        
        # Prepare SSL config dict (new format: cert, key, ca)
        ssl_config_dict = {
            "cert": ssl_config.get("cert"),
            "key": ssl_config.get("key"),
            "ca": ssl_config.get("ca"),
            "dnscheck": ssl_config.get("dnscheck", False),
            "verify_client": (proto == "mtls") or transport.get("verify_client", False),
        }
        
        # Convert to engine format
        hypercorn_ssl = ServerConfigAdapter.convert_ssl_config_for_engine(
            ssl_config_dict, "hypercorn"
        )
        server_config.update(hypercorn_ssl)
    
    # Run server using adapter (blocking call - engine.run_server uses asyncio.run internally)
    engine = ServerEngineFactory.get_engine("hypercorn")
    if not engine:
        raise RuntimeError("Hypercorn engine not available")
    
    engine.run_server(app, server_config)


if __name__ == "__main__":
    main()
