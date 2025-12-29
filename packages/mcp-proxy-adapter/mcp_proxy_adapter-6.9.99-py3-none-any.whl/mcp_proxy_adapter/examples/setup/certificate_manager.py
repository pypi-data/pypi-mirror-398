"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Certificate manager for MCP Proxy Adapter test environment setup.
"""

import os
import subprocess
from pathlib import Path
from typing import bool


def generate_certificates_with_framework(output_dir: Path) -> bool:
    """
    Generate certificates using mcp_security_framework if available.

    Args:
        output_dir: Directory to generate certificates in

    Returns:
        True if certificates were generated successfully, False otherwise
    """
    try:
        from mcp_security_framework.core.cert_manager import CertificateManager
        from mcp_security_framework.schemas.config import (
            CertificateConfig,
            CAConfig,
            ServerCertConfig,
            ClientCertConfig,
        )

        print("🔐 Generating certificates using mcp_security_framework...")

        # Create certificate directories
        certs_dir = output_dir / "certs"
        keys_dir = output_dir / "keys"
        certs_dir.mkdir(parents=True, exist_ok=True)
        keys_dir.mkdir(parents=True, exist_ok=True)

        # Initialize certificate manager
        cert_manager = CertificateManager()

        # Generate CA certificate
        ca_config = CAConfig(
            common_name="MCP Test CA",
            country="US",
            state="Test State",
            city="Test City",
            organization="MCP Test Org",
            organizational_unit="Test Unit",
            validity_days=365
        )

        ca_cert_path = certs_dir / "ca_cert.pem"
        ca_key_path = keys_dir / "ca_key.pem"

        print("📜 Generating CA certificate...")
        cert_manager.generate_ca_certificate(
            ca_config,
            str(ca_cert_path),
            str(ca_key_path)
        )

        # Generate server certificate
        server_config = ServerCertConfig(
            common_name="localhost",
            san_dns=["localhost", "127.0.0.1"],
            san_ip=["127.0.0.1", "::1"],
            validity_days=365
        )

        server_cert_path = certs_dir / "localhost_server.crt"
        server_key_path = keys_dir / "server_key.pem"

        print("🖥️ Generating server certificate...")
        cert_manager.generate_server_certificate(
            server_config,
            str(server_cert_path),
            str(server_key_path),
            str(ca_cert_path),
            str(ca_key_path)
        )

        # Generate client certificate
        client_config = ClientCertConfig(
            common_name="test-client",
            validity_days=365
        )

        client_cert_path = certs_dir / "client_cert.pem"
        client_key_path = keys_dir / "client_key.pem"

        print("👤 Generating client certificate...")
        cert_manager.generate_client_certificate(
            client_config,
            str(client_cert_path),
            str(client_key_path),
            str(ca_cert_path),
            str(ca_key_path)
        )

        print("✅ Certificates generated successfully!")
        print(f"   CA Certificate: {ca_cert_path}")
        print(f"   Server Certificate: {server_cert_path}")
        print(f"   Client Certificate: {client_cert_path}")

        return True

    except ImportError:
        print("⚠️ mcp_security_framework not available, using OpenSSL fallback...")
        return _generate_certificates_with_openssl(output_dir)
    except Exception as e:
        print(f"❌ Error generating certificates with framework: {e}")
        print("🔄 Falling back to OpenSSL...")
        return _generate_certificates_with_openssl(output_dir)


def _generate_certificates_with_openssl(output_dir: Path) -> bool:
    """
    Generate certificates using OpenSSL as fallback.

    Args:
        output_dir: Directory to generate certificates in

    Returns:
        True if certificates were generated successfully, False otherwise
    """
    try:
        print("🔐 Generating certificates using OpenSSL...")

        # Create certificate directories
        certs_dir = output_dir / "certs"
        keys_dir = output_dir / "keys"
        certs_dir.mkdir(parents=True, exist_ok=True)
        keys_dir.mkdir(parents=True, exist_ok=True)

        # Generate CA private key
        ca_key_path = keys_dir / "ca_key.pem"
        subprocess.run([
            "openssl", "genrsa", "-out", str(ca_key_path), "2048"
        ], check=True)

        # Generate CA certificate
        ca_cert_path = certs_dir / "ca_cert.pem"
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-key", str(ca_key_path),
            "-out", str(ca_cert_path), "-days", "365",
            "-subj", "/C=US/ST=Test/L=Test/O=Test/OU=Test/CN=MCP Test CA"
        ], check=True)

        # Generate server private key
        server_key_path = keys_dir / "server_key.pem"
        subprocess.run([
            "openssl", "genrsa", "-out", str(server_key_path), "2048"
        ], check=True)

        # Generate server certificate request
        server_csr_path = certs_dir / "server.csr"
        subprocess.run([
            "openssl", "req", "-new", "-key", str(server_key_path),
            "-out", str(server_csr_path),
            "-subj", "/C=US/ST=Test/L=Test/O=Test/OU=Test/CN=localhost"
        ], check=True)

        # Generate server certificate
        server_cert_path = certs_dir / "localhost_server.crt"
        subprocess.run([
            "openssl", "x509", "-req", "-in", str(server_csr_path),
            "-CA", str(ca_cert_path), "-CAkey", str(ca_key_path),
            "-out", str(server_cert_path), "-days", "365",
            "-CAcreateserial"
        ], check=True)

        # Generate client private key
        client_key_path = keys_dir / "client_key.pem"
        subprocess.run([
            "openssl", "genrsa", "-out", str(client_key_path), "2048"
        ], check=True)

        # Generate client certificate request
        client_csr_path = certs_dir / "client.csr"
        subprocess.run([
            "openssl", "req", "-new", "-key", str(client_key_path),
            "-out", str(client_csr_path),
            "-subj", "/C=US/ST=Test/L=Test/O=Test/OU=Test/CN=test-client"
        ], check=True)

        # Generate client certificate
        client_cert_path = certs_dir / "client_cert.pem"
        subprocess.run([
            "openssl", "x509", "-req", "-in", str(client_csr_path),
            "-CA", str(ca_cert_path), "-CAkey", str(ca_key_path),
            "-out", str(client_cert_path), "-days", "365"
        ], check=True)

        # Clean up CSR files
        server_csr_path.unlink(missing_ok=True)
        client_csr_path.unlink(missing_ok=True)

        print("✅ Certificates generated successfully with OpenSSL!")
        print(f"   CA Certificate: {ca_cert_path}")
        print(f"   Server Certificate: {server_cert_path}")
        print(f"   Client Certificate: {client_cert_path}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ OpenSSL command failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ OpenSSL not found. Please install OpenSSL or mcp_security_framework")
        return False
    except Exception as e:
        print(f"❌ Error generating certificates with OpenSSL: {e}")
        return False
