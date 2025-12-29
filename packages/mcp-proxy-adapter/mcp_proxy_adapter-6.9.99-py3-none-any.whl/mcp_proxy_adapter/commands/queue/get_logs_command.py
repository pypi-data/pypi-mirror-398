"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Command to get logs (stdout/stderr) of a job.
"""

from typing import Dict, Any

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    QueueJobError,
    get_global_queue_manager,
)
from mcp_proxy_adapter.core.errors import ValidationError


class QueueGetJobLogsCommand(Command):
    """Command to get stdout and stderr logs of a job."""

    name = "queue_get_job_logs"
    descr = "Get stdout and stderr logs of a job"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job identifier to get logs for",
                    "minLength": 1,
                }
            },
            "required": ["job_id"],
        }

    async def execute(self, job_id: str = None, **kwargs) -> Dict[str, Any]:
        """Execute queue get job logs command."""
        if not job_id:
            job_id = kwargs.get("job_id")
        try:

            if not job_id:
                raise ValidationError("job_id is required")

            # Get global queue manager
            queue_manager = await get_global_queue_manager()

            # Get job logs
            logs = await queue_manager.get_job_logs(job_id)

            return SuccessResult(
                data={
                    "job_id": logs["job_id"],
                    "stdout": logs["stdout"],
                    "stderr": logs["stderr"],
                    "stdout_lines": logs["stdout_lines"],
                    "stderr_lines": logs["stderr_lines"],
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
                message=f"Failed to get job logs: {str(e)}",
                code=-32603,
            )

