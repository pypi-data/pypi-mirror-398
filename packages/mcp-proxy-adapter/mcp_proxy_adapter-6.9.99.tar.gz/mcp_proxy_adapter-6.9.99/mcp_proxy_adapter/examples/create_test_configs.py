#!/usr/bin/env python3
"""
Test Configuration Generator
Creates test configurations using the advanced ConfigBuilder utility.
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import json
from pathlib import Path

from config_builder import ConfigBuilder, ConfigFactory, Protocol, AuthMethod


class TestConfigGenerator:
    """Generator for test configurations using ConfigBuilder."""

    def __init__(self, output_dir: str = "configs"):
        """
        Initialize the generator.
        
        Args:
            output_dir: Directory to output test configurations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def _save_config(self, name: str, config: Dict[str, Any]) -> Path:
        """Save configuration to file."""
        output_path = self.output_dir / f"{name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ Created test config: {output_path}")
        return output_path

    def create_all_test_configs(self):
        """Create all standard test configurations using ConfigFactory."""
        print("🔧 Creating test configurations using ConfigBuilder...")
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # 1. HTTP Simple
        config = ConfigFactory.create_http_simple(port=20020, log_dir=str(self.output_dir.parent / "logs"))
        self._save_config("http_simple", config)
        
        # 2. HTTP with Token Auth
        api_keys = {
                "admin": "admin-secret-key",
                "user": "user-secret-key"
        }
        config = ConfigFactory.create_http_token(port=20021, log_dir=str(self.output_dir.parent / "logs"), api_keys=api_keys)
        self._save_config("http_token", config)
        
        # 3. HTTPS Simple
        config = ConfigFactory.create_https_simple(
            port=20022, 
            log_dir=str(self.output_dir.parent / "logs"),
            cert_dir=str(self.output_dir.parent / "certs"),
            key_dir=str(self.output_dir.parent / "keys")
        )
        self._save_config("https_simple", config)
        
        # 4. HTTPS with Token Auth
        config = ConfigFactory.create_https_token(
            port=20023,
            log_dir=str(self.output_dir.parent / "logs"),
            cert_dir=str(self.output_dir.parent / "certs"),
            key_dir=str(self.output_dir.parent / "keys"),
            api_keys=api_keys
        )
        self._save_config("https_token", config)
        
        # 5. mTLS Simple
        config = ConfigFactory.create_mtls_simple(
            port=20024,
            log_dir=str(self.output_dir.parent / "logs"),
            cert_dir=str(self.output_dir.parent / "certs"),
            key_dir=str(self.output_dir.parent / "keys")
        )
        self._save_config("mtls_simple", config)
        
        # 6. mTLS with Roles
        roles = {
            "admin": ["read", "write", "delete", "admin"],
            "user": ["read", "write"],
            "guest": ["read"]
        }
        config = ConfigFactory.create_mtls_with_roles(
            port=20025,
            log_dir=str(self.output_dir.parent / "logs"),
            cert_dir=str(self.output_dir.parent / "certs"),
            key_dir=str(self.output_dir.parent / "keys"),
            roles=roles
        )
        self._save_config("mtls_with_roles", config)
        
        # 7. mTLS with Proxy Registration
        config = ConfigFactory.create_mtls_with_proxy(
            port=20026,
            log_dir=str(self.output_dir.parent / "logs"),
            cert_dir=str(self.output_dir.parent / "certs"),
            key_dir=str(self.output_dir.parent / "keys"),
            proxy_url="https://127.0.0.1:20005",
            server_id="mcp_test_server"
        )
        self._save_config("mtls_with_proxy", config)
        
        # 8. Full Featured Configuration
        config = ConfigFactory.create_full_featured(
            port=20027,
            log_dir=str(self.output_dir.parent / "logs"),
            cert_dir=str(self.output_dir.parent / "certs"),
            key_dir=str(self.output_dir.parent / "keys"),
            proxy_url="https://127.0.0.1:20005",
            server_id="mcp_full_server"
        )
        self._save_config("full_featured", config)
        
        # 9. Additional configurations for comprehensive testing
        
        # mTLS No Roles (for testing without role-based access)
        config = ConfigFactory.create_mtls_simple(
            port=20028,
            log_dir=str(self.output_dir.parent / "logs"),
            cert_dir=str(self.output_dir.parent / "certs"),
            key_dir=str(self.output_dir.parent / "keys")
        )
        self._save_config("mtls_no_roles", config)
        
        print(f"✅ Created {len(list(self.output_dir.glob('*.json')))} test configurations in {self.output_dir}/")
        
        # Create roles.json file for role-based configurations
        self._create_roles_file(roles)

    def _create_roles_file(self, roles: Dict[str, list]):
        """Create roles.json file for role-based access control."""
        roles_config = {
            "enabled": True,
            "default_policy": {
                "deny_by_default": False,
                "require_role_match": False,
                "case_sensitive": False,
                "allow_wildcard": False
            },
            "roles": roles,
            "permissions": {
                "read": ["GET"],
                "write": ["POST", "PUT", "PATCH"],
                "delete": ["DELETE"],
                "admin": ["*"]
            }
        }
        
        roles_path = self.output_dir / "roles.json"
        with open(roles_path, 'w', encoding='utf-8') as f:
            json.dump(roles_config, f, indent=2, ensure_ascii=False)
        print(f"✅ Created roles.json: {roles_path}")



def main():
    """Main function to create all test configurations."""
    print("🔧 Creating Test Configurations")
    print("=" * 40)
    
    generator = TestConfigGenerator()
    generator.create_all_test_configs()
    
    print("\n🎉 All test configurations created successfully!")
    print(f"📁 Output directory: {generator.output_dir}")


if __name__ == "__main__":
    main()