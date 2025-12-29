#!/usr/bin/env python3
"""
Simple Configuration Generator for MCP Proxy Adapter
Generates a complete configuration with HTTP protocol and all restrictions disabled.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import uuid
import argparse
from pathlib import Path
from typing import Dict, Any


def generate_complete_config(host: str = "0.0.0.0", port: int = 8000) -> Dict[str, Any]:
    """
    Generate a complete configuration with all required sections.
    HTTP protocol with all security features disabled.
    
    Args:
        host: Server host
        port: Server port
        
    Returns:
        Complete configuration dictionary
    """
    return {
        "uuid": str(uuid.uuid4()),  # This generates valid UUID4
        "server": {
            "host": host,
            "port": port,
            "protocol": "http",
            "debug": False,
            "log_level": "INFO"
        },
        "logging": {
            "level": "INFO",
            "file": None,
            "log_dir": "./logs",
            "log_file": "mcp_proxy_adapter.log",
            "error_log_file": "mcp_proxy_adapter_error.log",
            "access_log_file": "mcp_proxy_adapter_access.log",
            "max_file_size": "10MB",
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S",
            "console_output": True,
            "file_output": True
        },
        "commands": {
            "auto_discovery": True,
            "commands_directory": "./commands",
            "catalog_directory": "./catalog",
            "plugin_servers": [],
            "auto_install_dependencies": True,
            "enabled_commands": ["health", "echo", "list", "help"],
            "disabled_commands": [],
            "custom_commands_path": "./commands"
        },
        "transport": {
            "type": "http",
            "port": None,
            "verify_client": False,
            "chk_hostname": False
        },
        "proxy_registration": {
            "enabled": False,
            "protocol": "mtls",
            "proxy_url": "https://172.28.0.10:3004",
            "server_id": "mcp_proxy_adapter",
            "server_name": "MCP Proxy Adapter",
            "description": "JSON-RPC API for interacting with MCP Proxy",
            "version": "6.2.33",
            "registration_timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 5,
            "auto_register_on_startup": True,
            "auto_unregister_on_shutdown": True,
            "verify_ssl": True,
            "verify_hostname": False,
            "heartbeat": {
                "enabled": True,
                "interval": 30,
                "timeout": 10,
                "retry_attempts": 3,
                "retry_delay": 5,
                "url": "/heartbeat"
            }
        },
        "debug": {
            "enabled": False,
            "level": "WARNING"
        },
        "ssl": {
            "enabled": False,
            "cert_file": None,
            "key_file": None,
            "ca_cert": None
        },
        "security": {
            "enabled": False,
            "tokens": {},
            "roles": {},
            "roles_file": None
        },
        "roles": {
            "enabled": False,
            "config_file": None,
            "default_policy": {
                "deny_by_default": False,
                "require_role_match": False,
                "case_sensitive": False,
                "allow_wildcard": False
            },
            "auto_load": False,
            "validation_enabled": False
        }
    }


def save_config(config: Dict[str, Any], output_file: str) -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary
        output_file: Output file path
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuration saved to: {output_path}")


def main():
    """Main function to generate configuration."""
    parser = argparse.ArgumentParser(
        description="Generate complete MCP Proxy Adapter configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python config_builder.py
  python config_builder.py --host 127.0.0.1 --port 9000
  python config_builder.py --output ./configs/my_config.json
        """
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )
    
    parser.add_argument(
        "--output",
        default="config.json",
        help="Output file path (default: config.json)"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated configuration"
    )
    
    args = parser.parse_args()
    
    print("🔧 Generating MCP Proxy Adapter configuration...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Protocol: HTTP")
    print(f"   Security: Disabled")
    print(f"   SSL: Disabled")
    print(f"   Roles: Disabled")
    print()
    
    # Generate configuration
    config = generate_complete_config(args.host, args.port)
    
    # Save configuration
    save_config(config, args.output)
    
    # Validate if requested
    if args.validate:
        print("\n🔍 Validating configuration...")
        try:
            from mcp_proxy_adapter.core.config_validator import ConfigValidator
            
            validator = ConfigValidator()
            validator.config_data = config
            results = validator.validate_config()
            
            if results:
                print("⚠️  Validation issues found:")
                for result in results:
                    level_symbol = {
                        "error": "❌",
                        "warning": "⚠️",
                        "info": "ℹ️"
                    }[result.level]
                    print(f"  {level_symbol} {result.message}")
                    if result.suggestion:
                        print(f"     Suggestion: {result.suggestion}")
            else:
                print("✅ Configuration validation passed!")
                
        except ImportError:
            print("⚠️  Configuration validation not available")
        except Exception as e:
            print(f"❌ Validation error: {e}")
    
    print(f"\n📋 Configuration summary:")
    print(f"   - Server: {config['server']['host']}:{config['server']['port']}")
    print(f"   - Protocol: {config['server']['protocol']}")
    print(f"   - Security: {'Enabled' if config['security']['enabled'] else 'Disabled'}")
    print(f"   - SSL: {'Enabled' if config.get('ssl', {}).get('enabled', False) else 'Disabled'}")
    print(f"   - Roles: {'Enabled' if config['roles']['enabled'] else 'Disabled'}")
    print(f"   - Proxy Registration: {'Enabled' if config['proxy_registration']['enabled'] else 'Disabled'}")


if __name__ == "__main__":
    main()