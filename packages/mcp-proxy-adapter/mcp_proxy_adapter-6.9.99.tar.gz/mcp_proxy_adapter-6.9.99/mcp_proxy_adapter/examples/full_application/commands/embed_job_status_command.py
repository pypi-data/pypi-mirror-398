"""
Embed Job Status Command - Check status of jobs created by embed_queue.

This command demonstrates how to check status of jobs created through
embed_queue command. This is the service-specific status endpoint
that queue_get_job_status tries first before falling back to standard
queue_get_job_status endpoint.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    get_global_queue_manager,
    QueueJobError,
    QueueJobResult,
)


class EmbedJobStatusResult(SuccessResult):
    """Result class for embed_job_status command."""

    def __init__(self, job_id: str, status: str, job_data: Dict[str, Any]):
        """
        Initialize embed job status result.

        Args:
            job_id: Job identifier
            status: Job status
            job_data: Full job data
        """
        data = {
            "job_id": job_id,
            "status": status,
            **job_data,
        }
        super().__init__(data=data)


class EmbedJobStatusCommand(Command):
    """
    Embed job status command - checks status of jobs created by embed_queue.

    This is a service-specific status endpoint that queue_get_job_status
    tries first before falling back to standard queue_get_job_status.
    """

    name = "embed_job_status"
    descr = "Get status of a job created by embed_queue command"

    async def execute(self, job_id: str, **kwargs) -> EmbedJobStatusResult:
        """
        Execute embed_job_status command.

        Checks the status of a job created by embed_queue.
        This endpoint is tried first by queue_get_job_status before
        falling back to standard queue_get_job_status.

        Args:
            job_id: Job ID to check status for
            **kwargs: Additional parameters

        Returns:
            EmbedJobStatusResult with job status and data
        """
        if not job_id:
            return ErrorResult(
                message="job_id parameter is required",
                code=-32602,
            )

        try:
            # Get global queue manager
            queue_manager = await get_global_queue_manager()

            # Get job status - returns QueueJobResult object, not dict
            job_status: QueueJobResult = await queue_manager.get_job_status(job_id)

            if job_status is None:
                return ErrorResult(
                    message=f"Job {job_id} not found",
                    code=-32001,
                    details={"job_id": job_id},
                )

            # Extract status and data from QueueJobResult object
            status = job_status.status or "unknown"
            job_data = {
                "job_id": job_status.job_id or job_id,
                "status": status,
                "result": job_status.result,
                "error": job_status.error,
                "progress": job_status.progress,
                "description": job_status.description,
            }

            return EmbedJobStatusResult(
                job_id=job_id,
                status=status,
                job_data=job_data,
            )

        except QueueJobError as e:
            return ErrorResult(
                message=f"Queue job error: {str(e)}",
                code=-32603,
                details={"job_id": job_id},
            )
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get job status: {str(e)}",
                code=-32603,
                details={"job_id": job_id},
            )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID to check status for",
                },
            },
            "required": ["job_id"],
            "additionalProperties": False,
        }
