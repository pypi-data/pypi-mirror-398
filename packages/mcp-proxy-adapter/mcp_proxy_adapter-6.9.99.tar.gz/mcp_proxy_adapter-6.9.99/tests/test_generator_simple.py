#!/usr/bin/env python3
"""
Simple Generator Testing Script
Tests the generate_config.py script without CLI dependencies

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple


class SimpleGeneratorTester:
    """Test the configuration generator for all modes"""
    
    def __init__(self):
        self.test_dir = Path("./test_generator_configs")
        self.cert_dir = "./mtls_certificates/server"
        self.key_dir = "./mtls_certificates/server"
        self.ca_dir = "./mtls_certificates/ca"
        self.results = {}
        
        # Ensure test directory exists
        self.test_dir.mkdir(exist_ok=True)
    
    def run_generator_command(self, args: List[str]) -> Tuple[bool, str, str]:
        """Run the generator command and return success, stdout, stderr"""
        cmd = ["python", "mcp_proxy_adapter/examples/generate_config.py"] + args
        print(f"🔧 Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def test_generator_validation(self) -> Dict[str, Any]:
        """Test that generator validates input parameters correctly"""
        print("\n" + "="*60)
        print("🧪 TESTING GENERATOR VALIDATION")
        print("="*60)
        
        validation_tests = {
            "missing_protocol": {
                "args": ["--token", "--proxy-registration"],
                "should_fail": True,
                "description": "Missing required --protocol parameter"
            },
            "missing_proxy_url": {
                "args": ["--protocol", "http", "--proxy-registration"],
                "should_fail": True,
                "description": "Missing --proxy-url when --proxy-registration enabled"
            },
            "invalid_protocol": {
                "args": ["--protocol", "invalid", "--token"],
                "should_fail": True,
                "description": "Invalid protocol value"
            },
            "valid_http": {
                "args": ["--protocol", "http", "--token", "--proxy-registration", "--proxy-url", "http://localhost:3005"],
                "should_fail": False,
                "description": "Valid HTTP configuration"
            },
            "valid_https": {
                "args": ["--protocol", "https", "--token", "--proxy-registration", "--proxy-url", "https://localhost:3005", "--cert-dir", self.cert_dir, "--key-dir", self.key_dir],
                "should_fail": False,
                "description": "Valid HTTPS configuration"
            },
            "valid_mtls": {
                "args": ["--protocol", "mtls", "--token", "--roles", "--proxy-registration", "--proxy-url", "https://localhost:3005", "--cert-dir", self.cert_dir, "--key-dir", self.key_dir],
                "should_fail": False,
                "description": "Valid mTLS configuration"
            }
        }
        
        results = {}
        for test_name, test_config in validation_tests.items():
            print(f"\n🔍 Testing: {test_config['description']}")
            success, stdout, stderr = self.run_generator_command(test_config["args"])
            
            expected_failure = test_config["should_fail"]
            actual_failure = not success
            
            if expected_failure == actual_failure:
                status = "✅ PASS"
                if expected_failure:
                    print(f"   Expected failure: {stderr.strip()}")
                else:
                    print(f"   Generated config successfully")
            else:
                status = "❌ FAIL"
                if expected_failure and success:
                    print(f"   Expected failure but succeeded: {stdout}")
                else:
                    print(f"   Expected success but failed: {stderr}")
            
            results[test_name] = {
                "status": status,
                "expected_failure": expected_failure,
                "actual_failure": actual_failure,
                "stdout": stdout,
                "stderr": stderr
            }
        
        return results
    
    def test_all_modes_generation(self) -> Dict[str, Any]:
        """Test generation of all 8 modes"""
        print("\n" + "="*60)
        print("🧪 TESTING ALL MODES GENERATION")
        print("="*60)
        
        modes = [
            # (protocol, token, roles, description)
            ("http", False, False, "HTTP Basic"),
            ("http", True, False, "HTTP + Token"),
            ("http", True, True, "HTTP + Token + Roles"),
            ("https", False, False, "HTTPS Basic"),
            ("https", True, False, "HTTPS + Token"),
            ("https", True, True, "HTTPS + Token + Roles"),
            ("mtls", False, False, "mTLS Basic"),
            ("mtls", True, True, "mTLS + Token + Roles"),
        ]
        
        results = {}
        for protocol, token, roles, description in modes:
            print(f"\n🔍 Testing: {description}")
            
            # Build command arguments
            args = ["--protocol", protocol]
            if token:
                args.append("--token")
            if roles:
                args.append("--roles")
            
            # Add proxy registration
            args.extend(["--proxy-registration", "--proxy-url", f"https://localhost:3005"])
            
            # Add SSL config for https/mtls
            if protocol in ["https", "mtls"]:
                args.extend(["--cert-dir", self.cert_dir, "--key-dir", self.key_dir])
            
            # Add output
            output_name = f"{protocol}_{'token' if token else 'basic'}{'_roles' if roles else ''}"
            args.extend(["--output", output_name, "--output-dir", str(self.test_dir)])
            
            success, stdout, stderr = self.run_generator_command(args)
            
            if success:
                config_file = self.test_dir / f"{output_name}.json"
                if config_file.exists():
                    # Validate generated config
                    try:
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                        
                        # Check basic structure
                        required_sections = ["server", "ssl", "transport", "proxy_registration"]
                        missing_sections = [s for s in required_sections if s not in config]
                        
                        if missing_sections:
                            status = "❌ FAIL - Missing sections"
                            print(f"   Missing sections: {missing_sections}")
                        else:
                            # Check protocol consistency
                            server_protocol = config["server"]["protocol"]
                            transport_type = config["transport"]["type"]
                            
                            if protocol == "http" and server_protocol == "http" and transport_type == "http":
                                status = "✅ PASS"
                            elif protocol in ["https", "mtls"] and server_protocol == protocol and transport_type == "https":
                                status = "✅ PASS"
                            else:
                                status = "❌ FAIL - Protocol mismatch"
                                print(f"   Server: {server_protocol}, Transport: {transport_type}")
                    except Exception as e:
                        status = f"❌ FAIL - Invalid JSON: {e}"
                        print(f"   JSON Error: {e}")
                else:
                    status = "❌ FAIL - Config file not created"
                    print(f"   Config file not found: {config_file}")
            else:
                status = "❌ FAIL - Generation failed"
                print(f"   Generation error: {stderr}")
            
            results[output_name] = {
                "status": status,
                "success": success,
                "stdout": stdout,
                "stderr": stderr
            }
        
        return results
    
    def test_mtls_specific(self) -> Dict[str, Any]:
        """Test mTLS specific configuration"""
        print("\n" + "="*60)
        print("🧪 TESTING mTLS SPECIFIC CONFIGURATION")
        print("="*60)
        
        # Test mTLS config generation
        args = [
            "--protocol", "mtls",
            "--token", "--roles",
            "--proxy-registration", "--proxy-url", "https://localhost:3005",
            "--cert-dir", self.cert_dir,
            "--key-dir", self.key_dir,
            "--output", "mtls_test",
            "--output-dir", str(self.test_dir)
        ]
        
        success, stdout, stderr = self.run_generator_command(args)
        
        if not success:
            return {"mtls_generation": {"status": "❌ FAIL", "error": stderr}}
        
        # Check mTLS specific settings
        config_file = self.test_dir / "mtls_test.json"
        if not config_file.exists():
            return {"mtls_generation": {"status": "❌ FAIL", "error": "Config file not created"}}
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check mTLS specific requirements
            checks = {
                "ssl_enabled": config.get("ssl", {}).get("enabled", False),
                "transport_https": config.get("transport", {}).get("type") == "https",
                "verify_client": config.get("transport", {}).get("verify_client", False),
                "chk_hostname_false": config.get("transport", {}).get("chk_hostname", True) == False,
                "ca_cert_present": "ca_cert" in config.get("ssl", {}),
                "cert_file_present": "cert_file" in config.get("ssl", {}),
                "key_file_present": "key_file" in config.get("ssl", {}),
            }
            
            all_passed = all(checks.values())
            status = "✅ PASS" if all_passed else "❌ FAIL"
            
            print(f"   SSL enabled: {checks['ssl_enabled']}")
            print(f"   Transport HTTPS: {checks['transport_https']}")
            print(f"   Verify client: {checks['verify_client']}")
            print(f"   Check hostname false: {checks['chk_hostname_false']}")
            print(f"   CA cert present: {checks['ca_cert_present']}")
            print(f"   Cert file present: {checks['cert_file_present']}")
            print(f"   Key file present: {checks['key_file_present']}")
            
            return {
                "mtls_generation": {
                    "status": status,
                    "checks": checks,
                    "all_passed": all_passed
                }
            }
            
        except Exception as e:
            return {"mtls_generation": {"status": f"❌ FAIL - {e}", "error": str(e)}}
    
    def test_certificate_paths(self) -> Dict[str, Any]:
        """Test that certificate paths are correctly set"""
        print("\n" + "="*60)
        print("🧪 TESTING CERTIFICATE PATHS")
        print("="*60)
        
        # Test HTTPS config
        args = [
            "--protocol", "https",
            "--proxy-registration", "--proxy-url", "https://localhost:3005",
            "--cert-dir", self.cert_dir,
            "--key-dir", self.key_dir,
            "--output", "https_cert_test",
            "--output-dir", str(self.test_dir)
        ]
        
        success, stdout, stderr = self.run_generator_command(args)
        
        if not success:
            return {"cert_paths": {"status": "❌ FAIL", "error": stderr}}
        
        config_file = self.test_dir / "https_cert_test.json"
        if not config_file.exists():
            return {"cert_paths": {"status": "❌ FAIL", "error": "Config file not created"}}
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            ssl_config = config.get("ssl", {})
            expected_cert = f"{self.cert_dir}/mcp-proxy.crt"
            expected_key = f"{self.key_dir}/mcp-proxy.key"
            
            checks = {
                "cert_file_correct": ssl_config.get("cert_file") == expected_cert,
                "key_file_correct": ssl_config.get("key_file") == expected_key,
                "ssl_enabled": ssl_config.get("enabled", False),
            }
            
            all_passed = all(checks.values())
            status = "✅ PASS" if all_passed else "❌ FAIL"
            
            print(f"   Cert file: {ssl_config.get('cert_file')} (expected: {expected_cert})")
            print(f"   Key file: {ssl_config.get('key_file')} (expected: {expected_key})")
            print(f"   SSL enabled: {ssl_config.get('enabled')}")
            
            return {
                "cert_paths": {
                    "status": status,
                    "checks": checks,
                    "all_passed": all_passed
                }
            }
            
        except Exception as e:
            return {"cert_paths": {"status": f"❌ FAIL - {e}", "error": str(e)}}
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 GENERATOR TESTING SUMMARY")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        for test_category, results in self.results.items():
            print(f"\n{test_category.upper()}:")
            for test_name, result in results.items():
                status = result.get("status", "UNKNOWN")
                print(f"  {status}: {test_name}")
                total_tests += 1
                if "✅ PASS" in status:
                    passed_tests += 1
        
        print(f"\n🎯 FINAL SCORE: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Generator is working correctly!")
        else:
            print("⚠️  Some tests failed. Check the details above.")
    
    def run_all_tests(self):
        """Run all generator tests"""
        print("🚀 Starting Simple Generator Testing")
        print("="*80)
        
        # Test 1: Generator validation
        self.results["validation"] = self.test_generator_validation()
        
        # Test 2: All modes generation
        self.results["generation"] = self.test_all_modes_generation()
        
        # Test 3: mTLS specific
        self.results["mtls"] = self.test_mtls_specific()
        
        # Test 4: Certificate paths
        self.results["cert_paths"] = self.test_certificate_paths()
        
        # Print summary
        self.print_summary()


def main():
    """Main test function"""
    tester = SimpleGeneratorTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
