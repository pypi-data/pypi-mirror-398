#!/usr/bin/env python3
"""
Test script to reproduce the Docker logging issue.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("Testing logging import...")
    from mcp_proxy_adapter.core.logging import logger
    print("✅ Logger import successful")
    print(f"Logger type: {type(logger)}")
    print(f"Logger value: {logger}")
except Exception as e:
    print(f"❌ Logger import failed: {e}")
    print(f"Exception type: {type(e)}")
    import traceback
    traceback.print_exc()

try:
    print("\nTesting get_global_logger...")
    from mcp_proxy_adapter.core.logging import get_global_logger
    logger2 = get_global_logger()
    print("✅ get_global_logger successful")
    print(f"Logger type: {type(logger2)}")
    print(f"Logger value: {logger2}")
except Exception as e:
    print(f"❌ get_global_logger failed: {e}")
    print(f"Exception type: {type(e)}")
    import traceback
    traceback.print_exc()
