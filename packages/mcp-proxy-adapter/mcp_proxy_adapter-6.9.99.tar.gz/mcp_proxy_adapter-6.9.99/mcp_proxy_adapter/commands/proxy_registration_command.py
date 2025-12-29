"""
Proxy Registration Command

This command handles proxy registration functionality with security framework integration.
It provides endpoints for registration, unregistration, heartbeat, and discovery.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.logging import get_global_logger


@dataclass
class ProxyRegistrationCommandResult(SuccessResult):
    """Result of proxy registration command."""

    operation: str
    success: bool
    server_key: Optional[str] = None
    message: str = ""
    details: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize data attribute for SuccessResult compatibility."""
        # Initialize data attribute if not already set
        if not hasattr(self, 'data') or self.data is None:
            self.data = {
                "operation": self.operation,
                "server_key": self.server_key,
                "details": self.details,
            }
        # Ensure message is set
        if not hasattr(self, 'message') or not self.message:
            self.message = self.message if hasattr(self, 'message') else ""


class ProxyRegistrationCommand(Command):
    """Proxy registration command with security framework integration."""

    name = "proxy_registration"
    descr = "Proxy registration operations (register, unregister, heartbeat, discover)"
    category = "proxy"
    author = "Vasiliy Zdanovskiy"
    email = "vasilyvz@gmail.com"

    # In-memory registry for testing
    _registry: Dict[str, Dict[str, Any]] = {}
    _server_counter = 1

    async def execute(self, **kwargs) -> ProxyRegistrationCommandResult:
        """
        Execute proxy registration command.

        Args:
            operation: Operation to perform (register, unregister, heartbeat, discover)
            server_id: Server ID for registration
            server_url: Server URL for registration
            server_name: Server name
            description: Server description
            version: Server version
            capabilities: Server capabilities
            endpoints: Server endpoints
            auth_method: Authentication method
            security_enabled: Whether security is enabled
            server_key: Server key for unregistration/heartbeat
            copy_number: Copy number for unregistration
            timestamp: Timestamp for heartbeat
            status: Status for heartbeat

        Returns:
            ProxyRegistrationCommandResult
        """
        operation = kwargs.get("operation", "register")

        # Check user permissions
        context = kwargs.get("context", {})
        user_info = context.get("user", {})
        user_permissions = user_info.get("permissions", [])

        # Define required permissions for each operation
        operation_permissions = {
            "register": ["register"],
            "unregister": ["unregister"],
            "heartbeat": ["heartbeat"],
            "discover": ["discover"],
        }

        required_permissions = operation_permissions.get(operation, ["read"])

        # Get config - initialize if not present
        if not hasattr(self, 'config') or self.config is None:
            from mcp_proxy_adapter.config import get_config
            try:
                self.config = get_config().config_data
            except Exception:
                self.config = {}
        
        # Check if security is enabled before checking permissions
        security_enabled = self.config.get("security", {}).get("enabled", False)
        
        # Only check permissions if security is enabled
        if security_enabled:
            get_global_logger().info(
                f"Checking permissions: user_permissions={user_permissions}, required={required_permissions}"
            )
            if not self._check_permissions(user_permissions, required_permissions):
                return ProxyRegistrationCommandResult(
                    operation=operation,
                    success=False,
                    message=f"Permission denied: {operation} requires {required_permissions}",
                )
        else:
            get_global_logger().debug(f"Security disabled, skipping permission check for operation: {operation}")

        get_global_logger().info(f"Executing proxy registration operation: {operation}")
        get_global_logger().debug(
            f"User permissions: {user_permissions}, required: {required_permissions}"
        )

        if operation == "register":
            return await self._handle_register(kwargs)
        elif operation == "unregister":
            return await self._handle_unregister(kwargs)
        elif operation == "heartbeat":
            return await self._handle_heartbeat(kwargs)
        elif operation == "discover":
            return await self._handle_discover(kwargs)
        else:
            return ProxyRegistrationCommandResult(
                operation=operation,
                success=False,
                message=f"Unknown operation: {operation}",
            )

    async def _handle_register(
        self, kwargs: Dict[str, Any]
    ) -> ProxyRegistrationCommandResult:
        """Handle registration operation."""
        server_id = kwargs.get("server_id")
        server_url = kwargs.get("server_url")
        server_name = kwargs.get("server_name", "Unknown Server")
        description = kwargs.get("description", "")
        version = kwargs.get("version", "1.0.0")
        capabilities = kwargs.get("capabilities", ["jsonrpc", "rest"])
        endpoints = kwargs.get("endpoints", {})
        auth_method = kwargs.get("auth_method", "none")
        security_enabled = kwargs.get("security_enabled", False)

        if not server_id or not server_url:
            return ProxyRegistrationCommandResult(
                operation="register",
                success=False,
                message="Missing required parameters: server_id and server_url",
            )

        # Check if server already exists
        existing_servers = [
            key for key in self._registry.keys() if key.startswith(server_id)
        ]
        copy_number = len(existing_servers) + 1
        server_key = f"{server_id}_{copy_number}"

        # Create server record
        server_record = {
            "server_id": server_id,
            "server_url": server_url,
            "server_name": server_name,
            "description": description,
            "version": version,
            "capabilities": capabilities,
            "endpoints": endpoints,
            "auth_method": auth_method,
            "security_enabled": security_enabled,
            "registered_at": int(time.time()),
            "last_heartbeat": int(time.time()),
            "status": "active",
        }

        self._registry[server_key] = server_record

        get_global_logger().info(f"Registered server: {server_key} at {server_url}")

        return ProxyRegistrationCommandResult(
            operation="register",
            success=True,
            server_key=server_key,
            message=f"Server registered successfully with key: {server_key}",
            details={
                "server_id": server_id,
                "copy_number": copy_number,
                "registered_at": server_record["registered_at"],
            },
        )

    async def _handle_unregister(
        self, kwargs: Dict[str, Any]
    ) -> ProxyRegistrationCommandResult:
        """Handle unregistration operation."""
        server_id = kwargs.get("server_id")
        copy_number = kwargs.get("copy_number", 1)

        if not server_id:
            return ProxyRegistrationCommandResult(
                operation="unregister",
                success=False,
                message="Missing required parameter: server_id",
            )

        server_key = f"{server_id}_{copy_number}"

        if server_key in self._registry:
            del self._registry[server_key]
            get_global_logger().info(f"Unregistered server: {server_key}")

            return ProxyRegistrationCommandResult(
                operation="unregister",
                success=True,
                message=f"Server unregistered successfully: {server_key}",
                details={"unregistered": True},
            )
        else:
            return ProxyRegistrationCommandResult(
                operation="unregister",
                success=True,
                message=f"Server not found in registry: {server_key}",
                details={"unregistered": False},
            )

    async def _handle_heartbeat(
        self, kwargs: Dict[str, Any]
    ) -> ProxyRegistrationCommandResult:
        """Handle heartbeat operation."""
        server_id = kwargs.get("server_id")
        server_key = kwargs.get("server_key")
        timestamp = kwargs.get("timestamp", int(time.time()))
        status = kwargs.get("status", "healthy")

        if not server_key:
            return ProxyRegistrationCommandResult(
                operation="heartbeat",
                success=False,
                message="Missing required parameter: server_key",
            )

        if server_key in self._registry:
            self._registry[server_key]["last_heartbeat"] = timestamp
            self._registry[server_key]["status"] = status

            get_global_logger().debug(f"Heartbeat received for server: {server_key}")

            return ProxyRegistrationCommandResult(
                operation="heartbeat",
                success=True,
                message="Heartbeat processed successfully",
                details={
                    "server_key": server_key,
                    "timestamp": timestamp,
                    "status": status,
                },
            )
        else:
            return ProxyRegistrationCommandResult(
                operation="heartbeat",
                success=False,
                message=f"Server not found: {server_key}",
            )

    async def _handle_discover(
        self, kwargs: Dict[str, Any]
    ) -> ProxyRegistrationCommandResult:
        """Handle discovery operation."""
        # Return all registered servers
        proxies = []

        for server_key, server_record in self._registry.items():
            # Check if server is active (heartbeat within last 5 minutes)
            last_heartbeat = server_record.get("last_heartbeat", 0)
            if time.time() - last_heartbeat < 300:  # 5 minutes
                proxy_info = {
                    "server_key": server_key,
                    "server_id": server_record["server_id"],
                    "server_url": server_record["server_url"],
                    "server_name": server_record["server_name"],
                    "description": server_record["description"],
                    "version": server_record["version"],
                    "capabilities": server_record["capabilities"],
                    "endpoints": server_record["endpoints"],
                    "auth_method": server_record["auth_method"],
                    "security_enabled": server_record["security_enabled"],
                    "registered_at": server_record["registered_at"],
                    "last_heartbeat": server_record["last_heartbeat"],
                    "status": server_record["status"],
                }
                proxies.append(proxy_info)

        get_global_logger().info(f"Discovery request returned {len(proxies)} active servers")

        return ProxyRegistrationCommandResult(
            operation="discover",
            success=True,
            message=f"Found {len(proxies)} active proxy servers",
            details={"proxies": proxies},
        )

    def _check_permissions(
        self, user_permissions: List[str], required_permissions: List[str]
    ) -> bool:
        """
        Check if user has required permissions.

        Args:
            user_permissions: User's permissions
            required_permissions: Required permissions

        Returns:
            True if user has required permissions
        """
        # Admin has all permissions
        if "*" in user_permissions:
            return True

        # Check if user has all required permissions
        for required in required_permissions:
            if required not in user_permissions:
                return False

        return True
