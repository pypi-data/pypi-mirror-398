"""
Integrations Router - Proxy to Kubiya Integrations API

This router provides access to organization integrations from Kubiya API.
Integrations provide delegated credentials to third-party services (GitHub, Jira, AWS, etc.)
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional, List, Dict, Any
import structlog

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.lib.kubiya_client import get_kubiya_client, KUBIYA_API_BASE

logger = structlog.get_logger()

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("")
async def list_integrations(
    request: Request,
    organization: dict = Depends(get_current_organization),
    connected_only: bool = False,
) -> List[Dict[str, Any]]:
    """
    List all integrations available in the organization.

    This endpoint proxies to Kubiya Integrations API and returns a list of
    integrations with their metadata and connection status.

    Args:
        connected_only: If True, only return connected/active integrations (default: False)

    Returns:
        List of integrations with metadata
    """
    try:
        token = request.state.kubiya_token
        auth_type = getattr(request.state, "kubiya_auth_type", "Bearer")
        org_id = organization["id"]

        logger.debug(
            "integrations_list_auth",
            auth_type=auth_type,
            token_prefix=token[:20] if token else None,
            org_id=org_id
        )

        # Prepare headers for Kubiya API
        headers = {
            "Authorization": f"{auth_type} {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Kubiya-Client": "agent-control-plane",
            "X-Organization-ID": org_id,
        }

        # Call Kubiya Integrations API with full details
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{KUBIYA_API_BASE}/api/v2/integrations?full=true",
                headers=headers,
            )

            if response.status_code == 200:
                integrations = response.json()

                # Filter to only connected integrations if requested
                if connected_only:
                    integrations = [
                        i for i in integrations
                        if i.get("connected") or i.get("status") == "active"
                    ]

                logger.info(
                    "integrations_fetched",
                    org_id=org_id,
                    total_count=len(response.json()),
                    connected_count=len(integrations),
                )
                return integrations
            else:
                logger.error(
                    "kubiya_api_error",
                    status=response.status_code,
                    response=response.text[:500],
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch integrations from Kubiya API: {response.text[:200]}",
                )

    except httpx.TimeoutException:
        logger.error("kubiya_api_timeout", endpoint="integrations")
        raise HTTPException(status_code=504, detail="Kubiya API request timed out")
    except httpx.RequestError as e:
        logger.error("kubiya_api_request_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to connect to Kubiya API: {str(e)}")
    except Exception as e:
        logger.error("unexpected_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{integration_id}")
async def get_integration(
    integration_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
) -> Dict[str, Any]:
    """
    Get details of a specific integration.

    Args:
        integration_id: Integration UUID

    Returns:
        Integration details
    """
    try:
        token = request.state.kubiya_token
        auth_type = getattr(request.state, "kubiya_auth_type", "Bearer")
        org_id = organization["id"]

        # Prepare headers for Kubiya API
        headers = {
            "Authorization": f"{auth_type} {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Kubiya-Client": "agent-control-plane",
            "X-Organization-ID": org_id,
        }

        # Call Kubiya Integrations API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{KUBIYA_API_BASE}/api/v2/integrations/{integration_id}",
                headers=headers,
            )

            if response.status_code == 200:
                integration = response.json()
                logger.info(
                    "integration_fetched",
                    org_id=org_id,
                    integration_id=integration_id[:8],
                )
                return integration
            else:
                logger.error(
                    "kubiya_api_error",
                    status=response.status_code,
                    integration_id=integration_id[:8],
                    response=response.text[:500],
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch integration from Kubiya API: {response.text[:200]}",
                )

    except httpx.TimeoutException:
        logger.error("kubiya_api_timeout", endpoint=f"integrations/{integration_id[:8]}")
        raise HTTPException(status_code=504, detail="Kubiya API request timed out")
    except httpx.RequestError as e:
        logger.error("kubiya_api_request_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to connect to Kubiya API: {str(e)}")
    except Exception as e:
        logger.error("unexpected_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{integration_type}/{integration_id}/token")
async def get_integration_token(
    integration_type: str,
    integration_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
) -> Dict[str, Any]:
    """
    Get delegated credentials/token for a specific integration.

    This endpoint is used by workers at runtime to get integration credentials.
    Should be called securely from backend only, not exposed to frontend.

    Args:
        integration_type: Type of integration (github, github_app, jira, etc.)
        integration_id: Integration UUID or installation ID

    Returns:
        Integration credentials/token

    Examples:
        - /api/v1/integrations/github/uuid-here/token
        - /api/v1/integrations/github_app/installation-id/token
        - /api/v1/integrations/jira/uuid-here/token
    """
    try:
        token = request.state.kubiya_token
        auth_type = getattr(request.state, "kubiya_auth_type", "Bearer")
        org_id = organization["id"]

        # Prepare headers for Kubiya API
        headers = {
            "Authorization": f"{auth_type} {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Kubiya-Client": "agent-control-plane",
            "X-Organization-ID": org_id,
        }

        # Build token URL based on integration type
        integration_type_lower = integration_type.lower()

        if integration_type_lower == "github":
            token_url = f"{KUBIYA_API_BASE}/api/v1/integration/github/token/{integration_id}"
        elif integration_type_lower == "github_app":
            token_url = f"{KUBIYA_API_BASE}/api/v1/integration/github_app/token/{integration_id}"
        elif integration_type_lower == "jira":
            token_url = f"{KUBIYA_API_BASE}/api/v1/integration/jira/token/{integration_id}"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported integration type: {integration_type}. Supported types: github, github_app, jira",
            )

        # Get token
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.get(token_url, headers=headers)

            if token_response.status_code == 200:
                # Try to parse as JSON first
                try:
                    token_data = token_response.json()
                    logger.info(
                        "integration_token_fetched",
                        org_id=org_id,
                        integration_id=integration_id[:8] if len(integration_id) > 8 else integration_id,
                        integration_type=integration_type,
                    )
                    return token_data
                except:
                    # If not JSON, return as plain text value
                    token_value = token_response.text
                    logger.info(
                        "integration_token_fetched",
                        org_id=org_id,
                        integration_id=integration_id[:8] if len(integration_id) > 8 else integration_id,
                        integration_type=integration_type,
                    )
                    return {"token": token_value}
            else:
                logger.error(
                    "kubiya_api_error",
                    status=token_response.status_code,
                    integration_id=integration_id[:8] if len(integration_id) > 8 else integration_id,
                    response=token_response.text[:500],
                )
                raise HTTPException(
                    status_code=token_response.status_code,
                    detail=f"Failed to fetch integration token: {token_response.text[:200]}",
                )

    except httpx.TimeoutException:
        logger.error("kubiya_api_timeout", endpoint=f"integrations/{integration_id[:8]}/token")
        raise HTTPException(status_code=504, detail="Kubiya API request timed out")
    except httpx.RequestError as e:
        logger.error("kubiya_api_request_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to connect to Kubiya API: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("unexpected_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
