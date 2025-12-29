"""Transport utilities for asynchronous JSON-RPC client.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union, cast

import httpx

from mcp_proxy_adapter.core.ssl_utils import SSLUtils


class JsonRpcTransport:
    """Base transport class providing HTTP primitives."""

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
        Initialize JSON-RPC transport.

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
                MCP_PROXY_ADAPTER_HTTP_TIMEOUT environment variable, or defaults to 30.0
        """
        scheme = "https" if protocol in ("https", "mtls") else "http"
        self.base_url = f"{scheme}://{host}:{port}"

        self.headers: Dict[str, str] = {"Content-Type": "application/json"}
        if token_header and token:
            self.headers[token_header] = token

        self.verify: Union[bool, str] = True
        self.cert: Optional[Tuple[str, str]] = None
        self._check_hostname = check_hostname

        if protocol in ("https", "mtls"):
            if cert and key:
                self.cert = (str(Path(cert)), str(Path(key)))
            if ca:
                self.verify = str(Path(ca))
            else:
                self.verify = False

        # Determine timeout: parameter > environment variable > default
        if timeout is not None:
            self.timeout = float(timeout)
        else:
            env_timeout = os.getenv("MCP_PROXY_ADAPTER_HTTP_TIMEOUT")
            if env_timeout:
                try:
                    self.timeout = float(env_timeout)
                except (ValueError, TypeError):
                    self.timeout = 30.0
            else:
                self.timeout = 30.0
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Return cached async HTTP client or create it lazily."""

        if self._client is None:
            # If verify is a path to CA cert, create SSL context with hostname check disabled
            verify = self.verify
            if isinstance(verify, str):
                verify_path = Path(verify)
                if verify_path.exists():
                    # Extract client cert and key from self.cert tuple if available
                    client_cert = None
                    client_key = None
                    if (
                        self.cert
                        and isinstance(self.cert, tuple)
                        and len(self.cert) == 2
                    ):
                        client_cert = self.cert[0]
                        client_key = self.cert[1]

                    ssl_context = SSLUtils.create_client_ssl_context(
                        ca_cert=str(verify_path),
                        client_cert=client_cert,
                        client_key=client_key,
                        verify=True,
                        check_hostname=self._check_hostname,
                    )
                    # Ensure check_hostname is set correctly (SSLManager may not apply it)
                    if hasattr(ssl_context, "check_hostname"):
                        ssl_context.check_hostname = self._check_hostname
                    verify = ssl_context
                else:
                    # Path doesn't exist, but it's a string - treat as False to avoid errors
                    verify = False

            self._client = httpx.AsyncClient(
                verify=verify,
                cert=self.cert,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close underlying HTTPX client."""

        if self._client:
            await self._client.aclose()
            self._client = None

    async def health(self) -> Dict[str, Any]:
        """Fetch health information from service."""

        client = await self._get_client()
        response = await client.get(f"{self.base_url}/health", headers=self.headers)
        response.raise_for_status()
        return cast(Dict[str, Any], response.json())

    async def get_openapi_schema(self) -> Dict[str, Any]:
        """Fetch OpenAPI schema from service."""

        client = await self._get_client()
        response = await client.get(
            f"{self.base_url}/openapi.json", headers=self.headers
        )
        response.raise_for_status()
        return cast(Dict[str, Any], response.json())

    async def jsonrpc_batch_call(
        self,
        requests: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Execute batch JSON-RPC requests.

        Args:
            requests: List of JSON-RPC request dictionaries, each containing:
                - method: Method name
                - params: Method parameters (optional)
                - id: Request ID (optional)

        Returns:
            List of JSON-RPC responses in the same order as requests

        Example:
            requests = [
                {"jsonrpc": "2.0", "method": "echo", "params": {"message": "Hello"}, "id": 1},
                {"jsonrpc": "2.0", "method": "help", "params": {}, "id": 2},
            ]
            responses = await client.jsonrpc_batch_call(requests)
        """
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/api/jsonrpc/batch",
            json=requests,
            headers=self.headers,
        )
        response.raise_for_status()
        return cast(List[Dict[str, Any]], response.json())

    async def cmd_call(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        validate: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute command via /cmd endpoint.

        This method uses the /cmd endpoint which supports the CommandRequest schema
        with oneOf discriminator for different commands. The schema includes detailed
        parameter validation for each command.

        Args:
            command: Command name to execute
            params: Optional command parameters (specific to command)
            validate: If True, validate request against OpenAPI schema before sending

        Returns:
            Command execution result

        Raises:
            RuntimeError: If command execution fails or validation fails
        """
        # Validate against OpenAPI schema if requested
        if validate:
            schema = await self.get_openapi_schema()
            from mcp_proxy_adapter.client.jsonrpc_client.openapi_validator import (
                OpenAPIValidator,
            )

            validator = OpenAPIValidator(schema)
            is_valid, error_msg = validator.validate_command_request(command, params)
            if not is_valid:
                raise RuntimeError(f"Validation error: {error_msg}")

        payload: Dict[str, Any] = {
            "command": command,
        }
        if params:
            payload["params"] = params

        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/cmd",
            json=payload,
            headers=self.headers,
        )
        response.raise_for_status()
        result = cast(Dict[str, Any], response.json())

        # Check for error in response
        if "error" in result:
            error = result["error"]
            message = error.get("message", "Unknown error")
            code = error.get("code", -1)
            raise RuntimeError(f"Command error: {message} (code: {code})")

        return result.get("result", {})

    def get_schema_generator(self) -> "SchemaRequestGenerator":
        """
        Get schema request generator instance.

        This method requires the schema to be loaded first. Use get_openapi_schema()
        to load the schema, then create a generator.

        Returns:
            SchemaRequestGenerator instance

        Note:
            This is a synchronous method, but it requires the schema to be loaded
            asynchronously first. Consider using get_schema_generator_async() instead.
        """
        from mcp_proxy_adapter.client.jsonrpc_client.schema_generator import (
            SchemaRequestGenerator,
        )

        # This will fail if schema is not loaded - user should use async version
        raise RuntimeError(
            "Schema must be loaded first. Use get_schema_generator_async() instead, "
            "or load schema with await get_openapi_schema() first."
        )

    async def get_schema_generator_async(self) -> "SchemaRequestGenerator":
        """
        Get schema request generator instance with automatic schema loading.

        Returns:
            SchemaRequestGenerator instance
        """
        from mcp_proxy_adapter.client.jsonrpc_client.schema_generator import (
            SchemaRequestGenerator,
        )

        schema = await self.get_openapi_schema()
        return SchemaRequestGenerator(schema)

    async def jsonrpc_call(
        self,
        method: str,
        params: Dict[str, Any],
        req_id: int = 1,
    ) -> Dict[str, Any]:
        """Perform JSON-RPC request and return raw response payload."""

        payload: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": req_id,
        }
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/api/jsonrpc",
            json=payload,
            headers=self.headers,
        )
        response.raise_for_status()
        return cast(Dict[str, Any], response.json())

    def _extract_result(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract ``result`` part from JSON-RPC reply raising on error."""

        if "error" in response:
            error = response["error"]
            message = error.get("message", "Unknown error")
            code = error.get("code", -1)
            raise RuntimeError(f"JSON-RPC error: {message} (code: {code})")
        result_data = response.get("result", {})
        return cast(Dict[str, Any], result_data)
