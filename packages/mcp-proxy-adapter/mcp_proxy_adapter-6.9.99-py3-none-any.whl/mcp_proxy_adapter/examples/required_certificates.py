#!/usr/bin/env python3
"""
Required Certificates Configuration
Defines all certificates needed for testing different server configurations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""


# Base paths
CERTS_DIR = Path("certs")
KEYS_DIR = Path("keys")

# Required certificates for different server configurations
REQUIRED_CERTIFICATES = {
    # CA Certificate (required for all SSL/mTLS configurations)
    "ca_cert": {
        "type": "ca",
        "common_name": "MCP Proxy Adapter Test CA",
        "organization": "Test Organization",
        "country": "US",
        "state": "Test State",
        "city": "Test City",
        "validity_days": 3650,  # 10 years
        "output_cert": CERTS_DIR / "ca_cert.pem",
        "output_key": KEYS_DIR / "ca_key.pem",
        "required_for": ["https", "mtls", "proxy_registration"]
    },
    
    # Server Certificate for HTTPS configurations
    "server_cert": {
        "type": "server",
        "common_name": "localhost",
        "organization": "Test Organization", 
        "country": "US",
        "state": "Test State",
        "city": "Test City",
        "validity_days": 365,
        "san": ["localhost", "127.0.0.1", "mcp-proxy-adapter-test.local"],
        "ca_cert_path": CERTS_DIR / "ca_cert.pem",
        "ca_key_path": KEYS_DIR / "ca_key.pem",
        "output_cert": CERTS_DIR / "server_cert.pem",
        "output_key": KEYS_DIR / "server_key.pem",
        "required_for": ["https", "mtls"]
    },
    
    # Admin Client Certificate
    "admin_cert": {
        "type": "client",
        "common_name": "admin-client",
        "organization": "Test Organization",
        "country": "US", 
        "state": "Test State",
        "city": "Test City",
        "validity_days": 365,
        "roles": ["admin"],
        "permissions": ["*"],
        "ca_cert_path": CERTS_DIR / "ca_cert.pem",
        "ca_key_path": KEYS_DIR / "ca_key.pem",
        "output_cert": CERTS_DIR / "admin_cert.pem",
        "output_key": KEYS_DIR / "admin_key.pem",
        "required_for": ["mtls", "client_auth"]
    },
    
    # User Client Certificate
    "user_cert": {
        "type": "client",
        "common_name": "user-client",
        "organization": "Test Organization",
        "country": "US",
        "state": "Test State", 
        "city": "Test City",
        "validity_days": 365,
        "roles": ["user"],
        "permissions": ["read", "write"],
        "ca_cert_path": CERTS_DIR / "ca_cert.pem",
        "ca_key_path": KEYS_DIR / "ca_key.pem",
        "output_cert": CERTS_DIR / "user_cert.pem",
        "output_key": KEYS_DIR / "user_key.pem",
        "required_for": ["mtls", "client_auth"]
    },
    
    # Proxy Certificate for proxy registration
    "proxy_cert": {
        "type": "server",
        "common_name": "proxy-server",
        "organization": "Test Organization",
        "country": "US",
        "state": "Test State",
        "city": "Test City", 
        "validity_days": 365,
        "san": ["localhost", "127.0.0.1"],
        "ca_cert_path": CERTS_DIR / "ca_cert.pem",
        "ca_key_path": KEYS_DIR / "ca_key.pem",
        "output_cert": CERTS_DIR / "proxy_cert.pem",
        "output_key": KEYS_DIR / "proxy_key.pem",
        "required_for": ["proxy_registration"]
    }
}

# Certificate aliases for different configurations
CERTIFICATE_ALIASES = {
    # HTTPS configurations
    "https_server_cert": "server_cert",
    "https_server_key": "server_cert", 
    
    # mTLS configurations
    "mtls_server_cert": "server_cert",
    "mtls_server_key": "server_cert",
    "mtls_ca_cert": "ca_cert",
    
    # Proxy registration
    "proxy_server_cert": "proxy_cert",
    "proxy_server_key": "proxy_cert",
    
    # Legacy names for compatibility
    "localhost_server_cert": "server_cert",
    "mcp_proxy_adapter_server_cert": "server_cert",
    "mcp_proxy_adapter_ca_cert": "ca_cert"
}

# Configuration file mappings
CONFIG_CERTIFICATE_MAPPINGS = {
    "https_simple.json": {
        "ssl.cert_file": "certs/server_cert.pem",
        "ssl.key_file": "keys/server_key.pem",
        "ssl.ca_cert": "certs/ca_cert.pem"
    },
    "https_auth.json": {
        "ssl.cert_file": "certs/server_cert.pem", 
        "ssl.key_file": "keys/server_key.pem",
        "ssl.ca_cert": "certs/ca_cert.pem"
    },
    "https_token.json": {
        "ssl.cert_file": "certs/server_cert.pem",
        "ssl.key_file": "keys/server_key.pem", 
        "ssl.ca_cert": "certs/ca_cert.pem"
    },
    "mtls_simple.json": {
        "ssl.cert_file": "certs/server_cert.pem",
        "ssl.key_file": "keys/server_key.pem",
        "ssl.ca_cert": "certs/ca_cert.pem",
        "ssl.client_cert_file": "certs/admin_cert.pem",
        "ssl.client_key_file": "keys/admin_key.pem"
    },
    "mtls_no_roles.json": {
        "ssl.cert_file": "certs/server_cert.pem",
        "ssl.key_file": "keys/server_key.pem",
        "ssl.ca_cert": "certs/ca_cert.pem"
    },
    "mtls_with_roles.json": {
        "ssl.cert_file": "certs/server_cert.pem",
        "ssl.key_file": "keys/server_key.pem",
        "ssl.ca_cert": "certs/ca_cert.pem",
        "ssl.client_cert_file": "certs/admin_cert.pem", 
        "ssl.client_key_file": "keys/admin_key.pem"
    },
    "mtls_with_proxy.json": {
        "ssl.cert_file": "certs/server_cert.pem",
        "ssl.key_file": "keys/server_key.pem",
        "ssl.ca_cert": "certs/ca_cert.pem",
        "ssl.client_cert_file": "certs/admin_cert.pem",
        "ssl.client_key_file": "keys/admin_key.pem",
        "proxy_registration.ssl.ca_cert": "certs/ca_cert.pem"
    }
}

def get_required_certificates_for_config(config_name: str) -> List[str]:
    """Get list of required certificates for a specific configuration."""
    if config_name not in CONFIG_CERTIFICATE_MAPPINGS:
        return []
    
    required = []
    mappings = CONFIG_CERTIFICATE_MAPPINGS[config_name]
    
    for cert_path in mappings.values():
        if "server_cert.pem" in cert_path:
            required.append("server_cert")
        elif "ca_cert.pem" in cert_path:
            required.append("ca_cert")
        elif "admin_cert.pem" in cert_path:
            required.append("admin_cert")
        elif "proxy_cert.pem" in cert_path:
            required.append("proxy_cert")
    
    return list(set(required))

def get_all_required_certificates() -> List[str]:
    """Get list of all required certificates."""
    all_certs = set()
    for config_name in CONFIG_CERTIFICATE_MAPPINGS.keys():
        all_certs.update(get_required_certificates_for_config(config_name))
    return list(all_certs)

if __name__ == "__main__":
    print("📋 Required Certificates Configuration")
    print("=" * 50)
    
    all_required = get_all_required_certificates()
    print(f"Total certificates needed: {len(all_required)}")
    print(f"Certificates: {', '.join(all_required)}")
    
    print(f"\n📁 Certificate files to create:")
    for cert_name in all_required:
        cert_info = REQUIRED_CERTIFICATES[cert_name]
        print(f"  {cert_info['output_cert']}")
        print(f"  {cert_info['output_key']}")
