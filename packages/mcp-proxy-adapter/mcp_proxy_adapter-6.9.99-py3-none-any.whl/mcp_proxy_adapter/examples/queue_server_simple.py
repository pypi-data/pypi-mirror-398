#!/usr/bin/env python3
"""
Simple Queue Server for MCP Proxy Adapter.

This example demonstrates how to run an MCP server with queue integration
using a minimal configuration.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import uvicorn
from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.queue_commands import (
    QueueAddJobCommand,
    QueueStartJobCommand,
    QueueStopJobCommand,
    QueueDeleteJobCommand,
    QueueGetJobStatusCommand,
    QueueListJobsCommand,
    QueueHealthCommand,
)


def setup_queue_commands():
    """Setup queue management commands."""
    print("🔧 Setting up queue management commands...")
    
    # Register queue commands
    registry.register_custom(QueueAddJobCommand())
    registry.register_custom(QueueStartJobCommand())
    registry.register_custom(QueueStopJobCommand())
    registry.register_custom(QueueDeleteJobCommand())
    registry.register_custom(QueueGetJobStatusCommand())
    registry.register_custom(QueueListJobsCommand())
    registry.register_custom(QueueHealthCommand())
    
    print("✅ Queue commands registered")


def create_queue_server_app():
    """Create MCP server application with queue integration."""
    # Create minimal config
    config = {
        "uuid": "123e4567-e89b-42d3-8a56-426614174000",
        "server": {
            "host": "172.28.0.1",
            "port": 8000,
            "protocol": "http",
            "debug": False,
            "log_level": "INFO"
        },
        "logging": {
            "level": "INFO",
            "file": None,
            "log_dir": "./logs",
            "log_file": "mcp_proxy_adapter.log",
            "error_log_file": "mcp_proxy_adapter_error.log",
            "access_log_file": "mcp_proxy_adapter_access.log",
            "max_file_size": "10MB",
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S",
            "console_output": True,
            "file_output": True
        },
        "commands": {
            "auto_discovery": True,
            "commands_directory": "./commands",
            "catalog_directory": "./catalog",
            "plugin_servers": [],
            "auto_install_dependencies": True,
            "enabled_commands": ["health", "echo", "list", "help"],
            "disabled_commands": [],
            "custom_commands_path": "./commands"
        },
        "transport": {
            "type": "http",
            "port": 8000
        },
        "ssl": {
            "enabled": False
        },
        "proxy_registration": {
            "enabled": True,
            "proxy_url": "https://172.28.0.4:3004",
            "server_id": "mcp_queue_server",
            "server_name": "MCP Queue Server",
            "description": "Queue management server with mTLS",
            "version": "6.9.28",
            "protocol": "mtls",
            "ssl": {
                "enabled": True,
                "verify_ssl": False,
                "verify_hostname": False,
                "verify_mode": "CERT_REQUIRED",
                "ca_cert": "./mtls_certificates/ca/ca.crt",
                "cert_file": "./mtls_certificates/client/test-client.crt",
                "key_file": "./mtls_certificates/client/test-client.key"
            },
            "certificate": {
                "cert_file": "./mtls_certificates/client/test-client.crt",
                "key_file": "./mtls_certificates/client/test-client.key"
            },
            "registration_timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 5,
            "auto_register_on_startup": True,
            "auto_unregister_on_shutdown": True,
            "heartbeat": {
                "enabled": True,
                "interval": 30,
                "timeout": 10,
                "retry_attempts": 3,
                "retry_delay": 5,
                "url": "/heartbeat"
            }
        },
        "debug": {
            "enabled": False,
            "level": "WARNING"
        },
        "security": {
            "enabled": False
        },
        "roles": {
            "enabled": False
        }
    }
    
    # Register commands before creating the app
    setup_queue_commands()
    
    app = create_app(app_config=config)
    
    @app.on_event("startup")
    async def startup_event():
        """Startup event handler."""
        print("🚀 Queue server started")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler."""
        print("🛑 Queue server stopped")
    
    return app


async def main():
    """Main function to run the queue server."""
    print("🚀 Starting MCP Proxy Adapter Queue Server")
    print("=" * 50)
    
    # Create the app
    app = create_queue_server_app()
    
    # Run the server
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    print("✅ MCP Queue Server started at http://localhost:8000")
    print("📝 Example usage:")
    print("  curl -X POST http://localhost:8000/api/jsonrpc \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"jsonrpc\": \"2.0\", \"method\": \"queue_health\", \"params\": {}, \"id\": 1}'")
    print()
    
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
