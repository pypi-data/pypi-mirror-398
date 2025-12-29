#!/usr/bin/env python3
"""
Comprehensive tests for embed_queue and embed_job_status commands.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

This test verifies:
1. embed_queue command creates jobs through queue system
2. embed_job_status command checks status of embed_queue jobs
3. queue_get_job_status auto-detection works correctly with embed_queue jobs
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_proxy_adapter.client.jsonrpc_client.client import JsonRpcClient


async def test_embed_queue_command_creation(client: JsonRpcClient) -> bool:
    """Test that embed_queue command creates a job successfully."""
    print("🧪 Testing embed_queue command - job creation...")

    try:
        # Call embed_queue command
        result = await client.jsonrpc_call(
            "embed_queue",
            {
                "command": "echo",
                "params": {"message": "Test embed_queue"},
            },
        )

        extracted = client._extract_result(result)

        if not extracted.get("success"):
            print(f"❌ FAIL: embed_queue failed: {extracted}")
            return False

        job_id = extracted.get("data", {}).get("job_id")
        if not job_id:
            print(f"❌ FAIL: No job_id in response: {extracted}")
            return False

        command = extracted.get("data", {}).get("command")
        if command != "echo":
            print(f"❌ FAIL: Command mismatch: expected 'echo', got '{command}'")
            return False

        print(f"✅ PASS: embed_queue created job {job_id}")
        return job_id

    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_embed_job_status_command(client: JsonRpcClient, job_id: str) -> bool:
    """Test that embed_job_status command checks job status correctly."""
    print(f"🧪 Testing embed_job_status command for job {job_id}...")

    try:
        # Wait a bit for job to be registered
        await asyncio.sleep(0.5)

        # Call embed_job_status command
        result = await client.jsonrpc_call(
            "embed_job_status",
            {"job_id": job_id},
        )

        extracted = client._extract_result(result)

        if not extracted.get("success"):
            print(f"❌ FAIL: embed_job_status failed: {extracted}")
            return False

        status = extracted.get("data", {}).get("status")
        if not status:
            print(f"❌ FAIL: No status in response: {extracted}")
            return False

        returned_job_id = extracted.get("data", {}).get("job_id")
        if returned_job_id != job_id:
            print(f"❌ FAIL: Job ID mismatch: expected {job_id}, got {returned_job_id}")
            return False

        print(f"✅ PASS: embed_job_status returned status: {status}")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_queue_get_job_status_auto_detection_embed(
    client: JsonRpcClient, job_id: str
) -> bool:
    """
    Test that queue_get_job_status auto-detects embed_job_status endpoint.

    This is the key test - queue_get_job_status should try embed_job_status
    first and succeed for jobs created by embed_queue.
    """
    print(
        f"🧪 Testing queue_get_job_status auto-detection for embed_queue job {job_id}..."
    )

    try:
        # Wait a bit for job to be registered
        await asyncio.sleep(0.5)

        # Call queue_get_job_status - should auto-detect embed_job_status
        status_result = await client.queue_get_job_status(job_id)

        if not status_result.get("success"):
            print(f"❌ FAIL: queue_get_job_status failed: {status_result}")
            return False

        status = status_result.get("data", {}).get("status")
        if not status:
            print(f"❌ FAIL: No status in response: {status_result}")
            return False

        returned_job_id = status_result.get("data", {}).get("job_id")
        if returned_job_id != job_id:
            print(f"❌ FAIL: Job ID mismatch: expected {job_id}, got {returned_job_id}")
            return False

        print(
            f"✅ PASS: queue_get_job_status auto-detected embed_job_status, status: {status}"
        )
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_embed_queue_full_workflow(client: JsonRpcClient) -> bool:
    """Test full workflow: embed_queue -> start job -> check status."""
    print("🧪 Testing full embed_queue workflow...")

    try:
        # Step 1: Create job via embed_queue
        result = await client.jsonrpc_call(
            "embed_queue",
            {
                "command": "echo",
                "params": {"message": "Full workflow test"},
            },
        )

        extracted = client._extract_result(result)
        if not extracted.get("success"):
            print(f"❌ FAIL: embed_queue failed: {extracted}")
            return False

        job_id = extracted.get("data", {}).get("job_id")
        print(f"   ✅ Step 1: Job created: {job_id}")

        # Step 2: Start the job
        await asyncio.sleep(0.5)
        start_result = await client.jsonrpc_call(
            "queue_start_job",
            {"job_id": job_id},
        )

        start_extracted = client._extract_result(start_result)
        if not start_extracted.get("success"):
            print(f"❌ FAIL: queue_start_job failed: {start_extracted}")
            return False

        print("   ✅ Step 2: Job started")

        # Step 3: Wait for job to complete
        max_wait = 10
        waited = 0
        while waited < max_wait:
            status_result = await client.queue_get_job_status(job_id)
            status = status_result.get("data", {}).get("status")
            if status in ("completed", "failed"):
                print(f"   ✅ Step 3: Job completed with status: {status}")
                break
            await asyncio.sleep(0.5)
            waited += 0.5

        if waited >= max_wait:
            print(f"⚠️  WARN: Job did not complete within {max_wait} seconds")
            return False

        # Step 4: Verify result
        final_status = await client.queue_get_job_status(job_id)
        result_data = final_status.get("data", {}).get("result")
        if result_data:
            print(f"   ✅ Step 4: Job result retrieved: {result_data}")
        else:
            print("   ⚠️  WARN: No result data available")

        print("✅ PASS: Full workflow completed successfully")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_embed_queue_vs_standard_queue(client: JsonRpcClient) -> bool:
    """
    Test that embed_queue jobs use embed_job_status,
    while standard queue_add_job jobs use queue_get_job_status.
    """
    print("🧪 Testing embed_queue vs standard queue_add_job...")

    try:
        # Create job via embed_queue
        embed_result = await client.jsonrpc_call(
            "embed_queue",
            {
                "command": "echo",
                "params": {"message": "Embed queue test"},
            },
        )

        embed_extracted = client._extract_result(embed_result)
        embed_job_id = embed_extracted.get("data", {}).get("job_id")
        print(f"   ✅ Created embed_queue job: {embed_job_id}")

        # Create job via standard queue_add_job
        standard_result = await client.jsonrpc_call(
            "queue_add_job",
            {
                "job_type": "command_execution",
                "job_id": f"standard_{uuid.uuid4().hex[:8]}",
                "params": {
                    "command": "echo",
                    "params": {"message": "Standard queue test"},
                },
            },
        )

        standard_extracted = client._extract_result(standard_result)
        standard_job_id = standard_extracted.get("data", {}).get("job_id")
        print(f"   ✅ Created standard queue job: {standard_job_id}")

        # Wait a bit
        await asyncio.sleep(0.5)

        # Both should work with queue_get_job_status (auto-detection)
        embed_status = await client.queue_get_job_status(embed_job_id)
        standard_status = await client.queue_get_job_status(standard_job_id)

        if not embed_status.get("success"):
            print(f"❌ FAIL: embed_queue job status failed: {embed_status}")
            return False

        if not standard_status.get("success"):
            print(f"❌ FAIL: standard queue job status failed: {standard_status}")
            return False

        print(
            f"   ✅ embed_queue job status: {embed_status.get('data', {}).get('status')}"
        )
        print(
            f"   ✅ standard queue job status: {standard_status.get('data', {}).get('status')}"
        )

        print("✅ PASS: Both job types work with queue_get_job_status")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main() -> int:
    """Run all embed_queue tests."""
    print("=" * 80)
    print("Testing embed_queue and embed_job_status commands")
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
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to server at {server_url}: {e}")
        print("   Please start the server first:")
        print(
            "   python mcp_proxy_adapter/examples/full_application/main.py --config <config> --port 8080"
        )
        return 1

    # Create client
    client = JsonRpcClient(protocol="http", host="localhost", port=8080)

    results = []

    try:
        # Test 1: embed_queue command creation
        job_id = await test_embed_queue_command_creation(client)
        if not job_id:
            print("❌ Test 1 failed")
            return 1
        results.append(("embed_queue creation", True))

        # Test 2: embed_job_status command
        if not await test_embed_job_status_command(client, job_id):
            print("❌ Test 2 failed")
            return 1
        results.append(("embed_job_status", True))

        # Test 3: queue_get_job_status auto-detection
        if not await test_queue_get_job_status_auto_detection_embed(client, job_id):
            print("❌ Test 3 failed")
            return 1
        results.append(("queue_get_job_status auto-detection", True))

        # Test 4: Full workflow
        if not await test_embed_queue_full_workflow(client):
            print("❌ Test 4 failed")
            return 1
        results.append(("full workflow", True))

        # Test 5: embed_queue vs standard queue
        if not await test_embed_queue_vs_standard_queue(client):
            print("❌ Test 5 failed")
            return 1
        results.append(("embed_queue vs standard queue", True))

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
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
