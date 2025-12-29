"""Queue management helpers for JsonRpcClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from mcp_proxy_adapter.client.jsonrpc_client.transport import JsonRpcTransport


class QueueApiMixin(JsonRpcTransport):
    """Mixin with queue-related JSON-RPC shortcuts."""

    async def queue_health(self) -> Dict[str, Any]:
        response = await self.jsonrpc_call("queue_health", {})
        return self._extract_result(response)

    async def queue_add_job(
        self,
        job_type: str,
        job_id: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload = {"job_type": job_type, "job_id": job_id, "params": params}
        response = await self.jsonrpc_call("queue_add_job", payload)
        return self._extract_result(response)

    async def queue_start_job(self, job_id: str) -> Dict[str, Any]:
        response = await self.jsonrpc_call("queue_start_job", {"job_id": job_id})
        return self._extract_result(response)

    async def queue_stop_job(self, job_id: str) -> Dict[str, Any]:
        response = await self.jsonrpc_call("queue_stop_job", {"job_id": job_id})
        return self._extract_result(response)

    async def queue_delete_job(self, job_id: str) -> Dict[str, Any]:
        response = await self.jsonrpc_call("queue_delete_job", {"job_id": job_id})
        return self._extract_result(response)

    async def queue_get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status with automatic endpoint detection.

        This method automatically detects which status endpoint to use based on
        the job type. For service-specific queue commands (e.g., embed_queue),
        it tries the service-specific status endpoint first (e.g., embed_job_status),
        then falls back to the standard queue_get_job_status endpoint if the job
        is not found or the endpoint doesn't exist.

        Args:
            job_id: Job identifier to get status for

        Returns:
            Dictionary containing job status information

        Raises:
            RuntimeError: If job is not found in both endpoints or other error occurs
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"[queue_get_job_status] Starting auto-detection for job_id: {job_id}")
        
        # Try service-specific status endpoints first (e.g., embed_job_status for embed_queue)
        # This allows auto-detection without requiring the command that created the job
        try:
            logger.debug(f"[queue_get_job_status] Trying embed_job_status for job_id: {job_id}")
            response = await self.jsonrpc_call("embed_job_status", {"job_id": job_id})
            result = self._extract_result(response)
            logger.debug(f"[queue_get_job_status] embed_job_status response: {result}")
            
            # Check if result indicates job was found
            # If success is False, fall back to standard endpoint (embed_job_status is only for embed_queue jobs)
            if isinstance(result, dict) and result.get("success") is False:
                error_msg = result.get("error", {}).get("message", "")
                logger.debug(f"[queue_get_job_status] embed_job_status returned False, error: {error_msg}")
                # For any error from embed_job_status, fall back to standard endpoint
                # This is correct because embed_job_status is only for embed_queue jobs,
                # standard jobs should use queue_get_job_status
                logger.debug(f"[queue_get_job_status] embed_job_status failed, falling back to standard endpoint")
                pass
            else:
                # Job found in embed_job_status, return result
                logger.debug(f"[queue_get_job_status] Job found in embed_job_status, returning: {result}")
                return result
        except RuntimeError as e:
            # Check if error is "job not found" or "method not found" - fall back to standard endpoint
            error_msg = str(e).lower()
            logger.debug(f"[queue_get_job_status] RuntimeError from embed_job_status: {error_msg}")
            if "not found" in error_msg or "method" in error_msg:
                # Job not found in embed_job_status or method doesn't exist, try standard endpoint
                logger.debug(f"[queue_get_job_status] Method/job not found, falling back to standard endpoint")
                pass
            else:
                # Other error from embed_job_status, re-raise it
                logger.error(f"[queue_get_job_status] RuntimeError from embed_job_status (not recoverable): {e}")
                raise
        except Exception as e:
            # Any other exception (network errors, etc.) - fall back to standard endpoint
            logger.debug(f"[queue_get_job_status] Exception from embed_job_status (falling back): {type(e).__name__}: {e}")
            pass

        # Fall back to standard queue_get_job_status endpoint
        logger.debug(f"[queue_get_job_status] Falling back to standard queue_get_job_status for job_id: {job_id}")
        response = await self.jsonrpc_call("queue_get_job_status", {"job_id": job_id})
        result = self._extract_result(response)
        logger.debug(f"[queue_get_job_status] Standard endpoint response: {result}")
        return result

    async def queue_get_job_logs(self, job_id: str) -> Dict[str, Any]:
        """
        Get stdout and stderr logs for a job.

        Args:
            job_id: Job identifier to get logs for

        Returns:
            Dictionary containing:
            - job_id: Job identifier
            - stdout: List of stdout log lines
            - stderr: List of stderr log lines
            - stdout_lines: Number of stdout lines
            - stderr_lines: Number of stderr lines
        """
        response = await self.jsonrpc_call("queue_get_job_logs", {"job_id": job_id})
        return self._extract_result(response)

    async def queue_list_jobs(
        self,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if job_type:
            params["job_type"] = job_type
        response = await self.jsonrpc_call("queue_list_jobs", params)
        return self._extract_result(response)
