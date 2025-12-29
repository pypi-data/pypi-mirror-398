"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Proxy server commands for registration, heartbeat, and discovery.
These commands are used by the proxy server built on the adapter.
"""

from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional

# Module-level logger
logger = logging.getLogger(__name__)

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


# In-memory registry for proxy server
_registry: Dict[str, Dict[str, Dict[str, Any]]] = {}


class ProxyRegisterResult(SuccessResult):
    """Result of proxy register command."""

    def __init__(self, server_id: str, server_url: str, registered: bool):
        """Initialize proxy register result."""
        data = {
            "server_id": server_id,
            "server_url": server_url,
            "registered": registered,
        }
        super().__init__(data=data)

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for result."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "const": True},
                "data": {
                    "type": "object",
                    "properties": {
                        "server_id": {"type": "string"},
                        "server_url": {"type": "string"},
                        "registered": {"type": "boolean"},
                    },
                    "required": ["server_id", "server_url", "registered"],
                },
            },
            "required": ["success", "data"],
        }

    @property
    def server_id(self) -> str:
        """Get server ID."""
        return self.data.get("server_id", "")

    @property
    def server_url(self) -> str:
        """Get server URL."""
        return self.data.get("server_url", "")

    @property
    def registered(self) -> bool:
        """Get registered status."""
        return self.data.get("registered", False)


class ProxyUnregisterResult(SuccessResult):
    """Result of proxy unregister command."""

    def __init__(self, server_id: str, unregistered: bool):
        """Initialize proxy unregister result."""
        data = {
            "server_id": server_id,
            "unregistered": unregistered,
        }
        super().__init__(data=data)

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for result."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "const": True},
                "data": {
                    "type": "object",
                    "properties": {
                        "server_id": {"type": "string"},
                        "unregistered": {"type": "boolean"},
                    },
                    "required": ["server_id", "unregistered"],
                },
            },
            "required": ["success", "data"],
        }

    @property
    def server_id(self) -> str:
        """Get server ID."""
        return self.data.get("server_id", "")

    @property
    def unregistered(self) -> bool:
        """Get unregistered status."""
        return self.data.get("unregistered", False)


class ProxyHeartbeatResult(SuccessResult):
    """Result of proxy heartbeat command."""

    def __init__(self, server_id: str, heartbeat_received: bool):
        """Initialize proxy heartbeat result."""
        data = {
            "server_id": server_id,
            "heartbeat_received": heartbeat_received,
        }
        super().__init__(data=data)

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for result."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "const": True},
                "data": {
                    "type": "object",
                    "properties": {
                        "server_id": {"type": "string"},
                        "heartbeat_received": {"type": "boolean"},
                    },
                    "required": ["server_id", "heartbeat_received"],
                },
            },
            "required": ["success", "data"],
        }

    @property
    def server_id(self) -> str:
        """Get server ID."""
        return self.data.get("server_id", "")

    @property
    def heartbeat_received(self) -> bool:
        """Get heartbeat received status."""
        return self.data.get("heartbeat_received", False)


class ProxyListResult(SuccessResult):
    """Result of proxy list command."""

    def __init__(self, servers: List[Dict[str, Any]]):
        """Initialize proxy list result."""
        data = {"servers": servers}
        super().__init__(data=data)

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for result."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "const": True},
                "data": {
                    "type": "object",
                    "properties": {
                        "servers": {
                            "type": "array",
                            "items": {"type": "object"},
                        },
                    },
                    "required": ["servers"],
                },
            },
            "required": ["success", "data"],
        }

    @property
    def servers(self) -> List[Dict[str, Any]]:
        """Get servers list."""
        return self.data.get("servers", [])


class ProxyRegisterCommand(Command):
    """Register a server with the proxy."""

    name = "proxy_register"
    descr = "Register a server with the proxy"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "string",
                    "description": "Server identifier (or use 'name')",
                },
                "name": {
                    "type": "string",
                    "description": "Server name (alternative to server_id)",
                },
                "server_url": {
                    "type": "string",
                    "description": "Server URL (or use 'url')",
                },
                "url": {
                    "type": "string",
                    "description": "Server URL (alternative to server_url)",
                },
                "capabilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of server capabilities",
                    "default": [],
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional server metadata",
                    "default": {},
                },
                "uuid": {
                    "type": "string",
                    "description": "Server instance UUID (at root level, not in metadata)",
                    "format": "uuid",
                },
            },
            "required": [],
        }

    async def execute(
        self,
        server_id: str = None,
        name: str = None,
        server_url: str = None,
        url: str = None,
        capabilities: List[str] = None,
        metadata: Dict[str, Any] = None,
        **kwargs,
    ) -> ProxyRegisterResult:
        """Execute proxy register command.

        Validates server accessibility using JsonRpcClient from adapter
        based on server_validation configuration section.
        """
        # Handle both direct parameters and kwargs
        if server_id is None:
            server_id = kwargs.get("server_id") or kwargs.get("name", "")
        if name and not server_id:
            server_id = name
        if server_url is None:
            server_url = kwargs.get("server_url") or kwargs.get("url", "")
        if url and not server_url:
            server_url = url
        if capabilities is None:
            capabilities = kwargs.get("capabilities", [])
        if metadata is None:
            metadata = kwargs.get("metadata", {})

        if not server_id or not server_url:
            return ErrorResult(
                message="server_id (or name) and server_url (or url) are required",
                code=-32602,  # Invalid params
            )

        # Validate server accessibility using JsonRpcClient from adapter
        # Get server_validation config from app context
        validation_config = self._get_validation_config()
        if validation_config and validation_config.get("enabled", False):
            validation_result = await self._validate_server(
                server_url=server_url, validation_config=validation_config
            )
            if not validation_result:
                return ErrorResult(
                    message=f"Server validation failed: server at {server_url} is not accessible",
                    code=-32603,  # Server validation error
                )

        # Extract UUID from kwargs (it's at root level of payload, not in metadata)
        uuid_value = kwargs.get("uuid")
        
        # Register server
        if server_id not in _registry:
            _registry[server_id] = {}

        # Simple registration (no server_key for now)
        # UUID must be at root level, not in metadata
        server_data = {
            "server_id": server_id,
            "server_url": server_url,
            "capabilities": capabilities,
            "metadata": metadata,
            "registered_at": time.time(),
            "last_heartbeat": time.time(),
        }
        
        # Add UUID at root level if provided
        if uuid_value:
            server_data["uuid"] = uuid_value
        
        _registry[server_id]["default"] = server_data

        return ProxyRegisterResult(
            server_id=server_id,
            server_url=server_url,
            registered=True,
        )

    def _get_validation_config(self) -> Optional[Dict[str, Any]]:
        """Get server_validation configuration from app context."""
        try:
            from mcp_proxy_adapter.config import get_config

            config = get_config()
            if hasattr(config, "model") and hasattr(config.model, "server_validation"):
                validation = config.model.server_validation
                return {
                    "enabled": validation.enabled,
                    "protocol": validation.protocol,
                    "cert_file": validation.cert_file,
                    "key_file": validation.key_file,
                    "ca_cert_file": validation.ca_cert_file,
                    "crl_file": validation.crl_file,
                    "use_system_ca": validation.use_system_ca,
                    "timeout": validation.timeout,
                    "use_token": validation.use_token,
                    "use_roles": validation.use_roles,
                    "tokens": validation.tokens,
                    "roles": validation.roles,
                    "auth_header": validation.auth_header,
                    "roles_header": validation.roles_header,
                    "health_path": validation.health_path,
                    "check_hostname": getattr(validation, "check_hostname", True),
                }
        except Exception:
            pass
        return None

    async def _validate_server(
        self, server_url: str, validation_config: Dict[str, Any]
    ) -> bool:
        """Validate server accessibility using JsonRpcClient from adapter."""
        try:
            from urllib.parse import urlparse
            from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient

            parsed = urlparse(server_url)
            # Use protocol from server_validation config, not from server_url
            # This ensures proxy uses the correct protocol as configured
            protocol = validation_config.get("protocol", "http")
            host = parsed.hostname or "localhost"
            port = parsed.port or (443 if protocol == "https" else 80)

            # Extract certificates from validation config
            cert = None
            key = None
            ca = None
            if validation_config.get("cert_file") and validation_config.get("key_file"):
                cert = validation_config["cert_file"]
                key = validation_config["key_file"]
            if validation_config.get("ca_cert_file"):
                ca = validation_config["ca_cert_file"]

            # Create JsonRpcClient with validation config
            check_hostname = validation_config.get("check_hostname", True)
            if not check_hostname:
                logger.info(
                    "🔍 [PROXY] Hostname verification disabled for %s", server_url
                )
            client = JsonRpcClient(
                protocol=protocol,
                host=host,
                port=port,
                cert=cert,
                key=key,
                ca=ca,
                check_hostname=check_hostname,
            )

            try:
                # Try to call health endpoint
                health_path = (
                    validation_config.get("health_path", "/health") or "/health"
                )
                health_url = f"{server_url.rstrip('/')}{health_path}"
                httpx_client = await client._get_client()
                headers: Dict[str, Any] = {}

                # Apply token if configured
                if validation_config.get("use_token"):
                    token_value: Optional[str] = None
                    tokens_cfg = validation_config.get("tokens", {})
                    if isinstance(tokens_cfg, dict):
                        for values in tokens_cfg.values():
                            if isinstance(values, list) and values:
                                token_value = values[0]
                                break
                            if isinstance(values, str):
                                token_value = values
                                break
                    elif isinstance(tokens_cfg, list) and tokens_cfg:
                        token_value = tokens_cfg[0]
                    if token_value:
                        headers[validation_config.get("auth_header", "X-API-Key")] = (
                            token_value
                        )

                # Apply roles header if configured
                if validation_config.get("use_roles"):
                    roles_cfg = validation_config.get("roles", {})
                    roles_value: Optional[str] = None
                    if isinstance(roles_cfg, dict):
                        collected = []
                        for values in roles_cfg.values():
                            if isinstance(values, list):
                                collected.extend(values)
                            elif isinstance(values, str):
                                collected.append(values)
                        if collected:
                            roles_value = ",".join(collected)
                    elif isinstance(roles_cfg, list) and roles_cfg:
                        roles_value = ",".join(
                            role for role in roles_cfg if isinstance(role, str)
                        )
                    if roles_value:
                        headers[validation_config.get("roles_header", "X-Roles")] = (
                            roles_value
                        )

                response = await httpx_client.get(
                    health_url,
                    timeout=validation_config.get("timeout", 10),
                    headers=headers or None,
                )
                if response.status_code != 200:
                    logger.warning(
                        "🔍 [PROXY] Server validation HTTP %s for %s: %s",
                        response.status_code,
                        health_url,
                        response.text[:200],
                    )
                return response.status_code == 200
            finally:
                await client.close()
        except Exception as exc:
            logger.error(
                "🔍 [PROXY] Server validation exception (%s): %s",
                server_url,
                exc,
                exc_info=True,
            )
            return False


class ProxyUnregisterCommand(Command):
    """Unregister a server from the proxy."""

    name = "proxy_unregister"
    descr = "Unregister a server from the proxy"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "string",
                    "description": "Server identifier (or use 'name')",
                },
                "name": {
                    "type": "string",
                    "description": "Server name (alternative to server_id)",
                },
            },
            "required": [],
        }

    async def execute(
        self, server_id: str = None, name: str = None, **kwargs
    ) -> ProxyUnregisterResult:
        """Execute proxy unregister command."""
        if server_id is None:
            server_id = kwargs.get("server_id") or kwargs.get("name", "")
        if name and not server_id:
            server_id = name

        if not server_id:
            return ErrorResult(
                message="server_id (or name) is required",
                code=-32602,  # Invalid params
            )

        unregistered = False
        if server_id in _registry:
            _registry.pop(server_id, None)
            unregistered = True

        return ProxyUnregisterResult(
            server_id=server_id,
            unregistered=unregistered,
        )


class ProxyHeartbeatCommand(Command):
    """Update server heartbeat."""

    name = "proxy_heartbeat"
    descr = "Update server heartbeat"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "string",
                    "description": "Server identifier (or use 'name')",
                },
                "name": {
                    "type": "string",
                    "description": "Server name (alternative to server_id)",
                },
                "server_url": {
                    "type": "string",
                    "description": "Server URL (required if server is not registered yet)",
                },
                "url": {
                    "type": "string",
                    "description": "Server URL (alternative to server_url)",
                },
                "capabilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Server capabilities",
                    "default": [],
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional server metadata",
                    "default": {},
                },
                "uuid": {
                    "type": "string",
                    "description": "Server instance UUID (at root level, not in metadata)",
                    "format": "uuid",
                },
            },
            "required": [],
        }

    async def execute(
        self,
        server_id: str = None,
        name: str = None,
        server_url: str = None,
        url: str = None,
        capabilities: List[str] = None,
        metadata: Dict[str, Any] = None,
        **kwargs,
    ) -> ProxyHeartbeatResult:
        """Execute proxy heartbeat command."""
        if server_id is None:
            server_id = kwargs.get("server_id") or kwargs.get("name", "")
        if name and not server_id:
            server_id = name

        if server_url is None:
            server_url = kwargs.get("server_url") or kwargs.get("url", "")
        if url and not server_url:
            server_url = url
        if capabilities is None:
            capabilities = kwargs.get("capabilities", [])
        if metadata is None:
            metadata = kwargs.get("metadata", {})

        if not server_id:
            return ErrorResult(
                message="server_id (or name) is required",
                code=-32602,  # Invalid params
            )

        # Extract UUID from kwargs (it's at root level of payload, not in metadata)
        uuid_value = kwargs.get("uuid")
        
        heartbeat_received = False
        entry = _registry.setdefault(server_id, {}).get("default")
        if entry is None:
            if not server_url:
                return ErrorResult(
                    message="server_url (or url) is required for first heartbeat from server",
                    code=-32602,
                )
            entry = {
                "server_id": server_id,
                "server_url": server_url,
                "capabilities": capabilities or [],
                "metadata": metadata or {},
                "registered_at": time.time(),
                "last_heartbeat": time.time(),
            }
            # Add UUID at root level if provided
            if uuid_value:
                entry["uuid"] = uuid_value
            _registry[server_id]["default"] = entry
            heartbeat_received = True
        else:
            if server_url:
                entry["server_url"] = server_url
            if capabilities is not None:
                entry["capabilities"] = capabilities
            if metadata is not None:
                entry["metadata"] = metadata
            # Update UUID at root level if provided
            if uuid_value:
                entry["uuid"] = uuid_value
            entry["last_heartbeat"] = time.time()
            heartbeat_received = True

        return ProxyHeartbeatResult(
            server_id=server_id,
            heartbeat_received=heartbeat_received,
        )


class ProxyListCommand(Command):
    """List all registered servers."""

    name = "proxy_list"
    descr = "List all registered servers"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {},
        }

    async def execute(self, **kwargs) -> ProxyListResult:
        """Execute proxy list command."""
        servers = []
        for server_id, instances in _registry.items():
            for instance_key, server_data in instances.items():
                server_entry = {
                    "server_id": server_data.get("server_id", server_id),
                    "server_url": server_data.get("server_url", ""),
                    "capabilities": server_data.get("capabilities", []),
                    "metadata": server_data.get("metadata", {}),
                    "registered_at": server_data.get("registered_at", 0),
                    "last_heartbeat": server_data.get("last_heartbeat", 0),
                }
                # UUID must be at root level, not in metadata
                if "uuid" in server_data:
                    server_entry["uuid"] = server_data["uuid"]
                servers.append(server_entry)

        return ProxyListResult(servers=servers)
