"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Core mTLS Proxy Client.

Provides an asynchronous client for communicating with a proxy-like server over
mutual TLS. Designed to be used by services built on this framework to:
- perform health/heartbeat checks
- register themselves with the proxy

This client intentionally avoids framework-specific configuration objects and
accepts explicit parameters for clarity and portability.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING
from urllib.parse import urljoin

import aiohttp  # type: ignore[import]

from mcp_proxy_adapter.core.ssl_utils import SSLUtils

if TYPE_CHECKING:
    from ssl import SSLContext

@dataclass(frozen=True)
class RegistrationRequest:
    """Data payload for registration calls to the proxy server."""

    server_id: str
    server_name: str
    description: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert registration request to dictionary.
        
        Returns:
            Dictionary representation of the registration request
        """
        payload: Dict[str, Any] = {
            "server_id": self.server_id,
            "server_name": self.server_name,
        }
        if self.description is not None:
            payload["description"] = self.description
        if self.extra:
            payload.update(self.extra)
        return payload


class ProxyClient:
    """Asynchronous mTLS HTTP client for communicating with a proxy server.

    Usage:
        async with ProxyClient(
            base_url="https://your-proxy-host:3004",
            ca_cert_path="/path/to/ca.crt",
            client_cert_path="/path/to/client.crt",
            client_key_path="/path/to/client.key",
        ) as client:
            status, health = await client.health()
            status, hb = await client.heartbeat()
            status, reg = await client.register(
                RegistrationRequest(...)
            )
    """

    def __init__(
        self,
        base_url: str,
        *,
        ca_cert_path: str,
        client_cert_path: str,
        client_key_path: str,
        request_timeout_s: float = 5.0,
        min_tls_version: str = "TLSv1.2",
        verify_mode: str = "CERT_REQUIRED",
    ) -> None:
        """
        Initialize proxy client.
        
        Args:
            base_url: Base URL of the proxy server
            ca_cert_path: Path to CA certificate file
            client_cert_path: Path to client certificate file
            client_key_path: Path to client private key file
            request_timeout_s: Request timeout in seconds
            min_tls_version: Minimum TLS version
            verify_mode: SSL verification mode
        """
        if not base_url.startswith("http"):
            raise ValueError("base_url must start with http/https")
        self._base_url: str = base_url.rstrip("/")
        self._ca_cert_path: str = ca_cert_path
        self._client_cert_path: str = client_cert_path
        self._client_key_path: str = client_key_path
        self._request_timeout_s: float = request_timeout_s
        self._min_tls_version: str = (
            getattr(min_tls_version, "value", min_tls_version)  # Handle ssl.TLSVersion
        )
        self._verify_mode: str = (
            verify_mode.name if hasattr(verify_mode, "name") else str(verify_mode)
        )

        self._ssl_context: Optional["SSLContext"] = None
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "ProxyClient":
        """
        Async context manager entry.

        Returns:
            ProxyClient instance
        """
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """
        Async context manager exit.

        Args:
            exc_type: Exception type
            exc: Exception instance
            tb: Traceback
        """
        await self.close()

    async def _ensure_session(self) -> None:
        """
        Ensure aiohttp session is created and initialized.

        Creates SSL context and aiohttp ClientSession if not already created.
        """
        if self._session is not None:
            return
        ssl_context = self._build_ssl_context()
        timeout = aiohttp.ClientTimeout(total=self._request_timeout_s)
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
        )
        self._ssl_context = ssl_context

    async def close(self) -> None:
        """
        Close the proxy client session and cleanup resources.

        Closes aiohttp session and clears SSL context.
        """
        if self._session is not None:
            await self._session.close()
        self._session = None
        self._ssl_context = None

    def _build_ssl_context(self) -> "SSLContext":
        """
        Build SSL context for mTLS connections.
        
        Returns:
            Configured SSL context
        """
        return SSLUtils.create_client_ssl_context(
            ca_cert=self._ca_cert_path,
            client_cert=self._client_cert_path,
            client_key=self._client_key_path,
            verify=self._verify_mode != "CERT_NONE",
            min_tls_version=self._min_tls_version,
            check_hostname=True,
        )

    async def _get_json(self, path: str) -> Tuple[int, Dict[str, Any]]:
        """
        Perform GET request and return JSON response.

        Args:
            path: URL path to request

        Returns:
            Tuple of (status_code, response_data)
        """
        await self._ensure_session()
        assert self._session is not None
        url = urljoin(self._base_url + "/", path.lstrip("/"))
        async with self._session.get(url) as resp:
            status = resp.status
            body_text = await resp.text()
            try:
                data: Dict[str, Any] = (
                    json.loads(body_text) if body_text else {}
                )
            except json.JSONDecodeError:
                data = {"raw": body_text}
            return status, data

    async def _post_json(
        self,
        path: str,
        payload: Dict[str, Any],
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Perform POST request with JSON payload.

        Args:
            path: URL path to request
            payload: JSON payload to send

        Returns:
            Tuple of (status_code, response_data)
        """
        await self._ensure_session()
        assert self._session is not None
        url = urljoin(self._base_url + "/", path.lstrip("/"))
        headers = {"Content-Type": "application/json"}
        async with self._session.post(
            url,
            headers=headers,
            json=payload,
        ) as resp:
            status = resp.status
            body_text = await resp.text()
            try:
                data: Dict[str, Any] = (
                    json.loads(body_text) if body_text else {}
                )
            except json.JSONDecodeError:
                data = {"raw": body_text}
            return status, data

    async def health(
        self,
        path: str = "/health",
    ) -> Tuple[int, Dict[str, Any]]:
        """Perform a health check against the proxy."""
        return await self._get_json(path)

    async def heartbeat(
        self,
        path: str = "/heartbeat",
    ) -> Tuple[int, Dict[str, Any]]:
        """Perform a heartbeat (liveness) check against the proxy."""
        return await self._get_json(path)

    async def register(
        self,
        request: RegistrationRequest,
        *,
        path: str = "/register",
    ) -> Tuple[int, Dict[str, Any]]:
        """Register the current service on the proxy server."""
        payload = request.to_dict()
        return await self._post_json(
            path,
            payload,
        )
