"""
Middleware for performance monitoring.
"""

import time
import statistics
from typing import Dict, List, Callable, Awaitable

from fastapi import Request, Response

from mcp_proxy_adapter.core.logging import get_global_logger
from .base import BaseMiddleware


class PerformanceMiddleware(BaseMiddleware):
    """
    Middleware for measuring performance.
    """

    def __init__(self, app):
        """
        Initializes performance middleware.

        Args:
            app: FastAPI application.
        """
        super().__init__(app)
        self.request_times: Dict[str, List[float]] = {}
        self.log_interval = 100  # Log statistics every 100 requests
        self.request_count = 0


    def _log_stats(self) -> None:
        """
        Logs performance statistics.
        """
        get_global_logger().info("Performance statistics:")

        for path, times in self.request_times.items():
            if len(times) > 1:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                # Calculate 95th percentile
                p95_time = sorted(times)[int(len(times) * 0.95)]

                get_global_logger().info(
                    f"Path: {path}, Requests: {len(times)}, "
                    f"Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, "
                    f"Max: {max_time:.3f}s, p95: {p95_time:.3f}s"
                )
