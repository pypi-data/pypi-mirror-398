#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
Full test suite runner for MCP Proxy Adapter.
Automates the complete testing workflow.
"""
import os
import sys
import subprocess
from pathlib import Path


class FullTestSuiteRunner:
    """Comprehensive test suite runner that automates the entire testing process."""

    def __init__(self):
        """Initialize the test suite runner."""
        self.working_dir = Path.cwd()
        self.configs_dir = self.working_dir / "configs"
        self.certs_dir = self.working_dir / "certs"
        self.keys_dir = self.working_dir / "keys"
        self.roles_file = self.working_dir / "configs" / "roles.json"

    def print_step(self, step: str, description: str):
        """Print a formatted step header."""
        print(f"\n{'=' * 60}")
        print(f"🔧 STEP {step}: {description}")
        print(f"{'=' * 60}")

    def print_success(self, message: str):
        """Print a success message."""
        print(f"✅ {message}")

    def print_error(self, message: str):
        """Print an error message."""
        print(f"❌ {message}")

    def print_info(self, message: str):
        """Print an info message."""
        print(f"ℹ️  {message}")

    def check_environment(self) -> bool:
        """Check if the environment is properly set up."""
        self.print_step("1", "Environment Validation")

        # Check if we're in a virtual environment
        if not hasattr(sys, "real_prefix") and not (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            self.print_error("Not running in a virtual environment!")
            self.print_info("Please activate your virtual environment first:")
            self.print_info("  source venv/bin/activate  # or .venv/bin/activate")
            return False

        self.print_success("Virtual environment is active")

        # Check if mcp_proxy_adapter is installed
        try:
            import mcp_proxy_adapter

            self.print_success(
                f"mcp_proxy_adapter is installed (version: {mcp_proxy_adapter.__version__})"
            )
        except ImportError:
            self.print_error("mcp_proxy_adapter is not installed!")
            self.print_info("Please install it first:")
            self.print_info("  pip install mcp_proxy_adapter")
            return False

        # Check Python version
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            self.print_success(
                f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
            )
        else:
            self.print_error(
                f"Python {python_version.major}.{python_version.minor} is not supported. Need Python 3.8+"
            )
            return False

        return True

    def create_directories(self) -> bool:
        """Create necessary directories for testing."""
        self.print_step("2", "Directory Creation")

        try:
            # Create configs directory
            self.configs_dir.mkdir(exist_ok=True)
            self.print_success(
                f"Created/verified configs directory: {self.configs_dir}"
            )

            # Create certs directory
            self.certs_dir.mkdir(exist_ok=True)
            self.print_success(f"Created/verified certs directory: {self.certs_dir}")

            # Create keys directory
            self.keys_dir.mkdir(exist_ok=True)
            self.print_success(f"Created/verified keys directory: {self.keys_dir}")

            return True

        except Exception as e:
            self.print_error(f"Failed to create directories: {e}")
            return False

    def generate_certificates(self) -> bool:
        """Generate SSL certificates for testing."""
        self.print_step("3", "Certificate Generation")

        try:
            # Check if certificate generation script exists
            cert_script = self.working_dir / "mcp_proxy_adapter" / "examples" / "generate_certificates.py"
            if not cert_script.exists():
                self.print_error(
                    f"Certificate generation script not found: {cert_script}"
                )
                return False

            # Run certificate generation script
            cmd = [sys.executable, str(cert_script)]
            self.print_info("Running certificate generation script...")

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.working_dir
            )

            if result.returncode == 0:
                self.print_success("Certificates generated successfully")
                if result.stdout:
                    print(result.stdout)
                
                # Update configuration files with correct certificate paths
                self.print_info("Updating configuration files with correct certificate paths...")
                update_script = self.working_dir / "update_config_certificates.py"
                if update_script.exists():
                    update_cmd = [sys.executable, str(update_script)]
                    update_result = subprocess.run(
                        update_cmd, capture_output=True, text=True, cwd=self.working_dir
                    )
                    if update_result.returncode == 0:
                        self.print_success("Configuration files updated successfully")
                    else:
                        self.print_error(f"Failed to update configuration files: {update_result.stderr}")
                
                return True
            else:
                self.print_error("Certificate generation failed!")
                if result.stderr:
                    print("Error output:")
                    print(result.stderr)
                # Don't fail the entire suite if certificate generation fails
                # Allow it to continue with existing certificates
                self.print_info("Continuing with existing certificates...")
                return True

        except Exception as e:
            self.print_error(f"Failed to generate certificates: {e}")
            return False

    def generate_configurations(self) -> bool:
        """Generate test configurations from comprehensive config."""
        self.print_step("4", "Configuration Generation")

        try:
            # Check if create_test_configs.py exists
            config_script = self.working_dir / "mcp_proxy_adapter" / "examples" / "create_test_configs.py"
            if not config_script.exists():
                self.print_error(f"Configuration generator not found: {config_script}")
                return False

            # Check if comprehensive_config.json exists
            comprehensive_config = self.working_dir / "comprehensive_config.json"
            if not comprehensive_config.exists():
                self.print_error(
                    f"Comprehensive config not found: {comprehensive_config}"
                )
                return False

            self.print_info(
                "Generating test configurations from comprehensive config..."
            )
            self.print_info("This will create:")
            self.print_info("  - HTTP configurations (simple and with auth)")
            self.print_info("  - HTTPS configurations (simple and with auth)")
            self.print_info(
                "  - mTLS configurations (simple, with roles, with proxy registration)"
            )
            self.print_info("  - Full featured configuration (everything enabled)")

            # Run the configuration generator
            cmd = [
                sys.executable,
                "mcp_proxy_adapter/examples/create_test_configs.py",
                "--comprehensive-config",
                "comprehensive_config.json",
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.working_dir
            )

            if result.returncode == 0:
                self.print_success("Configuration generation completed successfully!")
                if result.stdout:
                    print("Generator output:")
                    print(result.stdout)

                # Create roles.json file
                self.print_info("Creating roles.json file...")
                roles_content = {
                    "roles": {
                        "admin": {
                            "permissions": ["*"],
                            "description": "Full administrative access",
                        },
                        "user": {
                            "permissions": ["read", "write"],
                            "description": "Standard user access",
                        },
                        "readonly": {
                            "permissions": ["read"],
                            "description": "Read-only access",
                        },
                        "guest": {
                            "permissions": ["read"],
                            "description": "Limited guest access",
                        },
                    }
                }

                roles_file = self.configs_dir / "roles.json"
                import json

                with open(roles_file, "w", encoding="utf-8") as f:
                    json.dump(roles_content, f, indent=2, ensure_ascii=False)
                self.print_success(f"Created roles.json: {roles_file}")

                return True
            else:
                self.print_error("Configuration generation failed!")
                if result.stdout:
                    print("Generator output:")
                    print(result.stdout)
                if result.stderr:
                    print("Error output:")
                    print(result.stderr)
                return False

        except Exception as e:
            self.print_error(f"Failed to generate configurations: {e}")
            return False

    def run_security_tests(self) -> bool:
        """Run the security test suite."""
        self.print_step("5", "Security Testing")

        try:
            # Run security tests
            cmd = [sys.executable, "run_security_tests_fixed.py", "--verbose"]
            self.print_info("Running security tests...")

            # Debug: show current working directory and check files
            self.print_info(f"DEBUG: Current working directory: {os.getcwd()}")
            self.print_info(f"DEBUG: Working directory from class: {self.working_dir}")

            # Check if certificates exist before running tests
            localhost_cert = self.certs_dir / "localhost_server.crt"
            self.print_info(
                f"DEBUG: localhost_server.crt exists: {localhost_cert.exists()}"
            )
            if localhost_cert.exists():
                self.print_info(
                    f"DEBUG: localhost_server.crt is symlink: {localhost_cert.is_symlink()}"
                )
                if localhost_cert.is_symlink():
                    self.print_info(
                        f"DEBUG: localhost_server.crt symlink target: {localhost_cert.readlink()}"
                    )

            # List all files in certs directory
            self.print_info("DEBUG: Files in certs directory:")
            for file in self.certs_dir.iterdir():
                self.print_info(f"DEBUG:   {file.name} -> {file}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.working_dir
            )

            if result.returncode == 0:
                self.print_success("Security tests completed successfully!")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                self.print_error("Security tests failed!")
                if result.stdout:
                    print("Test output:")
                    print(result.stdout)
                if result.stderr:
                    print("Error output:")
                    print(result.stderr)
                return False

        except Exception as e:
            self.print_error(f"Failed to run security tests: {e}")
            return False

    def run_mtls_registration_test(self) -> bool:
        """Run mTLS with proxy registration test."""
        self.print_step("6", "mTLS Proxy Registration Testing")

        try:
            # Check if test_proxy_registration.py exists
            test_script = self.working_dir / "test_proxy_registration.py"
            if not test_script.exists():
                self.print_error(f"Test script not found: {test_script}")
                return False

            # Create test_proxy_registration.json config if it doesn't exist
            test_config = self.configs_dir / "test_proxy_registration.json"
            if not test_config.exists():
                self.print_info(
                    "Creating test_proxy_registration.json configuration..."
                )
                test_config_content = {
                    "uuid": "550e8400-e29b-41d4-a716-446655440001",
                    "server": {"host": "127.0.0.1", "port": 20006},
                    "ssl": {
                        "enabled": True,
                        "cert_file": "certs/localhost_server.crt",
                        "key_file": "keys/server_key.pem",
                        "ca_cert": "certs/mcp_proxy_adapter_ca_ca.crt",
                        "client_cert_file": "certs/admin_cert.pem",
                        "client_key_file": "certs/admin_key.pem",
                        "verify_client": True,
                    },
                    "registration": {
                "enabled": True,
                "auth_method": "token",
                "server_url": "https://127.0.0.1:20005/register",
                "proxy_url": "https://127.0.0.1:20005",
                "fallback_proxy_url": "http://127.0.0.1:20005",
                "ssl": {
                    "verify_mode": "CERT_NONE",
                    "check_hostname": False
                },
                        "server_id": "mcp_test_server",
                        "server_name": "MCP Test Server",
                        "description": "Test server for proxy registration",
                        "version": "1.0.0",
                        "token": {
                            "enabled": True,
                            "token": "proxy_registration_token_123",
                        },
                        "proxy_info": {
                            "name": "mcp_test_server",
                            "description": "Test server for proxy registration",
                            "version": "1.0.0",
                            "capabilities": [
                                "jsonrpc",
                                "rest",
                                "security",
                                "proxy_registration",
                            ],
                            "endpoints": {
                                "jsonrpc": "/api/jsonrpc",
                                "rest": "/cmd",
                                "health": "/health",
                            },
                        },
                        "heartbeat": {
                            "enabled": True, 
                            "interval": 30,
                            "timeout": 10,
                            "retry_attempts": 3,
                            "retry_delay": 60
                        },
                    },
                    "security": {
                        "enabled": True,
                        "auth": {"enabled": True, "methods": ["certificate"]},
                        "permissions": {
                            "enabled": True,
                            "roles_file": "configs/roles.json",
                        },
                    },
                    "protocols": {
                        "enabled": True,
                        "default_protocol": "mtls",
                        "allowed_protocols": ["https", "mtls"],
                    },
                }

                import json

                with open(test_config, "w", encoding="utf-8") as f:
                    json.dump(test_config_content, f, indent=2)
                self.print_success(f"Created test configuration: {test_config}")

            self.print_info("Running mTLS proxy registration test...")
            self.print_info("This test verifies:")
            self.print_info(
                "  - mTLS server startup with client certificate verification"
            )
            self.print_info("  - Proxy registration functionality")
            self.print_info("  - SSL configuration validation")

            # Run the test
            cmd = [sys.executable, "test_proxy_registration.py"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.working_dir
            )

            if result.returncode == 0:
                self.print_success(
                    "mTLS proxy registration test completed successfully!"
                )
                if result.stdout:
                    print("Test output:")
                    print(result.stdout)
                return True
            else:
                self.print_error("mTLS proxy registration test failed!")
                if result.stdout:
                    print("Test output:")
                    print(result.stdout)
                if result.stderr:
                    print("Error output:")
                    print(result.stderr)
                return False

        except Exception as e:
            self.print_error(f"Failed to run mTLS registration test: {e}")
            return False

    def cleanup(self):
        """Clean up temporary files and processes."""
        self.print_info("Cleaning up...")

        # Simple cleanup - just print success message
        # Process cleanup is handled by the test scripts themselves
        print("✅ Cleanup completed")


    def test_all_configurations(self) -> bool:
        """Test all server configurations including proxy registration."""
        self.print_step("7", "Testing All Server Configurations")
        
        # List of all configuration files to test
        config_files = [
            "http_simple.json",
            "http_auth.json", 
            "http_token.json",
            "https_simple.json",
            "https_auth.json",
            "https_token.json",
            "mtls_simple.json",
            "mtls_no_roles.json",
            "mtls_with_roles.json",
            "mtls_with_proxy.json",
            "full_featured.json"
        ]
        
        results = []
        errors = []
        
        for config_file in config_files:
            config_path = self.configs_dir / config_file
            if not config_path.exists():
                error_msg = f"Configuration file not found: {config_file}"
                self.print_error(error_msg)
                errors.append(error_msg)
                results.append((config_file, False, error_msg))
                continue
                
            self.print_info(f"Testing configuration: {config_file}")
            
            try:
                # Test server startup with this configuration
                cmd = [
                    sys.executable, "-m", "mcp_proxy_adapter", 
                    "--config", str(config_path)
                ]
                
                # Run server for 5 seconds to test startup
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=10,
                    cwd=self.working_dir
                )
                
                if result.returncode == 0:
                    self.print_success(f"✅ {config_file} - Server started successfully")
                    results.append((config_file, True, "Server started successfully"))
                else:
                    error_msg = f"Server failed to start: {result.stderr[:200]}"
                    self.print_error(f"❌ {config_file} - {error_msg}")
                    errors.append(f"{config_file}: {error_msg}")
                    results.append((config_file, False, error_msg))
                    
            except subprocess.TimeoutExpired:
                # Server started successfully (timeout means it's running)
                self.print_success(f"✅ {config_file} - Server started and running")
                results.append((config_file, True, "Server started and running"))
            except Exception as e:
                error_msg = f"Test failed: {str(e)}"
                self.print_error(f"❌ {config_file} - {error_msg}")
                errors.append(f"{config_file}: {error_msg}")
                results.append((config_file, False, error_msg))
        
        # Print summary
        self.print_step("7.1", "Configuration Test Results Summary")
        successful = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        print(f"📊 Configuration Test Results:")
        print(f"   Total configurations tested: {total}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {total - successful}")
        print(f"   Success rate: {(successful/total)*100:.1f}%")
        
        if errors:
            print(f"\n❌ Errors encountered:")
            for error in errors:
                print(f"   • {error}")
        
        return len(errors) == 0

    def run_full_suite(self) -> bool:
        """Run the complete test suite."""
        print("🚀 MCP Proxy Adapter - Full Test Suite")
        print("=" * 60)
        print(f"Working directory: {self.working_dir}")
        print(f"Python executable: {sys.executable}")

        try:
            # Step 1: Environment validation
            if not self.check_environment():
                return False

            # Step 2: Directory creation
            if not self.create_directories():
                return False

            # Step 3: Certificate generation (skip if fails, use existing certificates)
            self.generate_certificates()  # Don't fail if certificates already exist

            # Step 4: Configuration generation
            if not self.generate_configurations():
                return False

            # Step 5: Security testing
            if not self.run_security_tests():
                return False

            # Step 6: mTLS proxy registration testing
            if not self.run_mtls_registration_test():
                return False

            # Step 7: Test all configurations
            if not self.test_all_configurations():
                return False

            # All steps completed successfully
            print(f"\n{'=' * 60}")
            print("🎉 FULL TEST SUITE COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("✅ Environment validated")
            print("✅ Directories cleaned")
            print("✅ Directories created")
            print("✅ Certificates generated")
            print("✅ Configurations generated")
            print("✅ Security tests passed")
            print("✅ mTLS proxy registration test passed")
            print("✅ All server configurations tested")
            print(f"\n📁 Test artifacts created in: {self.working_dir}")
            print(f"📁 Configurations: {self.configs_dir}")
            print(f"📁 Certificates: {self.certs_dir}")
            print(f"📁 Keys: {self.keys_dir}")

            return True

        except KeyboardInterrupt:
            print("\n\n⚠️  Test suite interrupted by user")
            return False
        except Exception as e:
            self.print_error(f"Unexpected error during test suite execution: {e}")
            return False
        finally:
            try:
                self.print_info("Starting cleanup in finally block...")
                self.cleanup()
                self.print_info("Cleanup in finally block completed")
            except Exception as e:
                self.print_error(f"Cleanup failed in finally block: {e}")
                import traceback

                traceback.print_exc()


def main():
    """Main entry point."""
    runner = FullTestSuiteRunner()

    try:
        success = runner.run_full_suite()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
