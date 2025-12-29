"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Server runner for app factory.
"""

import sys
from typing import Dict, Any, Optional

import hypercorn.asyncio
import hypercorn.config

from fastapi import FastAPI


async def run_server(
    app: FastAPI,
    server_config: Dict[str, Any],
    mtls_server: Optional[Any] = None,
) -> None:
    """
    Run the server with hypercorn.

    Args:
        app: FastAPI application
        server_config: Server configuration dictionary
        mtls_server: Optional mTLS server instance

    Raises:
        SystemExit: If server fails to start
    """
    try:
        print("🚀 Starting main server...")
        print("   Use Ctrl+C to stop the server")
        print("=" * 60)

        # Configure hypercorn
        config_hypercorn = hypercorn.config.Config()
        config_hypercorn.bind = [f"{server_config['host']}:{server_config['port']}"]
        config_hypercorn.loglevel = server_config.get("log_level", "info")

        # Add SSL shutdown timeout to prevent SSL shutdown timeout errors
        config_hypercorn.ssl_handshake_timeout = 10.0
        config_hypercorn.keep_alive_timeout = 5.0

        # Add SSL configuration if present
        if "certfile" in server_config:
            config_hypercorn.certfile = server_config["certfile"]
        if "keyfile" in server_config:
            config_hypercorn.keyfile = server_config["keyfile"]
        if "ca_certs" in server_config:
            config_hypercorn.ca_certs = server_config["ca_certs"]

        ssl_context = server_config.get("ssl_context")
        if ssl_context is not None:
            config_hypercorn.verify_mode = ssl_context.verify_mode  # type: ignore[attr-defined]
            config_hypercorn.create_ssl_context = lambda ctx=ssl_context: ctx  # type: ignore[assignment]

        # Determine if SSL is enabled
        ssl_enabled = any(key in server_config for key in ["certfile", "keyfile"])
        verify_client = server_config.get("verify_client", False)

        if ssl_enabled:
            if verify_client:
                print(
                    f"🔐 Starting external mTLS proxy with hypercorn "
                    f"(internal server on port {mtls_server.port if mtls_server else 'N/A'})..."
                )
            else:
                print("🔐 Starting HTTPS server with hypercorn...")
        else:
            print("🌐 Starting HTTP server with hypercorn...")

        # Run the server
        await hypercorn.asyncio.serve(app, config_hypercorn)  # type: ignore[arg-type]

    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        if mtls_server:
            print("🛑 Stopping internal mTLS server...")
            mtls_server.stop()
    except OSError as e:
        print(f"\n❌ Failed to start server: {e}")
        if mtls_server:
            print("🛑 Stopping mTLS server...")
            mtls_server.stop()
        import traceback

        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        if mtls_server:
            print("🛑 Stopping internal mTLS server...")
            mtls_server.stop()
        import traceback

        traceback.print_exc()
        sys.exit(1)
