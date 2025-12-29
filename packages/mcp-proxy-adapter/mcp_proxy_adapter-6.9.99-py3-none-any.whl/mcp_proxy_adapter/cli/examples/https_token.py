#!/usr/bin/env python3
"""
HTTPS Token Configuration Example

This example demonstrates how to generate and use an HTTPS configuration with token authentication.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import sys
import json
from pathlib import Path


def main():
    """Generate and test HTTPS token configuration."""
    print("🔧 HTTPS Token Configuration Example")
    print("=" * 50)
    
    # Generate HTTPS configuration with token authentication
    print("1. Generating HTTPS configuration with token authentication...")
    result = subprocess.run([
        sys.executable, "-m", "mcp_proxy_adapter.cli.main",
        "sets", "https",
        "--token",
        "--roles",
        "--port", "8443",
        "--output-dir", "./examples_configs"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error generating configuration: {result.stderr}")
        return 1
    
    print("✅ HTTPS configuration with token authentication generated")
    
    # Find the generated config file
    config_dir = Path("./examples_configs")
    config_files = list(config_dir.glob("https_token_roles*.json"))
    
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
    print(f"   Security: {'Enabled' if config.get('security', {}).get('enabled') else 'Disabled'}")
    print(f"   Token Auth: {'Enabled' if config.get('security', {}).get('tokens') else 'Disabled'}")
    print(f"   Roles: {'Enabled' if config.get('roles', {}).get('enabled') else 'Disabled'}")
    
    # Show available tokens
    if config.get('security', {}).get('tokens'):
        print("\n4. Available authentication tokens:")
        for role, token in config['security']['tokens'].items():
            print(f"   {role}: {token}")
    
    print("\n🎉 HTTPS token configuration example completed!")
    print(f"📁 Configuration saved to: {config_file}")
    print("\n💡 To start the server:")
    print(f"   mcp-proxy-adapter server --config {config_file}")
    print("\n💡 To test with curl:")
    print(f"   curl -k https://localhost:8443/health")
    print(f"   curl -k -H 'X-API-Key: admin-secret-key' https://localhost:8443/api/jsonrpc -d '{{\"jsonrpc\":\"2.0\",\"method\":\"echo\",\"params\":{{\"message\":\"Hello\"}},\"id\":1}}'")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
