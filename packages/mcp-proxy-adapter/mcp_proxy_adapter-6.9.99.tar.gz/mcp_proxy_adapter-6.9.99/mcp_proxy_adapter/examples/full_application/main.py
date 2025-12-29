#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Full Application Example

This is a complete application that demonstrates all features of MCP Proxy Adapter framework:
- Built-in commands
- Custom commands
- Dynamically loaded commands
- Built-in command hooks
- Application hooks

CRITICAL: Commands with use_queue=True and Spawn Mode
-----------------------------------------------------
This example includes commands that use use_queue=True (e.g., LongRunningCommand).
These commands execute in child processes when using multiprocessing spawn mode.

IMPORTANT REGISTRATION REQUIREMENTS FOR QUEUE COMMANDS:
1. Commands are registered in main process via register_all_commands()
2. For spawn mode compatibility, modules are automatically registered for auto-import
   when using register_custom_commands_hook() (module path is extracted automatically)
3. Alternatively, you can manually register modules using register_auto_import_module()
4. Environment variable MCP_AUTO_REGISTER_MODULES can be used as fallback

HOW IT WORKS:
- Main process: Commands registered via registry.register()
- Child process (spawn mode): Modules are imported, triggering auto-registration
- Commands become available in child process without pickle issues

This example demonstrates the recommended approach: direct registration in main process
combined with automatic module path extraction for child process support.
"""
import argparse
import json
from pathlib import Path

from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.core.server_engine import ServerEngineFactory
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.core.config.simple_config import SimpleConfig
from mcp_proxy_adapter.config import get_config
from mcp_proxy_adapter.core.app_factory.ssl_config import build_server_ssl_config


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

    # Register long-running command with queue
    # CRITICAL: This command uses use_queue=True, so it executes in child processes
    # The module path is automatically registered for auto-import in spawn mode
    # when using register_custom_commands_hook() (see hooks/application_hooks.py)
    try:
        from mcp_proxy_adapter.examples.full_application.commands.long_running_command import (
            LongRunningCommand,
        )
        from mcp_proxy_adapter.commands.hooks import register_auto_import_module

        registry.register(LongRunningCommand, "custom")
        # Register module for auto-import in child processes (spawn mode)
        register_auto_import_module(
            "mcp_proxy_adapter.examples.full_application.commands.long_running_command"
        )
        print("✅ Long-running command registered (with spawn mode support)")
    except Exception as e:
        print(f"⚠️  Long-running command not available: {e}")

    # Register embed_queue and embed_job_status commands
    try:
        from mcp_proxy_adapter.examples.full_application.commands.embed_queue_command import (
            EmbedQueueCommand,
        )
        from mcp_proxy_adapter.examples.full_application.commands.embed_job_status_command import (
            EmbedJobStatusCommand,
        )

        registry.register(EmbedQueueCommand, "custom")
        registry.register(EmbedJobStatusCommand, "custom")
        print("✅ Embed queue commands registered (embed_queue, embed_job_status)")
    except Exception as e:
        print(f"⚠️  Embed queue commands not available: {e}")

    # Register slow-start long task command for testing fire-and-forget execution
    try:
        from mcp_proxy_adapter.examples.full_application.commands.slow_start_long_task_command import (
            SlowStartLongTaskCommand,
        )

        registry.register(SlowStartLongTaskCommand, "custom")
        # Register module for auto-import in child processes (spawn mode)
        register_auto_import_module(
            "mcp_proxy_adapter.examples.full_application.commands.slow_start_long_task_command"
        )
        print("✅ Slow-start long task command registered (for fire-and-forget testing)")
    except Exception as e:
        print(f"⚠️  Slow-start long task command not available: {e}")

    # Note: Queue commands are automatically registered by register_builtin_commands()
    # if queue_manager is enabled in configuration. No manual registration needed.


def main() -> None:
    """Minimal runnable entrypoint for full application example."""
    parser = argparse.ArgumentParser(description="MCP Proxy Adapter Full Application")
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

    # Validate configuration before starting server
    from mcp_proxy_adapter.core.config.simple_config_validator import (
        SimpleConfigValidator,
    )

    validator = SimpleConfigValidator(config_path=str(cfg_path))
    validation_errors = validator.validate(model)
    if validation_errors:
        print("❌ Configuration validation failed:")
        for error in validation_errors:
            print(f"   - {error.message}")
        # Check for instance_uuid validation errors specifically
        uuid_errors = [
            e for e in validation_errors if "instance_uuid" in e.message.lower()
        ]
        if uuid_errors:
            print("\n⚠️  Instance UUID validation errors detected:")
            print(
                "   - registration.instance_uuid is required when registration.enabled=true"
            )
            print("   - instance_uuid must be a valid UUID4 format")
            print("   - Example: 550e8400-e29b-41d4-a716-446655440000")
        print("\n❌ Server startup aborted due to configuration validation errors.")
        raise SystemExit(1)

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
        title="Full Application Example",
        description="Complete MCP Proxy Adapter with all features",
        version="1.0.0",
        app_config=app_config,
        config_path=str(cfg_path),
    )

    port = int(app_config.get("server", {}).get("port", 8080))
    host = app_config.get("server", {}).get("host", args.host)

    print("🚀 Starting Full Application Example")
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

    try:
        ssl_engine_config = build_server_ssl_config(app_config)
        if ssl_engine_config:
            server_config.update(ssl_engine_config)
    except ValueError as exc:
        print(f"❌ SSL configuration invalid: {exc}")
        raise SystemExit(1)

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

    # Note: server_config was already prepared above (lines 169-193)
    # No need to duplicate SSL configuration setup here

    # Run server using adapter (blocking call - engine.run_server uses asyncio.run internally)
    engine = ServerEngineFactory.get_engine("hypercorn")
    if not engine:
        raise RuntimeError("Hypercorn engine not available")

    engine.run_server(app, server_config)


if __name__ == "__main__":
    main()
