"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

HTTP handlers for the MCP Proxy Adapter API.
Provides JSON-RPC handling and health/commands endpoints.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

from fastapi import Request

from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.core.errors import (
    MicroserviceError,
    InvalidRequestError,
    MethodNotFoundError,
    InternalError,
)
from mcp_proxy_adapter.core.logging import get_global_logger, RequestLogger


async def execute_command(
    command_name: str,
    params: Optional[Dict[str, Any]],
    request_id: Optional[str] = None,
    request: Optional[Request] = None,
) -> Dict[str, Any]:
    """Execute a registered command by name with parameters.

    If command has use_queue=True, command will be executed via queue and job_id will be returned.
    Otherwise, command will be executed synchronously and result will be returned.

    Raises MethodNotFoundError if command is not found.
    Wraps unexpected exceptions into InternalError.
    """
    logger = RequestLogger(__name__, request_id) if request_id else get_global_logger()

    try:
        logger.info(f"Executing command: {command_name}")

        # Resolve command
        try:
            command_class = registry.get_command(command_name)
        except Exception:
            raise MethodNotFoundError(f"Method not found: {command_name}")

        # Build context (user info if middleware set state)
        context: Dict[str, Any] = {}
        if request is not None and hasattr(request, "state"):
            user_id = getattr(request.state, "user_id", None)
            user_role = getattr(request.state, "user_role", None)
            user_roles = getattr(request.state, "user_roles", None)
            if user_id or user_role or user_roles:
                context["user"] = {
                    "id": user_id,
                    "role": user_role,
                    "roles": user_roles or [],
                }

        # Check if command should be executed via queue
        use_queue = getattr(command_class, "use_queue", False)

        if use_queue:
            # Execute via queue - enqueue quickly and offload heavy work to worker process.
            # HTTP/JSON-RPC layer should only:
            #   1) validate params
            #   2) enqueue CommandExecutionJob
            #   3) return job_id to client as fast as possible
            #
            # All heavy processing must happen inside the queue worker process so that
            # long-running pipelines do not block the initial HTTP request or hit
            # fixed 30s timeouts in queuemgr start_job / HTTP client.
            try:
                from mcp_proxy_adapter.integrations.queuemgr_integration import (
                    get_global_queue_manager,
                )
                from mcp_proxy_adapter.commands.queue.jobs import CommandExecutionJob
                from mcp_proxy_adapter.commands.hooks import hooks
                import uuid

                queue_manager = await get_global_queue_manager()
                job_id = str(uuid.uuid4())

                # Get list of modules to import in child process
                # This ensures commands are available in spawn mode
                auto_import_modules = hooks.get_auto_import_modules()

                # Prepare job parameters - heavy processing happens in CommandExecutionJob.run()
                job_params = {
                    "command": command_name,
                    "params": params or {},
                    "context": context,
                    "auto_import_modules": auto_import_modules,  # Pass modules to child process
                }

                # Add job to queue (fast, no heavy work here)
                await queue_manager.add_job(CommandExecutionJob, job_id, job_params)

                # Start job in background to avoid blocking HTTP request on queuemgr timeouts
                async def _start_job_background() -> None:
                    try:
                        await queue_manager.start_job(job_id)
                        logger.info(
                            "Background start for job %s (command=%s) completed",
                            job_id,
                            command_name,
                        )
                    except Exception as start_exc:
                        # Important: do not fail the original HTTP request if queuemgr
                        # reports a timeout or IPC error. The job may still transition
                        # to a terminal state and be observable via queue_get_job_status.
                        logger.warning(
                            "Background start for job %s (command=%s) failed: %s",
                            job_id,
                            command_name,
                            start_exc,
                        )

                asyncio.create_task(_start_job_background())

                # Return job_id instead of result as soon as job is enqueued.
                # Client code (execute_command_unified with auto_poll=True) will
                # use queue_get_job_status(job_id) to monitor progress and result.
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "pending",
                    "message": f"Command '{command_name}' has been queued for execution",
                }

            except Exception as exc:
                logger.exception(f"Failed to queue command '{command_name}': {exc}")
                raise InternalError(f"Failed to queue command: {str(exc)}")

        # Execute synchronously (default behavior)
        # Ensure params is a dict, not None
        if params is None:
            params = {}
        started_at = time.time()
        try:
            result_obj = await asyncio.wait_for(
                command_class.run(**params, context=context), timeout=30.0
            )
        except asyncio.TimeoutError:
            elapsed = time.time() - started_at
            raise InternalError(f"Command timed out after {elapsed:.2f}s")

        elapsed = time.time() - started_at
        logger.info(f"Command '{command_name}' executed in {elapsed:.3f}s")
        return result_obj.to_dict()

    except MicroserviceError:
        # Re-raise domain-specific errors so that JSON-RPC layer can format them properly.
        raise
    except Exception as exc:
        logger.exception(f"Unhandled error in command '{command_name}': {exc}")
        raise InternalError("Internal error", data={"error": str(exc)})


async def handle_batch_json_rpc(
    batch_requests: List[Dict[str, Any]], request: Optional[Request] = None
) -> List[Dict[str, Any]]:
    """Handle batch JSON-RPC requests."""
    responses: List[Dict[str, Any]] = []
    request_id = getattr(request.state, "request_id", None) if request else None
    for item in batch_requests:
        responses.append(await handle_json_rpc(item, request_id, request))
    return responses


async def handle_json_rpc(
    request_data: Dict[str, Any],
    request_id: Optional[str] = None,
    request: Optional[Request] = None,
) -> Dict[str, Any]:
    """Handle a single JSON-RPC request with strict 2.0 compatibility.

    Also supports simplified form: {"command": "echo", "params": {...}}.
    """
    # Keep handler logic very thin – all heavy work is delegated to execute_command().
    method: Optional[str]
    params: Dict[str, Any]
    json_rpc_id: Any

    if "jsonrpc" in request_data:
        if request_data.get("jsonrpc") != "2.0":
            return _error_response(
                InvalidRequestError("Invalid Request: jsonrpc must be '2.0'"),
                request_data.get("id"),
            )
        method = request_data.get("method")
        params = request_data.get("params") or {}
        json_rpc_id = request_data.get("id")
        if not method:
            return _error_response(
                InvalidRequestError("Invalid Request: method is required"), json_rpc_id
            )
    else:
        # Simplified
        method = request_data.get("command")
        params = request_data.get("params") or {}
        json_rpc_id = request_data.get("id", 1)
        if not method:
            return _error_response(
                InvalidRequestError("Invalid Request: command is required"), json_rpc_id
            )

    result = await execute_command(method, params, request_id, request)
    return {"jsonrpc": "2.0", "result": result, "id": json_rpc_id}


def _error_response(error: MicroserviceError, request_id: Any) -> Dict[str, Any]:
    """
    Create JSON-RPC error response.

    Args:
        error: Microservice error instance
        request_id: Request ID from original request

    Returns:
        Dictionary with JSON-RPC error response format
    """
    return {"jsonrpc": "2.0", "error": error.to_dict(), "id": request_id}


async def get_server_health() -> Dict[str, Any]:
    """Return server health info."""
    import os
    import platform
    import sys
    import psutil
    from datetime import datetime

    process = psutil.Process(os.getpid())
    start_time = datetime.fromtimestamp(process.create_time())
    uptime_seconds = (datetime.now() - start_time).total_seconds()
    mem = process.memory_info().rss / (1024 * 1024)

    return {
        "status": "ok",
        "model": "mcp-proxy-adapter",
        "version": "1.0.0",
        "uptime": uptime_seconds,
        "components": {
            "system": {
                "python_version": sys.version,
                "platform": platform.platform(),
                "cpu_count": os.cpu_count(),
            },
            "process": {
                "pid": os.getpid(),
                "memory_usage_mb": mem,
                "start_time": start_time.isoformat(),
            },
            "commands": {"registered_count": len(registry.get_all_commands())},
        },
    }


async def get_commands_list() -> Dict[str, Dict[str, Any]]:
    """Return list of registered commands with schemas."""
    result: Dict[str, Dict[str, Any]] = {}
    for name, cls in registry.get_all_commands().items():
        schema = cls.get_schema()
        result[name] = {
            "name": name,
            "schema": schema,
            "description": schema.get("description", ""),
        }
    return result


async def handle_heartbeat() -> Dict[str, Any]:
    """Handle heartbeat request from proxy.

    This endpoint is used by the proxy to check if the server is alive.
    Returns server status and metadata.
    """
    logger = get_global_logger()
    logger.debug("💓 Heartbeat request received")

    # Get server info from config if available
    server_name = "mcp-proxy-adapter"
    server_url = "http://localhost:8080"

    try:
        from mcp_proxy_adapter.config import get_config

        cfg = get_config()
        if hasattr(cfg, "model") and hasattr(cfg.model, "server"):
            server_config = cfg.model.server
            if hasattr(server_config, "name"):
                server_name = server_config.name or server_name
            if hasattr(server_config, "host") and hasattr(server_config, "port"):
                protocol = (
                    "https"
                    if (
                        hasattr(server_config, "ssl")
                        and server_config.ssl
                        and server_config.ssl.enabled
                    )
                    else "http"
                )
                host = server_config.host or "localhost"
                port = server_config.port or 8080
                server_url = f"{protocol}://{host}:{port}"
    except Exception:
        pass  # Use defaults if config is not available

    return {
        "status": "ok",
        "server_name": server_name,
        "server_url": server_url,
        "timestamp": time.time(),
    }
