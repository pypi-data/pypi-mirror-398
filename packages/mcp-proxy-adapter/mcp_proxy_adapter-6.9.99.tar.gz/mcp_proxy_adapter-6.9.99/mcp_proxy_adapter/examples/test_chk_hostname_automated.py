#!/usr/bin/env python3
"""
Automated tests for chk_hostname functionality in all SSL modes.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import tempfile
import os
from pathlib import Path
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_proxy_adapter.config import Config
from mcp_proxy_adapter.examples.config_builder import ConfigBuilder, Protocol, AuthMethod


def test_chk_hostname_default_config():
    """Test that default config has chk_hostname=False for HTTP."""
    print("🧪 Testing default config chk_hostname...")
    
    config = Config()
    
    # Default should be HTTP with chk_hostname=False
    assert config.get("server.protocol") == "http"
    assert config.get("transport.chk_hostname") is False
    
    print("✅ Default config: chk_hostname=False for HTTP")


def test_chk_hostname_http_config():
    """Test that HTTP config has chk_hostname=False."""
    print("🧪 Testing HTTP config chk_hostname...")
    
    # Create HTTP config
    http_config = ConfigBuilder().set_protocol(Protocol.HTTP).build()
    
    # Save to temporary file and load with Config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(http_config, f)
        temp_config_path = f.name
    
    try:
        config = Config(temp_config_path)
        
        # HTTP should have chk_hostname=False
        assert config.get("server.protocol") == "http"
        assert config.get("transport.chk_hostname") is False
        
        print("✅ HTTP config: chk_hostname=False")
    finally:
        os.unlink(temp_config_path)


def test_chk_hostname_https_config():
    """Test that HTTPS config has chk_hostname=True."""
    print("🧪 Testing HTTPS config chk_hostname...")
    
    # Create HTTPS config
    https_config = ConfigBuilder().set_protocol(Protocol.HTTPS).build()
    
    # Save to temporary file and load with Config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(https_config, f)
        temp_config_path = f.name
    
    try:
        config = Config(temp_config_path)
        
        
        # HTTPS should have chk_hostname=True
        assert config.get("server.protocol") == "https"
        assert config.get("transport.chk_hostname") is True
        
        print("✅ HTTPS config: chk_hostname=True")
    finally:
        os.unlink(temp_config_path)


def test_chk_hostname_mtls_config():
    """Test that mTLS config has chk_hostname=True."""
    print("🧪 Testing mTLS config chk_hostname...")
    
    # Create mTLS config
    mtls_config = ConfigBuilder().set_protocol(Protocol.MTLS).build()
    
    # Save to temporary file and load with Config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mtls_config, f)
        temp_config_path = f.name
    
    try:
        config = Config(temp_config_path)
        
        # mTLS should have chk_hostname=True
        assert config.get("server.protocol") == "mtls"
        assert config.get("transport.chk_hostname") is True
        
        print("✅ mTLS config: chk_hostname=True")
    finally:
        os.unlink(temp_config_path)


def test_chk_hostname_override():
    """Test that chk_hostname can be overridden in config."""
    print("🧪 Testing chk_hostname override...")
    
    # Create HTTPS config with chk_hostname=False override
    https_config = ConfigBuilder().set_protocol(Protocol.HTTPS).build()
    # Add transport section if it doesn't exist
    if "transport" not in https_config:
        https_config["transport"] = {}
    https_config["transport"]["chk_hostname"] = False
    
    # Save to temporary file and load with Config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(https_config, f)
        temp_config_path = f.name
    
    try:
        config = Config(temp_config_path)
        
        
        # Should respect the override
        assert config.get("server.protocol") == "https"
        assert config.get("transport.chk_hostname") is False
        
        print("✅ HTTPS config with chk_hostname=False override works")
    finally:
        os.unlink(temp_config_path)


def test_chk_hostname_all_combinations():
    """Test chk_hostname for all protocol and auth combinations."""
    print("🧪 Testing chk_hostname for all combinations...")
    
    protocols = [Protocol.HTTP, Protocol.HTTPS, Protocol.MTLS]
    auth_methods = [AuthMethod.NONE, AuthMethod.TOKEN, AuthMethod.TOKEN_ROLES]
    
    for protocol in protocols:
        for auth_method in auth_methods:
            # Create config
            config_data = (ConfigBuilder()
                          .set_protocol(protocol)
                          .set_auth(auth_method)
                          .build())
            
            # Save to temporary file and load with Config
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(config_data, f)
                temp_config_path = f.name
            
            try:
                config = Config(temp_config_path)
                
                protocol_name = protocol.value
                auth_name = auth_method.value
                
                # Check chk_hostname based on protocol
                if protocol_name == "http":
                    expected_chk_hostname = False
                else:  # https or mtls
                    expected_chk_hostname = True
                
                actual_chk_hostname = config.get("transport.ssl.chk_hostname")
                
                assert actual_chk_hostname == expected_chk_hostname, (
                    f"Protocol {protocol_name} with auth {auth_name}: "
                    f"expected chk_hostname={expected_chk_hostname}, "
                    f"got {actual_chk_hostname}"
                )
                
                print(f"✅ {protocol_name}+{auth_name}: chk_hostname={actual_chk_hostname}")
                
            finally:
                os.unlink(temp_config_path)
    
    print("✅ All protocol+auth combinations have correct chk_hostname values")


def main():
    """Run all chk_hostname tests."""
    print("🧪 Running Automated chk_hostname Tests")
    print("=" * 50)
    
    try:
        test_chk_hostname_default_config()
        test_chk_hostname_http_config()
        test_chk_hostname_https_config()
        test_chk_hostname_mtls_config()
        test_chk_hostname_override()
        test_chk_hostname_all_combinations()
        
        print("=" * 50)
        print("🎉 All chk_hostname tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
