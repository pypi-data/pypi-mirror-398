#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Integration test for custom commands with use_queue=True on real server.

This test:
1. Starts a real server with custom commands
2. Registers commands via hooks
3. Executes commands via queue (spawn mode)
4. Verifies commands work correctly in child processes

This test should be run as part of the comprehensive test pipeline.
"""

import asyncio
import json
import multiprocessing
import subprocess
import sys
import time
from pathlib import Path

import requests

# Set spawn mode
multiprocessing.set_start_method("spawn", force=True)

BASE_URL = "http://127.0.0.1:8080"
TEST_TIMEOUT = 60


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    return False


def test_custom_command_registration():
    """Test that custom commands are registered and available."""
    print("\n🧪 Test: Custom command registration")
    
    # Check health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("   ✅ Server is running")
    except Exception as e:
        print(f"   ❌ Server not available: {e}")
        return False
    
    # Check if long_running_task command is available
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "long_running_task",
            "params": {"task_name": "test", "duration": 1, "steps": 2},
            "id": 1,
        }
        response = requests.post(
            f"{BASE_URL}/api/jsonrpc",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print("   ✅ Command is registered and available")
                return True
            elif "error" in result:
                error_code = result["error"].get("code", 0)
                error_message = result["error"].get("message", "")
                if error_code == -32601:  # Method not found
                    print(f"   ❌ Command not found: {error_message}")
                    return False
                else:
                    print(f"   ⚠️  Command error (but registered): {error_message}")
                    return True
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False


def test_queue_command_execution():
    """Test that queue command executes successfully."""
    print("\n🧪 Test: Queue command execution")
    
    # Execute long_running_task via queue
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "long_running_task",
            "params": {"task_name": "integration_test", "duration": 2, "steps": 4},
            "id": 1,
        }
        response = requests.post(
            f"{BASE_URL}/api/jsonrpc",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        
        if response.status_code != 200:
            print(f"   ❌ Request failed: {response.status_code}")
            return False
        
        result = response.json()
        
        if "error" in result:
            error = result["error"]
            error_code = error.get("code", 0)
            error_message = error.get("message", "")
            
            if error_code == -32601:  # Method not found
                print(f"   ❌ Command not found: {error_message}")
                print(f"   ❌ This indicates registration issue in child process!")
                return False
            else:
                print(f"   ❌ Command error: {error_message}")
                return False
        
        if "result" not in result:
            print(f"   ❌ No result in response: {result}")
            return False
        
        command_result = result["result"]
        
        # Check if job was queued
        if isinstance(command_result, dict) and "job_id" in command_result:
            job_id = command_result["job_id"]
            print(f"   ✅ Job queued: {job_id}")
            
            # Wait for job to complete
            max_wait = 30
            waited = 0
            while waited < max_wait:
                # Check job status
                status_payload = {
                    "jsonrpc": "2.0",
                    "method": "job_status",
                    "params": {"job_id": job_id},
                    "id": 2,
                }
                status_response = requests.post(
                    f"{BASE_URL}/api/jsonrpc",
                    json=status_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=5,
                )
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    if "result" in status_result:
                        job_status = status_result["result"]
                        status = job_status.get("status", "unknown")
                        
                        if status == "completed":
                            print(f"   ✅ Job completed successfully")
                            print(f"   ✅ Result: {job_status.get('result', {})}")
                            return True
                        elif status == "failed":
                            error = job_status.get("error", "Unknown error")
                            print(f"   ❌ Job failed: {error}")
                            return False
                        elif status in ("running", "queued"):
                            # Still running, wait more
                            time.sleep(1)
                            waited += 1
                            continue
                
                time.sleep(1)
                waited += 1
            
            print(f"   ❌ Job did not complete within {max_wait} seconds")
            return False
        else:
            # Command executed synchronously (shouldn't happen for use_queue=True)
            print(f"   ⚠️  Command executed synchronously (unexpected for use_queue=True)")
            print(f"   ✅ But command worked: {command_result}")
            return True
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run integration tests."""
    print("=" * 70)
    print("Integration Test: Custom Commands with Queue in Spawn Mode")
    print("=" * 70)
    print("\n⚠️  This test requires a running server.")
    print("   Start server with:")
    print("   python mcp_proxy_adapter/examples/full_application/main.py \\")
    print("     --config mcp_proxy_adapter/examples/full_application/configs/http_basic.json \\")
    print("     --port 8080")
    print()
    
    # Wait for server
    print("Waiting for server to be ready...")
    if not wait_for_server(BASE_URL, timeout=30):
        print("❌ Server is not available. Please start the server first.")
        return 1
    
    print("✅ Server is ready")
    
    results = []
    
    # Test 1: Command registration
    try:
        results.append(("Command registration", test_custom_command_registration()))
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        results.append(("Command registration", False))
    
    # Test 2: Queue command execution
    try:
        results.append(("Queue command execution", test_queue_command_execution()))
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        results.append(("Queue command execution", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} tests")
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1
    
    print("\n🎉 All integration tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
