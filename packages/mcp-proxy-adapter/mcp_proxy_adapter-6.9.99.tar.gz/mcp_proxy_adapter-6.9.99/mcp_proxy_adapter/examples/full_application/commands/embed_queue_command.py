"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Embed Queue Command - Example command that uses queue system.

This command demonstrates how to create jobs through the queue system
and how embed_job_status can be used to check job status.

NOTE: This command does NOT use use_queue=True itself, but it creates
queue jobs for other commands. Commands executed via this command
will run in child processes if they have use_queue=True.

For commands that use use_queue=True directly, see long_running_command.py
for registration requirements in spawn mode.
"""

from typing import Any, Dict
import uuid

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    get_global_queue_manager,
    QueueJobError,
)
from mcp_proxy_adapter.commands.queue.jobs import CommandExecutionJob


class EmbedQueueResult(SuccessResult):
    """Result class for embed_queue command."""

    def __init__(self, job_id: str, command: str, status: str):
        """
        Initialize embed queue result.

        Args:
            job_id: Job identifier
            command: Command name that was queued
            status: Job status
        """
        data = {
            "job_id": job_id,
            "command": command,
            "status": status,
            "message": f"Command '{command}' queued successfully with job_id: {job_id}",
        }
        super().__init__(data=data)


class EmbedQueueCommand(Command):
    """
    Embed queue command - creates jobs through queue system.

    This command demonstrates how to create jobs using queue_add_job
    internally. Jobs created by this command should be checked using
    embed_job_status endpoint.
    """

    name = "embed_queue"
    descr = "Queue a command for execution through the queue system"

    async def execute(
        self,
        command: str,
        params: Dict[str, Any] = None,
        job_id: str = None,
        **kwargs,
    ) -> EmbedQueueResult:
        """
        Execute embed_queue command.

        Creates a job through queue_add_job with type command_execution.
        The job will be checked using embed_job_status endpoint.

        Args:
            command: Command name to execute
            params: Command parameters
            job_id: Optional job ID (auto-generated if not provided)
            **kwargs: Additional parameters

        Returns:
            EmbedQueueResult with job_id and status
        """
        if params is None:
            params = kwargs.get("params", {})

        if not command:
            return ErrorResult(
                message="command parameter is required",
                code=-32602,
            )

        try:
            # Generate job_id if not provided
            if not job_id:
                job_id = f"embed_{uuid.uuid4().hex[:12]}"

            # Get global queue manager
            queue_manager = await get_global_queue_manager()

            # Create job parameters for command_execution
            job_params = {
                "command": command,
                "params": params or {},
            }

            # Add job to queue using CommandExecutionJob
            result = await queue_manager.add_job(
                CommandExecutionJob, job_id, job_params
            )

            return EmbedQueueResult(
                job_id=job_id,
                command=command,
                status=result.status,
            )

        except QueueJobError as e:
            return ErrorResult(
                message=f"Queue job error: {str(e)}",
                code=-32603,
                details={"job_id": getattr(e, "job_id", "unknown")},
            )
        except Exception as e:
            return ErrorResult(
                message=f"Failed to queue command: {str(e)}",
                code=-32603,
            )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command name to execute",
                },
                "params": {
                    "type": "object",
                    "description": "Command parameters",
                    "default": {},
                },
                "job_id": {
                    "type": "string",
                    "description": "Optional job ID (auto-generated if not provided)",
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        }
