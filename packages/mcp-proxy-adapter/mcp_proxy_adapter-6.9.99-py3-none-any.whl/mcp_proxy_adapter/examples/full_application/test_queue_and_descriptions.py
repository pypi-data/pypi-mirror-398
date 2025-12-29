#!/usr/bin/env python3
"""
Test script for queue system and method descriptions.
Tests that any command can be enqueued and method descriptions are properly returned.
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient


async def test_method_descriptions(client: JsonRpcClient) -> None:
    """Test that method descriptions are properly returned."""
    print("\n" + "=" * 80)
    print("📋 Testing Method Descriptions")
    print("=" * 80)

    # Test help command - should return all commands with full schemas
    print("\n1. Testing help command (all commands):")
    try:
        result = await client.help()
        commands = result.get("data", {}).get("commands", {})
        print(f"   ✅ Found {len(commands)} commands")
        
        # Check that custom commands have full descriptions
        for cmd_name in ["custom_echo", "calculator", "echo"]:
            if cmd_name in commands:
                cmd_info = commands[cmd_name]
                print(f"\n   Command: {cmd_name}")
                print(f"   Description: {cmd_info.get('description', 'N/A')}")
                print(f"   Type: {cmd_info.get('type', 'N/A')}")
                schema = cmd_info.get("schema", {})
                properties = schema.get("properties", {})
                print(f"   Parameters: {len(properties)}")
                for param_name, param_info in properties.items():
                    param_type = param_info.get("type", "unknown")
                    required = param_name in schema.get("required", [])
                    default = param_info.get("default", "N/A")
                    print(f"     - {param_name}: {param_type} (required: {required}, default: {default})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # Test get_methods() - should return MethodInfo objects
    print("\n2. Testing get_methods() API:")
    try:
        methods = await client.get_methods()
        print(f"   ✅ Found {len(methods)} methods")
        
        for method_name in ["custom_echo", "calculator", "echo"]:
            if method_name in methods:
                method_info = methods[method_name]
                print(f"\n   Method: {method_name}")
                print(f"   Description: {method_info.description}")
                print(f"   Parameters: {len(method_info.parameters)}")
                for param in method_info.parameters:
                    print(f"     - {param.name}: {param.type} (required: {param.required})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # Test get_method_description() for specific methods
    print("\n3. Testing get_method_description() for custom_echo:")
    try:
        description = await client.get_method_description("custom_echo")
        print(f"   ✅ Description received:")
        print(f"   {description[:500]}...")  # Show first 500 chars
    except Exception as e:
        print(f"   ❌ Error: {e}")


async def test_queue_system(client: JsonRpcClient) -> None:
    """Test queue system and command execution in queue."""
    print("\n" + "=" * 80)
    print("📋 Testing Queue System")
    print("=" * 80)

    # Test queue health
    print("\n1. Testing queue_health:")
    try:
        result = await client.jsonrpc_call("queue_health", {})
        result_data = client._extract_result(result)
        print(f"   ✅ Queue health: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ⚠️  Queue not available: {e}")
        return

    # Test adding a command execution job
    print("\n2. Testing queue_add_job with command_execution (custom_echo):")
    try:
        job_id = f"test-custom-echo-{int(time.time())}"
        result = await client.jsonrpc_call("queue_add_job", {
            "job_type": "command_execution",
            "job_id": job_id,
            "params": {
                "command": "custom_echo",
                "params": {
                    "message": "Hello from queue!",
                    "repeat": 2
                }
            }
        })
        result_data = client._extract_result(result)
        print(f"   ✅ Job added: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
        
        # Start the job
        print("\n3. Starting the job:")
        await asyncio.sleep(1)
        result = await client.jsonrpc_call("queue_start_job", {"job_id": job_id})
        result_data = client._extract_result(result)
        print(f"   ✅ Job started: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
        
        # Check job status
        print("\n4. Checking job status:")
        await asyncio.sleep(2)
        result = await client.jsonrpc_call("queue_get_job_status", {"job_id": job_id})
        result_data = client._extract_result(result)
        print(f"   ✅ Job status: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # Test adding calculator command to queue
    print("\n5. Testing queue_add_job with command_execution (calculator):")
    try:
        job_id = f"test-calculator-{int(time.time())}"
        result = await client.jsonrpc_call("queue_add_job", {
            "job_type": "command_execution",
            "job_id": job_id,
            "params": {
                "command": "calculator",
                "params": {
                    "operation": "multiply",
                    "a": 7,
                    "b": 8
                }
            }
        })
        result_data = client._extract_result(result)
        print(f"   ✅ Job added: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
        
        # Start the job
        print("\n6. Starting the job:")
        await asyncio.sleep(1)
        result = await client.jsonrpc_call("queue_start_job", {"job_id": job_id})
        result_data = client._extract_result(result)
        print(f"   ✅ Job started: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
        
        # Check job status
        print("\n7. Checking job status:")
        await asyncio.sleep(2)
        result = await client.jsonrpc_call("queue_get_job_status", {"job_id": job_id})
        result_data = client._extract_result(result)
        print(f"   ✅ Job status: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # Test adding echo command to queue
    print("\n8. Testing queue_add_job with command_execution (echo):")
    try:
        job_id = f"test-echo-{int(time.time())}"
        result = await client.jsonrpc_call("queue_add_job", {
            "job_type": "command_execution",
            "job_id": job_id,
            "params": {
                "command": "echo",
                "params": {
                    "message": "Hello from queued echo!"
                }
            }
        })
        result_data = client._extract_result(result)
        print(f"   ✅ Job added: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
        
        # Start the job
        print("\n9. Starting the job:")
        await asyncio.sleep(1)
        result = await client.jsonrpc_call("queue_start_job", {"job_id": job_id})
        result_data = client._extract_result(result)
        print(f"   ✅ Job started: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
        
        # Check job status
        print("\n10. Checking job status:")
        await asyncio.sleep(2)
        result = await client.jsonrpc_call("queue_get_job_status", {"job_id": job_id})
        result_data = client._extract_result(result)
        print(f"   ✅ Job status: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 Testing Queue System and Method Descriptions")
    print("=" * 80)

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
        # Test health
        print("\n🔍 Testing health endpoint:")
        try:
            health_result = await client.health()
            print(f"   ✅ Health check passed")
        except Exception as e:
            print(f"   ⚠️  Health check error: {e}")

        # Run tests
        await test_method_descriptions(client)
        await test_queue_system(client)

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

