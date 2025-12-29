"""
Custom OpenAPI schema generator for MCP Microservice compatible with MCP-Proxy.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""


from fastapi import FastAPI
from typing import Dict, Any

# from mcp_proxy_adapter.api.openapi import (
#     CustomOpenAPIGenerator,
#     register_openapi_generator,
#     get_openapi_generator,
#     list_openapi_generators,
# )


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema for the application.

    Args:
        app: FastAPI application instance

    Returns:
        Generated OpenAPI schema
    """
    from mcp_proxy_adapter.api.openapi.openapi_generator import CustomOpenAPIGenerator
    generator = CustomOpenAPIGenerator()
    return generator.generate(app)


def custom_openapi_with_fallback(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with fallback to default generator.

    Args:
        app: FastAPI application instance

    Returns:
        Generated OpenAPI schema
    """
    try:
        return custom_openapi(app)
    except Exception as e:
        from mcp_proxy_adapter.core.logging import get_global_logger
        logger = get_global_logger()
        logger.warning(f"Custom OpenAPI generation failed, using fallback: {e}")
        
        # Fallback to default FastAPI OpenAPI generator
        from fastapi.openapi.utils import get_openapi
        return get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
