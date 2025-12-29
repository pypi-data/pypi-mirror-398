#!/usr/bin/env python3
"""
Security Testing Script - Fixed Version
This script runs comprehensive security tests without fallback mode
and with proper port management.
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from security_test_client import SecurityTestClient, TestResult


class SecurityTestRunner:
    """Security test runner with proper port management."""

    def __init__(self):
        """
        Initialize security test runner.
        """
        self.project_root = Path(__file__).parent.parent.parent
        self.configs_dir = self.project_root / "configs"
        self.server_processes = {}
        self.test_results = []

    def kill_process_on_port(self, port: int) -> bool:
        """Kill process using specific port."""
        try:
            # Find process using the port
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip()
                # Kill the process
                subprocess.run(["kill", "-9", pid], check=True)
                print(f"✅ Killed process {pid} on port {port}")
                time.sleep(1)  # Wait for port to be released
                return True
            else:
                print(f"ℹ️ No process found on port {port}")
                return True
        except subprocess.TimeoutExpired:
            print(f"⚠️ Timeout checking port {port}")
            return False
        except Exception as e:
            print(f"❌ Error killing process on port {port}: {e}")
            return False

    def start_server(
        self, config_name: str, config_path: Path
    ) -> Optional[subprocess.Popen]:
        """Start server with proper error handling."""
        try:
            # Get port from config
            with open(config_path) as f:
                config = json.load(f)
            port = config.get("server", {}).get("port", 8000)
            # Kill any existing process on this port
            self.kill_process_on_port(port)
            # Start server
            cmd = [
                sys.executable,
                "-m",
                "mcp_proxy_adapter.main",
                "--config",
                str(config_path.absolute()),  # Use absolute path to avoid path issues
            ]
            # Always start from examples directory where configs are located
            cwd = self.project_root / "mcp_proxy_adapter" / "examples"
            print(f"🚀 Starting {config_name} on port {port}...")
            process = subprocess.Popen(
                cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            # Wait a bit for server to start
            time.sleep(3)
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {config_name} started successfully on port {port}")
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {config_name} failed to start:")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return None
        except Exception as e:
            print(f"❌ Error starting {config_name}: {e}")
            return None

    def stop_server(self, config_name: str, process: subprocess.Popen):
        """Stop server gracefully."""
        try:
            print(f"🛑 Stopping {config_name}...")
            process.terminate()
            process.wait(timeout=5)
            print(f"✅ {config_name} stopped")
        except subprocess.TimeoutExpired:
            print(f"⚠️ Force killing {config_name}...")
            process.kill()
            process.wait()
        except Exception as e:
            print(f"❌ Error stopping {config_name}: {e}")

    async def test_server(
        self, config_name: str, config_path: Path
    ) -> List[TestResult]:
        """Test a single server configuration."""
        results = []
        
        # Get config for port number first
        with open(config_path) as f:
            config = json.load(f)
        port = config.get("server", {}).get("port", 8000)
        
        # Start server
        process = self.start_server(config_name, config_path)
        if not process:
            return [
                TestResult(
                    test_name=f"{config_name}_startup",
                    server_url=f"http://localhost:{port}",
                    auth_type="none",
                    success=False,
                    error_message="Server failed to start",
                )
            ]
        try:
            # Get remaining config for client setup
            auth_enabled = config.get("security", {}).get("enabled", False)
            # For new simplified structure, if security is enabled, we use token auth
            auth_methods = ["api_key"] if auth_enabled else []
            # Create test client with correct protocol
            server_protocol = config.get("server", {}).get("protocol", "http")
            protocol = "https" if server_protocol in ["https", "mtls"] else "http"
            client = SecurityTestClient(base_url=f"{protocol}://localhost:{port}")
            print(f"🔍 DEBUG: Created client with URL: {client.base_url}")
            client.auth_enabled = auth_enabled
            client.auth_methods = auth_methods
            client.api_keys = config.get("security", {}).get("tokens", {})
            client.roles_file = config.get("security", {}).get("roles_file")
            client.roles = config.get("security", {}).get("roles", {})
            # For mTLS, override SSL context creation and change working directory
            if server_protocol == "mtls":
                client.create_ssl_context = client.create_ssl_context_for_mtls
                # Ensure mTLS uses certificate auth
                client.auth_methods = ["certificate"]
                # Change to examples directory for mTLS tests
                import os

                os.chdir(self.project_root / "mcp_proxy_adapter" / "examples")
            # Run tests
            async with client:
                # Test 1: Health check
                result = await client.test_health()
                results.append(result)
                # Test 2: Command execution
                result = await client.test_command_execution()
                results.append(result)
                # Test 3: Authentication (if enabled)
                if auth_enabled:
                    result = await client.test_authentication()
                    results.append(result)
                    # Test 4: Negative authentication
                    result = await client.test_negative_authentication()
                    results.append(result)
                    # Test 5: Role-based access
                    if "api_key" in auth_methods:
                        result = await client.test_role_based_access(
                            client.base_url, "api_key", role="admin"
                        )
                    else:
                        result = await client.test_role_based_access(
                            client.base_url, "certificate", role="admin"
                        )
                    results.append(result)
                    # Test 6: Role permissions
                    if "api_key" in auth_methods:
                        result = await client.test_role_permissions(
                            client.base_url, "api_key", role="admin", action="read"
                        )
                    else:
                        result = await client.test_role_permissions(
                            client.base_url, "certificate", role="admin", action="read"
                        )
                    results.append(result)
                    # Test 7: Multiple roles test
                    if "api_key" in auth_methods:
                        result = await client.test_multiple_roles(
                            client.base_url, "api_key"
                        )
                    else:
                        result = await client.test_multiple_roles(
                            client.base_url, "certificate"
                        )
                    results.append(result)
                else:
                    # Test 3: No authentication required
                    result = await client.test_no_auth_required()
                    results.append(result)
                    # Test 4: Negative auth (should fail)
                    result = await client.test_negative_authentication()
                    results.append(result)
        except Exception as e:
                results.append(
                TestResult(
                    test_name=f"{config_name}_client_error",
                    server_url=f"{protocol}://localhost:{port}",
                    auth_type="none",
                    success=False,
                    error_message=str(e),
                )
            )
        finally:
            # Stop server
            self.stop_server(config_name, process)
        return results

    def create_variant_from_full_config(self, full_config_path: Path, protocol: str, auth: str, port: int) -> Path:
        """
        Create a variant configuration from full config.
        
        Args:
            full_config_path: Path to the full configuration file
            protocol: Protocol type (http, https, mtls)
            auth: Authentication type (none, token, token_roles)
            port: Server port
            
        Returns:
            Path to the temporary configuration file
        """
        import tempfile
        import json
        
        # Load the full configuration
        with open(full_config_path, 'r') as f:
            full_config = json.load(f)
        
        # Create a copy of the full config
        variant_config = full_config.copy()
        
        # Set server port and protocol
        variant_config["server"]["port"] = port
        variant_config["server"]["protocol"] = protocol
        
        # Apply protocol configuration
        if protocol in variant_config.get("protocol_variants", {}):
            protocol_config = variant_config["protocol_variants"][protocol]
            variant_config["server"].update(protocol_config["server"])
        
        # Apply authentication configuration
        if auth in variant_config.get("auth_variants", {}):
            auth_config = variant_config["auth_variants"][auth]
            variant_config["security"].update(auth_config["security"])
        
        # Remove the helper sections
        variant_config.pop("protocol_variants", None)
        variant_config.pop("auth_variants", None)
        
        # Create temporary config file
        temp_dir = tempfile.mkdtemp(prefix="full_config_test_")
        config_name = f"{protocol}_{auth}.json"
        config_path = Path(temp_dir) / config_name
        
        with open(config_path, 'w') as f:
            json.dump(variant_config, f, indent=2, ensure_ascii=False)
        
        return config_path

    async def run_all_tests(self):
        """Run all security tests."""
        print("🔒 Starting Security Testing Suite")
        print("=" * 50)
        # Test configurations
        configs = [
            ("basic_http", "http.json"),
            ("http_token", "http_token_roles.json"),
            ("https", "https.json"),
            ("https_token", "https_token_roles.json"),
            ("mtls", "mtls.json"),
        ]
        total_tests = 0
        passed_tests = 0
        for config_name, config_file in configs:
            config_path = self.configs_dir / config_file
            if not config_path.exists():
                print(f"❌ Configuration not found: {config_path}")
                continue
            print(f"\n📋 Testing {config_name.upper()} configuration")
            print("-" * 30)
            results = await self.test_server(config_name, config_path)
            for result in results:
                total_tests += 1
                if result.success:
                    passed_tests += 1
                    print(f"✅ {result.test_name}: PASS")
                else:
                    print(f"❌ {result.test_name}: FAIL - {result.error_message}")
            self.test_results.extend(results)
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(
            f"Success rate: {(passed_tests/total_tests*100):.1f}%"
            if total_tests > 0
            else "N/A"
        )
        # Detailed results
        print("\n📋 DETAILED RESULTS")
        print("-" * 30)
        for result in self.test_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} {result.test_name}")
            if not result.success and result.error_message:
                print(f"   Error: {result.error_message}")
        return passed_tests == total_tests

    async def run_full_config_tests(self, full_config_path: str):
        """Run tests using full configuration with all variants."""
        print("🚀 Full Configuration Variants Testing")
        print("=" * 60)
        print(f"📁 Using full config: {full_config_path}")
        
        full_config_file = Path(full_config_path)
        if not full_config_file.exists():
            print(f"❌ Full configuration file not found: {full_config_path}")
            return False
        
        # Define all combinations to test
        variants = [
            # HTTP variants
            ("http", "none", 20000),
            ("http", "token", 20001),
            ("http", "token_roles", 20002),
            
            # HTTPS variants
            ("https", "none", 20003),
            ("https", "token", 20004),
            ("https", "token_roles", 20005),
            
            # mTLS variants
            ("mtls", "none", 20006),
            ("mtls", "token", 20007),
            ("mtls", "token_roles", 20008),
        ]
        
        total_tests = 0
        passed_tests = 0
        all_results = []
        
        for protocol, auth, port in variants:
            print(f"\n{'='*60}")
            print(f"🧪 Testing {protocol.upper()} with {auth.upper()} authentication")
            print(f"{'='*60}")
            
            # Create variant configuration
            config_path = self.create_variant_from_full_config(full_config_file, protocol, auth, port)
            
            # Test the variant
            config_name = f"{protocol}_{auth}"
            results = await self.test_server(config_name, config_path)
            
            # Count results
            for result in results:
                total_tests += 1
                if result.success:
                    passed_tests += 1
                    print(f"✅ {result.test_name}: PASS")
                else:
                    print(f"❌ {result.test_name}: FAIL - {result.error_message}")
            
            all_results.extend(results)
            
            # Clean up temporary config
            import shutil
            shutil.rmtree(config_path.parent)
        
        # Print final summary
        print(f"\n{'='*60}")
        print("📊 FULL CONFIG TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if total_tests - passed_tests > 0:
            print(f"\n❌ Failed tests:")
            for result in all_results:
                if not result.success:
                    print(f"   • {result.test_name}: {result.error_message}")
        
        return passed_tests == total_tests



async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Testing Suite for MCP Proxy Adapter")
    parser.add_argument("--full-config", help="Path to full configuration file for variant testing")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    runner = SecurityTestRunner()
    try:
        if args.full_config:
            # Test full configuration variants
            success = await runner.run_full_config_tests(args.full_config)
        else:
            # Run standard tests
            success = await runner.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
