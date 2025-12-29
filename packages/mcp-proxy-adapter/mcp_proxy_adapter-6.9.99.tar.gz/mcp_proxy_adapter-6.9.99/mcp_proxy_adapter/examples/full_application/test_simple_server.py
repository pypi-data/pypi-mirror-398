#!/usr/bin/env python3
"""
Simple server test using the framework.
"""

import sys
import json
import signal
from pathlib import Path

from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.core.server_engine import ServerEngineFactory
from mcp_proxy_adapter.core.server_adapter import ServerConfigAdapter
from mcp_proxy_adapter.core.config.simple_config import SimpleConfig
from mcp_proxy_adapter.config import get_config
from mcp_proxy_adapter.commands.command_registry import registry

def register_test_commands():
    """Register test commands."""
    from mcp_proxy_adapter.commands.help_command import HelpCommand
    registry.register(HelpCommand, "builtin")
    print("✅ Test commands registered")

def main():
    """Test simple server startup using framework."""
    print("🚀 Testing Simple Server Startup")
    print("=" * 50)
    
    # Load configuration
    config_path = Path(__file__).parent / "configs" / "http_basic.json"
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    try:
        # Load configuration
        with config_path.open("r", encoding="utf-8") as f:
            app_config = json.load(f)
        
        # Load SimpleConfig model
        simple_config = SimpleConfig(str(config_path))
        model = simple_config.load()
        
        # Update global configuration
        cfg = get_config()
        cfg.config_path = str(config_path)
        cfg.model = model
        cfg.config_data = app_config
        if hasattr(cfg, "feature_manager"):
            cfg.feature_manager.config_data = cfg.config_data
        
        print(f"✅ Configuration loaded: {config_path}")
        
        # Register commands
        register_test_commands()
        
        # Create app
        app = create_app(
            title="Test Server",
            description="Simple test server using framework",
            version="1.0.0",
            app_config=app_config,
            config_path=str(config_path),
        )
        
        print("✅ FastAPI app created successfully")
        
        # Setup graceful shutdown
        def signal_handler(signum, frame):
            print("\n🛑 Test server stopping...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Get server configuration
        server_cfg = app_config.get("server", {})
        host = server_cfg.get("host", "0.0.0.0")
        port = server_cfg.get("port", 8080)
        proto = server_cfg.get("protocol", "http")
        
        # Prepare server configuration
        server_config = {
            "host": host,
            "port": port,
            "log_level": "info",
            "reload": False,
        }
        
        # Add SSL configuration if needed
        ssl_config = server_cfg.get("ssl", {})
        if ssl_config:
            ssl_config_dict = {
                "cert": ssl_config.get("cert"),
                "key": ssl_config.get("key"),
                "ca": ssl_config.get("ca"),
                "dnscheck": ssl_config.get("dnscheck", False),
                "verify_client": (proto == "mtls"),
            }
            hypercorn_ssl = ServerConfigAdapter.convert_ssl_config_for_engine(
                ssl_config_dict, "hypercorn"
            )
            server_config.update(hypercorn_ssl)
        
        scheme = "https" if proto in ("https", "mtls") else "http"
        print(f"🚀 Starting server on {scheme}://{host}:{port}")
        print(f"📡 Test with: curl -X POST {scheme}://localhost:{port}/api/jsonrpc -H 'Content-Type: application/json' -d '{{\"jsonrpc\": \"2.0\", \"method\": \"help\", \"id\": 1}}'")
        print("🛑 Press Ctrl+C to stop")
        
        # Run server using framework
        engine = ServerEngineFactory.get_engine("hypercorn")
        if not engine:
            raise RuntimeError("Hypercorn engine not available")
        
        engine.run_server(app, server_config)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
