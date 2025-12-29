#!/usr/bin/env python3
"""
Sequential testing of all server modes.
"""
import subprocess
import time
import requests
import sys
import os

# Skip this file in pytest runs - it's a standalone script
import pytest
pytest.skip("Standalone scenario", allow_module_level=True)

def kill_processes():
    """Kill all Python processes."""
    try:
        os.system("pkill -f 'python.*main.py'")
        time.sleep(2)
    except:
        pass

def test_mode(config_file, port, mode_name):
    """Test a specific server mode."""
    print(f"\n{'='*60}")
    print(f"🔍 Testing {mode_name} on port {port}")
    print(f"{'='*60}")
    
    # Kill any existing processes
    kill_processes()
    
    # Start server
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", f"mcp_proxy_adapter/examples/full_application/configs/{config_file}",
        "--port", str(port)
    ]
    
    print(f"🚀 Starting server: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(8)
        
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        protocol = "https" if "https" in config_file or "mtls" in config_file else "http"
        url = f"{protocol}://localhost:{port}/health"
        
        if protocol == "https":
            response = requests.get(url, verify=False, timeout=10)
        else:
            response = requests.get(url, timeout=10)
            
        print(f"Health response: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ {mode_name} - health endpoint works")
        else:
            print(f"❌ {mode_name} - health endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            
        # Test echo command
        print("🔍 Testing echo command...")
        data = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"message": "Hello World"},
            "id": 1
        }
        
        api_url = f"{protocol}://localhost:{port}/api/jsonrpc"
        if protocol == "https":
            response = requests.post(api_url, json=data, verify=False, timeout=10)
        else:
            response = requests.post(api_url, json=data, timeout=10)
            
        print(f"Echo response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if "result" in result and result["result"].get("success"):
                print(f"✅ {mode_name} - echo command works")
            else:
                print(f"❌ {mode_name} - echo command failed: {result}")
        else:
            print(f"❌ {mode_name} - echo command failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ {mode_name} - test failed: {e}")
    finally:
        # Stop server
        print("🛑 Stopping server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("✅ Server stopped")
        time.sleep(2)  # Wait before next test

def main():
    """Run all tests sequentially."""
    print("🚀 Starting comprehensive server mode testing...")
    print("=" * 60)
    
    # Test modes
    modes = [
        ("http_basic.json", 15000, "HTTP Basic"),
        ("http_token.json", 15001, "HTTP + Token"),
        ("http_token_roles.json", 15002, "HTTP + Token + Roles"),
        ("https_basic.json", 15003, "HTTPS Basic"),
        ("https_token.json", 15004, "HTTPS + Token"),
        ("https_token_roles.json", 15005, "HTTPS + Token + Roles"),
        ("mtls_no_roles_correct.json", 15006, "mTLS Basic"),
        ("mtls_with_roles_correct.json", 15007, "mTLS + Roles")
    ]
    
    results = []
    
    for config_file, port, mode_name in modes:
        try:
            test_mode(config_file, port, mode_name)
            results.append(f"✅ {mode_name} - PASSED")
        except Exception as e:
            results.append(f"❌ {mode_name} - FAILED: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TESTING SUMMARY")
    print("=" * 60)
    for result in results:
        print(result)
    
    print("\n🎯 Testing completed!")

if __name__ == "__main__":
    main()
