"""
Module with utility functions for the microservice.
"""

import hashlib
import json
import os
import socket
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from mcp_proxy_adapter.core.logging import get_global_logger


















def check_port_availability(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    Checks if a port is available for binding.
    
    Args:
        host: Host address to check
        port: Port number to check
        timeout: Connection timeout in seconds
        
    Returns:
        True if port is available, False if port is in use
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result != 0  # True if connection failed (port is free)
    except Exception as e:
        get_global_logger().warning(f"Error checking port {port} on {host}: {e}")
        return True  # Assume port is available if check fails


def find_available_port(host: str, start_port: int, max_attempts: int = 100) -> Optional[int]:
    """
    Finds an available port starting from the specified port.
    
    Args:
        host: Host address to check
        start_port: Starting port number
        max_attempts: Maximum number of ports to check
        
    Returns:
        Available port number or None if no port found
    """
    for port in range(start_port, start_port + max_attempts):
        if check_port_availability(host, port):
            return port
    return None


def get_port_usage_info(port: int) -> str:
    """
    Gets information about what process is using a port.
    
    Args:
        port: Port number to check
        
    Returns:
        String with port usage information
    """
    try:
        import subprocess
        result = subprocess.run(
            ["lsof", "-i", f":{port}"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return f"Port {port} is used by:\n{result.stdout.strip()}"
        else:
            return f"Port {port} appears to be in use but process info unavailable"
    except Exception as e:
        return f"Port {port} is in use (unable to get process info: {e})"




