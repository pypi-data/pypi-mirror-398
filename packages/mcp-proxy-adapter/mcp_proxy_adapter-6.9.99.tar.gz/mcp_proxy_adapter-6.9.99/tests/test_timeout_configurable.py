"""
Tests for configurable HTTP timeout in JsonRpcClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from mcp_proxy_adapter.client.jsonrpc_client.client import JsonRpcClient
from mcp_proxy_adapter.client.jsonrpc_client.transport import JsonRpcTransport


class TestTimeoutConfigurable:
    """Test suite for configurable HTTP timeout."""

    def test_timeout_default_value(self):
        """Test that default timeout is 30.0 seconds."""
        transport = JsonRpcTransport()
        assert transport.timeout == 30.0

    def test_timeout_parameter(self):
        """Test that timeout parameter is used when provided."""
        transport = JsonRpcTransport(timeout=60.0)
        assert transport.timeout == 60.0

    def test_timeout_environment_variable(self):
        """Test that timeout can be set via environment variable."""
        with patch.dict(os.environ, {"MCP_PROXY_ADAPTER_HTTP_TIMEOUT": "45.0"}):
            transport = JsonRpcTransport()
            assert transport.timeout == 45.0

    def test_timeout_parameter_overrides_env(self):
        """Test that timeout parameter overrides environment variable."""
        with patch.dict(os.environ, {"MCP_PROXY_ADAPTER_HTTP_TIMEOUT": "45.0"}):
            transport = JsonRpcTransport(timeout=60.0)
            assert transport.timeout == 60.0

    def test_timeout_invalid_env_value(self):
        """Test that invalid environment variable value falls back to default."""
        with patch.dict(os.environ, {"MCP_PROXY_ADAPTER_HTTP_TIMEOUT": "invalid"}):
            transport = JsonRpcTransport()
            assert transport.timeout == 30.0

    def test_timeout_client_parameter(self):
        """Test that JsonRpcClient accepts timeout parameter."""
        client = JsonRpcClient(timeout=60.0)
        assert client.timeout == 60.0

    def test_timeout_client_default(self):
        """Test that JsonRpcClient uses default timeout when not specified."""
        client = JsonRpcClient()
        assert client.timeout == 30.0

    def test_timeout_client_env_variable(self):
        """Test that JsonRpcClient uses environment variable when timeout not specified."""
        with patch.dict(os.environ, {"MCP_PROXY_ADAPTER_HTTP_TIMEOUT": "45.0"}):
            client = JsonRpcClient()
            assert client.timeout == 45.0

    @pytest.mark.asyncio
    async def test_timeout_used_in_httpx_client(self):
        """Test that timeout is passed to httpx.AsyncClient."""
        transport = JsonRpcTransport(timeout=60.0)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            client = await transport._get_client()

            # Verify httpx.AsyncClient was called with correct timeout
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["timeout"] == 60.0

    def test_timeout_zero_value(self):
        """Test that timeout can be set to 0 (no timeout)."""
        transport = JsonRpcTransport(timeout=0.0)
        assert transport.timeout == 0.0

    def test_timeout_negative_value(self):
        """Test that negative timeout is accepted (httpx will handle it)."""
        transport = JsonRpcTransport(timeout=-1.0)
        assert transport.timeout == -1.0

    def test_timeout_very_large_value(self):
        """Test that very large timeout values are accepted."""
        transport = JsonRpcTransport(timeout=3600.0)  # 1 hour
        assert transport.timeout == 3600.0
