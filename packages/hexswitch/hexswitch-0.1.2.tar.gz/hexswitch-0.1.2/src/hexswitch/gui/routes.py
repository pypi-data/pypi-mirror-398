"""API routes for HexSwitch GUI."""

from typing import TYPE_CHECKING

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from hexswitch.ports.registry import get_port_registry
from hexswitch.shared.observability import get_global_metrics_collector

if TYPE_CHECKING:
    pass

router = APIRouter()


@router.get("/api/ports")
async def get_ports() -> JSONResponse:
    """Get list of all registered ports.

    Returns:
        JSON response with port information.
    """
    get_port_registry()
    ports = []

    # Get all registered ports
    # Note: Port registry doesn't expose a list method, so we'll need to
    # track this differently or add a method to the registry
    # For now, return empty list
    return JSONResponse(content={"ports": ports})


@router.get("/api/handlers")
async def get_handlers() -> JSONResponse:
    """Get list of all registered handlers.

    Returns:
        JSON response with handler information.
    """
    get_port_registry()
    handlers = []

    # Similar to ports, we need a way to list all handlers
    # For now, return empty list
    return JSONResponse(content={"handlers": handlers})


@router.get("/api/adapters")
async def get_adapters(request: Request) -> JSONResponse:
    """Get status of all adapters.

    Args:
        request: FastAPI request object (contains app.state.runtime).

    Returns:
        JSON response with adapter status.
    """
    adapters = []

    # Get runtime from app state
    runtime = getattr(request.app.state, "runtime", None)
    if runtime:
        # Get inbound adapters
        for adapter in runtime.inbound_adapters:
            adapters.append({
                "name": adapter.name,
                "type": "inbound",
                "running": getattr(adapter, "_running", False),
            })

        # Get outbound adapters
        for adapter in runtime.outbound_adapters:
            adapters.append({
                "name": adapter.name,
                "type": "outbound",
                "connected": getattr(adapter, "_connected", False),
            })

    return JSONResponse(content={"adapters": adapters})


@router.get("/api/metrics")
async def get_metrics() -> JSONResponse:
    """Get current metrics.

    Returns:
        JSON response with metrics data.
    """
    metrics_collector = get_global_metrics_collector()
    all_metrics = metrics_collector.get_all_metrics()

    return JSONResponse(content=all_metrics)


@router.get("/api/health")
async def get_health() -> JSONResponse:
    """Get system health status.

    Returns:
        JSON response with health information.
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "hexswitch",
    })
