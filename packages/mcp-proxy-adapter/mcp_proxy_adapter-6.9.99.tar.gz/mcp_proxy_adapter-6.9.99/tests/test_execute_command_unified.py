"""Tests for execute_command_unified method.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient, QueueJobStatus


class TestExecuteCommandUnified:
    """Test suite for execute_command_unified method."""

    @pytest.fixture
    def client(self) -> JsonRpcClient:
        """Create test client instance."""
        return JsonRpcClient(protocol="http", host="127.0.0.1", port=8080)

    @pytest.mark.asyncio
    async def test_immediate_execution_no_job_id(self, client: JsonRpcClient) -> None:
        """Test immediate execution when no job_id is returned."""
        # Mock execute_command to return immediate result
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "data": {"result": "test"}}
        )

        result = await client.execute_command_unified("echo", {"message": "test"})

        assert result["mode"] == "immediate"
        assert result["queued"] is False
        assert result["command"] == "echo"
        assert "result" in result

    @pytest.mark.asyncio
    async def test_immediate_execution_expect_queue_false(
        self, client: JsonRpcClient
    ) -> None:
        """Test immediate execution when expect_queue=False even with job_id."""
        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": "test-job-123"}
        )

        result = await client.execute_command_unified(
            "echo", {"message": "test"}, expect_queue=False
        )

        assert result["mode"] == "immediate"
        assert result["queued"] is False

    @pytest.mark.asyncio
    async def test_expect_queue_true_no_job_id_raises_error(
        self, client: JsonRpcClient
    ) -> None:
        """Test that expect_queue=True without job_id raises RuntimeError."""
        # Mock execute_command to return no job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "data": {"result": "test"}}
        )

        with pytest.raises(RuntimeError, match="expected to run via queue"):
            await client.execute_command_unified(
                "long_task", {"seconds": 10}, expect_queue=True
            )

    @pytest.mark.asyncio
    async def test_queued_execution_auto_poll_false(
        self, client: JsonRpcClient
    ) -> None:
        """Test queued execution with auto_poll=False."""
        job_id = "test-job-123"
        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": job_id}
        )

        result = await client.execute_command_unified(
            "long_task", {"seconds": 10}, auto_poll=False
        )

        assert result["mode"] == "queued"
        assert result["queued"] is True
        assert result["job_id"] == job_id
        assert "status" in result

    @pytest.mark.asyncio
    async def test_queued_execution_auto_poll_true_completed(
        self, client: JsonRpcClient
    ) -> None:
        """Test queued execution with auto_poll=True and completed status."""
        job_id = "test-job-123"
        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": job_id}
        )

        # Mock queue_get_job_status to return completed status
        status_responses = [
            {"status": "running", "result": None},
            {"status": "completed", "result": {"output": "done"}},
        ]
        client.queue_get_job_status = AsyncMock(  # type: ignore[method-assign]
            side_effect=status_responses
        )

        result = await client.execute_command_unified(
            "long_task", {"seconds": 10}, auto_poll=True, poll_interval=0.1
        )

        assert result["mode"] == "queued"
        assert result["queued"] is True
        assert result["job_id"] == job_id
        assert result["status"] == "completed"
        assert result["result"] == {"output": "done"}

    @pytest.mark.asyncio
    async def test_queued_execution_auto_poll_true_failed(
        self, client: JsonRpcClient
    ) -> None:
        """Test queued execution with auto_poll=True and failed status."""
        job_id = "test-job-123"
        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": job_id}
        )

        # Mock queue_get_job_status to return failed status
        status_responses = [
            {"status": "running", "result": None},
            {"status": "failed", "result": None, "error": "Task failed"},
        ]
        client.queue_get_job_status = AsyncMock(  # type: ignore[method-assign]
            side_effect=status_responses
        )

        with pytest.raises(RuntimeError, match="failed"):
            await client.execute_command_unified(
                "long_task", {"seconds": 10}, auto_poll=True, poll_interval=0.1
            )

    @pytest.mark.asyncio
    async def test_queued_execution_timeout(self, client: JsonRpcClient) -> None:
        """Test queued execution with timeout."""
        job_id = "test-job-123"
        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": job_id}
        )

        # Mock queue_get_job_status to always return running
        client.queue_get_job_status = AsyncMock(  # type: ignore[method-assign]
            return_value={"status": "running", "result": None}
        )

        with pytest.raises(TimeoutError, match="did not finish within"):
            await client.execute_command_unified(
                "long_task",
                {"seconds": 10},
                auto_poll=True,
                poll_interval=0.1,
                timeout=0.3,
            )

    @pytest.mark.asyncio
    async def test_status_hook_invocation(self, client: JsonRpcClient) -> None:
        """Test that status_hook is called for each poll iteration."""
        job_id = "test-job-123"
        status_hook_calls = []

        async def status_hook(status: Dict[str, Any]) -> None:
            status_hook_calls.append(status)

        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": job_id}
        )

        # Mock queue_get_job_status to return multiple statuses
        # Flow: initial call -> hook, then loop: pending -> hook, poll -> running -> hook, poll -> completed -> exit -> hook
        status_responses = [
            {"status": "pending", "result": None},  # Initial status
            {"status": "pending", "result": None},  # First poll in loop (still pending)
            {"status": "running", "result": None},  # Second poll in loop
            {"status": "completed", "result": {"output": "done"}},  # Third poll - exits loop
        ]
        client.queue_get_job_status = AsyncMock(  # type: ignore[method-assign]
            side_effect=status_responses
        )

        await client.execute_command_unified(
            "long_task",
            {"seconds": 10},
            auto_poll=True,
            poll_interval=0.1,
            status_hook=status_hook,
        )

        # Should be called for initial status + each poll iteration + final status
        # Initial: pending -> hook
        # Loop: pending (still pending) -> hook, poll -> running -> hook, poll -> completed -> hook (in loop), exit
        # Final: completed -> hook (after loop)
        # Total: 5 calls (initial pending, loop pending, loop running, loop completed, final completed)
        assert len(status_hook_calls) == 5
        assert status_hook_calls[0]["status"] == "pending"  # Initial
        assert status_hook_calls[1]["status"] == "pending"  # In loop
        assert status_hook_calls[2]["status"] == "running"  # In loop
        assert status_hook_calls[3]["status"] == "completed"  # In loop (before exit)
        assert status_hook_calls[4]["status"] == "completed"  # Final (after loop)

    @pytest.mark.asyncio
    async def test_cancelled_status_handling(self, client: JsonRpcClient) -> None:
        """Test handling of cancelled/stopped status."""
        job_id = "test-job-123"
        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": job_id}
        )

        # Mock queue_get_job_status to return stopped status
        client.queue_get_job_status = AsyncMock(  # type: ignore[method-assign]
            return_value={"status": "stopped", "result": None}
        )

        result = await client.execute_command_unified(
            "long_task", {"seconds": 10}, auto_poll=True, poll_interval=0.1
        )

        assert result["mode"] == "queued"
        assert result["status"] == "stopped"
        assert "warning" in result
        assert "stopped" in result["warning"]

    @pytest.mark.asyncio
    async def test_unknown_status_handling(self, client: JsonRpcClient) -> None:
        """Test handling of unknown status values."""
        job_id = "test-job-123"
        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": job_id}
        )

        # Mock queue_get_job_status to return unknown status
        client.queue_get_job_status = AsyncMock(  # type: ignore[method-assign]
            return_value={"status": "unknown_status", "result": None}
        )

        result = await client.execute_command_unified(
            "long_task", {"seconds": 10}, auto_poll=True, poll_interval=0.1
        )

        assert result["mode"] == "queued"
        assert result["status"] == "unknown_status"
        assert "warning" in result
        assert "Unknown status value" in result["warning"]

    @pytest.mark.asyncio
    async def test_queue_get_job_status_error_handling(
        self, client: JsonRpcClient
    ) -> None:
        """Test error handling when queue_get_job_status fails."""
        job_id = "test-job-123"
        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": job_id}
        )

        # Mock queue_get_job_status to raise exception
        client.queue_get_job_status = AsyncMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Job not found")
        )

        with pytest.raises(RuntimeError, match="Failed to get status"):
            await client.execute_command_unified(
                "long_task", {"seconds": 10}, auto_poll=True, poll_interval=0.1
            )

    @pytest.mark.asyncio
    async def test_nested_result_extraction(self, client: JsonRpcClient) -> None:
        """Test extraction of result from nested structures."""
        job_id = "test-job-123"
        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": job_id}
        )

        # Mock queue_get_job_status to return nested result
        # The extraction logic extracts "data" from result if present
        client.queue_get_job_status = AsyncMock(  # type: ignore[method-assign]
            return_value={
                "status": "completed",
                "result": {"data": {"output": "nested_result"}},
            }
        )

        result = await client.execute_command_unified(
            "long_task", {"seconds": 10}, auto_poll=True, poll_interval=0.1
        )

        # The extraction logic extracts data from result if result contains "data"
        assert result["result"] == {"output": "nested_result"}

    @pytest.mark.asyncio
    async def test_use_cmd_endpoint(self, client: JsonRpcClient) -> None:
        """Test execution using /cmd endpoint."""
        # Mock cmd_call instead of jsonrpc_call
        client.cmd_call = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "data": {"result": "test"}}
        )

        result = await client.execute_command_unified(
            "echo", {"message": "test"}, use_cmd_endpoint=True
        )

        assert result["mode"] == "immediate"
        client.cmd_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_id_extraction_from_data_section(
        self, client: JsonRpcClient
    ) -> None:
        """Test extraction of job_id from data section."""
        job_id = "test-job-123"
        # Mock execute_command to return job_id in data section
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "data": {"jobId": job_id}}
        )

        # Mock queue_get_job_status to return completed
        client.queue_get_job_status = AsyncMock(  # type: ignore[method-assign]
            return_value={"status": "completed", "result": {"output": "done"}}
        )

        result = await client.execute_command_unified(
            "long_task", {"seconds": 10}, auto_poll=True, poll_interval=0.1
        )

        assert result["mode"] == "queued"
        assert result["job_id"] == job_id

    @pytest.mark.asyncio
    async def test_all_pending_states_polling(self, client: JsonRpcClient) -> None:
        """Test that all pending states trigger polling."""
        job_id = "test-job-123"
        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": job_id}
        )

        # Test all pending states
        for pending_state in QueueJobStatus.get_pending_states():
            status_responses = [
                {"status": pending_state, "result": None},
                {"status": "completed", "result": {"output": "done"}},
            ]
            client.queue_get_job_status = AsyncMock(  # type: ignore[method-assign]
                side_effect=status_responses
            )

            result = await client.execute_command_unified(
                "long_task", {"seconds": 10}, auto_poll=True, poll_interval=0.1
            )

            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_all_failure_states_raise_error(self, client: JsonRpcClient) -> None:
        """Test that all failure states raise RuntimeError."""
        job_id = "test-job-123"
        # Mock execute_command to return job_id
        client.execute_command = AsyncMock(  # type: ignore[method-assign]
            return_value={"success": True, "job_id": job_id}
        )

        # Test all failure states
        for failure_state in QueueJobStatus.get_failure_states():
            client.queue_get_job_status = AsyncMock(  # type: ignore[method-assign]
                return_value={
                    "status": failure_state,
                    "result": None,
                    "error": "Failed",
                }
            )

            with pytest.raises(RuntimeError, match="failed"):
                await client.execute_command_unified(
                    "long_task", {"seconds": 10}, auto_poll=True, poll_interval=0.1
                )
