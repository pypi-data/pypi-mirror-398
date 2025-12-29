"""
Direct Security Framework Integration

This module provides direct integration with mcp_security_framework,
replacing all project security methods with framework calls.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, List

# Direct imports from framework
try:
    from mcp_security_framework import (
        SecurityManager,
        AuthManager,
        CertificateManager,
        PermissionManager,
        RateLimiter,
    )
    from mcp_security_framework.schemas.config import (
        SecurityConfig,
        AuthConfig,
        SSLConfig,
        PermissionConfig,
        RateLimitConfig,
        CertificateConfig,
        LoggingConfig,
    )
    from mcp_security_framework.schemas.models import (
        AuthResult,
        ValidationResult,
        CertificatePair,
    )
    from mcp_security_framework.middleware.fastapi_middleware import (
        FastAPISecurityMiddleware,
    )

    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError as e:
    # NO FALLBACK! mcp_security_framework is REQUIRED
    raise RuntimeError(
        f"CRITICAL: mcp_security_framework is required but not available: {e}. "
        "Install it with: pip install mcp_security_framework>=1.2.8"
    ) from e

from mcp_proxy_adapter.core.logging import get_global_logger


class SecurityIntegration:
    """
    Direct integration with mcp_security_framework.

    This class replaces all project security methods with direct calls
    to the security framework components.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize security integration.

        Args:
            config: Configuration dictionary
        """
        if not SECURITY_FRAMEWORK_AVAILABLE:
            raise ImportError("mcp_security_framework is not available")

        self.config = config
        self.security_config = self._create_security_config()

        # Initialize framework components
        self.security_manager = SecurityManager(self.security_config)
        self.permission_manager = PermissionManager(self.security_config.permissions)
        self.auth_manager = AuthManager(
            self.security_config.auth, self.permission_manager
        )
        self.certificate_manager = CertificateManager(self.security_config.certificates)
        self.rate_limiter = RateLimiter(self.security_config.rate_limit)

        get_global_logger().info("Security integration initialized with mcp_security_framework")

    def _create_security_config(self) -> SecurityConfig:
        """Create SecurityConfig from project configuration."""
        # self.config is already the security section passed from unified_security.py
        security_section = self.config

        # Create SSL config - SSL is handled by server protocol, not security config
        ssl_config = SSLConfig(
            enabled=False,  # SSL is handled by server protocol
            cert_file=None,
            key_file=None,
            ca_cert_file=None,
            client_cert_file=None,
            client_key_file=None,
            verify_mode="CERT_REQUIRED",
            min_tls_version="TLSv1.2",
            check_hostname=True,
            check_expiry=True,
            expiry_warning_days=30,
        )

        # Create auth config - use new simplified structure
        auth_config = AuthConfig(
            enabled=security_section.get("enabled", True),
            methods=["api_key"],  # Use token-based authentication
            api_keys=security_section.get("tokens", {}),
            user_roles={},  # Will be handled by permissions
            jwt_secret=None,
            jwt_algorithm="HS256",
            jwt_expiry_hours=24,
            certificate_auth=False,
            public_paths=[],
        )

        # Create permission config - use new simplified structure
        roles = security_section.get("roles", {})
        roles_file = security_section.get("roles_file")
        
        # Enable permissions if we have roles or roles_file
        permissions_enabled = bool(roles or roles_file)

        if permissions_enabled:
            # If roles_file is None or empty string, don't pass it to avoid framework errors
            if roles_file is None or roles_file == "":
                get_global_logger().warning(
                    "roles_file is None or empty, permissions will use default configuration"
                )
                roles_file = None

            permission_config = PermissionConfig(
                enabled=True,
                roles_file=roles_file,
                default_role="guest",
                admin_role="admin",
                role_hierarchy={},
                permission_cache_enabled=True,
                permission_cache_ttl=300,
                wildcard_permissions=False,
                strict_mode=True,
                roles=roles,
            )
        else:
            # Create minimal permission config when permissions are disabled
            permission_config = PermissionConfig(
                enabled=False,
                roles_file=None,
                default_role="guest",
                admin_role="admin",
                role_hierarchy={},
                permission_cache_enabled=False,
                permission_cache_ttl=300,
                wildcard_permissions=False,
                strict_mode=False,
                roles={},
            )

        # Create rate limit config - use defaults since rate_limit section doesn't exist in new structure
        rate_limit_config = RateLimitConfig(
            enabled=True,
            default_requests_per_minute=60,
            default_requests_per_hour=1000,
            burst_limit=2,
            window_size_seconds=60,
            storage_backend="memory",
            exempt_paths=[],
            exempt_roles=[],
        )

        # Create certificate config - certificates are handled by server protocol
        certificate_config = CertificateConfig(
            enabled=False,  # Certificates are handled by server protocol
            ca_cert_path=None,
            ca_key_path=None,
            cert_storage_path="./certs",
            key_storage_path="./keys",
            default_validity_days=365,
            key_size=2048,
            hash_algorithm="sha256",
        )

        # Create logging config - use defaults since logging section doesn't exist in new structure
        logging_config = LoggingConfig(
            enabled=True,
            level="INFO",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            console_output=True,
            file_path=None,
        )

        # Create main security config
        return SecurityConfig(
            ssl=ssl_config,
            auth=auth_config,
            permissions=permission_config,
            rate_limit=rate_limit_config,
            certificates=certificate_config,
            logging=logging_config,
            debug=security_section.get("debug", False),
            environment=security_section.get("environment", "dev"),
            version=security_section.get("version", "1.0.0"),
        )

    # Authentication methods - direct calls to AuthManager
    async def authenticate_api_key(self, api_key: str) -> AuthResult:
        """Authenticate using API key."""
        return await self.auth_manager.authenticate_api_key(api_key)

    async def authenticate_jwt(self, token: str) -> AuthResult:
        """Authenticate using JWT token."""
        return await self.auth_manager.authenticate_jwt(token)

    async def authenticate_certificate(self, cert_data: bytes) -> AuthResult:
        """Authenticate using certificate."""
        return await self.auth_manager.authenticate_certificate(cert_data)

    async def validate_request(self, request_data: Dict[str, Any]) -> ValidationResult:
        """Validate request using security manager."""
        return await self.security_manager.validate_request(request_data)

    # Certificate methods - direct calls to CertificateManager
    async def create_ca_certificate(
        self, common_name: str, **kwargs
    ) -> CertificatePair:
        """Create CA certificate."""
        return await self.certificate_manager.create_ca_certificate(
            common_name, **kwargs
        )

    async def create_client_certificate(
        self, common_name: str, **kwargs
    ) -> CertificatePair:
        """Create client certificate."""
        return await self.certificate_manager.create_client_certificate(
            common_name, **kwargs
        )

    async def create_server_certificate(
        self, common_name: str, **kwargs
    ) -> CertificatePair:
        """Create server certificate."""
        return await self.certificate_manager.create_server_certificate(
            common_name, **kwargs
        )

    async def validate_certificate(self, cert_path: str) -> bool:
        """Validate certificate with CRL check if enabled."""
        try:
            # Get CRL configuration from security config
            crl_config = None
            if hasattr(self.security_config, "certificates"):
                cert_config = self.security_config.certificates
                # Only analyze CRL paths if certificates are enabled
                if (
                    hasattr(cert_config, "enabled")
                    and cert_config.enabled
                    and hasattr(cert_config, "crl_enabled")
                    and cert_config.crl_enabled
                ):
                    crl_config = {
                        "crl_enabled": cert_config.crl_enabled,
                        "crl_path": getattr(cert_config, "crl_path", None),
                        "crl_url": getattr(cert_config, "crl_url", None),
                        "crl_validity_days": getattr(
                            cert_config, "crl_validity_days", 30
                        ),
                    }

            # Use mcp_security_framework's validate_certificate_chain with CRL
            if crl_config and crl_config.get("crl_enabled"):
                from mcp_security_framework.utils.cert_utils import (
                    validate_certificate_chain,
                )
                from .crl_utils import CRLManager

                # Get CRL data
                crl_manager = CRLManager(crl_config)
                crl_data = crl_manager.get_crl_data()

                # Validate with CRL
                if crl_data:
                    return validate_certificate_chain(
                        cert_path,
                        self.security_config.certificates.ca_cert_path,
                        crl_data,
                    )

            # Fallback to standard validation
            return await self.certificate_manager.validate_certificate(cert_path)

        except Exception as e:
            get_global_logger().error(f"Certificate validation failed: {e}")
            return False

    async def extract_roles_from_certificate(self, cert_path: str) -> List[str]:
        """Extract roles from certificate."""
        return await self.certificate_manager.extract_roles_from_certificate(cert_path)

    async def revoke_certificate(self, cert_path: str) -> bool:
        """Revoke certificate."""
        return await self.certificate_manager.revoke_certificate(cert_path)

    # Permission methods - direct calls to PermissionManager
    async def check_permission(self, user_id: str, permission: str) -> bool:
        """Check user permission."""
        return await self.permission_manager.check_permission(user_id, permission)

    async def get_user_roles(self, user_id: str) -> List[str]:
        """Get user roles."""
        return await self.permission_manager.get_user_roles(user_id)

    async def add_user_role(self, user_id: str, role: str) -> bool:
        """Add role to user."""
        return await self.permission_manager.add_user_role(user_id, role)

    async def remove_user_role(self, user_id: str, role: str) -> bool:
        """Remove role from user."""
        return await self.permission_manager.remove_user_role(user_id, role)

    # Rate limiting methods - direct calls to RateLimiter
    async def check_rate_limit(
        self, identifier: str, limit_type: str = "per_minute"
    ) -> bool:
        """Check rate limit."""
        return await self.rate_limiter.check_rate_limit(identifier, limit_type)

    async def increment_rate_limit(self, identifier: str) -> None:
        """Increment rate limit counter."""
        await self.rate_limiter.increment_rate_limit(identifier)

    async def get_rate_limit_info(self, identifier: str) -> Dict[str, Any]:
        """Get rate limit information."""
        return await self.rate_limiter.get_rate_limit_info(identifier)

    # Middleware creation - direct use of framework middleware

    # Utility methods




# Factory function for easy integration
