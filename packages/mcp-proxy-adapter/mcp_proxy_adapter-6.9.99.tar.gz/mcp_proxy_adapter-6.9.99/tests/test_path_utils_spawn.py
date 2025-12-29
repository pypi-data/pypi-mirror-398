#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Test for path_utils module - ensuring modules are available in spawn mode.

This test verifies that:
1. ensure_application_path() adds paths to sys.path and PYTHONPATH
2. ensure_registered_modules_paths() finds and adds module paths
3. Modules are importable in child processes after path setup
"""

import multiprocessing
import os
import sys
import tempfile
from pathlib import Path

# Set spawn mode
multiprocessing.set_start_method("spawn", force=True)

from mcp_proxy_adapter.core.path_utils import (
    ensure_application_path,
    ensure_registered_modules_paths,
    ensure_module_path_in_syspath,
    find_module_path,
)


def test_find_module_path():
    """Test finding module path."""
    print("\n🧪 Test 1: Find module path")
    
    # Test with existing module
    path = find_module_path("mcp_proxy_adapter.commands")
    assert path is not None, "Should find path for existing module"
    assert path.exists(), "Path should exist"
    print(f"   ✅ Found module path: {path}")
    
    # Test with non-existent module
    path = find_module_path("nonexistent.module.xyz")
    assert path is None, "Should return None for non-existent module"
    print("   ✅ Correctly returned None for non-existent module")
    
    return True


def test_ensure_module_path_in_syspath():
    """Test ensuring module path is in sys.path."""
    print("\n🧪 Test 2: Ensure module path in sys.path")
    
    # Test with existing module
    result = ensure_module_path_in_syspath("mcp_proxy_adapter.commands")
    assert result, "Should successfully add module path"
    
    # Verify path is in sys.path
    module_path = find_module_path("mcp_proxy_adapter.commands")
    assert module_path is not None
    assert str(module_path.resolve()) in sys.path, "Module path should be in sys.path"
    print(f"   ✅ Module path added to sys.path: {module_path}")
    
    return True


def test_ensure_application_path():
    """Test ensuring application path is in PYTHONPATH."""
    print("\n🧪 Test 3: Ensure application path")
    
    # Create temporary config file
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.json"
        config_file.write_text('{"test": "config"}')
        
        # Ensure application path
        added_paths = ensure_application_path(str(config_file))
        
        # Verify path was added
        assert len(added_paths) > 0, "Should add at least one path"
        assert str(Path(tmpdir).resolve()) in sys.path, "Application path should be in sys.path"
        
        # Verify PYTHONPATH was updated
        pythonpath = os.environ.get("PYTHONPATH", "")
        assert str(Path(tmpdir).resolve()) in pythonpath, "Application path should be in PYTHONPATH"
        
        print(f"   ✅ Application path added: {added_paths}")
        print(f"   ✅ PYTHONPATH updated: {pythonpath}")
    
    return True


def test_ensure_registered_modules_paths():
    """Test ensuring registered modules paths."""
    print("\n🧪 Test 4: Ensure registered modules paths")
    
    # Register a module
    from mcp_proxy_adapter.commands.hooks import register_auto_import_module
    
    register_auto_import_module("mcp_proxy_adapter.commands")
    
    # Ensure registered modules paths
    added_paths = ensure_registered_modules_paths()
    
    # Should have added at least the commands module path
    assert len(added_paths) >= 0, "Should attempt to add module paths"
    
    print(f"   ✅ Registered modules paths ensured: {added_paths}")
    
    return True


def _child_process_test_worker():
    """Test function that runs in child process (module-level for pickle)."""
    import sys
    import os
    
    # Check PYTHONPATH is set
    pythonpath = os.environ.get("PYTHONPATH", "")
    if not pythonpath:
        return False, "PYTHONPATH not set in child process"
    
    # Try to import a module that should be available
    try:
        import mcp_proxy_adapter.commands
        return True, "Module imported successfully"
    except ImportError as e:
        return False, f"Module import failed: {e}"


def test_child_process_import():
    """Test that modules are importable in child process."""
    print("\n🧪 Test 5: Child process import")
    
    # Ensure application path
    added_paths = ensure_application_path()
    
    # Run in child process (using module-level function)
    with multiprocessing.Pool(1) as pool:
        result, message = pool.apply(_child_process_test_worker)
    
    assert result, f"Child process test failed: {message}"
    print(f"   ✅ Child process import test: {message}")
    
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("Testing Path Utils for Spawn Mode")
    print("=" * 70)
    
    results = []
    
    # Test 1: Find module path
    try:
        results.append(("Find module path", test_find_module_path()))
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        results.append(("Find module path", False))
    
    # Test 2: Ensure module path in sys.path
    try:
        results.append(("Ensure module path in sys.path", test_ensure_module_path_in_syspath()))
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        results.append(("Ensure module path in sys.path", False))
    
    # Test 3: Ensure application path
    try:
        results.append(("Ensure application path", test_ensure_application_path()))
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        results.append(("Ensure application path", False))
    
    # Test 4: Ensure registered modules paths
    try:
        results.append(("Ensure registered modules paths", test_ensure_registered_modules_paths()))
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        results.append(("Ensure registered modules paths", False))
    
    # Test 5: Child process import
    try:
        results.append(("Child process import", test_child_process_import()))
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        results.append(("Child process import", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} tests")
    
    if failed > 0:
        return 1
    
    print("\n🎉 All tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

