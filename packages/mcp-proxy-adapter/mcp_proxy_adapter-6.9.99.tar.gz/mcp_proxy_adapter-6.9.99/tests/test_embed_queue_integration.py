#!/usr/bin/env python3
"""
Integration test for embed_queue command with real server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

This test requires a running server. It tests:
1. embed_queue command creates jobs
2. embed_job_status checks job status
3. queue_get_job_status auto-detection works
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_proxy_adapter.client.jsonrpc_client.client import JsonRpcClient


async def test_embed_queue_integration() -> bool:
    """Test embed_queue command integration with real server."""
    print("=" * 80)
    print("Testing embed_queue command integration")
    print("=" * 80)
    print()

    # Check if server is running
    server_url = "http://localhost:8080"
    try:
        import requests

        response = requests.get(f"{server_url}/health", timeout=2)
        if response.status_code != 200:
            print(f"❌ Server not available at {server_url}")
            print("   Please start the server first:")
            print(
                "   python mcp_proxy_adapter/examples/full_application/main.py --config <config> --port 8080"
            )
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
        # Test 1: Check if embed_queue command is available
        print("🧪 Test 1: Checking if embed_queue command is available...")
        help_result = await client.help()
        commands_list = help_result.get("data", {}).get("commands", [])
        has_embed_queue = any(cmd.get("name") == "embed_queue" for cmd in commands_list)

        if not has_embed_queue:
            print("❌ FAIL: embed_queue command not found in server")
            print("   Available commands:", [c.get("name") for c in commands_list[:10]])
            return False

        print("✅ PASS: embed_queue command is available")
        results.append(("command_availability", True))

        # Test 2: Create job via embed_queue
        print("\n🧪 Test 2: Creating job via embed_queue...")
        embed_result = await client.jsonrpc_call(
            "embed_queue",
            {
                "command": "echo",
                "params": {"message": "Integration test message"},
            },
        )

        embed_extracted = client._extract_result(embed_result)
        if not embed_extracted.get("success"):
            print(f"❌ FAIL: embed_queue failed: {embed_extracted}")
            return False

        job_id = embed_extracted.get("data", {}).get("job_id")
        if not job_id:
            print(f"❌ FAIL: No job_id in response: {embed_extracted}")
            return False

        print(f"✅ PASS: Job created with ID: {job_id}")
        results.append(("embed_queue_creation", True))

        # Test 3: Check status via embed_job_status
        print("\n🧪 Test 3: Checking status via embed_job_status...")
        await asyncio.sleep(0.5)  # Wait for job to be registered

        embed_status_result = await client.jsonrpc_call(
            "embed_job_status",
            {"job_id": job_id},
        )

        embed_status_extracted = client._extract_result(embed_status_result)
        if not embed_status_extracted.get("success"):
            print(f"❌ FAIL: embed_job_status failed: {embed_status_extracted}")
            return False

        status = embed_status_extracted.get("data", {}).get("status")
        print(f"✅ PASS: embed_job_status returned status: {status}")
        results.append(("embed_job_status", True))

        # Test 4: Check status via queue_get_job_status (auto-detection)
        print("\n🧪 Test 4: Testing queue_get_job_status auto-detection...")
        auto_status_result = await client.queue_get_job_status(job_id)

        if not auto_status_result.get("success"):
            print(f"❌ FAIL: queue_get_job_status failed: {auto_status_result}")
            return False

        auto_status = auto_status_result.get("data", {}).get("status")
        print(
            f"✅ PASS: queue_get_job_status auto-detected embed_job_status, status: {auto_status}"
        )
        results.append(("queue_get_job_status_auto_detection", True))

        # Test 5: Start job and wait for completion
        print("\n🧪 Test 5: Starting job and waiting for completion...")
        start_result = await client.jsonrpc_call(
            "queue_start_job",
            {"job_id": job_id},
        )

        start_extracted = client._extract_result(start_result)
        if not start_extracted.get("success"):
            print(f"⚠️  WARN: queue_start_job failed: {start_extracted}")
        else:
            print("✅ Job started")

        # Wait for completion
        max_wait = 10
        waited = 0
        while waited < max_wait:
            status_result = await client.queue_get_job_status(job_id)
            status = status_result.get("data", {}).get("status")
            if status in ("completed", "failed"):
                print(f"✅ Job completed with status: {status}")
                results.append(("job_completion", True))
                break
            await asyncio.sleep(0.5)
            waited += 0.5

        if waited >= max_wait:
            print(f"⚠️  WARN: Job did not complete within {max_wait} seconds")
            results.append(("job_completion", False))

    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        import traceback

        traceback.print_exc()
        return False
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
    success = asyncio.run(test_embed_queue_integration())
    sys.exit(0 if success else 1)
