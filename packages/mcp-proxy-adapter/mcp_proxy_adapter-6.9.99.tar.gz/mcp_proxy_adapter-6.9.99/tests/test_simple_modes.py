#!/usr/bin/env python3
"""
Simple mode testing script
Tests all 8 modes sequentially without Docker

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


class SimpleModeTester:
    """Test all 8 modes using simple approach"""
    
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
                timeout=30
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
        args.extend(["--proxy-registration", "--proxy-url", "http://localhost:3005"])
        
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
    
    def start_proxy(self) -> bool:
        """Start proxy server"""
        print("\n🚀 Starting proxy server...")
        
        # Stop any existing proxy
        self.run_command("pkill -f 'run_proxy_server.py'", check_error=False)
        time.sleep(2)
        
        # Start proxy
        success, stdout, stderr = self.run_command("nohup python mcp_proxy_adapter/examples/run_proxy_server.py --host 0.0.0.0 --port 3005 > logs/proxy.log 2>&1 &")
        
        if success:
            print("✅ Proxy started")
            time.sleep(3)  # Wait for proxy to start
            return True
        else:
            print(f"❌ Failed to start proxy: {stderr}")
            return False
    
    def test_config_validation(self, config_file: str) -> bool:
        """Test configuration validation"""
        print(f"🔍 Validating config: {config_file}")
        
        try:
            with open(self.test_dir / config_file, 'r') as f:
                config = json.load(f)
            
            # Check basic structure
            required_sections = ["server", "ssl", "transport", "proxy_registration"]
            missing_sections = [s for s in required_sections if s not in config]
            
            if missing_sections:
                print(f"❌ Missing sections: {missing_sections}")
                return False
            
            # Check protocol consistency
            server_protocol = config["server"]["protocol"]
            transport_type = config["transport"]["type"]
            
            if server_protocol == "http" and transport_type == "http":
                print("✅ HTTP config valid")
                return True
            elif server_protocol in ["https", "mtls"] and transport_type == "https":
                print("✅ HTTPS/mTLS config valid")
                return True
            else:
                print(f"❌ Protocol mismatch: server={server_protocol}, transport={transport_type}")
                return False
            
        except Exception as e:
            print(f"❌ Config validation failed: {e}")
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
        config_name = f"{mode_name.lower().replace(' ', '_').replace('+', '_')}"
        if not self.generate_config(protocol, token, roles, config_name, port):
            return {"status": "FAIL", "error": "Config generation failed"}
        
        # Validate config (generator adds .json automatically)
        config_file = f"{config_name}.json"
        if not self.test_config_validation(config_file):
            return {"status": "FAIL", "error": "Config validation failed"}
        
        return {"status": "PASS", "message": f"{mode_name} config generated and validated successfully"}
    
    async def run_all_tests(self):
        """Run all 8 mode tests"""
        print("🚀 Starting Simple Mode Testing")
        print("="*80)
        
        # Start proxy
        if not self.start_proxy():
            print("❌ Failed to start proxy")
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
                time.sleep(1)
            
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
            # Stop proxy
            self.run_command("pkill -f 'run_proxy_server.py'", check_error=False)
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 SIMPLE MODE TESTING SUMMARY")
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
    tester = SimpleModeTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())