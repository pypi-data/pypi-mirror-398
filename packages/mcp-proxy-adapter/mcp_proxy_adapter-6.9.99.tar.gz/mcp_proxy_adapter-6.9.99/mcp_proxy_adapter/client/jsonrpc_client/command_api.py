"""Command helpers for JsonRpcClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, Optional, TYPE_CHECKING

from mcp_proxy_adapter.client.jsonrpc_client.queue_status import QueueJobStatus
from mcp_proxy_adapter.client.jsonrpc_client.transport import JsonRpcTransport

if TYPE_CHECKING:
    from mcp_proxy_adapter.client.jsonrpc_client.schema_generator import MethodInfo


class CommandApiMixin(JsonRpcTransport):
    """Mixin providing standard JSON-RPC command helpers."""

    async def echo(
        self, message: str = "Hello, World!", timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"message": message}
        if timestamp:
            params["timestamp"] = timestamp
        response = await self.jsonrpc_call("echo", params)
        return self._extract_result(response)

    async def help(self, command_name: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if command_name:
            params["command"] = command_name
        response = await self.jsonrpc_call("help", params)
        return self._extract_result(response)

    async def get_config(self) -> Dict[str, Any]:
        response = await self.jsonrpc_call("config", {})
        return self._extract_result(response)

    async def long_task(self, seconds: int) -> Dict[str, Any]:
        response = await self.jsonrpc_call("long_task", {"seconds": seconds})
        return self._extract_result(response)

    async def job_status(self, job_id: str) -> Dict[str, Any]:
        response = await self.jsonrpc_call("job_status", {"job_id": job_id})
        return self._extract_result(response)

    async def execute_command(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        use_cmd_endpoint: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute command using either /cmd endpoint or JSON-RPC.

        The /cmd endpoint supports the CommandRequest schema with oneOf discriminator
        and detailed parameter validation. Use use_cmd_endpoint=True to use this endpoint.

        Args:
            command: Command name to execute
            params: Optional command parameters
            use_cmd_endpoint: If True, use /cmd endpoint; otherwise use JSON-RPC

        Returns:
            Command execution result
        """
        if use_cmd_endpoint:
            return await self.cmd_call(command, params)
        else:
            response = await self.jsonrpc_call(command, params or {})
            return self._extract_result(response)

    async def execute_command_unified(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        use_cmd_endpoint: bool = False,
        expect_queue: Optional[bool] = None,
        auto_poll: bool = True,
        poll_interval: float = 1.0,
        timeout: Optional[float] = None,
        status_hook: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a command and transparently handle queued or immediate responses.

        The method hides differences between synchronous execution and queued jobs:

        1. Submits the command once via ``execute_command``.
        2. Detects whether the backend queued the job (by looking for ``job_id``).
        3. Optionally polls queue status until completion using asynchronous sleeps.

        Args:
            command: Command name to execute.
            params: Payload for the command.
            use_cmd_endpoint: Use the ``/cmd`` endpoint instead of JSON-RPC.
            expect_queue: Force assumption about queue usage. If ``True`` and
                the server does not return a job id, a ``RuntimeError`` is raised.
                If ``False`` the response is returned immediately even if it
                contains a job id.
            auto_poll: When ``True`` (default) the client polls queue status
                until the job completes. When ``False`` the method returns as
                soon as the job id is detected.
            poll_interval: Seconds between queue status checks.
            timeout: Optional overall timeout for polling.
            status_hook: Optional awaitable callback invoked after each poll with
                the raw status payload (useful for progress reporting).

        Returns:
            Dictionary that always contains ``mode`` describing execution type.
            For immediate commands: ``{"mode": "immediate", "result": ...}``.
            For queued commands: ``{"mode": "queued", "job_id": ..., "status": ..., "result": ...}``.

        Raises:
            RuntimeError: If expected queue job id is missing or the job fails.
            TimeoutError: When polling exceeds the specified timeout.
        """

        command_result = await self.execute_command(
            command,
            params or {},
            use_cmd_endpoint=use_cmd_endpoint,
        )

        job_id = self._extract_job_identifier(command_result)

        # If expect_queue is explicitly False, return immediate result even if job_id exists
        if expect_queue is False:
            return {
                "mode": "immediate",
                "command": command,
                "result": command_result,
                "queued": False,
            }

        # If expect_queue is True but no job_id, raise error
        if expect_queue is True and job_id is None:
            raise RuntimeError(
                f"Command '{command}' expected to run via queue, but no job_id was returned."
            )

        # If no job_id and expect_queue is None (auto-detect), return immediate result
        if job_id is None:
            return {
                "mode": "immediate",
                "command": command,
                "result": command_result,
                "queued": False,
            }

        if not auto_poll:
            return {
                "mode": "queued",
                "command": command,
                "job_id": job_id,
                "queued": True,
                "status": (
                    command_result.get("status", "queued")
                    if isinstance(command_result, dict)
                    else "queued"
                ),
                "result": command_result,
            }

        deadline = time.monotonic() + timeout if timeout else None

        # Determine which status method to use based on command
        # For embed_queue commands, use embed_job_status instead of queue_get_job_status
        use_embed_status = command == "embed_queue"

        # Helper function to get job status using the correct endpoint
        async def get_job_status(job_id: str) -> Dict[str, Any]:
            """Get job status using appropriate endpoint based on command type."""
            if use_embed_status:
                # Use embed_job_status for embed_queue commands
                response = await self.jsonrpc_call(
                    "embed_job_status", {"job_id": job_id}
                )
                return self._extract_result(response)
            else:
                # Use standard queue_get_job_status for other commands
                return await self.queue_get_job_status(job_id)  # type: ignore[attr-defined,no-any-return]

        # Get initial status with error handling
        try:
            status = await get_job_status(job_id)
            # Check if response indicates error (job not found might mean completed and deleted)
            if isinstance(status, dict) and status.get("success") is False:
                error_msg = status.get("error", {}).get("message", "")
                if "not found" in error_msg.lower():
                    # Job might have completed and been auto-deleted
                    # Return as completed since we can't determine actual status
                    return {
                        "mode": "queued",
                        "command": command,
                        "job_id": job_id,
                        "status": "completed",
                        "result": None,
                        "queued": True,
                        "raw_status": status,
                        "warning": "Job not found in queue (may have been auto-deleted after completion)",
                    }
        except Exception as e:
            raise RuntimeError(f"Failed to get status for job {job_id}: {e}") from e

        # Call status_hook for initial status
        if status_hook:
            try:
                await status_hook(status)
            except TypeError as e:
                raise TypeError(
                    f"status_hook must be an awaitable callable: {e}"
                ) from e

        pending_states = QueueJobStatus.get_pending_states()
        # Extract status from nested structure if needed
        status_str = str(status.get("status", "")).lower()
        if not status_str:
            # Try nested structures: data.status, result.status, result.data.status
            status_str = (
                str(status.get("data", {}).get("status", "")).lower()
                or str(status.get("result", {}).get("status", "")).lower()
                or str(
                    status.get("result", {}).get("data", {}).get("status", "")
                ).lower()
            )

        while status_str in pending_states:
            if deadline and time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Command '{command}' job {job_id} did not finish within {timeout} seconds."
                )

            await asyncio.sleep(poll_interval)

            # Get next status with error handling
            try:
                status = await get_job_status(job_id)
                # Check if response indicates error (job not found might mean completed and deleted)
                if isinstance(status, dict) and status.get("success") is False:
                    error_msg = status.get("error", {}).get("message", "")
                    if "not found" in error_msg.lower():
                        # Job completed and was auto-deleted, exit loop
                        status_str = "completed"
                        break
            except Exception as e:
                raise RuntimeError(
                    f"Failed to get status for job {job_id} during polling: {e}"
                ) from e

            # Extract status from nested structure if needed
            status_str = str(status.get("status", "")).lower()
            if not status_str:
                # Try nested structures: data.status, result.status, result.data.status
                status_str = (
                    str(status.get("data", {}).get("status", "")).lower()
                    or str(status.get("result", {}).get("status", "")).lower()
                    or str(
                        status.get("result", {}).get("data", {}).get("status", "")
                    ).lower()
                )

            # Call status_hook after each poll iteration
            if status_hook:
                try:
                    await status_hook(status)
                except TypeError as e:
                    raise TypeError(
                        f"status_hook must be an awaitable callable: {e}"
                    ) from e

        # Call status_hook for final state
        if status_hook:
            try:
                await status_hook(status)
            except TypeError as e:
                raise TypeError(
                    f"status_hook must be an awaitable callable: {e}"
                ) from e

        # Extract final status from nested structure if needed
        final_status_str = str(status.get("status", "")).lower()
        if not final_status_str:
            # Try nested structures: data.status, result.status, result.data.status
            final_status_str = (
                str(status.get("data", {}).get("status", "")).lower()
                or str(status.get("result", {}).get("status", "")).lower()
                or str(
                    status.get("result", {}).get("data", {}).get("status", "")
                ).lower()
            )

        # Parse and validate final status
        try:
            final_status_enum = QueueJobStatus.from_string(final_status_str)
        except ValueError:
            # Unknown status - treat as completed but add warning
            return {
                "mode": "queued",
                "command": command,
                "job_id": job_id,
                "status": final_status_str or "unknown",
                "result": status.get("result") or status.get("data", {}).get("result"),
                "queued": True,
                "raw_status": status,
                "warning": f"Unknown status value: {final_status_str}",
            }

        # Handle failure states
        if final_status_enum.is_failure():
            raise RuntimeError(
                f"Queued command '{command}' failed (job_id={job_id}, status={final_status_enum.value}): {status}"
            )

        # Handle cancelled states - return with warning
        if final_status_enum.is_cancelled():
            return {
                "mode": "queued",
                "command": command,
                "job_id": job_id,
                "status": final_status_enum.value,
                "result": status.get("result"),
                "queued": True,
                "raw_status": status,
                "warning": f"Job ended with status: {final_status_enum.value}",
            }

        # Extract result - handle nested structures
        result = status.get("result")
        if isinstance(result, dict) and "data" in result:
            result = result.get("data")
        elif isinstance(status, dict) and "data" in status:
            data = status.get("data", {})
            if isinstance(data, dict):
                result = data.get("result", result)

        return {
            "mode": "queued",
            "command": command,
            "job_id": job_id,
            "status": final_status_enum.value,
            "result": result,
            "queued": True,
            "raw_status": status,
        }

    async def execute(
        self,
        method_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute method with schema-based validation and default values.

        This method uses the SchemaRequestGenerator to:
        - Validate required parameters
        - Set default values for missing optional parameters
        - Validate parameter types
        - Execute the command and return deserialized Python object

        Args:
            method_name: Name of the method to execute
            params: Method parameters (optional)

        Returns:
            Deserialized command execution result (Python dict)

        Raises:
            MethodNotFoundError: If method is not found in schema
            RequiredParameterMissingError: If required parameter is missing
            InvalidParameterTypeError: If parameter type is invalid
            InvalidParameterValueError: If parameter value is invalid
            RuntimeError: If command execution fails
        """
        from mcp_proxy_adapter.client.jsonrpc_client.exceptions import (
            MethodNotFoundError,
            RequiredParameterMissingError,
            InvalidParameterTypeError,
            InvalidParameterValueError,
        )

        # Get schema generator
        generator = await self.get_schema_generator_async()

        # Validate and prepare parameters
        try:
            prepared_params = generator.validate_and_prepare_params(method_name, params)
        except (
            MethodNotFoundError,
            RequiredParameterMissingError,
            InvalidParameterTypeError,
            InvalidParameterValueError,
        ):
            raise  # Re-raise schema validation errors

        # Execute command
        result = await self.cmd_call(method_name, prepared_params)

        # Result is already a Python dict (deserialized JSON)
        return result

    async def get_methods(self) -> Dict[str, "MethodInfo"]:
        """
        Get all available methods with their descriptions.

        Returns:
            Dictionary mapping method names to MethodInfo objects
        """
        generator = await self.get_schema_generator_async()
        return generator.get_methods()  # type: ignore[no-any-return]

    async def get_method_description(self, method_name: str) -> str:
        """
        Get detailed description of a method.

        Args:
            method_name: Name of the method

        Returns:
            Detailed description string including:
            - Method name and description
            - Return type and description
            - Parameter details (type, description, default, required)
        """
        generator = await self.get_schema_generator_async()
        return generator.get_method_description(method_name)  # type: ignore[no-any-return]

    async def schema_example(self) -> str:
        """
        Get schema example with detailed descriptions.

        Returns:
            JSON string containing:
            - Full OpenAPI schema
            - Standard description (OpenAPI 3.0.2)
            - Detailed field descriptions
            - All methods with parameter details
        """
        generator = await self.get_schema_generator_async()
        return generator.schema_example()  # type: ignore[no-any-return]

    async def get_commands_list(self) -> Dict[str, Any]:
        """
        Get list of all available commands.

        This method calls the GET /commands endpoint to retrieve
        the list of all registered commands on the server.

        Returns:
            Dictionary containing list of commands and their metadata
        """
        client = await self._get_client()
        response = await client.get(f"{self.base_url}/commands", headers=self.headers)
        response.raise_for_status()
        from typing import cast

        return cast(Dict[str, Any], response.json())

    async def get_heartbeat(self) -> Dict[str, Any]:
        """
        Get server heartbeat information.

        This method calls the GET /heartbeat endpoint to retrieve
        server heartbeat status and metadata.

        Returns:
            Dictionary containing heartbeat status, server name, URL, and timestamp
        """
        client = await self._get_client()
        response = await client.get(f"{self.base_url}/heartbeat", headers=self.headers)
        response.raise_for_status()
        from typing import cast

        return cast(Dict[str, Any], response.json())

    async def list_commands(self) -> Dict[str, Any]:
        """
        List all available commands via JSON-RPC.

        This is an alias for calling the 'list' command via JSON-RPC.
        Equivalent to: execute_command("list", {})

        Returns:
            Dictionary containing list of commands
        """
        return await self.execute_command("list", {})

    async def load_command(self, module_path: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Load a command module.

        Args:
            module_path: Path to the command module to load
            **kwargs: Additional parameters for the load command

        Returns:
            Result of the load operation
        """
        params = {"module_path": module_path, **kwargs}
        return await self.execute_command("load", params)

    async def unload_command(self, command_name: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Unload a command.

        Args:
            command_name: Name of the command to unload
            **kwargs: Additional parameters for the unload command

        Returns:
            Result of the unload operation
        """
        params = {"command": command_name, **kwargs}
        return await self.execute_command("unload", params)

    async def reload_command(self, command_name: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Reload a command.

        Args:
            command_name: Name of the command to reload
            **kwargs: Additional parameters for the reload command

        Returns:
            Result of the reload operation
        """
        params = {"command": command_name, **kwargs}
        return await self.execute_command("reload", params)

    async def get_tool(self, tool_name: str) -> Dict[str, Any]:
        """
        Get tool description.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool description and metadata
        """
        client = await self._get_client()
        response = await client.get(
            f"{self.base_url}/tools/{tool_name}",
            headers=self.headers,
        )
        response.raise_for_status()
        from typing import cast

        return cast(Dict[str, Any], response.json())

    async def execute_tool(
        self,
        tool_name: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool.

        Args:
            tool_name: Name of the tool to execute
            payload: Tool execution parameters

        Returns:
            Tool execution result
        """
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/tools/{tool_name}",
            json=payload or {},
            headers=self.headers,
        )
        response.raise_for_status()
        from typing import cast

        return cast(Dict[str, Any], response.json())

    # Queue-related command helpers

    @staticmethod
    def _extract_job_identifier(command_response: Any) -> Optional[str]:
        """
        Extract job identifier from a command response, if present.
        """
        if not isinstance(command_response, dict):
            return None

        data_section = command_response.get("data", {})
        if not isinstance(data_section, dict):
            data_section = {}

        candidates = [
            command_response.get("job_id"),
            command_response.get("jobId"),
            data_section.get("job_id"),
            data_section.get("jobId"),
        ]

        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate
        return None

    async def get_command_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of a command execution in queue.

        This is a convenience method that calls queue_get_job_status.
        Use this when you have a job_id from a queued command execution.

        Args:
            job_id: Job ID returned from execute_command when command uses queue

        Returns:
            Dictionary containing job status, progress, description, and result
        """
        return await self.queue_get_job_status(job_id)  # type: ignore[attr-defined,no-any-return]

    async def cancel_command(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a command execution in queue.

        This method stops and deletes the job from the queue.
        Equivalent to: queue_stop_job() + queue_delete_job()

        Args:
            job_id: Job ID returned from execute_command when command uses queue

        Returns:
            Result of the cancellation operation
        """
        # Try to stop first, then delete
        try:
            await self.queue_stop_job(job_id)  # type: ignore[attr-defined]
        except Exception:
            pass  # Job might already be stopped or completed
        return await self.queue_delete_job(job_id)  # type: ignore[attr-defined,no-any-return]

    async def list_queued_commands(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        List all commands currently in the queue.

        This method filters jobs to show only command executions (job_type="command_execution").

        Args:
            status: Filter by status (pending, running, completed, failed, stopped)
            limit: Maximum number of jobs to return (default: 100)

        Returns:
            Dictionary containing list of queued commands with their status
        """
        # Use queue_list_jobs with job_type filter for command executions
        result = await self.queue_list_jobs(  # type: ignore[attr-defined]
            status=status, job_type="command_execution"
        )

        # Apply limit if specified
        if limit and "data" in result:
            jobs = result.get("data", {}).get("jobs", [])
            if len(jobs) > limit:
                result["data"]["jobs"] = jobs[:limit]
                result["data"]["total_count"] = limit

        return result  # type: ignore[no-any-return]

    async def list_all_queue_jobs(
        self,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        List all jobs in the queue (commands and other job types).

        Args:
            status: Filter by status (pending, running, completed, failed, stopped)
            job_type: Filter by job type (command_execution, data_processing, api_call)
            limit: Maximum number of jobs to return (default: 100)

        Returns:
            Dictionary containing list of all jobs with their status
        """
        result = await self.queue_list_jobs(  # type: ignore[attr-defined]
            status=status, job_type=job_type
        )

        # Apply limit if specified
        if limit and "data" in result:
            jobs = result.get("data", {}).get("jobs", [])
            if len(jobs) > limit:
                result["data"]["jobs"] = jobs[:limit]
                result["data"]["total_count"] = limit

        return result  # type: ignore[no-any-return]
