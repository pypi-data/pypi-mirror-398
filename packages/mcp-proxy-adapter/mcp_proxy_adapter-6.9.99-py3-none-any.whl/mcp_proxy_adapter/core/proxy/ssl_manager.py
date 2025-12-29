"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

SSL management for proxy registration.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from urllib.parse import urlparse

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.ssl_utils import SSLUtils

if TYPE_CHECKING:
    from ssl import SSLContext


class SSLManager:
    """Manager for SSL connections in proxy registration."""

    def __init__(self, client_security, registration_config: Dict[str, Any], config: Dict[str, Any], proxy_url: str):
        """
        Initialize SSL manager.

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

    def get_ssl_context(self) -> Optional["SSLContext"]:
        """
        Get SSL context for secure connections (alias for create_ssl_context).
        
        Returns:
            SSL context or None if SSL not needed
        """
        return self.create_ssl_context()

    def create_ssl_context(self) -> Optional["SSLContext"]:
        """
        Create SSL context for secure connections using registration SSL configuration.

        Returns:
            SSL context or None if SSL not needed
        """
        self.logger.info(f"🔍 [SSL] Creating SSL context for proxy URL: {self.proxy_url}")
        
        # Decide SSL strictly by proxy URL scheme: use SSL only for https proxy URLs
        try:
            parsed_url = urlparse(self.proxy_url) if self.proxy_url else None
            scheme = parsed_url.scheme if parsed_url else "http"
            self.logger.info(f"🔍 [SSL] Parsed proxy URL scheme: {scheme}")
            
            if scheme.lower() != "https":
                self.logger.info(f"🔍 [SSL] Proxy URL is HTTP ({scheme}), skipping SSL context creation for registration")
                return None
        except Exception as e:
            self.logger.warning(f"🔍 [SSL] Failed to parse proxy_url '{self.proxy_url}': {e}, assuming HTTP and skipping SSL context")
            return None
            
        if not self.client_security:
            self.logger.warning("🔍 [SSL] SSL context creation failed: client_security is None")
            return None

        try:
            # Check if SSL is enabled for registration
            # Support both old format (certificate) and new format (ssl)
            cert_config = self.registration_config.get("certificate", {})
            ssl_config_raw = self.registration_config.get("ssl", {})
            
            self.logger.info(f"🔍 [SSL] Registration certificate config (old format): {cert_config}")
            self.logger.info(f"🔍 [SSL] Registration ssl config (new format): {ssl_config_raw}")
            
            # Convert new format (ssl.cert, ssl.key, ssl.ca) to old format (cert_config, ssl_config)
            if ssl_config_raw and isinstance(ssl_config_raw, dict):
                # New format: ssl.cert, ssl.key, ssl.ca
                if not cert_config and (ssl_config_raw.get("cert") or ssl_config_raw.get("key")):
                    cert_config = {
                        "cert_file": ssl_config_raw.get("cert"),
                        "key_file": ssl_config_raw.get("key"),
                    }
                ssl_config = {}
                if ssl_config_raw.get("ca"):
                    ssl_config["ca_cert"] = ssl_config_raw.get("ca")
                if ssl_config_raw.get("dnscheck") is not None:
                    ssl_config["check_hostname"] = ssl_config_raw.get("dnscheck", False)
            else:
                ssl_config = {}

            self.logger.info(f"🔍 [SSL] Converted cert_config: {cert_config}")
            self.logger.info(f"🔍 [SSL] Converted ssl_config: {ssl_config}")

            # FALLBACK: if no explicit registration SSL/certs provided, reuse global SSL config
            if not cert_config and not ssl_config:
                global_ssl = self.config.get("security", {}).get("ssl", {}) or self.config.get("ssl", {})
                self.logger.info(f"🔍 [SSL] No registration SSL config, checking global SSL: {global_ssl}")
                if global_ssl:
                    # Map global ssl to registration-style configs
                    # Support both old format (cert_file, key_file) and new format (cert, key)
                    mapped_cert = {}
                    cert_file = global_ssl.get("cert") or global_ssl.get("cert_file")
                    key_file = global_ssl.get("key") or global_ssl.get("key_file")
                    if cert_file and key_file:
                        mapped_cert = {
                            "cert_file": cert_file,
                            "key_file": key_file,
                        }
                    mapped_ssl = {}
                    ca_cert = global_ssl.get("ca") or global_ssl.get("ca_cert")
                    if ca_cert:
                        mapped_ssl["ca_cert"] = ca_cert
                    if global_ssl.get("verify_client") is not None:
                        mapped_ssl["verify_mode"] = (
                            "CERT_REQUIRED" if global_ssl.get("verify_client") else "CERT_NONE"
                        )
                    cert_config = mapped_cert
                    ssl_config = mapped_ssl
                    self.logger.info(f"🔍 [SSL] Mapped global SSL to cert_config: {cert_config}, ssl_config: {ssl_config}")

            # Use client security manager to create SSL context
            if cert_config or ssl_config:
                self.logger.info(f"🔍 [SSL] Creating SSL context with cert_config: {cert_config}, ssl_config: {ssl_config}")
                ssl_context = self.client_security.create_ssl_context(
                    cert_config=cert_config,
                    ssl_config=ssl_config
                )
                if ssl_context:
                    self.logger.info(f"🔍 [SSL] SSL context created successfully. Protocol: {ssl_context.protocol}, verify_mode: {ssl_context.verify_mode}, check_hostname: {ssl_context.check_hostname}")
                    return ssl_context
                else:
                    self.logger.warning("🔍 [SSL] Failed to create SSL context for registration (returned None)")
                    return None
            else:
                self.logger.info("🔍 [SSL] No SSL configuration found for registration, creating default context (verify disabled)")
                return SSLUtils.create_client_ssl_context(
                    verify=False,
                    check_hostname=False,
                )

        except Exception as e:
            self.logger.error(f"🔍 [SSL] Error creating SSL context for registration: {e}", exc_info=True)
            return None
