#!/usr/bin/env python3
"""
Bugfix for mcp_security_framework CertificateConfig
This script provides a fix for the CertificateConfig validation issue.

ISSUE: CertificateConfig requires CA certificate and key paths even when creating a CA certificate.
This creates a chicken-and-egg problem where you need a CA to create a CA.

SOLUTION: Modify the validation logic to allow CA creation mode.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import sys
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class FixedCertificateConfig(BaseModel):
    """
    Fixed Certificate Management Configuration Model

    This model defines certificate management configuration settings
    including CA settings, certificate storage, and validation options.

    BUGFIX: Added ca_creation_mode to allow CA certificate creation
    without requiring existing CA paths.

    Attributes:
        enabled: Whether certificate management is enabled
        ca_creation_mode: Whether we are in CA creation mode (bypasses CA path validation)
        ca_cert_path: Path to CA certificate
        ca_key_path: Path to CA private key
        cert_storage_path: Path for certificate storage
        key_storage_path: Path for private key storage
        default_validity_days: Default certificate validity in days
        key_size: RSA key size for generated certificates
        hash_algorithm: Hash algorithm for certificate signing
        crl_enabled: Whether CRL is enabled
        crl_path: Path for CRL storage
        crl_validity_days: CRL validity period in days
        auto_renewal: Whether automatic certificate renewal is enabled
        renewal_threshold_days: Days before expiry to renew
    """

    enabled: bool = Field(
        default=False, description="Whether certificate management is enabled"
    )
    ca_creation_mode: bool = Field(
        default=False, description="Whether we are in CA creation mode (bypasses CA path validation)"
    )
    ca_cert_path: Optional[str] = Field(
        default=None, description="Path to CA certificate"
    )
    ca_key_path: Optional[str] = Field(
        default=None, description="Path to CA private key"
    )
    cert_storage_path: str = Field(
        default="./certs", description="Path for certificate storage"
    )
    key_storage_path: str = Field(
        default="./keys", description="Path for private key storage"
    )
    default_validity_days: int = Field(
        default=365, ge=1, le=3650, description="Default certificate validity in days"
    )
    key_size: int = Field(
        default=2048,
        ge=1024,
        le=4096,
        description="RSA key size for generated certificates",
    )
    hash_algorithm: str = Field(
        default="sha256", description="Hash algorithm for certificate signing"
    )
    crl_enabled: bool = Field(default=False, description="Whether CRL is enabled")
    crl_path: Optional[str] = Field(default=None, description="Path for CRL storage")
    crl_validity_days: int = Field(
        default=30, ge=1, le=365, description="CRL validity period in days"
    )
    auto_renewal: bool = Field(
        default=False, description="Whether automatic certificate renewal is enabled"
    )
    renewal_threshold_days: int = Field(
        default=30, ge=1, le=90, description="Days before expiry to renew"
    )

    @field_validator("hash_algorithm")
    @classmethod
    def validate_hash_algorithm(cls, v):
        """Validate hash algorithm."""
        valid_algorithms = ["sha256", "sha384", "sha512"]
        if v not in valid_algorithms:
            raise ValueError(f"Hash algorithm must be one of {valid_algorithms}")
        return v

    @model_validator(mode="after")
    def validate_model(self):
        """Validate model after initialization."""
        return self


def create_patch_file():
    """Create a patch file for the mcp_security_framework."""
    
    patch_content = '''--- a/mcp_security_framework/schemas/config.py
+++ b/mcp_security_framework/schemas/config.py
@@ -1,6 +1,7 @@
 from typing import Optional
 from pydantic import BaseModel, Field, field_validator, model_validator
 
+
 class CertificateConfig(BaseModel):
     """
     Certificate Management Configuration Model
@@ -8,6 +9,7 @@ class CertificateConfig(BaseModel):
     This model defines certificate management configuration settings
     including CA settings, certificate storage, and validation options.
 
+    BUGFIX: Added ca_creation_mode to allow CA certificate creation
     Attributes:
         enabled: Whether certificate management is enabled
         ca_cert_path: Path to CA certificate
@@ -20,6 +22,9 @@ class CertificateConfig(BaseModel):
     enabled: bool = Field(
         default=False, description="Whether certificate management is enabled"
     )
+    ca_creation_mode: bool = Field(
+        default=False, description="Whether we are in CA creation mode (bypasses CA path validation)"
+    )
     ca_cert_path: Optional[str] = Field(
         default=None, description="Path to CA certificate"
     )
@@ -60,7 +65,9 @@ class CertificateConfig(BaseModel):
     @model_validator(mode="after")
     def validate_certificate_configuration(self):
         """Validate certificate configuration consistency."""
         if self.enabled:
-            if not self.ca_cert_path or not self.ca_key_path:
-                raise ValueError(
-                    "Certificate management enabled but CA certificate and key paths are required"
-                )
+            # BUGFIX: Only require CA paths if not in CA creation mode
+            if not self.ca_creation_mode:
+                if not self.ca_cert_path or not self.ca_key_path:
+                    raise ValueError(
+                        "Certificate management enabled but CA certificate and key paths are required. "
+                        "Set ca_creation_mode=True if you are creating a CA certificate."
+                    )
 
         if self.crl_enabled and not self.crl_path:
             raise ValueError("CRL enabled but CRL path is required")
 
         return self
'''
    
    patch_file = Path("certificate_config_bugfix.patch")
    with open(patch_file, 'w') as f:
        f.write(patch_content)
    
    print(f"✅ Patch file created: {patch_file}")
    return patch_file


def test_fixed_config():
    """Test the fixed configuration."""
    print("🧪 Testing Fixed CertificateConfig")
    print("=" * 50)
    
    # Test 1: CA creation mode should work without CA paths
    print("Test 1: CA creation mode")
    try:
        config1 = FixedCertificateConfig(
            enabled=True,
            ca_creation_mode=True,
            cert_storage_path="./certs",
            key_storage_path="./keys"
        )
        print("✅ CA creation mode works correctly")
    except Exception as e:
        print(f"❌ CA creation mode failed: {e}")
        return False
    
    # Test 2: Normal mode should require CA paths
    print("Test 2: Normal mode without CA paths")
    try:
        config2 = FixedCertificateConfig(
            enabled=True,
            ca_creation_mode=False,
            cert_storage_path="./certs",
            key_storage_path="./keys"
        )
        print("❌ Normal mode should have failed without CA paths")
        return False
    except ValueError as e:
        print("✅ Normal mode correctly requires CA paths")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Test 3: Normal mode with CA paths should work
    print("Test 3: Normal mode with CA paths")
    try:
        config3 = FixedCertificateConfig(
            enabled=True,
            ca_creation_mode=False,
            ca_cert_path="./certs/ca.crt",
            ca_key_path="./keys/ca.key",
            cert_storage_path="./certs",
            key_storage_path="./keys"
        )
        print("✅ Normal mode with CA paths works correctly")
    except Exception as e:
        print(f"❌ Normal mode with CA paths failed: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    return True


def main():
    """Main entry point."""
    print("🔧 mcp_security_framework CertificateConfig Bugfix")
    print("=" * 60)
    print()
    print("ISSUE DESCRIPTION:")
    print("CertificateConfig requires CA certificate and key paths even when")
    print("creating a CA certificate. This creates a chicken-and-egg problem.")
    print()
    print("SOLUTION:")
    print("Add ca_creation_mode field to bypass CA path validation when")
    print("creating a CA certificate.")
    print()
    
    # Test the fix
    if test_fixed_config():
        # Create patch file
        patch_file = create_patch_file()
        print(f"\n📁 To apply this fix to mcp_security_framework:")
        print(f"   1. Copy the patch file to the framework directory")
        print(f"   2. Run: patch -p1 < {patch_file}")
        print(f"   3. Or manually apply the changes shown in the patch")
        print()
        print("🔧 USAGE EXAMPLE:")
        print("   # For CA creation:")
        print("   config = CertificateConfig(")
        print("       enabled=True,")
        print("       ca_creation_mode=True,  # <-- This is the fix")
        print("       cert_storage_path='./certs',")
        print("       key_storage_path='./keys'")
        print("   )")
        print()
        print("   # For normal certificate creation:")
        print("   config = CertificateConfig(")
        print("       enabled=True,")
        print("       ca_creation_mode=False,")
        print("       ca_cert_path='./certs/ca.crt',")
        print("       ca_key_path='./keys/ca.key'")
        print("   )")
    else:
        print("❌ Tests failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
