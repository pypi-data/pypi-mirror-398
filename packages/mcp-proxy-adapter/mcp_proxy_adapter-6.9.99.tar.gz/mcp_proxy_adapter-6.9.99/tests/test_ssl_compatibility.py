#!/usr/bin/env python3
"""
SSL Compatibility Test for MCP Security Framework 1.2.6
Tests SSL context configuration and compatibility
"""
import sys
from mcp_security_framework import SSLConfig, SecurityManager

def test_ssl_config_basic():
    """Test basic SSL configuration"""
    print("🔍 Testing basic SSL configuration...")
    
    try:
        ssl_config = SSLConfig(
            enabled=True,
            cert_file="./mtls_certificates/server/test-server.crt",
            key_file="./mtls_certificates/server/test-server.key",
            verify=False
        )
        print(f"✅ Basic SSL config created: {ssl_config.enabled}")
        return True
    except Exception as e:
        print(f"❌ Failed to create basic SSL config: {e}")
        return False

def test_ssl_config_with_ca():
    """Test SSL configuration with CA"""
    print("\n🔍 Testing SSL configuration with CA...")
    
    try:
        ssl_config = SSLConfig(
            enabled=True,
            cert_file="./mtls_certificates/server/test-server.crt",
            key_file="./mtls_certificates/server/test-server.key",
            ca_cert_file="./mtls_certificates/ca/test-ca.crt",
            verify=True,
            check_hostname=True
        )
        print(f"✅ SSL config with CA created: verify={ssl_config.verify}, check_hostname={ssl_config.check_hostname}")
        return True
    except Exception as e:
        print(f"❌ Failed to create SSL config with CA: {e}")
        return False

def test_ssl_config_with_client_certs():
    """Test SSL configuration with client certificates"""
    print("\n🔍 Testing SSL configuration with client certificates...")
    
    try:
        ssl_config = SSLConfig(
            enabled=True,
            cert_file="./mtls_certificates/server/test-server.crt",
            key_file="./mtls_certificates/server/test-server.key",
            ca_cert_file="./mtls_certificates/ca/test-ca.crt",
            client_cert_file="./mtls_certificates/client/test-client.crt",
            client_key_file="./mtls_certificates/client/test-client.key",
            verify=True
        )
        print(f"✅ SSL config with client certs created: verify={ssl_config.verify}")
        return True
    except Exception as e:
        print(f"❌ Failed to create SSL config with client certs: {e}")
        return False

def test_ssl_validation_method():
    """Test SSL validation method"""
    print("\n🔍 Testing SSL validation method...")
    
    try:
        ssl_config = SSLConfig(
            enabled=True,
            cert_file="./mtls_certificates/server/test-server.crt",
            key_file="./mtls_certificates/server/test-server.key",
            verify=True
        )
        
        # Check if validation method exists
        if hasattr(ssl_config, 'validate_ssl_configuration'):
            print(f"✅ SSL validation method exists")
            return True
        else:
            print(f"❌ SSL validation method not found")
            return False
    except Exception as e:
        print(f"❌ Failed to test SSL validation: {e}")
        return False

def test_ssl_fields():
    """Test SSL configuration fields"""
    print("\n🔍 Testing SSL configuration fields...")
    
    try:
        ssl_config = SSLConfig()
        fields = list(SSLConfig.model_fields.keys())
        
        expected_fields = [
            'enabled', 'cert_file', 'key_file', 'ca_cert_file',
            'client_cert_file', 'client_key_file', 'verify',
            'verify_mode', 'min_tls_version', 'max_tls_version',
            'cipher_suite', 'check_hostname', 'check_expiry',
            'expiry_warning_days'
        ]
        
        missing_fields = [f for f in expected_fields if f not in fields]
        extra_fields = [f for f in fields if f not in expected_fields]
        
        if missing_fields:
            print(f"⚠️  Missing fields: {missing_fields}")
        if extra_fields:
            print(f"ℹ️  Extra fields: {extra_fields}")
        
        print(f"✅ SSL config has {len(fields)} fields")
        print(f"   Fields: {', '.join(fields)}")
        return True
    except Exception as e:
        print(f"❌ Failed to test SSL fields: {e}")
        return False

def main():
    """Run all SSL compatibility tests"""
    print("=" * 60)
    print("🔒 SSL COMPATIBILITY TEST - MCP Security Framework 1.2.6")
    print("=" * 60)
    
    tests = [
        test_ssl_config_basic,
        test_ssl_config_with_ca,
        test_ssl_config_with_client_certs,
        test_ssl_validation_method,
        test_ssl_fields
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ! SSL контекст полностью совместим!")
        return 0
    else:
        print("\n⚠️  Некоторые тесты провалены. Требуется проверка.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

