#!/usr/bin/env python3
"""
Simple script to test a single server mode.
"""
import subprocess
import time
import requests
import sys
import os

def test_http_basic():
    """Test HTTP basic mode on port 15000."""
    print("🔍 Testing HTTP basic mode on port 15000...")
    port = 15000
    
    # Kill any existing processes on this port
    try:
        os.system(f"pkill -f 'python.*main.py'")
        time.sleep(2)
    except:
        pass
    
    # Start server
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/http_basic.json",
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
        response = requests.get(f"http://localhost:{port}/health", timeout=10)
        print(f"Health response: {response.status_code}")
        if response.status_code == 200:
            print("✅ HTTP basic - health endpoint works")
            print(f"Response: {response.text}")
        else:
            print(f"❌ HTTP basic - health endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            
        # Test echo command
        print("🔍 Testing echo command...")
        data = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"message": "Hello World"},
            "id": 1
        }
        response = requests.post(f"http://localhost:{port}/api/jsonrpc", 
                               json=data, timeout=10)
        print(f"Echo response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Echo result: {result}")
            if "result" in result and result["result"].get("success"):
                print("✅ HTTP basic - echo command works")
            else:
                print(f"❌ HTTP basic - echo command failed: {result}")
        else:
            print(f"❌ HTTP basic - echo command failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ HTTP basic - test failed: {e}")
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
    test_http_basic()
