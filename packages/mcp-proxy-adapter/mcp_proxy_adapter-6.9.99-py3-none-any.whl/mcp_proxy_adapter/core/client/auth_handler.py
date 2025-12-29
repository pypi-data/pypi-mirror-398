"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Authentication handler for UniversalClient.
"""

import base64
import time
from typing import Dict, Optional

try:
    import jwt
except ImportError:
    jwt = None

try:
    from mcp_security_framework import (
        create_jwt_token,
        extract_roles_from_cert,
    )

    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False
    create_jwt_token = None
    extract_roles_from_cert = None


class AuthHandler:
    """Handler for client authentication methods."""

    def __init__(self, security_config: Dict, cert_manager=None):
        """
        Initialize authentication handler.
        
        Args:
            security_config: Security configuration dictionary
            cert_manager: Optional certificate manager instance
        """
        self.security_config = security_config
        self.cert_manager = cert_manager
        self.current_token: Optional[str] = None
        self.token_expiry: Optional[float] = None

    async def authenticate_api_key(self) -> None:
        """Authenticate using API key."""
        api_key_config = self.security_config.get("api_key", {})
        api_key = api_key_config.get("key")

        if not api_key:
            raise ValueError("API key not provided in configuration")

        # Store API key for requests
        self.current_token = api_key
        print(f"Authenticated with API key: {api_key[:8]}...")

    async def authenticate_jwt(self) -> None:
        """Authenticate using JWT token."""
        jwt_config = self.security_config.get("jwt", {})

        # Check if we have a stored token that's still valid
        if (
            self.current_token
            and self.token_expiry
            and time.time() < self.token_expiry
        ):
            print("Using existing JWT token")
            return

        # Get credentials for JWT
        username = jwt_config.get("username")
        password = jwt_config.get("password")
        secret = jwt_config.get("secret")

        if not all([username, password, secret]):
            raise ValueError("JWT credentials not provided in configuration")

        # Create JWT token
        if SECURITY_FRAMEWORK_AVAILABLE and create_jwt_token:
            self.current_token = create_jwt_token(
                username, secret, expiry_hours=jwt_config.get("expiry_hours", 24)
            )
        elif jwt:
            # Simple JWT creation (for demonstration)
            payload = {
                "username": username,
                "exp": time.time()
                + (jwt_config.get("expiry_hours", 24) * 3600),
            }
            self.current_token = jwt.encode(payload, secret, algorithm="HS256")
        else:
            raise ValueError("JWT library not available")

        self.token_expiry = time.time() + (
            jwt_config.get("expiry_hours", 24) * 3600
        )
        print(f"Authenticated with JWT token: {self.current_token[:20]}...")

    async def authenticate_certificate(self) -> None:
        """Authenticate using client certificate."""
        cert_config = self.security_config.get("certificate", {})

        cert_file = cert_config.get("cert_file")
        key_file = cert_config.get("key_file")

        if not cert_file or not key_file:
            raise ValueError("Certificate files not provided in configuration")

        # Validate certificate
        if SECURITY_FRAMEWORK_AVAILABLE and self.cert_manager:
            try:
                cert_info = self.cert_manager.validate_certificate(cert_file, key_file)
                print(f"Certificate validated: {cert_info.get('subject', 'Unknown')}")

                # Extract roles from certificate
                if extract_roles_from_cert:
                    roles = extract_roles_from_cert(cert_file)
                    if roles:
                        print(f"Certificate roles: {roles}")
            except Exception as e:
                print(f"Warning: Certificate validation failed: {e}")

        print("Certificate authentication prepared")

    async def authenticate_basic(self) -> None:
        """Authenticate using basic authentication."""
        basic_config = self.security_config.get("basic", {})
        username = basic_config.get("username")
        password = basic_config.get("password")

        if not username or not password:
            raise ValueError("Basic auth credentials not provided in configuration")

        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.current_token = f"Basic {credentials}"
        print(f"Authenticated with basic auth: {username}")

    def get_auth_headers(self, auth_method: str) -> Dict[str, str]:
        """
        Get authentication headers for requests.
        
        Args:
            auth_method: Authentication method name
            
        Returns:
            Dictionary with authentication headers
        """
        headers = {"Content-Type": "application/json"}

        if not self.current_token:
            return headers

        if auth_method == "api_key":
            api_key_config = self.security_config.get("api_key", {})
            header_name = api_key_config.get("header", "X-API-Key")
            headers[header_name] = self.current_token
        elif auth_method == "jwt":
            headers["Authorization"] = f"Bearer {self.current_token}"
        elif auth_method == "basic":
            headers["Authorization"] = self.current_token

        return headers

