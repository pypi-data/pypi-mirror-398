"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Queue management commands package.
"""

from .add_job_command import QueueAddJobCommand
from .start_job_command import QueueStartJobCommand
from .stop_job_command import QueueStopJobCommand
from .delete_job_command import QueueDeleteJobCommand
from .get_status_command import QueueGetJobStatusCommand
from .get_logs_command import QueueGetJobLogsCommand
from .list_jobs_command import QueueListJobsCommand
from .health_command import QueueHealthCommand
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

# Auto-register all queue commands
from mcp_proxy_adapter.commands.command_registry import registry

_queue_commands = [
    QueueAddJobCommand,
    QueueStartJobCommand,
    QueueStopJobCommand,
    QueueDeleteJobCommand,
    QueueGetJobStatusCommand,
    QueueGetJobLogsCommand,
    QueueListJobsCommand,
    QueueHealthCommand,
]

for cmd_class in _queue_commands:
    try:
        registry.register(cmd_class, "builtin")
    except Exception:
        # Command may already be registered, ignore
        pass

__all__ = [
    "QueueAddJobCommand",
    "QueueStartJobCommand",
    "QueueStopJobCommand",
    "QueueDeleteJobCommand",
    "QueueGetJobStatusCommand",
    "QueueGetJobLogsCommand",
    "QueueListJobsCommand",
    "QueueHealthCommand",
    "DataProcessingJob",
    "FileOperationJob",
    "ApiCallJob",
    "CustomJob",
    "LongRunningJob",
    "BatchProcessingJob",
    "FileDownloadJob",
    "CommandExecutionJob",
    "PeriodicLoggingJob",
]

