"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Authentication management for proxy registration.
"""

from typing import Dict, Any

from mcp_proxy_adapter.core.logging import get_global_logger


class AuthManager:
    """Manager for authentication in proxy registration."""

    def __init__(self, client_security, registration_config: Dict[str, Any]):
        """
        Initialize authentication manager.

        Args:
            client_security: Client security manager instance
            registration_config: Registration configuration
        """
        self.client_security = client_security
        self.registration_config = registration_config
        self.logger = get_global_logger()
