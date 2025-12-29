#!/usr/bin/env python3
"""
Test mTLS Server for Full Application Example
Simple HTTPS server with mTLS for testing curl commands.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import sys
import json
import socket
import threading
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import TYPE_CHECKING

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from mcp_proxy_adapter.core.ssl_utils import SSLUtils

if TYPE_CHECKING:
    from ssl import SSLContext

class TestMTLSHandler(BaseHTTPRequestHandler):
    """Test handler for mTLS requests."""
    
    
    
    def get_client_cert_info(self):
        """Get client certificate information."""
        try:
            cert = self.connection.getpeercert()
            if cert:
                return {
                    "subject": dict(x[0] for x in cert.get('subject', [])),
                    "issuer": dict(x[0] for x in cert.get('issuer', [])),
                    "serial": cert.get('serialNumber'),
                    "not_before": cert.get('notBefore'),
                    "not_after": cert.get('notAfter')
                }
        except Exception:
            pass
        return None
    

class TestMTLSServer:
    """Test mTLS server for the full application example."""
    
    def __init__(self, config_path: str):
        """
        Initialize test mTLS server.
        
        Args:
            config_path: Path to server configuration file
        """
        self.config_path = config_path
        self.config = self.load_config()
        self.server = None
        self.thread = None
        
    def load_config(self):
        """
        Load configuration from file.
        
        Returns:
            Dictionary with server configuration
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            json.JSONDecodeError: If configuration file is invalid JSON
        """
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def create_ssl_context(self):
        """
        Create SSL context for mTLS connections using security framework.
        
        Returns:
            Configured SSL context with server certificate and optional client verification
            
        Raises:
            FileNotFoundError: If certificate files don't exist
            ValueError: If SSL context creation fails
        """
        ssl_config = self.config.get('ssl', {})
        
        cert_file = ssl_config.get('cert_file')
        key_file = ssl_config.get('key_file')
        ca_cert_file = ssl_config.get('ca_cert_file')
        verify_client = ssl_config.get('verify_client', False)
        ciphers = ssl_config.get('ciphers')
        
        # Create SSL context using security framework
        context = SSLUtils.create_ssl_context(
            cert_file=cert_file,
            key_file=key_file,
            ca_cert=ca_cert_file,
            verify_client=verify_client,
            cipher_suites=[ciphers] if ciphers else None,
            min_tls_version="TLSv1.2",
        )
        
        return context
    
    def start_server(self):
        """
        Start the mTLS server and begin serving requests.
        
        This method blocks until the server is stopped (Ctrl+C).
        Server will listen on the configured host and port.
        """
        server_config = self.config.get('server', {})
        host = server_config.get('host', '0.0.0.0')
        port = server_config.get('port', 8443)
        
        print(f"🚀 Starting mTLS Test Server")
        print(f"📁 Configuration: {self.config_path}")
        print(f"🌐 Server: {host}:{port}")
        print(f"🔐 mTLS: {'Enabled' if self.config.get('ssl', {}).get('verify_client', False) else 'Disabled'}")
        
        # Create server
        self.server = HTTPServer((host, port), TestMTLSHandler)
        
        # Configure SSL
        ssl_context = self.create_ssl_context()
        self.server.socket = ssl_context.wrap_socket(
            self.server.socket,
            server_side=True
        )
        
        print(f"✅ mTLS Test Server started on {host}:{port}")
        print(f"🔐 SSL Context configured")
        print(f"📜 Available endpoints:")
        print(f"  - GET  /health - Health check")
        print(f"  - GET  /echo   - Echo test")
        print(f"  - POST /echo   - Echo with data")
        print(f"\n🛑 Press Ctrl+C to stop the server")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped by user")
            self.server.shutdown()
    
    def start_background(self):
        """
        Start server in background thread.
        
        Returns:
            True if server started successfully, False otherwise
        """
        self.thread = threading.Thread(target=self.start_server, daemon=True)
        self.thread.start()
        time.sleep(1)  # Give server time to start
        return self.thread.is_alive()
    
    def stop_server(self):
        """
        Stop the server and wait for background thread to finish.
        
        This method gracefully shuts down the server and waits up to 5 seconds
        for the background thread to complete.
        """
        if self.server:
            self.server.shutdown()
        if self.thread:
            self.thread.join(timeout=5)

def main():
    """
    Main entry point for test mTLS server.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test mTLS Server")
    parser.add_argument("--config", required=True, help="Configuration file path")
    parser.add_argument("--background", action="store_true", help="Run in background")
    args = parser.parse_args()
    
    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    # Create and start server
    server = TestMTLSServer(str(config_path))
    
    if args.background:
        print("🔄 Starting server in background...")
        if server.start_background():
            print("✅ Server started in background")
            print("💡 Use Ctrl+C to stop")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping background server...")
                server.stop_server()
        else:
            print("❌ Failed to start server in background")
            return 1
    else:
        server.start_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
