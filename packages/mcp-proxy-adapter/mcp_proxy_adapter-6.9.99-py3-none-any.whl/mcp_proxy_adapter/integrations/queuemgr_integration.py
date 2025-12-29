"""
Queue Manager Integration for MCP Proxy Adapter.

This module provides integration between mcp_proxy_adapter and queuemgr
for managing background jobs and task queues.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

# mypy: disable-error-code=import-untyped

import tempfile
import os
import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any, Type, List

try:
    from queuemgr.jobs.base import QueueJobBase as QueuemgrJobBase
    from queuemgr.core.types import JobStatus as QueuemgrJobStatus
    from queuemgr.core.ipc import update_job_state
    from queuemgr import AsyncQueueSystem
    from queuemgr.exceptions import (
        QueueManagerError,
        JobNotFoundError,
        JobAlreadyExistsError,
        InvalidJobStateError,
        JobExecutionError,
        ProcessControlError,
        ValidationError as QueuemgrValidationError,
        TimeoutError as QueuemgrTimeoutError,
    )
    import queuemgr

    # Check queuemgr version - require 1.0.10+ for completed jobs retention support
    QUEUEMGR_VERSION = getattr(queuemgr, "__version__", "unknown")
    if QUEUEMGR_VERSION != "unknown":
        from packaging import version

        if version.parse(QUEUEMGR_VERSION) < version.parse("1.0.10"):
            raise ImportError(
                f"queuemgr version {QUEUEMGR_VERSION} is too old. "
                f"mcp-proxy-adapter requires queuemgr>=1.0.10 for completed jobs retention support. "
                f"Please upgrade: pip install --upgrade queuemgr>=1.0.10"
            )

    QUEUEMGR_AVAILABLE = True
except ImportError:
    # Fallback for when queuemgr is not available
    QUEUEMGR_AVAILABLE = False
    QueuemgrJobBase = object
    QueuemgrJobStatus = str
    AsyncQueueSystem = None
    update_job_state = None
    QueueManagerError = Exception
    JobNotFoundError = Exception
    JobAlreadyExistsError = Exception
    InvalidJobStateError = Exception
    JobExecutionError = Exception
    ProcessControlError = Exception
    QueuemgrValidationError = Exception
    QueuemgrTimeoutError = Exception

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.errors import MicroserviceError


class QueueJobStatus:
    """Job status constants for queue integration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    DELETED = "deleted"


class QueueJobResult:
    """Result of a queue job execution."""

    def __init__(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        progress: int = 0,
        description: str = "",
    ):
        """
        Initialize queue job result.

        Args:
            job_id: Unique job identifier
            status: Job status
            result: Job result data
            error: Error message if failed
            progress: Progress percentage (0-100)
            description: Job description
        """
        self.job_id = job_id
        self.status = status
        self.result = result or {}
        self.error = error
        self.progress = max(0, min(100, progress))
        self.description = description


class QueueJobError(Exception):
    """Exception raised for queue job errors."""

    def __init__(
        self, job_id: str, message: str, original_error: Optional[Exception] = None
    ):
        """
        Initialize queue job error.

        Args:
            job_id: Job identifier that failed
            message: Error message
            original_error: Original exception that caused the error
        """
        super().__init__(f"Job {job_id}: {message}")
        self.job_id = job_id
        self.original_error = original_error


class QueueJobBase(QueuemgrJobBase):
    """
    Base class for MCP Proxy Adapter queue jobs.

    This class extends the queuemgr QueueJobBase to provide
    MCP-specific helper methods for result, status, and progress handling.

    This class is designed to work with multiprocessing spawn mode (required for CUDA).
    It implements pickle serialization methods to avoid module reference errors.
    """

    _STATUS_MAP = {
        "pending": QueuemgrJobStatus.PENDING,
        "queued": QueuemgrJobStatus.PENDING,
        "running": QueuemgrJobStatus.RUNNING,
        "in_progress": QueuemgrJobStatus.RUNNING,
        "completed": QueuemgrJobStatus.COMPLETED,
        "success": QueuemgrJobStatus.COMPLETED,
        "failed": QueuemgrJobStatus.ERROR,
        "error": QueuemgrJobStatus.ERROR,
        "stopped": QueuemgrJobStatus.INTERRUPTED,
        "interrupted": QueuemgrJobStatus.INTERRUPTED,
        "deleted": QueuemgrJobStatus.INTERRUPTED,
    }

    def __init__(self, job_id: str, params: Dict[str, Any]):
        """
        Initialize MCP queue job.

        Args:
            job_id: Unique job identifier
            params: Job parameters
        """
        if not QUEUEMGR_AVAILABLE:
            raise MicroserviceError(
                "queuemgr is not available. Install it with: pip install queuemgr>=1.0.8"
            )

        super().__init__(job_id, params)
        self.logger = get_global_logger()
        self.mcp_params = params

    def __getstate__(self) -> Dict[str, Any]:
        """
        Prepare minimal pickle state without non-serializable objects.

        This method is called when the object is pickled. It removes
        references to modules (like logger) that cannot be pickled.

        Returns:
            Dictionary with serializable state
        """
        state: Dict[str, Any] = self.__dict__.copy()
        # Remove logger to avoid module serialization issues
        # Logger will be recreated in child process via __setstate__
        state.pop("logger", None)
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """
        Restore state after unpickling - recreate logger in child process.

        This method is called when the object is unpickled in the child process.
        It restores the state and recreates the logger to avoid module reference issues.

        Args:
            state: Dictionary with serialized state
        """
        self.__dict__.update(state)
        # Recreate logger in child process to avoid module reference issues
        self.logger = get_global_logger()

    def run(self) -> None:
        """Execute job logic. Subclasses must override this method."""
        raise NotImplementedError("Queue jobs must implement run()")

    def execute(self) -> None:
        """Adapter entrypoint invoked by queuemgr worker processes."""
        self.run()

    def set_status(self, status: str) -> None:
        """Update job status in shared state."""
        if not self._shared_state or not update_job_state:
            return
        update_job_state(
            self._shared_state,
            status=self._convert_status(status),
        )

    def set_description(self, description: str) -> None:
        """Update job description."""
        if not self._shared_state or not update_job_state:
            return
        update_job_state(self._shared_state, description=description[:1024])

    def set_progress(self, progress: int) -> None:
        """Update job progress ensuring it stays within 0-100 range."""
        if not self._shared_state or not update_job_state:
            return
        safe_progress = max(0, min(100, int(progress)))
        update_job_state(self._shared_state, progress=safe_progress)

    def set_mcp_result(
        self, result: Dict[str, Any], status: Optional[str] = None
    ) -> None:
        """Store job result payload and update status if provided."""
        status_value = status or result.get("status") or "completed"
        self.set_result(result)
        self.set_status(status_value)
        if "description" in result:
            self.set_description(str(result["description"]))

    def set_mcp_error(self, message: str, status: str = "failed") -> None:
        """Record job error details and switch status to error."""
        self.logger.error(f"Queue job {self.job_id} error: {message}")
        self.set_status(status)
        self.set_description(message)
        self.set_result({"status": "error", "message": message})

    def _convert_status(self, status: str) -> QueuemgrJobStatus:
        """Convert human-readable status string into JobStatus enum."""
        if isinstance(status, QueuemgrJobStatus):
            return status
        normalized = (status or "pending").strip().lower()
        return self._STATUS_MAP.get(normalized, QueuemgrJobStatus.PENDING)


class QueueManagerIntegration:
    """
    Queue Manager Integration for MCP Proxy Adapter.

    This class provides a high-level interface for managing
    background jobs using the queuemgr system.
    """

    def __init__(
        self,
        registry_path: Optional[str] = None,
        shutdown_timeout: float = 30.0,
        max_concurrent_jobs: int = 10,
        in_memory: bool = True,
        max_queue_size: Optional[int] = None,
        per_job_type_limits: Optional[Dict[str, int]] = None,
        completed_job_retention_seconds: int = 3600,
    ):
        """
        Initialize queue manager integration.

        Args:
            registry_path: Path to the queue registry file (ignored if in_memory=True)
            shutdown_timeout: Timeout for graceful shutdown
            max_concurrent_jobs: Maximum number of concurrent jobs
            in_memory: If True, use temporary file that is deleted on shutdown (default: True)
            max_queue_size: Maximum number of jobs in queue. If reached, oldest job is deleted before adding new one.
                           If None, no limit (default: None)
            per_job_type_limits: Dict mapping job_type to max count. If limit is reached for a job type,
                                oldest job of that type is deleted before adding new one. If None, no per-type limits (default: None)
            completed_job_retention_seconds: How long to keep completed jobs before cleanup (default: 21600 = 6 hours).
                                           Set to 0 to keep completed jobs indefinitely.
        """
        if not QUEUEMGR_AVAILABLE:
            raise MicroserviceError(
                "queuemgr is not available. Install it with: pip install queuemgr>=1.0.8"
            )

        self.in_memory = in_memory
        self._temp_file: Optional[Any] = None

        if in_memory:
            # Create temporary file that will be deleted on shutdown
            self._temp_file = tempfile.NamedTemporaryFile(
                mode="w+", suffix=".jsonl", prefix="mcp_queue_", delete=False
            )
            self.registry_path = self._temp_file.name
            self.logger = get_global_logger()
            self.logger.debug(f"Using in-memory queue registry: {self.registry_path}")
        else:
            self.registry_path = registry_path or "mcp_queue_registry.jsonl"
            self.logger = get_global_logger()

        self.shutdown_timeout = shutdown_timeout
        self.max_concurrent_jobs = max_concurrent_jobs
        self.max_queue_size = max_queue_size
        self.per_job_type_limits = per_job_type_limits
        self.completed_job_retention_seconds = completed_job_retention_seconds
        self._queue_system: Optional[AsyncQueueSystem] = None
        self._is_running = False
        self._cleanup_task: Optional[Any] = None

    async def start(self) -> None:
        """Start the queue manager integration."""
        if self._is_running:
            self.logger.warning("Queue manager integration is already running")
            return

        try:
            # Use absolute path for registry
            registry_path_str = str(Path(self.registry_path).resolve())

            if not self.in_memory:
                # Ensure registry directory exists for persistent storage
                registry_path_obj = Path(registry_path_str)
                if registry_path_obj.parent and not registry_path_obj.parent.exists():
                    registry_path_obj.parent.mkdir(parents=True, exist_ok=True)
                    self.logger.info(
                        f"Created registry directory: {registry_path_obj.parent}"
                    )
            else:
                # For in-memory mode, ensure temp file is closed so queuemgr can use it
                if self._temp_file:
                    self._temp_file.close()
                self.logger.debug(
                    f"Using in-memory queue registry: {registry_path_str}"
                )

            # Note: We don't pass max_queue_size and per_job_type_limits to queuemgr
            # because we want to control deletion logic ourselves to preserve completed jobs
            # We'll handle limits manually in add_job method
            self._queue_system = AsyncQueueSystem(
                registry_path=registry_path_str,
                shutdown_timeout=self.shutdown_timeout,
                max_queue_size=None,  # Disable automatic deletion - we handle it manually
                per_job_type_limits=None,  # Disable automatic deletion - we handle it manually
            )
            await self._queue_system.start()
            self._is_running = True

            # Start periodic cleanup task for old completed jobs
            if self.completed_job_retention_seconds > 0:
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
                self.logger.debug(
                    f"Started periodic cleanup task (retention: {self.completed_job_retention_seconds}s)"
                )

            if self.in_memory:
                self.logger.info(
                    "✅ Queue manager integration started (in-memory mode)"
                )
            else:
                self.logger.info(
                    f"✅ Queue manager integration started (registry: {registry_path_str})"
                )

        except Exception as e:
            self.logger.error(f"❌ Failed to start queue manager integration: {e}")
            raise MicroserviceError(f"Failed to start queue manager: {str(e)}")

    async def stop(self) -> None:
        """Stop the queue manager integration."""
        if not self._is_running:
            self.logger.warning("Queue manager integration is not running")
            return

        try:
            if self._queue_system:
                await self._queue_system.stop()
            self._is_running = False

            # Clean up temporary file for in-memory mode
            if (
                self.in_memory
                and self.registry_path
                and os.path.exists(self.registry_path)
            ):
                try:
                    os.unlink(self.registry_path)
                    self.logger.debug(
                        f"Deleted temporary registry file: {self.registry_path}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to delete temporary registry file: {e}"
                    )

            self.logger.info("✅ Queue manager integration stopped")

        except Exception as e:
            self.logger.error(f"❌ Failed to stop queue manager integration: {e}")
            raise MicroserviceError(f"Failed to stop queue manager: {str(e)}")

    def is_running(self) -> bool:
        """Check if the queue manager integration is running."""
        return self._is_running and self._queue_system is not None

    async def add_job(
        self,
        job_class: Type[QueueJobBase],
        job_id: str,
        params: Dict[str, Any],
    ) -> QueueJobResult:
        """
        Add a job to the queue.

        Args:
            job_class: Job class to instantiate
            job_id: Unique job identifier
            params: Job parameters

        Returns:
            QueueJobResult with job information

        Raises:
            QueueJobError: If job cannot be added
        """
        if not self.is_running():
            raise QueueJobError(
                job_id,
                "Queue manager is not running. "
                "Please ensure queue manager is initialized in server startup event. "
                "Use: await init_global_queue_manager() in your startup event.",
            )

        try:
            queue_system = self._require_queue_system(job_id)

            # Check limits and clean up old non-completed jobs if needed
            # (completed jobs are preserved until retention period expires)
            await self._enforce_limits_before_add()

            await queue_system.add_job(job_class, job_id, params)
            return QueueJobResult(
                job_id=job_id,
                status=QueueJobStatus.PENDING,
                description="Job added to queue",
            )

        except JobAlreadyExistsError as e:
            raise QueueJobError(job_id, f"Job already exists: {str(e)}", e)
        except QueuemgrValidationError as e:
            raise QueueJobError(job_id, f"Invalid job parameters: {str(e)}", e)
        except Exception as e:
            raise QueueJobError(job_id, f"Failed to add job: {str(e)}", e)

    async def start_job(self, job_id: str) -> QueueJobResult:
        """
        Start a job in the queue.

        Args:
            job_id: Job identifier to start

        Returns:
            QueueJobResult with job status

        Raises:
            QueueJobError: If job cannot be started
        """
        if not self.is_running():
            raise QueueJobError(
                job_id,
                "Queue manager is not running. "
                "Please ensure queue manager is initialized in server startup event. "
                "Use: await init_global_queue_manager() in your startup event.",
            )

        try:
            queue_system = self._require_queue_system(job_id)
            await queue_system.start_job(job_id)
            return QueueJobResult(
                job_id=job_id, status=QueueJobStatus.RUNNING, description="Job started"
            )

        except JobNotFoundError as e:
            raise QueueJobError(job_id, f"Job not found: {str(e)}", e)
        except InvalidJobStateError as e:
            raise QueueJobError(job_id, f"Invalid job state: {str(e)}", e)
        except Exception as e:
            raise QueueJobError(job_id, f"Failed to start job: {str(e)}", e)

    async def stop_job(self, job_id: str) -> QueueJobResult:
        """
        Stop a job in the queue.

        Args:
            job_id: Job identifier to stop

        Returns:
            QueueJobResult with job status

        Raises:
            QueueJobError: If job cannot be stopped
        """
        if not self.is_running():
            raise QueueJobError(
                job_id,
                "Queue manager is not running. "
                "Please ensure queue manager is initialized in server startup event. "
                "Use: await init_global_queue_manager() in your startup event.",
            )

        try:
            queue_system = self._require_queue_system(job_id)
            await queue_system.stop_job(job_id)
            return QueueJobResult(
                job_id=job_id, status=QueueJobStatus.STOPPED, description="Job stopped"
            )

        except JobNotFoundError as e:
            raise QueueJobError(job_id, f"Job not found: {str(e)}", e)
        except (ProcessControlError, QueuemgrTimeoutError) as e:
            fallback_status = await self._wait_for_terminal_status(job_id)
            if fallback_status is not None:
                self.logger.warning(
                    "Stop job %s reported %s but job is already in status=%s. Treating as success.",
                    job_id,
                    e.__class__.__name__,
                    fallback_status,
                )
                return QueueJobResult(
                    job_id=job_id,
                    status=fallback_status,
                    description="Job already finished",
                )
            raise QueueJobError(job_id, f"Process control error: {str(e)}", e)
        except Exception as e:
            raise QueueJobError(job_id, f"Failed to stop job: {str(e)}", e)

    async def delete_job(self, job_id: str) -> QueueJobResult:
        """
        Delete a job from the queue.

        Args:
            job_id: Job identifier to delete

        Returns:
            QueueJobResult with job status

        Raises:
            QueueJobError: If job cannot be deleted
        """
        if not self.is_running():
            raise QueueJobError(
                job_id,
                "Queue manager is not running. "
                "Please ensure queue manager is initialized in server startup event. "
                "Use: await init_global_queue_manager() in your startup event.",
            )

        try:
            queue_system = self._require_queue_system(job_id)
            await queue_system.delete_job(job_id)
            return QueueJobResult(
                job_id=job_id, status=QueueJobStatus.DELETED, description="Job deleted"
            )

        except JobNotFoundError as e:
            raise QueueJobError(job_id, f"Job not found: {str(e)}", e)
        except (ProcessControlError, QueuemgrTimeoutError) as e:
            # queuemgr may still complete the operation even when a timeout/IPC error is reported.
            # Confirm whether the job disappeared before surfacing the error to callers.
            job_removed = await self._confirm_job_removed(queue_system, job_id)
            if job_removed:
                self.logger.warning(
                    "Delete job %s reported %s but job is already gone. Treating as success.",
                    job_id,
                    e.__class__.__name__,
                )
                return QueueJobResult(
                    job_id=job_id,
                    status=QueueJobStatus.DELETED,
                    description="Job deleted (confirmed after timeout)",
                )
            raise QueueJobError(job_id, f"Process control error: {str(e)}", e)
        except Exception as e:
            raise QueueJobError(job_id, f"Failed to delete job: {str(e)}", e)

    async def get_job_status(self, job_id: str) -> QueueJobResult:
        """
        Get the status of a job.

        Args:
            job_id: Job identifier to get status for

        Returns:
            QueueJobResult with job status and information

        Raises:
            QueueJobError: If job status cannot be retrieved
        """
        if not self.is_running():
            raise QueueJobError(
                job_id,
                "Queue manager is not running. "
                "Please ensure queue manager is initialized in server startup event. "
                "Use: await init_global_queue_manager() in your startup event.",
            )

        try:
            queue_system = self._require_queue_system(job_id)
            status_data = await queue_system.get_job_status(job_id)
            normalized = self._normalize_job_record(status_data)

            # Convert queuemgr status to MCP status
            mcp_status = self._convert_status(normalized.get("status", "unknown"))

            # Log for debugging completed jobs
            if mcp_status in (QueueJobStatus.COMPLETED, QueueJobStatus.FAILED):
                self.logger.debug(
                    f"Retrieved completed/failed job {job_id}: status={mcp_status}, "
                    f"has_result={bool(normalized.get('result'))}, "
                    f"completed_at={normalized.get('completed_at')}, "
                    f"finished_at={normalized.get('finished_at')}"
                )

            return QueueJobResult(
                job_id=normalized.get("job_id", job_id),
                status=mcp_status,
                result=normalized.get("result", {}),
                error=normalized.get("error"),
                progress=normalized.get("progress", 0),
                description=normalized.get("description", ""),
            )

        except JobNotFoundError as e:
            # Log for debugging - check if job was completed and should still exist
            self.logger.warning(
                f"Job {job_id} not found in queue. This may indicate queuemgr deleted it automatically."
            )
            raise QueueJobError(job_id, f"Job not found: {str(e)}", e)
        except Exception as e:
            raise QueueJobError(job_id, f"Failed to get job status: {str(e)}", e)

    async def get_job_logs(self, job_id: str) -> Dict[str, Any]:
        """
        Get stdout and stderr logs for a job.

        Args:
            job_id: Job identifier to get logs for

        Returns:
            Dictionary containing:
            - stdout: List of stdout log lines
            - stderr: List of stderr log lines

        Raises:
            QueueJobError: If job logs cannot be retrieved
        """
        if not self.is_running():
            raise QueueJobError(
                job_id,
                "Queue manager is not running. "
                "Please ensure queue manager is initialized in server startup event. "
                "Use: await init_global_queue_manager() in your startup event.",
            )

        try:
            queue_system = self._require_queue_system(job_id)
            logs_data = await queue_system.get_job_logs(job_id)

            # Normalize logs data - queuemgr returns Dict[str, List[str]]
            # with keys 'stdout' and 'stderr'
            stdout = logs_data.get("stdout", [])
            stderr = logs_data.get("stderr", [])

            # Ensure we return lists
            if not isinstance(stdout, list):
                stdout = [str(stdout)] if stdout else []
            if not isinstance(stderr, list):
                stderr = [str(stderr)] if stderr else []

            return {
                "job_id": job_id,
                "stdout": stdout,
                "stderr": stderr,
                "stdout_lines": len(stdout),
                "stderr_lines": len(stderr),
            }

        except JobNotFoundError as e:
            raise QueueJobError(job_id, f"Job not found: {str(e)}", e)
        except Exception as e:
            raise QueueJobError(job_id, f"Failed to get job logs: {str(e)}", e)

    async def list_jobs(self) -> List[QueueJobResult]:
        """
        List all jobs in the queue.

        Returns:
            List of QueueJobResult objects

        Raises:
            QueueJobError: If jobs cannot be listed
        """
        if not self.is_running():
            raise QueueJobError(
                "",
                "Queue manager is not running. "
                "Please ensure queue manager is initialized in server startup event. "
                "Use: await init_global_queue_manager() in your startup event.",
            )

        try:
            queue_system = self._require_queue_system()
            jobs_data = await queue_system.list_jobs()

            results = []
            for job_data in jobs_data:
                normalized = self._normalize_job_record(job_data)
                mcp_status = self._convert_status(normalized.get("status", "unknown"))
                results.append(
                    QueueJobResult(
                        job_id=normalized.get("job_id", "unknown"),
                        status=mcp_status,
                        result=normalized.get("result", {}),
                        error=normalized.get("error"),
                        progress=normalized.get("progress", 0),
                        description=normalized.get("description", ""),
                    )
                )

            return results

        except Exception as e:
            raise QueueJobError("", f"Failed to list jobs: {str(e)}", e)

    def _convert_status(self, queuemgr_status: Any) -> str:
        """
        Convert queuemgr status to MCP status.

        Args:
            queuemgr_status: Status from queuemgr (can be string, JobStatus enum, or int)

        Returns:
            MCP-compatible status
        """
        # Handle JobStatus enum from queuemgr
        if hasattr(queuemgr_status, "name"):
            # It's an enum, get its name
            status_str = queuemgr_status.name.lower()
        elif hasattr(queuemgr_status, "value"):
            # It's an enum with value, get the value
            status_str = str(queuemgr_status.value).lower()
        elif isinstance(queuemgr_status, int):
            # It's an integer status code
            status_map = {
                0: "pending",
                1: "running",
                2: "completed",
                3: "failed",
                4: "stopped",
                5: "deleted",
            }
            status_str = status_map.get(queuemgr_status, "pending")
        else:
            # It's a string
            status_str = str(queuemgr_status).lower()

        status_mapping = {
            "pending": QueueJobStatus.PENDING,
            "running": QueueJobStatus.RUNNING,
            "completed": QueueJobStatus.COMPLETED,
            "failed": QueueJobStatus.FAILED,
            "stopped": QueueJobStatus.STOPPED,
            "deleted": QueueJobStatus.DELETED,
            # Handle queuemgr enum names
            "queuemgrjobstatus.pending": QueueJobStatus.PENDING,
            "queuemgrjobstatus.running": QueueJobStatus.RUNNING,
            "queuemgrjobstatus.completed": QueueJobStatus.COMPLETED,
            "queuemgrjobstatus.error": QueueJobStatus.FAILED,
            "queuemgrjobstatus.interrupted": QueueJobStatus.STOPPED,
        }

        return status_mapping.get(status_str, QueueJobStatus.PENDING)

    async def get_queue_health(self) -> Dict[str, Any]:
        """
        Get queue system health information.

        Returns:
            Dictionary with health information

        Raises:
            QueueJobError: If health cannot be retrieved
        """
        if not self.is_running():
            raise QueueJobError(
                "",
                "Queue manager is not running. "
                "Please ensure queue manager is initialized in server startup event. "
                "Use: await init_global_queue_manager() in your startup event.",
            )

        try:
            jobs = await self.list_jobs()
            return {
                "status": "healthy" if self.is_running() else "unhealthy",
                "running": self.is_running(),
                "total_jobs": len(jobs),
                "pending_jobs": len(
                    [j for j in jobs if j.status == QueueJobStatus.PENDING]
                ),
                "running_jobs": len(
                    [j for j in jobs if j.status == QueueJobStatus.RUNNING]
                ),
                "completed_jobs": len(
                    [j for j in jobs if j.status == QueueJobStatus.COMPLETED]
                ),
                "failed_jobs": len(
                    [j for j in jobs if j.status == QueueJobStatus.FAILED]
                ),
                "registry_path": self.registry_path,
                "max_concurrent_jobs": self.max_concurrent_jobs,
            }
        except Exception as e:
            raise QueueJobError("", f"Failed to get queue health: {str(e)}", e)

    @staticmethod
    def _normalize_job_record(job_data: Any) -> Dict[str, Any]:
        """
        Convert queuemgr job record (dict or dataclass) into dictionary form.
        """
        normalized: Dict[str, Any]
        if isinstance(job_data, dict):
            normalized = job_data.copy()
        else:
            normalized = {}
            # Extract all possible fields from queuemgr job record
            for attr in (
                "job_id",
                "status",
                "progress",
                "description",
                "result",
                "error",
                "created_at",
                "updated_at",
                "completed_at",
                "finished_at",
                "started_at",
                "job_type",
            ):
                if hasattr(job_data, attr):
                    value = getattr(job_data, attr)
                    # Convert JobStatus enum to string representation
                    if attr == "status" and hasattr(value, "name"):
                        normalized[attr] = value.name.lower()
                    elif attr == "status" and hasattr(value, "value"):
                        normalized[attr] = str(value.value)
                    else:
                        normalized[attr] = value

        # Ensure required fields exist
        if "description" not in normalized:
            normalized["description"] = ""
        if "progress" not in normalized:
            normalized["progress"] = 0
        normalized.setdefault("result", {})
        normalized.setdefault("error", None)

        # Convert status to string if it's still an object
        if "status" in normalized and not isinstance(normalized["status"], (str, int)):
            status_val = normalized["status"]
            if hasattr(status_val, "name"):
                normalized["status"] = status_val.name.lower()
            elif hasattr(status_val, "value"):
                normalized["status"] = str(status_val.value)
            else:
                normalized["status"] = str(status_val).lower()

        return normalized

    def _require_queue_system(self, job_id: str = "") -> AsyncQueueSystem:
        """
        Ensure queue system backend is initialized before use.
        """
        if self._queue_system is None:
            raise QueueJobError(
                job_id,
                "Queue system backend is not initialized. "
                "Ensure init_global_queue_manager() completed successfully.",
            )
        return self._queue_system

    async def _confirm_job_removed(
        self, queue_system: Optional[AsyncQueueSystem], job_id: str
    ) -> bool:
        """
        Verify whether job is already absent from the queue after a timeout/IPC error.

        Args:
            queue_system: Active queue system instance.
            job_id: Identifier of the job being deleted.

        Returns:
            True if job is no longer present, False otherwise.
        """
        if queue_system is None:
            return False

        try:
            await queue_system.get_job_status(job_id)
        except JobNotFoundError:
            return True
        except Exception:
            return False
        return False

    async def _wait_for_terminal_status(
        self, job_id: str, timeout: float = 20.0, interval: float = 0.5
    ) -> Optional[str]:
        """
        Poll job status for a short period waiting for a terminal state.

        Args:
            job_id: Identifier of the job being inspected.
            timeout: Maximum number of seconds to wait.
            interval: Delay between polling attempts.

        Returns:
            Terminal job status if job reached completion, otherwise None.
        """
        deadline = time.monotonic() + timeout
        terminal_statuses = {
            QueueJobStatus.COMPLETED,
            QueueJobStatus.FAILED,
            QueueJobStatus.STOPPED,
            QueueJobStatus.DELETED,
        }

        while time.monotonic() < deadline:
            try:
                job_result = await self.get_job_status(job_id)
            except QueueJobError as status_error:
                message = str(status_error).lower()
                if "not found" in message:
                    return QueueJobStatus.DELETED
                await asyncio.sleep(interval)
                continue

            if job_result.status in terminal_statuses:
                return job_result.status

            await asyncio.sleep(interval)

        return None

    async def _enforce_limits_before_add(self) -> None:
        """
        Enforce max_queue_size and per_job_type_limits by deleting old non-completed jobs.
        Completed jobs are preserved until retention period expires.
        """
        if self.max_queue_size is None and self.per_job_type_limits is None:
            return  # No limits to enforce

        try:
            all_jobs = await self.list_jobs()

            # Separate completed and non-completed jobs
            # (completed jobs are preserved, only non-completed jobs count toward limits)
            non_completed_jobs = [
                j
                for j in all_jobs
                if j.status not in (QueueJobStatus.COMPLETED, QueueJobStatus.FAILED)
            ]

            # Check global max_queue_size (only count non-completed jobs)
            if (
                self.max_queue_size is not None
                and len(non_completed_jobs) >= self.max_queue_size
            ):
                # Delete oldest non-completed job
                non_completed_jobs.sort(key=lambda j: getattr(j, "created_at", 0))
                oldest_job = non_completed_jobs[0]
                try:
                    await self.delete_job(oldest_job.job_id)
                    self.logger.debug(
                        f"Deleted oldest non-completed job {oldest_job.job_id} to enforce max_queue_size={self.max_queue_size}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to delete job {oldest_job.job_id} for limit enforcement: {e}"
                    )

            # Check per_job_type_limits
            if self.per_job_type_limits:
                # Group non-completed jobs by type
                jobs_by_type: Dict[str, List[QueueJobResult]] = {}
                for job in non_completed_jobs:
                    job_type = getattr(job, "job_type", "default")
                    if job_type not in jobs_by_type:
                        jobs_by_type[job_type] = []
                    jobs_by_type[job_type].append(job)

                # Enforce limits per type
                for job_type, limit in self.per_job_type_limits.items():
                    type_jobs = jobs_by_type.get(job_type, [])
                    if len(type_jobs) >= limit:
                        # Delete oldest job of this type
                        type_jobs.sort(key=lambda j: getattr(j, "created_at", 0))
                        oldest_job = type_jobs[0]
                        try:
                            await self.delete_job(oldest_job.job_id)
                            self.logger.debug(
                                f"Deleted oldest {job_type} job {oldest_job.job_id} to enforce per_job_type_limits[{job_type}]={limit}"
                            )
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to delete job {oldest_job.job_id} for limit enforcement: {e}"
                            )

        except Exception as e:
            self.logger.warning(f"Error enforcing queue limits: {e}")

    async def _periodic_cleanup(self) -> None:
        """
        Periodically clean up old completed jobs that exceed retention period.
        Runs every hour or retention_period/6, whichever is smaller.
        """
        if self.completed_job_retention_seconds <= 0:
            return  # Retention disabled

        # Run cleanup every hour or retention_period/6, whichever is smaller
        cleanup_interval = min(3600, max(60, self.completed_job_retention_seconds // 6))

        if not self._is_running:
            return

        while self._is_running:
            try:
                await asyncio.sleep(cleanup_interval)

                current_time = time.time()
                all_jobs = await self.list_jobs()

                deleted_count = 0
                for job in all_jobs:
                    if job.status not in (
                        QueueJobStatus.COMPLETED,
                        QueueJobStatus.FAILED,
                    ):
                        continue  # Only clean up completed/failed jobs

                    # Get job completion time from job data
                    # queuemgr stores completion time in job record
                    try:
                        if self._queue_system is None:
                            continue
                        job_status_data = await self._queue_system.get_job_status(
                            job.job_id
                        )
                        job_normalized = self._normalize_job_record(job_status_data)

                        # Try to get completion time from various fields
                        completed_at = (
                            job_normalized.get("completed_at")
                            or job_normalized.get("finished_at")
                            or job_normalized.get("updated_at")
                        )

                        if completed_at:
                            # If it's a timestamp
                            if isinstance(completed_at, (int, float)):
                                age_seconds = current_time - completed_at
                            else:
                                # Skip if we can't determine age
                                continue
                        else:
                            # If no completion time, skip (shouldn't happen for completed jobs)
                            continue

                        # Delete if older than retention period
                        if age_seconds >= self.completed_job_retention_seconds:
                            try:
                                await self.delete_job(job.job_id)
                                deleted_count += 1
                                self.logger.debug(
                                    f"Cleaned up old completed job {job.job_id} (age: {age_seconds:.0f}s)"
                                )
                            except Exception as e:
                                self.logger.warning(
                                    f"Failed to cleanup job {job.job_id}: {e}"
                                )

                    except Exception as e:
                        self.logger.debug(
                            f"Could not determine age for job {job.job_id}: {e}"
                        )
                        continue

                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old completed job(s)")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {e}")
                # Continue running even on error


# Global queue manager instance
_global_queue_manager: Optional[QueueManagerIntegration] = None


async def init_global_queue_manager(
    registry_path: Optional[str] = None,
    shutdown_timeout: float = 30.0,
    max_concurrent_jobs: int = 10,
    in_memory: bool = True,
    max_queue_size: Optional[int] = None,
    per_job_type_limits: Optional[Dict[str, int]] = None,
    completed_job_retention_seconds: int = 21600,
) -> QueueManagerIntegration:
    """
    Initialize global queue manager instance and auto-register queue commands.

    Args:
        registry_path: Path to the queue registry file (ignored if in_memory=True)
        shutdown_timeout: Timeout for graceful shutdown
        max_concurrent_jobs: Maximum number of concurrent jobs
        in_memory: If True, use temporary file that is deleted on shutdown (default: True)
        max_queue_size: Maximum number of non-completed jobs in queue. If reached, oldest non-completed job is deleted before adding new one.
                       Completed jobs are preserved until retention period expires. If None, no limit (default: None)
        per_job_type_limits: Dict mapping job_type to max count. If limit is reached for a job type,
                            oldest non-completed job of that type is deleted before adding new one. If None, no per-type limits (default: None)
        completed_job_retention_seconds: How long to keep completed jobs before cleanup (default: 21600 = 6 hours).
                                       Set to 0 to keep completed jobs indefinitely.

    Returns:
        Initialized QueueManagerIntegration instance

    Raises:
        MicroserviceError: If initialization fails
    """
    global _global_queue_manager

    if _global_queue_manager is not None and _global_queue_manager.is_running():
        return _global_queue_manager

    # Auto-register queue management commands
    try:
        from mcp_proxy_adapter.commands.queue import (
            QueueAddJobCommand,
            QueueStartJobCommand,
            QueueStopJobCommand,
            QueueDeleteJobCommand,
            QueueGetJobStatusCommand,
            QueueGetJobLogsCommand,
            QueueListJobsCommand,
            QueueHealthCommand,
        )
        from mcp_proxy_adapter.commands.command_registry import registry

        logger = get_global_logger()

        # Register queue commands only if not already registered
        queue_commands = [
            (QueueAddJobCommand, "queue_add_job"),
            (QueueStartJobCommand, "queue_start_job"),
            (QueueStopJobCommand, "queue_stop_job"),
            (QueueDeleteJobCommand, "queue_delete_job"),
            (QueueGetJobStatusCommand, "queue_get_job_status"),
            (QueueGetJobLogsCommand, "queue_get_job_logs"),
            (QueueListJobsCommand, "queue_list_jobs"),
            (QueueHealthCommand, "queue_health"),
        ]

        for cmd_class, cmd_name in queue_commands:
            try:
                # Check if command is already registered by trying to fetch it
                already_registered = True
                try:
                    registry.get_command(cmd_name)
                except KeyError:
                    already_registered = False

                if not already_registered:
                    registry.register(cmd_class, "builtin")
                    logger.debug(f"Auto-registered queue command: {cmd_name}")
                else:
                    logger.debug(f"Queue command already registered: {cmd_name}")
            except Exception as e:
                logger.warning(f"Failed to register queue command {cmd_name}: {e}")
    except Exception as e:
        logger = get_global_logger()
        logger.warning(f"Failed to auto-register queue commands: {e}")

    _global_queue_manager = QueueManagerIntegration(
        registry_path=registry_path,
        shutdown_timeout=shutdown_timeout,
        max_concurrent_jobs=max_concurrent_jobs,
        in_memory=in_memory,
        max_queue_size=max_queue_size,
        per_job_type_limits=per_job_type_limits,
        completed_job_retention_seconds=completed_job_retention_seconds,
    )
    await _global_queue_manager.start()
    return _global_queue_manager


async def shutdown_global_queue_manager() -> None:
    """
    Shutdown global queue manager instance.

    Raises:
        MicroserviceError: If shutdown fails
    """
    global _global_queue_manager

    if _global_queue_manager is not None:
        await _global_queue_manager.stop()
        _global_queue_manager = None


async def get_global_queue_manager() -> QueueManagerIntegration:
    """
    Get global queue manager instance.

    Returns:
        QueueManagerIntegration instance

    Raises:
        QueueJobError: If queue manager is not initialized or not running
    """
    if _global_queue_manager is None:
        raise QueueJobError(
            "",
            "Queue manager is not initialized. "
            "Please call init_global_queue_manager() in your startup event.",
        )

    if not _global_queue_manager.is_running():
        raise QueueJobError(
            "",
            "Queue manager is not running. "
            "Please ensure queue manager is initialized in server startup event. "
            "Use: await init_global_queue_manager() in your startup event.",
        )

    return _global_queue_manager
