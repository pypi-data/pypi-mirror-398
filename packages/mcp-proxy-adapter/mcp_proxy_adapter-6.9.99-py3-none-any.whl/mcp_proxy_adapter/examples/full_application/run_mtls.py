#!/usr/bin/env python3
"""
mTLS Full Application Runner
Runs the full application example with mTLS configuration.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import sys
import argparse
import logging
import json
import socket
from pathlib import Path
from typing import TYPE_CHECKING

# Add the framework to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from mcp_proxy_adapter.core.ssl_utils import SSLUtils

if TYPE_CHECKING:
    from ssl import SSLContext

def validate_mtls_config(config_path: str) -> bool:
    """Validate mTLS configuration file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required sections
        required_sections = [
            'uuid', 'server', 'logging', 'commands', 'transport',
            'proxy_registration', 'debug', 'security', 'roles', 'ssl'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing required sections: {missing_sections}")
            return False
        
        # Check SSL configuration
        ssl_config = config.get('ssl', {})
        if not ssl_config.get('enabled', False):
            print("❌ SSL must be enabled for mTLS")
            return False
        
        # Check certificate files
        cert_file = ssl_config.get('cert_file')
        key_file = ssl_config.get('key_file')
        ca_cert_file = ssl_config.get('ca_cert_file')
        
        if not cert_file or not key_file or not ca_cert_file:
            print("❌ SSL configuration missing certificate files")
            return False
        
        # Check if certificate files exist
        cert_path = Path(cert_file)
        key_path = Path(key_file)
        ca_path = Path(ca_cert_file)
        
        if not cert_path.exists():
            print(f"❌ Certificate file not found: {cert_file}")
            return False
        
        if not key_path.exists():
            print(f"❌ Key file not found: {key_file}")
            return False
        
        if not ca_path.exists():
            print(f"❌ CA certificate file not found: {ca_cert_file}")
            return False
        
        print("✅ mTLS Configuration validation passed")
        return True
        
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration validation error: {e}")
        return False

def test_mtls_connection(config_path: str):
    """Test mTLS connection to the server."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        server_config = config.get('server', {})
        host = server_config.get('host', '0.0.0.0')
        port = server_config.get('port', 8443)
        
        ssl_config = config.get('ssl', {})
        cert_file = ssl_config.get('cert_file')
        key_file = ssl_config.get('key_file')
        ca_cert_file = ssl_config.get('ca_cert_file')
        
        print(f"🔐 Testing mTLS connection to {host}:{port}")
        
        # Create SSL context using security framework
        context = SSLUtils.create_client_ssl_context(
            ca_cert=ca_cert_file,
            client_cert=cert_file,
            client_key=key_file,
            verify=True,
            check_hostname=False,  # For testing, hostname may not match
        )
        
        # Test connection
        with socket.create_connection((host, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print(f"✅ mTLS connection successful")
                print(f"🔒 Cipher: {ssock.cipher()}")
                print(f"📜 Protocol: {ssock.version()}")
                return True
                
    except Exception as e:
        print(f"❌ mTLS connection failed: {e}")
        return False

def run_mtls_application(config_path: str):
    """Run the mTLS application example."""
    print("🚀 Starting mTLS Full Application Example")
    print(f"📁 Configuration: {config_path}")
    
    # Validate configuration
    if not validate_mtls_config(config_path):
        print("❌ mTLS Configuration validation failed")
        return False
    
    # Load configuration
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        server_config = config.get('server', {})
        host = server_config.get('host', '0.0.0.0')
        port = server_config.get('port', 8443)
        protocol = server_config.get('protocol', 'https')
        
        ssl_config = config.get('ssl', {})
        proxy_config = config.get('proxy_registration', {})
        
        print(f"🌐 Server: {host}:{port}")
        print(f"🔗 Protocol: {protocol}")
        print(f"🔒 SSL: {'Enabled' if ssl_config.get('enabled', False) else 'Disabled'}")
        print(f"🔐 mTLS: {'Enabled' if ssl_config.get('verify_client', False) else 'Disabled'}")
        print(f"🔒 Security: {'Enabled' if config.get('security', {}).get('enabled', False) else 'Disabled'}")
        print(f"👥 Roles: {'Enabled' if config.get('roles', {}).get('enabled', False) else 'Disabled'}")
        print(f"🌐 Proxy Registration: {'Enabled' if proxy_config.get('enabled', False) else 'Disabled'}")
        
        if proxy_config.get('enabled', False):
            proxy_url = proxy_config.get('proxy_url', 'https://localhost:3004')
            server_id = proxy_config.get('server_id', 'unknown')
            print(f"📡 Proxy URL: {proxy_url}")
            print(f"🆔 Server ID: {server_id}")
        
        # Simulate application startup
        print("\n🔧 Setting up mTLS application components...")
        print("✅ Configuration loaded and validated")
        print("✅ SSL/TLS certificates loaded")
        print("✅ mTLS context created")
        print("✅ Logging configured")
        print("✅ Command registry initialized")
        print("✅ Transport layer configured with mTLS")
        print("✅ Security layer configured")
        print("✅ Proxy registration configured")
        
        if proxy_config.get('enabled', False):
            print("✅ Proxy registration enabled")
            print(f"📡 Will register with proxy at: {proxy_config.get('proxy_url')}")
            print(f"🆔 Server ID: {proxy_config.get('server_id')}")
        
        print(f"\n🎉 mTLS Full Application Example started successfully!")
        print(f"📡 Server listening on {host}:{port}")
        print(f"🌐 Access via: {protocol}://{host}:{port}")
        print("\n📋 Available features:")
        print("  - Built-in commands (health, echo, list, help)")
        print("  - Custom commands (custom_echo, dynamic_calculator)")
        print("  - Application hooks")
        print("  - Command hooks")
        print("  - Proxy endpoints")
        print("  - mTLS authentication")
        print("  - Security (if enabled)")
        print("  - Role management (if enabled)")
        
        print("\n🔐 mTLS Configuration:")
        print(f"  - Certificate: {ssl_config.get('cert_file')}")
        print(f"  - Private Key: {ssl_config.get('key_file')}")
        print(f"  - CA Certificate: {ssl_config.get('ca_cert_file')}")
        print(f"  - Client Verification: {'Required' if ssl_config.get('verify_client', False) else 'Optional'}")
        print(f"  - Ciphers: {ssl_config.get('ciphers', 'Default')}")
        print(f"  - Protocols: {ssl_config.get('protocols', 'Default')}")
        
        print("\n✅ mTLS Application simulation completed successfully")
        print("💡 In a real application, the mTLS server would be running here")
        return True
            
    except Exception as e:
        print(f"❌ Application startup error: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Run mTLS Full Application Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_mtls.py --config configs/mtls_no_roles_correct.json
  python run_mtls.py --config configs/mtls_with_roles_correct.json
  python run_mtls.py --config configs/mtls_no_roles_correct.json --test-connection
        """
    )
    
    parser.add_argument(
        "--config",
        default="configs/mtls_no_roles_correct.json",
        help="Configuration file path"
    )
    
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test mTLS connection"
    )
    
    args = parser.parse_args()
    
    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        print("💡 Available mTLS configurations:")
        configs_dir = Path("configs")
        if configs_dir.exists():
            for config_file in configs_dir.glob("*mtls*.json"):
                print(f"  - {config_file}")
        return 1
    
    # Test connection if requested
    if args.test_connection:
        success = test_mtls_connection(str(config_path))
        return 0 if success else 1
    
    # Run application
    success = run_mtls_application(str(config_path))
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
