#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Test Server for MCP Proxy Adapter Framework
This is a complete test server that demonstrates all features of MCP Proxy Adapter framework:
- Built-in commands
- Custom commands
- Dynamically loaded commands
- Built-in command hooks
- Application hooks

This server is used for comprehensive testing of all security modes.
"""
import argparse
import json
from pathlib import Path

from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.core.server_engine import ServerEngineFactory
from mcp_proxy_adapter.core.server_adapter import ServerConfigAdapter
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.core.config.simple_config import SimpleConfig
from mcp_proxy_adapter.config import get_config


def register_all_commands() -> None:
    """Register all available commands (built-in, load, queue, custom, dynamic)."""
    from mcp_proxy_adapter.commands.load_command import LoadCommand
    from mcp_proxy_adapter.commands.help_command import HelpCommand

    # Register help command
    registry.register(HelpCommand, "builtin")
    print("✅ Help command registered")

    # Register load command
    registry.register(LoadCommand, "builtin")
    print("✅ Load command registered")

    # Register custom commands from hooks
    try:
        from mcp_proxy_adapter.examples.full_application.commands.custom_echo_command import (
            CustomEchoCommand,
        )

        registry.register(CustomEchoCommand, "custom")
        print("✅ Custom echo command registered")
    except Exception as e:
        print(f"⚠️  Custom echo command not available: {e}")

    # Register dynamic calculator command
    try:
        from mcp_proxy_adapter.examples.full_application.commands.dynamic_calculator_command import (
            DynamicCalculatorCommand,
        )

        registry.register(DynamicCalculatorCommand, "custom")
        print("✅ Dynamic calculator command registered")
    except Exception as e:
        print(f"⚠️  Dynamic calculator command not available: {e}")

    # Register long-running queued command
    try:
        from mcp_proxy_adapter.examples.full_application.commands.long_running_command import (
            LongRunningCommand,
        )

        registry.register(LongRunningCommand, "custom")
        print("✅ Long-running queued command registered")
    except Exception as e:
        print(f"⚠️  Long-running queued command not available: {e}")

    # Note: Queue commands are automatically registered by register_builtin_commands()
    # if queue_manager is enabled in configuration. No manual registration needed.


def main() -> None:
    """Test server entrypoint for MCP Proxy Adapter."""
    parser = argparse.ArgumentParser(description="MCP Proxy Adapter Test Server")
    parser.add_argument("--config", required=True, help="Path to configuration file")
    parser.add_argument("--port", type=int, help="Port to run server on (override)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"❌ Configuration file not found: {cfg_path}")
        raise SystemExit(1)

    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            app_config = json.load(f)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Failed to load configuration: {exc}")
        raise SystemExit(1)

    # Load SimpleConfig model (standard adapter configuration)
    simple_config = SimpleConfig(str(cfg_path))
    model = simple_config.load()

    if args.port:
        app_config.setdefault("server", {}).update({"port": args.port})
        model.server.port = args.port
        print(f"🔧 Overriding port to {args.port}")
    if args.host:
        app_config.setdefault("server", {}).update({"host": args.host})
        model.server.host = args.host
        print(f"🔧 Overriding host to {args.host}")

    # Merge SimpleConfig sections back into raw config (preserve custom sections such as transport)
    simple_config.model = model
    model_dict = simple_config.to_dict()
    for section, value in model_dict.items():
        app_config[section] = value

    # Ensure required fields for validation (debug and log_level)
    if "server" not in app_config:
        app_config["server"] = {}
    app_config["server"].setdefault("debug", False)
    app_config["server"].setdefault("log_level", "INFO")

    # Update global configuration instance used by adapter internals
    cfg = get_config()
    cfg.config_path = str(cfg_path)
    setattr(cfg, "model", model)
    cfg.config_data = app_config
    if hasattr(cfg, "feature_manager"):
        cfg.feature_manager.config_data = cfg.config_data

    # Strict protocol checks: forbid any form of mTLS over HTTP
    # Work directly with server section (SimpleConfig format)
    server_cfg = app_config.get("server", {})
    proto = str(server_cfg.get("protocol", "http")).lower()

    # Get certificates from server section (new ssl structure)
    ssl_config = server_cfg.get("ssl", {})
    cert_file = ssl_config.get("cert") if ssl_config else None
    key_file = ssl_config.get("key") if ssl_config else None
    ca_cert_file = ssl_config.get("ca") if ssl_config else None

    transport = app_config.get("transport", {}) or {}
    require_client_cert = bool(transport.get("verify_client") or (proto == "mtls"))

    if proto == "http":
        if require_client_cert:
            raise SystemExit(
                "CRITICAL CONFIG ERROR: mTLS (client certificate verification) cannot be used with HTTP. "
                "Switch protocol to 'mtls' (or 'https' without client verification), and configure SSL certificates."
            )

    if proto == "mtls":
        if not (cert_file and key_file):
            raise SystemExit(
                "CRITICAL CONFIG ERROR: Protocol 'mtls' requires server.ssl.cert and server.ssl.key."
            )
        if not require_client_cert:
            raise SystemExit(
                "CRITICAL CONFIG ERROR: Protocol 'mtls' requires client certificate verification. "
                "Set transport.verify_client=true."
            )
        if not ca_cert_file:
            raise SystemExit("CRITICAL CONFIG ERROR: 'mtls' requires server.ssl.ca.")

    app = create_app(
        title="MCP Proxy Adapter Test Server",
        description="Test server for MCP Proxy Adapter with all features",
        version="1.0.0",
        app_config=app_config,
        config_path=str(cfg_path),
    )

    port = int(app_config.get("server", {}).get("port", 8080))
    host = app_config.get("server", {}).get("host", args.host)

    print("🚀 Starting MCP Proxy Adapter Test Server")
    print(f"📋 Configuration: {cfg_path}")
    print("============================================================")

    # Register all commands
    register_all_commands()
    print(
        f"📋 Registered commands: {', '.join(sorted(registry.get_all_commands().keys()))}"
    )

    # Prepare server configuration for ServerEngine
    server_config = {
        "host": host,
        "port": port,
        "log_level": "info",
        "reload": False,
    }

    # Add SSL configuration from server section (new ssl structure)
    ssl_config = server_cfg.get("ssl", {})
    if ssl_config:
        # Use ServerConfigAdapter to convert SSL config
        # Prepare SSL config dict (new format: cert, key, ca)
        ssl_config_dict = {
            "cert": ssl_config.get("cert"),
            "key": ssl_config.get("key"),
            "ca": ssl_config.get("ca"),
            "dnscheck": ssl_config.get("dnscheck", False),
            "verify_client": (server_cfg.get("protocol") == "mtls")
            or transport.get("verify_client", False),
        }

        # Convert to engine format
        hypercorn_ssl = ServerConfigAdapter.convert_ssl_config_for_engine(
            ssl_config_dict, "hypercorn"
        )
        server_config.update(hypercorn_ssl)

    # Optional proxy registration - support both old (proxy_registration) and new (registration) formats
    pr = {}
    if isinstance(app_config, dict):
        # Try new SimpleConfig format first (registration section)
        registration = app_config.get("registration", {})
        if registration and registration.get("enabled"):
            # Convert protocol to scheme (mtls -> https)
            reg_protocol = registration.get("protocol", "http")
            reg_scheme = "https" if reg_protocol in ("https", "mtls") else "http"
            pr = {
                "enabled": True,
                "proxy_url": f"{reg_scheme}://{registration.get('host', 'localhost')}:{registration.get('port', 3005)}",
                "server_id": registration.get("server_id")
                or registration.get("server_name"),
                "server_name": registration.get("server_name")
                or registration.get("server_id"),
                "auto_register_on_startup": registration.get("auto_on_startup", True),
                "auto_unregister_on_shutdown": registration.get(
                    "auto_on_shutdown", True
                ),
                "heartbeat": {
                    "enabled": True,
                    "interval": (
                        registration.get("heartbeat", {}).get("interval", 30)
                        if isinstance(registration.get("heartbeat"), dict)
                        else 30
                    ),
                },
            }
        # Fallback to old format (proxy_registration section)
        elif app_config.get("proxy_registration"):
            pr = app_config.get("proxy_registration", {})
        # Also check proxy_client (SimpleConfig old format)
        elif app_config.get("proxy_client", {}).get("enabled"):
            pc = app_config.get("proxy_client", {})
            # Convert protocol to scheme (mtls -> https)
            pc_protocol = pc.get("protocol", "http")
            pc_scheme = "https" if pc_protocol in ("https", "mtls") else "http"
            pr = {
                "enabled": True,
                "proxy_url": f"{pc_scheme}://{pc.get('host', 'localhost')}:{pc.get('port', 3005)}",
                "server_id": pc.get("server_id") or pc.get("server_name"),
                "server_name": pc.get("server_name") or pc.get("server_id"),
                "auto_register_on_startup": (
                    pc.get("registration", {}).get("auto_on_startup", True)
                    if isinstance(pc.get("registration"), dict)
                    else True
                ),
                "auto_unregister_on_shutdown": (
                    pc.get("registration", {}).get("auto_on_shutdown", True)
                    if isinstance(pc.get("registration"), dict)
                    else True
                ),
                "heartbeat": pc.get("heartbeat", {}),
            }

    name = pr.get("server_id") or pr.get("server_name") or "mcp-adapter"
    scheme = (
        "https"
        if str(app_config.get("server", {}).get("protocol", "http"))
        in ("https", "mtls")
        else "http"
    )
    advertised_host = (
        app_config.get("server", {}).get("advertised_host") or "mcp-adapter"
    )
    advertised_url = f"{scheme}://{advertised_host}:{port}"

    # Run server using adapter (blocking call - engine.run_server uses asyncio.run internally)
    engine = ServerEngineFactory.get_engine("hypercorn")
    if not engine:
        raise RuntimeError("Hypercorn engine not available")

    engine.run_server(app, server_config)


if __name__ == "__main__":
    main()
