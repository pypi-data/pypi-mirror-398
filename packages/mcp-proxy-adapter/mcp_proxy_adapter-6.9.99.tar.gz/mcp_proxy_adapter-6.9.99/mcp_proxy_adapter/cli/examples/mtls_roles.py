#!/usr/bin/env python3
"""
mTLS Roles Configuration Example

This example demonstrates how to generate and use an mTLS configuration with role-based access control.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import sys
import json
from pathlib import Path


def main():
    """Generate and test mTLS roles configuration."""
    print("🔧 mTLS Roles Configuration Example")
    print("=" * 50)
    
    # Generate mTLS configuration with roles
    print("1. Generating mTLS configuration with roles...")
    result = subprocess.run([
        sys.executable, "-m", "mcp_proxy_adapter.cli.main",
        "sets", "mtls",
        "--roles",
        "--port", "8443",
        "--output-dir", "./examples_configs"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error generating configuration: {result.stderr}")
        return 1
    
    print("✅ mTLS configuration with roles generated")
    
    # Find the generated config file
    config_dir = Path("./examples_configs")
    config_files = list(config_dir.glob("mtls_roles*.json"))
    
    if not config_files:
        print("❌ No configuration files found")
        return 1
    
    config_file = config_files[0]
    print(f"📁 Configuration file: {config_file}")
    
    # Test the configuration
    print("\n2. Testing configuration...")
    result = subprocess.run([
        sys.executable, "-m", "mcp_proxy_adapter.cli.main",
        "testconfig",
        "--config", str(config_file),
        "--verbose"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Configuration validation failed: {result.stderr}")
        return 1
    
    print("✅ Configuration validation passed")
    
    # Show configuration content
    print("\n3. Configuration content:")
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    print(f"   Protocol: {config['server']['protocol']}")
    print(f"   Host: {config['server']['host']}")
    print(f"   Port: {config['server']['port']}")
    print(f"   SSL: {'Enabled' if config.get('ssl', {}).get('enabled') else 'Disabled'}")
    print(f"   Client Verification: {'Enabled' if config.get('transport', {}).get('verify_client') else 'Disabled'}")
    print(f"   Roles: {'Enabled' if config.get('roles', {}).get('enabled') else 'Disabled'}")
    
    # Show SSL configuration
    if config.get('ssl'):
        ssl_config = config['ssl']
        print(f"\n4. SSL Configuration:")
        print(f"   Certificate: {ssl_config.get('cert_file', 'Not set')}")
        print(f"   Private Key: {ssl_config.get('key_file', 'Not set')}")
        print(f"   CA Certificate: {ssl_config.get('ca_cert', 'Not set')}")
    
    # Show roles configuration
    if config.get('roles', {}).get('enabled'):
        print(f"\n5. Roles Configuration:")
        print(f"   Config File: {config['roles'].get('config_file', 'Not set')}")
        print(f"   Auto Load: {config['roles'].get('auto_load', False)}")
        print(f"   Validation: {'Enabled' if config['roles'].get('validation_enabled') else 'Disabled'}")
    
    print("\n🎉 mTLS roles configuration example completed!")
    print(f"📁 Configuration saved to: {config_file}")
    print("\n💡 To start the server:")
    print(f"   mcp-proxy-adapter server --config {config_file}")
    print("\n💡 To test with curl (requires client certificates):")
    print(f"   curl -k --cert client.crt --key client.key https://localhost:8443/health")
    print(f"   curl -k --cert client.crt --key client.key https://localhost:8443/api/jsonrpc -d '{{\"jsonrpc\":\"2.0\",\"method\":\"echo\",\"params\":{{\"message\":\"Hello mTLS\"}},\"id\":1}}'")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
