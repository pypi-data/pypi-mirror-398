#!/usr/bin/env python3
"""
Automated test for all 8 MCP Proxy Adapter modes
Tests configuration generation, server startup, health checks, JSON-RPC, and proxy registration

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import time
import json
import requests
import sys
from pathlib import Path

# Skip this file in pytest runs - it's a standalone script
import pytest
pytest.skip("Standalone scenario", allow_module_level=True)

def run_command(cmd, check=True):
    """Run command and return result"""
    print(f"🔧 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {result.stderr}")
        return None
    return result

def test_mode(config_name, protocol, use_token=False, use_roles=False, use_ssl=False, use_mtls=False):
    """Test a single mode"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing {config_name}")
    print(f"   Protocol: {protocol}")
    print(f"   Token: {use_token}")
    print(f"   Roles: {use_roles}")
    print(f"   SSL: {use_ssl}")
    print(f"   mTLS: {use_mtls}")
    print(f"{'='*60}")
    
    # Update docker-compose to use this config
    compose_content = f"""services:
  mcp-test-server:
    user: "1000:1000"
    command: ["sh","-c","python mcp_proxy_adapter/examples/full_application/main.py --config /app/test_configs/{config_name}.json --port 8001"]
    ports:
      - "8080:8001"
    volumes:
      - ./test_configs:/app/test_configs:ro
      - ./mtls_certificates:/app/mtls_certificates:ro
      - ./logs:/app/logs
  mcp-local-proxy:
    build:
      context: .
      dockerfile: Dockerfile.test-server
    container_name: mcp-local-proxy
    command: ["sh","-c","python mcp_proxy_adapter/examples/run_proxy_server.py --host 0.0.0.0 --port 3005"]
    ports:
      - "3005:3005"
    volumes:
      - ./logs:/app/logs
    networks:
      - smart-assistant
networks:
  smart-assistant:
    external: false
    name: mcp-e2e-net
"""
    
    with open('docker-compose.override.local.yml', 'w') as f:
        f.write(compose_content)
    
    # Restart server with new config
    print("🔄 Restarting server with new configuration...")
    result = run_command(['docker', 'compose', '-f', 'docker-compose.test.yml', '-f', 'docker-compose.override.local.yml', 'restart', 'mcp-test-server'])
    if not result:
        return False
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(8)
    
    # Check server logs
    result = run_command(['docker', 'logs', 'mcp-test-server', '--tail', '10'])
    if result and 'Successfully registered with proxy' in result.stdout:
        print("✅ Server started and registered with proxy")
    else:
        print("❌ Server failed to start or register")
        return False
    
    # Test health endpoint
    print("🔍 Testing health endpoint...")
    try:
        if use_ssl or use_mtls:
            # For HTTPS/mTLS, test from inside container
            result = run_command(['docker', 'exec', 'mcp-test-server', 'python', '-c', 
                                f'import requests; print(requests.get("https://localhost:8000/health", verify=False).json())'])
        else:
            result = run_command(['docker', 'exec', 'mcp-test-server', 'python', '-c', 
                                'import requests; print(requests.get("http://localhost:8000/health").json())'])
        
        if result and 'status' in result.stdout and 'ok' in result.stdout:
            print("✅ Health endpoint working")
        else:
            print("❌ Health endpoint failed")
            return False
    except Exception as e:
        print(f"❌ Health test error: {e}")
        return False
    
    # Test JSON-RPC endpoint
    print("🔍 Testing JSON-RPC endpoint...")
    try:
        headers = {}
        if use_token:
            headers['X-API-Key'] = 'admin-secret-key'
        
        if use_ssl or use_mtls:
            # For HTTPS/mTLS, test from inside container
            cmd = ['docker', 'exec', 'mcp-test-server', 'python', '-c', 
                   f'import requests; print(requests.post("https://localhost:8000/api/jsonrpc", '
                   f'json={{"jsonrpc": "2.0", "method": "echo", "params": {{"message": "Hello {config_name}"}}, "id": 1}}, '
                   f'headers={headers}, verify=False).json())']
        else:
            cmd = ['docker', 'exec', 'mcp-test-server', 'python', '-c', 
                   f'import requests; print(requests.post("http://localhost:8000/api/jsonrpc", '
                   f'json={{"jsonrpc": "2.0", "method": "echo", "params": {{"message": "Hello {config_name}"}}, "id": 1}}, '
                   f'headers={headers}).json())']
        
        result = run_command(cmd)
        if result and 'success' in result.stdout and 'True' in result.stdout:
            print("✅ JSON-RPC endpoint working")
        else:
            print("❌ JSON-RPC endpoint failed")
            return False
    except Exception as e:
        print(f"❌ JSON-RPC test error: {e}")
        return False
    
    # Test proxy registration
    print("🔍 Testing proxy registration...")
    try:
        result = run_command(['curl', '-s', 'http://localhost:3005/proxy/list'])
        if result and 'adapters' in result.stdout:
            data = json.loads(result.stdout)
            if data['count'] > 0:
                print("✅ Proxy registration working")
            else:
                print("❌ No adapters registered")
                return False
        else:
            print("❌ Proxy registration failed")
            return False
    except Exception as e:
        print(f"❌ Proxy registration test error: {e}")
        return False
    
    print(f"✅ {config_name} mode test PASSED")
    return True

def main():
    """Main test function"""
    print("🚀 Starting MCP Proxy Adapter comprehensive testing")
    print("=" * 80)
    
    # Test configurations
    test_configs = [
        ("http_basic", "http", False, False, False, False),
        ("http_token", "http", True, False, False, False),
        ("http_token_roles", "http", True, True, False, False),
        ("https_basic", "https", False, False, True, False),
        ("https_token", "https", True, False, True, False),
        ("https_token_roles", "https", True, True, True, False),
        ("mtls_basic", "mtls", False, False, True, True),
        ("mtls_token_roles", "mtls", True, True, True, True),
    ]
    
    results = []
    passed = 0
    total = len(test_configs)
    
    for config_name, protocol, use_token, use_roles, use_ssl, use_mtls in test_configs:
        success = test_mode(config_name, protocol, use_token, use_roles, use_ssl, use_mtls)
        results.append((config_name, success))
        if success:
            passed += 1
        time.sleep(2)  # Pause between tests
    
    # Final report
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    for config_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {config_name}")
    
    print(f"\n🎯 FINAL SCORE: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! MCP Proxy Adapter is working correctly!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
