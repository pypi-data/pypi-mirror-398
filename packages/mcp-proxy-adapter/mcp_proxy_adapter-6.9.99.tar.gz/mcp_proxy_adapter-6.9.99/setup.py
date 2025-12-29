#!/usr/bin/env python3
"""
Setup script for MCP Proxy Adapter.

Author: Vasiliy Zdanovskiy
Email: vasilyvz@gmail.com
"""

from setuptools import setup, find_packages
import os
import sys

# Read version from version.py file directly
def read_version():
    """Read project version from mcp_proxy_adapter/version.py."""
    version_path = os.path.join(os.path.dirname(__file__), "mcp_proxy_adapter", "version.py")
    if os.path.exists(version_path):
        with open(version_path, "r", encoding="utf-8") as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"').strip("'")
    return "6.9.0"

__version__ = read_version()
print(f"Building version: {__version__}")

# Read the README file
def read_readme():
    """Read long description from README.md."""
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# Read requirements
def read_requirements():
    """Read package requirements from requirements.txt."""
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

setup(
    name="mcp-proxy-adapter",
    version=__version__,
    description="Powerful JSON-RPC microservices framework with built-in security, authentication, proxy registration, and queue-backed command execution for long-running operations",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Vasiliy Zdanovskiy",
    author_email="vasilyvz@gmail.com",
    maintainer="Vasiliy Zdanovskiy",
    maintainer_email="vasilyvz@gmail.com",
    url="https://github.com/maverikod/mcp-proxy-adapter",
    project_urls={
        "Homepage": "https://github.com/maverikod/mcp-proxy-adapter",
        "Documentation": "https://github.com/maverikod/mcp-proxy-adapter#readme",
        "Source": "https://github.com/maverikod/mcp-proxy-adapter",
        "Tracker": "https://github.com/maverikod/mcp-proxy-adapter/issues",
        "PyPI": "https://pypi.org/project/mcp-proxy-adapter/",
    },
    packages=find_packages(include=["mcp_proxy_adapter*"]),
    package_data={
        "mcp_proxy_adapter": ["schemas/*.json"],
    },
    include_package_data=True,
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
            "pytest-mock>=3.10.0",
        ],
        "examples": [],
    },
    entry_points={
        "console_scripts": [
            "mcp-proxy-adapter=mcp_proxy_adapter.__main__:main",
            "adapter-cfg-gen=mcp_proxy_adapter.cli.commands.config_generate:main",
            "adapter-cfg-val=mcp_proxy_adapter.cli.commands.config_validate:main",
            "adapter-cfg-docs=mcp_proxy_adapter.cli.commands.config_docs:main",
            "mcp-config-generate=mcp_proxy_adapter.core.config.cli_generator:main",
        ],
        "mcp_proxy_adapter.examples": [
            "setup_test_environment=mcp_proxy_adapter.examples.setup_test_environment:main",
            "create_test_configs=mcp_proxy_adapter.examples.create_test_configs:main",
            "generate_certificates=mcp_proxy_adapter.examples.generate_all_certificates:main",
            "run_security_tests=mcp_proxy_adapter.examples.run_security_tests_fixed:main",
            "run_full_test_suite=mcp_proxy_adapter.examples.run_full_test_suite:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: FastAPI",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
    ],
    keywords=[
        "json-rpc",
        "microservices",
        "fastapi",
        "security",
        "authentication",
        "authorization",
        "proxy",
        "mcp",
        "mtls",
        "ssl",
        "rest",
        "api",
    ],
    license="MIT",
    zip_safe=False,
)
