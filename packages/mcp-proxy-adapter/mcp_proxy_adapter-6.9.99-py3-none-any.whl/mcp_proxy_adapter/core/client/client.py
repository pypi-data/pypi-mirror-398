"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Universal Client for MCP Proxy Adapter Framework.

This module provides a universal client that can connect to MCP Proxy Adapter servers
using various authentication methods and protocols.
"""

from typing import Any, Dict, Optional

import aiohttp

from .auth_handler import AuthHandler
from .ssl_handler import SSLHandler
from .request_handler import RequestHandler

# Import security framework components
try:
    from mcp_security_framework import (
        SecurityManager,
        AuthManager,
        CertificateManager,
        PermissionManager,
    )

    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False
    SecurityManager = None
    AuthManager = None
    CertificateManager = None
    PermissionManager = None


class UniversalClient:
    """
    Universal client that demonstrates all possible secure connection methods.

    Supports:
    - HTTP/HTTPS connections
    - API Key authentication
    - JWT token authentication
    - Certificate-based authentication
    - SSL/TLS with custom certificates
    - Role-based access control
    - Rate limiting awareness
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize universal client with configuration.

        Args:
            config: Client configuration with security settings
        """
        self.config = config
        self.base_url = config.get("server_url", "http://localhost:8000")
        self.timeout = config.get("timeout", 30)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 1)

        # Security configuration
        self.security_config = config.get("security", {})
        self.auth_method = self.security_config.get("auth_method", "none")

        # Initialize security managers if framework is available
        self.security_manager = None
        self.auth_manager = None
        self.cert_manager = None

        if SECURITY_FRAMEWORK_AVAILABLE:
            self._initialize_security_managers()

        # Initialize handlers
        self.auth_handler = AuthHandler(self.security_config, self.cert_manager)
        self.ssl_handler = SSLHandler(self.security_config, self.security_manager)

        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_handler: Optional[RequestHandler] = None

        print(f"Universal client initialized with auth method: {self.auth_method}")

    def _initialize_security_managers(self) -> None:
        """Initialize security framework managers."""
        try:
            # Initialize security manager
            self.security_manager = SecurityManager(self.security_config)

            # Initialize permission manager first
            permissions_config = self.security_config.get("permissions", {})
            self.permission_manager = PermissionManager(permissions_config)

            # Initialize auth manager with permission_manager
            auth_config = self.security_config.get("auth", {})
            self.auth_manager = AuthManager(auth_config, self.permission_manager)

            # Initialize certificate manager
            cert_config = self.security_config.get("certificates", {})
            self.cert_manager = CertificateManager(cert_config)

            # Update handlers with managers
            self.auth_handler.cert_manager = self.cert_manager
            self.ssl_handler.security_manager = self.security_manager

            print("Security framework managers initialized successfully")
        except Exception as e:
            print(f"Warning: Failed to initialize security managers: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Establish connection with authentication."""
        print(
            f"Connecting to {self.base_url} with {self.auth_method} authentication..."
        )

        # Create SSL context
        ssl_context = self.ssl_handler.create_ssl_context()

        # Create connector with SSL context
        connector = None
        if ssl_context:
            connector = aiohttp.TCPConnector(ssl=ssl_context)

        # Create session
        self.session = aiohttp.ClientSession(connector=connector)

        # Initialize request handler
        self.request_handler = RequestHandler(
            self.base_url,
            self.timeout,
            self.retry_attempts,
            self.retry_delay,
            self.session,
            self.security_manager,
        )

        # Perform authentication based on method
        if self.auth_method == "api_key":
            await self.auth_handler.authenticate_api_key()
        elif self.auth_method == "jwt":
            await self.auth_handler.authenticate_jwt()
        elif self.auth_method == "certificate":
            await self.auth_handler.authenticate_certificate()
        elif self.auth_method == "basic":
            await self.auth_handler.authenticate_basic()
        else:
            print("No authentication required")

        print("Connection established successfully")

    async def disconnect(self) -> None:
        """Close connection and cleanup."""
        if self.session:
            await self.session.close()
            self.session = None
        self.request_handler = None
        print("Connection closed")

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make authenticated request to server.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            headers: Additional headers

        Returns:
            Response data
        """
        # Prepare headers
        auth_headers = self.auth_handler.get_auth_headers(self.auth_method)
        request_headers = auth_headers.copy()
        if headers:
            request_headers.update(headers)

        return await self.request_handler.request(
            method, endpoint, data, request_headers
        )

    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request."""
        return await self.request("GET", endpoint, **kwargs)

    async def post(
        self, endpoint: str, data: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Make POST request."""
        return await self.request("POST", endpoint, data=data, **kwargs)

    async def put(
        self, endpoint: str, data: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Make PUT request."""
        return await self.request("PUT", endpoint, data=data, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self.request("DELETE", endpoint, **kwargs)

    async def test_connection(self) -> bool:
        """Test connection to server."""
        try:
            result = await self.get("/health")
            if "error" not in result:
                print("✅ Connection test successful")
                return True
            else:
                print(f"❌ Connection test failed: {result}")
                return False
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    async def test_security_features(self) -> Dict[str, bool]:
        """Test various security features."""
        results = {}

        # Test basic connectivity
        results["connectivity"] = await self.test_connection()

        # Test authentication
        if self.auth_method != "none":
            try:
                result = await self.get("/api/auth/status")
                results["authentication"] = "error" not in result
            except Exception:
                results["authentication"] = False

        # Test SSL/TLS
        if self.base_url.startswith("https"):
            results["ssl_tls"] = True
        else:
            results["ssl_tls"] = False

        return results

    async def register_proxy(self, proxy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register with proxy server.

        Args:
            proxy_config: Proxy registration configuration

        Returns:
            Registration result
        """
        try:
            result = await self.post(
                "/api/jsonrpc",
                {
                    "jsonrpc": "2.0",
                    "method": "proxy_registration",
                    "params": proxy_config,
                    "id": 1,
                },
            )
            return result
        except Exception as e:
            print(f"Proxy registration failed: {e}")
            return {"error": str(e)}

    async def execute_command(
        self, command: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a command on the server.

        Args:
            command: Command name
            params: Command parameters

        Returns:
            Command result
        """
        try:
            result = await self.post(
                "/api/jsonrpc",
                {"jsonrpc": "2.0", "method": command, "params": params or {}, "id": 1},
            )
            return result
        except Exception as e:
            print(f"Command execution failed: {e}")
            return {"error": str(e)}

