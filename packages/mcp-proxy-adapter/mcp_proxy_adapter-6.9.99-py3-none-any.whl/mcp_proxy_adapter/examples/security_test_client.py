#!/usr/bin/env python3
"""
Security Test Client for MCP Proxy Adapter
This client tests various security configurations including:
- Basic HTTP
- HTTP + Token authentication
- HTTPS
- HTTPS + Token authentication
- mTLS with certificate authentication

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if parent_dir.exists():
    sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir))

# Import mcp_security_framework components
try:
    _MCP_SECURITY_AVAILABLE = True
    print("✅ mcp_security_framework available")
except ImportError as e:
    print(f"❌ CRITICAL ERROR: mcp_security_framework is required but not available!")
    print(f"❌ Import error: {e}")
    print("❌ Please install mcp_security_framework: pip install mcp_security_framework")
    raise ImportError("mcp_security_framework is required for security tests") from e

# Import cryptography components
try:
    _CRYPTOGRAPHY_AVAILABLE = True
    print("✅ cryptography available")
except ImportError:
    _CRYPTOGRAPHY_AVAILABLE = False
    print("⚠️ cryptography not available, SSL validation will be limited")

# Import security test components
from .security_test import SecurityTestClient


async def main():
    """Main function to run security tests."""
    print("🚀 Starting MCP Proxy Adapter Security Tests")
    print("=" * 50)
    
    # Define test servers
    test_servers = [
        "http://localhost:8080",      # HTTP Basic
        "http://localhost:8080",      # HTTP + Token
        "https://localhost:8443",     # HTTPS Basic
        "https://localhost:8443",     # HTTPS + Token
        "https://localhost:20006",    # mTLS Basic
        "https://localhost:20007",    # mTLS + Token
        "https://localhost:20008",    # mTLS + Roles
    ]
    
    # Run security tests
    async with SecurityTestClient() as client:
        results = await client.run_security_tests(test_servers)
        client.print_summary()
    
    print("\\n🎉 Security tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
