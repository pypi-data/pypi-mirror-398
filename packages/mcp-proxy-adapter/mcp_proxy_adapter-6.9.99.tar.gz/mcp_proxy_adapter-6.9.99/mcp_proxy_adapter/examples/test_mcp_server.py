#!/usr/bin/env python3
"""
Test MCP Server for framework validation.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import logging
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestMCPServer:
    """Test MCP Server for framework validation."""
    
    def __init__(self):
        """
        Initialize test MCP server.
        """
        self.server = Server("test-mcp-server")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="echo",
                    description="Echo back the input message",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Message to echo back"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                types.Tool(
                    name="add",
                    description="Add two numbers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "a": {
                                "type": "number",
                                "description": "First number"
                            },
                            "b": {
                                "type": "number", 
                                "description": "Second number"
                            }
                        },
                        "required": ["a", "b"]
                    }
                ),
                types.Tool(
                    name="get_info",
                    description="Get server information",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls."""
            get_global_logger().info(f"Tool called: {name} with args: {arguments}")
            
            if name == "echo":
                message = arguments.get("message", "")
                return [types.TextContent(type="text", text=f"Echo: {message}")]
            
            elif name == "add":
                a = arguments.get("a", 0)
                b = arguments.get("b", 0)
                result = a + b
                return [types.TextContent(type="text", text=f"Result: {a} + {b} = {result}")]
            
            elif name == "get_info":
                info = {
                    "server_name": "test-mcp-server",
                    "version": "1.0.0",
                    "status": "running",
                    "tools_count": 3
                }
                return [types.TextContent(type="text", text=json.dumps(info, indent=2))]
            
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        
        @self.server.list_resources()
        async def list_resources() -> List[types.Resource]:
            """List available resources."""
            return [
                types.Resource(
                    uri="test://config",
                    name="Server Configuration",
                    description="Current server configuration",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="test://status",
                    name="Server Status", 
                    description="Current server status",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content."""
            if uri == "test://config":
                config = {
                    "server_name": "test-mcp-server",
                    "port": 3001,
                    "protocol": "stdio",
                    "features": ["tools", "resources"]
                }
                return json.dumps(config, indent=2)
            
            elif uri == "test://status":
                status = {
                    "status": "running",
                    "uptime": "0s",
                    "requests_handled": 0,
                    "last_request": None
                }
                return json.dumps(status, indent=2)
            
            else:
                raise ValueError(f"Unknown resource: {uri}")
        
        @self.server.list_prompts()
        async def list_prompts() -> List[types.Prompt]:
            """List available prompts."""
            return [
                types.Prompt(
                    name="greeting",
                    description="Generate a greeting message",
                    arguments=[
                        types.PromptArgument(
                            name="name",
                            description="Name to greet",
                            required=True
                        )
                    ]
                )
            ]
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, str]) -> List[types.TextContent]:
            """Get prompt content."""
            if name == "greeting":
                user_name = arguments.get("name", "User")
                greeting = f"Hello, {user_name}! Welcome to the test MCP server."
                return [types.TextContent(type="text", text=greeting)]
            
            else:
                raise ValueError(f"Unknown prompt: {name}")

async def main():
    """Main server function."""
    get_global_logger().info("Starting Test MCP Server...")
    
    server_instance = TestMCPServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
