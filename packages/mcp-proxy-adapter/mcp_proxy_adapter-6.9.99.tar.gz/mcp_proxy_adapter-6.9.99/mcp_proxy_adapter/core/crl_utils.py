"""
CRL Utilities Module

This module provides utilities for working with Certificate Revocation Lists (CRL).
Supports both file-based and URL-based CRL sources.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
Version: 1.0.0
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Union, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import mcp_security_framework CRL utilities
try:
    from mcp_security_framework.utils.cert_utils import (
        is_certificate_revoked,
        validate_certificate_against_crl,
        is_crl_valid,
        get_crl_info,
    )

    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False

logger = logging.getLogger(__name__)


class CRLManager:
    """
    Manager for Certificate Revocation Lists (CRL).

    Supports both file-based and URL-based CRL sources.
    Automatically downloads CRL from URLs and caches them locally.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize CRL manager.

        Args:
            config: Configuration dictionary containing CRL settings
        """
        self.config = config
        self.crl_enabled = config.get("crl_enabled", False)

        # Only analyze CRL paths if certificates are enabled
        certificates_enabled = config.get("certificates_enabled", True)
        if certificates_enabled and self.crl_enabled:
            self.crl_path = config.get("crl_path")
            self.crl_url = config.get("crl_url")
            self.crl_validity_days = config.get("crl_validity_days", 30)
        else:
            # Don't analyze CRL paths if certificates are disabled
            self.crl_path = None
            self.crl_url = None
            self.crl_validity_days = 30

        # Cache for downloaded CRL files
        self._crl_cache: Dict[str, str] = {}

        # Setup HTTP session with retry strategy
        self._setup_http_session()

        get_global_logger().info(
            f"CRL Manager initialized - enabled: {self.crl_enabled}, certificates_enabled: {certificates_enabled}"
        )

    def _setup_http_session(self):
        """Setup HTTP session with retry strategy for CRL downloads."""
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set timeout
        self.session.timeout = 30

    def get_crl_data(self) -> Optional[Union[str, bytes, Path]]:
        """
        Get CRL data from configured source.

        Returns:
            CRL data as string, bytes, or Path, or None if not available

        Raises:
            ValueError: If CRL is enabled but no source is configured
            FileNotFoundError: If CRL file is not found
            requests.RequestException: If CRL download fails
        """
        if not self.crl_enabled:
            get_global_logger().debug("CRL is disabled, skipping CRL check")
            return None

        # Check if CRL URL is configured
        if self.crl_url:
            return self._get_crl_from_url()

        # Check if CRL file path is configured
        if self.crl_path:
            return self._get_crl_from_file()

        # If CRL is enabled but no source is configured, this is an error
        if self.crl_enabled:
            raise ValueError(
                "CRL is enabled but neither crl_path nor crl_url is configured"
            )

        return None

    def _get_crl_from_url(self) -> str:
        """
        Download CRL from URL.

        Returns:
            Path to downloaded CRL file

        Raises:
            requests.RequestException: If download fails
            ValueError: If downloaded data is not valid CRL
        """
        try:
            get_global_logger().info(f"Downloading CRL from URL: {self.crl_url}")

            # Download CRL
            response = self.session.get(self.crl_url)
            response.raise_for_status()

            # Validate content type
            content_type = response.headers.get("content-type", "").lower()
            if (
                "application/pkix-crl" not in content_type
                and "application/x-pkcs7-crl" not in content_type
            ):
                get_global_logger().warning(f"Unexpected content type for CRL: {content_type}")

            # Save to temporary file
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".crl", delete=False
            ) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            # Validate CRL format
            if SECURITY_FRAMEWORK_AVAILABLE:
                try:
                    is_crl_valid(temp_file_path)
                    get_global_logger().info(
                        f"CRL downloaded and validated successfully from {self.crl_url}"
                    )
                except Exception as e:
                    os.unlink(temp_file_path)
                    raise ValueError(f"Downloaded CRL is not valid: {e}")
            else:
                get_global_logger().warning(
                    "mcp_security_framework not available, skipping CRL validation"
                )

            # Cache the file path
            self._crl_cache[self.crl_url] = temp_file_path

            return temp_file_path

        except requests.RequestException as e:
            get_global_logger().error(f"Failed to download CRL from {self.crl_url}: {e}")
            raise
        except Exception as e:
            get_global_logger().error(f"CRL download failed: {e}")
            raise

    def _get_crl_from_file(self) -> str:
        """
        Get CRL from file path.

        Returns:
            Path to CRL file

        Raises:
            FileNotFoundError: If CRL file is not found
            ValueError: If CRL file is not valid
        """
        if not os.path.exists(self.crl_path):
            raise FileNotFoundError(f"CRL file not found: {self.crl_path}")

        # Validate CRL format
        if SECURITY_FRAMEWORK_AVAILABLE:
            try:
                is_crl_valid(self.crl_path)
                get_global_logger().info(f"CRL file validated successfully: {self.crl_path}")
            except Exception as e:
                raise ValueError(f"CRL file is not valid: {e}")
        else:
            get_global_logger().warning(
                "mcp_security_framework not available, skipping CRL validation"
            )

        return self.crl_path

    def is_certificate_revoked(self, cert_path: str) -> bool:
        """
        Check if certificate is revoked according to CRL.

        Args:
            cert_path: Path to certificate file

        Returns:
            True if certificate is revoked, False otherwise

        Raises:
            ValueError: If CRL is enabled but not available
            FileNotFoundError: If certificate file is not found
        """
        if not self.crl_enabled:
            return False

        if not SECURITY_FRAMEWORK_AVAILABLE:
            get_global_logger().warning("mcp_security_framework not available, skipping CRL check")
            return False

        try:
            crl_data = self.get_crl_data()
            if not crl_data:
                get_global_logger().warning("CRL is enabled but no CRL data is available")
                return False

            is_revoked = is_certificate_revoked(cert_path, crl_data)

            if is_revoked:
                get_global_logger().warning(f"Certificate is revoked according to CRL: {cert_path}")
            else:
                get_global_logger().debug(
                    f"Certificate is not revoked according to CRL: {cert_path}"
                )

            return is_revoked

        except Exception as e:
            get_global_logger().error(f"CRL check failed for certificate {cert_path}: {e}")
            # For security, consider certificate invalid if CRL check fails
            return True

    def validate_certificate_against_crl(self, cert_path: str) -> Dict[str, Any]:
        """
        Validate certificate against CRL and return detailed status.

        Args:
            cert_path: Path to certificate file

        Returns:
            Dictionary containing validation results

        Raises:
            ValueError: If CRL is enabled but not available
            FileNotFoundError: If certificate file is not found
        """
        if not self.crl_enabled:
            return {
                "is_revoked": False,
                "crl_checked": False,
                "crl_source": None,
                "message": "CRL check is disabled",
            }

        if not SECURITY_FRAMEWORK_AVAILABLE:
            get_global_logger().warning(
                "mcp_security_framework not available, skipping CRL validation"
            )
            return {
                "is_revoked": False,
                "crl_checked": False,
                "crl_source": None,
                "message": "mcp_security_framework not available",
            }

        try:
            crl_data = self.get_crl_data()
            if not crl_data:
                get_global_logger().warning("CRL is enabled but no CRL data is available")
                return {
                    "is_revoked": True,  # For security, consider invalid if CRL unavailable
                    "crl_checked": False,
                    "crl_source": None,
                    "message": "CRL is enabled but not available",
                }

            # Get CRL source info
            crl_source = self.crl_url if self.crl_url else self.crl_path

            # Validate certificate against CRL
            result = validate_certificate_against_crl(cert_path, crl_data)

            result["crl_checked"] = True
            result["crl_source"] = crl_source

            return result

        except Exception as e:
            get_global_logger().error(f"CRL validation failed for certificate {cert_path}: {e}")
            # For security, consider certificate invalid if CRL validation fails
            return {
                "is_revoked": True,
                "crl_checked": False,
                "crl_source": self.crl_url if self.crl_url else self.crl_path,
                "message": f"CRL validation failed: {e}",
            }

    def get_crl_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the configured CRL.

        Returns:
            Dictionary containing CRL information, or None if CRL is not available
        """
        if not self.crl_enabled:
            return None

        if not SECURITY_FRAMEWORK_AVAILABLE:
            get_global_logger().warning("mcp_security_framework not available, cannot get CRL info")
            return None

        try:
            crl_data = self.get_crl_data()
            if not crl_data:
                return None

            return get_crl_info(crl_data)

        except Exception as e:
            get_global_logger().error(f"Failed to get CRL info: {e}")
            return None

    def cleanup_cache(self):
        """Clean up temporary CRL files."""
        for url, temp_path in self._crl_cache.items():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    get_global_logger().debug(f"Cleaned up temporary CRL file: {temp_path}")
            except Exception as e:
                get_global_logger().warning(f"Failed to cleanup temporary CRL file {temp_path}: {e}")

        self._crl_cache.clear()

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.cleanup_cache()
