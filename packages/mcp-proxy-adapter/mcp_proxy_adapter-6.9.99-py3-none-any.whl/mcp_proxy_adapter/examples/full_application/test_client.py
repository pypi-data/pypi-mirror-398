#!/usr/bin/env python3
"""
Full Application Test Client
Tests all commands and tool descriptions for the full application example.
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient


async def test_builtin_commands(client: JsonRpcClient) -> None:
    """Test built-in commands."""
    print("\n" + "=" * 80)
    print("📋 Testing Built-in Commands")
    print("=" * 80)

    # Test echo
    print("\n1. Testing echo command:")
    try:
        result = await client.echo(message="Hello from test client!")
        print(f"   ✅ Success: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test help
    print("\n2. Testing help command:")
    try:
        result = await client.help()
        commands = result.get("data", {}).get("commands", [])
        print(f"   ✅ Success: Found {len(commands)} commands")
        print(f"   Commands: {', '.join([cmd.get('name', 'unknown') for cmd in commands[:10]])}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test long_task
    print("\n3. Testing long_task command:")
    try:
        result = await client.long_task(seconds=2)
        job_id = result.get("data", {}).get("job_id")
        print(f"   ✅ Success: Job ID = {job_id}")
        
        # Wait a bit and check status
        await asyncio.sleep(1)
        status_result = await client.job_status(job_id=job_id)
        status = status_result.get("data", {}).get("status")
        print(f"   Job status: {status}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


async def test_custom_commands(client: JsonRpcClient) -> None:
    """Test custom commands."""
    print("\n" + "=" * 80)
    print("📋 Testing Custom Commands")
    print("=" * 80)

    # Test custom_echo
    print("\n1. Testing custom_echo command:")
    try:
        result = await client.jsonrpc_call("custom_echo", {
            "message": "Test message",
            "repeat": 3
        })
        result_data = client._extract_result(result)
        print(f"   ✅ Success: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test calculator
    print("\n2. Testing calculator command (add):")
    try:
        result = await client.jsonrpc_call("calculator", {
            "operation": "add",
            "a": 10,
            "b": 5
        })
        result_data = client._extract_result(result)
        print(f"   ✅ Success: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n3. Testing calculator command (multiply):")
    try:
        result = await client.jsonrpc_call("calculator", {
            "operation": "multiply",
            "a": 7,
            "b": 8
        })
        result_data = client._extract_result(result)
        print(f"   ✅ Success: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n4. Testing calculator command (divide):")
    try:
        result = await client.jsonrpc_call("calculator", {
            "operation": "divide",
            "a": 20,
            "b": 4
        })
        result_data = client._extract_result(result)
        print(f"   ✅ Success: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n5. Testing calculator command (error - division by zero):")
    try:
        result = await client.jsonrpc_call("calculator", {
            "operation": "divide",
            "a": 10,
            "b": 0
        })
        result_data = client._extract_result(result)
        print(f"   Result: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ✅ Expected error: {e}")


async def test_dynamic_commands(client: JsonRpcClient) -> None:
    """Test dynamic command loading."""
    print("\n" + "=" * 80)
    print("📋 Testing Dynamic Commands (load)")
    print("=" * 80)

    # Test load command - load a command from file
    print("\n1. Testing load command:")
    try:
        # Try to load a command from the commands directory
        commands_dir = Path(__file__).parent / "commands"
        echo_file = commands_dir / "echo_command.py"
        
        if echo_file.exists():
            result = await client.jsonrpc_call("load", {
                "source": str(echo_file)
            })
            result_data = client._extract_result(result)
            print(f"   ✅ Success: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"   ⚠️  File not found: {echo_file}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


async def test_tool_descriptions(client: JsonRpcClient) -> None:
    """Test getting tool descriptions."""
    print("\n" + "=" * 80)
    print("📋 Testing Tool Descriptions")
    print("=" * 80)

    # Get all commands info using help
    print("\n1. Getting all commands info via help:")
    try:
        result = await client.help()
        commands = result.get("data", {}).get("commands", [])
        print(f"   ✅ Found {len(commands)} commands")
        
        # Show details for each command
        for cmd in commands[:5]:  # Show first 5
            name = cmd.get("name", "unknown")
            descr = cmd.get("description", "No description")
            print(f"\n   Command: {name}")
            print(f"   Description: {descr}")
            if "schema" in cmd:
                print(f"   Schema: {json.dumps(cmd['schema'], indent=4, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test getting methods using get_methods()
    print("\n2. Getting all methods via get_methods():")
    try:
        methods = await client.get_methods()
        print(f"   ✅ Found {len(methods)} methods")
        
        # Show details for custom commands
        for method_name in ["custom_echo", "calculator", "echo", "help"]:
            if method_name in methods:
                method_info = methods[method_name]
                print(f"\n   Method: {method_name}")
                print(f"   Description: {method_info.description}")
                print(f"   Parameters: {len(method_info.parameters)}")
                for param in method_info.parameters:
                    print(f"     - {param.name}: {param.type} (required: {param.required})")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test getting schema for specific commands
    print("\n3. Getting schema for custom_echo via help:")
    try:
        result = await client.help()
        commands = result.get("data", {}).get("commands", [])
        custom_echo = next((c for c in commands if c.get("name") == "custom_echo"), None)
        if custom_echo:
            print(f"   ✅ Found custom_echo:")
            print(f"   {json.dumps(custom_echo, indent=4, ensure_ascii=False)}")
        else:
            print(f"   ⚠️  custom_echo not found in commands list")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n4. Getting schema for calculator via help:")
    try:
        result = await client.help()
        commands = result.get("data", {}).get("commands", [])
        calculator = next((c for c in commands if c.get("name") == "calculator"), None)
        if calculator:
            print(f"   ✅ Found calculator:")
            print(f"   {json.dumps(calculator, indent=4, ensure_ascii=False)}")
        else:
            print(f"   ⚠️  calculator not found in commands list")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test get_method_description for specific methods
    print("\n5. Getting detailed description for custom_echo:")
    try:
        description = await client.get_method_description("custom_echo")
        print(f"   ✅ Description:\n{description}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n6. Getting detailed description for calculator:")
    try:
        description = await client.get_method_description("calculator")
        print(f"   ✅ Description:\n{description}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


async def test_client_methods(client: JsonRpcClient) -> None:
    """Test client convenience methods."""
    print("\n" + "=" * 80)
    print("📋 Testing Client Convenience Methods")
    print("=" * 80)

    # Test echo method
    print("\n1. Testing client.echo() method:")
    try:
        result = await client.echo(message="Hello from convenience method!")
        print(f"   ✅ Success: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test help method
    print("\n2. Testing client.help() method:")
    try:
        result = await client.help()
        commands = result.get("data", {}).get("commands", [])
        print(f"   ✅ Success: Found {len(commands)} commands")
    except Exception as e:
        print(f"   ❌ Error: {e}")


async def main():
    """Main test function."""
    print("🚀 Starting Full Application Test Client")
    print("=" * 80)

    # Create client
    host = "localhost"
    port = 8080
    protocol = "http"

    print(f"\n📡 Connecting to {protocol}://{host}:{port}")

    client = JsonRpcClient(
        protocol=protocol,
        host=host,
        port=port,
    )

    try:
        # Test health endpoint first
        print("\n🔍 Testing health endpoint:")
        try:
            health_result = await client.health()
            print(f"   ✅ Health check passed: {json.dumps(health_result, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"   ⚠️  Health check error: {e}")

        # Run all tests
        await test_builtin_commands(client)
        await test_custom_commands(client)
        await test_dynamic_commands(client)
        await test_tool_descriptions(client)
        await test_client_methods(client)

        print("\n" + "=" * 80)
        print("✅ All tests completed!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

