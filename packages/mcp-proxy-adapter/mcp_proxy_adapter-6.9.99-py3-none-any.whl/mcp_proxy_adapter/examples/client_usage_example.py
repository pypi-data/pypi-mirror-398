#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Example of using JsonRpcClient library for MCP Proxy Adapter.

This example demonstrates:
- Basic client initialization
- Using built-in commands (echo, help, long_task, job_status)
- Using queue management commands (queue_add_job, queue_start_job, etc.)
- Error handling

Usage:
    # Make sure server is running, then:
    python -m mcp_proxy_adapter.examples.client_usage_example
"""

from __future__ import annotations

import json
import time
import uuid

from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient


def example_builtin_commands(client: JsonRpcClient) -> None:
    """Example of using built-in commands."""
    print("\n" + "=" * 60)
    print("📋 Example: Built-in Commands")
    print("=" * 60)

    # Echo command
    print("\n1. Echo command:")
    result = client.echo(message="Hello from client!")
    print(f"   Result: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # Help command
    print("\n2. Help command:")
    result = client.help()
    print(f"   Commands available: {len(result.get('data', {}).get('commands', []))}")

    # Long task
    print("\n3. Starting long task (5 seconds):")
    result = client.long_task(seconds=5)
    job_id = result.get("data", {}).get("job_id")
    print(f"   Job ID: {job_id}")

    # Check job status
    print("\n4. Checking job status:")
    time.sleep(2)
    result = client.job_status(job_id=job_id)
    print(f"   Status: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # Wait for completion
    print("\n5. Waiting for task completion...")
    time.sleep(4)
    result = client.job_status(job_id=job_id)
    status = result.get("data", {}).get("status")
    print(f"   Final status: {status}")


def example_queue_commands(client: JsonRpcClient) -> None:
    """Example of using queue management commands."""
    print("\n" + "=" * 60)
    print("📋 Example: Queue Management Commands")
    print("=" * 60)

    job_id = f"example-{uuid.uuid4().hex[:8]}"

    # Queue health
    print("\n1. Queue health:")
    try:
        result = client.queue_health()
        print(f"   Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except RuntimeError as e:
        print(f"   ⚠️  Queue commands not available: {e}")
        return

    # Add job
    print(f"\n2. Adding job (job_id={job_id}):")
    result = client.queue_add_job(
        job_type="long_running",
        job_id=job_id,
        params={"duration": 5, "task_type": "example_task"},
    )
    print(f"   Result: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # Get job status (should be pending)
    print("\n3. Getting job status (should be pending):")
    result = client.queue_get_job_status(job_id=job_id)
    print(f"   Status: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # List jobs
    print("\n4. Listing all jobs:")
    result = client.queue_list_jobs()
    print(f"   Jobs count: {len(result.get('data', {}).get('jobs', []))}")

    # Start job
    print("\n5. Starting job:")
    result = client.queue_start_job(job_id=job_id)
    print(f"   Result: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # Check status (should be running)
    print("\n6. Checking status (should be running):")
    time.sleep(1)
    result = client.queue_get_job_status(job_id=job_id)
    print(f"   Status: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # Wait for completion
    print("\n7. Waiting for job completion...")
    time.sleep(6)
    result = client.queue_get_job_status(job_id=job_id)
    status = result.get("data", {}).get("status")
    print(f"   Final status: {status}")

    # Delete job
    print("\n8. Deleting job:")
    result = client.queue_delete_job(job_id=job_id)
    print(f"   Result: {json.dumps(result, ensure_ascii=False, indent=2)}")


def main() -> None:
    """Main example function."""
    print("🚀 JsonRpcClient Usage Example")
    print("=" * 60)

    # Initialize client (adjust protocol, host, port as needed)
    client = JsonRpcClient(
        protocol="http",
        host="127.0.0.1",
        port=8080,
    )

    # Check server health
    print("\n📡 Checking server health...")
    try:
        health = client.health()
        print(f"✅ Server is healthy: {json.dumps(health, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Server is not available: {e}")
        print("   Make sure the server is running on http://127.0.0.1:8080")
        return

    # Run examples
    try:
        example_builtin_commands(client)
    except Exception as e:
        print(f"\n❌ Error in built-in commands example: {e}")

    try:
        example_queue_commands(client)
    except Exception as e:
        print(f"\n❌ Error in queue commands example: {e}")

    print("\n" + "=" * 60)
    print("✅ Examples completed")
    print("=" * 60)


if __name__ == "__main__":
    main()

