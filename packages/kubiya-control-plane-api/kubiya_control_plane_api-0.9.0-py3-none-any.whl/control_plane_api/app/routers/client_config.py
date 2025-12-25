"""
Client Configuration Router

Provides configuration endpoints for CLI and other clients to discover
backend service URLs and credentials.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.config import get_api_config

settings = get_api_config()

router = APIRouter(prefix="/client", tags=["client-config"])


class ClientConfig(BaseModel):
    """Configuration for CLI clients."""

    # Backend service URLs
    context_graph_api_base: str

    # Future: LLM credentials (for direct client-side agent execution)
    # litellm_api_base: Optional[str] = None
    # litellm_api_key: Optional[str] = None

    # Future: Temporal configuration
    # temporal_address: Optional[str] = None
    # temporal_namespace: Optional[str] = None

    # Organization context
    organization_id: str
    organization_name: str


@router.get("/config", response_model=ClientConfig)
async def get_client_config(
    organization: dict = Depends(get_current_organization),
):
    """
    Get client configuration including backend service URLs.

    This endpoint allows CLI clients to discover the context graph API URL
    and other service endpoints, enabling direct connections without proxying
    through the control plane.

    Returns:
        ClientConfig with service URLs and credentials
    """
    return ClientConfig(
        context_graph_api_base=settings.context_graph_api_base,
        organization_id=organization["id"],
        organization_name=organization.get("name", organization["id"]),
    )
