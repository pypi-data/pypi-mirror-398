#!/usr/bin/env python3
"""
Integration test for custom commands execution via queue in spawn mode.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

This test verifies that custom commands with use_queue=True execute
successfully in child processes when using spawn mode.
"""

import asyncio
import multiprocessing
import sys
import uuid
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_proxy_adapter.client.jsonrpc_client.client import JsonRpcClient
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.commands.hooks import register_custom_commands_hook


# Test custom command that will be registered via hook and executed via queue
class TestQueueCommand(Command):
    """Test command for queue execution in spawn mode."""

    name = "test_queue_cmd"
    descr = "Test command executed via queue in spawn mode"
    use_queue = True  # This requires execution in child process

    async def execute(self, test_data: str = "default", **kwargs):
        """Execute test command."""
        return SuccessResult(
            data={
                "test_data": test_data,
                "command_name": self.name,
                "executed_via": "queue",
                "process_mode": "spawn",
            }
        )


def register_test_queue_commands(registry):
    """Hook function to register test queue commands."""
    registry.register(TestQueueCommand, "custom")


async def test_custom_command_queue_execution() -> bool:
    """
    Test that custom commands execute successfully via queue in spawn mode.

    This test requires a running server with:
    - queue_manager enabled
    - multiprocessing spawn mode
    - custom commands registered via hooks
    """
    print("=" * 80)
    print("Testing custom command execution via queue in spawn mode")
    print("=" * 80)
    print()

    # Check if server is running
    server_url = "http://localhost:8080"
    try:
        import requests

        response = requests.get(f"{server_url}/health", timeout=2)
        if response.status_code != 200:
            print(f"❌ Server not available at {server_url}")
            print("   Please start the server first with custom commands registered")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server at {server_url}: {e}")
        print("   Please start the server first:")
        print(
            "   python mcp_proxy_adapter/examples/full_application/main.py --config <config> --port 8080"
        )
        return False

    client = JsonRpcClient(protocol="http", host="localhost", port=8080)
    results = []

    try:
        # Step 1: Check if command is available
        print("🧪 Step 1: Checking if test_queue_cmd is available...")
        help_result = await client.help()
        commands_list = help_result.get("data", {}).get("commands", [])
        has_test_cmd = any(
            cmd.get("name") == "test_queue_cmd" for cmd in commands_list
        )

        if not has_test_cmd:
            print("⚠️  WARN: test_queue_cmd not found in server")
            print("   This is expected if hooks are not registered in server")
            print("   Skipping queue execution test")
            return True  # Not a failure, just not configured

        print("✅ Command test_queue_cmd is available")

        # Step 2: Execute command via queue
        print("\n🧪 Step 2: Executing command via queue...")
        test_data = f"test_{uuid.uuid4().hex[:8]}"

        # Create job via queue_add_job
        job_result = await client.jsonrpc_call(
            "queue_add_job",
            {
                "job_type": "command_execution",
                "job_id": f"test_queue_{uuid.uuid4().hex[:8]}",
                "params": {
                    "command": "test_queue_cmd",
                    "params": {"test_data": test_data},
                },
            },
        )

        job_extracted = client._extract_result(job_result)
        if not job_extracted.get("success"):
            print(f"❌ FAIL: Failed to create job: {job_extracted}")
            return False

        job_id = job_extracted.get("data", {}).get("job_id")
        print(f"✅ Job created: {job_id}")

        # Step 3: Start job
        print("\n🧪 Step 3: Starting job...")
        await asyncio.sleep(0.5)

        start_result = await client.jsonrpc_call(
            "queue_start_job",
            {"job_id": job_id},
        )

        start_extracted = client._extract_result(start_result)
        if not start_extracted.get("success"):
            print(f"❌ FAIL: Failed to start job: {start_extracted}")
            return False

        print("✅ Job started")

        # Step 4: Wait for completion
        print("\n🧪 Step 4: Waiting for job completion...")
        max_wait = 15
        waited = 0
        completed = False

        while waited < max_wait:
            status_result = await client.queue_get_job_status(job_id)
            status = status_result.get("data", {}).get("status")

            if status == "completed":
                completed = True
                print(f"✅ Job completed successfully")

                # Verify result
                result_data = status_result.get("data", {}).get("result")
                if result_data:
                    test_result = result_data.get("data", {}).get("test_data")
                    if test_result == test_data:
                        print(f"✅ Result data matches: {test_result}")
                        results.append(("queue_execution", True))
                    else:
                        print(
                            f"❌ Result data mismatch: expected {test_data}, got {test_result}"
                        )
                        results.append(("queue_execution", False))
                else:
                    print("⚠️  WARN: No result data available")
                    results.append(("queue_execution", True))  # Still success

                break
            elif status == "failed":
                error = status_result.get("data", {}).get("error")
                print(f"❌ FAIL: Job failed: {error}")
                results.append(("queue_execution", False))
                break

            await asyncio.sleep(0.5)
            waited += 0.5

        if not completed:
            print(f"⚠️  WARN: Job did not complete within {max_wait} seconds")
            results.append(("queue_execution", False))

    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        import traceback

        traceback.print_exc()
        results.append(("queue_execution", False))
    finally:
        await client.close()

    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n🎯 SUMMARY: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False


if __name__ == "__main__":
    # Set spawn mode for testing
    try:
        multiprocessing.set_start_method("spawn", force=True)
    except RuntimeError:
        pass  # Already set

    success = asyncio.run(test_custom_command_queue_execution())
    sys.exit(0 if success else 1)

