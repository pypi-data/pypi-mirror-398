#!/usr/bin/env python3
"""
Test a single server mode.
"""
import subprocess
import time
import requests
import sys
import os

# Skip this file in pytest runs - it's a standalone script
import pytest
pytest.skip("Standalone scenario", allow_module_level=True)

def test_mode(config_file, port, mode_name):
    """Test a specific server mode."""
    print(f"🔍 Testing {mode_name} on port {port}...")
    
    # Kill any existing processes
    try:
        os.system("pkill -f 'python.*main.py'")
        time.sleep(2)
    except:
        pass
    
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
            print(f"Response: {response.text}")
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
            print(f"Echo result: {result}")
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

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python test_mode.py <config_file> <port> <mode_name>")
        print("Example: python test_mode.py http_basic.json 15000 'HTTP Basic'")
        sys.exit(1)
    
    config_file = sys.argv[1]
    port = int(sys.argv[2])
    mode_name = sys.argv[3]
    
    test_mode(config_file, port, mode_name)
