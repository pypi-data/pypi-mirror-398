"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Command to get the status of a job.
"""

from typing import Dict, Any

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    QueueJobError,
    get_global_queue_manager,
)
from mcp_proxy_adapter.core.errors import ValidationError


class QueueGetJobStatusCommand(Command):
    """Command to get the status of a job."""
    
    name = "queue_get_job_status"
    descr = "Get the status and details of a job"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job identifier to get status for",
                    "minLength": 1,
                }
            },
            "required": ["job_id"],
        }

    async def execute(self, job_id: str = None, **kwargs) -> Dict[str, Any]:
        """Execute queue get job status command."""
        if not job_id:
            job_id = kwargs.get("job_id")
        try:

            if not job_id:
                raise ValidationError("job_id is required")

            # Get global queue manager
            queue_manager = await get_global_queue_manager()

            # Get job status
            result = await queue_manager.get_job_status(job_id)

            return SuccessResult(
                data={
                    "job_id": result.job_id,
                    "status": result.status,
                    "progress": result.progress,
                    "description": result.description,
                    "result": result.result,
                    "error": result.error,
                }
            )

        except QueueJobError as e:
            return ErrorResult(
                message=f"Queue job error: {str(e)}",
                code=-32603,
                details={"job_id": getattr(e, "job_id", "unknown")},
            )
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get job status: {str(e)}",
                code=-32603,
            )

