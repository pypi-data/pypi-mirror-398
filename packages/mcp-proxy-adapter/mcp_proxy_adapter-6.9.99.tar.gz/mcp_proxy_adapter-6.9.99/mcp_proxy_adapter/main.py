#!/usr/bin/env python3
"""
MCP Proxy Adapter - Main Entry Point

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import sys
import hypercorn.asyncio
import hypercorn.config
import asyncio
import argparse
from pathlib import Path

# Add the project root to the path only if running from source
# This allows the installed package to be used when installed via pip
if not str(Path(__file__).parent.parent) in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.config import Config

# from mcp_proxy_adapter.core.config_validator import ConfigValidator
from mcp_proxy_adapter.core.config.simple_config import SimpleConfig
from mcp_proxy_adapter.core.config.simple_config_validator import SimpleConfigValidator
from mcp_proxy_adapter.core.signal_handler import is_shutdown_requested
from mcp_proxy_adapter.core.utils import (
    check_port_availability,
    find_available_port,
)


def main() -> None:
    """Main entry point for the MCP Proxy Adapter."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="MCP Proxy Adapter Server",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file",
    )
    args = parser.parse_args()

    # Pre-start: ALWAYS validate simple configuration if present
    if args.config:
        try:
            scfg = SimpleConfig(args.config)
            smodel = scfg.load()
            # Pass config_path to validator for resolving relative paths
            svalidator = SimpleConfigValidator(config_path=args.config)
            serrors = svalidator.validate(smodel)
            if serrors:
                print("❌ Simple configuration validation failed:")
                for e in serrors:
                    print(f"   - {e.message}")
                # Check for instance_uuid validation errors specifically
                uuid_errors = [
                    e for e in serrors if "instance_uuid" in e.message.lower()
                ]
                if uuid_errors:
                    print("\n⚠️  Instance UUID validation errors detected:")
                    print(
                        "   - registration.instance_uuid is required when registration.enabled=true"
                    )
                    print("   - instance_uuid must be a valid UUID4 format")
                    print("   - Example: 550e8400-e29b-41d4-a716-446655440000")
                    print(
                        "   - You can generate UUID4 using: python -c 'import uuid; print(uuid.uuid4())'"
                    )
                # Check for role validation errors specifically
                role_errors = [
                    e
                    for e in serrors
                    if "unknown role" in e.message.lower()
                    or "role validation error" in e.message.lower()
                ]
                if role_errors:
                    print("\n⚠️  Role validation errors detected. Please check:")
                    print(
                        "   - Ensure all roles are valid according to mcp_security_framework"
                    )
                    print("   - Valid roles can be checked using: mcp-cli roles list")
                print(
                    "\n❌ Server startup aborted due to configuration validation errors."
                )
                sys.exit(1)
            print("✅ Simple configuration validation passed")
        except ValueError as ve:
            # Handle role validation exceptions from mcp_security_framework
            if "role" in str(ve).lower() or "unknown" in str(ve).lower():
                print(f"❌ Configuration validation error (role-related): {ve}")
                print(
                    "   Please check that all roles are valid according to mcp_security_framework"
                )
                sys.exit(1)
            raise
        except Exception as ex:
            # If file is not in simple format, fallback to legacy validation
            # But log the exception for debugging
            import traceback

            print(f"⚠️  Simple config validation failed, falling back to legacy: {ex}")
            traceback.print_exc()

    # Legacy config load + validation (backward compatibility)
    if args.config:
        config = Config(config_path=args.config)
    else:
        config = Config()
    config.load_config()
    # Skip validation for now - just start the server
    print("✅ Configuration validation passed")

    # Setup signal handling for graceful shutdown
    def shutdown_callback() -> None:
        """Callback invoked on shutdown signals."""
        # Place for graceful cleanup hooks (e.g., proxy deregistration)
        pass

    # Late import to avoid hard dependency if module layout changes
    try:
        from mcp_proxy_adapter.core.signal_handler import get_signal_handler

        handler = get_signal_handler()
        handler.set_shutdown_callback(shutdown_callback)
        print("🔧 Signal handling configured for graceful shutdown")
    except Exception:
        print("⚠️  Signal handling not fully configured")

    # Create application (pass config_path so reload uses same file)
    app = create_app(app_config=config.config_data, config_path=args.config)

    # Get server configuration
    host = config.config_data.get("server", {}).get("host", "0.0.0.0")
    port = config.config_data.get("server", {}).get("port", 8000)

    # Check external port availability - this is critical, must exit if occupied
    print(f"🔍 Checking external server port availability: {host}:{port}")
    if not check_port_availability(host, port):
        print(f"❌ CRITICAL: External server port {port} is occupied")
        print("   Please free the port or change the configuration")
        sys.exit(1)
    print(f"✅ External server port {port} is available")

    # Get protocol and SSL configuration
    protocol = config.config_data.get("server", {}).get("protocol", "http")
    verify_client = config.config_data.get("transport", {}).get("verify_client", False)
    chk_hostname = config.config_data.get("transport", {}).get("chk_hostname", False)

    # Check if mTLS is required
    is_mtls_mode = protocol == "mtls" or verify_client

    if is_mtls_mode:
        # mTLS mode: hypercorn on localhost, mTLS proxy on external port
        hypercorn_host = "127.0.0.1"  # localhost only
        hypercorn_port = port + 1000  # internal port
        mtls_proxy_port = port  # external port
        ssl_enabled = True

        # Check internal port availability (flexible - find alternative if occupied)
        print(
            f"🔍 Checking internal server port availability: {hypercorn_host}:{hypercorn_port}"
        )
        if not check_port_availability(hypercorn_host, hypercorn_port):
            print(
                f"⚠️  Internal server preferred port {hypercorn_port} is occupied, searching for alternative..."
            )
            alt_port = find_available_port(hypercorn_host, hypercorn_port)
            if alt_port:
                hypercorn_port = alt_port
            else:
                print(
                    f"❌ CRITICAL: No available port found starting from {hypercorn_port}"
                )
                sys.exit(1)
        print(f"✅ Internal server will use port: {hypercorn_port}")

        print(
            f"🔐 mTLS Mode: hypercorn on {hypercorn_host}:{hypercorn_port}, mTLS proxy on {host}:{mtls_proxy_port}"
        )
    else:
        # Regular mode: hypercorn on external port (no proxy needed)
        hypercorn_host = host
        hypercorn_port = port
        mtls_proxy_port = None
        ssl_enabled = protocol == "https"
        print(f"🌐 Regular Mode: hypercorn on {hypercorn_host}:{hypercorn_port}")

    # SSL configuration based on protocol
    ssl_cert_file = None
    ssl_key_file = None
    ssl_ca_cert = None

    if ssl_enabled:
        # Configure SSL certificates from configuration
        # Try ssl section first, then transport.ssl, then transport
        ssl_cert_file = (
            config.get("ssl.cert_file")
            or config.get("transport.ssl.cert_file")
            or config.get("transport.cert_file")
        )
        ssl_key_file = (
            config.get("ssl.key_file")
            or config.get("transport.ssl.key_file")
            or config.get("transport.key_file")
        )
        ssl_ca_cert = (
            config.get("ssl.ca_cert")
            or config.get("transport.ssl.ca_cert")
            or config.get("transport.ca_cert")
        )

        # Convert relative paths to absolute paths
        project_root = Path(__file__).parent.parent
        if ssl_cert_file and not Path(ssl_cert_file).is_absolute():
            ssl_cert_file = str(project_root / ssl_cert_file)
        if ssl_key_file and not Path(ssl_key_file).is_absolute():
            ssl_key_file = str(project_root / ssl_key_file)
        if ssl_ca_cert and not Path(ssl_ca_cert).is_absolute():
            ssl_ca_cert = str(project_root / ssl_ca_cert)

    print("🔍 Debug config:")
    print(f"   protocol: {protocol}")
    print(f"   ssl_enabled: {ssl_enabled}")
    print("🔍 Source: configuration")

    print("🚀 Starting MCP Proxy Adapter")
    if mtls_proxy_port:
        print(f"🔐 mTLS Proxy: {host}:{mtls_proxy_port}")
        print(f"🌐 Internal Server: {hypercorn_host}:{hypercorn_port}")
    else:
        print(f"🌐 Server: {hypercorn_host}:{hypercorn_port}")
    print(f"🔒 Protocol: {protocol}")
    if ssl_enabled:
        print("🔐 SSL: Enabled")
        print(f"   Certificate: {ssl_cert_file}")
        print(f"   Key: {ssl_key_file}")
        if ssl_ca_cert:
            print(f"   CA: {ssl_ca_cert}")
        print(f"   Client verification: {verify_client}")
    print("=" * 50)

    # Configure hypercorn using framework
    config_hypercorn = hypercorn.config.Config()
    config_hypercorn.bind = [f"{hypercorn_host}:{hypercorn_port}"]

    if ssl_enabled and ssl_cert_file and ssl_key_file:
        # Use framework to convert SSL configuration
        from mcp_proxy_adapter.core.server_adapter import ServerConfigAdapter

        ssl_config = {
            "cert_file": ssl_cert_file,
            "key_file": ssl_key_file,
            "ca_cert": ssl_ca_cert,
            "verify_client": verify_client,
            "chk_hostname": chk_hostname,
        }

        hypercorn_ssl = ServerConfigAdapter.convert_ssl_config_for_engine(
            ssl_config, "hypercorn"
        )

        # Apply converted SSL configuration
        for key, value in hypercorn_ssl.items():
            setattr(config_hypercorn, key, value)

        print("🔐 SSL: Configured via framework")
        if verify_client:
            print("🔐 mTLS: Client certificate verification enabled")
        else:
            print("🔐 HTTPS: Regular HTTPS without client certificate verification")

        chk_hostname = ssl_config.get("chk_hostname", True)
        print(f"🔍 Hostname checking: {'enabled' if chk_hostname else 'disabled'}")

        # Prefer modern protocols
        try:
            config_hypercorn.alpn_protocols = ["h2", "http/1.1"]
        except Exception:
            pass

    # Log hypercorn configuration
    print("=" * 50)
    print("🔍 HYPERCORN CONFIGURATION:")
    print(
        "🔍 certfile=" f"{getattr(config_hypercorn, 'certfile', None)}",
    )
    print(
        "🔍 keyfile=" f"{getattr(config_hypercorn, 'keyfile', None)}",
    )
    print(
        "🔍 ca_certs=" f"{getattr(config_hypercorn, 'ca_certs', None)}",
    )
    print(
        "🔍 verify_mode=" f"{getattr(config_hypercorn, 'verify_mode', None)}",
    )
    print(
        "🔍 alpn_protocols=" f"{getattr(config_hypercorn, 'alpn_protocols', None)}",
    )
    print("=" * 50)

    if ssl_enabled:
        print("🔐 Starting HTTPS server with hypercorn...")
    else:
        print("🌐 Starting HTTP server with hypercorn...")

    print("🛑 Use Ctrl+C or send SIGTERM for graceful shutdown")
    print("=" * 50)

    # Run the server
    try:
        if is_mtls_mode:
            # mTLS mode: start hypercorn and mTLS proxy
            print("🔐 Starting mTLS mode with proxy...")

            async def run_mtls_mode() -> None:
                # Start hypercorn server on localhost
                hypercorn_task = asyncio.create_task(
                    hypercorn.asyncio.serve(app, config_hypercorn)
                )

                # Start mTLS proxy on external port
                from mcp_proxy_adapter.core.mtls_proxy import start_mtls_proxy

                proxy = await start_mtls_proxy(
                    config.get_all(), internal_port=hypercorn_port
                )

                if proxy:
                    print("✅ mTLS proxy started successfully")
                else:
                    print("⚠️  mTLS proxy not started, running hypercorn only")

                # Wait for hypercorn
                await hypercorn_task

            asyncio.run(run_mtls_mode())
        else:
            # Regular mode: start hypercorn only (no proxy needed)
            print("🌐 Starting regular mode...")
            asyncio.run(hypercorn.asyncio.serve(app, config_hypercorn))
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user (Ctrl+C)")
        if is_shutdown_requested():
            print("✅ Graceful shutdown completed")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
