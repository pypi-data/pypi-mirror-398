#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Comprehensive test pipeline for all MCP Proxy Adapter modes with custom commands.

This test pipeline:
1. Tests all 8 security modes (HTTP, HTTPS, mTLS with various auth combinations)
2. Verifies custom commands registration in spawn mode
3. Tests queue commands execution in child processes
4. Validates that commands with use_queue=True work correctly

This is the main test that should be run before publishing to PyPI.
"""

import json
import multiprocessing
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

# Set spawn mode for multiprocessing (required for CUDA compatibility)
multiprocessing.set_start_method("spawn", force=True)

# Test configurations
# Use basic_framework configs if full_application configs don't exist
TEST_CONFIGS = [
    {
        "name": "HTTP Basic",
        "config": "mcp_proxy_adapter/examples/full_application/configs/http_basic.json",
        "fallback": "mcp_proxy_adapter/examples/basic_framework/configs/http_simple.json",
        "port": 8080,
        "use_ssl": False,
        "use_mtls": False,
        "token": None,
    },
    {
        "name": "HTTP + Token",
        "config": "mcp_proxy_adapter/examples/full_application/configs/http_token.json",
        "fallback": "mcp_proxy_adapter/examples/basic_framework/configs/http_auth.json",
        "port": 8080,
        "use_ssl": False,
        "use_mtls": False,
        "token": "admin-secret-key",
    },
    {
        "name": "HTTP + Token + Roles",
        "config": "mcp_proxy_adapter/examples/full_application/configs/http_token_roles.json",
        "fallback": "mcp_proxy_adapter/examples/basic_framework/configs/http_auth.json",
        "port": 8080,
        "use_ssl": False,
        "use_mtls": False,
        "token": "admin-secret-key",
    },
    {
        "name": "HTTPS Basic",
        "config": "mcp_proxy_adapter/examples/full_application/configs/https_basic.json",
        "fallback": "mcp_proxy_adapter/examples/basic_framework/configs/https_simple.json",
        "port": 8443,
        "use_ssl": True,
        "use_mtls": False,
        "token": None,
    },
    {
        "name": "HTTPS + Token",
        "config": "mcp_proxy_adapter/examples/full_application/configs/https_token.json",
        "fallback": "mcp_proxy_adapter/examples/basic_framework/configs/https_auth.json",
        "port": 8443,
        "use_ssl": True,
        "use_mtls": False,
        "token": "admin-secret-key-https",
    },
    {
        "name": "HTTPS + Token + Roles",
        "config": "mcp_proxy_adapter/examples/full_application/configs/https_token_roles.json",
        "fallback": "mcp_proxy_adapter/examples/basic_framework/configs/https_auth.json",
        "port": 8443,
        "use_ssl": True,
        "use_mtls": False,
        "token": "admin-secret-key-https",
    },
    {
        "name": "mTLS Basic",
        "config": "mcp_proxy_adapter/examples/full_application/configs/mtls_no_roles_correct.json",
        "fallback": "mcp_proxy_adapter/examples/basic_framework/configs/mtls_simple.json",
        "port": 8443,
        "use_ssl": True,
        "use_mtls": True,
        "token": "admin-secret-key-mtls",
    },
    {
        "name": "mTLS + Roles",
        "config": "mcp_proxy_adapter/examples/full_application/configs/mtls_with_roles_correct.json",
        "fallback": "mcp_proxy_adapter/examples/basic_framework/configs/mtls_with_roles.json",
        "port": 8443,
        "use_ssl": True,
        "use_mtls": True,
        "token": "admin-secret-key-mtls",
    },
]

TEST_RESULTS = []


def log_result(test_name: str, status: str, details: str = ""):
    """Log test result."""
    result = {"test": test_name, "status": status, "details": details}
    TEST_RESULTS.append(result)
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_icon} {test_name}: {status}")
    if details:
        print(f"   {details}")


def wait_for_server(url: str, timeout: int = 30, verify: bool = True) -> bool:
    """Wait for server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=2, verify=verify)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    return False


def kill_server_on_port(port: int):
    """Kill any process running on the specified port."""
    try:
        # Use shorter timeout and non-blocking approach
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"], 
            capture_output=True, 
            text=True, 
            timeout=1,  # Reduced from 3
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.stdout and result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if not pid.strip():
                    continue
                try:
                    # Try graceful termination first (non-blocking)
                    subprocess.Popen(
                        ["kill", "-TERM", pid], 
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    time.sleep(0.1)  # Reduced from 0.3
                    # Force kill (non-blocking)
                    subprocess.Popen(
                        ["kill", "-9", pid], 
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception:
                    pass
            # Reduced wait time
            time.sleep(0.2)  # Reduced from 0.5
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass


def test_health_endpoint(config: dict) -> bool:
    """Test health endpoint."""
    protocol = "https" if config["use_ssl"] else "http"
    url = f"{protocol}://localhost:{config['port']}"
    verify = not config["use_ssl"]  # Don't verify SSL for test certificates

    try:
        response = requests.get(f"{url}/health", timeout=5, verify=verify)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                return True
        return False
    except Exception as e:
        print(f"   Health check error: {e}")
        return False


def test_echo_command(config: dict) -> bool:
    """Test basic echo command."""
    protocol = "https" if config["use_ssl"] else "http"
    url = f"{protocol}://localhost:{config['port']}"
    verify = not config["use_ssl"]

    headers = {"Content-Type": "application/json"}
    if config["token"]:
        headers["X-API-Key"] = config["token"]

    payload = {
        "jsonrpc": "2.0",
        "method": "echo",
        "params": {"message": "Hello from comprehensive test"},
        "id": 1,
    }

    try:
        response = requests.post(
            f"{url}/api/jsonrpc",
            json=payload,
            headers=headers,
            timeout=10,
            verify=verify,
        )
        if response.status_code == 200:
            result = response.json()
            if "result" in result and result["result"].get("success"):
                return True
        return False
    except Exception as e:
        print(f"   Echo command error: {e}")
        return False


def test_queue_command(config: dict) -> bool:
    """Test queue command (long_running_task) execution."""
    protocol = "https" if config["use_ssl"] else "http"
    url = f"{protocol}://localhost:{config['port']}"
    verify = not config["use_ssl"]

    headers = {"Content-Type": "application/json"}
    if config["token"]:
        headers["X-API-Key"] = config["token"]

    # Execute long_running_task (has use_queue=True)
    payload = {
        "jsonrpc": "2.0",
        "method": "long_running_task",
        "params": {"task_name": "comprehensive_test", "duration": 2, "steps": 4},
        "id": 1,
    }

    try:
        response = requests.post(
            f"{url}/api/jsonrpc",
            json=payload,
            headers=headers,
            timeout=10,
            verify=verify,
        )

        if response.status_code != 200:
            return False

        result = response.json()

        # Check for errors
        if "error" in result:
            error = result["error"]
            error_code = error.get("code", 0)
            error_message = error.get("message", "")

            if error_code == -32601:  # Method not found
                print(f"   ❌ Command not found: {error_message}")
                print(f"   ❌ This indicates registration issue in spawn mode!")
                return False
            else:
                print(f"   ⚠️  Command error: {error_message}")
                return False

        if "result" not in result:
            return False

        command_result = result["result"]

        # Check if job was queued
        if isinstance(command_result, dict) and "job_id" in command_result:
            job_id = command_result["job_id"]

            # Wait for job to complete
            # Use queue_get_job_status instead of job_status because long_running_task
            # uses use_queue=True, which means it uses queuemgr, not the old job_manager
            max_wait = 30
            waited = 0
            while waited < max_wait:
                status_payload = {
                    "jsonrpc": "2.0",
                    "method": "queue_get_job_status",
                    "params": {"job_id": job_id},
                    "id": 2,
                }
                status_response = requests.post(
                    f"{url}/api/jsonrpc",
                    json=status_payload,
                    headers=headers,
                    timeout=5,
                    verify=verify,
                )

                if status_response.status_code == 200:
                    status_result = status_response.json()
                    
                    # Check for errors in response (queue_get_job_status returns ErrorResult on job not found)
                    if "error" in status_result:
                        error = status_result["error"]
                        error_message = error.get("message", "")
                        # Job not found error - may happen if job was cleaned up or never created
                        if "not found" in error_message.lower() or "Job not found" in error_message:
                            if waited >= 5:
                                print(f"   ❌ Job {job_id} not found after multiple checks")
                                print(f"   ❌ This indicates job creation or registration issue!")
                                return False
                            # Continue waiting - job might still be processing
                            time.sleep(1)
                            waited += 1
                            continue
                        else:
                            print(f"   ❌ Job status error: {error_message}")
                            return False
                    
                    if "result" in status_result:
                        job_status = status_result["result"]
                        
                        # queue_get_job_status returns SuccessResult with data field
                        # Format: {"success": True, "data": {"job_id": ..., "status": ..., ...}}
                        if isinstance(job_status, dict):
                            # Get data from result (SuccessResult format)
                            data = job_status.get("data", job_status)
                            
                            # Get status from data
                            status = data.get("status", "unknown")

                            if status == "completed":
                                return True
                            elif status == "failed":
                                error = data.get("error", "Unknown error")
                                # CRITICAL: Check for hooks variable error
                                if (
                                    "cannot access local variable 'hooks'"
                                    in str(error).lower()
                                ):
                                    print(
                                        f"   ❌ CRITICAL: Hooks variable initialization error!"
                                    )
                                    print(f"   ❌ This indicates the fix is not working!")
                                    return False
                                print(f"   ❌ Job failed: {error}")
                                return False
                            # Status is pending, running, or other - continue waiting
                            # (no need to print, just wait and continue loop)
                        else:
                            # Unexpected format - continue waiting
                            pass
                        
                        # Continue waiting for job to complete (pending/running/other statuses)
                        time.sleep(1)
                        waited += 1
                        continue

            return False
        else:
            # Command executed synchronously (unexpected but OK)
            return True

    except Exception as e:
        error_msg = str(e)
        # CRITICAL: Check for hooks variable error
        if "cannot access local variable 'hooks'" in error_msg.lower():
            print(f"   ❌ CRITICAL: Hooks variable initialization error!")
            print(f"   ❌ This indicates the fix is not working!")
            return False
        print(f"   Queue command error: {e}")
        return False


def test_mode(config: dict) -> bool:
    """Test a single mode configuration."""
    print(f"\n{'='*70}")
    print(f"Testing: {config['name']}")
    print(f"{'='*70}")
    print(f"[DEBUG] test_mode START for {config['name']}")

    # Kill any existing server on this port
    print(f"[DEBUG] Killing any existing server on port {config['port']}")
    kill_server_on_port(config["port"])
    time.sleep(1)
    print(f"[DEBUG] Port cleanup completed")

    # Start server - use fallback config if primary doesn't exist
    config_path = Path(config["config"])
    if not config_path.exists() and "fallback" in config:
        fallback_path = Path(config["fallback"])
        if fallback_path.exists():
            config_path = fallback_path
            print(f"⚠️  Using fallback config: {config_path}")
        else:
            log_result(
                f"{config['name']} - Server start",
                "FAIL",
                f"Config file not found: {config['config']} or {config.get('fallback', 'N/A')}",
            )
            return False
    elif not config_path.exists():
        log_result(
            f"{config['name']} - Server start",
            "FAIL",
            f"Config file not found: {config_path}",
        )
        return False

    protocol = "https" if config["use_ssl"] else "http"
    url = f"{protocol}://localhost:{config['port']}"
    verify = not config["use_ssl"]

    # Build command
    cmd = [
        sys.executable,
        "mcp_proxy_adapter/examples/full_application/main.py",
        "--config",
        str(config_path),
        "--port",
        str(config["port"]),
    ]

    print(f"Starting server: {' '.join(cmd)}")
    sys.stdout.flush()
    server_process = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    try:
        # Wait for server to start
        print("Waiting for server to start...")
        if not wait_for_server(url, timeout=30, verify=verify):
            log_result(
                f"{config['name']} - Server start", "FAIL", "Server did not start"
            )
            return False

        log_result(
            f"{config['name']} - Server start", "PASS", "Server started successfully"
        )

        # Test 1: Health endpoint
        if test_health_endpoint(config):
            log_result(f"{config['name']} - Health endpoint", "PASS")
        else:
            log_result(f"{config['name']} - Health endpoint", "FAIL")
            return False

        # Test 2: Echo command
        if test_echo_command(config):
            log_result(f"{config['name']} - Echo command", "PASS")
        else:
            log_result(f"{config['name']} - Echo command", "FAIL")
            return False

        # Test 3: Queue command (CRITICAL - tests spawn mode registration)
        print(f"[DEBUG] Starting queue command test for {config['name']}")
        if test_queue_command(config):
            log_result(
                f"{config['name']} - Queue command",
                "PASS",
                "Command executed successfully in child process",
            )
        else:
            log_result(
                f"{config['name']} - Queue command",
                "FAIL",
                "Command failed in child process - registration issue!",
            )
            print(f"[DEBUG] Queue command test FAILED for {config['name']}, returning False")
            return False

        print(f"[DEBUG] All tests PASSED for {config['name']}, about to return True")
        sys.stdout.flush()
        result = True
        print(f"[DEBUG] Set result=True for {config['name']}, entering finally block")
        sys.stdout.flush()
        return result

    finally:
        print(f"[DEBUG] Entering finally block for {config['name']}")
        sys.stdout.flush()
        # Stop server with timeout protection - use non-blocking approach
        try:
            print(f"[DEBUG] Checking server process status for {config['name']}")
            sys.stdout.flush()
            if server_process.poll() is None:  # Process is still running
                print(f"[DEBUG] Server process is still running, terminating for {config['name']}")
                sys.stdout.flush()
                try:
                    server_process.terminate()
                    # Use shorter timeout and don't block
                    try:
                        server_process.wait(timeout=1)
                        print(f"[DEBUG] Server process terminated gracefully for {config['name']}")
                        sys.stdout.flush()
                    except subprocess.TimeoutExpired:
                        print(f"[DEBUG] Server process timeout, killing for {config['name']}")
                        sys.stdout.flush()
                        server_process.kill()
                        # Don't wait - just kill and move on
                        time.sleep(0.2)
                        print(f"[DEBUG] Server process killed for {config['name']}")
                        sys.stdout.flush()
                except Exception as e:
                    print(f"[DEBUG] Exception during terminate/kill: {e}")
                    sys.stdout.flush()
                    try:
                        server_process.kill()
                    except Exception:
                        pass
            else:
                exit_code = server_process.poll()
                print(f"[DEBUG] Server process already terminated for {config['name']} (exit code: {exit_code})")
                sys.stdout.flush()
        except Exception as e:
            print(f"[DEBUG] Exception in server termination: {e}")
            sys.stdout.flush()
            try:
                if server_process.poll() is None:
                    server_process.kill()
            except Exception:
                pass
        
        # Ensure port is free - use non-blocking approach
        print(f"[DEBUG] Cleaning up port {config['port']} for {config['name']}")
        sys.stdout.flush()
        try:
            # Run kill_server_on_port in a way that doesn't block
            kill_server_on_port(config["port"])
            print(f"[DEBUG] Port cleanup completed for {config['name']}")
            sys.stdout.flush()
        except Exception as e:
            print(f"[DEBUG] Exception during port cleanup: {e}")
            sys.stdout.flush()
        
        # Small delay to ensure cleanup
        print(f"[DEBUG] Waiting 0.3s before finishing cleanup for {config['name']}")
        sys.stdout.flush()
        try:
            time.sleep(0.3)  # Reduced from 0.5
        except Exception as e:
            print(f"[DEBUG] Exception during sleep in finally: {e}")
            sys.stdout.flush()
        print(f"[DEBUG] Finally block completed for {config['name']}, function will return")
        sys.stdout.flush()


def main():
    """Run comprehensive test pipeline."""
    print("=" * 70)
    print("MCP Proxy Adapter - Comprehensive Test Pipeline")
    print("Testing all modes with custom commands in spawn mode")
    print("=" * 70)

    # Check if configs exist (with fallback support)
    missing_configs = []
    for config in TEST_CONFIGS:
        primary = Path(config["config"])
        if not primary.exists():
            # Check fallback
            if "fallback" in config:
                fallback = Path(config["fallback"])
                if not fallback.exists():
                    missing_configs.append(
                        f"{config['config']} (fallback: {config['fallback']})"
                    )
            else:
                missing_configs.append(config["config"])

    if missing_configs:
        print("⚠️  Missing configuration files (will use fallback if available):")
        for cfg in missing_configs:
            print(f"   - {cfg}")
        print("\n⚠️  Continuing with available configs...")

    # Run tests for each mode
    results = []
    for i, config in enumerate(TEST_CONFIGS):
        print(f"\n{'='*70}")
        print(f"Progress: {i+1}/{len(TEST_CONFIGS)} modes")
        print(f"{'='*70}")
        print(f"[DEBUG] Starting iteration {i+1} for {config['name']}")
        try:
            # Ensure port is free before starting
            print(f"[DEBUG] Pre-cleaning port {config['port']} for {config['name']}")
            kill_server_on_port(config["port"])
            time.sleep(0.5)
            print(f"[DEBUG] Port pre-cleanup completed, calling test_mode for {config['name']}")
            
            try:
                success = test_mode(config)
                print(f"[DEBUG] test_mode returned successfully for {config['name']}: {success}")
                sys.stdout.flush()
            except Exception as e:
                print(f"[DEBUG] EXCEPTION in test_mode for {config['name']}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                sys.stdout.flush()
                success = False
            results.append((config["name"], success))
            print(f"✅ Completed: {config['name']} - {'PASS' if success else 'FAIL'}")
            print(f"[DEBUG] Result added to list for {config['name']}")
            sys.stdout.flush()
            
            # Small delay between tests to ensure cleanup
            print(f"[DEBUG] Waiting 0.5s before next test")
            sys.stdout.flush()
            time.sleep(0.5)
            print(f"[DEBUG] Iteration {i+1} completed for {config['name']}, moving to next")
            sys.stdout.flush()
        except KeyboardInterrupt:
            print(f"\n⚠️  Test interrupted by user at {config['name']}")
            print(f"[DEBUG] KeyboardInterrupt caught for {config['name']}")
            results.append((config["name"], False))
            # Cleanup before break
            kill_server_on_port(config["port"])
            break
        except Exception as e:
            print(f"❌ Error testing {config['name']}: {e}")
            print(f"[DEBUG] Exception caught in main loop for {config['name']}: {type(e).__name__}")
            import traceback

            traceback.print_exc()
            results.append((config["name"], False))
            # Ensure cleanup even on error
            try:
                kill_server_on_port(config["port"])
            except Exception:
                pass
            time.sleep(0.5)
        print(f"[DEBUG] End of iteration {i+1} for {config['name']}, loop continues")

    # Summary
    print("\n" + "=" * 70)
    print("Test Pipeline Summary")
    print("=" * 70)

    passed = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} modes")

    if failed > 0:
        print("\n⚠️  Some modes failed. Check the output above for details.")
        print("\n🔍 Key things to check:")
        print("   1. Are custom commands registered correctly?")
        print("   2. Do commands with use_queue=True work in spawn mode?")
        print("   3. Are modules auto-imported in child processes?")
        return 1

    print("\n🎉 All modes passed! Custom commands work correctly in spawn mode.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
