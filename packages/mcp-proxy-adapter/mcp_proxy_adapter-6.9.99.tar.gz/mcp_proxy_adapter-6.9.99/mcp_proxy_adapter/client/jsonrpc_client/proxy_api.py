"""Proxy registration helpers for JsonRpcClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import logging
import re
import uuid as uuid_module
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Union, cast
from urllib.parse import urlparse

from mcp_proxy_adapter.client.jsonrpc_client.transport import JsonRpcTransport

if TYPE_CHECKING:
    from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient


class ProxyApiMixin(JsonRpcTransport):
    """Mixin providing proxy registration helpers."""

    def _extract_and_validate_uuid(
        self, metadata: Optional[Dict[str, Any]]
    ) -> str:
        """
        Extract UUID from metadata and validate it as UUID4.

        Args:
            metadata: Metadata dictionary that may contain UUID

        Returns:
            Validated UUID4 string

        Raises:
            ValueError: If UUID is missing or invalid
        """
        # Extract UUID from metadata
        uuid_value = None
        if metadata:
            uuid_value = metadata.get("uuid")

        # Validate UUID is present
        if not uuid_value:
            raise ValueError(
                "uuid is required for server registration but not found in metadata"
            )

        # Validate UUID4 format
        try:
            uuid_obj = uuid_module.UUID(str(uuid_value))
            if uuid_obj.version != 4:
                raise ValueError(
                    f"uuid must be UUID4 format, got UUID version {uuid_obj.version}"
                )
            # Normalize to lowercase string with hyphens
            return str(uuid_obj).lower()
        except (ValueError, AttributeError, TypeError) as e:
            raise ValueError(
                f"uuid must be a valid UUID4 format: {str(e)}"
            ) from e

    async def register_with_proxy(
        self,
        proxy_url: str,
        server_name: str,
        server_url: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cert: Optional[Tuple[str, str]] = None,
        verify: Optional[Union[bool, str]] = None,
    ) -> Dict[str, Any]:
        """Register with proxy using JsonRpcClient (no direct httpx usage)."""
        # Extract and validate UUID from metadata
        uuid_value = self._extract_and_validate_uuid(metadata)

        # Remove UUID from metadata if present (it should only be at root level)
        clean_metadata = dict(metadata or {})
        clean_metadata.pop("uuid", None)
        
        payload: Dict[str, Any] = {
            "server_id": server_name,
            "server_url": server_url,
            "uuid": uuid_value,  # UUID at root level - REQUIRED
            "capabilities": capabilities or [],
            "metadata": clean_metadata,
        }

        # Build register URL from proxy_url
        # proxy_url can be full URL (https://host:port/path) or relative path
        proxy_base = proxy_url.rstrip("/")
        register_url = (
            proxy_base if proxy_base.endswith("/register") else f"{proxy_base}/register"
        )

        # Determine if we should use configured client or create new JsonRpcClient
        # Use configured client if:
        # 1. No cert/verify override provided AND
        # 2. proxy_url matches base_url (same host/port/protocol)
        use_configured_client = (
            cert is None
            and verify is None
            and proxy_url.startswith(self.base_url)
        )

        logger = logging.getLogger(__name__)
        logger.info(
            "🔍 [REGISTRATION] Starting registration process"
        )
        logger.info(
            "🔍 [REGISTRATION] Register URL: %s", register_url
        )
        logger.info(
            "🔍 [REGISTRATION] Base URL: %s", self.base_url
        )
        logger.info(
            "🔍 [REGISTRATION] Server name: %s, Server URL: %s", server_name, server_url
        )
        import json
        logger.info(
            "🔍 [REGISTRATION] Payload: %s", json.dumps(payload, indent=2)
        )
        logger.info(
            "🔍 [REGISTRATION] Cert: %s, Verify: %s", cert is not None, verify
        )
        logger.info(
            "🔍 [REGISTRATION] Use configured client: %s", use_configured_client
        )

        try:
            if use_configured_client:
                # Use configured client from JsonRpcTransport
                client = await self._get_client()
                response = await client.post(register_url, json=payload)
            else:
                # Create new JsonRpcClient with explicit settings
                # Extract protocol, host, port from proxy_url
                parsed = urlparse(proxy_base)
                client_protocol = parsed.scheme or "http"
                client_host = parsed.hostname or "localhost"
                client_port = parsed.port or (443 if client_protocol == "https" else 80)
                
                # Extract cert and key from override or self
                client_cert = None
                client_key = None
                client_ca = None
                if cert:
                    client_cert, client_key = cert
                elif self.cert:
                    client_cert, client_key = self.cert
                
                if isinstance(verify, str):
                    client_ca = verify
                elif isinstance(self.verify, str):
                    client_ca = self.verify
                elif verify is False:
                    client_ca = None
                else:
                    client_ca = self.verify if isinstance(self.verify, str) else None
                
                # Create JsonRpcClient for proxy (lazy import to avoid circular dependency)
                from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient
                
                proxy_client = JsonRpcClient(
                    protocol=client_protocol,
                    host=client_host,
                    port=client_port,
                    cert=client_cert,
                    key=client_key,
                    ca=client_ca,
                )
                try:
                    # Use internal client from JsonRpcTransport
                    client = await proxy_client._get_client()
                    response = await client.post(register_url, json=payload)
                finally:
                    await proxy_client.close()

            # Handle response
            logger.info(
                "🔍 [REGISTRATION] Response status: %s", response.status_code
            )
            logger.info(
                "🔍 [REGISTRATION] Response headers: %s", dict(response.headers)
            )
            try:
                response_text = response.text
                logger.info(
                    "🔍 [REGISTRATION] Response body: %s", response_text[:500]
                )
            except Exception:
                pass
            
            # Handle response
            if response.status_code == 400:
                error_data = cast(Dict[str, Any], response.json())
                error_msg = error_data.get("error", "").lower()
                if "already registered" in error_msg:
                    # Retry registration after unregister
                    await self._retry_registration_after_unregister_via_client(
                        proxy_base,
                        register_url,
                        server_name,
                        server_url,
                        capabilities,
                        metadata,
                        error_data,
                        cert,
                        verify,
                    )

            if response.status_code >= 400:
                try:
                    error_data = cast(Dict[str, Any], response.json())
                    error_msg = error_data.get(
                        "error",
                        error_data.get("message", f"HTTP {response.status_code}"),
                    )
                    raise RuntimeError(f"Registration failed: {error_msg}")
                except (ValueError, KeyError):
                    response.raise_for_status()

            response.raise_for_status()
            result = cast(Dict[str, Any], response.json())
            return result
        except Exception as exc:  # noqa: BLE001
            if "Connection" in str(type(exc).__name__):
                error_msg = f"Connection failed to {register_url}"
                raise ConnectionError(error_msg) from exc
            elif "Timeout" in str(type(exc).__name__):
                raise TimeoutError(f"Request timeout to {register_url}") from exc
            else:
                raise ConnectionError(
                    f"HTTP error connecting to {register_url}: {exc}"
                ) from exc

    async def unregister_from_proxy(
        self,
        proxy_url: str,
        server_name: str,
        cert: Optional[Tuple[str, str]] = None,
        verify: Optional[Union[bool, str]] = None,
    ) -> Dict[str, Any]:
        """Unregister from proxy using JsonRpcClient (no direct httpx usage)."""
        payload: Dict[str, Any] = {
            "server_id": server_name,
            "server_url": "",
            "capabilities": [],
            "metadata": {},
        }

        proxy_base = proxy_url.rstrip("/")
        unregister_url = (
            proxy_base
            if proxy_base.endswith("/unregister")
            else f"{proxy_base}/unregister"
        )

        # Extract protocol, host, port from proxy_url
        parsed = urlparse(proxy_base)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)
        
        # Extract cert and key from override or self
        client_cert = None
        client_key = None
        client_ca = None
        if cert:
            client_cert, client_key = cert
        elif self.cert:
            client_cert, client_key = self.cert
        
        if isinstance(verify, str):
            client_ca = verify
        elif isinstance(self.verify, str):
            client_ca = self.verify
        elif verify is False:
            client_ca = None
        else:
            client_ca = self.verify if isinstance(self.verify, str) else None
        
        # Create JsonRpcClient for proxy (lazy import to avoid circular dependency)
        from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient
        
        proxy_client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
            cert=client_cert,
            key=client_key,
            ca=client_ca,
        )
        try:
            # Use internal client from JsonRpcTransport
            client = await proxy_client._get_client()
            response = await client.post(unregister_url, json=payload)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        finally:
            await proxy_client.close()

    async def heartbeat_to_proxy(
        self,
        proxy_url: str,
        server_name: str,
        server_url: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cert: Optional[Tuple[str, str]] = None,
        verify: Optional[Union[bool, str]] = None,
    ) -> None:
        """Send heartbeat to proxy using JsonRpcClient (no direct httpx usage).
        
        Args:
            proxy_url: Full URL to heartbeat endpoint (e.g., "http://host:port/proxy/heartbeat")
            server_name: Server identifier
            server_url: Server URL
            capabilities: Server capabilities
            metadata: Server metadata
            cert: Optional client certificate tuple (cert_file, key_file)
            verify: Optional SSL verification (bool or CA cert path)
        """
        # Extract and validate UUID from metadata
        uuid_value = self._extract_and_validate_uuid(metadata)

        # Remove UUID from metadata if present (it should only be at root level)
        clean_metadata = dict(metadata or {})
        clean_metadata.pop("uuid", None)
        
        payload: Dict[str, Any] = {
            "server_id": server_name,
            "server_url": server_url,
            "uuid": uuid_value,  # UUID at root level - REQUIRED
            "capabilities": capabilities or [],
            "metadata": clean_metadata,
        }

        # Extract protocol, host, port from proxy_url
        parsed = urlparse(proxy_url)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)
        
        # Extract cert and key from override or self
        client_cert = None
        client_key = None
        client_ca = None
        if cert:
            client_cert, client_key = cert
        elif self.cert:
            client_cert, client_key = self.cert
        
        if isinstance(verify, str):
            client_ca = verify
        elif isinstance(self.verify, str):
            client_ca = self.verify
        elif verify is False:
            client_ca = None
        else:
            client_ca = self.verify if isinstance(self.verify, str) else None
        
        # Create JsonRpcClient for proxy (lazy import to avoid circular dependency)
        from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient
        
        proxy_client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
            cert=client_cert,
            key=client_key,
            ca=client_ca,
        )
        try:
            # Use internal client from JsonRpcTransport
            client = await proxy_client._get_client()
            response = await client.post(proxy_url, json=payload)
            response.raise_for_status()
        finally:
            await proxy_client.close()

    async def list_proxy_servers(self, proxy_url: str) -> Dict[str, Any]:
        """List proxy servers using JsonRpcClient (no direct httpx usage)."""
        proxy_base = proxy_url.rstrip("/")
        
        # Extract protocol, host, port from proxy_url
        parsed = urlparse(proxy_base)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)
        
        # Create JsonRpcClient for proxy
        proxy_client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
        )
        try:
            # Use internal client from JsonRpcTransport
            client = await proxy_client._get_client()
            response = await client.get(f"{proxy_base}/proxy/list")
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        finally:
            await proxy_client.close()

    async def get_proxy_health(self, proxy_url: str) -> Dict[str, Any]:
        """Get proxy health using JsonRpcClient (no direct httpx usage)."""
        proxy_base = proxy_url.rstrip("/")
        
        # Extract protocol, host, port from proxy_url
        parsed = urlparse(proxy_base)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)
        
        # Create JsonRpcClient for proxy
        proxy_client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
        )
        try:
            # Use internal client from JsonRpcTransport
            client = await proxy_client._get_client()
            response = await client.get(f"{proxy_base}/proxy/health")
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        finally:
            await proxy_client.close()

    async def _retry_registration_after_unregister_via_client(
        self,
        proxy_base: str,
        register_url: str,
        server_name: str,
        server_url: str,
        capabilities: Optional[List[str]],
        metadata: Optional[Dict[str, Any]],
        error_data: Dict[str, Any],
        cert: Optional[Tuple[str, str]],
        verify: Optional[Union[bool, str]],
    ) -> None:
        """Retry registration after unregister using JsonRpcClient."""
        match = re.search(
            r"already registered as ([^\s,]+)",
            error_data.get("error", ""),
            re.IGNORECASE,
        )
        if not match:
            return

        registered_server_key = match.group(1)
        original_server_id = (
            re.sub(r"_\d+$", "", registered_server_key)
            if "_" in registered_server_key
            else registered_server_key
        )

        # Extract protocol, host, port from proxy_base
        parsed = urlparse(proxy_base)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)
        
        # Extract cert and key from override or self
        client_cert = None
        client_key = None
        client_ca = None
        if cert:
            client_cert, client_key = cert
        elif self.cert:
            client_cert, client_key = self.cert
        
        if isinstance(verify, str):
            client_ca = verify
        elif isinstance(self.verify, str):
            client_ca = self.verify
        elif verify is False:
            client_ca = None
        else:
            client_ca = self.verify if isinstance(self.verify, str) else None
        
        # Create JsonRpcClient for proxy (lazy import to avoid circular dependency)
        from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient
        
        proxy_client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
            cert=client_cert,
            key=client_key,
            ca=client_ca,
        )
        try:
            # Use internal client from JsonRpcTransport
            client = await proxy_client._get_client()
            
            # Unregister
            unregister_payload: Dict[str, Any] = {
                "server_id": original_server_id,
                "server_url": "",
                "capabilities": [],
                "metadata": {},
            }
            unregister_response = await client.post(
                f"{proxy_base}/unregister",
                json=unregister_payload,
            )
            if unregister_response.status_code != 200:
                return

            # Retry registration
            # Extract and validate UUID from metadata
            uuid_value = self._extract_and_validate_uuid(metadata)
            
            retry_payload: Dict[str, Any] = {
                "server_id": server_name,
                "server_url": server_url,
                "uuid": uuid_value,  # UUID at root level - REQUIRED
                "capabilities": capabilities or [],
                "metadata": metadata or {},
            }
            await client.post(register_url, json=retry_payload)
        finally:
            await proxy_client.close()
