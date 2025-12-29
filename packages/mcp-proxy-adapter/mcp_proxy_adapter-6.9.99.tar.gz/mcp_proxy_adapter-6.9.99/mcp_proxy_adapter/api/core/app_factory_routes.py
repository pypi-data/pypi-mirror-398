"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Route registration helper for AppFactory.
"""

from typing import Any, Dict, List, Union

from fastapi import Body, FastAPI, Request

from mcp_proxy_adapter.api.handlers import (
    handle_json_rpc,
    handle_batch_json_rpc,
    get_server_health,
    get_commands_list,
    handle_heartbeat,
)

try:
    from mcp_proxy_adapter.api.schemas import (
        JsonRpcRequest,
        JsonRpcSuccessResponse,
        JsonRpcErrorResponse,
        HealthResponse,
        CommandListResponse,
    )
except Exception:  # pragma: no cover - fallback for simplified environments
    JsonRpcRequest = Dict[str, Any]  # type: ignore
    JsonRpcSuccessResponse = Dict[str, Any]  # type: ignore
    JsonRpcErrorResponse = Dict[str, Any]  # type: ignore
    HealthResponse = Dict[str, Any]  # type: ignore
    CommandListResponse = Dict[str, Any]  # type: ignore

try:
    from mcp_proxy_adapter.api.tools import get_tool_description, execute_tool
except Exception:  # pragma: no cover - optional dependency
    get_tool_description = None
    execute_tool = None


def setup_routes(app: FastAPI) -> None:
    """
    Register built-in API routes.

    Args:
        app: FastAPI application.
    """

    @app.get("/health", response_model=HealthResponse)
    async def health():  # type: ignore
        return await get_server_health()  # type: ignore[misc]

    @app.get("/commands", response_model=CommandListResponse)
    async def commands():  # type: ignore
        return await get_commands_list()  # type: ignore[misc]

    @app.get("/heartbeat")
    async def heartbeat():  # type: ignore
        """Built-in heartbeat endpoint for proxy health checks."""
        return await handle_heartbeat()  # type: ignore[misc]

    @app.post(
        "/api/jsonrpc",
        response_model=Union[JsonRpcSuccessResponse, JsonRpcErrorResponse],
    )
    async def jsonrpc(request: JsonRpcRequest):  # type: ignore
        return await handle_json_rpc(request.dict())  # type: ignore[misc]

    @app.post(
        "/api/jsonrpc/batch",
        response_model=List[Union[JsonRpcSuccessResponse, JsonRpcErrorResponse]],
    )
    async def jsonrpc_batch(requests: List[JsonRpcRequest]):  # type: ignore
        payload = [req.dict() for req in requests]
        return await handle_batch_json_rpc(payload)  # type: ignore[misc]

    @app.post("/tools/{tool_name}")
    async def execute_tool_endpoint(
        tool_name: str,
        request: Request,
        payload: Dict[str, Any] = Body(default_factory=dict),
    ):
        if execute_tool is None:
            raise ValueError("Tool execution is not available in this environment")
        return await execute_tool(tool_name, request, payload)

    @app.get("/tools/{tool_name}")
    async def get_tool_endpoint(tool_name: str):
        if get_tool_description is None:
            raise ValueError("Tool description is not available in this environment")
        return await get_tool_description(tool_name)


