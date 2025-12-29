#!/usr/bin/env python3
"""
Simple compatibility test between config generator and validator.
Tests only the structure and required fields, not file existence or certificate validity.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_proxy_adapter.core.config_validator import ConfigValidator
from mcp_proxy_adapter.examples.config_builder import generate_complete_config


def main():
    """Main function to run compatibility tests."""
    tests = []
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  💥 Test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 FINAL RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Generator and validator are structurally compatible.")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
