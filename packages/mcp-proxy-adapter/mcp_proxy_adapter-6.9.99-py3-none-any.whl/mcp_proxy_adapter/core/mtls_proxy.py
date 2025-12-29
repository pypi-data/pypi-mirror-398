"""
mTLS Proxy for MCP Proxy Adapter

This module provides mTLS proxy functionality that accepts mTLS connections
and proxies them to the internal hypercorn server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from .logging import get_global_logger
from .ssl_utils import SSLUtils

logger = logging.getLogger(__name__)


class MTLSProxy:
    """
    mTLS Proxy that accepts mTLS connections and proxies them to internal server.
    """
    
    def __init__(
        self,
                 external_host: str,
                 external_port: int,
                 internal_host: str = "127.0.0.1",
                 internal_port: int = 9000,
                 cert_file: Optional[str] = None,
                 key_file: Optional[str] = None,
        ca_cert: Optional[str] = None,
    ):
        """
        Initialize mTLS Proxy.
        
        Args:
            external_host: External host to bind to
            external_port: External port to bind to
            internal_host: Internal server host
            internal_port: Internal server port
            cert_file: Server certificate file
            key_file: Server private key file
            ca_cert: CA certificate file for client verification
        """
        self.external_host = external_host
        self.external_port = external_port
        self.internal_host = internal_host
        self.internal_port = internal_port
        self.cert_file = cert_file
        self.key_file = key_file
        self.ca_cert = ca_cert
        self.server = None
        
    async def start(self):
        """Start the mTLS proxy server."""
        try:
            # Create SSL context
            ssl_context = SSLUtils.create_ssl_context(
                cert_file=self.cert_file,
                key_file=self.key_file,
                ca_cert=self.ca_cert,
                verify_client=bool(self.ca_cert),
                min_tls_version="TLSv1.2",
            )
                
            # Start server
            self.server = await asyncio.start_server(
                self._handle_client,
                self.external_host,
                self.external_port,
                ssl=ssl_context,
            )
            
            get_global_logger().info(
                f"🔐 mTLS Proxy started on {self.external_host}:{self.external_port}"
            )
            get_global_logger().info(
                f"🌐 Proxying to {self.internal_host}:{self.internal_port}"
            )
            
        except Exception as e:
            get_global_logger().error(f"❌ Failed to start mTLS proxy: {e}")
            raise
                
    async def _proxy_data(self, reader, writer, direction):
        """Proxy data between reader and writer."""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except Exception as e:
            get_global_logger().debug(f"Proxy connection closed ({direction}): {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _handle_client(self, reader, writer):
        """
        Handle incoming client connection.

        Args:
            reader: Client reader stream
            writer: Client writer stream
        """
        internal_reader = None
        internal_writer = None

        try:
            # Connect to internal server
            internal_reader, internal_writer = await asyncio.open_connection(
                self.internal_host, self.internal_port
            )

            # Create bidirectional proxy tasks
            client_to_server = asyncio.create_task(
                self._proxy_data(reader, internal_writer, "client->server")
            )
            server_to_client = asyncio.create_task(
                self._proxy_data(internal_reader, writer, "server->client")
            )

            # Wait for either direction to complete
            done, pending = await asyncio.wait(
                [client_to_server, server_to_client],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            # Wait for cancellation
            await asyncio.gather(*pending, return_exceptions=True)

        except Exception as e:
            get_global_logger().debug(f"Client connection error: {e}")
        finally:
            # Clean up connections
            if internal_writer:
                try:
                    internal_writer.close()
                    await internal_writer.wait_closed()
                except Exception:
                    pass
            if writer:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass


async def start_mtls_proxy(
    config: Dict[str, Any], internal_port: Optional[int] = None
) -> Optional[MTLSProxy]:
    """
    Start mTLS proxy from configuration.

    Args:
        config: Configuration dictionary
        internal_port: Internal server port (hypercorn port). If not provided,
                      will be calculated as external_port + 1000

    Returns:
        MTLSProxy instance if started successfully, None otherwise
    """
    try:
        server_config = config.get("server", {})
        transport_config = config.get("transport", {})
        ssl_config = config.get("ssl", {})

        # Get external host and port
        external_host = server_config.get("host", "0.0.0.0")
        external_port = server_config.get("port", 8001)

        # Get internal port (use provided or calculate)
        if internal_port is None:
            internal_port = external_port + 1000

        # Get certificate paths - try multiple locations
        cert_file = (
            ssl_config.get("cert_file")
            or transport_config.get("ssl", {}).get("cert_file")
            or transport_config.get("cert_file")
        )
        key_file = (
            ssl_config.get("key_file")
            or transport_config.get("ssl", {}).get("key_file")
            or transport_config.get("key_file")
        )
        ca_cert = (
            ssl_config.get("ca_cert")
            or transport_config.get("ssl", {}).get("ca_cert")
            or transport_config.get("ca_cert")
        )

        if not cert_file or not key_file:
            get_global_logger().warning(
                "mTLS certificates not found, skipping mTLS proxy"
            )
            return None

        # Create and start proxy
        proxy = MTLSProxy(
            external_host=external_host,
            external_port=external_port,
            internal_host="127.0.0.1",
            internal_port=internal_port,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert=ca_cert,
        )

        await proxy.start()
        return proxy

    except Exception as e:
        get_global_logger().error(f"Failed to start mTLS proxy: {e}")
        return None
