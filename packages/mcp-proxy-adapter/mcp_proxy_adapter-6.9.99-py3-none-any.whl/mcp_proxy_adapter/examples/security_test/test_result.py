"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Test result data class for security testing.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TestResult:
    """Test result data class."""
    test_name: str
    server_url: str
    auth_type: str
    success: bool
    status_code: Optional[int] = None
    response_data: Optional[Dict] = None
    error_message: Optional[str] = None
    duration: float = 0.0
