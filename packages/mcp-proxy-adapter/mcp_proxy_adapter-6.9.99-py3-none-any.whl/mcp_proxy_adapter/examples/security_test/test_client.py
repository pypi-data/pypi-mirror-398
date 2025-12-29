"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Main security test client for comprehensive testing.
"""

import time
from pathlib import Path

from aiohttp import ClientSession, ClientTimeout, TCPConnector

from .test_result import TestResult
from .ssl_context_manager import SSLContextManager
from .auth_manager import AuthManager


class SecurityTestClient:
    """Security test client for comprehensive testing."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize security test client.

        Args:
            base_url: Base URL for the server
        """
        self.base_url = base_url
        self.session: Optional[ClientSession] = None
        self.test_results: List[TestResult] = []
        
        # Initialize managers
        project_root = Path(__file__).parent.parent.parent.parent
        self.ssl_manager = SSLContextManager(project_root)
        self.auth_manager = AuthManager()

    async def __aenter__(self):
        """Async context manager entry."""
        timeout = ClientTimeout(total=30)
        # Create SSL context only for HTTPS URLs
        if self.base_url.startswith('https://'):
            # Check if this is mTLS (ports 20006, 20007, 20008 are mTLS test ports)
            if any(port in self.base_url for port in ['20006', '20007', '20008']):
                # Use mTLS context with client certificates
                ssl_context = self.ssl_manager.create_ssl_context_for_mtls()
            else:
                # Use regular HTTPS context
                ssl_context = self.ssl_manager.create_ssl_context()
            connector = TCPConnector(ssl=ssl_context)
        else:
            # For HTTP URLs, use default connector without SSL
            connector = TCPConnector()
        
        # Create session
        self.session = ClientSession(timeout=timeout, connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def test_health_check(
        self, server_url: str, auth_type: str = "none", **kwargs
    ) -> TestResult:
        """Test health check endpoint."""
        start_time = time.time()
        test_name = f"Health Check ({auth_type})"
        try:
            headers = self.auth_manager.create_auth_headers(auth_type, **kwargs)
            async with self.session.get(
                f"{server_url}/health", headers=headers
            ) as response:
                duration = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=True,
                        status_code=response.status,
                        response_data=data,
                        duration=duration
                    )
                else:
                    error_text = await response.text()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=False,
                        status_code=response.status,
                        error_message=f"HTTP {response.status}: {error_text}",
                        duration=duration
                    )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message=str(e),
                duration=duration
            )

    async def test_echo_command(
        self, server_url: str, auth_type: str = "none", **kwargs
    ) -> TestResult:
        """Test echo command endpoint."""
        start_time = time.time()
        test_name = f"Echo Command ({auth_type})"
        try:
            headers = self.auth_manager.create_auth_headers(auth_type, **kwargs)
            payload = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Hello from security test client"},
                "id": 1
            }
            async with self.session.post(
                f"{server_url}/api/jsonrpc", json=payload, headers=headers
            ) as response:
                duration = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=True,
                        status_code=response.status,
                        response_data=data,
                        duration=duration
                    )
                else:
                    error_text = await response.text()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=False,
                        status_code=response.status,
                        error_message=f"HTTP {response.status}: {error_text}",
                        duration=duration
                    )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message=str(e),
                duration=duration
            )


