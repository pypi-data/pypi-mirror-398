#!/usr/bin/env python3
"""
Configuration Generator CLI for MCP Proxy Adapter
Generates configurations based on command line flags with validation.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Add the current directory to the path to import config_builder
sys.path.insert(0, str(Path(__file__).parent))

from config_builder import generate_complete_config

# Import validation modules
try:
    from mcp_proxy_adapter.core.config_validator import ConfigValidator
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    print("Warning: Configuration validation not available. Install the package to enable validation.")


def create_config_from_flags(
    protocol: str,
    token: bool = False,
    roles: bool = False,
    host: str = "127.0.0.1",
    port: int = 8000,
    cert_dir: str = "./certs",
    key_dir: str = "./keys",
    output_dir: str = "./configs",
    proxy_registration: bool = False,
    proxy_url: str = None,
    auto_registration: bool = False,
    server_id: str = "mcp_proxy_adapter"
) -> Dict[str, Any]:
    """
    Create configuration based on command line flags.
    
    Args:
        protocol: Protocol type (http, https, mtls)
        token: Enable token authentication
        roles: Enable role-based access control
        host: Server host
        port: Server port
        cert_dir: Certificate directory
        key_dir: Key directory
        output_dir: Output directory for configs
        
    Returns:
        Configuration dictionary
    """
    # Start with basic configuration
    config = generate_complete_config(host, port)
    
    # Set protocol
    config["server"]["protocol"] = protocol
    
    # Configure SSL based on protocol
    if protocol == "https":
        config["ssl"]["enabled"] = True
        config["ssl"]["cert_file"] = f"{cert_dir}/mcp-proxy.crt"
        config["ssl"]["key_file"] = f"{key_dir}/mcp-proxy.key"
        # Update transport for HTTPS
        config["transport"]["type"] = "https"
        config["transport"]["chk_hostname"] = True
    elif protocol == "mtls":
        config["ssl"]["enabled"] = True
        config["ssl"]["cert_file"] = f"{cert_dir}/mcp-proxy.crt"
        config["ssl"]["key_file"] = f"{key_dir}/mcp-proxy.key"
        config["ssl"]["ca_cert"] = f"{cert_dir}/../ca/ca.crt"
        # Update transport for mTLS
        config["transport"]["type"] = "https"
        config["transport"]["chk_hostname"] = False  # Disable hostname check for mTLS
        config["transport"]["verify_client"] = True
        # Add SSL section to transport for mTLS
        config["transport"]["ssl"] = {
            "verify_client": True,
            "ca_cert": f"{cert_dir}/../ca/ca.crt"
        }
    
    # Configure security if token authentication is enabled
    if token:
        config["security"]["enabled"] = True
        config["security"]["tokens"] = {
            "admin": "admin-secret-key",
            "user": "user-secret-key",
            "readonly": "readonly-secret-key"
        }
        
        if roles:
            config["security"]["roles"] = {
                "admin": ["read", "write", "delete", "admin"],
                "user": ["read", "write"],
                "readonly": ["read"]
            }
            config["security"]["roles_file"] = f"{output_dir}/roles.json"
            config["roles"]["enabled"] = True
            config["roles"]["config_file"] = f"{output_dir}/roles.json"
    
    # Configure proxy registration if enabled
    if proxy_registration or auto_registration:
        if not proxy_url:
            raise ValueError("proxy_url is required when proxy registration is enabled")
        
        config["proxy_registration"]["enabled"] = True
        config["proxy_registration"]["protocol"] = protocol
        config["proxy_registration"]["proxy_url"] = proxy_url
        config["proxy_registration"]["server_id"] = server_id
        
        # Update server URL based on protocol
        if protocol == "https" or protocol == "mtls":
            config["proxy_registration"]["proxy_url"] = proxy_url.replace("http://", "https://")
        
        # For mTLS, disable DNS verification but keep SSL verification
        if protocol == "mtls":
            config["proxy_registration"]["verify_ssl"] = True
            config["proxy_registration"]["verify_hostname"] = False  # Disable DNS verification only
    
    return config


def save_config(config: Dict[str, Any], filename: str, output_dir: str, validate: bool = True) -> Path:
    """Save configuration to file with optional validation."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    config_file = output_path / f"{filename}.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    # Validate configuration if requested and validation is available
    if validate and VALIDATION_AVAILABLE:
        print(f"🔍 Validating configuration: {config_file}")
        validator = ConfigValidator()
        validator.config_data = config
        results = validator.validate_config()
        
        if results:
            print("⚠️  Validation issues found:")
            for result in results:
                level_symbol = "❌" if result.level == "error" else "⚠️" if result.level == "warning" else "ℹ️"
                print(f"  {level_symbol} {result.message}")
                if hasattr(result, 'suggestion') and result.suggestion:
                    print(f"     Suggestion: {result.suggestion}")
        else:
            print("✅ Configuration validation passed!")
    
    return config_file


def create_full_config_with_all_options(host: str = "127.0.0.1", port: int = 20000) -> Dict[str, Any]:
    """
    Create a full configuration with all options enabled but set to HTTP base.
    This allows testing all features by enabling different sections.
    
    Args:
        host: Server host
        port: Server port
        
    Returns:
        Full configuration dictionary with all options
    """
    # Start with basic configuration
    config = generate_complete_config(host, port)
    
    # Add protocol variants for easy switching
    config["protocol_variants"] = {
        "http": {"server": {"protocol": "http"}},
        "https": {"server": {"protocol": "https"}},
        "mtls": {"server": {"protocol": "mtls"}}
    }
    
    # Add authentication configurations for easy switching
    api_keys = {
        "admin": "admin-secret-key",
        "user": "user-secret-key", 
        "readonly": "readonly-secret-key"
    }
    roles = {
        "admin": ["read", "write", "delete", "admin"],
        "user": ["read", "write"],
        "readonly": ["read"]
    }
    
    config["auth_variants"] = {
        "none": {"security": {"enabled": False}},
        "token": {
            "security": {
                "enabled": True,
                "tokens": api_keys,
                "roles": roles,
                "roles_file": None
            }
        },
        "token_roles": {
            "security": {
                "enabled": True,
                "tokens": api_keys,
                "roles": roles,
                "roles_file": "configs/roles.json"
            }
        }
    }
    
    return config


def generate_all_configs(output_dir: str = "./configs", host: str = "127.0.0.1", validate: bool = True) -> None:
    """Generate all standard configurations."""
    configs = [
        # HTTP configurations
        ("http", False, False, 20000),
        ("http", True, True, 20001),  # token=True always includes roles
        ("http", True, True, 20002),  # token_roles is same as token now
        
        # HTTPS configurations
        ("https", False, False, 20003),
        ("https", True, True, 20004),  # token=True always includes roles
        ("https", True, True, 20005),  # token_roles is same as token now
        
        # mTLS configurations
        ("mtls", False, False, 20006),
        ("mtls", True, True, 20007),  # token=True always includes roles
        ("mtls", True, True, 20008),  # token_roles is same as token now
    ]
    
    print("🔧 Generating MCP Proxy Adapter configurations...")
    print("=" * 60)
    
    generated_files = []
    
    for protocol, token, roles, port in configs:
        # Create configuration name
        name_parts = [protocol]
        if token:
            name_parts.append("token")
        if roles:
            name_parts.append("roles")
        
        config_name = "_".join(name_parts)
        
        # Generate configuration
        config = create_config_from_flags(
            protocol=protocol,
            token=token,
            roles=roles,
            host=host,
            port=port,
            output_dir=output_dir
        )
        
        # Save configuration with validation
        config_file = save_config(config, config_name, output_dir, validate=validate)
        generated_files.append(config_file)
        
        print(f"✅ Created {config_name}.json (port {port})")
    
    # Create roles.json file if any role-based configs were generated
    roles_config = {
        "enabled": True,
        "default_policy": {
            "deny_by_default": False,
            "require_role_match": False,
            "case_sensitive": False,
            "allow_wildcard": False
        },
        "roles": {
            "admin": ["read", "write", "delete", "admin"],
            "user": ["read", "write"],
            "readonly": ["read"],
            "guest": ["read"],
            "proxy": ["read", "write"]
        },
        "permissions": {
            "read": ["GET"],
            "write": ["POST", "PUT", "PATCH"],
            "delete": ["DELETE"],
            "admin": ["*"]
        }
    }
    
    roles_file = Path(output_dir) / "roles.json"
    with open(roles_file, 'w', encoding='utf-8') as f:
        json.dump(roles_config, f, indent=2, ensure_ascii=False)
    print(f"✅ Created roles.json")
    
    print(f"\n🎉 Generated {len(generated_files)} configurations in {output_dir}/")
    print("\n📋 Generated configurations:")
    for config_file in generated_files:
        print(f"  - {config_file.name}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="MCP Proxy Adapter Configuration Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all standard configurations
  python generate_config.py --all
  
  # Generate full config with all options (HTTP base)
  python generate_config.py --full-config
  
  # Generate specific configuration
  python generate_config.py --protocol https --token --roles --port 8080
  
  # Generate HTTP configuration with token auth
  python generate_config.py --protocol http --token
  
  # Generate mTLS configuration with roles
  python generate_config.py --protocol mtls --roles
  
        # Generate mTLS configuration with automatic proxy registration
        python generate_config.py --protocol mtls --auto-registration --proxy-url https://172.28.0.10:3004
        
        # Generate HTTP configuration with automatic proxy registration
        python generate_config.py --protocol http --proxy-registration --proxy-url http://172.28.0.10:3004
        """
    )
    
    # Configuration options
    parser.add_argument("--protocol", choices=["http", "https", "mtls"], 
                       help="Protocol type (http, https, mtls)")
    parser.add_argument("--token", action="store_true", 
                       help="Enable token authentication")
    parser.add_argument("--roles", action="store_true", 
                       help="Enable role-based access control")
    parser.add_argument("--proxy-registration", action="store_true", 
                       help="Enable proxy registration with auto-determined parameters")
    parser.add_argument("--proxy-url", 
                       help="Proxy URL for registration (required when --proxy-registration is enabled)")
    parser.add_argument("--auto-registration", action="store_true",
                       help="Enable automatic proxy registration (same as --proxy-registration)")
    parser.add_argument("--server-id", default="mcp_proxy_adapter",
                       help="Server ID for registration (default: mcp_proxy_adapter)")
    parser.add_argument("--all", action="store_true", 
                       help="Generate all standard configurations")
    parser.add_argument("--full-config", action="store_true", 
                       help="Generate full config with all options (HTTP base)")
    
    # Server configuration
    parser.add_argument("--host", default="127.0.0.1", 
                       help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, 
                       help="Server port (default: 8000)")
    
    # Paths
    parser.add_argument("--cert-dir", default="./certs", 
                       help="Certificate directory (default: ./certs)")
    parser.add_argument("--key-dir", default="./keys", 
                       help="Key directory (default: ./keys)")
    parser.add_argument("--output-dir", default="./configs", 
                       help="Output directory (default: ./configs)")
    
    # Output options
    parser.add_argument("--output", "-o", 
                       help="Output filename (without extension)")
    parser.add_argument("--stdout", action="store_true", 
                       help="Output to stdout instead of file")
    parser.add_argument("--no-validate", action="store_true", 
                       help="Skip configuration validation")
    parser.add_argument("--validate-only", action="store_true", 
                       help="Only validate existing configuration file")
    
    args = parser.parse_args()
    
    # Validate required arguments
    if not args.validate_only and not args.all and not args.full_config:
        if not args.protocol:
            parser.error("--protocol is required")
        
        if (args.proxy_registration or args.auto_registration) and not args.proxy_url:
            parser.error("--proxy-url is required when --proxy-registration or --auto-registration is enabled")
        
        # Validate port range
        if not (1 <= args.port <= 65535):
            parser.error("Port must be between 1 and 65535")
        
        # Validate certificate directories for HTTPS/mTLS
        if args.protocol in ['https', 'mtls']:
            if not os.path.exists(args.cert_dir):
                parser.error(f"Certificate directory does not exist: {args.cert_dir}")
            if not os.path.exists(args.key_dir):
                parser.error(f"Key directory does not exist: {args.key_dir}")
        
        # Validate output directory
        if not os.path.exists(args.output_dir):
            try:
                os.makedirs(args.output_dir, exist_ok=True)
            except OSError as e:
                parser.error(f"Cannot create output directory {args.output_dir}: {e}")
    
    try:
        if args.validate_only:
            # Validate existing configuration file
            if not VALIDATION_AVAILABLE:
                print("❌ Validation not available. Install the package to enable validation.")
                return 1
            
            config_file = args.output or "config.json"
            if not os.path.exists(config_file):
                print(f"❌ Configuration file not found: {config_file}")
                return 1
            
            print(f"🔍 Validating configuration file: {config_file}")
            validator = ConfigValidator()
            validator.load_config(config_file)
            results = validator.validate_config()
            
            if results:
                print("⚠️  Validation issues found:")
                for result in results:
                    level_symbol = "❌" if result.level == "error" else "⚠️" if result.level == "warning" else "ℹ️"
                    print(f"  {level_symbol} {result.message}")
                    if hasattr(result, 'suggestion') and result.suggestion:
                        print(f"     Suggestion: {result.suggestion}")
            else:
                print("✅ Configuration validation passed!")
            
            # Check if there are any errors
            errors = [r for r in results if r.level == "error"] if results else []
            return 0 if not errors else 1
        
        elif args.all:
            # Generate all configurations
            generate_all_configs(
                output_dir=args.output_dir,
                host=args.host,
                validate=not args.no_validate
            )
        elif args.full_config:
            # Generate full config with all options
            config = create_full_config_with_all_options(
                host=args.host,
                port=args.port
            )
            
            if args.stdout:
                # Output to stdout
                print(json.dumps(config, indent=2, ensure_ascii=False))
            else:
                # Save to file
                filename = args.output or "full_config"
                config_file = save_config(config, filename, args.output_dir, validate=not args.no_validate)
                print(f"✅ Full configuration saved to: {config_file}")
        elif args.protocol:
            
            # Generate specific configuration
            config = create_config_from_flags(
                protocol=args.protocol,
                token=args.token,
                roles=args.roles,
                port=args.port,
                cert_dir=args.cert_dir,
                key_dir=args.key_dir,
                output_dir=args.output_dir,
                proxy_registration=args.proxy_registration,
                proxy_url=args.proxy_url,
                auto_registration=args.auto_registration,
                server_id=args.server_id
            )
            
            if args.stdout:
                # Output to stdout
                print(json.dumps(config, indent=2, ensure_ascii=False))
            else:
                # Save to file
                if args.output:
                    filename = args.output
                else:
                    # Generate filename from flags
                    name_parts = [args.protocol]
                    if args.token:
                        name_parts.append("token")
                    if args.roles:
                        name_parts.append("roles")
                    filename = "_".join(name_parts)
                
                config_file = save_config(config, filename, args.output_dir, validate=not args.no_validate)
                print(f"✅ Configuration saved to: {config_file}")
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
