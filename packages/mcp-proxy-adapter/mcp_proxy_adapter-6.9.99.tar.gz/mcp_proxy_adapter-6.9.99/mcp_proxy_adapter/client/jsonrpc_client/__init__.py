"""JSON-RPC client package facade.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from mcp_proxy_adapter.client.jsonrpc_client.client import JsonRpcClient
from mcp_proxy_adapter.client.jsonrpc_client.openapi_validator import OpenAPIValidator
from mcp_proxy_adapter.client.jsonrpc_client.schema_generator import (
    SchemaRequestGenerator,
    MethodInfo,
    ParameterInfo,
)
from mcp_proxy_adapter.client.jsonrpc_client.exceptions import (
    ClientError,
    SchemaGeneratorError,
    MethodNotFoundError,
    RequiredParameterMissingError,
    InvalidParameterTypeError,
    InvalidParameterValueError,
    ClientConnectionError,
    ClientRequestError,
    SchemaValidationError,
)
from mcp_proxy_adapter.client.jsonrpc_client.queue_status import QueueJobStatus

__all__ = [
    "JsonRpcClient",
    "OpenAPIValidator",
    "SchemaRequestGenerator",
    "MethodInfo",
    "ParameterInfo",
    "ClientError",
    "SchemaGeneratorError",
    "MethodNotFoundError",
    "RequiredParameterMissingError",
    "InvalidParameterTypeError",
    "InvalidParameterValueError",
    "ClientConnectionError",
    "ClientRequestError",
    "SchemaValidationError",
    "QueueJobStatus",
]
