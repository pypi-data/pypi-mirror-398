"""
Integration modules for mcp_proxy_adapter.

This package contains integrations with external systems and libraries
to extend the functionality of the MCP Proxy Adapter framework.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from .queuemgr_integration import (
    QueueManagerIntegration,
    QueueJobBase,
    QueueJobResult,
    QueueJobStatus,
    QueueJobError,
    init_global_queue_manager,
    shutdown_global_queue_manager,
    get_global_queue_manager,
)

__all__ = [
    "QueueManagerIntegration",
    "QueueJobBase", 
    "QueueJobResult",
    "QueueJobStatus",
    "QueueJobError",
    "init_global_queue_manager",
    "shutdown_global_queue_manager",
    "get_global_queue_manager",
]
