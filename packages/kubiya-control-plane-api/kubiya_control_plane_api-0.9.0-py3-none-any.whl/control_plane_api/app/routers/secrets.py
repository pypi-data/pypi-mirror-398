"""
Secrets Router - Proxy to Kubiya Secrets API

This router provides access to organization secrets from Kubiya API.
Secrets are used in the execution environment for agents and teams.
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional, List, Dict, Any
import structlog

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.lib.kubiya_client import get_kubiya_client, KUBIYA_API_BASE

logger = structlog.get_logger()

router = APIRouter(prefix="/secrets", tags=["secrets"])


@router.get("")
async def list_secrets(
    request: Request,
    organization: dict = Depends(get_current_organization),
) -> List[Dict[str, Any]]:
    """
    List all secrets available in the organization.

    This endpoint proxies to Kubiya Secrets API and returns a list of secret metadata
    (names, IDs, descriptions) without exposing actual secret values.

    Returns:
        List of secrets with metadata (no values)
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

        # Call Kubiya Secrets API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{KUBIYA_API_BASE}/api/v2/secrets",
                headers=headers,
            )

            if response.status_code == 200:
                secrets = response.json()
                logger.info(
                    "secrets_fetched",
                    org_id=org_id,
                    count=len(secrets),
                )
                return secrets
            else:
                logger.error(
                    "kubiya_api_error",
                    status=response.status_code,
                    response=response.text[:500],
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch secrets from Kubiya API: {response.text[:200]}",
                )

    except httpx.TimeoutException:
        logger.error("kubiya_api_timeout", endpoint="secrets")
        raise HTTPException(status_code=504, detail="Kubiya API request timed out")
    except httpx.RequestError as e:
        logger.error("kubiya_api_request_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to connect to Kubiya API: {str(e)}")
    except Exception as e:
        logger.error("unexpected_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/value/{name}")
async def get_secret_value(
    name: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
) -> Dict[str, Any]:
    """
    Get the value of a specific secret.

    This endpoint is used by workers at runtime to resolve secret values.
    Should be called securely from backend only, not exposed to frontend.

    Args:
        name: Secret name to retrieve

    Returns:
        {"value": "secret_value"}
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

        # Call Kubiya Secrets API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{KUBIYA_API_BASE}/api/v2/secrets/get_value/{name}",
                headers=headers,
            )

            if response.status_code == 200:
                # Kubiya API returns plain text (the secret value), not JSON
                secret_value = response.text
                logger.info(
                    "secret_value_fetched",
                    org_id=org_id,
                    secret_name=name[:20],
                )
                # Return in a structured format for consistency
                return {"value": secret_value}
            else:
                logger.error(
                    "kubiya_api_error",
                    status=response.status_code,
                    secret_name=name[:20],
                    response=response.text[:500],
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch secret value from Kubiya API: {response.text[:200]}",
                )

    except httpx.TimeoutException:
        logger.error("kubiya_api_timeout", endpoint=f"secrets/value/{name[:20]}")
        raise HTTPException(status_code=504, detail="Kubiya API request timed out")
    except httpx.RequestError as e:
        logger.error("kubiya_api_request_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to connect to Kubiya API: {str(e)}")
    except Exception as e:
        logger.error("unexpected_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
