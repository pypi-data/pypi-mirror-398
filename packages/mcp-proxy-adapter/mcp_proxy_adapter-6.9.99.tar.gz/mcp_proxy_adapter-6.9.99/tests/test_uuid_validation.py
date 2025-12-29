#!/usr/bin/env python3
"""
Test UUID validation in proxy registration
"""
import json
import subprocess
import time
import sys

def test_uuid_validation():
    """Test UUID validation with invalid and valid UUIDs"""
    print("🔍 Testing UUID validation...")
    
    # Test with invalid UUID
    print("\n1️⃣ Testing with invalid UUID...")
    invalid_config = {
        "uuid": "123e4567-e89b-12d3-a456-426614174000",  # Invalid UUID4 (wrong version)
        "server": {
            "host": "0.0.0.0",
            "port": 8080,
            "protocol": "http",
            "debug": False,
            "log_level": "INFO"
        },
        "logging": {
            "level": "INFO",
            "file": None,
            "log_dir": "./logs",
            "log_file": "mcp_proxy_adapter.log",
            "error_log_file": "mcp_proxy_adapter_error.log",
            "access_log_file": "mcp_proxy_adapter_access.log",
            "max_file_size": "10MB",
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
            "enabled_commands": ["health", "echo", "list", "help"],
            "disabled_commands": [],
            "custom_commands_path": "./commands"
        },
        "proxy_registration": {
            "enabled": True,
            "proxy_url": "http://localhost:3005",
            "uuid": "123e4567-e89b-12d3-a456-426614174000",  # Invalid UUID4
            "server_id": "test_server",
            "server_name": "Test Server",
            "description": "Test",
            "version": "1.0.0",
            "registration_timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 5,
            "auto_register_on_startup": True,
            "auto_unregister_on_shutdown": True
        },
        "security": {"enabled": False},
        "roles": {"enabled": False}
    }
    
    with open("test_invalid_uuid.json", "w") as f:
        json.dump(invalid_config, f, indent=2)
    
    try:
        cmd = [
            "python", "mcp_proxy_adapter/examples/full_application/main.py",
            "--config", "test_invalid_uuid.json"
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
        process.terminate()
        stdout, stderr = process.communicate()
        
        if "Invalid UUID4 format" in stderr.decode():
            print("✅ Invalid UUID correctly rejected")
        else:
            print("❌ Invalid UUID was not rejected")
            print(f"   stderr: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing invalid UUID: {e}")
        return False
    
    # Test with valid UUID4
    print("\n2️⃣ Testing with valid UUID4...")
    valid_config = {
        "uuid": "123e4567-e89b-42d3-8a56-426614174000",  # Valid UUID4
        "server": {
            "host": "0.0.0.0",
            "port": 8080,
            "protocol": "http",
            "debug": False,
            "log_level": "INFO"
        },
        "logging": {
            "level": "INFO",
            "file": None,
            "log_dir": "./logs",
            "log_file": "mcp_proxy_adapter.log",
            "error_log_file": "mcp_proxy_adapter_error.log",
            "access_log_file": "mcp_proxy_adapter_access.log",
            "max_file_size": "10MB",
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
            "enabled_commands": ["health", "echo", "list", "help"],
            "disabled_commands": [],
            "custom_commands_path": "./commands"
        },
        "proxy_registration": {
            "enabled": True,
            "proxy_url": "http://localhost:3005",
            "uuid": "123e4567-e89b-42d3-8a56-426614174000",  # Valid UUID4
            "server_id": "test_server",
            "server_name": "Test Server",
            "description": "Test",
            "version": "1.0.0",
            "registration_timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 5,
            "auto_register_on_startup": True,
            "auto_unregister_on_shutdown": True
        },
        "security": {"enabled": False},
        "roles": {"enabled": False}
    }
    
    with open("test_valid_uuid.json", "w") as f:
        json.dump(valid_config, f, indent=2)
    
    try:
        cmd = [
            "python", "mcp_proxy_adapter/examples/full_application/main.py",
            "--config", "test_valid_uuid.json"
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
        process.terminate()
        stdout, stderr = process.communicate()
        
        if "UUID validation passed" in stdout.decode():
            print("✅ Valid UUID4 correctly accepted")
        else:
            print("❌ Valid UUID4 was not accepted")
            print(f"   stdout: {stdout.decode()}")
            print(f"   stderr: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing valid UUID: {e}")
        return False
    
    print("\n✅ UUID validation test completed successfully")
    return True

if __name__ == "__main__":
    success = test_uuid_validation()
    sys.exit(0 if success else 1)
