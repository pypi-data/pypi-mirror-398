"""
Direct import tests to avoid circular import issues.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any

# Import modules directly to avoid circular imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_proxy_adapter.core.config_validator import ConfigValidator
from mcp_proxy_adapter.core.errors import ConfigError
from mcp_proxy_adapter.core.validation.validation_result import ValidationResult


class TestDirectImport(unittest.TestCase):
    """Test validation functionality with direct imports."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = ConfigValidator()
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ssl_validation_basic(self):
        """Test basic SSL validation."""
        config_data = {
            "ssl": {
                "enabled": True,
                "cert_file": None,
                "key_file": None,
                "ca_cert": None
            }
        }
        
        results = self.validator.validate_config(config_data)
        
        # Should have errors about missing SSL files
        errors = [r for r in results if r.level == "error"]
        ssl_errors = [e for e in errors if "SSL" in e.message]
        
        self.assertGreater(len(ssl_errors), 0, "Should have SSL errors")
        print("✅ SSL validation works correctly")
    
    def test_validation_summary(self):
        """Test validation summary."""
        config_data = {
            "ssl": {
                "enabled": True,
                "cert_file": None,
                "key_file": None,
                "ca_cert": None
            }
        }
        
        results = self.validator.validate_config(config_data)
        summary = self.validator.get_validation_summary()
        
        self.assertIn("total_issues", summary)
        self.assertIn("errors", summary)
        self.assertIn("warnings", summary)
        self.assertIn("info", summary)
        self.assertIn("is_valid", summary)
        
        print("✅ Validation summary works correctly")


if __name__ == '__main__':
    print("🧪 Running Direct Import Tests")
    print("=" * 50)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 50)
    print("✅ All direct import tests completed!")
