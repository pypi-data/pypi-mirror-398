#!/usr/bin/env python3
"""
Ручной тест сервера
"""
import subprocess
import time
import requests

def test_manual():
    """Ручной тест"""
    print("🔍 Ручной тест сервера")
    
    # Запуск сервера в фоне
    cmd = [
        "python", "mcp_proxy_adapter/examples/full_application/main.py",
        "--config", "mcp_proxy_adapter/examples/full_application/configs/http_basic.json"
    ]
    
    print(f"🚀 Запуск команды: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    print(f"📊 PID процесса: {process.pid}")
    
    # Ждем запуска
    print("⏳ Ждем запуска сервера...")
    time.sleep(15)
    
    # Проверяем статус процесса
    poll = process.poll()
    print(f"📊 Статус процесса: {poll} (None = работает)")
    
    if poll is not None:
        stdout, stderr = process.communicate()
        print(f"❌ Процесс завершился с кодом {poll}")
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        return False
    
    # Тест подключения
    try:
        print("🔍 Тест подключения к серверу...")
        response = requests.get("http://localhost:8080/health", timeout=10)
        print(f"✅ Сервер отвечает: {response.status_code}")
        print(f"📄 Ответ: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    finally:
        # Остановка процесса
        print("🛑 Остановка сервера...")
        process.terminate()
        process.wait(timeout=5)

if __name__ == "__main__":
    test_manual()
