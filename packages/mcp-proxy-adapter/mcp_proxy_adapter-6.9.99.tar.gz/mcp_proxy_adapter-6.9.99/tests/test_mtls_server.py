#!/usr/bin/env python3
"""
Test mTLS Server for MCP Proxy Adapter
This server automatically registers with mcp-proxy:3004 using mTLS

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from mcp_proxy_adapter.core.server_adapter import UnifiedServerRunner
    from mcp_proxy_adapter.api.app import create_app
    from mcp_proxy_adapter.core.config_validator import ConfigValidator
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure the package is installed: pip install -e .")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from environment or default path."""
    config_path = os.getenv('CONFIG_PATH', './mtls_docker_test/mtls.json')
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate configuration
        validator = ConfigValidator()
        validator.config_data = config
        results = validator.validate_config()
        
        errors = [r for r in results if r.level == "error"]
        if errors:
            print("❌ Configuration validation errors:")
            for error in errors:
                print(f"  • {error.message}")
            sys.exit(1)
        
        warnings = [r for r in results if r.level == "warning"]
        if warnings:
            print("⚠️  Configuration validation warnings:")
            for warning in warnings:
                print(f"  • {warning.message}")
        
        print("✅ Configuration loaded and validated successfully")
        return config
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        sys.exit(1)

def main():
    """Main function to start the test server."""
    print("🚀 Starting MCP Proxy Adapter Test Server")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    
    # Print configuration summary
    print(f"📋 Server Configuration:")
    print(f"  • Host: {config['server']['host']}")
    print(f"  • Port: {config['server']['port']}")
    print(f"  • Protocol: {config['server']['protocol']}")
    print(f"  • Proxy Registration: {'Enabled' if config['proxy_registration']['enabled'] else 'Disabled'}")
    if config['proxy_registration']['enabled']:
        print(f"  • Proxy URL: {config['proxy_registration']['proxy_url']}")
    print(f"  • SSL Enabled: {config['ssl']['enabled']}")
    print(f"  • Client Verification: {config['transport']['verify_client']}")
    print(f"  • DNS Check: {not config['transport']['chk_hostname']}")
    print("=" * 50)
    
    try:
        # Create ASGI application
        app = create_app(app_config=config)
        
        # Prepare server configuration
        server_config = {
            'host': config['server']['host'],
            'port': config['server']['port'],
            'log_level': config['server'].get('log_level', 'INFO'),
            'reload': False
        }
        
        # Add SSL configuration for mTLS
        if config['ssl']['enabled']:
            server_config.update({
                'certfile': config['ssl']['cert_file'],
                'keyfile': config['ssl']['key_file'],
                'ca_certs': config['ssl']['ca_cert'],
                'verify_mode': 'CERT_REQUIRED' if config['transport']['verify_client'] else 'CERT_NONE'
            })
        
        print("🌐 Starting server...")
        print(f"🔗 Server will be available at: https://{server_config['host']}:{server_config['port']}")
        print("🔐 mTLS authentication required")
        print("📡 Auto-registration with proxy enabled")
        print("=" * 50)
        
        # Start server using UnifiedServerRunner
        runner = UnifiedServerRunner()
        runner.run_server(app, server_config)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        logger.exception("Server error details:")
        sys.exit(1)

if __name__ == "__main__":
    main()
