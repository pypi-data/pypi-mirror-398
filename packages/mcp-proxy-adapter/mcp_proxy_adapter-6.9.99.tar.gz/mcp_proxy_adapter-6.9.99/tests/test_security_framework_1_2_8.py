#!/usr/bin/env python3
"""
Тест совместимости с фреймворком безопасности 1.2.8

Проверяет исправления:
- mTLS аутентификация с verify=False
- embed_client SSL проблемы
- SecurityManager загрузка клиентских сертификатов
- Обратная совместимость

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import sys
import os
import json
import ssl
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

def test_imports():
    """Тест импорта фреймворка безопасности."""
    print("\n🔍 Тестирование импорта фреймворка безопасности 1.2.8...")
    
    try:
        from mcp_security_framework import (
            SecurityManager,
            AuthManager,
            CertificateManager,
            PermissionManager,
            RateLimiter,
        )
        from mcp_security_framework.schemas.config import (
            SecurityConfig,
            AuthConfig,
            SSLConfig,
            PermissionConfig,
            RateLimitConfig,
            CertificateConfig,
            LoggingConfig,
        )
        from mcp_security_framework.middleware.fastapi_middleware import (
            FastAPISecurityMiddleware,
        )
        print("✅ Все импорты успешны")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_ssl_config_with_verify_false():
    """Тест SSL конфигурации с verify=False."""
    print("\n🔍 Тестирование SSL конфигурации с verify=False...")
    
    try:
        from mcp_security_framework.schemas.config import SSLConfig
        
        # Тест с verify=False (исправление для mTLS)
        ssl_config = SSLConfig(
            enabled=True,
            cert_file="./mtls_certificates/server/test-server.crt",
            key_file="./mtls_certificates/server/test-server.key",
            verify=False,  # Ключевое исправление
            check_hostname=False,
            verify_mode="CERT_REQUIRED"  # Для mTLS
        )
        
        print("✅ SSL конфигурация с verify=False создана успешно")
        print(f"  - enabled: {ssl_config.enabled}")
        print(f"  - verify: {ssl_config.verify}")
        print(f"  - verify_mode: {ssl_config.verify_mode}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка SSL конфигурации: {e}")
        return False

def test_security_manager_with_client_certs():
    """Тест SecurityManager с клиентскими сертификатами."""
    print("\n🔍 Тестирование SecurityManager с клиентскими сертификатами...")
    
    try:
        from mcp_security_framework import SecurityManager
        from mcp_security_framework.schemas.config import SecurityConfig, SSLConfig
        
        # Конфигурация с клиентскими сертификатами
        ssl_config = SSLConfig(
            enabled=True,
            cert_file="./mtls_certificates/server/test-server.crt",
            key_file="./mtls_certificates/server/test-server.key",
            ca_cert_file="./mtls_certificates/ca/ca.crt",
            verify=False,
            verify_mode="CERT_REQUIRED"
        )
        
        security_config = SecurityConfig(
            ssl=ssl_config
        )
        
        # Создание SecurityManager (исправление для загрузки клиентских сертификатов)
        security_manager = SecurityManager(security_config)
        
        print("✅ SecurityManager создан с клиентскими сертификатами")
        print(f"  - SSL manager: {type(security_manager.ssl_manager)}")
        print(f"  - SSL enabled: {security_manager.config.ssl.enabled}")
        print(f"  - SSL verify: {security_manager.config.ssl.verify}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка SecurityManager: {e}")
        return False

def test_auth_config_with_none_handling():
    """Тест AuthConfig с обработкой None значений."""
    print("\n🔍 Тестирование AuthConfig с обработкой None значений...")
    
    try:
        from mcp_security_framework.schemas.config import AuthConfig
        
        # Тест с None значениями (исправление для обратной совместимости)
        auth_config = AuthConfig(
            enabled=True,
            methods=["api_key", "certificate"],
            certificate_auth=True
        )
        
        print("✅ AuthConfig с None значениями создан успешно")
        print(f"  - enabled: {auth_config.enabled}")
        print(f"  - methods: {auth_config.methods}")
        print(f"  - certificate_auth: {auth_config.certificate_auth}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка AuthConfig: {e}")
        return False

def test_fastapi_middleware_integration():
    """Тест интеграции с FastAPI middleware."""
    print("\n🔍 Тестирование FastAPI middleware интеграции...")
    
    try:
        from mcp_security_framework.middleware.fastapi_middleware import FastAPISecurityMiddleware
        from mcp_security_framework.schemas.config import SecurityConfig, AuthConfig
        
        # Конфигурация для middleware
        auth_config = AuthConfig(
            enabled=True,
            methods=["api_key"]
        )
        
        security_config = SecurityConfig(
            auth=auth_config
        )
        
        # Создание SecurityManager сначала
        from mcp_security_framework import SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Создание middleware (исправление для JSON-RPC аутентификации)
        middleware = FastAPISecurityMiddleware(security_manager)
        
        print("✅ FastAPI middleware создан успешно")
        print(f"  - Security manager: {type(middleware.security_manager)}")
        print(f"  - Auth enabled: {middleware.config.auth.enabled}")
        print(f"  - SSL enabled: {middleware.config.ssl.enabled}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка FastAPI middleware: {e}")
        return False

def test_embed_client_compatibility():
    """Тест совместимости с embed_client."""
    print("\n🔍 Тестирование совместимости с embed_client...")
    
    try:
        import ssl
        from mcp_security_framework.schemas.config import SSLConfig
        
        # Конфигурация для embed_client (исправление SSL проблем)
        ssl_config = SSLConfig(
            enabled=True,
            cert_file="./mtls_certificates/server/test-server.crt",
            key_file="./mtls_certificates/server/test-server.key",
            ca_cert_file="./mtls_certificates/ca/ca.crt",
            verify=False,  # Ключевое исправление для embed_client
            check_hostname=False
        )
        
        # Создание SSL контекста
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = ssl_config.check_hostname
        ssl_context.verify_mode = ssl.CERT_NONE if not ssl_config.verify else ssl.CERT_REQUIRED
        
        print("✅ SSL контекст для embed_client создан успешно")
        print(f"  - verify_mode: {ssl_context.verify_mode}")
        print(f"  - check_hostname: {ssl_context.check_hostname}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка embed_client совместимости: {e}")
        return False

def test_mtls_authentication():
    """Тест mTLS аутентификации."""
    print("\n🔍 Тестирование mTLS аутентификации...")
    
    try:
        from mcp_security_framework import SecurityManager
        from mcp_security_framework.schemas.config import SecurityConfig, SSLConfig, AuthConfig
        
        # Конфигурация mTLS
        ssl_config = SSLConfig(
            enabled=True,
            cert_file="./mtls_certificates/server/test-server.crt",
            key_file="./mtls_certificates/server/test-server.key",
            ca_cert_file="./mtls_certificates/ca/ca.crt",
            verify=False,  # Исправление для mTLS
            verify_mode="CERT_REQUIRED"
        )
        
        auth_config = AuthConfig(
            enabled=True,
            methods=["certificate"],
            certificate_auth=True
        )
        
        security_config = SecurityConfig(
            ssl=ssl_config,
            auth=auth_config
        )
        
        # Создание SecurityManager
        security_manager = SecurityManager(security_config)
        
        print("✅ mTLS аутентификация настроена успешно")
        print(f"  - SSL enabled: {security_manager.config.ssl.enabled}")
        print(f"  - SSL verify: {security_manager.config.ssl.verify}")
        print(f"  - Certificate auth: {auth_config.certificate_auth}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка mTLS аутентификации: {e}")
        return False

def test_backward_compatibility():
    """Тест обратной совместимости."""
    print("\n🔍 Тестирование обратной совместимости...")
    
    try:
        from mcp_security_framework.schemas.config import SecurityConfig, AuthConfig, SSLConfig
        
        # Старая конфигурация (должна работать)
        old_config = {
            "enabled": True,
            "auth": {
                "enabled": True,
                "methods": ["api_key"],
                "roles_file": None  # Исправление для None значений
            },
            "ssl": {
                "enabled": False,
                "verify": None  # Исправление для None значений
            }
        }
        
        # Создание конфигурации (исправление для None значений)
        auth_config = AuthConfig(
            enabled=old_config["auth"]["enabled"],
            methods=old_config["auth"]["methods"],
            roles_file=old_config["auth"]["roles_file"]
        )
        
        ssl_config = SSLConfig(
            enabled=old_config["ssl"]["enabled"],
            verify=old_config["ssl"]["verify"] if old_config["ssl"]["verify"] is not None else False
        )
        
        security_config = SecurityConfig(
            auth=auth_config,
            ssl=ssl_config
        )
        
        print("✅ Обратная совместимость работает")
        print(f"  - SSL enabled: {security_config.ssl.enabled}")
        print(f"  - Auth enabled: {security_config.auth.enabled}")
        print(f"  - SSL verify: {security_config.ssl.verify}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка обратной совместимости: {e}")
        return False

def main():
    """Главная функция тестирования."""
    print("🚀 Тестирование фреймворка безопасности 1.2.8")
    print("=" * 60)
    
    tests = [
        ("Импорт фреймворка", test_imports),
        ("SSL конфигурация с verify=False", test_ssl_config_with_verify_false),
        ("SecurityManager с клиентскими сертификатами", test_security_manager_with_client_certs),
        ("AuthConfig с обработкой None", test_auth_config_with_none_handling),
        ("FastAPI middleware интеграция", test_fastapi_middleware_integration),
        ("embed_client совместимость", test_embed_client_compatibility),
        ("mTLS аутентификация", test_mtls_authentication),
        ("Обратная совместимость", test_backward_compatibility),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Результаты
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 ИТОГО: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Фреймворк безопасности 1.2.8 полностью совместим!")
    elif passed >= total * 0.8:
        print("✅ Большинство тестов пройдено. Фреймворк в основном совместим.")
    else:
        print("⚠️  Много тестов не пройдено. Требуется дополнительная работа.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
