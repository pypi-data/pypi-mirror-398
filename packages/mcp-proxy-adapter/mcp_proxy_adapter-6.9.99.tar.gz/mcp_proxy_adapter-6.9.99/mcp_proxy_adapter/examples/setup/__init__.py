"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Test environment setup package for MCP Proxy Adapter.
"""

from .config_validator import ConfigurationValidator
from .test_files_generator import create_test_files
from .config_generator import create_configuration_documentation, generate_enhanced_configurations
from .certificate_manager import generate_certificates_with_framework
from .test_runner import test_proxy_registration, run_full_test_suite
from .environment_setup import setup_test_environment

__all__ = [
    "ConfigurationValidator",
    "create_test_files", 
    "create_configuration_documentation",
    "generate_enhanced_configurations",
    "generate_certificates_with_framework",
    "test_proxy_registration",
    "run_full_test_suite",
    "setup_test_environment",
]
