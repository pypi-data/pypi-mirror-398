#!/usr/bin/env python3
"""
Test exact user configuration to reproduce the bug
"""
import ssl
import json
import tempfile
import os
from mcp_proxy_adapter.core.proxy_registration import ProxyRegistrationManager

def test_user_exact_config():
    """Test with the exact configuration from user's bug report"""
    print("🔍 Testing user's exact configuration...")
    
    # Exact config from user's bug report - NO verify_mode specified
    user_config = {
        "uuid": "123e4567-e89b-42d3-8a56-426614174000",
        "proxy_registration": {
            "enabled": True,
            "proxy_url": "https://172.28.0.3:3004",
            "server_id": "embedding-service-mtls",
            "server_name": "Embedding Service",
            "description": "JSON-RPC API for interacting with MCP Proxy",
            "version": "6.2.33",
            "registration_timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 5,
            "heartbeat": {
                "enabled": True,
                "interval": 30,
                "timeout": 10,
                "retry_attempts": 3,
                "retry_delay": 5
            },
            "certificate": {
                "cert_file": "./mtls_certificates/client/embedding-service.crt",
                "key_file": "./mtls_certificates/client/embedding-service.key"
            },
            "ssl": {
                "enabled": True,
                "verify_ssl": True,  # This is TRUE, not FALSE
                "verify_hostname": False,  # This should disable hostname verification
                "ca_cert": "./mtls_certificates/ca/ca.crt"
                # verify_mode is NOT specified - should default to "CERT_REQUIRED"
            }
        }
    }
    
    print("Configuration analysis:")
    print(f"  - verify_ssl: {user_config['proxy_registration']['ssl']['verify_ssl']}")
    print(f"  - verify_hostname: {user_config['proxy_registration']['ssl']['verify_hostname']}")
    print(f"  - verify_mode: {user_config['proxy_registration']['ssl'].get('verify_mode', 'NOT SPECIFIED (defaults to CERT_REQUIRED)')}")
    
    try:
        manager = ProxyRegistrationManager(user_config)
        ssl_context = manager._create_ssl_context()
        
        print(f"\nSSL Context created:")
        print(f"  - check_hostname: {ssl_context.check_hostname}")
        print(f"  - verify_mode: {ssl_context.verify_mode} (2=CERT_REQUIRED)")
        
        # Expected behavior: verify_hostname: false should result in check_hostname: False
        expected_hostname_check = False
        actual_hostname_check = ssl_context.check_hostname
        
        print(f"\nExpected: check_hostname = {expected_hostname_check}")
        print(f"Actual:   check_hostname = {actual_hostname_check}")
        
        if actual_hostname_check == expected_hostname_check:
            print("✅ SUCCESS: verify_hostname: false correctly applied")
            return True
        else:
            print("❌ FAILURE: verify_hostname: false was IGNORED")
            print(f"   The SSL context still has hostname verification enabled!")
            return False
            
    except Exception as e:
        print(f"❌ Failed to create SSL context: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("🚀 Testing user's exact configuration for verify_hostname bug...")
    
    success = test_user_exact_config()
    
    if success:
        print("\n🎉 Test passed! verify_hostname configuration is working correctly.")
        print("   The bug report may be outdated or the configuration is different.")
    else:
        print("\n⚠️ Test failed! verify_hostname configuration is NOT working properly.")
        print("   The bug report is correct - verify_hostname is being ignored.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
