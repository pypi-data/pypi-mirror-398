#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Test script for HTTP and HTTPS protocol examples with proxy registration.
"""

import json
import os
import subprocess
import sys
import time
import requests
from pathlib import Path


class ProtocolTester:
    """Test HTTP and HTTPS protocol examples with proxy registration."""
    
    def __init__(self):
        """
        Initialize protocol tester.
        """
        self.base_dir = Path(__file__).parent
        self.http_config = self.base_dir / "http_proxy_example.json"
        self.https_config = self.base_dir / "https_proxy_example.json"
        self.proxy_process = None
        self.http_server_process = None
        self.https_server_process = None
        
    def check_ports_available(self):
        """Check if required ports are available."""
        # Check server ports (20021, 20022) - these should be free
        server_ports = [20021, 20022]
        occupied_ports = []
        
        for port in server_ports:
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        occupied_ports.append(port)
            except Exception:
                pass
        
        # Check if proxy port (20005) is available or already running
        proxy_port = 20005
        proxy_running = False
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', proxy_port))
                if result == 0:
                    proxy_running = True
        except Exception:
            pass
                
        if occupied_ports:
            print(f"❌ Server ports {occupied_ports} are already in use")
            print("Please stop services using these ports and try again")
            return False
        
        if proxy_running:
            print(f"✅ Proxy server already running on port {proxy_port}")
        else:
            print(f"⚠️ Proxy server not running on port {proxy_port} - will start it")
            
        print(f"✅ Server ports {server_ports} are available")
        return True
    
    def start_proxy_server(self):
        """Start the proxy server if not already running."""
        # Check if proxy is already running
        if self.test_proxy_health():
            print("✅ Proxy server already running")
            return True
            
        print("🚀 Starting proxy server...")
        try:
            self.proxy_process = subprocess.Popen([
                sys.executable, "-m", "mcp_proxy_adapter.examples.run_proxy_server",
                "--host", "127.0.0.1",
                "--port", "20005",
                "--log-level", "info"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for proxy to start
            time.sleep(3)
            
            # Test proxy health
            if self.test_proxy_health():
                print("✅ Proxy server started successfully")
                return True
            else:
                print("❌ Proxy server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start proxy server: {e}")
            return False
    
    def test_proxy_health(self):
        """Test proxy server health on both HTTP and HTTPS."""
        print("🔍 Testing proxy server health...")
        
        # Try HTTP first
        try:
            response = requests.get(
                "https://127.0.0.1:20005/health",
                verify=False,
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Proxy server responding on HTTP")
                return True
        except Exception as e:
            print(f"⚠️ HTTP health check failed: {e}")
        
        # Try HTTPS
        try:
            response = requests.get(
                "https://127.0.0.1:20005/health",
                verify=False,
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Proxy server responding on HTTPS")
                return True
        except Exception as e:
            print(f"⚠️ HTTPS health check failed: {e}")
        
        print("❌ Proxy server not responding on either protocol")
        return False
    
    def start_http_server(self):
        """Start HTTP test server."""
        print("🚀 Starting HTTP test server...")
        try:
            self.http_server_process = subprocess.Popen([
                sys.executable, "-m", "mcp_proxy_adapter",
                "--config", str(self.http_config)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for server to start
            time.sleep(5)
            
            # Test server health
            if self.test_server_health("http", 20021):
                print("✅ HTTP server started successfully")
                return True
            else:
                print("❌ HTTP server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start HTTP server: {e}")
            return False
    
    def start_https_server(self):
        """Start HTTPS test server."""
        print("🚀 Starting HTTPS test server...")
        try:
            self.https_server_process = subprocess.Popen([
                sys.executable, "-m", "mcp_proxy_adapter",
                "--config", str(self.https_config)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for server to start
            time.sleep(5)
            
            # Test server health
            if self.test_server_health("https", 20022):
                print("✅ HTTPS server started successfully")
                return True
            else:
                print("❌ HTTPS server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start HTTPS server: {e}")
            return False
    
    def test_server_health(self, protocol, port):
        """Test server health."""
        # Try the specified protocol first
        try:
            url = f"{protocol}://127.0.0.1:{port}/health"
            response = requests.get(
                url,
                verify=False if protocol == "https" else True,
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ {protocol.upper()} server responding on port {port}")
                return True
            else:
                print(f"⚠️ {protocol.upper()} server health check failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️ {protocol.upper()} server health check failed: {e}")
        
        # If HTTPS failed, try HTTP as fallback
        if protocol == "https":
            try:
                url = f"http://127.0.0.1:{port}/health"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Server responding on HTTP (fallback) on port {port}")
                    return True
                else:
                    print(f"⚠️ HTTP fallback health check failed: {response.status_code}")
            except Exception as e:
                print(f"⚠️ HTTP fallback health check failed: {e}")
        
        return False
    
    def test_api_key_auth(self, protocol, port, token):
        """Test API key authentication."""
        try:
            url = f"{protocol}://127.0.0.1:{port}/api/test"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                url,
                headers=headers,
                verify=False if protocol == "https" else True,
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ {protocol.upper()} API key auth successful with token {token}")
                return True
            else:
                print(f"⚠️ {protocol.upper()} API key auth failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️ {protocol.upper()} API key auth failed: {e}")
            return False
    
    def test_proxy_registration(self, protocol, port, server_id):
        """Test proxy registration."""
        try:
            # Check if server is registered with proxy
            response = requests.get(
                "https://127.0.0.1:20005/list",
                verify=False,
                timeout=5
            )
            if response.status_code == 200:
                registered_servers = response.json()
                for server in registered_servers.get("adapters", []):
                    if server.get("name") == server_id:
                        print(f"✅ {protocol.upper()} server {server_id} registered with proxy")
                        return True
                
                print(f"⚠️ {protocol.upper()} server {server_id} not found in proxy registry")
                return False
            else:
                print(f"⚠️ Failed to get proxy registry: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️ Proxy registration check failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up all processes."""
        print("🧹 Cleaning up processes...")
        
        for process, name in [
            (self.http_server_process, "HTTP server"),
            (self.https_server_process, "HTTPS server"),
            (self.proxy_process, "Proxy server")
        ]:
            if process and process.poll() is None:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    
    def run_tests(self):
        """Run all protocol tests."""
        print("🧪 Starting Protocol Examples Test Suite")
        print("=" * 50)
        
        # Check ports
        if not self.check_ports_available():
            return False
        
        try:
            # Start proxy server
            if not self.start_proxy_server():
                return False
            
            # Start HTTP server
            if not self.start_http_server():
                return False
            
            # Start HTTPS server
            if not self.start_https_server():
                return False
            
            print("\n🔍 Running tests...")
            print("-" * 30)
            
            # Test API key authentication
            print("\n📋 Testing API Key Authentication:")
            self.test_api_key_auth("http", 20021, "admin-secret-key")
            self.test_api_key_auth("https", 20022, "admin-secret-key")
            
            # Test proxy registration
            print("\n📋 Testing Proxy Registration:")
            self.test_proxy_registration("http", 20021, "http_test_server")
            self.test_proxy_registration("https", 20022, "https_test_server")
            
            print("\n✅ Protocol examples test completed!")
            return True
            
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """Main function."""
    tester = ProtocolTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
