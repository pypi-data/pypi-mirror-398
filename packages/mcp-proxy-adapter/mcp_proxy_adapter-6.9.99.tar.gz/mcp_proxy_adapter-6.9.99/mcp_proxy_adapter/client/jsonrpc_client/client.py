"""Facade JsonRpcClient combining transport and feature mixins.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from typing import Optional

from mcp_proxy_adapter.client.jsonrpc_client.command_api import CommandApiMixin
from mcp_proxy_adapter.client.jsonrpc_client.proxy_api import ProxyApiMixin
from mcp_proxy_adapter.client.jsonrpc_client.queue_api import QueueApiMixin


class JsonRpcClient(ProxyApiMixin, QueueApiMixin, CommandApiMixin):
    """High-level asynchronous JSON-RPC client facade."""

    def __init__(
        self,
        protocol: str = "http",
        host: str = "127.0.0.1",
        port: int = 8080,
        token_header: Optional[str] = None,
        token: Optional[str] = None,
        cert: Optional[str] = None,
        key: Optional[str] = None,
        ca: Optional[str] = None,
        check_hostname: bool = False,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Initialize JSON-RPC client.

        Args:
            protocol: Transport protocol (http, https, mtls)
            host: Server hostname
            port: Server port
            token_header: Header name for authentication token
            token: Authentication token value
            cert: Path to client certificate file
            key: Path to client private key file
            ca: Path to CA certificate file
            check_hostname: Whether to verify hostname in SSL connections
            timeout: HTTP client timeout in seconds. If None, uses value from
                MCP_PROXY_ADAPTER_HTTP_TIMEOUT environment variable, or defaults to 30.0.
                This timeout applies to all HTTP requests including status polling.
        """
        super().__init__(
            protocol=protocol,
            host=host,
            port=port,
            token_header=token_header,
            token=token,
            cert=cert,
            key=key,
            ca=ca,
            check_hostname=check_hostname,
            timeout=timeout,
        )


__all__ = ["JsonRpcClient"]
