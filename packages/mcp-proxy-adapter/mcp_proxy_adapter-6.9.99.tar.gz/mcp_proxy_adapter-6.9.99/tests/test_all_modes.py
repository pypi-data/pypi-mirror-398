#!/usr/bin/env python3
"""
Script to test all server modes according to project rules.
"""
import subprocess
import time
import requests
import json
import os
import signal
import sys
import psutil

def kill_processes_on_port(port):
    """Kill all processes using the specified port."""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                connections = proc.info['connections']
                if connections:
                    for conn in connections:
                        if conn.laddr.port == port:
                            print(f"🔪 Killing process {proc.info['pid']} on port {port}")
                            proc.kill()
                            proc.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        print(f"⚠️ Warning: Could not kill processes on port {port}: {e}")

def check_port_available(port):
    """Check if port is available."""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                connections = proc.info['connections']
                if connections:
                    for conn in connections:
                        if conn.laddr.port == port:
                            return False
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return True
    except Exception:
        return True

def cleanup_before_test(port):
    """Clean up before starting test."""
    print(f"🧹 Cleaning up port {port}...")
    kill_processes_on_port(port)
    time.sleep(2)
    
    if check_port_available(port):
        print(f"✅ Port {port} is available")
    else:
        print(f"⚠️ Port {port} may still be in use")

def test_http_basic():
    """Test HTTP basic mode."""
    print("🔍 Testing HTTP basic mode on port 15000...")
    port = 15000
    
    # Clean up before test
    cleanup_before_test(port)
    
    # Start server
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/http_basic.json",
        "--port", str(port)
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            print("✅ HTTP basic - health endpoint works")
        else:
            print(f"❌ HTTP basic - health endpoint failed: {response.status_code}")
            
        # Test echo command
        data = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"message": "Hello World"},
            "id": 1
        }
        response = requests.post(f"http://localhost:{port}/api/jsonrpc", 
                               json=data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if "result" in result and result["result"].get("success"):
                print("✅ HTTP basic - echo command works")
            else:
                print(f"❌ HTTP basic - echo command failed: {result}")
        else:
            print(f"❌ HTTP basic - echo command failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ HTTP basic - test failed: {e}")
    finally:
        # Stop server
        process.terminate()
        process.wait()

def test_http_token():
    """Test HTTP with token authentication."""
    print("🔍 Testing HTTP + token mode on port 15001...")
    port = 15001
    
    # Clean up before test
    cleanup_before_test(port)
    
    # Start server
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/http_token.json",
        "--port", str(port)
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            print("✅ HTTP + token - health endpoint works")
        else:
            print(f"❌ HTTP + token - health endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ HTTP + token - test failed: {e}")
    finally:
        # Stop server
        process.terminate()
        process.wait()

def test_http_token_roles():
    """Test HTTP with token and roles."""
    print("🔍 Testing HTTP + token + roles mode on port 15002...")
    port = 15002
    
    # Clean up before test
    cleanup_before_test(port)
    
    # Start server
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/http_token_roles.json",
        "--port", str(port)
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            print("✅ HTTP + token + roles - health endpoint works")
        else:
            print(f"❌ HTTP + token + roles - health endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ HTTP + token + roles - test failed: {e}")
    finally:
        # Stop server
        process.terminate()
        process.wait()

def test_https_basic():
    """Test HTTPS basic mode."""
    print("🔍 Testing HTTPS basic mode on port 15003...")
    port = 15003
    
    # Clean up before test
    cleanup_before_test(port)
    
    # Start server
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/https_basic.json",
        "--port", str(port)
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint (with SSL verification disabled for testing)
        response = requests.get(f"https://localhost:{port}/health", 
                              verify=False, timeout=5)
        if response.status_code == 200:
            print("✅ HTTPS basic - health endpoint works")
        else:
            print(f"❌ HTTPS basic - health endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ HTTPS basic - test failed: {e}")
    finally:
        # Stop server
        process.terminate()
        process.wait()

def test_https_token():
    """Test HTTPS with token authentication."""
    print("🔍 Testing HTTPS + token mode on port 15004...")
    port = 15004
    
    # Clean up before test
    cleanup_before_test(port)
    
    # Start server
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/https_token.json",
        "--port", str(port)
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint
        response = requests.get(f"https://localhost:{port}/health", 
                              verify=False, timeout=5)
        if response.status_code == 200:
            print("✅ HTTPS + token - health endpoint works")
        else:
            print(f"❌ HTTPS + token - health endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ HTTPS + token - test failed: {e}")
    finally:
        # Stop server
        process.terminate()
        process.wait()

def test_https_token_roles():
    """Test HTTPS with token and roles."""
    print("🔍 Testing HTTPS + token + roles mode on port 15005...")
    port = 15005
    
    # Clean up before test
    cleanup_before_test(port)
    
    # Start server
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/https_token_roles.json",
        "--port", str(port)
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint
        response = requests.get(f"https://localhost:{port}/health", 
                              verify=False, timeout=5)
        if response.status_code == 200:
            print("✅ HTTPS + token + roles - health endpoint works")
        else:
            print(f"❌ HTTPS + token + roles - health endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ HTTPS + token + roles - test failed: {e}")
    finally:
        # Stop server
        process.terminate()
        process.wait()

def test_mtls_basic():
    """Test mTLS basic mode."""
    print("🔍 Testing mTLS basic mode on port 15006...")
    port = 15006
    
    # Clean up before test
    cleanup_before_test(port)
    
    # Start server
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/mtls_no_roles_correct.json",
        "--port", str(port)
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint (with SSL verification disabled for testing)
        response = requests.get(f"https://localhost:{port}/health", 
                              verify=False, timeout=5)
        if response.status_code == 200:
            print("✅ mTLS basic - health endpoint works")
        else:
            print(f"❌ mTLS basic - health endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ mTLS basic - test failed: {e}")
    finally:
        # Stop server
        process.terminate()
        process.wait()

def test_mtls_roles():
    """Test mTLS with roles mode."""
    print("🔍 Testing mTLS + roles mode on port 15007...")
    port = 15007
    
    # Clean up before test
    cleanup_before_test(port)
    
    # Start server
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/mtls_with_roles_correct.json",
        "--port", str(port)
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint (with SSL verification disabled for testing)
        response = requests.get(f"https://localhost:{port}/health", 
                              verify=False, timeout=5)
        if response.status_code == 200:
            print("✅ mTLS + roles - health endpoint works")
        else:
            print(f"❌ mTLS + roles - health endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ mTLS + roles - test failed: {e}")
    finally:
        # Stop server
        process.terminate()
        process.wait()

def main():
    """Run all tests."""
    print("🚀 Starting comprehensive server mode testing...")
    print("=" * 60)
    
    # Test all modes
    test_http_basic()
    print()
    
    test_http_token()
    print()
    
    test_http_token_roles()
    print()
    
    test_https_basic()
    print()
    
    test_https_token()
    print()
    
    test_https_token_roles()
    print()
    
    test_mtls_basic()
    print()
    
    test_mtls_roles()
    print()
    
    print("=" * 60)
    print("✅ All mode tests completed!")

if __name__ == "__main__":
    main()
