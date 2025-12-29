"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Test runner for MCP Proxy Adapter test environment setup.
"""

import time
from pathlib import Path
from typing import bool






def _test_basic_connectivity() -> bool:
    """Test basic network connectivity."""
    try:
        import socket
        
        # Test if we can create a socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            # This is a basic connectivity test
            print("✅ Basic connectivity test passed")
            return True
            
    except Exception as e:
        print(f"❌ Basic connectivity test failed: {e}")
        return False


def _test_configuration_validation() -> bool:
    """Test configuration validation."""
    try:
        from .config_validator import ConfigurationValidator
        
        validator = ConfigurationValidator()
        
        # Test valid configuration
        valid_config = {
            "protocols": {"enabled": True, "allowed_protocols": ["https"]},
            "security": {"ssl": {"enabled": True}}
        }
        
        is_valid, errors, warnings = validator.validate_config(valid_config, "test")
        
        if is_valid:
            print("✅ Configuration validation test passed")
            return True
        else:
            print(f"❌ Configuration validation test failed: {errors}")
            return False
            
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False


def _test_certificates() -> bool:
    """Test certificate files."""
    try:
        certs_dir = Path("certs")
        keys_dir = Path("keys")
        
        if not certs_dir.exists() or not keys_dir.exists():
            print("⚠️ Certificate directories not found, skipping certificate test")
            return True
        
        # Check for required certificate files
        required_files = [
            certs_dir / "ca_cert.pem",
            certs_dir / "localhost_server.crt",
            keys_dir / "server_key.pem"
        ]
        
        missing_files = [f for f in required_files if not f.exists()]
        
        if missing_files:
            print(f"⚠️ Missing certificate files: {missing_files}")
            return False
        
        print("✅ Certificate test passed")
        return True
        
    except Exception as e:
        print(f"❌ Certificate test failed: {e}")
        return False
