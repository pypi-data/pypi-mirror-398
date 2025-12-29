"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

RegistrationManager class for proxy registration functionality.
"""

import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient
from mcp_proxy_adapter.core.logging import get_global_logger

from mcp_proxy_adapter.api.core.registration_context import (
    HeartbeatSettings,
    ProxyCredentials,
    RegistrationContext,
    prepare_registration_context,
    resolve_heartbeat_settings,
    resolve_runtime_credentials,
    resolve_unregister_endpoint,
)
from mcp_proxy_adapter.api.core.registration_tasks import (
    create_heartbeat_task,
    unregister_from_proxy as unregister_task,
)

from .status import set_registration_status, set_stop_flag
from .helpers import (
    apply_context,
    log_credentials,
    format_httpx_error,
    can_start_tasks,
)


class RegistrationManager:
    """Manager for proxy registration functionality using JsonRpcClient."""

    def __init__(self) -> None:
        """Initialize registration manager."""
        self.logger = get_global_logger()
        self.registered = False
        self._registration_config: Optional[Dict[str, Any]] = None
        self.registration_task: Optional[asyncio.Task] = None
        self.server_name: Optional[str] = None
        self.server_url: Optional[str] = None
        self.proxy_url: Optional[str] = None
        self.capabilities: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.config: Optional[Dict[str, Any]] = None
        self._proxy_registration_config: Dict[str, Any] = {}
        self._registration_credentials: Optional[ProxyCredentials] = None
        self._runtime_credentials: Optional[ProxyCredentials] = None
        self._register_endpoint: str = "/register"
        self._heartbeat_settings: Optional[HeartbeatSettings] = None

    def _get_state(self) -> Dict[str, Any]:
        """Get manager state as dictionary."""
        return {
            "server_name": self.server_name,
            "server_url": self.server_url,
            "proxy_url": self.proxy_url,
            "capabilities": self.capabilities,
            "metadata": self.metadata,
            "config": self.config,
            "_proxy_registration_config": self._proxy_registration_config,
            "_registration_credentials": self._registration_credentials,
            "_runtime_credentials": self._runtime_credentials,
            "_register_endpoint": self._register_endpoint,
        }

    def _set_state(self, state: Dict[str, Any]) -> None:
        """Set manager state from dictionary."""
        self.server_name = state.get("server_name")
        self.server_url = state.get("server_url")
        self.proxy_url = state.get("proxy_url")
        self.capabilities = state.get("capabilities", [])
        self.metadata = state.get("metadata", {})
        self.config = state.get("config")
        self._proxy_registration_config = state.get("_proxy_registration_config", {})
        self._registration_credentials = state.get("_registration_credentials")
        self._runtime_credentials = state.get("_runtime_credentials")
        self._register_endpoint = state.get("_register_endpoint", "/register")

    def _apply_context(
        self, context: RegistrationContext, config: Dict[str, Any]
    ) -> None:
        """Apply registration context to manager state."""
        state = self._get_state()
        apply_context(context, config, state)
        self._set_state(state)

    def _log_credentials(self, prefix: str, credentials: ProxyCredentials) -> None:
        """Log proxy credentials information."""
        log_credentials(self.logger, prefix, credentials)

    def _format_httpx_error(self, exc: Exception) -> str:
        """Format httpx exception for logging."""
        return format_httpx_error(exc)

    def _can_start_tasks(self) -> bool:
        """Check if registration tasks can be started."""
        return can_start_tasks(self._get_state())

    async def register_with_proxy(self, config: Dict[str, Any]) -> bool:
        """
        Register this server with the proxy using JsonRpcClient.

        Uses only the new ``registration`` format from SimpleConfig.
        Registration is controlled by ``registration.auto_on_startup``.
        """
        context = prepare_registration_context(config, self.logger)
        if context is None:
            return True

        self._apply_context(context, config)

        proxy_url = self.proxy_url
        assert proxy_url is not None
        assert self.server_name is not None
        assert self.server_url is not None

        # Parse proxy URL to extract host and port
        parsed = urlparse(proxy_url)
        proxy_host = parsed.hostname or "localhost"
        proxy_port = parsed.port or (443 if parsed.scheme == "https" else 80)

        # Get protocol from URL scheme
        proxy_protocol = parsed.scheme or "http"
        # Check if mTLS (https with certificates)
        ssl_config = self._proxy_registration_config.get("ssl", {})
        if isinstance(ssl_config, dict) and ssl_config.get("cert") and ssl_config.get("ca"):
            proxy_protocol = "mtls"

        # Extract client certificate paths from credentials
        client_cert = None
        client_key = None
        client_ca = None
        if context.credentials.cert:
            client_cert, client_key = context.credentials.cert
        if isinstance(context.credentials.verify, str):
            client_ca = context.credentials.verify

        self.logger.debug(
            "Creating JsonRpcClient: protocol=%s, host=%s, port=%s, cert=%s, ca=%s",
            proxy_protocol,
            proxy_host,
            proxy_port,
            client_cert is not None,
            client_ca is not None,
        )
        if client_cert:
            self.logger.debug("   Client cert: %s, key: %s", client_cert, client_key)
        if client_ca:
            self.logger.debug("   CA cert: %s", client_ca)

        client = JsonRpcClient(
            protocol=proxy_protocol,
            host=proxy_host,
            port=proxy_port,
            cert=client_cert,
            key=client_key,
            ca=client_ca,
            check_hostname=context.credentials.check_hostname,
        )

        async def _register() -> Dict[str, Any]:
            self._log_credentials("🔐 Registration SSL config", context.credentials)
            self.logger.info(f"📡 Connecting to proxy: {proxy_url}")
            self.logger.info(
                "   Endpoint: %s, Server: %s -> %s",
                self._register_endpoint,
                self.server_name,
                self.server_url,
            )
            self.logger.info(f"🔍 [REG_MANAGER] Metadata: {self.metadata}")
            self.logger.info(f"🔍 [REG_MANAGER] UUID in metadata: {self.metadata.get('uuid')}")
            self.logger.info(f"🔍 [REG_MANAGER] Calling client.register_with_proxy...")
            try:
                result = await client.register_with_proxy(
                    proxy_url=proxy_url,
                    server_name=context.server_name,
                    server_url=context.advertised_url,
                    capabilities=self.capabilities,
                    metadata=self.metadata,
                    cert=context.credentials.cert,
                    verify=context.credentials.verify,
                )
                self.logger.info(f"🔍 [REG_MANAGER] Registration response received: {result}")
                return result
            except Exception as e:
                self.logger.error(f"🔍 [REG_MANAGER] ❌ Exception in register_with_proxy: {type(e).__name__}: {e}")
                import traceback
                self.logger.error(f"🔍 [REG_MANAGER] Traceback: {traceback.format_exc()}")
                raise

        max_retries = 5
        retry_delay = 2

        try:
            for attempt in range(max_retries):
                try:
                    registration_response = await _register()
                    if registration_response is not None:
                        self.logger.debug(
                            "Proxy registration response payload: %s",
                            registration_response,
                        )
                        error_msg = (
                            registration_response.get("error", "").lower()
                            if isinstance(registration_response, dict)
                            else ""
                        )
                        if "already registered" in error_msg:
                            self.logger.warning(
                                "⚠️  Server already registered, unregistering and resetting status"
                            )
                            self.registered = False
                            await set_registration_status(False)
                            try:
                                await self.unregister()
                            except Exception as e:
                                self.logger.warning(f"Failed to unregister: {e}")
                            return False

                        self.logger.info(
                            "✅ Successfully registered with proxy as %s -> %s",
                            self.server_name,
                            self.server_url,
                        )
                        self.registered = True
                        await set_registration_status(True)
                        return True
                except Exception as exc:  # noqa: BLE001
                    full_error = self._format_httpx_error(exc)
                    if attempt < max_retries - 1:
                        self.logger.warning(
                            "⚠️  Registration attempt %s/%s failed: %s. Retrying in %ss...",
                            attempt + 1,
                            max_retries,
                            full_error,
                            retry_delay,
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        self.logger.error(
                            "❌ Failed to register with proxy after %s attempts: %s",
                            max_retries,
                            full_error,
                        )
                        return False
            return False
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"❌ Registration error: {exc}")
            return False
        finally:
            await client.close()

    async def start_heartbeat(self, config: Dict[str, Any]) -> None:
        """Start heartbeat task using JsonRpcClient."""
        self.logger.info(
            "🔍 start_heartbeat called with config keys: %s",
            list(config.keys()) if config else "None",
        )

        await set_stop_flag(False)
        self._registration_config = config

        try:
            context = prepare_registration_context(config, self.logger)
        except ValueError as e:
            self.logger.error(f"❌ Configuration error in registration: {e}")
            self.logger.error("🛑 Stopping server due to configuration error")
            import sys

            sys.exit(1)
        except Exception as e:
            self.logger.error(f"❌ Failed to prepare registration context: {e}")
            self.logger.error("🛑 Stopping server due to registration error")
            import sys

            sys.exit(1)

        self.logger.info(f"🔍 Registration context prepared: {context is not None}")

        if context is not None:
            self._apply_context(context, config)

        if context is None:
            self.logger.debug("Registration is disabled, heartbeat task will not start")
            return

        self.logger.info("✅ Registration context available")
        self.logger.info(
            f"✅ Context applied: server_name={self.server_name}, proxy_url={self.proxy_url}"
        )

        if not self._can_start_tasks():
            self.logger.warning(
                "⚠️  Cannot start tasks (missing proxy_url, server_name, or server_url)"
            )
            return

        credentials = self._registration_credentials or resolve_runtime_credentials(
            self._proxy_registration_config,
        )
        settings = resolve_heartbeat_settings(
            self._proxy_registration_config,
            self.proxy_url or "http://localhost:3005",
        )
        self._runtime_credentials = credentials
        self._heartbeat_settings = settings

        heartbeat_url = settings.url
        self.logger.info(
            "💓 Starting heartbeat task (interval: %ss)", settings.interval
        )

        assert self.server_name is not None
        assert self.server_url is not None

        self.registration_task = create_heartbeat_task(
            registration_manager=self,
            proxy_url=heartbeat_url,
            server_name=self.server_name,
            server_url=self.server_url,
            capabilities=self.capabilities,
            metadata=self.metadata,
            settings=settings,
            credentials=credentials,
            logger=self.logger,
        )

    async def stop(self) -> None:
        """Stop registration manager and unregister from proxy."""
        await set_stop_flag(True)

        if self.registration_task:
            self.registration_task.cancel()
            try:
                await self.registration_task
            except asyncio.CancelledError:
                pass
            self.registration_task = None

        await set_stop_flag(False)

        if not (self.registered and self._can_start_tasks() and self.config):
            self.registered = False
            return

        credentials = self._runtime_credentials or resolve_runtime_credentials(
            self._proxy_registration_config,
        )
        endpoint = resolve_unregister_endpoint(
            self._proxy_registration_config,
        )

        assert self.proxy_url is not None
        assert self.server_name is not None

        try:
            await unregister_task(
                proxy_url=self.proxy_url,
                server_name=self.server_name,
                endpoint=endpoint,
                credentials=credentials,
                logger=self.logger,
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"Error unregistering from proxy: {exc}")
        finally:
            self.registered = False

    async def unregister(self) -> None:
        """Unregister from proxy (used internally)."""
        if not (self.registered and self._can_start_tasks() and self.config):
            return

        credentials = self._runtime_credentials or resolve_runtime_credentials(
            self._proxy_registration_config,
        )
        endpoint = resolve_unregister_endpoint(
            self._proxy_registration_config,
        )

        assert self.proxy_url is not None
        assert self.server_name is not None

        try:
            await unregister_task(
                proxy_url=self.proxy_url,
                server_name=self.server_name,
                endpoint=endpoint,
                credentials=credentials,
                logger=self.logger,
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"Error unregistering from proxy: {exc}")

