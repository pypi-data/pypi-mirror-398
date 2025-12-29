"""
Generate Command

This module implements the generate command for creating configuration files.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

# Import the existing config generator
try:
    from mcp_proxy_adapter.examples.config_builder import generate_complete_config
    from mcp_proxy_adapter.core.config_validator import ConfigValidator
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    print("Warning: Configuration validation not available. Install the package to enable validation.")


class GenerateCommand:
    """Command for generating configuration files."""
    
    def __init__(self):
        """Initialize the generate command."""
        pass
    
    def execute(self, args: Dict[str, Any]) -> int:
        """
        Execute the generate command.
        
        Args:
            args: Parsed command arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            # Handle special cases
            if args.get('all'):
                return self._generate_all_configs(args)
            
            # Generate single configuration
            return self._generate_single_config(args)
            
        except Exception as e:
            print(f"❌ Error generating configuration: {e}")
            return 1
    
    def _generate_single_config(self, args: Dict[str, Any]) -> int:
        """Generate a single configuration file."""
        # Create configuration
        config = self._create_config_from_args(args)
        
        # Save configuration
        if args.get('stdout'):
            # Output to stdout
            print(json.dumps(config, indent=2, ensure_ascii=False))
        else:
            # Save to file
            config_file = self._save_config(config, args)
            print(f"✅ Configuration saved to: {config_file}")
        
        return 0
    
    def _generate_all_configs(self, args: Dict[str, Any]) -> int:
        """Generate all standard configurations."""
        print("🔧 Generating MCP Proxy Adapter configurations...")
        print("=" * 60)
        
        # Define all standard configurations
        configs = [
            # HTTP configurations
            ("http", False, False, 20000),
            ("http", True, True, 20001),  # token + roles
            ("http", True, False, 20002),  # token only
            
            # HTTPS configurations
            ("https", False, False, 20003),
            ("https", True, True, 20004),  # token + roles
            ("https", True, False, 20005),  # token only
            
            # mTLS configurations
            ("mtls", False, False, 20006),
            ("mtls", False, True, 20007),  # roles only (from certificate)
        ]
        
        generated_files = []
        
        for protocol, token, roles, port in configs:
            # Create configuration name
            name_parts = [protocol]
            if token:
                name_parts.append("token")
            if roles:
                name_parts.append("roles")
            
            config_name = "_".join(name_parts)
            
            # Create args for this configuration
            config_args = args.copy()
            config_args.update({
                'protocol': protocol,
                'token': token,
                'roles': roles,
                'port': port
            })
            
            # Generate configuration
            config = self._create_config_from_args(config_args)
            
            # Save configuration
            config_file = self._save_config(config, config_args, config_name)
            generated_files.append(config_file)
            
            print(f"✅ Created {config_name}.json (port {port})")
        
        # Create roles.json file if any role-based configs were generated
        self._create_roles_file(args.get('output_dir', './configs'))
        
        print(f"\n🎉 Generated {len(generated_files)} configurations in {args.get('output_dir', './configs')}/")
        print("\n📋 Generated configurations:")
        for config_file in generated_files:
            print(f"  - {config_file.name}")
        
        return 0
    
    def _create_config_from_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create configuration dictionary from arguments."""
        # Start with basic configuration
        config = generate_complete_config(
            args.get('host', '127.0.0.1'),
            args.get('port', 8000)
        )
        
        # Set protocol
        config["server"]["protocol"] = args.get('protocol', 'http')
        
        # Configure SSL based on protocol
        if args.get('protocol') == 'https':
            config["ssl"]["enabled"] = True
            config["ssl"]["cert_file"] = f"{args.get('cert_dir', './certs')}/server.crt"
            config["ssl"]["key_file"] = f"{args.get('key_dir', './keys')}/server.key"
        elif args.get('protocol') == 'mtls':
            config["ssl"]["enabled"] = True
            config["ssl"]["cert_file"] = f"{args.get('cert_dir', './certs')}/server.crt"
            config["ssl"]["key_file"] = f"{args.get('key_dir', './keys')}/server.key"
            config["ssl"]["ca_cert"] = f"{args.get('cert_dir', './certs')}/ca.crt"
            config["transport"]["verify_client"] = True
        
        # Configure security if token authentication is enabled
        if args.get('token'):
            config["security"]["enabled"] = True
            config["security"]["tokens"] = {
                "admin": "admin-secret-key",
                "user": "user-secret-key",
                "readonly": "readonly-secret-key"
            }
            
            if args.get('roles'):
                config["security"]["roles"] = {
                    "admin": ["read", "write", "delete", "admin"],
                    "user": ["read", "write"],
                    "readonly": ["read"]
                }
                config["security"]["roles_file"] = f"{args.get('output_dir', './configs')}/roles.json"
                config["roles"]["enabled"] = True
                config["roles"]["config_file"] = f"{args.get('output_dir', './configs')}/roles.json"
        elif args.get('roles') and args.get('protocol') == 'mtls':
            # For mTLS, roles can be enabled without tokens (from certificate)
            config["roles"]["enabled"] = True
            config["roles"]["config_file"] = f"{args.get('output_dir', './configs')}/roles.json"
        
        # Configure proxy registration if enabled
        if args.get('proxy_url'):
            config["proxy_registration"]["enabled"] = True
            config["proxy_registration"]["proxy_url"] = args['proxy_url']
            config["proxy_registration"]["server_id"] = args.get('server_id', 'mcp-proxy-adapter')
        
        return config
    
    def _save_config(self, config: Dict[str, Any], args: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """Save configuration to file with optional validation."""
        output_dir = Path(args.get('output_dir', './configs'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine filename
        if filename:
            config_name = filename
        elif args.get('output'):
            config_name = args['output']
        else:
            # Generate filename from arguments
            name_parts = [args.get('protocol', 'http')]
            if args.get('token'):
                name_parts.append("token")
            if args.get('roles'):
                name_parts.append("roles")
            config_name = "_".join(name_parts)
        
        config_file = output_dir / f"{config_name}.json"
        
        # Save configuration
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Validate configuration if requested and validation is available
        if not args.get('no_validate') and VALIDATION_AVAILABLE:
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
    
    def _create_roles_file(self, output_dir: str) -> None:
        """Create roles.json file for role-based configurations."""
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


