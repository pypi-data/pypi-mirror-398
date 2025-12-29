"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Command to list all jobs in the queue.
"""

from typing import Dict, Any

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    QueueJobError,
    get_global_queue_manager,
)


class QueueListJobsCommand(Command):
    """Command to list all jobs in the queue."""
    
    name = "queue_list_jobs"
    descr = "List all jobs in the background queue"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "description": "Filter jobs by status",
                    "enum": [
                        "pending",
                        "running",
                        "completed",
                        "failed",
                        "stopped",
                        "deleted",
                    ],
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of jobs to return",
                    "minimum": 1,
                    "maximum": 1000,
                },
            },
        }

    async def execute(self, status_filter: str = None, limit: int = 100, **kwargs) -> Dict[str, Any]:
        """Execute queue list jobs command."""
        if status_filter is None:
            status_filter = kwargs.get("status_filter")
        if limit is None:
            limit = kwargs.get("limit", 100)
        try:

            # Get global queue manager
            queue_manager = await get_global_queue_manager()

            # List jobs
            jobs = await queue_manager.list_jobs()

            # Apply filters
            if status_filter:
                jobs = [job for job in jobs if job.status == status_filter]

            # Apply limit
            if limit and len(jobs) > limit:
                jobs = jobs[:limit]

            # Convert to dict format
            jobs_data = []
            for job in jobs:
                jobs_data.append(
                    {
                        "job_id": job.job_id,
                        "status": job.status,
                        "progress": job.progress,
                        "description": job.description,
                        "has_result": bool(job.result),
                        "has_error": bool(job.error),
                    }
                )

            return SuccessResult(
                data={
                    "jobs": jobs_data,
                    "total_count": len(jobs_data),
                    "status_filter": status_filter,
                    "limit": limit,
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
                message=f"Failed to list jobs: {str(e)}",
                code=-32603,
            )

