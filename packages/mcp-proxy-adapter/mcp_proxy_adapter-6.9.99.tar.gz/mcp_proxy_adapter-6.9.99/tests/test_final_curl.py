#!/usr/bin/env python3
"""
Test curl functionality.
"""
import requests
import time

def test_server():
    """Test server functionality."""
    print("🔍 Testing server on port 15000...")
    
    try:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        response = requests.get("http://localhost:15000/health", timeout=10)
        print(f"Health response: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health endpoint works")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
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
                print("✅ Echo command works")
            else:
                print(f"❌ Echo command failed: {result}")
        else:
            print(f"❌ Echo command failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_server()
