"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Command to start a job in the queue.
"""

from typing import Dict, Any

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    QueueJobError,
    get_global_queue_manager,
)
from mcp_proxy_adapter.core.errors import ValidationError


class QueueStartJobCommand(Command):
    """Command to start a job in the queue."""
    
    name = "queue_start_job"
    descr = "Start a job in the background queue"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job identifier to start",
                    "minLength": 1,
                }
            },
            "required": ["job_id"],
        }

    async def execute(self, job_id: str = None, **kwargs) -> Dict[str, Any]:
        """Execute queue start job command."""
        if not job_id:
            job_id = kwargs.get("job_id")
        try:

            if not job_id:
                raise ValidationError("job_id is required")

            # Get global queue manager
            queue_manager = await get_global_queue_manager()

            # Start job
            result = await queue_manager.start_job(job_id)

            return SuccessResult(
                data={
                    "message": f"Job {job_id} started successfully",
                    "job_id": job_id,
                    "status": result.status,
                    "description": result.description,
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
                message=f"Failed to start job: {str(e)}",
                code=-32603,
            )

