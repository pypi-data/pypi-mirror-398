#!/usr/bin/env python3
"""
Test configuration validation improvements
"""
import json
import uuid
from mcp_proxy_adapter.core.config_validator import ConfigValidator

def test_uuid_validation():
    """Test UUID4 validation"""
    print("🔍 Testing UUID4 validation...")
    
    # Test invalid UUID
    invalid_config = {
        "uuid": "123e4567-e89b-12d3-a456-426614174000",  # Invalid UUID4
        "server": {"host": "0.0.0.0", "port": 8080, "protocol": "http", "debug": False, "log_level": "INFO"},
        "logging": {"level": "INFO", "file": None, "log_dir": "./logs", "log_file": "test.log", 
                   "error_log_file": "error.log", "access_log_file": "access.log", "max_file_size": "10MB",
                   "backup_count": 5, "format": "%(asctime)s - %(message)s", "date_format": "%Y-%m-%d",
                   "console_output": True, "file_output": True},
        "commands": {"auto_discovery": True, "commands_directory": "./commands", "catalog_directory": "./catalog",
                    "plugin_servers": [], "auto_install_dependencies": True, "enabled_commands": ["health"],
                    "disabled_commands": [], "custom_commands_path": "./commands"}
    }
    
    validator = ConfigValidator()
    validator.config_data = invalid_config
    results = validator.validate_config()
    
    uuid_errors = [r for r in results if "Invalid UUID4 format" in r.message]
    if uuid_errors:
        print("✅ Invalid UUID correctly detected")
    else:
        print("❌ Invalid UUID not detected")
        return False
    
    # Test valid UUID
    valid_config = invalid_config.copy()
    valid_config["uuid"] = str(uuid.uuid4())  # Valid UUID4
    
    validator.config_data = valid_config
    results = validator.validate_config()
    
    uuid_errors = [r for r in results if "Invalid UUID4 format" in r.message]
    if not uuid_errors:
        print("✅ Valid UUID correctly accepted")
    else:
        print("❌ Valid UUID incorrectly rejected")
        return False
    
    return True

def test_unknown_fields():
    """Test unknown fields detection"""
    print("\n🔍 Testing unknown fields detection...")
    
    config_with_unknown = {
        "uuid": str(uuid.uuid4()),
        "unknown_field": "test",  # Unknown root field
        "server": {
            "host": "0.0.0.0", "port": 8080, "protocol": "http", "debug": False, "log_level": "INFO",
            "unknown_server_field": "test"  # Unknown server field
        },
        "logging": {"level": "INFO", "file": None, "log_dir": "./logs", "log_file": "test.log",
                   "error_log_file": "error.log", "access_log_file": "access.log", "max_file_size": "10MB",
                   "backup_count": 5, "format": "%(asctime)s - %(message)s", "date_format": "%Y-%m-%d",
                   "console_output": True, "file_output": True},
        "commands": {"auto_discovery": True, "commands_directory": "./commands", "catalog_directory": "./catalog",
                    "plugin_servers": [], "auto_install_dependencies": True, "enabled_commands": ["health"],
                    "disabled_commands": [], "custom_commands_path": "./commands"}
    }
    
    validator = ConfigValidator()
    validator.config_data = config_with_unknown
    results = validator.validate_config()
    
    unknown_warnings = [r for r in results if "Unknown field" in r.message]
    if len(unknown_warnings) >= 2:  # Should detect both unknown fields
        print("✅ Unknown fields correctly detected")
        for warning in unknown_warnings:
            print(f"   - {warning.message}")
    else:
        print("❌ Unknown fields not detected")
        return False
    
    return True

def test_config_generator():
    """Test configuration generator"""
    print("\n🔍 Testing configuration generator...")
    
    try:
        from mcp_proxy_adapter.examples.config_builder import generate_complete_config
        
        config = generate_complete_config()
        
        # Check if UUID is valid
        if "uuid" in config:
            validator = ConfigValidator()
            validator.config_data = config
            results = validator.validate_config()
            
            uuid_errors = [r for r in results if "Invalid UUID4 format" in r.message]
            if not uuid_errors:
                print("✅ Generator creates valid UUID4")
            else:
                print("❌ Generator creates invalid UUID4")
                return False
        else:
            print("❌ Generator doesn't create UUID")
            return False
        
        print("✅ Configuration generator works correctly")
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import generator: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing configuration validation improvements...")
    
    tests = [
        test_uuid_validation,
        test_unknown_fields,
        test_config_generator
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Configuration validation is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the configuration validation.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
