"""Queue management commands for MCP Proxy Adapter.

This module is kept for backward compatibility.
New code should import from mcp_proxy_adapter.commands.queue instead.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

# Re-export from new module structure for backward compatibility
from .queue import (
    QueueAddJobCommand,
    QueueStartJobCommand,
    QueueStopJobCommand,
    QueueDeleteJobCommand,
    QueueGetJobStatusCommand,
    QueueListJobsCommand,
    QueueHealthCommand,
    DataProcessingJob,
    FileOperationJob,
    ApiCallJob,
    CustomJob,
    LongRunningJob,
    BatchProcessingJob,
    FileDownloadJob,
    CommandExecutionJob,
)

__all__ = [
    "QueueAddJobCommand",
    "QueueStartJobCommand",
    "QueueStopJobCommand",
    "QueueDeleteJobCommand",
    "QueueGetJobStatusCommand",
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
]
