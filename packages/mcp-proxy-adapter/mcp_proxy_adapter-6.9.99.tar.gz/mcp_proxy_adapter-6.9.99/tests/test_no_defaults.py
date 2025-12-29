"""
Tests to verify that configuration system has NO default values.

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

# Import only the config module directly
from mcp_proxy_adapter.config import Config
from mcp_proxy_adapter.core.errors import ConfigError


class TestNoDefaults(unittest.TestCase):
    """Test that configuration system has no default values."""
    
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
    
    def test_missing_config_file_raises_error(self):
        """Test that missing configuration file raises ConfigError."""
        non_existent_file = os.path.join(self.temp_dir, "non_existent.json")
        
        with self.assertRaises(ConfigError) as context:
            Config(non_existent_file, validate_on_load=True)
        
        error = context.exception
        self.assertIn("does not exist", str(error))
        self.assertIn("Use the configuration generator", str(error))
        
        print("✅ Missing config file correctly raises ConfigError")
    
    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises ConfigError."""
        invalid_json_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_json_file, 'w') as f:
            f.write("{ invalid json }")
        
        with self.assertRaises(ConfigError) as context:
            Config(invalid_json_file, validate_on_load=True)
        
        error = context.exception
        self.assertIn("invalid JSON", str(error))
        
        print("✅ Invalid JSON correctly raises ConfigError")
    
    def test_incomplete_config_raises_error(self):
        """Test that incomplete configuration raises ConfigError."""
        incomplete_config = {
            "server": {
                "host": "0.0.0.0"
                # Missing required keys: port, protocol, debug, log_level
            }
        }
        
        config_file = self.create_test_config(incomplete_config)
        
        with self.assertRaises(ConfigError) as context:
            Config(config_file, validate_on_load=True)
        
        error = context.exception
        self.assertIn("Configuration validation failed", str(error))
        self.assertGreater(len(error.validation_results), 0)
        
        # Check that specific required keys are mentioned
        error_summary = error.get_error_summary()
        self.assertIn("port", error_summary)
        self.assertIn("protocol", error_summary)
        self.assertIn("debug", error_summary)
        self.assertIn("log_level", error_summary)
        
        print("✅ Incomplete configuration correctly raises ConfigError with detailed errors")
    
    def test_missing_required_sections_raises_error(self):
        """Test that missing required sections raises ConfigError."""
        minimal_config = {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "protocol": "http",
                "debug": False,
                "log_level": "INFO"
            }
            # Missing required sections: logging, commands, transport, etc.
        }
        
        config_file = self.create_test_config(minimal_config)
        
        with self.assertRaises(ConfigError) as context:
            Config(config_file, validate_on_load=True)
        
        error = context.exception
        self.assertIn("Configuration validation failed", str(error))
        
        # Check that missing sections are mentioned
        error_summary = error.get_error_summary()
        self.assertIn("logging", error_summary)
        self.assertIn("commands", error_summary)
        self.assertIn("transport", error_summary)
        
        print("✅ Missing required sections correctly raises ConfigError")
    
    def test_security_enabled_without_auth_raises_warning(self):
        """Test that security enabled without authentication raises warning (not error)."""
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
        
        # Should NOT raise ConfigError for warnings
        try:
            config = Config(config_file, validate_on_load=True)
            
            # Should have warnings but no errors
            warnings = config.get_validation_warnings()
            errors = config.get_validation_errors()
            
            self.assertGreater(len(warnings), 0, "Should have warnings for security without auth")
            self.assertEqual(len(errors), 0, "Should not have errors for warnings")
            
            # Check that security warning is present
            security_warnings = [w for w in warnings if "Security is enabled but no authentication methods" in w.message]
            self.assertGreater(len(security_warnings), 0, "Should have security warning")
            
            print("✅ Security warnings correctly detected without raising ConfigError")
            
        except ConfigError as e:
            self.fail(f"ConfigError should not be raised for warnings: {e}")
    
    def test_roles_enabled_without_config_file_raises_error(self):
        """Test that roles enabled without config file raises ConfigError."""
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
        
        config_file = self.create_test_config(config_data)
        
        with self.assertRaises(ConfigError) as context:
            Config(config_file, validate_on_load=True)
        
        error = context.exception
        self.assertIn("Configuration validation failed", str(error))
        
        # Check that roles error is mentioned
        error_summary = error.get_error_summary()
        self.assertIn("roles", error_summary.lower())
        self.assertIn("config_file", error_summary.lower())
        
        print("✅ Roles enabled without config file correctly raises ConfigError")
    
    def test_ssl_enabled_without_certificates_raises_error(self):
        """Test that SSL enabled without certificates raises ConfigError."""
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
        
        config_file = self.create_test_config(config_data)
        
        with self.assertRaises(ConfigError) as context:
            Config(config_file, validate_on_load=True)
        
        error = context.exception
        self.assertIn("Configuration validation failed", str(error))
        
        # Check that SSL errors are mentioned
        error_summary = error.get_error_summary()
        self.assertIn("ssl", error_summary.lower())
        self.assertIn("cert_file", error_summary.lower())
        self.assertIn("key_file", error_summary.lower())
        
        print("✅ SSL enabled without certificates correctly raises ConfigError")
    
    def test_valid_complete_config_does_not_raise_error(self):
        """Test that valid complete configuration does not raise ConfigError."""
        complete_config = {
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
        
        config_file = self.create_test_config(complete_config)
        
        # Should NOT raise ConfigError for valid configuration
        try:
            config = Config(config_file, validate_on_load=True)
            
            # Should be valid
            self.assertTrue(config.is_valid())
            
            # Should have no errors
            errors = config.get_validation_errors()
            self.assertEqual(len(errors), 0, "Valid configuration should have no errors")
            
            print("✅ Valid complete configuration correctly loads without ConfigError")
            
        except ConfigError as e:
            self.fail(f"ConfigError should not be raised for valid configuration: {e}")


if __name__ == '__main__':
    print("🧪 Running No Defaults Tests")
    print("=" * 50)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 50)
    print("✅ All no defaults tests completed!")
