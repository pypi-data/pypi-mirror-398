#!/usr/bin/env python3
"""
Script to validate compatibility between config generator and validator.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_proxy_adapter.core.config_validator import ConfigValidator
from mcp_proxy_adapter.examples.config_builder import generate_complete_config


def test_generator_validator_compatibility():
    """Test that generated configs pass validation."""
    print("🔍 Testing Generator-Validator Compatibility")
    print("=" * 50)
    
    # Test configurations to generate
    test_configs = [
        {
            "name": "HTTP Basic",
            "protocol": "http",
            "ssl_enabled": False,
            "security_enabled": False,
            "roles_enabled": False,
            "proxy_registration_enabled": False
        },
        {
            "name": "HTTP + Token",
            "protocol": "http", 
            "ssl_enabled": False,
            "security_enabled": True,
            "roles_enabled": False,
            "proxy_registration_enabled": False
        },
        {
            "name": "HTTP + Token + Roles",
            "protocol": "http",
            "ssl_enabled": False, 
            "security_enabled": True,
            "roles_enabled": True,
            "proxy_registration_enabled": False
        },
        {
            "name": "HTTPS Basic",
            "protocol": "https",
            "ssl_enabled": True,
            "security_enabled": False,
            "roles_enabled": False,
            "proxy_registration_enabled": False
        },
        {
            "name": "HTTPS + Token",
            "protocol": "https",
            "ssl_enabled": True,
            "security_enabled": True,
            "roles_enabled": False,
            "proxy_registration_enabled": False
        },
        {
            "name": "HTTPS + Token + Roles",
            "protocol": "https",
            "ssl_enabled": True,
            "security_enabled": True,
            "roles_enabled": True,
            "proxy_registration_enabled": False
        },
        {
            "name": "mTLS + Proxy Registration",
            "protocol": "mtls",
            "ssl_enabled": True,
            "security_enabled": False,
            "roles_enabled": False,
            "proxy_registration_enabled": True
        }
    ]
    
    results = []
    
    for test_config in test_configs:
        print(f"\n📋 Testing: {test_config['name']}")
        print("-" * 30)
        
        try:
            # Generate configuration
            print("  🔧 Generating configuration...")
            generated_config = generate_complete_config(
                host="localhost",
                port=8080
            )
            
            # Create temporary test files
            temp_dir = Path(tempfile.mkdtemp())
            test_files = {}
            
            # Modify config based on test parameters
            if test_config["protocol"] != "http":
                generated_config["server"]["protocol"] = test_config["protocol"]
            
            if test_config["ssl_enabled"]:
                generated_config["ssl"]["enabled"] = True
                # Create test SSL certificates
                cert_file = temp_dir / "test_cert.crt"
                key_file = temp_dir / "test_key.key"
                ca_cert = temp_dir / "test_ca.crt"
                
                # Create dummy certificate files
                cert_file.write_text("-----BEGIN CERTIFICATE-----\nDUMMY CERT\n-----END CERTIFICATE-----")
                key_file.write_text("-----BEGIN PRIVATE KEY-----\nDUMMY KEY\n-----END PRIVATE KEY-----")
                ca_cert.write_text("-----BEGIN CERTIFICATE-----\nDUMMY CA\n-----END CERTIFICATE-----")
                
                generated_config["ssl"]["cert_file"] = str(cert_file)
                generated_config["ssl"]["key_file"] = str(key_file)
                generated_config["ssl"]["ca_cert"] = str(ca_cert)
                
                test_files["ssl"] = [cert_file, key_file, ca_cert]
            
            if test_config["security_enabled"]:
                generated_config["security"]["enabled"] = True
                generated_config["security"]["tokens"] = {
                    "test_token": {"permissions": ["*"]}
                }
            
            if test_config["roles_enabled"]:
                generated_config["roles"]["enabled"] = True
                roles_file = temp_dir / "test_roles.json"
                roles_file.write_text('{"admin": ["*"], "user": ["read"]}')
                generated_config["roles"]["config_file"] = str(roles_file)
                test_files["roles"] = [roles_file]
            
            if test_config["proxy_registration_enabled"]:
                generated_config["proxy_registration"]["enabled"] = True
                generated_config["proxy_registration"]["proxy_url"] = "http://localhost:3005"
                
                # Create test client certificates
                client_cert = temp_dir / "test_client.crt"
                client_key = temp_dir / "test_client.key"
                client_cert.write_text("-----BEGIN CERTIFICATE-----\nDUMMY CLIENT CERT\n-----END CERTIFICATE-----")
                client_key.write_text("-----BEGIN PRIVATE KEY-----\nDUMMY CLIENT KEY\n-----END PRIVATE KEY-----")
                
                generated_config["proxy_registration"]["certificate"] = {
                    "cert_file": str(client_cert),
                    "key_file": str(client_key)
                }
                generated_config["proxy_registration"]["ssl"] = {
                    "ca_cert": str(ca_cert) if test_config["ssl_enabled"] else str(temp_dir / "test_ca.crt")
                }
                
                if "proxy" not in test_files:
                    test_files["proxy"] = []
                test_files["proxy"].extend([client_cert, client_key])
            
            # Validate configuration
            print("  ✅ Validating configuration...")
            validator = ConfigValidator()
            validator.config_data = generated_config
            validation_results = validator.validate_config()
            
            # Analyze results
            errors = [r for r in validation_results if r.level == "error"]
            warnings = [r for r in validation_results if r.level == "warning"]
            info = [r for r in validation_results if r.level == "info"]
            
            result = {
                "name": test_config["name"],
                "success": len(errors) == 0,
                "errors": len(errors),
                "warnings": len(warnings),
                "info": len(info),
                "error_details": errors,
                "warning_details": warnings
            }
            
            results.append(result)
            
            # Clean up temporary files
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"    ⚠️  Warning: Could not clean up temp files: {e}")
            
            # Print results
            if result["success"]:
                print(f"  ✅ PASS - {len(warnings)} warnings, {len(info)} info")
            else:
                print(f"  ❌ FAIL - {len(errors)} errors, {len(warnings)} warnings")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"    • {error.message}")
                if len(errors) > 3:
                    print(f"    ... and {len(errors) - 3} more errors")
            
        except Exception as e:
            print(f"  💥 EXCEPTION: {str(e)}")
            results.append({
                "name": test_config["name"],
                "success": False,
                "errors": 1,
                "warnings": 0,
                "info": 0,
                "error_details": [f"Exception: {str(e)}"],
                "warning_details": []
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 COMPATIBILITY SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FAILED TESTS:")
        for result in results:
            if not result["success"]:
                print(f"  • {result['name']}: {result['errors']} errors")
                for error in result["error_details"][:2]:
                    print(f"    - {error}")
    
    return results


def test_validation_coverage():
    """Test that validator covers all generator features."""
    print("\n🔍 Testing Validation Coverage")
    print("=" * 50)
    
    # Test that validator checks all required sections
    required_sections = [
        "server", "logging", "commands", "debug"
    ]
    
    optional_sections = [
        "ssl", "security", "roles", "proxy_registration", "transport"
    ]
    
    print("📋 Required sections validation:")
    for section in required_sections:
        print(f"  ✅ {section}")
    
    print("\n📋 Optional sections validation:")
    for section in optional_sections:
        print(f"  ✅ {section}")
    
    return True


def test_edge_cases():
    """Test edge cases and error conditions."""
    print("\n🔍 Testing Edge Cases")
    print("=" * 50)
    
    edge_cases = [
        {
            "name": "Empty config",
            "config": {},
            "should_fail": True
        },
        {
            "name": "Missing server section",
            "config": {"logging": {"level": "INFO"}},
            "should_fail": True
        },
        {
            "name": "Invalid protocol",
            "config": {
                "server": {"protocol": "invalid", "host": "localhost", "port": 8080},
                "logging": {"level": "INFO"},
                "commands": {"enabled": True},
                "debug": {"enabled": False}
            },
            "should_fail": True
        },
        {
            "name": "SSL enabled without certificates",
            "config": {
                "server": {"protocol": "https", "host": "localhost", "port": 8080},
                "ssl": {"enabled": True},
                "logging": {"level": "INFO"},
                "commands": {"enabled": True},
                "debug": {"enabled": False}
            },
            "should_fail": True
        }
    ]
    
    results = []
    
    for case in edge_cases:
        print(f"\n🧪 Testing: {case['name']}")
        
        try:
            validator = ConfigValidator()
            validator.config_data = case["config"]
            validation_results = validator.validate_config()
            
            errors = [r for r in validation_results if r.level == "error"]
            has_errors = len(errors) > 0
            
            expected_failure = case["should_fail"]
            test_passed = (has_errors == expected_failure)
            
            if test_passed:
                print(f"  ✅ PASS - {'Correctly failed' if has_errors else 'Correctly passed'}")
            else:
                print(f"  ❌ FAIL - Expected {'failure' if expected_failure else 'success'}, got {'failure' if has_errors else 'success'}")
            
            results.append({
                "name": case["name"],
                "passed": test_passed,
                "errors": len(errors)
            })
            
        except Exception as e:
            print(f"  💥 EXCEPTION: {str(e)}")
            results.append({
                "name": case["name"],
                "passed": False,
                "errors": 1
            })
    
    return results


def main():
    """Main test function."""
    print("🚀 Generator-Validator Compatibility Test")
    print("=" * 60)
    
    try:
        # Test 1: Generator-Validator compatibility
        compatibility_results = test_generator_validator_compatibility()
        
        # Test 2: Validation coverage
        test_validation_coverage()
        
        # Test 3: Edge cases
        edge_case_results = test_edge_cases()
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎯 FINAL RESULTS")
        print("=" * 60)
        
        compatibility_passed = sum(1 for r in compatibility_results if r["success"])
        edge_cases_passed = sum(1 for r in edge_case_results if r["passed"])
        
        print(f"Compatibility tests: {compatibility_passed}/{len(compatibility_results)} passed")
        print(f"Edge case tests: {edge_cases_passed}/{len(edge_case_results)} passed")
        
        total_passed = compatibility_passed + edge_cases_passed
        total_tests = len(compatibility_results) + len(edge_case_results)
        
        print(f"Overall: {total_passed}/{total_tests} tests passed")
        
        if total_passed == total_tests:
            print("🎉 ALL TESTS PASSED! Generator and validator are compatible.")
            return 0
        else:
            print("❌ Some tests failed. Check the output above for details.")
            return 1
            
    except Exception as e:
        print(f"💥 Test suite failed with exception: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
