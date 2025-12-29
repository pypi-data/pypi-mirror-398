#!/usr/bin/env python3
"""
Тест для отладки middleware аутентификации
"""
import requests
import subprocess
import time
import json

def test_middleware_debug():
    """Тест middleware аутентификации"""
    print("🔍 Тестирование middleware аутентификации")
    
    # Запуск сервера
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/http_token.json"
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(8)
    
    print("\n1. Тест health endpoint без токена:")
    try:
        response = requests.get("http://localhost:8080/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Тест health endpoint с токеном:")
    try:
        headers = {"X-API-Key": "test-token"}
        response = requests.get("http://localhost:8080/health", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Тест JSON-RPC без токена:")
    try:
        data = {"jsonrpc": "2.0", "method": "echo", "params": {"message": "Hello"}, "id": 1}
        response = requests.post("http://localhost:8080/api/jsonrpc", json=data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n4. Тест JSON-RPC с токеном:")
    try:
        headers = {"X-API-Key": "test-token"}
        data = {"jsonrpc": "2.0", "method": "echo", "params": {"message": "Hello"}, "id": 1}
        response = requests.post("http://localhost:8080/api/jsonrpc", json=data, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n5. Тест JSON-RPC с admin-secret-key:")
    try:
        headers = {"X-API-Key": "admin-secret-key"}
        data = {"jsonrpc": "2.0", "method": "echo", "params": {"message": "Hello"}, "id": 1}
        response = requests.post("http://localhost:8080/api/jsonrpc", json=data, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Остановка сервера
    process.terminate()
    process.wait()
    print("\n✅ Тест завершен")

if __name__ == "__main__":
    test_middleware_debug()
