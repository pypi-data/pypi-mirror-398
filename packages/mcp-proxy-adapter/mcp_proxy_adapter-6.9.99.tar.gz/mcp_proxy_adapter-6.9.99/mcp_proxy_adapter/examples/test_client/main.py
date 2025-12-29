#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Test Client for MCP Proxy Adapter Framework

This client demonstrates how to use JsonRpcClient to connect to MCP Proxy Adapter servers
with different security modes:
- HTTP Basic (no authentication)
- HTTP + Token
- HTTP + Token + Roles
- HTTPS Basic
- HTTPS + Token
- HTTPS + Token + Roles
- mTLS Basic
- mTLS + Roles

Usage:
    # Make sure test server is running, then:
    python -m mcp_proxy_adapter.examples.test_client.main --mode http_basic
    python -m mcp_proxy_adapter.examples.test_client.main --mode http_token --token your-token
    python -m mcp_proxy_adapter.examples.test_client.main --mode https_basic
    python -m mcp_proxy_adapter.examples.test_client.main --mode mtls
"""
import argparse
import asyncio
import json
from pathlib import Path
from typing import Optional

from mcp_proxy_adapter.client.jsonrpc_client.client import JsonRpcClient


async def test_http_basic(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Test HTTP Basic connection (no authentication)."""
    print("\n" + "=" * 60)
    print("🔍 Testing HTTP Basic Connection")
    print("=" * 60)
    
    client = JsonRpcClient(
        protocol="http",
        host=host,
        port=port,
        check_hostname=False,
    )
    
    try:
        # Health check
        print("\n1. Health check:")
        health = await client.health()
        print(f"   ✅ Health: {json.dumps(health, indent=2)}")
        
        # Echo command
        print("\n2. Echo command:")
        result = await client.echo("Hello from test client!")
        print(f"   ✅ Echo result: {json.dumps(result, indent=2)}")
        
        # Get methods
        print("\n3. Get available methods:")
        methods = await client.get_methods()
        print(f"   ✅ Found {len(methods)} methods: {', '.join(list(methods.keys())[:10])}...")
        
        # Get method description
        print("\n4. Get method description (echo):")
        desc = await client.get_method_description("echo")
        print(f"   ✅ Description: {json.dumps(desc, indent=2)[:200]}...")
        
        # Help command
        print("\n5. Help command:")
        help_result = await client.help()
        commands = help_result.get("data", {}).get("commands", [])
        print(f"   ✅ Available commands: {len(commands)}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        await client.close()


async def test_http_token(
    host: str = "127.0.0.1",
    port: int = 8080,
    token: str = "admin-secret-key",
    token_header: str = "X-API-Key",
) -> None:
    """Test HTTP connection with token authentication."""
    print("\n" + "=" * 60)
    print("🔍 Testing HTTP + Token Connection")
    print("=" * 60)
    
    client = JsonRpcClient(
        protocol="http",
        host=host,
        port=port,
        token_header=token_header,
        token=token,
        check_hostname=False,
    )
    
    try:
        # Health check
        print("\n1. Health check:")
        health = await client.health()
        print(f"   ✅ Health: {json.dumps(health, indent=2)}")
        
        # Echo command
        print("\n2. Echo command:")
        result = await client.echo("Hello from authenticated client!")
        print(f"   ✅ Echo result: {json.dumps(result, indent=2)}")
        
        # Get methods
        print("\n3. Get available methods:")
        methods = await client.get_methods()
        print(f"   ✅ Found {len(methods)} methods")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        await client.close()


async def test_https_basic(host: str = "127.0.0.1", port: int = 8443) -> None:
    """Test HTTPS Basic connection (no authentication)."""
    print("\n" + "=" * 60)
    print("🔍 Testing HTTPS Basic Connection")
    print("=" * 60)
    
    client = JsonRpcClient(
        protocol="https",
        host=host,
        port=port,
        check_hostname=False,
    )
    
    try:
        # Health check
        print("\n1. Health check:")
        health = await client.health()
        print(f"   ✅ Health: {json.dumps(health, indent=2)}")
        
        # Echo command
        print("\n2. Echo command:")
        result = await client.echo("Hello from HTTPS client!")
        print(f"   ✅ Echo result: {json.dumps(result, indent=2)}")
        
        # Get methods
        print("\n3. Get available methods:")
        methods = await client.get_methods()
        print(f"   ✅ Found {len(methods)} methods")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        await client.close()


async def test_https_token(
    host: str = "127.0.0.1",
    port: int = 8443,
    token: str = "admin-secret-key-https",
    token_header: str = "X-API-Key",
) -> None:
    """Test HTTPS connection with token authentication."""
    print("\n" + "=" * 60)
    print("🔍 Testing HTTPS + Token Connection")
    print("=" * 60)
    
    client = JsonRpcClient(
        protocol="https",
        host=host,
        port=port,
        token_header=token_header,
        token=token,
        check_hostname=False,
    )
    
    try:
        # Health check
        print("\n1. Health check:")
        health = await client.health()
        print(f"   ✅ Health: {json.dumps(health, indent=2)}")
        
        # Echo command
        print("\n2. Echo command:")
        result = await client.echo("Hello from authenticated HTTPS client!")
        print(f"   ✅ Echo result: {json.dumps(result, indent=2)}")
        
        # Get methods
        print("\n3. Get available methods:")
        methods = await client.get_methods()
        print(f"   ✅ Found {len(methods)} methods")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        await client.close()


async def test_mtls(
    host: str = "127.0.0.1",
    port: int = 8443,
    token: Optional[str] = "admin-secret-key-mtls",
    token_header: str = "X-API-Key",
    cert: str = "mtls_certificates/client/test-client.crt",
    key: str = "mtls_certificates/client/test-client.key",
    ca: str = "mtls_certificates/ca/ca.crt",
) -> None:
    """Test mTLS connection with client certificates."""
    print("\n" + "=" * 60)
    print("🔍 Testing mTLS Connection")
    print("=" * 60)
    
    # Check if certificate files exist
    cert_path = Path(cert)
    key_path = Path(key)
    ca_path = Path(ca)
    
    if not cert_path.exists():
        print(f"   ❌ Certificate file not found: {cert}")
        return
    if not key_path.exists():
        print(f"   ❌ Key file not found: {key}")
        return
    if not ca_path.exists():
        print(f"   ❌ CA file not found: {ca}")
        return
    
    client = JsonRpcClient(
        protocol="https",
        host=host,
        port=port,
        token_header=token_header if token else None,
        token=token,
        cert=str(cert_path),
        key=str(key_path),
        ca=str(ca_path),
        check_hostname=False,
    )
    
    try:
        # Health check
        print("\n1. Health check:")
        health = await client.health()
        print(f"   ✅ Health: {json.dumps(health, indent=2)}")
        
        # Echo command
        print("\n2. Echo command:")
        result = await client.echo("Hello from mTLS client!")
        print(f"   ✅ Echo result: {json.dumps(result, indent=2)}")
        
        # Get methods
        print("\n3. Get available methods:")
        methods = await client.get_methods()
        print(f"   ✅ Found {len(methods)} methods")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        await client.close()


async def main() -> None:
    """Main entry point for test client."""
    parser = argparse.ArgumentParser(
        description="Test client for MCP Proxy Adapter framework"
    )
    parser.add_argument(
        "--mode",
        choices=[
            "http_basic",
            "http_token",
            "http_token_roles",
            "https_basic",
            "https_token",
            "https_token_roles",
            "mtls",
            "mtls_roles",
        ],
        default="http_basic",
        help="Security mode to test",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server hostname (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Server port (default: 8080 for HTTP, 8443 for HTTPS/mTLS)",
    )
    parser.add_argument(
        "--token",
        help="Authentication token",
    )
    parser.add_argument(
        "--token-header",
        default="X-API-Key",
        help="Token header name (default: X-API-Key)",
    )
    parser.add_argument(
        "--cert",
        default="mtls_certificates/client/test-client.crt",
        help="Client certificate file for mTLS",
    )
    parser.add_argument(
        "--key",
        default="mtls_certificates/client/test-client.key",
        help="Client private key file for mTLS",
    )
    parser.add_argument(
        "--ca",
        default="mtls_certificates/ca/ca.crt",
        help="CA certificate file for mTLS",
    )
    
    args = parser.parse_args()
    
    # Determine default port based on mode
    if args.port is None:
        if args.mode.startswith("http"):
            args.port = 8080
        else:
            args.port = 8443
    
    # Determine default token based on mode
    if args.token is None:
        if args.mode in ("http_token", "http_token_roles"):
            args.token = "admin-secret-key"
        elif args.mode in ("https_token", "https_token_roles"):
            args.token = "admin-secret-key-https"
        elif args.mode in ("mtls", "mtls_roles"):
            args.token = "admin-secret-key-mtls"
    
    print("🚀 MCP Proxy Adapter Test Client")
    print(f"📡 Mode: {args.mode}")
    print(f"🌐 Host: {args.host}:{args.port}")
    
    # Run appropriate test
    if args.mode == "http_basic":
        await test_http_basic(args.host, args.port)
    elif args.mode in ("http_token", "http_token_roles"):
        await test_http_token(args.host, args.port, args.token, args.token_header)
    elif args.mode == "https_basic":
        await test_https_basic(args.host, args.port)
    elif args.mode in ("https_token", "https_token_roles"):
        await test_https_token(args.host, args.port, args.token, args.token_header)
    elif args.mode in ("mtls", "mtls_roles"):
        await test_mtls(
            args.host,
            args.port,
            args.token,
            args.token_header,
            args.cert,
            args.key,
            args.ca,
        )
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

