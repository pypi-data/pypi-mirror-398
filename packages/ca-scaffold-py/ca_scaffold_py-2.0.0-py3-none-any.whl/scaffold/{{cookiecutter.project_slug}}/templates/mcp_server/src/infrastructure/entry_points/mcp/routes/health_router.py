import logging
from typing import Annotated
from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, HTTPException, Depends
from src.applications.settings.container import Container
from src.infrastructure.driven_adapters import ApiConnectAdapter


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", tags=["health"])
@inject
async def health(
    api_connect_adapter: Annotated[
        ApiConnectAdapter,
        Depends(Provide[Container.api_connect_adapter])
    ]
):
    """Route to check the health of the application."""
    try:
        credentials_valid = await api_connect_adapter.validate_credentials()
        if credentials_valid:
            return {"status": "ok", "credentials": "valid"}
        logger.error("Health check failed: invalid credentials")
        raise HTTPException(
            status_code=503,
            detail="Service Unavailable: Invalid credentials"
        )
    except AttributeError as e:
        logger.error("Health check failed: error: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Service Unavailable"
        ) from e
