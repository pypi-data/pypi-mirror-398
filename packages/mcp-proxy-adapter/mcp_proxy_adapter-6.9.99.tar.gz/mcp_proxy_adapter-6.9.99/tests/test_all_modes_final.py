#!/usr/bin/env python3
"""
Полный тест всех режимов MCP Proxy Adapter
"""
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

CONFIG_DIR = Path("mcp_proxy_adapter/examples/full_application/configs")


class MCPProxyTester:
    """Тестер всех режимов MCP Proxy Adapter"""

    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.results: List[Dict[str, Any]] = []
        self._config_cache: Dict[str, Dict[str, Any]] = {}

    def cleanup(self):
        """Очистка процессов"""
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
        self.processes.clear()
        # Дополнительная очистка через pkill
        import os
        os.system("pkill -f 'python.*main.py' 2>/dev/null")
        time.sleep(2)

    def test_http_basic(self) -> Dict[str, Any]:
        """Тест HTTP Basic (порт 8080)"""
        print("\n🔍 Тестирование HTTP Basic (порт 8080)")

        try:
            config_path = self._config_path("http_basic.json")
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/full_application/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            # Ждем запуска сервера с проверкой готовности
            max_wait = 20
            wait_interval = 1
            for _ in range(max_wait):
                try:
                    response = requests.get("http://localhost:8080/health", timeout=2)
                    if response.status_code == 200:
                        break
                except Exception:
                    pass
                time.sleep(wait_interval)
            else:
                # Если сервер не запустился, ждем еще немного
                time.sleep(5)

            # Тест health endpoint
            health_response = requests.get("http://localhost:8080/health", timeout=10)
            health_ok = health_response.status_code == 200

            # Тест JSON-RPC
            jsonrpc_response = requests.post(
                "http://localhost:8080/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "echo",
                    "params": {"message": "Hello HTTP Basic"},
                    "id": 1,
                },
                timeout=10,
            )
            jsonrpc_ok = jsonrpc_response.status_code == 200

            result = {
                "mode": "HTTP Basic",
                "port": 8080,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "success": health_ok and jsonrpc_ok,
            }

            print(f"✅ HTTP Basic: Health={health_ok}, JSON-RPC={jsonrpc_ok}")
            return result

        except Exception as e:
            print(f"❌ HTTP Basic failed: {e}")
            return {"mode": "HTTP Basic", "success": False, "error": str(e)}

    def test_http_token(self) -> Dict[str, Any]:
        """Тест HTTP + Token (порт 8080)"""
        print("\n🔍 Тестирование HTTP + Token (порт 8080)")

        try:
            config_path = self._config_path("http_token.json")
            token = self._get_api_token(config_path)
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/full_application/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            # Ждем запуска сервера с проверкой готовности
            max_wait = 20
            wait_interval = 1
            for _ in range(max_wait):
                try:
                    response = requests.get("http://localhost:8080/health", timeout=2)
                    if response.status_code == 200:
                        break
                except Exception:
                    pass
                time.sleep(wait_interval)
            else:
                # Если сервер не запустился, ждем еще немного
                time.sleep(5)

            # Тест health endpoint с токеном
            health_response = requests.get("http://localhost:8080/health", timeout=10)
            health_ok = health_response.status_code == 200

            # Тест JSON-RPC без токена (должен быть 401)
            jsonrpc_no_token = requests.post(
                "http://localhost:8080/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "echo",
                    "params": {"message": "Hello"},
                    "id": 1,
                },
                timeout=10,
            )
            no_token_401 = jsonrpc_no_token.status_code == 401

            # Тест JSON-RPC с токеном
            jsonrpc_with_token = requests.post(
                "http://localhost:8080/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "echo",
                    "params": {"message": "Hello HTTP Token"},
                    "id": 1,
                },
                headers={"X-API-Key": token},
                timeout=10,
            )
            jsonrpc_ok = jsonrpc_with_token.status_code == 200

            result = {
                "mode": "HTTP + Token",
                "port": 8080,
                "health": health_ok,
                "no_token_401": no_token_401,
                "jsonrpc": jsonrpc_ok,
                "success": health_ok and no_token_401 and jsonrpc_ok,
            }

            print(
                f"✅ HTTP + Token: Health={health_ok}, NoToken401={no_token_401}, JSON-RPC={jsonrpc_ok}"
            )
            return result

        except Exception as e:
            print(f"❌ HTTP + Token failed: {e}")
            return {"mode": "HTTP + Token", "success": False, "error": str(e)}

    def test_http_token_roles(self) -> Dict[str, Any]:
        """Тест HTTP + Token + Roles (порт 8080)"""
        print("\n🔍 Тестирование HTTP + Token + Roles (порт 8080)")

        try:
            config_path = self._config_path("http_token_roles.json")
            token = self._get_api_token(config_path)
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/full_application/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            # Ждем запуска сервера с проверкой готовности
            max_wait = 20
            wait_interval = 1
            for _ in range(max_wait):
                try:
                    response = requests.get("http://localhost:8080/health", timeout=2)
                    if response.status_code == 200:
                        break
                except Exception:
                    pass
                time.sleep(wait_interval)
            else:
                # Если сервер не запустился, ждем еще немного
                time.sleep(5)

            # Тест health endpoint
            health_response = requests.get("http://localhost:8080/health", timeout=10)
            health_ok = health_response.status_code == 200

            # Тест JSON-RPC с токеном
            jsonrpc_response = requests.post(
                "http://localhost:8080/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "echo",
                    "params": {"message": "Hello HTTP Token Roles"},
                    "id": 1,
                },
                headers={"X-API-Key": token},
                timeout=10,
            )
            jsonrpc_ok = jsonrpc_response.status_code == 200

            result = {
                "mode": "HTTP + Token + Roles",
                "port": 8080,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "success": health_ok and jsonrpc_ok,
            }

            print(f"✅ HTTP + Token + Roles: Health={health_ok}, JSON-RPC={jsonrpc_ok}")
            return result

        except Exception as e:
            print(f"❌ HTTP + Token + Roles failed: {e}")
            return {"mode": "HTTP + Token + Roles", "success": False, "error": str(e)}

    def test_https_basic(self) -> Dict[str, Any]:
        """Тест HTTPS Basic (порт 8443)"""
        print("\n🔍 Тестирование HTTPS Basic (порт 8443)")

        try:
            config_path = self._config_path("https_basic.json")
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/full_application/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            # Ждем запуска сервера с проверкой готовности
            max_wait = 20
            wait_interval = 1
            for _ in range(max_wait):
                try:
                    response = requests.get("https://localhost:8443/health", verify=False, timeout=2)
                    if response.status_code == 200:
                        break
                except Exception:
                    pass
                time.sleep(wait_interval)
            else:
                # Если сервер не запустился, ждем еще немного
                time.sleep(5)

            # Тест health endpoint
            health_response = requests.get(
                "https://localhost:8443/health", verify=False, timeout=10
            )
            health_ok = health_response.status_code == 200

            # Тест JSON-RPC
            jsonrpc_response = requests.post(
                "https://localhost:8443/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "echo",
                    "params": {"message": "Hello HTTPS Basic"},
                    "id": 1,
                },
                verify=False,
                timeout=10,
            )
            jsonrpc_ok = jsonrpc_response.status_code == 200

            result = {
                "mode": "HTTPS Basic",
                "port": 8443,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "success": health_ok and jsonrpc_ok,
            }

            print(f"✅ HTTPS Basic: Health={health_ok}, JSON-RPC={jsonrpc_ok}")
            return result

        except Exception as e:
            print(f"❌ HTTPS Basic failed: {e}")
            return {"mode": "HTTPS Basic", "success": False, "error": str(e)}

    def test_https_token(self) -> Dict[str, Any]:
        """Тест HTTPS + Token (порт 8443)"""
        print("\n🔍 Тестирование HTTPS + Token (порт 8443)")

        try:
            config_path = self._config_path("https_token.json")
            token = self._get_api_token(config_path)
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/full_application/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            # Ждем запуска сервера с проверкой готовности
            max_wait = 20
            wait_interval = 1
            for _ in range(max_wait):
                try:
                    response = requests.get("https://localhost:8443/health", verify=False, timeout=2)
                    if response.status_code == 200:
                        break
                except Exception:
                    pass
                time.sleep(wait_interval)
            else:
                # Если сервер не запустился, ждем еще немного
                time.sleep(5)

            # Тест health endpoint
            health_response = requests.get(
                "https://localhost:8443/health", verify=False, timeout=10
            )
            health_ok = health_response.status_code == 200

            # Тест JSON-RPC с токеном
            jsonrpc_response = requests.post(
                "https://localhost:8443/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "echo",
                    "params": {"message": "Hello HTTPS Token"},
                    "id": 1,
                },
                headers={"X-API-Key": token},
                verify=False,
                timeout=10,
            )
            jsonrpc_ok = jsonrpc_response.status_code == 200

            result = {
                "mode": "HTTPS + Token",
                "port": 8443,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "success": health_ok and jsonrpc_ok,
            }

            print(f"✅ HTTPS + Token: Health={health_ok}, JSON-RPC={jsonrpc_ok}")
            return result

        except Exception as e:
            print(f"❌ HTTPS + Token failed: {e}")
            return {"mode": "HTTPS + Token", "success": False, "error": str(e)}

    def test_https_token_roles(self) -> Dict[str, Any]:
        """Тест HTTPS + Token + Roles (порт 8443)"""
        print("\n🔍 Тестирование HTTPS + Token + Roles (порт 8443)")

        try:
            config_path = self._config_path("https_token_roles.json")
            token = self._get_api_token(config_path)
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/full_application/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            # Ждем запуска сервера с проверкой готовности
            max_wait = 20
            wait_interval = 1
            for _ in range(max_wait):
                try:
                    response = requests.get("https://localhost:8443/health", verify=False, timeout=2)
                    if response.status_code == 200:
                        break
                except Exception:
                    pass
                time.sleep(wait_interval)
            else:
                # Если сервер не запустился, ждем еще немного
                time.sleep(5)

            # Тест health endpoint
            health_response = requests.get(
                "https://localhost:8443/health", verify=False, timeout=10
            )
            health_ok = health_response.status_code == 200

            # Тест JSON-RPC с токеном
            jsonrpc_response = requests.post(
                "https://localhost:8443/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "echo",
                    "params": {"message": "Hello HTTPS Token Roles"},
                    "id": 1,
                },
                headers={"X-API-Key": token},
                verify=False,
                timeout=10,
            )
            jsonrpc_ok = jsonrpc_response.status_code == 200

            result = {
                "mode": "HTTPS + Token + Roles",
                "port": 8443,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "success": health_ok and jsonrpc_ok,
            }

            print(
                f"✅ HTTPS + Token + Roles: Health={health_ok}, JSON-RPC={jsonrpc_ok}"
            )
            return result

        except Exception as e:
            print(f"❌ HTTPS + Token + Roles failed: {e}")
            return {"mode": "HTTPS + Token + Roles", "success": False, "error": str(e)}

    def test_mtls_basic(self) -> Dict[str, Any]:
        """Тест mTLS Basic (порт 8443)"""
        print("\n🔍 Тестирование mTLS Basic (порт 8443)")

        try:
            config_path = self._config_path("mtls_no_roles_correct.json")
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/full_application/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            # Ждем запуска сервера с проверкой готовности
            max_wait = 20
            wait_interval = 1
            for _ in range(max_wait):
                try:
                    response = requests.get(
                        "https://localhost:8443/health",
                        verify=False,
                        cert=(
                            "mtls_certificates/client/test-client.crt",
                            "mtls_certificates/client/test-client.key",
                        ),
                        timeout=2
                    )
                    if response.status_code == 200:
                        break
                except Exception:
                    pass
                time.sleep(wait_interval)
            else:
                # Если сервер не запустился, ждем еще немного
                time.sleep(5)

            # Тест health endpoint с mTLS
            health_response = requests.get(
                "https://localhost:8443/health",
                verify=False,
                cert=(
                    "mtls_certificates/client/test-client.crt",
                    "mtls_certificates/client/test-client.key",
                ),
                timeout=10,
            )
            health_ok = health_response.status_code == 200

            # Тест JSON-RPC с mTLS
            jsonrpc_response = requests.post(
                "https://localhost:8443/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "echo",
                    "params": {"message": "Hello mTLS Basic"},
                    "id": 1,
                },
                verify=False,
                cert=(
                    "mtls_certificates/client/test-client.crt",
                    "mtls_certificates/client/test-client.key",
                ),
                timeout=10,
            )
            jsonrpc_ok = jsonrpc_response.status_code == 200

            result = {
                "mode": "mTLS Basic",
                "port": 8443,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "success": health_ok and jsonrpc_ok,
            }

            print(f"✅ mTLS Basic: Health={health_ok}, JSON-RPC={jsonrpc_ok}")
            return result

        except Exception as e:
            print(f"❌ mTLS Basic failed: {e}")
            return {"mode": "mTLS Basic", "success": False, "error": str(e)}

    def test_mtls_roles(self) -> Dict[str, Any]:
        """Тест mTLS + Roles (порт 8443)"""
        print("\n🔍 Тестирование mTLS + Roles (порт 8443)")

        try:
            config_path = self._config_path("mtls_with_roles_correct.json")
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/full_application/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            # Ждем запуска сервера с проверкой готовности
            max_wait = 20
            wait_interval = 1
            for _ in range(max_wait):
                try:
                    response = requests.get(
                        "https://localhost:8443/health",
                        verify=False,
                        cert=(
                            "mtls_certificates/client/test-client.crt",
                            "mtls_certificates/client/test-client.key",
                        ),
                        timeout=2
                    )
                    if response.status_code == 200:
                        break
                except Exception:
                    pass
                time.sleep(wait_interval)
            else:
                # Если сервер не запустился, ждем еще немного
                time.sleep(5)

            # Тест health endpoint с mTLS
            health_response = requests.get(
                "https://localhost:8443/health",
                verify=False,
                cert=(
                    "mtls_certificates/client/test-client.crt",
                    "mtls_certificates/client/test-client.key",
                ),
                timeout=10,
            )
            health_ok = health_response.status_code == 200

            # Тест JSON-RPC с mTLS
            jsonrpc_response = requests.post(
                "https://localhost:8443/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "echo",
                    "params": {"message": "Hello mTLS Roles"},
                    "id": 1,
                },
                verify=False,
                cert=(
                    "mtls_certificates/client/test-client.crt",
                    "mtls_certificates/client/test-client.key",
                ),
                timeout=10,
            )
            jsonrpc_ok = jsonrpc_response.status_code == 200

            result = {
                "mode": "mTLS + Roles",
                "port": 8443,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "success": health_ok and jsonrpc_ok,
            }

            print(f"✅ mTLS + Roles: Health={health_ok}, JSON-RPC={jsonrpc_ok}")
            return result

        except Exception as e:
            print(f"❌ mTLS + Roles failed: {e}")
            return {"mode": "mTLS + Roles", "success": False, "error": str(e)}

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 Запуск полного тестирования MCP Proxy Adapter")
        print("=" * 60)

        # Список тестов
        tests = [
            self.test_http_basic,
            self.test_http_token,
            self.test_http_token_roles,
            self.test_https_basic,
            self.test_https_token,
            self.test_https_token_roles,
            self.test_mtls_basic,
            self.test_mtls_roles,
        ]

        # Запуск тестов
        for test in tests:
            try:
                result = test()
                self.results.append(result)
                self.cleanup()  # Очистка после каждого теста
                time.sleep(3)  # Увеличиваем паузу между тестами
            except Exception as e:
                print(f"❌ Тест {test.__name__} failed: {e}")
                self.results.append(
                    {"mode": test.__name__, "success": False, "error": str(e)}
                )
                self.cleanup()

        # Итоговый отчет
        self.print_summary()

    def print_summary(self):
        """Печать итогового отчета"""
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 60)

        passed = 0
        failed = 0

        for result in self.results:
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            mode = result.get("mode", "Unknown")
            print(f"{status}: {mode}")

            if result.get("success", False):
                passed += 1
            else:
                failed += 1
                if "error" in result:
                    print(f"    Error: {result['error']}")

        print(f"\n🎯 РЕЗУЛЬТАТ: {passed}/{len(self.results)} тестов прошли успешно")

        if passed == len(self.results):
            print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! MCP Proxy Adapter работает корректно!")
        else:
            print(f"⚠️  {failed} тестов не прошли. Требуется доработка.")

        # Сохранение результатов
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n📄 Результаты сохранены в test_results.json")

    def _config_path(self, filename: str) -> str:
        """
        Получить абсолютный путь до конфигурационного файла.
        """
        config_path = CONFIG_DIR / filename
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        return str(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Загрузить и кешировать конфигурацию, чтобы не читать файл несколько раз.
        """
        if config_path not in self._config_cache:
            with Path(config_path).open("r", encoding="utf-8") as config_file:
                self._config_cache[config_path] = json.load(config_file)
        return self._config_cache[config_path]

    def _get_api_token(self, config_path: str) -> str:
        """
        Извлечь первый токен API из указанного конфига.
        """
        config = self._load_config(config_path)
        tokens = config.get("auth", {}).get("tokens") or {}
        if not tokens:
            raise ValueError(f"No API tokens configured in {config_path}")
        token = next(iter(tokens.keys()))
        return token


def main():
    """Основная функция"""
    tester = MCPProxyTester()
    try:
        tester.run_all_tests()
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
