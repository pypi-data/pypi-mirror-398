"""
Isolated tests for configuration validation.
Tests the validation system without importing the full package.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import only the validation modules directly
from mcp_proxy_adapter.core.config_validator import ConfigValidator
from mcp_proxy_adapter.core.validation.validation_result import ValidationResult, ValidationLevel


class TestConfigValidationIsolated(unittest.TestCase):
    """Test configuration validation functionality in isolation."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = ConfigValidator()
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_valid_minimal_config(self):
        """Test validation of valid minimal configuration (POSITIVE TEST)."""
        config_data = {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "protocol": "http",
                "debug": False,
                "log_level": "INFO"
            },
            "logging": {
                "level": "INFO",
                "file": None,
                "log_dir": "./logs",
                "log_file": "test.log",
                "error_log_file": "error.log",
                "access_log_file": "access.log",
                "max_file_size": "10MB",
                "backup_count": 5,
                "format": "%(asctime)s - %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S",
                "console_output": True,
                "file_output": True
            },
            "commands": {
                "auto_discovery": True,
                "commands_directory": "./commands",
                "catalog_directory": "./catalog",
                "plugin_servers": [],
                "auto_install_dependencies": True,
                "enabled_commands": ["health", "echo"],
                "disabled_commands": [],
                "custom_commands_path": "./commands"
            },
            "transport": {
                "type": "http",
                "port": None,
                "verify_client": False,
                "chk_hostname": False
            },
            "proxy_registration": {
                "enabled": False,
                "proxy_url": "http://localhost:3004",
                "server_id": "test_server",
                "server_name": "Test Server",
                "description": "Test server",
                "version": "1.0.0",
                "registration_timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 5,
                "auto_register_on_startup": True,
                "auto_unregister_on_shutdown": True
            },
            "debug": {
                "enabled": False,
                "level": "WARNING"
            },
            "security": {
                "enabled": False,
                "tokens": {},
                "roles": {},
                "roles_file": None
            },
            "roles": {
                "enabled": False,
                "config_file": None,
                "default_policy": {
                    "deny_by_default": False,
                    "require_role_match": False,
                    "case_sensitive": False,
                    "allow_wildcard": False
                },
                "auto_load": False,
                "validation_enabled": False
            }
        }
        
        results = self.validator.validate_config(config_data)
        
        # Should have no errors for valid minimal config
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        self.assertEqual(len(errors), 0, f"Unexpected errors: {[e.message for e in errors]}")
        
        print("✅ POSITIVE TEST PASSED: Valid minimal configuration")
    
    def test_missing_required_sections(self):
        """Test validation with missing required sections (NEGATIVE TEST)."""
        config_data = {
            "server": {
                "host": "0.0.0.0",
                "port": 8000
                # Missing required keys
            }
        }
        
        results = self.validator.validate_config(config_data)
        
        # Should have errors for missing sections and keys
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        self.assertGreater(len(errors), 0, "Should have errors for missing sections")
        
        # Check for specific missing section error
        missing_section_errors = [e for e in errors if "Required section" in e.message]
        self.assertGreater(len(missing_section_errors), 0, "Should have missing section errors")
        
        print("✅ NEGATIVE TEST PASSED: Missing required sections detected")
    
    def test_security_enabled_without_auth(self):
        """Test security enabled without authentication methods (NEGATIVE TEST)."""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8000, "protocol": "http", "debug": False, "log_level": "INFO"},
            "logging": {"level": "INFO", "file": None, "log_dir": "./logs", "log_file": "test.log", 
                       "error_log_file": "error.log", "access_log_file": "access.log", "max_file_size": "10MB",
                       "backup_count": 5, "format": "%(asctime)s - %(message)s", "date_format": "%Y-%m-%d %H:%M:%S",
                       "console_output": True, "file_output": True},
            "commands": {"auto_discovery": True, "commands_directory": "./commands", "catalog_directory": "./catalog",
                        "plugin_servers": [], "auto_install_dependencies": True, "enabled_commands": ["health"],
                        "disabled_commands": [], "custom_commands_path": "./commands"},
            "transport": {"type": "http", "port": None, "verify_client": False, "chk_hostname": False},
            "proxy_registration": {"enabled": False, "proxy_url": "http://localhost:3004", "server_id": "test",
                                 "server_name": "Test", "description": "Test", "version": "1.0.0",
                                 "registration_timeout": 30, "retry_attempts": 3, "retry_delay": 5,
                                 "auto_register_on_startup": True, "auto_unregister_on_shutdown": True},
            "debug": {"enabled": False, "level": "WARNING"},
            "security": {
                "enabled": True,  # Security enabled
                "tokens": {},     # But no tokens
                "roles": {},      # And no roles
                "roles_file": None  # And no roles file
            },
            "roles": {"enabled": False, "config_file": None, "default_policy": {"deny_by_default": False,
                "require_role_match": False, "case_sensitive": False, "allow_wildcard": False},
                "auto_load": False, "validation_enabled": False}
        }
        
        results = self.validator.validate_config(config_data)
        
        # Should have warning about security enabled without auth
        warnings = [r for r in results if r.level == ValidationLevel.WARNING]
        security_warnings = [w for w in warnings if "Security is enabled but no authentication methods" in w.message]
        self.assertGreater(len(security_warnings), 0, "Should have security warning")
        
        print("✅ NEGATIVE TEST PASSED: Security warning detected")
    
    def test_roles_enabled_without_config_file(self):
        """Test roles enabled without config file (NEGATIVE TEST)."""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8000, "protocol": "http", "debug": False, "log_level": "INFO"},
            "logging": {"level": "INFO", "file": None, "log_dir": "./logs", "log_file": "test.log",
                       "error_log_file": "error.log", "access_log_file": "access.log", "max_file_size": "10MB",
                       "backup_count": 5, "format": "%(asctime)s - %(message)s", "date_format": "%Y-%m-%d %H:%M:%S",
                       "console_output": True, "file_output": True},
            "commands": {"auto_discovery": True, "commands_directory": "./commands", "catalog_directory": "./catalog",
                        "plugin_servers": [], "auto_install_dependencies": True, "enabled_commands": ["health"],
                        "disabled_commands": [], "custom_commands_path": "./commands"},
            "transport": {"type": "http", "port": None, "verify_client": False, "chk_hostname": False},
            "proxy_registration": {"enabled": False, "proxy_url": "http://localhost:3004", "server_id": "test",
                                 "server_name": "Test", "description": "Test", "version": "1.0.0",
                                 "registration_timeout": 30, "retry_attempts": 3, "retry_delay": 5,
                                 "auto_register_on_startup": True, "auto_unregister_on_shutdown": True},
            "debug": {"enabled": False, "level": "WARNING"},
            "security": {"enabled": False, "tokens": {}, "roles": {}, "roles_file": None},
            "roles": {
                "enabled": True,  # Roles enabled
                "config_file": None,  # But no config file
                "default_policy": {"deny_by_default": False, "require_role_match": False,
                                  "case_sensitive": False, "allow_wildcard": False},
                "auto_load": False, "validation_enabled": False
            }
        }
        
        results = self.validator.validate_config(config_data)
        
        # Should have error about roles enabled without config file
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        roles_errors = [e for e in errors if "Roles are enabled but config_file is not specified" in e.message]
        self.assertGreater(len(roles_errors), 0, "Should have roles error")
        
        print("✅ NEGATIVE TEST PASSED: Roles error detected")
    
    def test_ssl_enabled_without_certificates(self):
        """Test SSL enabled without certificate files (NEGATIVE TEST)."""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8000, "protocol": "https", "debug": False, "log_level": "INFO"},
            "logging": {"level": "INFO", "file": None, "log_dir": "./logs", "log_file": "test.log",
                       "error_log_file": "error.log", "access_log_file": "access.log", "max_file_size": "10MB",
                       "backup_count": 5, "format": "%(asctime)s - %(message)s", "date_format": "%Y-%m-%d %H:%M:%S",
                       "console_output": True, "file_output": True},
            "commands": {"auto_discovery": True, "commands_directory": "./commands", "catalog_directory": "./catalog",
                        "plugin_servers": [], "auto_install_dependencies": True, "enabled_commands": ["health"],
                        "disabled_commands": [], "custom_commands_path": "./commands"},
            "transport": {"type": "https", "port": None, "verify_client": False, "chk_hostname": True},
            "proxy_registration": {"enabled": False, "proxy_url": "https://localhost:3004", "server_id": "test",
                                 "server_name": "Test", "description": "Test", "version": "1.0.0",
                                 "registration_timeout": 30, "retry_attempts": 3, "retry_delay": 5,
                                 "auto_register_on_startup": True, "auto_unregister_on_shutdown": True},
            "debug": {"enabled": False, "level": "WARNING"},
            "security": {"enabled": False, "tokens": {}, "roles": {}, "roles_file": None},
            "roles": {"enabled": False, "config_file": None, "default_policy": {"deny_by_default": False,
                "require_role_match": False, "case_sensitive": False, "allow_wildcard": False},
                "auto_load": False, "validation_enabled": False},
            "ssl": {
                "enabled": True,  # SSL enabled
                "cert_file": None,  # But no cert file
                "key_file": None,   # And no key file
                "ca_cert": None
            }
        }
        
        results = self.validator.validate_config(config_data)
        
        # Should have errors about missing SSL files
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        ssl_errors = [e for e in errors if "SSL" in e.message and ("cert_file" in e.message or "key_file" in e.message)]
        self.assertGreater(len(ssl_errors), 0, "Should have SSL errors")
        
        print("✅ NEGATIVE TEST PASSED: SSL errors detected")
    
    def test_protocol_specific_validation(self):
        """Test protocol-specific validation (NEGATIVE TEST)."""
        # Test mTLS protocol requirements
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8000, "protocol": "mtls", "debug": False, "log_level": "INFO"},
            "logging": {"level": "INFO", "file": None, "log_dir": "./logs", "log_file": "test.log",
                       "error_log_file": "error.log", "access_log_file": "access.log", "max_file_size": "10MB",
                       "backup_count": 5, "format": "%(asctime)s - %(message)s", "date_format": "%Y-%m-%d %H:%M:%S",
                       "console_output": True, "file_output": True},
            "commands": {"auto_discovery": True, "commands_directory": "./commands", "catalog_directory": "./catalog",
                        "plugin_servers": [], "auto_install_dependencies": True, "enabled_commands": ["health"],
                        "disabled_commands": [], "custom_commands_path": "./commands"},
            "transport": {"type": "mtls", "port": None, "verify_client": False, "chk_hostname": True},
            "proxy_registration": {"enabled": False, "proxy_url": "https://localhost:3004", "server_id": "test",
                                 "server_name": "Test", "description": "Test", "version": "1.0.0",
                                 "registration_timeout": 30, "retry_attempts": 3, "retry_delay": 5,
                                 "auto_register_on_startup": True, "auto_unregister_on_shutdown": True},
            "debug": {"enabled": False, "level": "WARNING"},
            "security": {"enabled": False, "tokens": {}, "roles": {}, "roles_file": None},
            "roles": {"enabled": False, "config_file": None, "default_policy": {"deny_by_default": False,
                "require_role_match": False, "case_sensitive": False, "allow_wildcard": False},
                "auto_load": False, "validation_enabled": False},
            "ssl": {"enabled": True, "cert_file": None, "key_file": None, "ca_cert": None}
        }
        
        results = self.validator.validate_config(config_data)
        
        # Should have errors about mTLS requirements
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        mtls_errors = [e for e in errors if "mtls" in e.message.lower() or "client certificate" in e.message.lower()]
        self.assertGreater(len(mtls_errors), 0, "Should have mTLS errors")
        
        print("✅ NEGATIVE TEST PASSED: mTLS protocol errors detected")
    
    def test_file_existence_validation(self):
        """Test file existence validation (NEGATIVE TEST)."""
        # Create a non-existent file path
        non_existent_file = os.path.join(self.temp_dir, "non_existent.json")
        
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8000, "protocol": "http", "debug": False, "log_level": "INFO"},
            "logging": {"level": "INFO", "file": None, "log_dir": "./logs", "log_file": "test.log",
                       "error_log_file": "error.log", "access_log_file": "access.log", "max_file_size": "10MB",
                       "backup_count": 5, "format": "%(asctime)s - %(message)s", "date_format": "%Y-%m-%d %H:%M:%S",
                       "console_output": True, "file_output": True},
            "commands": {"auto_discovery": True, "commands_directory": "./commands", "catalog_directory": "./catalog",
                        "plugin_servers": [], "auto_install_dependencies": True, "enabled_commands": ["health"],
                        "disabled_commands": [], "custom_commands_path": "./commands"},
            "transport": {"type": "http", "port": None, "verify_client": False, "chk_hostname": False},
            "proxy_registration": {"enabled": False, "proxy_url": "http://localhost:3004", "server_id": "test",
                                 "server_name": "Test", "description": "Test", "version": "1.0.0",
                                 "registration_timeout": 30, "retry_attempts": 3, "retry_delay": 5,
                                 "auto_register_on_startup": True, "auto_unregister_on_shutdown": True},
            "debug": {"enabled": False, "level": "WARNING"},
            "security": {"enabled": False, "tokens": {}, "roles": {}, "roles_file": None},
            "roles": {
                "enabled": True,  # Roles enabled
                "config_file": non_existent_file,  # Non-existent file
                "default_policy": {"deny_by_default": False, "require_role_match": False,
                                  "case_sensitive": False, "allow_wildcard": False},
                "auto_load": False, "validation_enabled": False
            }
        }
        
        results = self.validator.validate_config(config_data)
        
        # Should have error about non-existent file
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        file_errors = [e for e in errors if non_existent_file in e.message]
        self.assertGreater(len(file_errors), 0, "Should have file existence error")
        
        print("✅ NEGATIVE TEST PASSED: File existence error detected")
    
    def test_conditional_validation_disabled_features(self):
        """Test that disabled features don't trigger validation errors (POSITIVE TEST)."""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8000, "protocol": "http", "debug": False, "log_level": "INFO"},
            "logging": {"level": "INFO", "file": None, "log_dir": "./logs", "log_file": "test.log",
                       "error_log_file": "error.log", "access_log_file": "access.log", "max_file_size": "10MB",
                       "backup_count": 5, "format": "%(asctime)s - %(message)s", "date_format": "%Y-%m-%d %H:%M:%S",
                       "console_output": True, "file_output": True},
            "commands": {"auto_discovery": True, "commands_directory": "./commands", "catalog_directory": "./catalog",
                        "plugin_servers": [], "auto_install_dependencies": True, "enabled_commands": ["health"],
                        "disabled_commands": [], "custom_commands_path": "./commands"},
            "transport": {"type": "http", "port": None, "verify_client": False, "chk_hostname": False},
            "proxy_registration": {"enabled": False, "proxy_url": "http://localhost:3004", "server_id": "test",
                                 "server_name": "Test", "description": "Test", "version": "1.0.0",
                                 "registration_timeout": 30, "retry_attempts": 3, "retry_delay": 5,
                                 "auto_register_on_startup": True, "auto_unregister_on_shutdown": True},
            "debug": {"enabled": False, "level": "WARNING"},
            "security": {"enabled": False, "tokens": {}, "roles": {}, "roles_file": None},
            "roles": {
                "enabled": False,  # Roles disabled
                "config_file": "non_existent.json",  # Non-existent file, but should not cause error
                "default_policy": {"deny_by_default": False, "require_role_match": False,
                                  "case_sensitive": False, "allow_wildcard": False},
                "auto_load": False, "validation_enabled": False
            }
        }
        
        results = self.validator.validate_config(config_data)
        
        # Should not have errors for disabled features
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        role_errors = [e for e in errors if "roles" in e.message.lower()]
        self.assertEqual(len(role_errors), 0, "Should not have errors for disabled roles feature")
        
        print("✅ POSITIVE TEST PASSED: Disabled features don't trigger errors")
    
    def test_validation_summary(self):
        """Test validation summary generation (POSITIVE TEST)."""
        config_data = {
            "server": {"host": "0.0.0.0", "port": 8000, "protocol": "http", "debug": False, "log_level": "INFO"},
            "logging": {"level": "INFO", "file": None, "log_dir": "./logs", "log_file": "test.log",
                       "error_log_file": "error.log", "access_log_file": "access.log", "max_file_size": "10MB",
                       "backup_count": 5, "format": "%(asctime)s - %(message)s", "date_format": "%Y-%m-%d %H:%M:%S",
                       "console_output": True, "file_output": True},
            "commands": {"auto_discovery": True, "commands_directory": "./commands", "catalog_directory": "./catalog",
                        "plugin_servers": [], "auto_install_dependencies": True, "enabled_commands": ["health"],
                        "disabled_commands": [], "custom_commands_path": "./commands"},
            "transport": {"type": "http", "port": None, "verify_client": False, "chk_hostname": False},
            "proxy_registration": {"enabled": False, "proxy_url": "http://localhost:3004", "server_id": "test",
                                 "server_name": "Test", "description": "Test", "version": "1.0.0",
                                 "registration_timeout": 30, "retry_attempts": 3, "retry_delay": 5,
                                 "auto_register_on_startup": True, "auto_unregister_on_shutdown": True},
            "debug": {"enabled": False, "level": "WARNING"},
            "security": {"enabled": False, "tokens": {}, "roles": {}, "roles_file": None},
            "roles": {"enabled": False, "config_file": None, "default_policy": {"deny_by_default": False,
                "require_role_match": False, "case_sensitive": False, "allow_wildcard": False},
                "auto_load": False, "validation_enabled": False}
        }
        
        results = self.validator.validate_config(config_data)
        summary = self.validator.get_validation_summary()
        
        self.assertIn("total_issues", summary)
        self.assertIn("errors", summary)
        self.assertIn("warnings", summary)
        self.assertIn("info", summary)
        self.assertIn("is_valid", summary)
        
        # For valid config, should have no errors
        self.assertEqual(summary["errors"], 0)
        self.assertTrue(summary["is_valid"])
        
        print("✅ POSITIVE TEST PASSED: Validation summary works correctly")
    
    def test_feature_flag_validation(self):
        """Test feature flag validation (POSITIVE AND NEGATIVE TESTS)."""
        # Test with security enabled but properly configured (POSITIVE)
        config_data_positive = {
            "server": {"host": "0.0.0.0", "port": 8000, "protocol": "http", "debug": False, "log_level": "INFO"},
            "logging": {"level": "INFO", "file": None, "log_dir": "./logs", "log_file": "test.log",
                       "error_log_file": "error.log", "access_log_file": "access.log", "max_file_size": "10MB",
                       "backup_count": 5, "format": "%(asctime)s - %(message)s", "date_format": "%Y-%m-%d %H:%M:%S",
                       "console_output": True, "file_output": True},
            "commands": {"auto_discovery": True, "commands_directory": "./commands", "catalog_directory": "./catalog",
                        "plugin_servers": [], "auto_install_dependencies": True, "enabled_commands": ["health"],
                        "disabled_commands": [], "custom_commands_path": "./commands"},
            "transport": {"type": "http", "port": None, "verify_client": False, "chk_hostname": False},
            "proxy_registration": {"enabled": False, "proxy_url": "http://localhost:3004", "server_id": "test",
                                 "server_name": "Test", "description": "Test", "version": "1.0.0",
                                 "registration_timeout": 30, "retry_attempts": 3, "retry_delay": 5,
                                 "auto_register_on_startup": True, "auto_unregister_on_shutdown": True},
            "debug": {"enabled": False, "level": "WARNING"},
            "security": {
                "enabled": True,  # Security enabled
                "tokens": {"admin": "admin-key", "user": "user-key"},  # With proper tokens
                "roles": {"admin": ["read", "write"], "user": ["read"]},  # With proper roles
                "roles_file": None
            },
            "roles": {"enabled": False, "config_file": None, "default_policy": {"deny_by_default": False,
                "require_role_match": False, "case_sensitive": False, "allow_wildcard": False},
                "auto_load": False, "validation_enabled": False}
        }
        
        results_positive = self.validator.validate_config(config_data_positive)
        errors_positive = [r for r in results_positive if r.level == ValidationLevel.ERROR]
        self.assertEqual(len(errors_positive), 0, "Should have no errors for properly configured security")
        
        print("✅ POSITIVE TEST PASSED: Properly configured security feature")
        
        # Test with security enabled but missing tokens (NEGATIVE)
        config_data_negative = config_data_positive.copy()
        config_data_negative["security"]["tokens"] = {}  # Empty tokens
        config_data_negative["security"]["roles"] = {}   # Empty roles
        
        results_negative = self.validator.validate_config(config_data_negative)
        warnings_negative = [r for r in results_negative if r.level == ValidationLevel.WARNING]
        security_warnings = [w for w in warnings_negative if "Security is enabled but no authentication methods" in w.message]
        self.assertGreater(len(security_warnings), 0, "Should have security warning")
        
        print("✅ NEGATIVE TEST PASSED: Security warning for missing authentication")


if __name__ == '__main__':
    print("🧪 Running Configuration Validation Tests")
    print("=" * 50)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
