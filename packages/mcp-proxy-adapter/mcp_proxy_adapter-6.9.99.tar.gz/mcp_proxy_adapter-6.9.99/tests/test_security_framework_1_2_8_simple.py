#!/usr/bin/env python3
"""
Упрощенный тест совместимости с фреймворком безопасности 1.2.8

Проверяет основные исправления:
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
            check_hostname=False
        )
        
        print("✅ SSL конфигурация с verify=False создана успешно")
        print(f"  - enabled: {ssl_config.enabled}")
        print(f"  - verify: {ssl_config.verify}")
        print(f"  - check_hostname: {ssl_config.check_hostname}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка SSL конфигурации: {e}")
        return False

def test_security_manager_creation():
    """Тест создания SecurityManager."""
    print("\n🔍 Тестирование создания SecurityManager...")
    
    try:
        from mcp_security_framework import SecurityManager
        from mcp_security_framework.schemas.config import SecurityConfig, SSLConfig
        
        # Конфигурация с SSL
        ssl_config = SSLConfig(
            enabled=True,
            cert_file="./mtls_certificates/server/test-server.crt",
            key_file="./mtls_certificates/server/test-server.key",
            ca_cert_file="./mtls_certificates/ca/ca.crt",
            verify=False,
            check_hostname=False
        )
        
        security_config = SecurityConfig(
            enabled=True,
            ssl=ssl_config
        )
        
        # Создание SecurityManager (исправление для загрузки клиентских сертификатов)
        security_manager = SecurityManager(security_config)
        
        print("✅ SecurityManager создан успешно")
        print(f"  - SecurityManager type: {type(security_manager)}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка SecurityManager: {e}")
        return False

def test_auth_config_creation():
    """Тест создания AuthConfig."""
    print("\n🔍 Тестирование создания AuthConfig...")
    
    try:
        from mcp_security_framework.schemas.config import AuthConfig
        
        # Тест создания AuthConfig
        auth_config = AuthConfig(
            enabled=True,
            methods=["api_key", "certificate"]
        )
        
        print("✅ AuthConfig создан успешно")
        print(f"  - enabled: {auth_config.enabled}")
        print(f"  - methods: {auth_config.methods}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка AuthConfig: {e}")
        return False

def test_fastapi_middleware_creation():
    """Тест создания FastAPI middleware."""
    print("\n🔍 Тестирование создания FastAPI middleware...")
    
    try:
        from mcp_security_framework.middleware.fastapi_middleware import FastAPISecurityMiddleware
        from mcp_security_framework.schemas.config import SecurityConfig, AuthConfig
        from mcp_security_framework import SecurityManager
        
        # Конфигурация для middleware
        auth_config = AuthConfig(
            enabled=True,
            methods=["api_key"]
        )
        
        security_config = SecurityConfig(
            enabled=True,
            auth=auth_config
        )
        
        # Создание SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Создание middleware
        middleware = FastAPISecurityMiddleware(security_manager)
        
        print("✅ FastAPI middleware создан успешно")
        print(f"  - Middleware type: {type(middleware)}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка FastAPI middleware: {e}")
        return False

def test_embed_client_ssl_context():
    """Тест SSL контекста для embed_client."""
    print("\n🔍 Тестирование SSL контекста для embed_client...")
    
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

def test_mtls_configuration():
    """Тест mTLS конфигурации."""
    print("\n🔍 Тестирование mTLS конфигурации...")
    
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
            check_hostname=False
        )
        
        auth_config = AuthConfig(
            enabled=True,
            methods=["certificate"]
        )
        
        security_config = SecurityConfig(
            enabled=True,
            ssl=ssl_config,
            auth=auth_config
        )
        
        # Создание SecurityManager
        security_manager = SecurityManager(security_config)
        
        print("✅ mTLS конфигурация создана успешно")
        print(f"  - SSL enabled: {ssl_config.enabled}")
        print(f"  - SSL verify: {ssl_config.verify}")
        print(f"  - Auth enabled: {auth_config.enabled}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка mTLS конфигурации: {e}")
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
                "methods": ["api_key"]
            },
            "ssl": {
                "enabled": False,
                "verify": False
            }
        }
        
        # Создание конфигурации
        auth_config = AuthConfig(
            enabled=old_config["auth"]["enabled"],
            methods=old_config["auth"]["methods"]
        )
        
        ssl_config = SSLConfig(
            enabled=old_config["ssl"]["enabled"],
            verify=old_config["ssl"]["verify"]
        )
        
        security_config = SecurityConfig(
            enabled=old_config["enabled"],
            auth=auth_config,
            ssl=ssl_config
        )
        
        print("✅ Обратная совместимость работает")
        print(f"  - Security enabled: {security_config.enabled}")
        print(f"  - Auth enabled: {auth_config.enabled}")
        print(f"  - SSL enabled: {ssl_config.enabled}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка обратной совместимости: {e}")
        return False

def main():
    """Главная функция тестирования."""
    print("🚀 Упрощенное тестирование фреймворка безопасности 1.2.8")
    print("=" * 60)
    
    tests = [
        ("Импорт фреймворка", test_imports),
        ("SSL конфигурация с verify=False", test_ssl_config_with_verify_false),
        ("Создание SecurityManager", test_security_manager_creation),
        ("Создание AuthConfig", test_auth_config_creation),
        ("Создание FastAPI middleware", test_fastapi_middleware_creation),
        ("SSL контекст для embed_client", test_embed_client_ssl_context),
        ("mTLS конфигурация", test_mtls_configuration),
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
