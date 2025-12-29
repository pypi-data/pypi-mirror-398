"""
Integration tests for Config class with validation.

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

# Import only the config module directly to avoid dependency issues
from mcp_proxy_adapter.core.config import Config
from mcp_proxy_adapter.core.errors import ConfigError


class TestConfigIntegration(unittest.TestCase):
    """Test integration with Config class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_config(self, config_data: Dict[str, Any]) -> str:
        """Create a temporary configuration file."""
        config_file = os.path.join(self.temp_dir, "test_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        return config_file
    
    def test_config_validation_integration_valid(self):
        """Test Config class with valid configuration (POSITIVE TEST)."""
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
        
        config_file = self.create_test_config(config_data)
        
        # Test Config class with validation (should not raise exception for valid config)
        try:
            config = Config(config_file, validate_on_load=True)
            
            # Should be able to get validation results
            self.assertTrue(hasattr(config, 'validation_results'))
            self.assertTrue(hasattr(config, 'is_valid'))
            self.assertTrue(hasattr(config, 'get_validation_summary'))
            
            # For valid config, should be valid
            self.assertTrue(config.is_valid())
            
            print("✅ POSITIVE TEST PASSED: Valid configuration loaded successfully")
            
        except ConfigError as e:
            self.fail(f"ConfigError raised for valid configuration: {e}")
    
    def test_config_error_on_invalid_config(self):
        """Test that ConfigError is raised for invalid configuration (NEGATIVE TEST)."""
        # Create an invalid configuration file (missing required sections)
        config_data = {
            "server": {
                "host": "0.0.0.0"
                # Missing required keys
            }
        }
        
        config_file = self.create_test_config(config_data)
        
        # Should raise ConfigError for invalid config
        with self.assertRaises(ConfigError) as context:
            Config(config_file, validate_on_load=True)
        
        # Check that the error contains useful information
        error = context.exception
        self.assertIn("Configuration validation failed", str(error))
        self.assertGreater(len(error.validation_results), 0)
        
        print("✅ NEGATIVE TEST PASSED: ConfigError raised for invalid configuration")
    
    def test_config_error_without_validation(self):
        """Test that Config can be created without validation (POSITIVE TEST)."""
        # Create a valid configuration file
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
        
        config_file = self.create_test_config(config_data)
        
        # Should not raise ConfigError when validation is disabled
        try:
            config = Config(config_file, validate_on_load=False)
            self.assertIsNotNone(config)
            print("✅ POSITIVE TEST PASSED: Config loaded without validation")
        except ConfigError:
            self.fail("ConfigError should not be raised when validation is disabled")
    
    def test_config_error_details(self):
        """Test that ConfigError provides detailed error information (NEGATIVE TEST)."""
        # Create an invalid configuration file
        config_data = {
            "server": {
                "host": "0.0.0.0"
                # Missing required keys
            }
        }
        
        config_file = self.create_test_config(config_data)
        
        try:
            Config(config_file, validate_on_load=True)
            self.fail("Should have raised ConfigError")
        except ConfigError as e:
            # Check error message
            self.assertIn("Configuration validation failed", str(e))
            
            # Check validation results
            self.assertGreater(len(e.validation_results), 0)
            
            # Check error summary
            error_summary = e.get_error_summary()
            self.assertIsInstance(error_summary, str)
            self.assertGreater(len(error_summary), 0)
            
            print("✅ NEGATIVE TEST PASSED: ConfigError provides detailed information")
    
    def test_config_validation_methods(self):
        """Test Config validation methods (POSITIVE TEST)."""
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
        
        config_file = self.create_test_config(config_data)
        config = Config(config_file, validate_on_load=True)
        
        # Test validation methods
        self.assertTrue(config.is_valid())
        
        # Test validation summary
        summary = config.get_validation_summary()
        # Check for either "total_issues" or "total" (depending on implementation)
        self.assertTrue("total_issues" in summary or "total" in summary, f"Summary keys: {summary.keys()}")
        self.assertIn("errors", summary)
        self.assertIn("warnings", summary)
        self.assertIn("is_valid", summary)
        
        # Test getting validation errors and warnings
        errors = config.get_validation_errors()
        warnings = config.get_validation_warnings()
        
        self.assertIsInstance(errors, list)
        self.assertIsInstance(warnings, list)
        
        print("✅ POSITIVE TEST PASSED: Config validation methods work correctly")
    
    def test_config_feature_requirements(self):
        """Test Config feature requirements checking (NEGATIVE TEST)."""
        # Create config with security enabled but no auth
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
        
        config_file = self.create_test_config(config_data)
        
        # Should not raise ConfigError for warnings (only errors)
        try:
            config = Config(config_file, validate_on_load=True)
            
            # Should have warnings but no errors
            warnings = config.get_validation_warnings()
            errors = config.get_validation_errors()
            
            self.assertGreater(len(warnings), 0, "Should have warnings for security without auth")
            self.assertEqual(len(errors), 0, "Should not have errors for warnings")
            
            print("✅ NEGATIVE TEST PASSED: Security warnings detected without errors")
            
        except ConfigError as e:
            self.fail(f"ConfigError should not be raised for warnings: {e}")
    
    def test_config_error_missing_file(self):
        """Test that ConfigError is raised when configuration file does not exist (NEGATIVE TEST)."""
        non_existent_file = os.path.join(self.temp_dir, "non_existent.json")
        
        # Should raise ConfigError for missing file
        with self.assertRaises(ConfigError) as context:
            Config(non_existent_file, validate_on_load=True)
        
        # Check that the error contains useful information
        error = context.exception
        self.assertIn("does not exist", str(error))
        self.assertIn("Use the configuration generator", str(error))
        
        print("✅ NEGATIVE TEST PASSED: ConfigError raised for missing configuration file")


if __name__ == '__main__':
    print("🧪 Running Config Integration Tests")
    print("=" * 50)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 50)
    print("✅ All integration tests completed!")
