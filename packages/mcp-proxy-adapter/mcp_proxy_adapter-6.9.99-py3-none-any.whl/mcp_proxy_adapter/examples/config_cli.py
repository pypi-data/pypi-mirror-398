#!/usr/bin/env python3
"""
CLI Utility for MCP Proxy Adapter Configuration Builder
Command-line interface for creating configurations with various parameters.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import argparse
import json
import sys
from pathlib import Path

from config_builder import ConfigBuilder, ConfigFactory, Protocol, AuthMethod


def parse_protocol(protocol_str: str) -> Protocol:
    """Parse protocol string to Protocol enum."""
    protocol_map = {
        "http": Protocol.HTTP,
        "https": Protocol.HTTPS,
        "mtls": Protocol.MTLS
    }
    if protocol_str.lower() not in protocol_map:
        raise ValueError(f"Invalid protocol: {protocol_str}. Must be one of: {list(protocol_map.keys())}")
    return protocol_map[protocol_str.lower()]


def parse_auth_method(auth_str: str) -> AuthMethod:
    """Parse authentication method string to AuthMethod enum."""
    auth_map = {
        "none": AuthMethod.NONE,
        "token": AuthMethod.TOKEN,
        "basic": AuthMethod.BASIC
    }
    if auth_str.lower() not in auth_map:
        raise ValueError(f"Invalid auth method: {auth_str}. Must be one of: {list(auth_map.keys())}")
    return auth_map[auth_str.lower()]


def parse_api_keys(api_keys_str: str) -> Dict[str, str]:
    """Parse API keys from string format 'key1:value1,key2:value2'."""
    if not api_keys_str:
        return {}
    
    api_keys = {}
    for pair in api_keys_str.split(','):
        if ':' not in pair:
            raise ValueError(f"Invalid API key format: {pair}. Expected 'key:value'")
        key, value = pair.split(':', 1)
        api_keys[key.strip()] = value.strip()
    
    return api_keys


def parse_roles(roles_str: str) -> Dict[str, List[str]]:
    """Parse roles from string format 'role1:perm1,perm2;role2:perm3,perm4'."""
    if not roles_str:
        return {}
    
    roles = {}
    for role_def in roles_str.split(';'):
        if ':' not in role_def:
            raise ValueError(f"Invalid role format: {role_def}. Expected 'role:perm1,perm2'")
        role, perms = role_def.split(':', 1)
        roles[role.strip()] = [perm.strip() for perm in perms.split(',')]
    
    return roles


def create_custom_config(args) -> Dict[str, Any]:
    """Create custom configuration based on command line arguments."""
    builder = ConfigBuilder()
    
    # Set server configuration
    builder.set_server(
        host=args.host,
        port=args.port,
        debug=args.debug,
        log_level=args.log_level
    )
    
    # Set logging configuration
    builder.set_logging(
        log_dir=args.log_dir,
        level=args.log_level,
        console_output=not args.no_console,
        file_output=not args.no_file_log
    )
    
    # Set protocol
    protocol = parse_protocol(args.protocol)
    builder.set_protocol(
        protocol,
        cert_dir=args.cert_dir,
        key_dir=args.key_dir
    )
    
    # Set authentication
    auth_method = parse_auth_method(args.auth)
    api_keys = parse_api_keys(args.api_keys) if args.api_keys else None
    roles = parse_roles(args.roles) if args.roles else None
    
    builder.set_auth(auth_method, api_keys=api_keys, roles=roles)
    
    # Set proxy registration
    if args.proxy_url:
        builder.set_proxy_registration(
            enabled=True,
            proxy_url=args.proxy_url,
            server_id=args.server_id,
            cert_dir=args.cert_dir
        )
    
    # Set debug
    if args.debug:
        builder.set_debug(enabled=True, log_level=args.log_level)
    
    # Set commands
    if args.enabled_commands or args.disabled_commands:
        enabled = args.enabled_commands.split(',') if args.enabled_commands else None
        disabled = args.disabled_commands.split(',') if args.disabled_commands else None
        builder.set_commands(enabled_commands=enabled, disabled_commands=disabled)
    
    return builder.build()


def create_preset_config(preset: str, **kwargs) -> Dict[str, Any]:
    """Create preset configuration."""
    preset_map = {
        "http_simple": ConfigFactory.create_http_simple,
        "http_token": ConfigFactory.create_http_token,
        "https_simple": ConfigFactory.create_https_simple,
        "https_token": ConfigFactory.create_https_token,
        "mtls_simple": ConfigFactory.create_mtls_simple,
        "mtls_with_roles": ConfigFactory.create_mtls_with_roles,
        "mtls_with_proxy": ConfigFactory.create_mtls_with_proxy,
        "full_featured": ConfigFactory.create_full_featured,
    }
    
    if preset not in preset_map:
        raise ValueError(f"Invalid preset: {preset}. Must be one of: {list(preset_map.keys())}")
    
    return preset_map[preset](**kwargs)


def list_presets():
    """List available presets."""
    presets = [
        ("http_simple", "Simple HTTP server without authentication"),
        ("http_token", "HTTP server with token authentication"),
        ("https_simple", "Simple HTTPS server without authentication"),
        ("https_token", "HTTPS server with token authentication"),
        ("mtls_simple", "Simple mTLS server without authentication"),
        ("mtls_with_roles", "mTLS server with role-based access control"),
        ("mtls_with_proxy", "mTLS server with proxy registration"),
        ("full_featured", "Full-featured server with all options enabled"),
    ]
    
    print("📋 Available Configuration Presets:")
    print("=" * 50)
    for preset, description in presets:
        print(f"  {preset:<20} - {description}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="MCP Proxy Adapter Configuration Builder CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create HTTP simple configuration
  python config_cli.py --preset http_simple --output configs/http_simple.json
  
  # Create custom HTTPS configuration with token auth
  python config_cli.py --protocol https --auth token --api-keys "admin:admin-key,user:user-key" --output configs/https_token.json
  
  # Create mTLS configuration with proxy registration
  python config_cli.py --protocol mtls --proxy-url "https://proxy.example.com:8080" --server-id "my_server" --output configs/mtls_proxy.json
  
  # List all available presets
  python config_cli.py --list-presets
        """
    )
    
    # Main options
    parser.add_argument("--preset", help="Use a preset configuration")
    parser.add_argument("--list-presets", action="store_true", help="List available presets")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    
    # Server configuration
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level (default: INFO)")
    
    # Logging configuration
    parser.add_argument("--log-dir", default="./logs", help="Log directory (default: ./logs)")
    parser.add_argument("--no-console", action="store_true", help="Disable console output")
    parser.add_argument("--no-file-log", action="store_true", help="Disable file logging")
    
    # Protocol configuration
    parser.add_argument("--protocol", choices=["http", "https", "mtls"], default="http", help="Protocol (default: http)")
    parser.add_argument("--cert-dir", default="./certs", help="Certificate directory (default: ./certs)")
    parser.add_argument("--key-dir", default="./keys", help="Key directory (default: ./keys)")
    
    # Authentication configuration
    parser.add_argument("--auth", choices=["none", "token", "basic"], default="none", help="Authentication method (default: none)")
    parser.add_argument("--api-keys", help="API keys in format 'key1:value1,key2:value2'")
    parser.add_argument("--roles", help="Roles in format 'role1:perm1,perm2;role2:perm3,perm4'")
    
    # Proxy registration
    parser.add_argument("--proxy-url", help="Proxy URL for registration")
    parser.add_argument("--server-id", default="mcp_proxy_adapter", help="Server ID for proxy registration (default: mcp_proxy_adapter)")
    
    # Commands configuration
    parser.add_argument("--enabled-commands", help="Comma-separated list of enabled commands")
    parser.add_argument("--disabled-commands", help="Comma-separated list of disabled commands")
    
    # Preset-specific options
    parser.add_argument("--preset-host", help="Host for preset configurations")
    parser.add_argument("--preset-port", type=int, help="Port for preset configurations")
    parser.add_argument("--preset-log-dir", help="Log directory for preset configurations")
    parser.add_argument("--preset-cert-dir", help="Certificate directory for preset configurations")
    parser.add_argument("--preset-key-dir", help="Key directory for preset configurations")
    parser.add_argument("--preset-proxy-url", help="Proxy URL for preset configurations")
    parser.add_argument("--preset-server-id", help="Server ID for preset configurations")
    
    args = parser.parse_args()
    
    try:
        # Handle list presets
        if args.list_presets:
            list_presets()
            return 0
        
        # Create configuration
        if args.preset:
            # Use preset configuration
            preset_kwargs = {}
            if args.preset_host:
                preset_kwargs["host"] = args.preset_host
            if args.preset_port:
                preset_kwargs["port"] = args.preset_port
            if args.preset_log_dir:
                preset_kwargs["log_dir"] = args.preset_log_dir
            if args.preset_cert_dir:
                preset_kwargs["cert_dir"] = args.preset_cert_dir
            if args.preset_key_dir:
                preset_kwargs["key_dir"] = args.preset_key_dir
            if args.preset_proxy_url:
                preset_kwargs["proxy_url"] = args.preset_proxy_url
            if args.preset_server_id:
                preset_kwargs["server_id"] = args.preset_server_id
            
            config = create_preset_config(args.preset, **preset_kwargs)
        else:
            # Create custom configuration
            config = create_custom_config(args)
        
        # Output configuration
        config_json = json.dumps(config, indent=2, ensure_ascii=False)
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(config_json)
            print(f"✅ Configuration saved to: {output_path}")
        else:
            print(config_json)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
