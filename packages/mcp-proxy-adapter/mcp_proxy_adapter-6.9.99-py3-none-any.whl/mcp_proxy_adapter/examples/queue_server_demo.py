#!/usr/bin/env python3
"""
Queue Server Demo for MCP Proxy Adapter.

This example demonstrates how to run an MCP server with queue integration
using a mock queue manager for demonstration purposes.

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


async def setup_queue_commands():
    """Setup queue management commands."""
    print("🔧 Setting up queue management commands...")
    
    # Register queue commands
    registry.register(QueueAddJobCommand())
    registry.register(QueueStartJobCommand())
    registry.register(QueueStopJobCommand())
    registry.register(QueueDeleteJobCommand())
    registry.register(QueueGetJobStatusCommand())
    registry.register(QueueListJobsCommand())
    registry.register(QueueHealthCommand())
    
    print("✅ Queue commands registered")


def create_queue_server_app():
    """Create MCP server application with queue integration."""
    app = create_app()
    
    @app.on_event("startup")
    async def startup_event():
        """Startup event handler."""
        print("🚀 Queue server demo started")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler."""
        print("🛑 Queue server demo stopped")
    
    return app


async def main():
    """Main function to run the queue server."""
    print("🚀 Starting MCP Proxy Adapter Queue Server Demo")
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
