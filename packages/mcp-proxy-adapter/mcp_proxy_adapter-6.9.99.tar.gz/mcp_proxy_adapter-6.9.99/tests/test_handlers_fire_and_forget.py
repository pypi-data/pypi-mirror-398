"""
Unit tests for handlers.py fire-and-forget queue execution.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_proxy_adapter.api.handlers import execute_command
from mcp_proxy_adapter.core.errors import MethodNotFoundError, InternalError


class TestExecuteCommandFireAndForget:
    """Test suite for execute_command with fire-and-forget queue execution."""

    @pytest.mark.asyncio
    async def test_execute_command_queue_mode_fire_and_forget(self) -> None:
        """Test that queue-backed commands return job_id immediately."""
        # Mock command class with use_queue=True
        mock_command_class = MagicMock()
        mock_command_class.use_queue = True
        mock_command_class.run = AsyncMock()

        # Mock registry
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            # Mock queue manager (imported inside function)
            with patch(
                "mcp_proxy_adapter.integrations.queuemgr_integration.get_global_queue_manager"
            ) as mock_get_qm:
                mock_queue_manager = AsyncMock()
                mock_get_qm.return_value = mock_queue_manager

                # Mock add_job
                mock_queue_manager.add_job = AsyncMock()

                # Mock hooks (imported inside function)
                with patch("mcp_proxy_adapter.commands.hooks.hooks") as mock_hooks:
                    mock_hooks.get_auto_import_modules.return_value = []

                    # Mock asyncio.create_task
                    with patch("asyncio.create_task") as mock_create_task:
                        mock_task = MagicMock()
                        mock_create_task.return_value = mock_task

                        # Mock uuid (imported inside function as 'import uuid')
                        with patch("uuid.uuid4") as mock_uuid:
                            mock_uuid_obj = MagicMock()
                            mock_uuid_obj.__str__ = MagicMock(
                                return_value="test-job-id-123"
                            )
                            mock_uuid.return_value = mock_uuid_obj

                            # Execute command
                            result = await execute_command(
                                command_name="test_command",
                                params={"param1": "value1"},
                            )

                            # Verify result
                            assert result["success"] is True
                            assert "job_id" in result
                            assert result["status"] == "pending"
                            assert "message" in result
                            assert result["job_id"] == "test-job-id-123"

                            # Verify add_job was called
                            mock_queue_manager.add_job.assert_called_once()
                            call_args = mock_queue_manager.add_job.call_args
                            assert call_args[0][1] == "test-job-id-123"  # job_id

                            # Verify start_job was scheduled in background
                            mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command_queue_mode_background_start_error_handled(
        self,
    ) -> None:
        """Test that background start_job errors don't fail the request."""
        # Mock command class with use_queue=True
        mock_command_class = MagicMock()
        mock_command_class.use_queue = True

        # Mock registry
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            # Mock queue manager (imported inside function)
            with patch(
                "mcp_proxy_adapter.integrations.queuemgr_integration.get_global_queue_manager"
            ) as mock_get_qm:
                mock_queue_manager = AsyncMock()
                mock_get_qm.return_value = mock_queue_manager

                # Mock add_job
                mock_queue_manager.add_job = AsyncMock()

                # Mock hooks (imported inside function)
                with patch("mcp_proxy_adapter.commands.hooks.hooks") as mock_hooks:
                    mock_hooks.get_auto_import_modules.return_value = []

                    # Mock asyncio.create_task with background function that raises error
                    async def failing_background_start():
                        raise Exception("Background start failed")

                    with patch("asyncio.create_task") as mock_create_task:
                        mock_task = MagicMock()
                        mock_create_task.return_value = mock_task

                        # Mock uuid (imported inside function as 'import uuid')
                        with patch("uuid.uuid4") as mock_uuid:
                            mock_uuid_obj = MagicMock()
                            mock_uuid_obj.__str__ = MagicMock(
                                return_value="test-job-id-123"
                            )
                            mock_uuid.return_value = mock_uuid_obj

                            # Execute command - should succeed even if background start fails
                            result = await execute_command(
                                command_name="test_command",
                                params={"param1": "value1"},
                            )

                            # Verify result is still returned
                            assert result["success"] is True
                            assert "job_id" in result
                            assert result["job_id"] == "test-job-id-123"

    @pytest.mark.asyncio
    async def test_execute_command_immediate_mode(self) -> None:
        """Test immediate command execution (non-queue mode)."""
        # Mock command class without use_queue
        mock_command_class = MagicMock()
        mock_command_class.use_queue = False
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"success": True, "data": "result"}
        mock_command_class.run = AsyncMock(return_value=mock_result)

        # Mock registry
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            # Execute command
            result = await execute_command(
                command_name="echo", params={"message": "test"}
            )

            # Verify result
            assert result == {"success": True, "data": "result"}
            mock_command_class.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command_not_found(self) -> None:
        """Test command not found error."""
        # Mock registry to raise KeyError
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.side_effect = KeyError("Command not found")

            with pytest.raises(MethodNotFoundError):
                await execute_command(command_name="nonexistent", params={})

    @pytest.mark.asyncio
    async def test_execute_command_queue_add_job_failure(self) -> None:
        """Test handling of queue add_job failure."""
        # Mock command class with use_queue=True
        mock_command_class = MagicMock()
        mock_command_class.use_queue = True

        # Mock registry
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            # Mock queue manager with failing add_job (imported inside function)
            with patch(
                "mcp_proxy_adapter.integrations.queuemgr_integration.get_global_queue_manager"
            ) as mock_get_qm:
                mock_queue_manager = AsyncMock()
                mock_get_qm.return_value = mock_queue_manager
                mock_queue_manager.add_job = AsyncMock(
                    side_effect=Exception("Queue error")
                )

                # Mock hooks (imported inside function)
                with patch("mcp_proxy_adapter.commands.hooks.hooks") as mock_hooks:
                    mock_hooks.get_auto_import_modules.return_value = []

                    # Mock uuid (imported inside function as 'import uuid')
                    with patch("uuid.uuid4") as mock_uuid:
                        mock_uuid_obj = MagicMock()
                        mock_uuid_obj.__str__ = MagicMock(
                            return_value="test-job-id-123"
                        )
                        mock_uuid.return_value = mock_uuid_obj

                        # Execute command should raise InternalError
                        with pytest.raises(
                            InternalError, match="Failed to queue command"
                        ):
                            await execute_command(
                                command_name="test_command",
                                params={"param1": "value1"},
                            )

    @pytest.mark.asyncio
    async def test_execute_command_immediate_timeout(self) -> None:
        """Test immediate command timeout."""
        # Mock command class without use_queue
        mock_command_class = MagicMock()
        mock_command_class.use_queue = False
        mock_command_class.run = AsyncMock()

        # Mock asyncio.wait_for to raise TimeoutError
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            with patch("asyncio.wait_for") as mock_wait_for:
                mock_wait_for.side_effect = TimeoutError()

                with pytest.raises(InternalError, match="timed out"):
                    await execute_command(
                        command_name="slow_command", params={"delay": 100}
                    )

    @pytest.mark.asyncio
    async def test_handle_json_rpc_success(self) -> None:
        """Test handle_json_rpc with successful command execution."""
        from mcp_proxy_adapter.api.handlers import handle_json_rpc

        # Mock execute_command
        with patch("mcp_proxy_adapter.api.handlers.execute_command") as mock_exec:
            mock_exec.return_value = {"success": True, "data": "result"}

            request_data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "test"},
                "id": 1,
            }

            result = await handle_json_rpc(request_data)

            assert result["jsonrpc"] == "2.0"
            assert result["id"] == 1
            assert "result" in result
            assert result["result"] == {"success": True, "data": "result"}

    @pytest.mark.asyncio
    async def test_handle_json_rpc_error(self) -> None:
        """Test handle_json_rpc with command error - errors are not caught, they propagate."""
        from mcp_proxy_adapter.api.handlers import handle_json_rpc
        from mcp_proxy_adapter.core.errors import MethodNotFoundError

        # Mock execute_command to raise MicroserviceError
        # Note: handle_json_rpc doesn't catch errors, they propagate to caller
        with patch("mcp_proxy_adapter.api.handlers.execute_command") as mock_exec:
            error = MethodNotFoundError("Command not found")
            mock_exec.side_effect = error

            request_data = {
                "jsonrpc": "2.0",
                "method": "nonexistent",
                "params": {},
                "id": 1,
            }

            # Error should propagate - caller should handle it
            with pytest.raises(MethodNotFoundError):
                await handle_json_rpc(request_data)

    @pytest.mark.asyncio
    async def test_handle_json_rpc_simplified_format(self) -> None:
        """Test handle_json_rpc with simplified format (command instead of method)."""
        from mcp_proxy_adapter.api.handlers import handle_json_rpc

        # Mock execute_command
        with patch("mcp_proxy_adapter.api.handlers.execute_command") as mock_exec:
            mock_exec.return_value = {"success": True}

            request_data = {
                "command": "echo",
                "params": {"message": "test"},
            }

            result = await handle_json_rpc(request_data)

            assert result["jsonrpc"] == "2.0"
            assert result["id"] == 1  # Default id
            assert "result" in result

    @pytest.mark.asyncio
    async def test_handle_batch_json_rpc(self) -> None:
        """Test handle_batch_json_rpc with multiple requests."""
        from mcp_proxy_adapter.api.handlers import handle_batch_json_rpc

        # Mock handle_json_rpc
        with patch("mcp_proxy_adapter.api.handlers.handle_json_rpc") as mock_handle:
            mock_handle.side_effect = [
                {"jsonrpc": "2.0", "result": "result1", "id": 1},
                {"jsonrpc": "2.0", "result": "result2", "id": 2},
            ]

            batch_requests = [
                {"jsonrpc": "2.0", "method": "echo", "params": {}, "id": 1},
                {"jsonrpc": "2.0", "method": "help", "params": {}, "id": 2},
            ]

            results = await handle_batch_json_rpc(batch_requests)

            assert len(results) == 2
            assert results[0]["result"] == "result1"
            assert results[1]["result"] == "result2"

    @pytest.mark.asyncio
    async def test_get_server_health(self) -> None:
        """Test get_server_health endpoint."""
        from mcp_proxy_adapter.api.handlers import get_server_health

        # Mock imports inside function (psutil, datetime, os, platform, sys)
        with patch("psutil.Process") as mock_process_class:
            mock_process = MagicMock()
            mock_process.create_time.return_value = 1000.0
            mock_mem_info = MagicMock()
            mock_mem_info.rss = 1024 * 1024 * 100  # 100 MB
            mock_process.memory_info.return_value = mock_mem_info
            mock_process_class.return_value = mock_process

            with patch("datetime.datetime") as mock_datetime:
                mock_start_time = MagicMock()
                mock_start_time.isoformat.return_value = "2024-01-01T00:00:00"
                mock_now = MagicMock()
                mock_now.timestamp.return_value = 2000.0
                mock_datetime.now.return_value = mock_now
                mock_datetime.fromtimestamp.return_value = mock_start_time

                with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
                    mock_registry.get_all_commands.return_value = {
                        "cmd1": None,
                        "cmd2": None,
                    }

                    with patch("os.getpid", return_value=12345):
                        with patch("os.cpu_count", return_value=4):
                            with patch("platform.platform", return_value="Linux"):
                                with patch("sys.version", return_value="3.12.0"):

                                    health = await get_server_health()

                                    assert health["status"] == "ok"
                                    assert "uptime" in health
                                    assert "components" in health
                                    assert (
                                        health["components"]["system"]["cpu_count"] == 4
                                    )

    @pytest.mark.asyncio
    async def test_get_commands_list(self) -> None:
        """Test get_commands_list endpoint."""
        from mcp_proxy_adapter.api.handlers import get_commands_list

        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_cmd1 = MagicMock()
            mock_cmd1.get_schema.return_value = {
                "type": "object",
                "description": "Command 1",
            }
            mock_cmd2 = MagicMock()
            mock_cmd2.get_schema.return_value = {
                "type": "object",
                "description": "Command 2",
            }

            mock_registry.get_all_commands.return_value = {
                "cmd1": mock_cmd1,
                "cmd2": mock_cmd2,
            }

            commands = await get_commands_list()

            assert "cmd1" in commands
            assert "cmd2" in commands
            assert commands["cmd1"]["name"] == "cmd1"

    @pytest.mark.asyncio
    async def test_handle_heartbeat(self) -> None:
        """Test handle_heartbeat endpoint."""
        from mcp_proxy_adapter.api.handlers import handle_heartbeat

        with patch("mcp_proxy_adapter.api.handlers.time") as mock_time:
            mock_time.time.return_value = 1234567890.0

            heartbeat = await handle_heartbeat()

            assert heartbeat["status"] == "ok"
            assert "server_name" in heartbeat
            assert "server_url" in heartbeat
            assert "timestamp" in heartbeat
            assert heartbeat["timestamp"] == 1234567890.0

    @pytest.mark.asyncio
    async def test_handle_json_rpc_invalid_jsonrpc_version(self) -> None:
        """Test handle_json_rpc with invalid jsonrpc version."""
        from mcp_proxy_adapter.api.handlers import handle_json_rpc

        request_data = {
            "jsonrpc": "1.0",  # Invalid version
            "method": "echo",
            "params": {},
            "id": 1,
        }

        result = await handle_json_rpc(request_data)

        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert "error" in result
        assert result["error"]["code"] == -32600  # Invalid Request

    @pytest.mark.asyncio
    async def test_handle_json_rpc_missing_method(self) -> None:
        """Test handle_json_rpc with missing method."""
        from mcp_proxy_adapter.api.handlers import handle_json_rpc

        request_data = {
            "jsonrpc": "2.0",
            "params": {},
            "id": 1,
        }

        result = await handle_json_rpc(request_data)

        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert "error" in result
        assert result["error"]["code"] == -32600  # Invalid Request

    @pytest.mark.asyncio
    async def test_handle_json_rpc_missing_command(self) -> None:
        """Test handle_json_rpc simplified format with missing command."""
        from mcp_proxy_adapter.api.handlers import handle_json_rpc

        request_data = {
            "params": {},
        }

        result = await handle_json_rpc(request_data)

        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1  # Default id
        assert "error" in result
        assert result["error"]["code"] == -32600  # Invalid Request

    @pytest.mark.asyncio
    async def test_execute_command_with_context(self) -> None:
        """Test execute_command with request context."""
        # Mock command class without use_queue
        mock_command_class = MagicMock()
        mock_command_class.use_queue = False
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"success": True}
        mock_command_class.run = AsyncMock(return_value=mock_result)

        # Mock registry
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            # Mock request with state
            mock_request = MagicMock()
            mock_request.state.user_id = "user123"
            mock_request.state.user_role = "admin"

            # Execute command with request
            await execute_command(
                command_name="echo",
                params={"message": "test"},
                request=mock_request,
            )

            # Verify context was passed to command
            call_kwargs = mock_command_class.run.call_args[1]
            assert "context" in call_kwargs
            assert call_kwargs["context"]["user"]["id"] == "user123"

    @pytest.mark.asyncio
    async def test_execute_command_unhandled_exception(self) -> None:
        """Test execute_command with unhandled exception."""
        # Mock command class without use_queue
        mock_command_class = MagicMock()
        mock_command_class.use_queue = False
        mock_command_class.run = AsyncMock(side_effect=ValueError("Unexpected error"))

        # Mock registry
        with patch("mcp_proxy_adapter.api.handlers.registry") as mock_registry:
            mock_registry.get_command.return_value = mock_command_class

            # Execute command should raise InternalError for unhandled exceptions
            with pytest.raises(InternalError, match="Internal error"):
                await execute_command(
                    command_name="failing_command", params={"param1": "value1"}
                )

    @pytest.mark.asyncio
    async def test_handle_heartbeat_with_config(self) -> None:
        """Test handle_heartbeat with config available."""
        from mcp_proxy_adapter.api.handlers import handle_heartbeat

        # Mock config (imported inside function)
        mock_config = MagicMock()
        mock_config.model.server.name = "test-server"
        mock_config.model.server.host = "127.0.0.1"
        mock_config.model.server.port = 9000
        mock_config.model.server.ssl = MagicMock()
        mock_config.model.server.ssl.enabled = False

        with patch("mcp_proxy_adapter.config.get_config") as mock_get_config:
            mock_get_config.return_value = mock_config

            with patch("mcp_proxy_adapter.api.handlers.time") as mock_time:
                mock_time.time.return_value = 1234567890.0

                heartbeat = await handle_heartbeat()

                assert heartbeat["status"] == "ok"
                assert heartbeat["server_name"] == "test-server"
                assert heartbeat["server_url"] == "http://127.0.0.1:9000"

    @pytest.mark.asyncio
    async def test_handle_heartbeat_with_https_config(self) -> None:
        """Test handle_heartbeat with HTTPS config."""
        from mcp_proxy_adapter.api.handlers import handle_heartbeat

        # Mock config with HTTPS (imported inside function)
        mock_config = MagicMock()
        mock_config.model.server.name = "test-server"
        mock_config.model.server.host = "127.0.0.1"
        mock_config.model.server.port = 9443
        mock_config.model.server.ssl = MagicMock()
        mock_config.model.server.ssl.enabled = True

        with patch("mcp_proxy_adapter.config.get_config") as mock_get_config:
            mock_get_config.return_value = mock_config

            with patch("mcp_proxy_adapter.api.handlers.time") as mock_time:
                mock_time.time.return_value = 1234567890.0

                heartbeat = await handle_heartbeat()

                assert heartbeat["server_url"] == "https://127.0.0.1:9443"
