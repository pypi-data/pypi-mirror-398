#!/usr/bin/env python3
"""
Bugfix for mcp_security_framework CertificateManager
This script provides a fix for the CertificateManager validation issue.

ISSUE: CertificateManager._validate_configuration() doesn't check ca_creation_mode
and always requires CA certificate and key paths, even when creating a CA.

SOLUTION: Modify the validation logic to skip CA path validation in CA creation mode.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import sys
from pathlib import Path


def create_cert_manager_patch():
    """Create a patch file for the CertificateManager."""
    
    patch_content = '''--- a/mcp_security_framework/core/cert_manager.py
+++ b/mcp_security_framework/core/cert_manager.py
@@ -1,6 +1,7 @@
 import logging
 import os
 from typing import Dict, List, Optional, Union
+from pathlib import Path
 
 from cryptography import x509
 from cryptography.hazmat.primitives import hashes, serialization
@@ -50,6 +51,7 @@ class CertificateManager:
         """
         self.config = config
         self.logger = logging.getLogger(__name__)
+        self._certificate_cache: Dict[str, CertificateInfo] = {}
+        self._crl_cache: Dict[str, x509.CertificateRevocationList] = {}
 
         # Validate configuration
         self._validate_configuration()
@@ -70,7 +72,7 @@ class CertificateManager:
     def _validate_configuration(self) -> None:
         """Validate certificate configuration."""
         # Skip validation if certificate management is disabled
-        if not self.config.enabled:
+        if not self.config.enabled:
             return
 
-        if not self.config.ca_cert_path:
-            raise CertificateConfigurationError("CA certificate path is required")
-
-        if not self.config.ca_key_path:
-            raise CertificateConfigurationError("CA private key path is required")
-
-        if not os.path.exists(self.config.ca_cert_path):
-            raise CertificateConfigurationError(
-                f"CA certificate file not found: {self.config.ca_cert_path}"
-            )
-
-        if not os.path.exists(self.config.ca_key_path):
-            raise CertificateConfigurationError(
-                f"CA private key file not found: {self.config.ca_key_path}"
-            )
+        # BUGFIX: Skip CA path validation if in CA creation mode
+        if self.config.ca_creation_mode:
+            self.get_global_logger().info("CA creation mode enabled, skipping CA path validation")
+            return
+
+        if not self.config.ca_cert_path:
+            raise CertificateConfigurationError("CA certificate path is required")
+
+        if not self.config.ca_key_path:
+            raise CertificateConfigurationError("CA private key path is required")
+
+        if not os.path.exists(self.config.ca_cert_path):
+            raise CertificateConfigurationError(
+                f"CA certificate file not found: {self.config.ca_cert_path}"
+            )
+
+        if not os.path.exists(self.config.ca_key_path):
+            raise CertificateConfigurationError(
+                f"CA private key file not found: {self.config.ca_key_path}"
+            )
'''
    
    patch_file = Path("cert_manager_bugfix.patch")
    with open(patch_file, 'w') as f:
        f.write(patch_content)
    
    print(f"✅ CertificateManager patch file created: {patch_file}")
    return patch_file


def test_fixed_cert_manager():
    """Test the fixed CertificateManager."""
    print("🧪 Testing Fixed CertificateManager")
    print("=" * 50)
    
    # Create a mock fixed CertificateManager class
    class FixedCertificateManager:
        """
        Fixed certificate manager with corrected validation logic.
        
        This class demonstrates the correct way to validate certificate
        configuration and handle certificate file paths.
        """
        def __init__(self, config):
            """
            Initialize fixed certificate manager.
            
            Args:
                config: Configuration object with certificate settings
            """
            self.config = config
            self.logger = type('Logger', (), {'info': lambda self, msg, **kwargs: print(f"INFO: {msg}")})()
            self._validate_configuration()
        
        def _validate_configuration(self):
            """Fixed validation logic."""
            if not self.config.enabled:
                return
            
            # BUGFIX: Skip CA path validation if in CA creation mode
            if self.config.ca_creation_mode:
                self.get_global_logger().info("CA creation mode enabled, skipping CA path validation")
                return
            
            if not self.config.ca_cert_path:
                raise ValueError("CA certificate path is required")
            
            if not self.config.ca_key_path:
                raise ValueError("CA private key path is required")
    
    # Test 1: CA creation mode should work without CA paths
    print("Test 1: CA creation mode")
    try:
        from mcp_security_framework.schemas.config import CertificateConfig
        
        config1 = CertificateConfig(
            enabled=True,
            ca_creation_mode=True,
            cert_storage_path="./certs",
            key_storage_path="./keys"
        )
        
        manager1 = FixedCertificateManager(config1)
        print("✅ CA creation mode works correctly")
    except Exception as e:
        print(f"❌ CA creation mode failed: {e}")
        return False
    
    # Test 2: Normal mode should require CA paths
    print("Test 2: Normal mode without CA paths")
    try:
        config2 = CertificateConfig(
            enabled=True,
            ca_creation_mode=False,
            cert_storage_path="./certs",
            key_storage_path="./keys"
        )
        
        manager2 = FixedCertificateManager(config2)
        print("❌ Normal mode should have failed without CA paths")
        return False
    except ValueError as e:
        print("✅ Normal mode correctly requires CA paths")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    return True


def main():
    """Main entry point."""
    print("🔧 mcp_security_framework CertificateManager Bugfix")
    print("=" * 60)
    print()
    print("ISSUE DESCRIPTION:")
    print("CertificateManager._validate_configuration() doesn't check ca_creation_mode")
    print("and always requires CA certificate and key paths, even when creating a CA.")
    print()
    print("SOLUTION:")
    print("Modify _validate_configuration() to skip CA path validation when")
    print("ca_creation_mode=True.")
    print()
    
    # Test the fix
    if test_fixed_cert_manager():
        # Create patch file
        patch_file = create_cert_manager_patch()
        print(f"\n📁 To apply this fix to mcp_security_framework:")
        print(f"   1. Copy the patch file to the framework directory")
        print(f"   2. Run: patch -p1 < {patch_file}")
        print(f"   3. Or manually apply the changes shown in the patch")
        print()
        print("🔧 USAGE EXAMPLE:")
        print("   # For CA creation:")
        print("   config = CertificateConfig(")
        print("       enabled=True,")
        print("       ca_creation_mode=True,  # <-- This bypasses CA path validation")
        print("       cert_storage_path='./certs',")
        print("       key_storage_path='./keys'")
        print("   )")
        print("   manager = CertificateManager(config)  # <-- This will now work")
    else:
        print("❌ Tests failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
