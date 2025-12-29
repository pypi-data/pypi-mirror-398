#!/usr/bin/env python3
"""
Docker-based testing script for all 8 modes
Tests server with mounted code for safe editing

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import subprocess
import time
import os
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent
import sys
sys.path.insert(0, str(project_root))

from mcp_proxy_adapter.core.client import UniversalClient, create_client_from_config


class DockerModeTester:
    """Test all 8 modes using Docker with mounted code"""
    
    def __init__(self):
        self.test_dir = Path("./test_configs")
        self.cert_dir = "./mtls_certificates/server"
        self.key_dir = "./mtls_certificates/server"
        self.ca_dir = "./mtls_certificates/ca"
        self.results = {}
        
        # Ensure test directory exists
        self.test_dir.mkdir(exist_ok=True)
    
    def run_command(self, command: str, check_error: bool = True) -> tuple[bool, str, str]:
        """Run command and return success, stdout, stderr"""
        print(f"🔧 Running: {command}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def generate_config(self, protocol: str, token: bool, roles: bool, output_name: str, port: int) -> bool:
        """Generate configuration for a specific mode"""
        print(f"\n🔧 Generating config: {output_name}")
        
        args = ["--protocol", protocol]
        if token:
            args.append("--token")
        if roles:
            args.append("--roles")
        
        # Add proxy registration
        args.extend(["--proxy-registration", "--proxy-url", "http://mcp-local-proxy:3005"])
        
        # Add SSL config for https/mtls
        if protocol in ["https", "mtls"]:
            args.extend(["--cert-dir", self.cert_dir, "--key-dir", self.key_dir])
        
        # Add output
        args.extend(["--output", output_name, "--output-dir", str(self.test_dir), "--port", str(port)])
        
        cmd = f"python mcp_proxy_adapter/examples/generate_config.py {' '.join(args)}"
        success, stdout, stderr = self.run_command(cmd)
        
        if success:
            print(f"✅ Config generated: {output_name}")
            return True
        else:
            print(f"❌ Config generation failed: {stderr}")
            return False
    
    def start_containers(self) -> bool:
        """Start Docker containers"""
        print("\n🐳 Starting Docker containers...")
        
        # Stop any existing containers
        self.run_command("docker compose -f docker-compose.test-mount.yml down", check_error=False)
        
        # Start containers
        success, stdout, stderr = self.run_command("docker compose -f docker-compose.test-mount.yml up -d")
        
        if success:
            print("✅ Containers started")
            time.sleep(5)  # Wait for containers to start
            return True
        else:
            print(f"❌ Failed to start containers: {stderr}")
            return False
    
    def stop_containers(self) -> bool:
        """Stop Docker containers"""
        print("\n🛑 Stopping Docker containers...")
        success, stdout, stderr = self.run_command("docker compose -f docker-compose.test-mount.yml down")
        
        if success:
            print("✅ Containers stopped")
            return True
        else:
            print(f"❌ Failed to stop containers: {stderr}")
            return False
    
    def restart_server_with_config(self, config_file: str, port: int) -> bool:
        """Restart server with new configuration"""
        print(f"\n🔄 Restarting server with {config_file} on port {port}")
        
        # Update server command
        cmd = f"""
        docker compose -f docker-compose.test-mount.yml exec mcp-test-server python mcp_proxy_adapter/examples/full_application/main.py --config {config_file} --port {port}
        """
        
        # Stop current server
        self.run_command("docker compose -f docker-compose.test-mount.yml exec mcp-test-server pkill -f main.py", check_error=False)
        time.sleep(2)
        
        # Start new server in background
        success, stdout, stderr = self.run_command(cmd + " &", check_error=False)
        time.sleep(5)  # Wait for server to start
        
        if success:
            print(f"✅ Server restarted with {config_file}")
            return True
        else:
            print(f"❌ Failed to restart server: {stderr}")
            return False
    
    def test_health_endpoint(self, protocol: str, port: int, token: str = None) -> bool:
        """Test health endpoint"""
        print(f"🔍 Testing health endpoint on {protocol}://localhost:{port}")
        
        url = f"{protocol}://localhost:{port}/health"
        headers = {}
        if token:
            headers['X-API-Key'] = token
        
        if protocol == "https" or protocol == "mtls":
            # Use curl with certificates for HTTPS/mTLS
            cert_args = ""
            if protocol == "mtls":
                cert_args = f"--cert {self.ca_dir}/../client/test-client.crt --key {self.ca_dir}/../client/test-client.key"
            
            cmd = f"curl -k {cert_args} {url}"
        else:
            cmd = f"curl {url}"
        
        success, stdout, stderr = self.run_command(cmd)
        
        if success and "status" in stdout and "ok" in stdout:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {stdout}")
            return False
    
    def test_jsonrpc_endpoint(self, protocol: str, port: int, message: str, token: str = None) -> bool:
        """Test JSON-RPC endpoint"""
        print(f"🔍 Testing JSON-RPC endpoint on {protocol}://localhost:{port}")
        
        url = f"{protocol}://localhost:{port}/api/jsonrpc"
        headers = {"Content-Type": "application/json"}
        if token:
            headers['X-API-Key'] = token
        
        data = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"message": message},
            "id": 1
        }
        
        if protocol == "https" or protocol == "mtls":
            # Use curl with certificates for HTTPS/mTLS
            cert_args = ""
            if protocol == "mtls":
                cert_args = f"--cert {self.ca_dir}/../client/test-client.crt --key {self.ca_dir}/../client/test-client.key"
            
            cmd = f"curl -k {cert_args} -X POST -H 'Content-Type: application/json' -d '{json.dumps(data)}' {url}"
        else:
            cmd = f"curl -X POST -H 'Content-Type: application/json' -d '{json.dumps(data)}' {url}"
        
        success, stdout, stderr = self.run_command(cmd)
        
        if success and "result" in stdout and "success" in stdout:
            print("✅ JSON-RPC endpoint working")
            return True
        else:
            print(f"❌ JSON-RPC endpoint failed: {stdout}")
            return False
    
    def test_proxy_registration(self) -> bool:
        """Test proxy registration"""
        print("🔍 Testing proxy registration...")
        
        success, stdout, stderr = self.run_command("curl -s http://localhost:3005/proxy/list")
        
        if success and "mcp_proxy_adapter" in stdout:
            print("✅ Proxy registration working")
            return True
        else:
            print(f"❌ Proxy registration failed: {stdout}")
            return False
    
    async def test_with_universal_client(self, config_file: str) -> bool:
        """Test using UniversalClient"""
        print(f"🔍 Testing with UniversalClient: {config_file}")
        
        try:
            client = create_client_from_config(str(self.test_dir / config_file))
            
            async with client:
                # Test connection
                success = await client.test_connection()
                
                if success:
                    print("✅ UniversalClient connection successful")
                    
                    # Test echo command
                    result = await client.execute_command("echo", {"message": "Hello from UniversalClient"})
                    
                    if "result" in result and "success" in result.get("result", {}):
                        print("✅ UniversalClient echo command successful")
                        return True
                    else:
                        print(f"❌ UniversalClient echo failed: {result}")
                        return False
                else:
                    print("❌ UniversalClient connection failed")
                    return False
                    
        except Exception as e:
            print(f"❌ UniversalClient test failed: {e}")
            return False
    
    def test_mode(self, mode_name: str, protocol: str, token: bool, roles: bool, port: int) -> Dict[str, Any]:
        """Test a specific mode"""
        print(f"\n{'='*60}")
        print(f"🧪 Testing {mode_name}")
        print(f"   Protocol: {protocol}")
        print(f"   Token: {token}")
        print(f"   Roles: {roles}")
        print(f"   Port: {port}")
        print(f"{'='*60}")
        
        # Generate config
        config_name = f"{mode_name.lower().replace(' ', '_').replace('+', '_')}.json"
        if not self.generate_config(protocol, token, roles, config_name, port):
            return {"status": "FAIL", "error": "Config generation failed"}
        
        # Restart server with new config
        if not self.restart_server_with_config(f"/app/test_configs/{config_name}", port):
            return {"status": "FAIL", "error": "Server restart failed"}
        
        # Test health endpoint
        token_value = "admin-secret-key" if token else None
        if not self.test_health_endpoint(protocol, port, token_value):
            return {"status": "FAIL", "error": "Health endpoint failed"}
        
        # Test JSON-RPC endpoint
        if not self.test_jsonrpc_endpoint(protocol, port, f"Hello {mode_name}", token_value):
            return {"status": "FAIL", "error": "JSON-RPC endpoint failed"}
        
        # Test proxy registration
        if not self.test_proxy_registration():
            return {"status": "FAIL", "error": "Proxy registration failed"}
        
        return {"status": "PASS", "message": f"{mode_name} mode working correctly"}
    
    async def run_all_tests(self):
        """Run all 8 mode tests"""
        print("🚀 Starting Docker-based comprehensive testing")
        print("="*80)
        
        # Start containers
        if not self.start_containers():
            print("❌ Failed to start containers")
            return
        
        try:
            # Define all 8 modes
            modes = [
                ("HTTP Basic", "http", False, False, 8000),
                ("HTTP + Token", "http", True, False, 8001),
                ("HTTP + Token + Roles", "http", True, True, 8002),
                ("HTTPS Basic", "https", False, False, 8003),
                ("HTTPS + Token", "https", True, False, 8004),
                ("HTTPS + Token + Roles", "https", True, True, 8005),
                ("mTLS Basic", "mtls", False, False, 8006),
                ("mTLS + Token + Roles", "mtls", True, True, 8007),
            ]
            
            # Test each mode
            for mode_name, protocol, token, roles, port in modes:
                result = self.test_mode(mode_name, protocol, token, roles, port)
                self.results[mode_name] = result
                
                if result["status"] == "PASS":
                    print(f"✅ {mode_name} - PASSED")
                else:
                    print(f"❌ {mode_name} - FAILED: {result.get('error', 'Unknown error')}")
                
                # Small delay between tests
                time.sleep(2)
            
            # Test UniversalClient for mTLS mode
            print(f"\n{'='*60}")
            print("🧪 Testing UniversalClient with mTLS")
            print(f"{'='*60}")
            
            mtls_config = "mTLS + Token + Roles".lower().replace(' ', '_').replace('+', '_') + ".json"
            client_success = await self.test_with_universal_client(mtls_config)
            
            if client_success:
                print("✅ UniversalClient test - PASSED")
            else:
                print("❌ UniversalClient test - FAILED")
            
            # Print summary
            self.print_summary()
            
        finally:
            # Stop containers
            self.stop_containers()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 DOCKER TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result["status"] == "PASS")
        
        for mode_name, result in self.results.items():
            status = "✅ PASS" if result["status"] == "PASS" else "❌ FAIL"
            print(f"{status}: {mode_name}")
            if result["status"] == "FAIL":
                print(f"    Error: {result.get('error', 'Unknown error')}")
        
        print(f"\n🎯 FINAL SCORE: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! All 8 modes working correctly!")
        else:
            print("⚠️  Some tests failed. Check the details above.")


async def main():
    """Main test function"""
    tester = DockerModeTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
