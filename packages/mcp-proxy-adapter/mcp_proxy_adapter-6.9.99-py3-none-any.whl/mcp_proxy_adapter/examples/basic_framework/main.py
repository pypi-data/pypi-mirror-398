#!/usr/bin/env python3
"""
Basic Framework Example
This example demonstrates the basic usage of the MCP Proxy Adapter framework
with minimal configuration and built-in commands.
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import sys
import argparse
from pathlib import Path

# Add the framework to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from mcp_proxy_adapter.core.app_factory import create_and_run_server


def main():
    """Main entry point for the basic framework example."""
    parser = argparse.ArgumentParser(description="Basic Framework Example")
    parser.add_argument(
        "--config", "-c", required=True, help="Path to configuration file"
    )
    parser.add_argument("--host", help="Server host")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    print(f"🚀 Starting Basic Framework Example")
    print(f"📋 Configuration: {args.config}")
    if args.host:
        print(f"🌐 Host override: {args.host}")
    if args.port:
        print(f"🔌 Port override: {args.port}")
    if args.debug:
        print(f"🔧 Debug mode: enabled")
    print("=" * 50)
    
    # Note: Host and port overrides should be handled in configuration file
    # or by modifying the configuration before passing to create_and_run_server
    import asyncio
    asyncio.run(create_and_run_server(
        config_path=args.config,
        title="Basic Framework Example",
        description="Basic MCP Proxy Adapter with minimal configuration",
        version="1.0.0",
        host=args.host or "0.0.0.0",
        log_level="debug" if args.debug else "info"
    ))


if __name__ == "__main__":
    main()
