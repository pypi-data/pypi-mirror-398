#!/usr/bin/env python3
"""
Test script to check reload_system.
"""
import sys
import os
import asyncio
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp_proxy_adapter'))

# Skip this file in pytest runs - it's a standalone script
import pytest
pytest.skip("Standalone scenario", allow_module_level=True)

from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.config import Config

async def test_reload_system():
    print("Testing reload_system...")
    
    # Load config
    config = Config("mcp_proxy_adapter/examples/full_application/configs/http_basic.json")
    config.load_config()
    
    print(f"Config loaded: {config.get('server.host')}")
    
    # Test reload_system
    try:
        result = await registry.reload_system(config_obj=config)
        print(f"✅ reload_system completed: {result}")
        
        # Check commands
        print(f"Total commands: {result.get('total_commands', 0)}")
        print(f"Built-in commands: {result.get('builtin_commands', 0)}")
        print(f"Custom commands: {result.get('custom_commands', 0)}")
        
        # Test echo command
        echo_cmd = registry.get_command("echo")
        if echo_cmd:
            print(f"✅ Echo command found: {echo_cmd.__class__.__name__}")
        else:
            print("❌ Echo command not found")
            
    except Exception as e:
        print(f"❌ reload_system failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_reload_system())
