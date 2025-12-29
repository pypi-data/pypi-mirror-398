#!/usr/bin/env python3
"""
Test for queue_get_job_status auto-detection fix.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

This test verifies that queue_get_job_status correctly auto-detects
the endpoint (embed_job_status vs queue_get_job_status) based on job type.
"""

import asyncio
import sys
import uuid
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_proxy_adapter.client.jsonrpc_client.client import JsonRpcClient


async def test_queue_get_job_status_standard_job_fallback() -> bool:
    """
    Test that standard jobs use queue_get_job_status endpoint (fallback).

    This test verifies that for standard queue jobs (created via queue_add_job),
    the method correctly falls back to queue_get_job_status when embed_job_status
    returns "not found" or doesn't exist.
    """
    print("🧪 Testing queue_get_job_status with standard job (fallback scenario)...")

    # Create a mock client
    client = JsonRpcClient(protocol="http", host="localhost", port=8080)

    # Mock jsonrpc_call to simulate embed_job_status returning "not found"
    # and queue_get_job_status returning success
    standard_job_id = f"standard_job_{uuid.uuid4().hex[:8]}"

    async def mock_jsonrpc_call(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if method == "embed_job_status":
            # Simulate "job not found" response
            return {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32001,
                    "message": f"Job {standard_job_id} not found",
                },
            }
        elif method == "queue_get_job_status":
            # Simulate successful response from standard endpoint
            return {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "success": True,
                    "data": {
                        "job_id": standard_job_id,
                        "status": "pending",
                        "job_type": "command_execution",
                    },
                },
            }
        else:
            raise RuntimeError(f"Unexpected method: {method}")

    client.jsonrpc_call = AsyncMock(side_effect=mock_jsonrpc_call)

    try:
        # Call queue_get_job_status - should fallback to queue_get_job_status
        result = await client.queue_get_job_status(standard_job_id)

        # Verify result
        if not result.get("success"):
            print(f"❌ FAIL: Expected success=True, got: {result}")
            return False

        if result.get("data", {}).get("job_id") != standard_job_id:
            print("❌ FAIL: Job ID mismatch")
            return False

        # Verify that embed_job_status was called first (fallback scenario)
        call_args_list = client.jsonrpc_call.call_args_list
        if len(call_args_list) < 2:
            print(f"❌ FAIL: Expected at least 2 calls, got {len(call_args_list)}")
            return False

        # First call should be embed_job_status
        first_call = call_args_list[0]
        if first_call[0][0] != "embed_job_status":
            print(
                f"❌ FAIL: First call should be embed_job_status, got: {first_call[0][0]}"
            )
            return False

        # Second call should be queue_get_job_status (fallback)
        second_call = call_args_list[1]
        if second_call[0][0] != "queue_get_job_status":
            print(
                f"❌ FAIL: Second call should be queue_get_job_status, got: {second_call[0][0]}"
            )
            return False

        print("✅ PASS: Standard job correctly uses fallback to queue_get_job_status")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_queue_get_job_status_embed_job_direct() -> bool:
    """
    Test that embed_queue jobs use embed_job_status endpoint (direct).

    This test verifies that for embed_queue jobs, the method correctly
    uses embed_job_status endpoint and doesn't fallback.
    """
    print("🧪 Testing queue_get_job_status with embed_queue job (direct scenario)...")

    # Create a mock client
    client = JsonRpcClient(protocol="http", host="localhost", port=8080)

    # Mock jsonrpc_call to simulate embed_job_status returning success
    embed_job_id = f"embed_job_{uuid.uuid4().hex[:8]}"

    async def mock_jsonrpc_call(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if method == "embed_job_status":
            # Simulate successful response from embed_job_status
            return {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "success": True,
                    "data": {
                        "job_id": embed_job_id,
                        "status": "running",
                        "job_type": "embed_queue",
                    },
                },
            }
        elif method == "queue_get_job_status":
            # This should not be called for embed jobs
            raise RuntimeError(
                "queue_get_job_status should not be called for embed jobs"
            )
        else:
            raise RuntimeError(f"Unexpected method: {method}")

    client.jsonrpc_call = AsyncMock(side_effect=mock_jsonrpc_call)

    try:
        # Call queue_get_job_status - should use embed_job_status directly
        result = await client.queue_get_job_status(embed_job_id)

        # Verify result
        if not result.get("success"):
            print(f"❌ FAIL: Expected success=True, got: {result}")
            return False

        if result.get("data", {}).get("job_id") != embed_job_id:
            print("❌ FAIL: Job ID mismatch")
            return False

        # Verify that only embed_job_status was called (no fallback)
        call_args_list = client.jsonrpc_call.call_args_list
        if len(call_args_list) != 1:
            print(f"❌ FAIL: Expected exactly 1 call, got {len(call_args_list)}")
            return False

        # Only call should be embed_job_status
        first_call = call_args_list[0]
        if first_call[0][0] != "embed_job_status":
            print(f"❌ FAIL: Expected embed_job_status, got: {first_call[0][0]}")
            return False

        print("✅ PASS: Embed job correctly uses embed_job_status directly")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_queue_get_job_status_method_not_found_fallback() -> bool:
    """
    Test that when embed_job_status method doesn't exist, it falls back correctly.

    This test verifies that when embed_job_status method is not available
    (method not found error), the method correctly falls back to queue_get_job_status.
    """
    print(
        "🧪 Testing queue_get_job_status with method not found (fallback scenario)..."
    )

    # Create a mock client
    client = JsonRpcClient(protocol="http", host="localhost", port=8080)

    # Mock jsonrpc_call to simulate embed_job_status method not existing
    job_id = f"test_job_{uuid.uuid4().hex[:8]}"

    async def mock_jsonrpc_call(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if method == "embed_job_status":
            # Simulate "method not found" error
            raise RuntimeError("Method embed_job_status not found")
        elif method == "queue_get_job_status":
            # Simulate successful response from standard endpoint
            return {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "success": True,
                    "data": {
                        "job_id": job_id,
                        "status": "completed",
                        "job_type": "command_execution",
                    },
                },
            }
        else:
            raise RuntimeError(f"Unexpected method: {method}")

    client.jsonrpc_call = AsyncMock(side_effect=mock_jsonrpc_call)

    try:
        # Call queue_get_job_status - should fallback to queue_get_job_status
        result = await client.queue_get_job_status(job_id)

        # Verify result
        if not result.get("success"):
            print(f"❌ FAIL: Expected success=True, got: {result}")
            return False

        if result.get("data", {}).get("job_id") != job_id:
            print("❌ FAIL: Job ID mismatch")
            return False

        # Verify that both methods were called (embed_job_status failed, queue_get_job_status succeeded)
        call_args_list = client.jsonrpc_call.call_args_list
        if len(call_args_list) < 2:
            print(f"❌ FAIL: Expected at least 2 calls, got {len(call_args_list)}")
            return False

        # First call should be embed_job_status
        first_call = call_args_list[0]
        if first_call[0][0] != "embed_job_status":
            print(
                f"❌ FAIL: First call should be embed_job_status, got: {first_call[0][0]}"
            )
            return False

        # Second call should be queue_get_job_status (fallback)
        second_call = call_args_list[1]
        if second_call[0][0] != "queue_get_job_status":
            print(
                f"❌ FAIL: Second call should be queue_get_job_status, got: {second_call[0][0]}"
            )
            return False

        print(
            "✅ PASS: Method not found correctly triggers fallback to queue_get_job_status"
        )
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main() -> int:
    """Run all tests."""
    print("=" * 80)
    print("Testing queue_get_job_status auto-detection fix")
    print("=" * 80)
    print()

    results = []

    # Test 1: Standard job fallback
    results.append(await test_queue_get_job_status_standard_job_fallback())
    print()

    # Test 2: Embed job direct
    results.append(await test_queue_get_job_status_embed_job_direct())
    print()

    # Test 3: Method not found fallback
    results.append(await test_queue_get_job_status_method_not_found_fallback())
    print()

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if r)
    total = len(results)

    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result else "❌ FAIL"
        test_names = [
            "Standard job fallback",
            "Embed job direct",
            "Method not found fallback",
        ]
        print(f"{status}: {test_names[i - 1]}")

    print(f"\n🎯 SUMMARY: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
