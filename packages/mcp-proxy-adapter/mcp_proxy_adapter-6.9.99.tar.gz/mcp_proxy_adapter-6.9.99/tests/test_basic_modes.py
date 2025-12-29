#!/usr/bin/env python3
"""
Базовый тест основных режимов MCP Proxy Adapter
"""
import requests
import subprocess
import time
import json

def test_http_basic():
    """Тест HTTP Basic"""
    print("\n🔍 Тестирование HTTP Basic")
    
    try:
        # Запуск сервера
        cmd = [
            "bash", "-c", "source .venv/bin/activate && python mcp_proxy_adapter/examples/full_application/main.py --config mcp_proxy_adapter/examples/full_application/configs/http_basic.json"
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        time.sleep(15)  # Ждем запуска
        
        # Тест health endpoint
        health_response = requests.get("http://localhost:8080/health", timeout=10)
        health_ok = health_response.status_code == 200
        
        # Тест JSON-RPC
        jsonrpc_response = requests.post(
            "http://localhost:8080/api/jsonrpc",
            json={"jsonrpc": "2.0", "method": "echo", "params": {"message": "Hello HTTP Basic"}, "id": 1},
            timeout=10
        )
        jsonrpc_ok = jsonrpc_response.status_code == 200
        
        result = {
            "mode": "HTTP Basic",
            "health": health_ok,
            "jsonrpc": jsonrpc_ok,
            "success": health_ok and jsonrpc_ok
        }
        
        print(f"✅ HTTP Basic: Health={health_ok}, JSON-RPC={jsonrpc_ok}")
        return result
        
    except Exception as e:
        print(f"❌ HTTP Basic failed: {e}")
        return {"mode": "HTTP Basic", "success": False, "error": str(e)}
    finally:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            pass

def test_http_token():
    """Тест HTTP + Token"""
    print("\n🔍 Тестирование HTTP + Token")
    
    try:
        # Запуск сервера
        cmd = [
            "bash", "-c", "source .venv/bin/activate && python mcp_proxy_adapter/examples/full_application/main.py --config mcp_proxy_adapter/examples/full_application/configs/http_token.json"
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        time.sleep(15)  # Ждем запуска
        
        # Тест health endpoint
        health_response = requests.get("http://localhost:8080/health", timeout=10)
        health_ok = health_response.status_code == 200
        
        # Тест JSON-RPC без токена (должен быть 401)
        jsonrpc_no_token = requests.post(
            "http://localhost:8080/api/jsonrpc",
            json={"jsonrpc": "2.0", "method": "echo", "params": {"message": "Hello"}, "id": 1},
            timeout=10
        )
        no_token_401 = jsonrpc_no_token.status_code == 401
        
        # Тест JSON-RPC с токеном
        jsonrpc_with_token = requests.post(
            "http://localhost:8080/api/jsonrpc",
            json={"jsonrpc": "2.0", "method": "echo", "params": {"message": "Hello HTTP Token"}, "id": 1},
            headers={"X-API-Key": "test-token"},
            timeout=10
        )
        jsonrpc_ok = jsonrpc_with_token.status_code == 200
        
        result = {
            "mode": "HTTP + Token",
            "health": health_ok,
            "no_token_401": no_token_401,
            "jsonrpc": jsonrpc_ok,
            "success": health_ok and no_token_401 and jsonrpc_ok
        }
        
        print(f"✅ HTTP + Token: Health={health_ok}, NoToken401={no_token_401}, JSON-RPC={jsonrpc_ok}")
        return result
        
    except Exception as e:
        print(f"❌ HTTP + Token failed: {e}")
        return {"mode": "HTTP + Token", "success": False, "error": str(e)}
    finally:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            pass

def main():
    """Основная функция"""
    print("🚀 Запуск базового тестирования MCP Proxy Adapter")
    print("=" * 60)
    
    # Очистка портов перед тестированием
    print("🧹 Очистка портов...")
    subprocess.run(["pkill", "-f", "python.*main.py"], capture_output=True)
    time.sleep(2)
    
    results = []
    
    # Тест HTTP Basic
    results.append(test_http_basic())
    time.sleep(5)  # Пауза между тестами
    
    # Тест HTTP + Token
    results.append(test_http_token())
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for result in results:
        status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
        mode = result.get("mode", "Unknown")
        print(f"{status}: {mode}")
        
        if result.get("success", False):
            passed += 1
        else:
            failed += 1
            if "error" in result:
                print(f"    Error: {result['error']}")
    
    print(f"\n🎯 РЕЗУЛЬТАТ: {passed}/{len(results)} тестов прошли успешно")
    
    if passed == len(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! MCP Proxy Adapter работает корректно!")
    else:
        print(f"⚠️  {failed} тестов не прошли. Требуется доработка.")
    
    # Сохранение результатов
    with open("test_basic_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Результаты сохранены в test_basic_results.json")

if __name__ == "__main__":
    main()
