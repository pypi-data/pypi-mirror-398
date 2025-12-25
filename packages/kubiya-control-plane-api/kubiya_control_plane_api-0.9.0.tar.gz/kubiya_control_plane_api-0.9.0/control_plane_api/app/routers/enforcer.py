"""
Enforcer Proxy Router - Proxy to OPA Watchdog Enforcer Service

This router provides a transparent proxy to the OPA Watchdog enforcer service,
allowing workers to call the enforcer through the control plane without knowing
the actual enforcer service URL.

All requests to /api/v1/enforcer/* are forwarded to the enforcer service.
"""

import os
import httpx
from fastapi import APIRouter, Request, Response, status, HTTPException
from fastapi.responses import StreamingResponse
import structlog

from control_plane_api.app.middleware.auth import get_current_organization
from fastapi import Depends

logger = structlog.get_logger()

router = APIRouter(prefix="/enforcer", tags=["enforcer"])

# Get the actual enforcer service URL from environment
# Default to the hosted enforcer service
ENFORCER_SERVICE_URL = os.environ.get("ENFORCER_SERVICE_URL", "https://enforcer-psi.vercel.app")


async def proxy_enforcer_request(
    request: Request,
    path: str = "",
) -> Response:
    """
    Generic proxy function for Enforcer API requests.

    Args:
        request: FastAPI request object
        path: Additional path to append after /enforcer

    Returns:
        Response from the enforcer service
    """
    # Build target URL
    target_url = f"{ENFORCER_SERVICE_URL.rstrip('/')}/{path.lstrip('/')}"

    # Get request body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()

    # Get query parameters
    query_params = dict(request.query_params)

    # Forward headers (including Authorization)
    headers = dict(request.headers)
    # Remove host header to avoid conflicts
    headers.pop("host", None)

    logger.debug(
        "proxy_enforcer_request",
        method=request.method,
        target_url=target_url,
        has_body=body is not None,
        query_params=query_params,
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=query_params,
                content=body,
                headers=headers,
            )

            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
    except httpx.TimeoutException:
        logger.error("enforcer_proxy_timeout", target_url=target_url)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Enforcer service request timed out"
        )
    except httpx.RequestError as e:
        logger.error("enforcer_proxy_error", error=str(e), target_url=target_url)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to enforcer service: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for enforcer proxy"""
    return {
        "status": "healthy",
        "enforcer_url": ENFORCER_SERVICE_URL,
        "proxy": "enabled"
    }


@router.get("/status")
async def status_check(request: Request):
    """Proxy status endpoint to enforcer service"""
    return await proxy_enforcer_request(request, "status")


@router.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_api_v1(
    request: Request,
    path: str,
):
    """Proxy all /api/v1/* requests to enforcer service"""
    return await proxy_enforcer_request(request, f"api/v1/{path}")


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_all(
    request: Request,
    path: str,
):
    """Proxy all other requests to enforcer service"""
    # Skip if already handled by other routes
    if path in ["health", "status"] or path.startswith("api/v1/"):
        return

    return await proxy_enforcer_request(request, path)
