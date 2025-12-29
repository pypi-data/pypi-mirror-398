#!/usr/bin/env python3
"""
Direct test for HTTP Basic mode without terminal issues.
"""
import subprocess
import time
import requests
import sys
import os
import signal

# Set up environment
os.environ['PATH'] = os.path.join(os.getcwd(), '.venv', 'bin') + ':' + os.environ['PATH']

def test_http_basic():
    """Test HTTP Basic mode on port 15000."""
    print("🔍 Testing HTTP Basic mode on port 15000...")
    
    # Kill any existing processes
    try:
        os.system("pkill -f 'python.*main.py'")
        time.sleep(2)
    except:
        pass
    
    # Start server with activated environment
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/http_basic.json",
        "--port", "15000"
    ]
    
    print(f"🚀 Starting server: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(8)
        
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        response = requests.get("http://localhost:15000/health", timeout=10)
        print(f"Health response: {response.status_code}")
        if response.status_code == 200:
            print("✅ HTTP Basic - health endpoint works")
            print(f"Response: {response.text}")
        else:
            print(f"❌ HTTP Basic - health endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            
        # Test echo command
        print("🔍 Testing echo command...")
        data = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"message": "Hello World"},
            "id": 1
        }
        response = requests.post("http://localhost:15000/api/jsonrpc", 
                               json=data, timeout=10)
        print(f"Echo response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Echo result: {result}")
            if "result" in result and result["result"].get("success"):
                print("✅ HTTP Basic - echo command works")
            else:
                print(f"❌ HTTP Basic - echo command failed: {result}")
        else:
            print(f"❌ HTTP Basic - echo command failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ HTTP Basic - test failed: {e}")
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
