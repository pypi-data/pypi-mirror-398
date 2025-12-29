"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Lightweight asynchronous client library for registry (proxy) server used in examples.
"""

from typing import Any, Dict, List, Optional

import httpx


class ProxyClient:
    """Asynchronous client for proxy server."""

    def __init__(self, base_url: str):
        """
        Initialize proxy client.

        Args:
            base_url: Base URL of the proxy server
        """
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=5.0)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health(self) -> Dict[str, Any]:
        """
        Get proxy server health status.

        Returns:
            Health status information
        """
        client = await self._get_client()
        r = await client.get(f"{self.base_url}/proxy/health")
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

    async def register(
        self,
        name: str,
        url: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Register a server with the proxy.

        Args:
            name: Server name
            url: Server URL
            capabilities: Optional list of capabilities
            metadata: Optional metadata dictionary

        Returns:
            Registration result
        """
        payload = {
            "name": name,
            "url": url,
            "capabilities": capabilities or [],
            "metadata": metadata or {},
        }
        client = await self._get_client()
        r = await client.post(f"{self.base_url}/register", json=payload)
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

    async def unregister(self, name: str) -> Dict[str, Any]:
        """
        Unregister a server from the proxy.

        Args:
            name: Server name

        Returns:
            Unregistration result
        """
        payload = {"name": name, "url": "", "capabilities": [], "metadata": {}}
        client = await self._get_client()
        r = await client.post(f"{self.base_url}/unregister", json=payload)
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

    async def list_servers(self) -> Dict[str, Any]:
        """
        List all servers registered with the proxy.

        Returns:
            List of registered servers
        """
        client = await self._get_client()
        r = await client.get(f"{self.base_url}/proxy/list")
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

    async def heartbeat(self, name: str, url: str) -> Dict[str, Any]:
        """
        Send heartbeat to the proxy.

        Args:
            name: Server name
            url: Server URL

        Returns:
            Heartbeat result
        """
        payload = {"name": name, "url": url, "capabilities": [], "metadata": {}}
        client = await self._get_client()
        r = await client.post(f"{self.base_url}/proxy/heartbeat", json=payload)
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]
