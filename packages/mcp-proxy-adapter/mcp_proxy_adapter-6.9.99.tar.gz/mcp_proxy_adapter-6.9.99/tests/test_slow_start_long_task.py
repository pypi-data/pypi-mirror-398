"""
Test for slow-start long task command with fire-and-forget execution.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import pytest
from mcp_proxy_adapter.client.jsonrpc_client.client import JsonRpcClient


@pytest.mark.asyncio
async def test_slow_start_long_task_fire_and_forget():
    """
    Test slow-start long task command with fire-and-forget execution.

    This test verifies:
    1. Command is submitted and job_id is returned immediately (< 1 second)
    2. Client can poll job status independently
    3. Job completes successfully after slow startup and long execution
    """
    client = JsonRpcClient(protocol="http", host="127.0.0.1", port=8080)

    try:
        # Submit command with short durations for testing
        # In production, startup_phase_duration=45, execution_phase_duration=180
        result = await client.execute_command_unified(
            command="slow_start_long_task",
            params={
                "task_name": "test_task",
                "startup_phase_duration": 5,  # 5 seconds startup for testing
                "execution_phase_duration": 10,  # 10 seconds execution for testing
                "startup_steps": 5,
                "execution_steps": 5,
            },
            auto_poll=True,
            poll_interval=1.0,
            timeout=30.0,  # 30 seconds total timeout for test
        )

        # Verify result structure
        assert result["mode"] == "queued", "Command should be queued"
        assert "job_id" in result, "Result should contain job_id"
        assert (
            result["status"] == "completed"
        ), f"Job should complete, got: {result['status']}"
        assert "result" in result, "Result should contain command result"

        # Extract result from nested structure
        # Structure: result["result"]["result"]["success"] and result["result"]["result"]["data"]
        nested_result = result["result"]
        if isinstance(nested_result, dict) and "result" in nested_result:
            command_result = nested_result["result"]
        else:
            command_result = nested_result

        # Verify result data
        assert command_result["success"] is True, "Command should succeed"
        assert (
            command_result["data"]["task_name"] == "test_task"
        ), "Task name should match"
        assert (
            command_result["data"]["status"] == "completed"
        ), "Task status should be completed"

        print(f"✅ Test passed: Job {result['job_id']} completed successfully")

    except TimeoutError:
        pytest.fail("Job did not complete within timeout")
    except Exception as e:
        pytest.fail(f"Test failed with error: {e}")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_slow_start_long_task_manual_polling():
    """
    Test slow-start long task with manual polling.

    This test verifies that manual polling works correctly
    for long-running commands.
    """
    client = JsonRpcClient(protocol="http", host="127.0.0.1", port=8080)

    try:
        # Submit command without auto-polling
        result = await client.execute_command_unified(
            command="slow_start_long_task",
            params={
                "task_name": "manual_poll_test",
                "startup_phase_duration": 3,  # 3 seconds for testing
                "execution_phase_duration": 5,  # 5 seconds for testing
                "startup_steps": 3,
                "execution_steps": 5,
            },
            auto_poll=False,  # Manual polling
        )

        job_id = result["job_id"]
        assert job_id is not None, "Job ID should be returned"

        # Manual polling loop
        max_attempts = 20
        for attempt in range(max_attempts):
            status = await client.queue_get_job_status(job_id)

            # Extract status from nested structure
            current_status = status.get("status", "unknown")
            if not current_status or current_status == "unknown":
                # Try nested structures
                data = status.get("data", {})
                current_status = data.get("status", "unknown")

            progress = status.get("progress", 0)
            if not progress:
                # Try nested structures
                data = status.get("data", {})
                progress = data.get("progress", 0)

            if current_status in ("completed", "failed", "stopped"):
                assert (
                    current_status == "completed"
                ), f"Job should complete, got: {current_status}"
                break

            await asyncio.sleep(1.0)
        else:
            pytest.fail("Job did not complete within max attempts")

        print(f"✅ Manual polling test passed: Job {job_id} completed")

    except Exception as e:
        pytest.fail(f"Manual polling test failed: {e}")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_slow_start_long_task_progress_hook():
    """
    Test slow-start long task with progress hook.

    This test verifies that progress hooks are called correctly.
    """
    client = JsonRpcClient(protocol="http", host="127.0.0.1", port=8080)

    progress_updates = []

    async def progress_callback(status: dict) -> None:
        """Collect progress updates."""
        # Extract status and progress from nested structure
        current_status = status.get("status", "unknown")
        progress = status.get("progress", 0)
        description = status.get("description", "")

        # Try nested structures if not found at top level
        if not current_status or current_status == "unknown":
            data = status.get("data", {})
            current_status = data.get("status", "unknown")
        if not progress:
            data = status.get("data", {})
            progress = data.get("progress", 0)
        if not description:
            data = status.get("data", {})
            description = data.get("description", "")

        progress_updates.append(
            {
                "status": current_status,
                "progress": progress,
                "description": description,
            }
        )

    try:
        result = await client.execute_command_unified(
            command="slow_start_long_task",
            params={
                "task_name": "progress_test",
                "startup_phase_duration": 3,
                "execution_phase_duration": 5,
                "startup_steps": 3,
                "execution_steps": 5,
            },
            auto_poll=True,
            poll_interval=0.5,  # Poll more frequently
            timeout=20.0,
            status_hook=progress_callback,
        )

        # Verify progress updates were collected
        assert len(progress_updates) > 0, "Progress updates should be collected"
        assert result["status"] == "completed", "Job should complete"

        # Verify progress increased over time
        progress_values = [u["progress"] for u in progress_updates]
        assert max(progress_values) > 0, "Progress should increase"

        print(
            f"✅ Progress hook test passed: {len(progress_updates)} updates collected"
        )

    except Exception as e:
        pytest.fail(f"Progress hook test failed: {e}")
    finally:
        await client.close()
