#!/usr/bin/env python3
"""
HTTP Basic Configuration Example

This example demonstrates how to generate and use a basic HTTP configuration.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import sys
import json
from pathlib import Path


def main():
    """Generate and test HTTP basic configuration."""
    print("🔧 HTTP Basic Configuration Example")
    print("=" * 50)
    
    # Generate HTTP configuration
    print("1. Generating HTTP configuration...")
    result = subprocess.run([
        sys.executable, "-m", "mcp_proxy_adapter.cli.main",
        "sets", "http",
        "--port", "8080",
        "--output-dir", "./examples_configs"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error generating configuration: {result.stderr}")
        return 1
    
    print("✅ HTTP configuration generated")
    
    # Find the generated config file
    config_dir = Path("./examples_configs")
    config_files = list(config_dir.glob("http*.json"))
    
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
    print(f"   Security: {'Enabled' if config.get('security', {}).get('enabled') else 'Disabled'}")
    
    print("\n🎉 HTTP basic configuration example completed!")
    print(f"📁 Configuration saved to: {config_file}")
    print("\n💡 To start the server:")
    print(f"   mcp-proxy-adapter server --config {config_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
