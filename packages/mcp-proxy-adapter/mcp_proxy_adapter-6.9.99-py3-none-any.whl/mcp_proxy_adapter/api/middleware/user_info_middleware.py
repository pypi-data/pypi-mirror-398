"""
User Info Middleware

This middleware extracts user information from authentication headers
and sets it in request.state for use by commands.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from mcp_proxy_adapter.core.logging import get_global_logger

# Import mcp_security_framework components
try:
    from mcp_security_framework import AuthManager, PermissionManager
    from mcp_security_framework.schemas.config import AuthConfig, PermissionConfig

    _MCP_SECURITY_AVAILABLE = True
    print("✅ mcp_security_framework available in middleware")
except ImportError:
    _MCP_SECURITY_AVAILABLE = False
    print("⚠️ mcp_security_framework not available in middleware, " "using basic auth")


class UserInfoMiddleware(BaseHTTPMiddleware):
    """
    Middleware for setting user information in request.state.

    This middleware extracts user information from authentication headers
    and sets it in request.state for use by commands.
    """

    def __init__(self, app, config: Dict[str, Any]):
        """
        Initialize user info middleware.

        Args:
            app: FastAPI application
            config: Configuration dictionary
        """
        super().__init__(app)
        self.config = config

        # Initialize AuthManager if available
        self.auth_manager = None
        self._security_available = _MCP_SECURITY_AVAILABLE

        if self._security_available:
            try:
                # Get API keys configuration
                security_config = config.get("security", {})
                
                # Check if security is enabled
                security_enabled = security_config.get("enabled", False)
                if not security_enabled:
                    get_global_logger().info("ℹ️ Security disabled in configuration, using basic auth")
                    self._security_available = False
                else:
                    auth_config = security_config.get("auth", {})
                    permissions_config = security_config.get("permissions", {})

                    # Check if permissions are enabled
                    permissions_enabled = permissions_config.get("enabled", False)

                    # Only use mcp_security_framework if permissions are enabled
                    if permissions_enabled:
                        # Create AuthConfig for mcp_security_framework
                        mcp_auth_config = AuthConfig(
                            enabled=True,
                            methods=["api_key"],
                            api_keys=auth_config.get("api_keys", {}),
                        )

                        # Create PermissionConfig for mcp_security_framework
                        roles_file = permissions_config.get("roles_file")
                        if roles_file is None:
                            get_global_logger().warning("⚠️ Permissions enabled but no roles_file specified, using default configuration")
                            roles_file = None
                        
                        mcp_permission_config = PermissionConfig(
                            roles_file=roles_file,
                            default_role=permissions_config.get("default_role", "guest"),
                            admin_role=permissions_config.get("admin_role", "admin"),
                            role_hierarchy=permissions_config.get("role_hierarchy", {}),
                            permission_cache_enabled=permissions_config.get(
                                "permission_cache_enabled", True
                            ),
                            permission_cache_ttl=permissions_config.get(
                                "permission_cache_ttl", 300
                            ),
                            wildcard_permissions=permissions_config.get(
                                "wildcard_permissions", False
                            ),
                            strict_mode=permissions_config.get("strict_mode", True),
                            roles=permissions_config.get("roles", {}),
                        )

                        # Initialize PermissionManager first
                        self.permission_manager = PermissionManager(mcp_permission_config)

                        # Initialize AuthManager with permission_manager
                        self.auth_manager = AuthManager(
                            mcp_auth_config, self.permission_manager
                        )
                        get_global_logger().info(
                            "✅ User info middleware initialized with " "mcp_security_framework"
                        )
                    else:
                        # When permissions are disabled, use basic auth without mcp_security_framework
                        get_global_logger().info("ℹ️ Permissions disabled, using basic token auth without mcp_security_framework")
                        self._security_available = False
                        # Initialize api_keys for basic auth
                        self.api_keys = auth_config.get("api_keys", {})
            except Exception as e:
                get_global_logger().warning(f"⚠️ Failed to initialize AuthManager: {e}")
                self._security_available = False

        # Always initialize api_keys for fallback
        security_config = config.get("security", {})
        auth_config = security_config.get("auth", {})
        self.api_keys = auth_config.get("api_keys", {})
        
        if not self._security_available:
            # Fallback to basic API key handling
            get_global_logger().info("ℹ️ User info middleware initialized with basic auth")
        else:
            get_global_logger().info("ℹ️ User info middleware initialized with mcp_security_framework (fallback enabled)")

