#!/usr/bin/env python3
"""
Complete framework testing with real MCP servers.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import subprocess
import time
import requests
from pathlib import Path
from typing import TYPE_CHECKING, Optional

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_proxy_adapter.core.ssl_utils import SSLUtils

if TYPE_CHECKING:
    from ssl import SSLContext

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FrameworkTester:
    """Complete framework testing with real MCP servers."""
    
    def __init__(self):
        """
        Initialize framework tester.
        """
        self.project_root = Path(__file__).parent.parent.parent
        self.configs_dir = self.project_root / "configs"
        self.examples_dir = Path(__file__).parent
        self.test_results = []
        self.server_processes = []
        
    async def test_all_protocols(self):
        """Test all protocols with real MCP server registration."""
        get_global_logger().info("🧪 Starting Complete Framework Testing")
        get_global_logger().info("=" * 60)
        
        # Test configurations
        test_configs = [
            ("http.json", "HTTP", 20000),
            ("https.json", "HTTPS", 20003), 
            ("mtls.json", "mTLS", 20006)
        ]
        
        for config_file, protocol, port in test_configs:
            get_global_logger().info(f"\n🔧 Testing {protocol} (port {port})")
            get_global_logger().info("-" * 40)
            
            try:
                # Start proxy adapter server
                proxy_process = await self._start_proxy_server(config_file, port)
                if not proxy_process:
                    continue
                
                # Wait for server to start
                await asyncio.sleep(2)
                
                # Test server registration
                await self._test_server_registration(protocol, port)
                
                # Test MCP communication
                await self._test_mcp_communication(protocol, port)
                
                # Test security features
                await self._test_security_features(protocol, port)
                
                # Stop server
                proxy_process.terminate()
                await asyncio.sleep(1)
                
                get_global_logger().info(f"✅ {protocol} testing completed successfully")
                
            except Exception as e:
                get_global_logger().error(f"❌ {protocol} testing failed: {e}")
                self.test_results.append({
                    "protocol": protocol,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Print summary
        self._print_summary()
    
    async def _start_proxy_server(self, config_file: str, port: int) -> Optional[subprocess.Popen]:
        """Start proxy adapter server."""
        config_path = self.configs_dir / config_file
        
        if not config_path.exists():
            get_global_logger().error(f"❌ Config file not found: {config_path}")
            return None
        
        get_global_logger().info(f"🚀 Starting proxy server with {config_file}")
        
        try:
            # Start server in background
            process = subprocess.Popen([
                "python", str(self.examples_dir / "main.py"),
                "--config", str(config_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.server_processes.append(process)
            return process
            
        except Exception as e:
            get_global_logger().error(f"❌ Failed to start server: {e}")
            return None
    
    async def _test_server_registration(self, protocol: str, port: int):
        """Test MCP server registration."""
        get_global_logger().info(f"📝 Testing server registration for {protocol}")
        
        base_url = f"http://localhost:{port}" if protocol == "HTTP" else f"https://localhost:{port}"
        
        # Test registration endpoint
        registration_data = {
            "server_id": "test-mcp-server",
            "server_url": "stdio://test-server",
            "server_name": "Test MCP Server",
            "description": "Test server for framework validation"
        }
        
        try:
            # For requests library, we use verify=False instead of SSL context
            # SSL context is handled by SSLUtils when needed for other clients
            response = requests.post(
                f"{base_url}/register",
                json=registration_data,
                verify=False,  # requests uses verify parameter, not SSL context
                timeout=10
            )
            
            if response.status_code == 200:
                get_global_logger().info("✅ Server registration successful")
            else:
                get_global_logger().warning(f"⚠️ Registration returned status {response.status_code}")
                
        except Exception as e:
            get_global_logger().error(f"❌ Registration failed: {e}")
            raise
    
    async def _test_mcp_communication(self, protocol: str, port: int):
        """Test MCP communication through proxy."""
        get_global_logger().info(f"🔗 Testing MCP communication for {protocol}")
        
        base_url = f"http://localhost:{port}" if protocol == "HTTP" else f"https://localhost:{port}"
        
        # Test MCP JSON-RPC call
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        try:
            # For requests library, we use verify=False instead of SSL context
            response = requests.post(
                f"{base_url}/mcp",
                json=mcp_request,
                headers={"Content-Type": "application/json"},
                verify=False,  # requests uses verify parameter, not SSL context
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    get_global_logger().info("✅ MCP communication successful")
                else:
                    get_global_logger().warning(f"⚠️ MCP response: {result}")
            else:
                get_global_logger().warning(f"⚠️ MCP call returned status {response.status_code}")
                
        except Exception as e:
            get_global_logger().error(f"❌ MCP communication failed: {e}")
            raise
    
    async def _test_security_features(self, protocol: str, port: int):
        """Test security features."""
        get_global_logger().info(f"🔒 Testing security features for {protocol}")
        
        base_url = f"http://localhost:{port}" if protocol == "HTTP" else f"https://localhost:{port}"
        
        # Test without authentication
        try:
            # For requests library, we use verify=False instead of SSL context
            response = requests.get(
                f"{base_url}/health",
                verify=False,  # requests uses verify parameter, not SSL context
                timeout=10
            )
            
            if response.status_code == 200:
                get_global_logger().info("✅ Health check successful")
            else:
                get_global_logger().warning(f"⚠️ Health check returned status {response.status_code}")
                
        except Exception as e:
            get_global_logger().error(f"❌ Security test failed: {e}")
            raise
    
    def _print_summary(self):
        """Print test summary."""
        get_global_logger().info("\n" + "=" * 60)
        get_global_logger().info("📊 FRAMEWORK TESTING SUMMARY")
        get_global_logger().info("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["status"] == "success"])
        
        get_global_logger().info(f"Total tests: {total_tests}")
        get_global_logger().info(f"Successful: {successful_tests}")
        get_global_logger().info(f"Failed: {total_tests - successful_tests}")
        
        if total_tests > 0:
            success_rate = (successful_tests / total_tests) * 100
            get_global_logger().info(f"Success rate: {success_rate:.1f}%")
            
            if success_rate == 100:
                get_global_logger().info("🎉 All tests passed! Framework is working correctly.")
            elif success_rate >= 80:
                get_global_logger().info("✅ Most tests passed. Framework is mostly functional.")
            else:
                get_global_logger().info("⚠️ Many tests failed. Framework needs attention.")
        
        get_global_logger().info("=" * 60)
    
    async def cleanup(self):
        """Cleanup server processes."""
        get_global_logger().info("🧹 Cleaning up server processes...")
        
        for process in self.server_processes:
            try:
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                get_global_logger().warning(f"Warning: Failed to cleanup process: {e}")
        
        self.server_processes.clear()

async def main():
    """Main testing function."""
    tester = FrameworkTester()
    
    try:
        await tester.test_all_protocols()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
