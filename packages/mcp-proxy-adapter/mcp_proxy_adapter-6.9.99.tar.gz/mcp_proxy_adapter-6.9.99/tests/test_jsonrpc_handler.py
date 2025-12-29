#!/usr/bin/env python3
"""
Test script to check JSON-RPC handler.
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp_proxy_adapter'))

# Skip this file in pytest runs - it's a standalone script
import pytest
pytest.skip("Standalone scenario", allow_module_level=True)

from mcp_proxy_adapter.api.handlers import execute_command
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.builtin_commands import register_builtin_commands

async def test_jsonrpc_handler():
    print("Testing JSON-RPC handler...")
    
    # Register built-in commands first
    try:
        count = register_builtin_commands()
        print(f"✅ Registered {count} built-in commands")
    except Exception as e:
        print(f"❌ Failed to register built-in commands: {e}")
        return
    
    # Test echo command
    try:
        result = await execute_command("echo", {"message": "Hello World"})
        print(f"✅ Echo command result: {result}")
    except Exception as e:
        print(f"❌ Echo command failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test health command
    try:
        result = await execute_command("health", {})
        print(f"✅ Health command result: {result}")
    except Exception as e:
        print(f"❌ Health command failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_jsonrpc_handler())
