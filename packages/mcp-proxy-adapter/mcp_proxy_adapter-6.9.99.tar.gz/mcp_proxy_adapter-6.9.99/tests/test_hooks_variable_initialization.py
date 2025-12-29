#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Test for hooks variable initialization fix in CommandExecutionJob.

This test verifies that:
1. hooks variable is always defined before use in CommandExecutionJob.run()
2. No 'cannot access local variable hooks' error occurs
3. Commands are registered correctly in child processes
"""

import asyncio
import multiprocessing
import sys
from pathlib import Path

# Set spawn mode before any imports
multiprocessing.set_start_method("spawn", force=True)

from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.hooks import (
    register_custom_commands_hook,
    hooks,
)
from mcp_proxy_adapter.commands.queue.jobs import CommandExecutionJob
from mcp_proxy_adapter.integrations.queuemgr_integration import QueueManagerIntegration
from mcp_proxy_adapter.commands.base import Command, CommandResult


# Import test module that auto-registers commands
from tests.test_module_for_spawn import TestSpawnCommand


# Hook function to register test command
def register_test_commands(registry_instance):
    """Register test commands via hook."""
    registry_instance.register(TestSpawnCommand, "custom")


async def test_hooks_variable_initialization():
    """
    Test that hooks variable is always defined in CommandExecutionJob.run().

    This test specifically checks the fix for:
    'cannot access local variable hooks where it is not associated with a value'
    """
    print("\n🧪 Test: hooks variable initialization in CommandExecutionJob")

    # Clear registry
    registry._commands.clear()
    registry._command_types.clear()

    # Clear hooks
    hooks._custom_commands_hooks.clear()
    hooks._auto_register_modules.clear()
    hooks._hook_modules.clear()

    # Register hook in main process
    register_custom_commands_hook(register_test_commands)

    # Verify modules are registered
    auto_import_modules = hooks.get_auto_import_modules()
    assert len(auto_import_modules) > 0, "Modules should be registered for auto-import"
    print(f"   ✅ Registered modules: {auto_import_modules}")

    # Initialize queue manager
    queue_manager = QueueManagerIntegration()
    await queue_manager.start()

    try:
        # Create job parameters with auto_import_modules
        # This simulates what handlers.py does
        job_params = {
            "command": "test_spawn_command",
            "params": {"message": "test"},
            "context": {},
            "auto_import_modules": auto_import_modules,  # Pass modules to child process
        }

        job_id = "test-hooks-init-job"

        # Add job to queue
        await queue_manager.add_job(CommandExecutionJob, job_id, job_params)

        # Start job
        await queue_manager.start_job(job_id)

        # Wait for job to complete
        max_wait = 10
        waited = 0
        while waited < max_wait:
            status_obj = await queue_manager.get_job_status(job_id)
            if status_obj.status in ["completed", "failed"]:
                break
            await asyncio.sleep(0.5)
            waited += 0.5

        # Get final status
        final_status = await queue_manager.get_job_status(job_id)

        # Verify job completed successfully
        assert final_status.status == "completed", (
            f"Job should complete successfully, got status: {final_status.status}, "
            f"error: {final_status.error}"
        )

        # Verify result
        assert final_status.result is not None, "Job should have a result"
        # Check for hooks variable error in result
        result_str = str(final_status.result)
        if "cannot access local variable 'hooks'" in result_str.lower():
            print(f"   ❌ CRITICAL: Hooks variable error found in result!")
            return False
        # Command may have validation errors, but should not have hooks error
        if final_status.result.get("success") is not True:
            # Check if error is about hooks
            error_msg = str(final_status.result.get("error", ""))
            if "cannot access local variable 'hooks'" in error_msg.lower():
                print(f"   ❌ CRITICAL: Hooks variable error: {error_msg}")
                return False
            # Other errors are OK for this test (we're just checking hooks variable)
            print(f"   ⚠️  Command had other error (OK for hooks test): {error_msg}")

        print(f"   ✅ Job completed successfully")
        print(f"   ✅ Result: {final_status.result}")
        print(f"   ✅ No 'hooks variable' error occurred")

        return True

    finally:
        await queue_manager.stop()


async def test_hooks_variable_without_auto_import_modules():
    """
    Test that hooks variable is defined even when auto_import_modules is not provided.

    This tests the fallback path where hooks are imported from hooks module.
    """
    print("\n🧪 Test: hooks variable initialization (fallback path)")

    # Clear registry
    registry._commands.clear()
    registry._command_types.clear()

    # Clear hooks
    hooks._custom_commands_hooks.clear()
    hooks._auto_register_modules.clear()
    hooks._hook_modules.clear()

    # Register hook in main process
    register_custom_commands_hook(register_test_commands)

    # Initialize queue manager
    queue_manager = QueueManagerIntegration()
    await queue_manager.start()

    try:
        # Create job parameters WITHOUT auto_import_modules
        # This tests the fallback path
        job_params = {
            "command": "test_spawn_command",
            "params": {"message": "test"},
            "context": {},
            # Note: auto_import_modules is NOT provided
        }

        job_id = "test-hooks-fallback-job"

        # Add job to queue
        await queue_manager.add_job(CommandExecutionJob, job_id, job_params)

        # Start job
        await queue_manager.start_job(job_id)

        # Wait for job to complete
        max_wait = 10
        waited = 0
        while waited < max_wait:
            status_obj = await queue_manager.get_job_status(job_id)
            if status_obj.status in ["completed", "failed"]:
                break
            await asyncio.sleep(0.5)
            waited += 0.5

        # Get final status
        final_status = await queue_manager.get_job_status(job_id)

        # Verify job completed successfully (or at least didn't fail with hooks error)
        assert final_status.status in [
            "completed",
            "failed",
        ], "Job should complete or fail"

        if final_status.status == "failed":
            # Check that error is NOT about hooks variable
            error_msg = str(final_status.error or "")
            assert (
                "cannot access local variable 'hooks'" not in error_msg
            ), f"Should not have 'hooks variable' error, got: {error_msg}"
            print(f"   ⚠️  Job failed (expected in fallback path): {error_msg}")
        else:
            print(f"   ✅ Job completed successfully (unexpected but good)")

        print(f"   ✅ No 'hooks variable' error occurred")

        return True

    finally:
        await queue_manager.stop()


async def main():
    """Run all tests."""
    print("=" * 70)
    print("Testing hooks variable initialization fix")
    print("=" * 70)

    results = []

    try:
        result = await test_hooks_variable_initialization()
        results.append(("hooks variable initialization", result))
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        results.append(("hooks variable initialization", False))

    try:
        result = await test_hooks_variable_without_auto_import_modules()
        results.append(("hooks variable fallback path", result))
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        results.append(("hooks variable fallback path", False))

    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed} passed, {total - passed} failed out of {total} tests")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
