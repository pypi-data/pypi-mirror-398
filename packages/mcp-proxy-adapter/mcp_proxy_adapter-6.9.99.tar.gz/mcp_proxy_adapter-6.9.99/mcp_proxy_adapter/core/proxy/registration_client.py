"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Registration client for proxy registration.
"""

from typing import Dict, Any
import asyncio
import aiohttp

from mcp_proxy_adapter.core.logging import get_global_logger
from .auth_manager import AuthManager
from .ssl_manager import SSLManager


class RegistrationClient:
    """Client for proxy registration operations."""

    def __init__(
        self,
        client_security,
        registration_config: Dict[str, Any],
        config: Dict[str, Any],
        proxy_url: str,
    ):
        """
        Initialize registration client.

        Args:
            client_security: Client security manager instance
            registration_config: Registration configuration
            config: Application configuration
            proxy_url: Proxy server URL
        """
        self.client_security = client_security
        self.registration_config = registration_config
        self.config = config
        self.proxy_url = proxy_url
        self.logger = get_global_logger()

        # Initialize managers
        self.auth_manager = AuthManager(client_security, registration_config)
        self.ssl_manager = SSLManager(
            client_security, registration_config, config, proxy_url
        )

    def _prepare_registration_data(self, server_url: str) -> Dict[str, Any]:
        """
        Prepare registration data.

        Args:
            server_url: Server URL to register

        Returns:
            Registration data dictionary
        """
        import uuid as uuid_module
        
        # Proxy expects "name" field, use server_id or server_name
        server_name = (
            self.registration_config.get("server_id")
            or self.registration_config.get("server_name")
            or "mcp_proxy_adapter"
        )

        # Extract UUID from registration config
        instance_uuid = self.registration_config.get("instance_uuid")
        
        # Validate UUID if present
        if instance_uuid:
            try:
                uuid_obj = uuid_module.UUID(str(instance_uuid))
                if uuid_obj.version != 4:
                    self.logger.warning(
                        f"⚠️ UUID is not UUID4 format (version: {uuid_obj.version}), "
                        "but continuing with registration"
                    )
                instance_uuid = str(uuid_obj).lower()  # Normalize
            except (ValueError, AttributeError, TypeError) as e:
                self.logger.error(
                    f"❌ Invalid UUID format in registration config: {e}. "
                    "Registration may fail."
                )

        metadata = {
            "server_id": self.registration_config.get("server_id"),
            "server_name": self.registration_config.get("server_name"),
            "instance_uuid": instance_uuid,
            "description": self.registration_config.get("description", ""),
            "version": self.registration_config.get("version", "1.0.0"),
        }

        # Build payload with UUID at root level (REQUIRED by proxy)
        payload = {
            "name": server_name,
            "url": server_url,
            "capabilities": self.registration_config.get("capabilities", ["jsonrpc"]),
            "metadata": metadata,
        }
        
        # Add UUID at root level if present (REQUIRED by proxy)
        if instance_uuid:
            payload["uuid"] = instance_uuid
            self.logger.info(f"🔍 [REG] UUID added to root level: {instance_uuid}")
        else:
            self.logger.warning(
                "⚠️ [REG] instance_uuid not found in registration config. "
                "UUID will not be included in root payload."
            )
        
        return payload

    async def register(self, server_url: str) -> bool:
        """
        Register server with proxy.

        Args:
            server_url: Server URL to register

        Returns:
            True if registration successful, False otherwise
        """
        try:
            registration_data = self._prepare_registration_data(server_url)

            # Get SSL context if needed
            self.logger.info(
                f"🔍 [REG] Getting SSL context for proxy URL: {self.proxy_url}"
            )
            ssl_context = self.ssl_manager.get_ssl_context()
            self.logger.info(
                f"🔍 [REG] SSL context: {ssl_context} (type: {type(ssl_context).__name__ if ssl_context else 'None'})"
            )

            # Get headers with authentication if needed
            headers = self.auth_manager.get_headers()

            # Prepare request configuration
            connector = None
            if ssl_context:
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                self.logger.info("🔍 [REG] Created TCPConnector with SSL context")
            else:
                self.logger.info(
                    "🔍 [REG] No SSL context, using default connector (HTTP)"
                )

            # Send registration request
            async with aiohttp.ClientSession(connector=connector) as session:
                register_url = f"{self.proxy_url}/register"
                self.logger.info(
                    f"🔍 [REG] Attempting to register server with proxy at {register_url}"
                )
                self.logger.info(f"🔍 [REG] Registration data: {registration_data}")
                self.logger.info(f"🔍 [REG] UUID in root level: {registration_data.get('uuid', 'MISSING')}")
                self.logger.info(f"🔍 [REG] Headers: {headers}")
                self.logger.info(
                    f"🔍 [REG] Using connector: {connector} (SSL: {ssl_context is not None})"
                )

                # Ensure Content-Type header is set
                if "Content-Type" not in headers:
                    headers["Content-Type"] = "application/json"

                self.logger.info(f"🔍 [REG] Sending POST request to {register_url}...")
                try:
                    async with session.post(
                        register_url,
                        json=registration_data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        self.logger.info(f"🔍 [REG] Response received: status={response.status}")
                        if response.status == 200:
                            result = await response.json()
                            self.logger.info(
                                f"✅ Successfully registered with proxy. Server key: {result.get('key')}"
                            )
                            return True
                        else:
                            error_text = await response.text()
                            self.logger.error(
                                f"❌ Failed to register with proxy: {response.status} {response.reason}: {error_text}"
                            )
                            return False
                except asyncio.TimeoutError as e:
                    self.logger.error(f"🔍 [REG] ❌ Registration timeout: {e}")
                    raise
                except aiohttp.ClientError as e:
                    self.logger.error(f"🔍 [REG] ❌ Client error: {e}")
                    raise
                except Exception as e:
                    self.logger.error(f"🔍 [REG] ❌ Request error: {e}")
                    raise

        except Exception as e:
            self.logger.error(f"🔍 [REG] ❌ Registration error: {e}", exc_info=True)
            return False

    async def unregister(self) -> bool:
        """
        Unregister server from proxy.

        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            server_name = (
                self.registration_config.get("server_id")
                or self.registration_config.get("server_name")
                or "mcp_proxy_adapter"
            )

            # Extract UUID for unregister (if available)
            instance_uuid = self.registration_config.get("instance_uuid")
            
            unregister_data = {
                "name": server_name,
                "url": "",  # Not needed for unregister
                "capabilities": [],
                "metadata": {},
            }
            
            # Add UUID at root level if present (for consistency)
            if instance_uuid:
                try:
                    import uuid as uuid_module
                    uuid_obj = uuid_module.UUID(str(instance_uuid))
                    unregister_data["uuid"] = str(uuid_obj).lower()
                except (ValueError, AttributeError, TypeError):
                    pass  # Skip UUID if invalid

            # Get SSL context if needed
            self.logger.info(
                f"🔍 [UNREG] Getting SSL context for proxy URL: {self.proxy_url}"
            )
            ssl_context = self.ssl_manager.get_ssl_context()
            self.logger.info(
                f"🔍 [UNREG] SSL context: {ssl_context} (type: {type(ssl_context).__name__ if ssl_context else 'None'})"
            )

            # Get headers with authentication if needed
            headers = self.auth_manager.get_headers()

            # Prepare request configuration
            connector = None
            if ssl_context:
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                self.logger.info("🔍 [UNREG] Created TCPConnector with SSL context")
            else:
                self.logger.info(
                    "🔍 [UNREG] No SSL context, using default connector (HTTP)"
                )

            # Send unregistration request
            async with aiohttp.ClientSession(connector=connector) as session:
                unregister_url = f"{self.proxy_url}/unregister"
                self.logger.info(
                    f"🔍 [UNREG] Attempting to unregister from proxy at {unregister_url}"
                )
                self.logger.info(
                    f"🔍 [UNREG] Using connector: {connector} (SSL: {ssl_context is not None})"
                )

                async with session.post(
                    unregister_url,
                    json=unregister_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        self.logger.info("✅ Successfully unregistered from proxy")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.warning(
                            f"⚠️ Failed to unregister from proxy: {response.status} {response.reason}: {error_text}"
                        )
                        return False

        except Exception as e:
            self.logger.error(f"Unregistration error: {e}", exc_info=True)
            return False
