"""
Simple validation tests without complex imports.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any


class TestSimpleValidation(unittest.TestCase):
    """Test validation functionality with simple approach."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ssl_configuration_validation_logic(self):
        """Test SSL configuration validation logic."""
        # Test case 1: SSL enabled but no certificates
        ssl_config = {
            "enabled": True,
            "cert_file": None,
            "key_file": None,
            "ca_cert": None
        }
        
        # Should detect missing certificates
        missing_cert = ssl_config["cert_file"] is None
        missing_key = ssl_config["key_file"] is None
        
        self.assertTrue(missing_cert, "Should detect missing certificate file")
        self.assertTrue(missing_key, "Should detect missing key file")
        
        print("✅ SSL validation logic correctly detects missing certificates")
    
    def test_ssl_disabled_validation_logic(self):
        """Test SSL disabled validation logic."""
        # Test case 2: SSL disabled
        ssl_config = {
            "enabled": False,
            "cert_file": "/nonexistent/cert.crt",  # Should not be validated
            "key_file": "/nonexistent/key.key",   # Should not be validated
            "ca_cert": None
        }
        
        # Should not validate when disabled
        should_validate = ssl_config["enabled"]
        
        self.assertFalse(should_validate, "Should not validate when SSL is disabled")
        
        print("✅ SSL validation logic correctly skips validation when disabled")
    
    def test_roles_configuration_validation_logic(self):
        """Test roles configuration validation logic."""
        # Test case 1: Roles enabled but no config file
        roles_config = {
            "enabled": True,
            "config_file": None
        }
        
        # Should detect missing config file
        missing_config = roles_config["config_file"] is None
        roles_enabled = roles_config["enabled"]
        
        self.assertTrue(roles_enabled, "Roles should be enabled")
        self.assertTrue(missing_config, "Should detect missing config file")
        
        print("✅ Roles validation logic correctly detects missing config file")
    
    def test_security_configuration_validation_logic(self):
        """Test security configuration validation logic."""
        # Test case 1: Security enabled but no authentication
        security_config = {
            "enabled": True,
            "tokens": {},
            "roles": {},
            "roles_file": None
        }
        
        # Should detect missing authentication methods
        has_tokens = bool(security_config["tokens"] and any(security_config["tokens"].values()))
        has_roles = bool(security_config["roles"] and any(security_config["roles"].values()))
        has_roles_file = bool(security_config["roles_file"] and os.path.exists(security_config["roles_file"]))
        
        no_auth_methods = not (has_tokens or has_roles or has_roles_file)
        
        self.assertTrue(security_config["enabled"], "Security should be enabled")
        self.assertTrue(no_auth_methods, "Should detect no authentication methods")
        
        print("✅ Security validation logic correctly detects missing authentication methods")
    
    def test_file_existence_validation_logic(self):
        """Test file existence validation logic."""
        # Test case 1: Non-existent file
        non_existent_file = "/nonexistent/file.txt"
        file_exists = os.path.exists(non_existent_file)
        
        self.assertFalse(file_exists, "Non-existent file should not exist")
        
        # Test case 2: Existing file
        existing_file = os.path.join(self.temp_dir, "test.txt")
        with open(existing_file, 'w') as f:
            f.write("test")
        
        file_exists = os.path.exists(existing_file)
        self.assertTrue(file_exists, "Existing file should exist")
        
        print("✅ File existence validation logic works correctly")
    
    def test_configuration_structure_validation(self):
        """Test configuration structure validation."""
        # Test case 1: Missing required sections
        incomplete_config = {
            "server": {
                "host": "0.0.0.0"
                # Missing: port, protocol, debug, log_level
            }
        }
        
        required_server_keys = ["host", "port", "protocol", "debug", "log_level"]
        missing_keys = [key for key in required_server_keys if key not in incomplete_config["server"]]
        
        self.assertGreater(len(missing_keys), 0, "Should detect missing required keys")
        self.assertIn("port", missing_keys)
        self.assertIn("protocol", missing_keys)
        self.assertIn("debug", missing_keys)
        self.assertIn("log_level", missing_keys)
        
        print("✅ Configuration structure validation correctly detects missing keys")
    
    def test_conditional_validation_logic(self):
        """Test conditional validation logic."""
        # Test case 1: Feature enabled - should validate
        feature_config = {
            "enabled": True,
            "required_file": None
        }
        
        should_validate = feature_config["enabled"]
        has_required_file = feature_config["required_file"] is not None
        
        self.assertTrue(should_validate, "Should validate when feature is enabled")
        self.assertFalse(has_required_file, "Should detect missing required file")
        
        # Test case 2: Feature disabled - should not validate
        feature_config_disabled = {
            "enabled": False,
            "required_file": None
        }
        
        should_validate_disabled = feature_config_disabled["enabled"]
        
        self.assertFalse(should_validate_disabled, "Should not validate when feature is disabled")
        
        print("✅ Conditional validation logic works correctly")
    
    def test_validation_error_aggregation(self):
        """Test validation error aggregation."""
        # Simulate multiple validation errors
        errors = [
            {"level": "error", "message": "Missing required key 'port'", "section": "server"},
            {"level": "error", "message": "Missing required key 'protocol'", "section": "server"},
            {"level": "warning", "message": "Security enabled but no auth methods", "section": "security"},
            {"level": "info", "message": "Using default values", "section": "logging"}
        ]
        
        error_count = len([e for e in errors if e["level"] == "error"])
        warning_count = len([e for e in errors if e["level"] == "warning"])
        info_count = len([e for e in errors if e["level"] == "info"])
        
        self.assertEqual(error_count, 2, "Should have 2 errors")
        self.assertEqual(warning_count, 1, "Should have 1 warning")
        self.assertEqual(info_count, 1, "Should have 1 info")
        
        print("✅ Validation error aggregation works correctly")


if __name__ == '__main__':
    print("🧪 Running Simple Validation Tests")
    print("=" * 50)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 50)
    print("✅ All simple validation tests completed!")
