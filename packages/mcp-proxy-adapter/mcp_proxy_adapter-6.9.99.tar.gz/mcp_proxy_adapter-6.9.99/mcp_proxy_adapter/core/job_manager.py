"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Simple in-memory job manager for long-running demo commands.
Not for production use.
"""

import asyncio
import uuid
from typing import Any, Dict, Optional, Awaitable


class JobRecord:
    """
    Record for tracking job execution status.
    
    Attributes:
        task: Asyncio task running the job
        status: Current job status ("running", "completed", "failed")
        result: Job result if completed
        error: Error message if failed
    """
    def __init__(self, task: asyncio.Task):
        """
        Initialize job record.
        
        Args:
            task: Asyncio task running the job
        """
        self.task = task
        self.status = "running"
        self.result: Optional[Any] = None
        self.error: Optional[str] = None


_jobs: Dict[str, JobRecord] = {}


def enqueue_coroutine(coro: Awaitable[Any]) -> str:
    """
    Enqueue a coroutine for background execution.
    
    Args:
        coro: Coroutine to execute in background
        
    Returns:
        Job ID string for tracking the job
    """
    job_id = str(uuid.uuid4())
    task = asyncio.create_task(_run_job(job_id, coro))
    _jobs[job_id] = JobRecord(task)
    return job_id


async def _run_job(job_id: str, coro):
    """
    Run a job coroutine and update its status.
    
    Args:
        job_id: Job identifier
        coro: Coroutine to execute
    """
    rec = _jobs[job_id]
    try:
        rec.result = await coro
        rec.status = "completed"
    except Exception as exc:  # noqa: BLE001
        rec.error = str(exc)
        rec.status = "failed"


def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get status of a job by ID.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Dictionary with job status information
    """
    rec = _jobs.get(job_id)
    if not rec:
        return {"exists": False}
    return {
        "exists": True,
        "status": rec.status,
        "done": rec.task.done(),
        "result": rec.result,
        "error": rec.error,
    }


