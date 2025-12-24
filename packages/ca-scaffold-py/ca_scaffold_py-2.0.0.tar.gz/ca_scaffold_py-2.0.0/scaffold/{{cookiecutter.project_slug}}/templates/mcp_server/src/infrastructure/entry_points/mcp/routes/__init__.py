from fastapi import APIRouter
from src.infrastructure.entry_points.mcp.routes import (
    health_router
)


def set_routes(prefix_url: str = "") -> APIRouter:
    """Set all routes for the FastAPI application."""
    api_router = APIRouter(prefix=prefix_url)
    api_router.include_router(
        health_router.router, prefix="/health", tags=["health"]
    )
    return api_router
