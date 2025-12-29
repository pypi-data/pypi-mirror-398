"""
Proxy Registration Endpoints
This module provides proxy registration endpoints for testing.
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import time
import uuid

# In-memory registry for testing
_registry: Dict[str, Dict] = {}
router = APIRouter(prefix="/proxy", tags=["proxy"])


class ServerRegistration(BaseModel):
    """Server registration request model."""

    server_id: str
    server_url: str
    server_name: str
    description: Optional[str] = None
    version: Optional[str] = "1.0.0"
    capabilities: Optional[List[str]] = None
    endpoints: Optional[Dict[str, str]] = None
    auth_method: Optional[str] = "none"
    security_enabled: Optional[bool] = False


class ServerUnregistration(BaseModel):
    """Server unregistration request model."""

    server_key: str  # Use server_key directly


class HeartbeatData(BaseModel):
    """Heartbeat data model."""

    server_id: str
    server_key: str
    timestamp: Optional[int] = None
    status: Optional[str] = "healthy"


class RegistrationResponse(BaseModel):
    """Registration response model."""

    success: bool
    server_key: str
    message: str
    copy_number: int


class DiscoveryResponse(BaseModel):
    """Discovery response model."""

    success: bool
    servers: List[Dict]
    total: int
    active: int


@router.post("/register", response_model=RegistrationResponse)
async def register_server(data: ServerRegistration) -> RegistrationResponse:
    """Register a server with the proxy."""
    server_key = str(uuid.uuid4())
    copy_number = 1
    if data.server_id in _registry:
        copy_number = len(_registry[data.server_id]) + 1

    if data.server_id not in _registry:
        _registry[data.server_id] = {}

    _registry[data.server_id][server_key] = {
        "server_id": data.server_id,
        "server_url": data.server_url,
        "server_name": data.server_name,
        "description": data.description,
        "version": data.version,
        "capabilities": data.capabilities or [],
        "endpoints": data.endpoints or {},
        "auth_method": data.auth_method,
        "security_enabled": data.security_enabled,
        "registered_at": time.time(),
        "last_heartbeat": time.time(),
    }

    return RegistrationResponse(
        success=True,
        server_key=server_key,
        message=f"Server {data.server_name} registered successfully",
        copy_number=copy_number,
    )


@router.post("/unregister")
async def unregister_server(data: ServerUnregistration) -> Dict[str, Any]:
    """Unregister a server from the proxy."""
    for server_id, instances in _registry.items():
        if data.server_key in instances:
            del instances[data.server_key]
            if not instances:
                del _registry[server_id]
            return {"success": True, "message": "Server unregistered"}
    raise HTTPException(status_code=404, detail="Server not found")


@router.post("/heartbeat")
async def heartbeat(data: HeartbeatData) -> Dict[str, Any]:
    """Update server heartbeat."""
    for server_id, instances in _registry.items():
        if data.server_key in instances:
            instances[data.server_key]["last_heartbeat"] = data.timestamp or time.time()
            instances[data.server_key]["status"] = data.status
            return {"success": True, "message": "Heartbeat updated"}
    raise HTTPException(status_code=404, detail="Server not found")


@router.get("/discover", response_model=DiscoveryResponse)
async def discover_servers() -> DiscoveryResponse:
    """Discover all registered servers."""
    servers = []
    for server_id, instances in _registry.items():
        for server_key, server_data in instances.items():
            servers.append({**server_data, "server_key": server_key})

    active = sum(1 for s in servers if time.time() - s.get("last_heartbeat", 0) < 60)
    return DiscoveryResponse(
        success=True,
        servers=servers,
        total=len(servers),
        active=active,
    )


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get proxy status."""
    total_servers = sum(len(instances) for instances in _registry.values())
    active_servers = sum(
        1
        for instances in _registry.values()
        for server_data in instances.values()
        if time.time() - server_data.get("last_heartbeat", 0) < 60
    )
    return {
        "status": "running",
        "total_servers": total_servers,
        "active_servers": active_servers,
        "registered_ids": list(_registry.keys()),
    }


@router.delete("/clear")
async def clear_registry() -> Dict[str, Any]:
    """Clear all registrations (for testing)."""
    _registry.clear()
    return {"success": True, "message": "Registry cleared"}
