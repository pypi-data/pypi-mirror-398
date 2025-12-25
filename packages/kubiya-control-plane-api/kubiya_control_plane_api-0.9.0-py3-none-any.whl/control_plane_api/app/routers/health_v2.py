"""
Enhanced health check endpoints for production monitoring.

Provides:
- Basic health check (/health)
- Readiness check with dependency validation (/health/ready)
- Liveness check (/health/live)
- Detailed health status (/health/detailed)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog
import httpx
import asyncio
import time
import os
import psutil

from control_plane_api.app.database import get_session
from control_plane_api.app.lib.redis_client import get_redis_client
from control_plane_api.app.lib.temporal_client import get_temporal_client
from control_plane_api.app.config import settings

logger = structlog.get_logger()

router = APIRouter()

# Track application start time
APP_START_TIME = time.time()


@router.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns 200 if the service is running.
    Used by load balancers for basic availability checks.
    """
    return {
        "status": "healthy",
        "service": "agent-control-plane",
        "version": settings.api_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/live", tags=["Health"])
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness probe for Kubernetes.
    
    Checks if the application is running and not deadlocked.
    Returns 200 if alive, 503 if the application needs to be restarted.
    """
    try:
        # Simple check - can we allocate memory and respond?
        test_data = list(range(1000))
        
        uptime = time.time() - APP_START_TIME
        
        return {
            "status": "alive",
            "uptime_seconds": round(uptime, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error("liveness_check_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Liveness check failed",
        )


@router.get("/health/ready", tags=["Health"])
async def readiness_check(
    db_session: Optional[AsyncSession] = Depends(get_session),
) -> Dict[str, Any]:
    """
    Readiness probe for Kubernetes and monitoring.
    
    Checks if the application is ready to serve traffic by validating:
    - Database connectivity
    - Redis connectivity (if configured)
    - Temporal connectivity (if configured)
    
    Returns 200 if ready, 503 if not ready to serve traffic.
    """
    checks = {
        "database": False,
        "redis": False,
        "temporal": False,
    }
    
    errors = []
    
    # Check database
    if db_session:
        try:
            result = await db_session.execute(text("SELECT 1"))
            checks["database"] = result.scalar() == 1
        except Exception as e:
            logger.warning("database_health_check_failed", error=str(e))
            errors.append(f"Database: {str(e)}")
    else:
        errors.append("Database: No session available")
    
    # Check Redis (if configured)
    try:
        redis_client = get_redis_client()
        if redis_client:
            await redis_client.ping()
            checks["redis"] = True
    except Exception as e:
        logger.warning("redis_health_check_failed", error=str(e))
        errors.append(f"Redis: {str(e)}")
    
    # Check Temporal (if configured)
    try:
        temporal_client = await get_temporal_client()
        if temporal_client:
            # Try to describe the namespace
            await temporal_client.service_client.describe_namespace(
                settings.temporal_namespace
            )
            checks["temporal"] = True
    except Exception as e:
        logger.warning("temporal_health_check_failed", error=str(e))
        errors.append(f"Temporal: {str(e)}")
    
    # Determine overall readiness
    # Database is required, Redis and Temporal are optional
    is_ready = checks["database"]
    
    response = {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
    
    if errors:
        response["errors"] = errors
    
    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response,
        )
    
    return response


@router.get("/health/detailed", tags=["Health"])
async def detailed_health_check(
    db_session: Optional[AsyncSession] = Depends(get_session),
) -> Dict[str, Any]:
    """
    Detailed health check with comprehensive system information.
    
    Provides:
    - Service health status
    - Dependency health checks
    - System metrics (CPU, memory, disk)
    - Configuration information
    
    Used for debugging and monitoring dashboards.
    """
    uptime = time.time() - APP_START_TIME
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Dependency checks
    dependencies = {}
    
    # Database check with latency
    db_latency = None
    if db_session:
        try:
            start = time.time()
            result = await db_session.execute(text("SELECT 1"))
            db_latency = (time.time() - start) * 1000  # Convert to ms
            dependencies["database"] = {
                "healthy": result.scalar() == 1,
                "latency_ms": round(db_latency, 2),
            }
        except Exception as e:
            dependencies["database"] = {
                "healthy": False,
                "error": str(e),
            }
    
    # Redis check with latency
    try:
        redis_client = get_redis_client()
        if redis_client:
            start = time.time()
            await redis_client.ping()
            redis_latency = (time.time() - start) * 1000
            dependencies["redis"] = {
                "healthy": True,
                "latency_ms": round(redis_latency, 2),
            }
    except Exception as e:
        dependencies["redis"] = {
            "healthy": False,
            "error": str(e),
        }
    
    # Temporal check
    try:
        temporal_client = await get_temporal_client()
        if temporal_client:
            start = time.time()
            await temporal_client.service_client.describe_namespace(
                settings.temporal_namespace
            )
            temporal_latency = (time.time() - start) * 1000
            dependencies["temporal"] = {
                "healthy": True,
                "latency_ms": round(temporal_latency, 2),
                "namespace": settings.temporal_namespace,
            }
    except Exception as e:
        dependencies["temporal"] = {
            "healthy": False,
            "error": str(e),
        }
    
    # External services check (if configured)
    external_services = {}
    
    # Check Kubiya API
    if settings.kubiya_api_base:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                start = time.time()
                response = await client.get(f"{settings.kubiya_api_base}/health")
                kubiya_latency = (time.time() - start) * 1000
                external_services["kubiya_api"] = {
                    "healthy": response.status_code == 200,
                    "latency_ms": round(kubiya_latency, 2),
                    "status_code": response.status_code,
                }
        except Exception as e:
            external_services["kubiya_api"] = {
                "healthy": False,
                "error": str(e),
            }
    
    # Check LiteLLM Proxy
    if settings.litellm_api_base:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                start = time.time()
                response = await client.get(f"{settings.litellm_api_base}/health")
                litellm_latency = (time.time() - start) * 1000
                external_services["litellm_proxy"] = {
                    "healthy": response.status_code == 200,
                    "latency_ms": round(litellm_latency, 2),
                    "status_code": response.status_code,
                }
        except Exception as e:
            external_services["litellm_proxy"] = {
                "healthy": False,
                "error": str(e),
            }
    
    # Determine overall health
    all_healthy = all(
        dep.get("healthy", False) for dep in dependencies.values()
    )
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.api_version,
        "environment": settings.environment,
        "uptime": {
            "seconds": round(uptime, 2),
            "human_readable": _format_uptime(uptime),
        },
        "system": {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count(),
            },
            "memory": {
                "percent": memory.percent,
                "used_gb": round(memory.used / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
            },
            "disk": {
                "percent": disk.percent,
                "used_gb": round(disk.used / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
            },
        },
        "dependencies": dependencies,
        "external_services": external_services if external_services else None,
    }


@router.get("/health/temporal-credentials", tags=["Health"])
async def check_temporal_credentials(
    request: Any = Depends(lambda: None),
    organization: dict = Depends(lambda: {"id": "test-org"}),
) -> Dict[str, Any]:
    """
    Check if organization has valid Temporal credentials.

    This endpoint helps diagnose credential issues by attempting to
    fetch Temporal credentials for the organization.

    Returns credential status including namespace, org, TTL, and API key presence.
    """
    from fastapi import Request
    from control_plane_api.app.middleware.auth import get_current_organization
    from control_plane_api.app.lib.temporal_credentials_service import get_temporal_credentials_for_org

    # This is a diagnostic endpoint, so we'll make the auth optional for testing
    # In production, you may want to require authentication
    try:
        # Try to get request and token if available
        from starlette.requests import Request as StarletteRequest

        # For authenticated requests
        if hasattr(request, 'state') and hasattr(request.state, 'kubiya_token'):
            token = request.state.kubiya_token
            org_id = organization.get("id", "unknown")
        else:
            # For unauthenticated health checks, return local status
            from control_plane_api.app.lib.temporal_credentials_service import is_local_temporal
            if is_local_temporal():
                return {
                    "status": "ok",
                    "mode": "local",
                    "message": "Using local Temporal server",
                    "namespace": os.getenv("TEMPORAL_NAMESPACE", "default"),
                    "host": os.getenv("TEMPORAL_HOST", "localhost:7233"),
                }
            else:
                return {
                    "status": "info",
                    "message": "Authentication required to check cloud Temporal credentials",
                    "mode": "cloud",
                }

        credentials = await get_temporal_credentials_for_org(
            org_id=org_id,
            token=token,
            use_fallback=False  # Don't fallback for health check
        )

        return {
            "status": "ok",
            "namespace": credentials.get("namespace"),
            "org": credentials.get("org"),
            "ttl": credentials.get("ttl"),
            "has_api_key": bool(credentials.get("api_key")),
            "host": credentials.get("host"),
        }
    except Exception as e:
        logger.error("temporal_credentials_health_check_failed", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to fetch Temporal credentials",
        }


def _format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format."""
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")

    return " ".join(parts)
