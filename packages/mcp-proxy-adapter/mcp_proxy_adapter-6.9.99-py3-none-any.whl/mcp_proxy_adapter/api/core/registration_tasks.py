"""Async helper routines for proxy heartbeat and unregister flows.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from .registration_context import HeartbeatSettings, ProxyCredentials


def create_heartbeat_task(
    registration_manager: Any,
    proxy_url: str,
    server_name: str,
    server_url: str,
    capabilities: List[str],
    metadata: Dict[str, Any],
    settings: HeartbeatSettings,
    credentials: ProxyCredentials,
    logger: Any,
) -> asyncio.Task:
    """Create and return an asyncio Task that sends heartbeats.

    The heartbeat loop will:
    1. Check global registration status (with mutex)
    2. If not registered, attempt registration
    3. If registered, send heartbeat
    """

    interval = max(2, settings.interval)

    # Import here to avoid circular import
    from mcp_proxy_adapter.api.core.registration_manager import (
        set_registration_status,
        get_stop_flag,
    )

    async def heartbeat_loop() -> None:
        # Extract protocol, host, port from proxy_url for JsonRpcClient
        from urllib.parse import urlparse

        parsed = urlparse(proxy_url)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)

        # Extract cert and key from credentials if available
        client_cert = None
        client_key = None
        client_ca = None
        if credentials.cert:
            client_cert, client_key = credentials.cert
        if isinstance(credentials.verify, str):
            client_ca = credentials.verify

        # Lazy import to avoid circular dependency
        from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient

        client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
            cert=client_cert,
            key=client_key,
            ca=client_ca,
            check_hostname=credentials.check_hostname,
        )
        try:
            while True:
                try:
                    # Check stop flag first (thread-safe with mutex)
                    should_stop = await get_stop_flag()
                    if should_stop:
                        logger.info("🛑 Stop flag set, stopping heartbeat loop")
                        break

                    if not getattr(registration_manager, "registered", False):
                        config_for_registration = getattr(
                            registration_manager, "_registration_config", None
                        )
                        if config_for_registration:
                            logger.info(
                                "📡 Attempting proxy registration before heartbeat"
                            )
                            try:
                                await registration_manager.register_with_proxy(
                                    config_for_registration
                                )
                            except Exception as exc:  # noqa: BLE001
                                logger.warning(
                                    "⚠️  Initial registration attempt failed: %s", exc
                                )
                                await asyncio.sleep(min(5, interval))
                                continue

                    heartbeat_url = settings.url
                    logger.info(
                        "💓 Sending heartbeat with registration payload to %s",
                        heartbeat_url,
                    )
                    try:
                        await client.heartbeat_to_proxy(
                            proxy_url=heartbeat_url,
                            server_name=server_name,
                            server_url=server_url,
                            capabilities=list(capabilities),
                            metadata=metadata,
                            cert=credentials.cert,
                            verify=credentials.verify,
                        )
                        registration_manager.registered = True
                        await set_registration_status(True)
                        logger.info("💓 Heartbeat/registration acknowledged by proxy")
                        await asyncio.sleep(interval)
                    except Exception as exc:
                        registration_manager.registered = False
                        await set_registration_status(False)
                        logger.warning("⚠️  Heartbeat/registration failed: %s", exc)
                        await asyncio.sleep(min(5, interval))
                except asyncio.CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    logger.error(f"Heartbeat/Registration error: {exc}")
                    await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.debug("Heartbeat loop cancelled")
            raise
        finally:
            await client.close()

    return asyncio.create_task(heartbeat_loop())


async def unregister_from_proxy(
    proxy_url: str,
    server_name: str,
    endpoint: str,
    credentials: ProxyCredentials,
    logger: Any,
) -> None:
    """Unregister adapter from proxy using provided credentials."""

    # Extract protocol, host, port from proxy_url for JsonRpcClient
    from urllib.parse import urlparse

    parsed = urlparse(proxy_url)
    client_protocol = parsed.scheme or "http"
    client_host = parsed.hostname or "localhost"
    client_port = parsed.port or (443 if client_protocol == "https" else 80)

    # Extract cert and key from credentials if available
    client_cert = None
    client_key = None
    client_ca = None
    if credentials.cert:
        client_cert, client_key = credentials.cert
    if isinstance(credentials.verify, str):
        client_ca = credentials.verify

    # Lazy import to avoid circular dependency
    from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient

    client = JsonRpcClient(
        protocol=client_protocol,
        host=client_host,
        port=client_port,
        cert=client_cert,
        key=client_key,
        ca=client_ca,
        check_hostname=credentials.check_hostname,
    )
    try:
        full_url = f"{proxy_url}{endpoint}"
        await client.unregister_from_proxy(
            proxy_url=full_url,
            server_name=server_name,
            cert=credentials.cert,
            verify=credentials.verify,
        )
        logger.info(f"\ud83d\udd1a Unregistered from proxy: {server_name}")
    finally:
        await client.close()
