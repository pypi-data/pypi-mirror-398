"""
Queue Server Example for MCP Proxy Adapter.

This example demonstrates how to run an MCP server with queue integration
for managing background jobs.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
from hypercorn.asyncio import serve
from hypercorn.config import Config as HyperConfig
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
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    init_global_queue_manager,
    shutdown_global_queue_manager,
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


def create_queue_server_app() -> any:
    """Create MCP server application with queue integration."""
    app = create_app()
    
    @app.on_event("startup")
    async def _on_startup() -> None:
        await init_global_queue_manager()
        await setup_queue_commands()
    
    @app.on_event("shutdown")
    async def _on_shutdown() -> None:
        await shutdown_global_queue_manager()
    
    return app


async def main():
    """Main function to run the queue server with Hypercorn."""
    print("🚀 Starting MCP Proxy Adapter Queue Server")
    print("=" * 50)
    
    app = create_queue_server_app()

    hc = HyperConfig()
    hc.bind = ["0.0.0.0:8000"]
    hc.loglevel = "info"

    print("✅ MCP Queue Server will start at http://localhost:8000")
    print("📝 Example usage:")
    print("  curl -X POST http://localhost:8000/api/jsonrpc \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"jsonrpc\": \"2.0\", \"method\": \"queue_health\", \"params\": {}, \"id\": 1}'")
    print()

    await serve(app, hc)


if __name__ == "__main__":
    asyncio.run(main())
