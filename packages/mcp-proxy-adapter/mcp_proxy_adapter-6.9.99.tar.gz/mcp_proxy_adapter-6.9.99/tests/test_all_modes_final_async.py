#!/usr/bin/env python3
"""
Полный тест всех режимов MCP Proxy Adapter с использованием клиента проекта
"""
import json
import subprocess
import time
import asyncio
from pathlib import Path
from typing import Any, Dict, List

from mcp_proxy_adapter.client.jsonrpc_client.client import JsonRpcClient

CONFIG_DIR = Path("mcp_proxy_adapter/examples/full_application/configs")


class MCPProxyTesterAsync:
    """Тестер всех режимов MCP Proxy Adapter с использованием клиента проекта"""

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

    async def wait_for_server(self, protocol: str, port: int, use_mtls: bool = False) -> bool:
        """Ожидание запуска сервера с проверкой готовности"""
        max_wait = 30
        wait_interval = 1
        
        for _ in range(max_wait):
            try:
                if use_mtls:
                    client = JsonRpcClient(
                        protocol=protocol,
                        host="127.0.0.1",
                        port=port,
                        check_hostname=False,
                        cert="mtls_certificates/client/test-client.crt",
                        key="mtls_certificates/client/test-client.key",
                        ca="mtls_certificates/ca/ca.crt",
                    )
                else:
                    client = JsonRpcClient(
                        protocol=protocol,
                        host="127.0.0.1",
                        port=port,
                        check_hostname=False,
                    )
                await client.health()
                await client.close()
                return True
            except Exception:
                pass
            await asyncio.sleep(wait_interval)
        
        return False

    async def test_http_basic(self) -> Dict[str, Any]:
        """Тест HTTP Basic (порт 8080)"""
        print("\n🔍 Тестирование HTTP Basic (порт 8080)")

        try:
            config_path = self._config_path("http_basic.json")
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/test_server/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            
            # Ждем запуска сервера
            if not await self.wait_for_server("http", 8080):
                return {"mode": "HTTP Basic", "success": False, "error": "Server did not start"}

            # Создаем клиент
            client = JsonRpcClient(
                protocol="http",
                host="127.0.0.1",
                port=8080,
                check_hostname=False,
            )

            # Тест health endpoint
            try:
                health_result = await client.health()
                health_ok = health_result is not None
            except Exception as e:
                health_ok = False
                print(f"Health check failed: {e}")

            # Тест JSON-RPC
            try:
                echo_result = await client.echo("Hello HTTP Basic")
                jsonrpc_ok = echo_result is not None and echo_result.get("success", False)
            except Exception as e:
                jsonrpc_ok = False
                print(f"Echo failed: {e}")

            # Тест получения описаний команд
            try:
                methods = await client.get_methods()
                methods_ok = len(methods) > 0
                print(f"  📋 Found {len(methods)} methods")
            except Exception as e:
                methods_ok = False
                print(f"Get methods failed: {e}")

            # Тест получения описания конкретной команды
            try:
                echo_desc = await client.get_method_description("echo")
                desc_ok = len(echo_desc) > 0
                # Тест получения описаний для разных типов команд
                help_desc = await client.get_method_description("help")
                help_desc_ok = len(help_desc) > 0
                # Проверяем наличие разных команд в списке методов
                method_names = list(methods.keys())
                has_builtin = "echo" in method_names
                has_custom = "calculator" in method_names or "custom_echo" in method_names
                has_queue = any("queue" in name for name in method_names)
                desc_ok = desc_ok and help_desc_ok and has_builtin
                print(f"  📋 Commands: builtin={has_builtin}, custom={has_custom}, queue={has_queue}")
            except Exception as e:
                desc_ok = False
                print(f"Get method description failed: {e}")

            await client.close()

            result = {
                "mode": "HTTP Basic",
                "port": 8080,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "methods": methods_ok,
                "description": desc_ok,
                "success": health_ok and jsonrpc_ok and methods_ok and desc_ok,
            }

            print(f"✅ HTTP Basic: Health={health_ok}, JSON-RPC={jsonrpc_ok}, Methods={methods_ok}, Description={desc_ok}")
            return result

        except Exception as e:
            print(f"❌ HTTP Basic failed: {e}")
            return {"mode": "HTTP Basic", "success": False, "error": str(e)}

    async def test_http_token(self) -> Dict[str, Any]:
        """Тест HTTP + Token (порт 8080)"""
        print("\n🔍 Тестирование HTTP + Token (порт 8080)")

        try:
            config_path = self._config_path("http_token.json")
            token = self._get_api_token(config_path)
            
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/test_server/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            
            # Ждем запуска сервера
            if not await self.wait_for_server("http", 8080):
                return {"mode": "HTTP + Token", "success": False, "error": "Server did not start"}

            # Создаем клиент с токеном
            client = JsonRpcClient(
                protocol="http",
                host="127.0.0.1",
                port=8080,
                token_header="X-API-Key",
                token=token,
                check_hostname=False,
            )

            # Тест health endpoint
            try:
                health_result = await client.health()
                health_ok = health_result is not None
            except Exception as e:
                health_ok = False

            # Тест JSON-RPC с токеном
            try:
                echo_result = await client.echo("Hello HTTP Token")
                jsonrpc_ok = echo_result is not None and echo_result.get("success", False)
            except Exception as e:
                jsonrpc_ok = False

            # Тест получения описаний команд
            desc_ok = False
            try:
                methods = await client.get_methods()
                methods_ok = len(methods) > 0
                if methods_ok:
                    print(f"  📋 Found {len(methods)} methods: {', '.join(list(methods.keys())[:5])}...")
                # Тест получения описания команды
                try:
                    echo_desc = await client.get_method_description("echo")
                    desc_ok = len(echo_desc) > 0
                except Exception:
                    desc_ok = False
            except Exception as e:
                methods_ok = False
                desc_ok = False
                print(f"Get methods failed: {e}")

            await client.close()

            result = {
                "mode": "HTTP + Token",
                "port": 8080,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "methods": methods_ok,
                "description": desc_ok,
                "success": health_ok and jsonrpc_ok and methods_ok and desc_ok,
            }

            print(f"✅ HTTP + Token: Health={health_ok}, JSON-RPC={jsonrpc_ok}, Methods={methods_ok}")
            return result

        except Exception as e:
            print(f"❌ HTTP + Token failed: {e}")
            return {"mode": "HTTP + Token", "success": False, "error": str(e)}

    async def test_http_token_roles(self) -> Dict[str, Any]:
        """Тест HTTP + Token + Roles (порт 8080)"""
        print("\n🔍 Тестирование HTTP + Token + Roles (порт 8080)")

        try:
            config_path = self._config_path("http_token_roles.json")
            token = self._get_api_token(config_path)
            
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/test_server/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            
            # Ждем запуска сервера
            if not await self.wait_for_server("http", 8080):
                return {"mode": "HTTP + Token + Roles", "success": False, "error": "Server did not start"}

            # Создаем клиент с токеном
            client = JsonRpcClient(
                protocol="http",
                host="127.0.0.1",
                port=8080,
                token_header="X-API-Key",
                token=token,
                check_hostname=False,
            )

            # Тест health endpoint
            try:
                health_result = await client.health()
                health_ok = health_result is not None
            except Exception as e:
                health_ok = False

            # Тест JSON-RPC с токеном
            try:
                echo_result = await client.echo("Hello HTTP Token Roles")
                jsonrpc_ok = echo_result is not None and echo_result.get("success", False)
            except Exception as e:
                jsonrpc_ok = False

            # Тест получения описаний команд
            try:
                methods = await client.get_methods()
                methods_ok = len(methods) > 0
                if methods_ok:
                    print(f"  📋 Found {len(methods)} methods: {', '.join(list(methods.keys())[:5])}...")
            except Exception as e:
                methods_ok = False
                print(f"Get methods failed: {e}")

            await client.close()

            result = {
                "mode": "HTTP + Token + Roles",
                "port": 8080,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "methods": methods_ok,
                "success": health_ok and jsonrpc_ok and methods_ok,
            }

            print(f"✅ HTTP + Token + Roles: Health={health_ok}, JSON-RPC={jsonrpc_ok}, Methods={methods_ok}")
            return result

        except Exception as e:
            print(f"❌ HTTP + Token + Roles failed: {e}")
            return {"mode": "HTTP + Token + Roles", "success": False, "error": str(e)}

    async def test_https_basic(self) -> Dict[str, Any]:
        """Тест HTTPS Basic (порт 8443)"""
        print("\n🔍 Тестирование HTTPS Basic (порт 8443)")

        try:
            config_path = self._config_path("https_basic.json")
            
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/test_server/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            
            # Ждем запуска сервера
            if not await self.wait_for_server("https", 8443):
                return {"mode": "HTTPS Basic", "success": False, "error": "Server did not start"}

            # Создаем клиент
            client = JsonRpcClient(
                protocol="https",
                host="127.0.0.1",
                port=8443,
                check_hostname=False,
            )

            # Тест health endpoint
            try:
                health_result = await client.health()
                health_ok = health_result is not None
            except Exception as e:
                health_ok = False

            # Тест JSON-RPC
            try:
                echo_result = await client.echo("Hello HTTPS Basic")
                jsonrpc_ok = echo_result is not None and echo_result.get("success", False)
            except Exception as e:
                jsonrpc_ok = False

            # Тест получения описаний команд
            try:
                methods = await client.get_methods()
                methods_ok = len(methods) > 0
                if methods_ok:
                    print(f"  📋 Found {len(methods)} methods: {', '.join(list(methods.keys())[:5])}...")
            except Exception as e:
                methods_ok = False
                print(f"Get methods failed: {e}")

            await client.close()

            result = {
                "mode": "HTTPS Basic",
                "port": 8443,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "methods": methods_ok,
                "success": health_ok and jsonrpc_ok and methods_ok,
            }

            print(f"✅ HTTPS Basic: Health={health_ok}, JSON-RPC={jsonrpc_ok}, Methods={methods_ok}")
            return result

        except Exception as e:
            print(f"❌ HTTPS Basic failed: {e}")
            return {"mode": "HTTPS Basic", "success": False, "error": str(e)}

    async def test_https_token(self) -> Dict[str, Any]:
        """Тест HTTPS + Token (порт 8443)"""
        print("\n🔍 Тестирование HTTPS + Token (порт 8443)")

        try:
            config_path = self._config_path("https_token.json")
            token = self._get_api_token(config_path)
            
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/test_server/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            
            # Ждем запуска сервера
            if not await self.wait_for_server("https", 8443):
                return {"mode": "HTTPS + Token", "success": False, "error": "Server did not start"}

            # Создаем клиент с токеном
            client = JsonRpcClient(
                protocol="https",
                host="127.0.0.1",
                port=8443,
                token="X-API-Key",
                token_header=token,
                check_hostname=False,
            )

            # Тест health endpoint
            try:
                health_result = await client.health()
                health_ok = health_result is not None
            except Exception as e:
                health_ok = False

            # Тест JSON-RPC с токеном
            try:
                echo_result = await client.echo("Hello HTTPS Token")
                jsonrpc_ok = echo_result is not None and echo_result.get("success", False)
            except Exception as e:
                jsonrpc_ok = False

            # Тест получения описаний команд
            try:
                methods = await client.get_methods()
                methods_ok = len(methods) > 0
                if methods_ok:
                    print(f"  📋 Found {len(methods)} methods: {', '.join(list(methods.keys())[:5])}...")
            except Exception as e:
                methods_ok = False
                print(f"Get methods failed: {e}")

            await client.close()

            result = {
                "mode": "HTTPS + Token",
                "port": 8443,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "methods": methods_ok,
                "success": health_ok and jsonrpc_ok and methods_ok,
            }

            print(f"✅ HTTPS + Token: Health={health_ok}, JSON-RPC={jsonrpc_ok}, Methods={methods_ok}")
            return result

        except Exception as e:
            print(f"❌ HTTPS + Token failed: {e}")
            return {"mode": "HTTPS + Token", "success": False, "error": str(e)}

    async def test_https_token_roles(self) -> Dict[str, Any]:
        """Тест HTTPS + Token + Roles (порт 8443)"""
        print("\n🔍 Тестирование HTTPS + Token + Roles (порт 8443)")

        try:
            config_path = self._config_path("https_token_roles.json")
            token = self._get_api_token(config_path)
            
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/test_server/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            
            # Ждем запуска сервера
            if not await self.wait_for_server("https", 8443):
                return {"mode": "HTTPS + Token + Roles", "success": False, "error": "Server did not start"}

            # Создаем клиент с токеном
            client = JsonRpcClient(
                protocol="https",
                host="127.0.0.1",
                port=8443,
                token="X-API-Key",
                token_header=token,
                check_hostname=False,
            )

            # Тест health endpoint
            try:
                health_result = await client.health()
                health_ok = health_result is not None
            except Exception as e:
                health_ok = False

            # Тест JSON-RPC с токеном
            try:
                echo_result = await client.echo("Hello HTTPS Token Roles")
                jsonrpc_ok = echo_result is not None and echo_result.get("success", False)
            except Exception as e:
                jsonrpc_ok = False

            # Тест получения описаний команд
            try:
                methods = await client.get_methods()
                methods_ok = len(methods) > 0
                if methods_ok:
                    print(f"  📋 Found {len(methods)} methods: {', '.join(list(methods.keys())[:5])}...")
            except Exception as e:
                methods_ok = False
                print(f"Get methods failed: {e}")

            await client.close()

            result = {
                "mode": "HTTPS + Token + Roles",
                "port": 8443,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "methods": methods_ok,
                "success": health_ok and jsonrpc_ok and methods_ok,
            }

            print(f"✅ HTTPS + Token + Roles: Health={health_ok}, JSON-RPC={jsonrpc_ok}, Methods={methods_ok}")
            return result

        except Exception as e:
            print(f"❌ HTTPS + Token + Roles failed: {e}")
            return {"mode": "HTTPS + Token + Roles", "success": False, "error": str(e)}

    async def test_mtls_basic(self) -> Dict[str, Any]:
        """Тест mTLS Basic (порт 8443)"""
        print("\n🔍 Тестирование mTLS Basic (порт 8443)")

        try:
            config_path = self._config_path("mtls_no_roles_correct.json")
            
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/test_server/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            
            # Ждем запуска сервера
            if not await self.wait_for_server("mtls", 8443, use_mtls=True):
                return {"mode": "mTLS Basic", "success": False, "error": "Server did not start"}

            # Создаем клиент с mTLS
            client = JsonRpcClient(
                protocol="mtls",
                host="127.0.0.1",
                port=8443,
                cert="mtls_certificates/client/test-client.crt",
                key="mtls_certificates/client/test-client.key",
                ca="mtls_certificates/ca/ca.crt",
                check_hostname=False,
            )

            # Тест health endpoint
            try:
                health_result = await client.health()
                health_ok = health_result is not None
            except Exception as e:
                health_ok = False

            # Тест JSON-RPC с mTLS
            try:
                echo_result = await client.echo("Hello mTLS Basic")
                jsonrpc_ok = echo_result is not None and echo_result.get("success", False)
            except Exception as e:
                jsonrpc_ok = False

            # Тест получения описаний команд
            try:
                methods = await client.get_methods()
                methods_ok = len(methods) > 0
                if methods_ok:
                    print(f"  📋 Found {len(methods)} methods: {', '.join(list(methods.keys())[:5])}...")
            except Exception as e:
                methods_ok = False
                print(f"Get methods failed: {e}")

            await client.close()

            result = {
                "mode": "mTLS Basic",
                "port": 8443,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "methods": methods_ok,
                "success": health_ok and jsonrpc_ok and methods_ok,
            }

            print(f"✅ mTLS Basic: Health={health_ok}, JSON-RPC={jsonrpc_ok}, Methods={methods_ok}")
            return result

        except Exception as e:
            print(f"❌ mTLS Basic failed: {e}")
            return {"mode": "mTLS Basic", "success": False, "error": str(e)}

    async def test_mtls_roles(self) -> Dict[str, Any]:
        """Тест mTLS + Roles (порт 8443)"""
        print("\n🔍 Тестирование mTLS + Roles (порт 8443)")

        try:
            config_path = self._config_path("mtls_with_roles_correct.json")
            
            # Запуск сервера
            cmd = [
                "python",
                "mcp_proxy_adapter/examples/test_server/main.py",
                "--config",
                config_path,
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes.append(process)
            
            # Ждем запуска сервера
            if not await self.wait_for_server("mtls", 8443, use_mtls=True):
                return {"mode": "mTLS + Roles", "success": False, "error": "Server did not start"}

            # Создаем клиент с mTLS
            client = JsonRpcClient(
                protocol="mtls",
                host="127.0.0.1",
                port=8443,
                cert="mtls_certificates/client/test-client.crt",
                key="mtls_certificates/client/test-client.key",
                ca="mtls_certificates/ca/ca.crt",
                check_hostname=False,
            )

            # Тест health endpoint
            try:
                health_result = await client.health()
                health_ok = health_result is not None
            except Exception as e:
                health_ok = False

            # Тест JSON-RPC с mTLS
            try:
                echo_result = await client.echo("Hello mTLS Roles")
                jsonrpc_ok = echo_result is not None and echo_result.get("success", False)
            except Exception as e:
                jsonrpc_ok = False

            # Тест получения описаний команд
            try:
                methods = await client.get_methods()
                methods_ok = len(methods) > 0
                if methods_ok:
                    print(f"  📋 Found {len(methods)} methods: {', '.join(list(methods.keys())[:5])}...")
            except Exception as e:
                methods_ok = False
                print(f"Get methods failed: {e}")

            await client.close()

            result = {
                "mode": "mTLS + Roles",
                "port": 8443,
                "health": health_ok,
                "jsonrpc": jsonrpc_ok,
                "methods": methods_ok,
                "success": health_ok and jsonrpc_ok and methods_ok,
            }

            print(f"✅ mTLS + Roles: Health={health_ok}, JSON-RPC={jsonrpc_ok}, Methods={methods_ok}")
            return result

        except Exception as e:
            print(f"❌ mTLS + Roles failed: {e}")
            return {"mode": "mTLS + Roles", "success": False, "error": str(e)}

    async def run_all_tests(self):
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
                result = await test()
                self.results.append(result)
                self.cleanup()  # Очистка после каждого теста
                await asyncio.sleep(3)  # Пауза между тестами
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
        with open("test_results_async.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n📄 Результаты сохранены в test_results_async.json")

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


async def main():
    """Основная функция"""
    tester = MCPProxyTesterAsync()
    try:
        await tester.run_all_tests()
    finally:
        tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

