"""
Server Command

This module implements the server command for starting MCP Proxy Adapter server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
from pathlib import Path
from typing import Dict, Any

try:
    from mcp_proxy_adapter.core.validation.config_validator import ConfigValidator
    from mcp_proxy_adapter.core.server_adapter import UnifiedServerRunner
    from mcp_proxy_adapter.api.app import create_app
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False


class ServerCommand:
    """Command for starting the MCP Proxy Adapter server."""
    
    def __init__(self):
        """Initialize the server command."""
        pass
    
    def execute(self, args: Dict[str, Any]) -> int:
        """
        Execute the server command.
        
        Args:
            args: Parsed command arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        config_file = args['config']
        no_validate = args.get('no_validate', False)
        
        try:
            # Load configuration
            print(f"🔍 Loading configuration from: {config_file}")
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate configuration if not disabled
            if not no_validate and VALIDATION_AVAILABLE:
                print("🔍 Validating configuration...")
                if not self._validate_config(config, config_file):
                    print("❌ Configuration validation failed. Server not started.")
                    return 1
                print("✅ Configuration validation passed!")
            elif no_validate:
                print("⚠️  Configuration validation skipped (--no-validate)")
            else:
                print("⚠️  Configuration validation not available")
            
            # Override configuration with command line arguments
            if args.get('port'):
                config['server']['port'] = args['port']
                print(f"🔧 Overriding port to: {args['port']}")
            
            if args.get('host'):
                config['server']['host'] = args['host']
                print(f"🔧 Overriding host to: {args['host']}")
            
            # Create and start server
            print("🚀 Starting MCP Proxy Adapter server...")
            self._start_server(config, args)
            
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {config_file}")
            return 1
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in configuration file: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return 1
    
    def _validate_config(self, config: Dict[str, Any], config_file: str) -> bool:
        """
        Validate configuration using ConfigValidator.
        
        Args:
            config: Configuration dictionary
            config_file: Path to configuration file
            
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            validator = ConfigValidator()
            validator.config_data = config
            results = validator.validate_config()
            
            # Check for errors
            errors = [r for r in results if r.level == "error"]
            warnings = [r for r in results if r.level == "warning"]
            
            if errors:
                print("❌ Configuration validation errors:")
                for error in errors:
                    print(f"  • {error.message}")
                    if hasattr(error, 'suggestion') and error.suggestion:
                        print(f"    → {error.suggestion}")
                return False
            
            if warnings:
                print("⚠️  Configuration validation warnings:")
                for warning in warnings:
                    print(f"  • {warning.message}")
                    if hasattr(warning, 'suggestion') and warning.suggestion:
                        print(f"    → {warning.suggestion}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during configuration validation: {e}")
            return False
    
    def _start_server(self, config: Dict[str, Any], args: Dict[str, Any]) -> None:
        """
        Start the MCP Proxy Adapter server.
        
        Args:
            config: Server configuration
            args: Command line arguments
        """
        try:
            # Create ASGI application
            app = create_app(config)
            
            # Prepare server configuration
            server_config = {
                'host': config['server']['host'],
                'port': config['server']['port'],
                'log_level': config['server'].get('log_level', 'INFO'),
                'reload': args.get('reload', False)
            }
            
            # Add SSL configuration if present
            if 'ssl' in config and config['ssl'].get('enabled'):
                server_config.update({
                    'certfile': config['ssl'].get('cert_file'),
                    'keyfile': config['ssl'].get('key_file'),
                    'ca_certs': config['ssl'].get('ca_cert'),
                    'verify_mode': 'CERT_REQUIRED' if config.get('transport', {}).get('verify_client') else 'CERT_NONE'
                })
            
            # Start server
            print(f"🌐 Server starting on {server_config['host']}:{server_config['port']}")
            print(f"📋 Protocol: {config['server']['protocol']}")
            print(f"🔐 Security: {'Enabled' if config.get('security', {}).get('enabled') else 'Disabled'}")
            print(f"🔑 Authentication: {'Token-based' if config.get('security', {}).get('tokens') else 'Certificate-based' if config['server']['protocol'] == 'mtls' else 'None'}")
            print(f"👥 Roles: {'Enabled' if config.get('roles', {}).get('enabled') else 'Disabled'}")
            print("=" * 60)
            
            # Use UnifiedServerRunner to start the server
            runner = UnifiedServerRunner()
            runner.run_server(app, server_config)
            
        except ImportError as e:
            print(f"❌ Missing required dependencies: {e}")
            print("💡 Install required packages: pip install hypercorn")
            raise
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            raise


