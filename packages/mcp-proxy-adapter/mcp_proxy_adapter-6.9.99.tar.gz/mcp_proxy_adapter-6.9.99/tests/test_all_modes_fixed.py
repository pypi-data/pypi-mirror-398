#!/usr/bin/env python3
"""
Полный тест всех 8 режимов MCP Proxy Adapter с уникальными портами
Согласно правилам проекта
"""
import requests
import subprocess
import time
import os
import signal
import sys
from typing import Dict, Any, List, Tuple

class MCPProxyAdapterTester:
    """Класс для тестирования всех режимов MCP Proxy Adapter"""
    
    def __init__(self):
        self.results = []
        self.processes = []
        self.base_url = "http://localhost"
        self.https_base_url = "https://localhost"
        
        # Уникальные порты для каждого режима
        self.ports = {
            "http_basic": 15000,
            "http_token": 15001,
            "http_roles": 15002,
            "https_basic": 15003,
            "https_token": 15004,
            "https_roles": 15005,
            "mtls_basic": 15006,
            "mtls_roles": 15007
        }
        
    def cleanup_processes(self):
        """Очистка всех процессов"""
        print("🧹 Очистка процессов...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        # Дополнительная очистка
        os.system("pkill -f 'python.*main.py' 2>/dev/null || true")
        time.sleep(2)
        
    def start_proxy_server(self):
        """Запуск тестового прокси сервера"""
        print("🚀 Запуск тестового прокси сервера...")
        try:
            cmd = [
                "python", "mcp_proxy_adapter/examples/run_proxy_server.py",
                "--host", "0.0.0.0", "--port", "3005"
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(process)
            time.sleep(3)
            
            # Проверка что прокси запустился
            try:
                response = requests.get("http://localhost:3005/servers", timeout=5)
                if response.status_code == 200:
                    print("✅ Прокси сервер запущен успешно")
                    return True
            except:
                pass
                
            print("⚠️ Прокси сервер не отвечает, продолжаем без него")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка запуска прокси сервера: {e}")
            return False
    
    def test_http_basic(self) -> Dict[str, Any]:
        """Тест HTTP Basic (порт 15000)"""
        port = self.ports["http_basic"]
        print(f"\n🔍 Тестирование HTTP Basic (порт {port})")
        
        try:
            # Запуск сервера
            cmd = [
                "python", "mcp_proxy_adapter/examples/full_application/main.py",
                "--config", "mcp_proxy_adapter/examples/full_application/configs/http_basic.json",
                "--port", str(port)
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(process)
            time.sleep(5)
            
            # Тест health endpoint
            health_url = f"{self.base_url}:{port}/health"
            health_response = requests.get(health_url, timeout=10)
            
            # Тест JSON-RPC
            jsonrpc_url = f"{self.base_url}:{port}/api/jsonrpc"
            jsonrpc_data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Hello HTTP Basic"},
                "id": 1
            }
            jsonrpc_response = requests.post(jsonrpc_url, json=jsonrpc_data, timeout=10)
            
            success = (health_response.status_code == 200 and 
                      jsonrpc_response.status_code == 200)
            
            result = {
                "mode": "HTTP Basic",
                "port": port,
                "success": success,
                "health_status": health_response.status_code,
                "jsonrpc_status": jsonrpc_response.status_code,
                "health_response": health_response.json() if health_response.status_code == 200 else None,
                "jsonrpc_response": jsonrpc_response.json() if jsonrpc_response.status_code == 200 else None
            }
            
            print(f"✅ HTTP Basic: {'PASS' if success else 'FAIL'}")
            return result
            
        except Exception as e:
            print(f"❌ HTTP Basic: ERROR - {e}")
            return {
                "mode": "HTTP Basic",
                "port": port,
                "success": False,
                "error": str(e)
            }
    
    def test_http_token(self) -> Dict[str, Any]:
        """Тест HTTP + Token (порт 15001)"""
        port = self.ports["http_token"]
        print(f"\n🔍 Тестирование HTTP + Token (порт {port})")
        
        try:
            # Запуск сервера
            cmd = [
                "python", "mcp_proxy_adapter/examples/full_application/main.py",
                "--config", "mcp_proxy_adapter/examples/full_application/configs/http_token.json",
                "--port", str(port)
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(process)
            time.sleep(5)
            
            headers = {"X-API-Key": "admin-secret-key"}
            
            # Тест health endpoint
            health_url = f"{self.base_url}:{port}/health"
            health_response = requests.get(health_url, headers=headers, timeout=10)
            
            # Тест JSON-RPC
            jsonrpc_url = f"{self.base_url}:{port}/api/jsonrpc"
            jsonrpc_data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Hello HTTP Token"},
                "id": 1
            }
            jsonrpc_response = requests.post(jsonrpc_url, json=jsonrpc_data, headers=headers, timeout=10)
            
            success = (health_response.status_code == 200 and 
                      jsonrpc_response.status_code == 200)
            
            result = {
                "mode": "HTTP + Token",
                "port": port,
                "success": success,
                "health_status": health_response.status_code,
                "jsonrpc_status": jsonrpc_response.status_code,
                "health_response": health_response.json() if health_response.status_code == 200 else None,
                "jsonrpc_response": jsonrpc_response.json() if jsonrpc_response.status_code == 200 else None
            }
            
            print(f"✅ HTTP + Token: {'PASS' if success else 'FAIL'}")
            return result
            
        except Exception as e:
            print(f"❌ HTTP + Token: ERROR - {e}")
            return {
                "mode": "HTTP + Token",
                "port": port,
                "success": False,
                "error": str(e)
            }
    
    def test_http_token_roles(self) -> Dict[str, Any]:
        """Тест HTTP + Token + Roles (порт 15002)"""
        port = self.ports["http_roles"]
        print(f"\n🔍 Тестирование HTTP + Token + Roles (порт {port})")
        
        try:
            # Запуск сервера
            cmd = [
                "python", "mcp_proxy_adapter/examples/full_application/main.py",
                "--config", "mcp_proxy_adapter/examples/full_application/configs/http_token_roles.json",
                "--port", str(port)
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(process)
            time.sleep(5)
            
            headers = {"X-API-Key": "admin-secret-key"}
            
            # Тест health endpoint
            health_url = f"{self.base_url}:{port}/health"
            health_response = requests.get(health_url, headers=headers, timeout=10)
            
            # Тест JSON-RPC
            jsonrpc_url = f"{self.base_url}:{port}/api/jsonrpc"
            jsonrpc_data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Hello HTTP Token Roles"},
                "id": 1
            }
            jsonrpc_response = requests.post(jsonrpc_url, json=jsonrpc_data, headers=headers, timeout=10)
            
            success = (health_response.status_code == 200 and 
                      jsonrpc_response.status_code == 200)
            
            result = {
                "mode": "HTTP + Token + Roles",
                "port": port,
                "success": success,
                "health_status": health_response.status_code,
                "jsonrpc_status": jsonrpc_response.status_code,
                "health_response": health_response.json() if health_response.status_code == 200 else None,
                "jsonrpc_response": jsonrpc_response.json() if jsonrpc_response.status_code == 200 else None
            }
            
            print(f"✅ HTTP + Token + Roles: {'PASS' if success else 'FAIL'}")
            return result
            
        except Exception as e:
            print(f"❌ HTTP + Token + Roles: ERROR - {e}")
            return {
                "mode": "HTTP + Token + Roles",
                "port": port,
                "success": False,
                "error": str(e)
            }
    
    def test_https_basic(self) -> Dict[str, Any]:
        """Тест HTTPS Basic (порт 15003)"""
        port = self.ports["https_basic"]
        print(f"\n🔍 Тестирование HTTPS Basic (порт {port})")
        
        try:
            # Запуск сервера
            cmd = [
                "python", "mcp_proxy_adapter/examples/full_application/main.py",
                "--config", "mcp_proxy_adapter/examples/full_application/configs/https_basic.json",
                "--port", str(port)
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(process)
            time.sleep(5)
            
            # Тест health endpoint
            health_url = f"{self.https_base_url}:{port}/health"
            health_response = requests.get(health_url, verify=False, timeout=10)
            
            # Тест JSON-RPC
            jsonrpc_url = f"{self.https_base_url}:{port}/api/jsonrpc"
            jsonrpc_data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Hello HTTPS Basic"},
                "id": 1
            }
            jsonrpc_response = requests.post(jsonrpc_url, json=jsonrpc_data, verify=False, timeout=10)
            
            success = (health_response.status_code == 200 and 
                      jsonrpc_response.status_code == 200)
            
            result = {
                "mode": "HTTPS Basic",
                "port": port,
                "success": success,
                "health_status": health_response.status_code,
                "jsonrpc_status": jsonrpc_response.status_code,
                "health_response": health_response.json() if health_response.status_code == 200 else None,
                "jsonrpc_response": jsonrpc_response.json() if jsonrpc_response.status_code == 200 else None
            }
            
            print(f"✅ HTTPS Basic: {'PASS' if success else 'FAIL'}")
            return result
            
        except Exception as e:
            print(f"❌ HTTPS Basic: ERROR - {e}")
            return {
                "mode": "HTTPS Basic",
                "port": port,
                "success": False,
                "error": str(e)
            }
    
    def test_https_token(self) -> Dict[str, Any]:
        """Тест HTTPS + Token (порт 15004)"""
        port = self.ports["https_token"]
        print(f"\n🔍 Тестирование HTTPS + Token (порт {port})")
        
        try:
            # Запуск сервера
            cmd = [
                "python", "mcp_proxy_adapter/examples/full_application/main.py",
                "--config", "mcp_proxy_adapter/examples/full_application/configs/https_token.json",
                "--port", str(port)
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(process)
            time.sleep(5)
            
            headers = {"X-API-Key": "admin-secret-key-https"}
            
            # Тест health endpoint
            health_url = f"{self.https_base_url}:{port}/health"
            health_response = requests.get(health_url, verify=False, headers=headers, timeout=10)
            
            # Тест JSON-RPC
            jsonrpc_url = f"{self.https_base_url}:{port}/api/jsonrpc"
            jsonrpc_data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Hello HTTPS Token"},
                "id": 1
            }
            jsonrpc_response = requests.post(jsonrpc_url, json=jsonrpc_data, verify=False, headers=headers, timeout=10)
            
            success = (health_response.status_code == 200 and 
                      jsonrpc_response.status_code == 200)
            
            result = {
                "mode": "HTTPS + Token",
                "port": port,
                "success": success,
                "health_status": health_response.status_code,
                "jsonrpc_status": jsonrpc_response.status_code,
                "health_response": health_response.json() if health_response.status_code == 200 else None,
                "jsonrpc_response": jsonrpc_response.json() if jsonrpc_response.status_code == 200 else None
            }
            
            print(f"✅ HTTPS + Token: {'PASS' if success else 'FAIL'}")
            return result
            
        except Exception as e:
            print(f"❌ HTTPS + Token: ERROR - {e}")
            return {
                "mode": "HTTPS + Token",
                "port": port,
                "success": False,
                "error": str(e)
            }
    
    def test_https_token_roles(self) -> Dict[str, Any]:
        """Тест HTTPS + Token + Roles (порт 15005)"""
        port = self.ports["https_roles"]
        print(f"\n🔍 Тестирование HTTPS + Token + Roles (порт {port})")
        
        try:
            # Запуск сервера
            cmd = [
                "python", "mcp_proxy_adapter/examples/full_application/main.py",
                "--config", "mcp_proxy_adapter/examples/full_application/configs/https_token_roles.json",
                "--port", str(port)
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(process)
            time.sleep(5)
            
            headers = {"X-API-Key": "admin-secret-key-https"}
            
            # Тест health endpoint
            health_url = f"{self.https_base_url}:{port}/health"
            health_response = requests.get(health_url, verify=False, headers=headers, timeout=10)
            
            # Тест JSON-RPC
            jsonrpc_url = f"{self.https_base_url}:{port}/api/jsonrpc"
            jsonrpc_data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Hello HTTPS Token Roles"},
                "id": 1
            }
            jsonrpc_response = requests.post(jsonrpc_url, json=jsonrpc_data, verify=False, headers=headers, timeout=10)
            
            success = (health_response.status_code == 200 and 
                      jsonrpc_response.status_code == 200)
            
            result = {
                "mode": "HTTPS + Token + Roles",
                "port": port,
                "success": success,
                "health_status": health_response.status_code,
                "jsonrpc_status": jsonrpc_response.status_code,
                "health_response": health_response.json() if health_response.status_code == 200 else None,
                "jsonrpc_response": jsonrpc_response.json() if jsonrpc_response.status_code == 200 else None
            }
            
            print(f"✅ HTTPS + Token + Roles: {'PASS' if success else 'FAIL'}")
            return result
            
        except Exception as e:
            print(f"❌ HTTPS + Token + Roles: ERROR - {e}")
            return {
                "mode": "HTTPS + Token + Roles",
                "port": port,
                "success": False,
                "error": str(e)
            }
    
    def test_mtls_basic(self) -> Dict[str, Any]:
        """Тест mTLS Basic (порт 15006)"""
        port = self.ports["mtls_basic"]
        print(f"\n🔍 Тестирование mTLS Basic (порт {port})")
        
        try:
            # Запуск сервера
            cmd = [
                "python", "mcp_proxy_adapter/examples/full_application/main.py",
                "--config", "mcp_proxy_adapter/examples/full_application/configs/mtls_no_roles_correct.json",
                "--port", str(port)
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(process)
            time.sleep(5)
            
            # Настройка mTLS сертификатов
            cert_file = "mtls_certificates/client/test-client.crt"
            key_file = "mtls_certificates/client/test-client.key"
            ca_file = "mtls_certificates/ca/ca.crt"
            
            headers = {"X-API-Key": "admin-secret-key-mtls"}
            
            # Тест health endpoint
            health_url = f"{self.https_base_url}:{port}/health"
            health_response = requests.get(
                health_url, 
                verify=False, 
                cert=(cert_file, key_file),
                headers=headers,
                timeout=10
            )
            
            # Тест JSON-RPC
            jsonrpc_url = f"{self.https_base_url}:{port}/api/jsonrpc"
            jsonrpc_data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Hello mTLS Basic"},
                "id": 1
            }
            jsonrpc_response = requests.post(
                jsonrpc_url, 
                json=jsonrpc_data, 
                verify=False, 
                cert=(cert_file, key_file),
                headers=headers,
                timeout=10
            )
            
            success = (health_response.status_code == 200 and 
                      jsonrpc_response.status_code == 200)
            
            result = {
                "mode": "mTLS Basic",
                "port": port,
                "success": success,
                "health_status": health_response.status_code,
                "jsonrpc_status": jsonrpc_response.status_code,
                "health_response": health_response.json() if health_response.status_code == 200 else None,
                "jsonrpc_response": jsonrpc_response.json() if jsonrpc_response.status_code == 200 else None
            }
            
            print(f"✅ mTLS Basic: {'PASS' if success else 'FAIL'}")
            return result
            
        except Exception as e:
            print(f"❌ mTLS Basic: ERROR - {e}")
            return {
                "mode": "mTLS Basic",
                "port": port,
                "success": False,
                "error": str(e)
            }
    
    def test_mtls_roles(self) -> Dict[str, Any]:
        """Тест mTLS + Roles (порт 15007)"""
        port = self.ports["mtls_roles"]
        print(f"\n🔍 Тестирование mTLS + Roles (порт {port})")
        
        try:
            # Запуск сервера
            cmd = [
                "python", "mcp_proxy_adapter/examples/full_application/main.py",
                "--config", "mcp_proxy_adapter/examples/full_application/configs/mtls_with_roles_correct.json",
                "--port", str(port)
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(process)
            time.sleep(5)
            
            # Настройка mTLS сертификатов
            cert_file = "mtls_certificates/client/test-client.crt"
            key_file = "mtls_certificates/client/test-client.key"
            ca_file = "mtls_certificates/ca/ca.crt"
            
            headers = {"X-API-Key": "admin-secret-key-mtls"}
            
            # Тест health endpoint
            health_url = f"{self.https_base_url}:{port}/health"
            health_response = requests.get(
                health_url, 
                verify=False, 
                cert=(cert_file, key_file),
                headers=headers,
                timeout=10
            )
            
            # Тест JSON-RPC
            jsonrpc_url = f"{self.https_base_url}:{port}/api/jsonrpc"
            jsonrpc_data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Hello mTLS Roles"},
                "id": 1
            }
            jsonrpc_response = requests.post(
                jsonrpc_url, 
                json=jsonrpc_data, 
                verify=False, 
                cert=(cert_file, key_file),
                headers=headers,
                timeout=10
            )
            
            success = (health_response.status_code == 200 and 
                      jsonrpc_response.status_code == 200)
            
            result = {
                "mode": "mTLS + Roles",
                "port": port,
                "success": success,
                "health_status": health_response.status_code,
                "jsonrpc_status": jsonrpc_response.status_code,
                "health_response": health_response.json() if health_response.status_code == 200 else None,
                "jsonrpc_response": jsonrpc_response.json() if jsonrpc_response.status_code == 200 else None
            }
            
            print(f"✅ mTLS + Roles: {'PASS' if success else 'FAIL'}")
            return result
            
        except Exception as e:
            print(f"❌ mTLS + Roles: ERROR - {e}")
            return {
                "mode": "mTLS + Roles",
                "port": port,
                "success": False,
                "error": str(e)
            }
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 Запуск полного тестирования MCP Proxy Adapter")
        print("=" * 60)
        
        # Очистка перед началом
        self.cleanup_processes()
        
        # Запуск прокси сервера
        proxy_started = self.start_proxy_server()
        
        # Список всех тестов
        tests = [
            self.test_http_basic,
            self.test_http_token,
            self.test_http_token_roles,
            self.test_https_basic,
            self.test_https_token,
            self.test_https_token_roles,
            self.test_mtls_basic,
            self.test_mtls_roles
        ]
        
        # Запуск тестов
        for i, test_func in enumerate(tests, 1):
            print(f"\n{'='*20} ТЕСТ {i}/8 {'='*20}")
            result = test_func()
            self.results.append(result)
            
            # Очистка между тестами
            self.cleanup_processes()
            time.sleep(2)
        
        # Финальная очистка
        self.cleanup_processes()
        
        # Анализ результатов
        self.analyze_results()
    
    def analyze_results(self):
        """Анализ результатов тестирования"""
        print("\n" + "="*60)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.get("success", False))
        failed_tests = total_tests - passed_tests
        
        print(f"Всего тестов: {total_tests}")
        print(f"✅ Успешно: {passed_tests}")
        print(f"❌ Неудачно: {failed_tests}")
        print(f"📈 Успешность: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print("-" * 60)
        
        for i, result in enumerate(self.results, 1):
            mode = result.get("mode", f"Тест {i}")
            success = result.get("success", False)
            port = result.get("port", "N/A")
            status = "✅ PASS" if success else "❌ FAIL"
            
            print(f"{i:2d}. {mode:<25} Порт {port:<5} {status}")
            
            if not success and "error" in result:
                print(f"    Ошибка: {result['error']}")
            elif not success:
                health_status = result.get("health_status", "N/A")
                jsonrpc_status = result.get("jsonrpc_status", "N/A")
                print(f"    Health: {health_status}, JSON-RPC: {jsonrpc_status}")
        
        print("\n" + "="*60)
        
        if passed_tests == total_tests:
            print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            print("MCP Proxy Adapter работает корректно во всех режимах")
        else:
            print("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
            print("Проверьте конфигурацию и сертификаты")
        
        return passed_tests == total_tests

def main():
    """Основная функция"""
    print("🧪 MCP Proxy Adapter - Полное тестирование всех режимов")
    print("Версия: 6.9.18")
    print("Дата: 2025-01-12")
    print("Порты: 15000-15007 (уникальные для каждого режима)")
    print()
    
    tester = MCPProxyAdapterTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        tester.cleanup_processes()
        return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        tester.cleanup_processes()
        return 1

if __name__ == "__main__":
    sys.exit(main())
