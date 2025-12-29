"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

HTTP request handler for UniversalClient.
"""

import asyncio
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import aiohttp

try:
    from mcp_security_framework import SecurityManager

    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False
    SecurityManager = None


class RequestHandler:
    """Handler for HTTP requests."""

    def __init__(
        self,
        base_url: str,
        timeout: int,
        retry_attempts: int,
        retry_delay: float,
        session: Optional[aiohttp.ClientSession],
        security_manager=None,
    ):
        """
        Initialize request handler.
        
        Args:
            base_url: Base URL for requests
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts
            retry_delay: Delay between retries in seconds
            session: aiohttp client session
            security_manager: Optional security manager instance
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.session = session
        self.security_manager = security_manager

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
        url = urljoin(self.base_url, endpoint)

        try:
            for attempt in range(self.retry_attempts):
                try:
                    async with self.session.request(
                        method,
                        url,
                        json=data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as response:
                        result = await response.json()

                        # Validate response if security framework available
                        if (
                            SECURITY_FRAMEWORK_AVAILABLE
                            and self.security_manager
                        ):
                            self.security_manager.validate_server_response(
                                dict(response.headers)
                            )

                        if response.status >= 400:
                            print(
                                f"Request failed with status {response.status}: {result}"
                            )
                            return {"error": result, "status": response.status}

                        return result

                except Exception as e:
                    print(f"Request attempt {attempt + 1} failed: {e}")
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self.retry_delay)
                    else:
                        raise
        except Exception as e:
            print(f"Request failed: {e}")
            raise

