"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Command to add a job to the queue.
"""

from typing import Dict, Any

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    QueueJobError,
    get_global_queue_manager,
)
from mcp_proxy_adapter.core.errors import ValidationError
from .jobs import (
    DataProcessingJob,
    FileOperationJob,
    ApiCallJob,
    CustomJob,
    LongRunningJob,
    BatchProcessingJob,
    FileDownloadJob,
    CommandExecutionJob,
    PeriodicLoggingJob,
)


class QueueAddJobCommand(Command):
    """Command to add a job to the queue."""
    
    name = "queue_add_job"
    descr = "Add a job to the background queue"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "job_type": {
                    "type": "string",
                    "description": "Type of job to add",
                    "enum": [
                        "data_processing",
                        "file_operation",
                        "api_call",
                        "custom",
                        "long_running",
                        "batch_processing",
                        "file_download",
                        "command_execution",
                        "periodic_logging",
                    ],
                },
                "command": {
                    "type": "string",
                    "description": "Command name to execute (for command_execution job type)",
                },
                "job_id": {
                    "type": "string",
                    "description": "Unique job identifier",
                    "minLength": 1,
                },
                "params": {
                    "type": "object",
                    "description": "Job-specific parameters",
                    "properties": {
                        "data": {"type": "object", "description": "Data to process"},
                        "operation": {"type": "string", "description": "Operation type"},
                        "file_path": {
                            "type": "string",
                            "description": "File path for file operations",
                        },
                        "url": {"type": "string", "description": "URL for API calls"},
                        "method": {
                            "type": "string",
                            "description": "HTTP method for API calls",
                        },
                        "headers": {"type": "object", "description": "HTTP headers"},
                        "timeout": {
                            "type": "number",
                            "description": "Job timeout in seconds",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Job priority (1-10)",
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration for long-running jobs (seconds)",
                        },
                        "task_type": {
                            "type": "string",
                            "description": "Type of task for long-running jobs",
                        },
                        "batch_size": {
                            "type": "integer",
                            "description": "Batch size for batch processing jobs",
                        },
                        "items": {
                            "type": "array",
                            "description": "Items to process in batch jobs",
                        },
                        "file_size": {
                            "type": "integer",
                            "description": "File size for download jobs (bytes)",
                        },
                        "command": {
                            "type": "string",
                            "description": "Command name to execute (for command_execution job type)",
                        },
                        "params": {
                            "type": "object",
                            "description": "Command parameters (for command_execution job type)",
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Duration in minutes for periodic_logging jobs (default: 5)",
                        },
                        "interval_seconds": {
                            "type": "integer",
                            "description": "Interval in seconds between log messages for periodic_logging jobs (default: 60)",
                        },
                        "message_prefix": {
                            "type": "string",
                            "description": "Prefix for log messages in periodic_logging jobs",
                        },
                    },
                },
            },
            "required": ["job_type", "job_id", "params"],
        }

    async def execute(self, job_type: str = None, job_id: str = None, params: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Execute queue add job command."""
        if params is None:
            params = kwargs.get("params", {})
        try:
            if not job_type:
                job_type = kwargs.get("job_type")
            if not job_id:
                job_id = kwargs.get("job_id")
            job_params = params or {}

            if not job_type or not job_id:
                raise ValidationError("job_type and job_id are required")

            # Get global queue manager
            queue_manager = await get_global_queue_manager()

            # Map job types to classes
            job_classes = {
                "data_processing": DataProcessingJob,
                "file_operation": FileOperationJob,
                "api_call": ApiCallJob,
                "custom": CustomJob,
                "long_running": LongRunningJob,
                "batch_processing": BatchProcessingJob,
                "file_download": FileDownloadJob,
                "command_execution": CommandExecutionJob,
                "periodic_logging": PeriodicLoggingJob,
            }
            
            # For command_execution, validate command parameter
            if job_type == "command_execution":
                command_name = job_params.get("command")
                if not command_name:
                    raise ValidationError("command parameter is required for command_execution job type")
                
                # CRITICAL: Pass auto_import_modules to CommandExecutionJob
                # This ensures custom commands are available in child processes (spawn mode)
                # Child processes need to import modules to trigger auto-registration
                try:
                    from mcp_proxy_adapter.commands.hooks import hooks
                    auto_import_modules = hooks.get_auto_import_modules()
                    if auto_import_modules:
                        job_params["auto_import_modules"] = auto_import_modules
                except Exception as e:
                    # Log but don't fail - job may still work if modules are in PYTHONPATH
                    from mcp_proxy_adapter.core.logging import get_global_logger
                    logger = get_global_logger()
                    logger.warning(
                        f"Failed to get auto_import_modules for CommandExecutionJob: {e}. "
                        f"Custom commands may not be available in child process."
                    )

            if job_type not in job_classes:
                raise ValidationError(f"Unknown job type: {job_type}")

            # Add job to queue
            result = await queue_manager.add_job(
                job_classes[job_type], job_id, job_params
            )

            return SuccessResult(
                data={
                    "message": f"Job {job_id} added successfully",
                    "job_id": job_id,
                    "job_type": job_type,
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
                message=f"Failed to add job: {str(e)}",
                code=-32603,
            )

