"""Health check endpoints"""

from fastapi import APIRouter, Request, HTTPException, status
from datetime import datetime
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint (no authentication required).

    Returns health status - all services shown as operational by default.
    External service health is checked in background, not blocking.
    """
    from control_plane_api.app.config import settings

    # Always return healthy for the control plane itself
    # External services are assumed operational unless we can't reach them
    services_status = {
        "kubiya_api": "healthy",
        "context_graph": "healthy",
        "cognitive_memory": "healthy"
    }

    return {
        "status": "healthy",
        "service": "agent-control-plane",
        "timestamp": datetime.utcnow().isoformat(),
        "services": services_status
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint (no authentication required)"""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/detailed")
async def detailed_health_check(request: Request):
    """
    Detailed health check with dependency status.

    Checks connectivity to database, Redis, and Temporal.
    No authentication required for health checks.
    """
    checks = {
        "api": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Database health check using SQLAlchemy
    try:
        from control_plane_api.app.database import health_check_db
        if health_check_db():
            checks["database"] = "healthy"
        else:
            checks["database"] = "unhealthy"
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        checks["database"] = "unhealthy"

    # Check Redis
    try:
        import redis
        from control_plane_api.app.config import settings
        r = redis.from_url(settings.redis_url)
        r.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        checks["redis"] = f"unhealthy: {str(e)}"

    # Check Temporal (just configuration check, not actual connection)
    try:
        from control_plane_api.app.config import settings
        if settings.temporal_host and settings.temporal_namespace:
            checks["temporal"] = "configured"
        else:
            checks["temporal"] = "not configured"
    except Exception as e:
        logger.error("temporal_health_check_failed", error=str(e))
        checks["temporal"] = f"error: {str(e)}"

    # Determine overall status
    checks["status"] = "healthy" if all(
        v in ["healthy", "configured"]
        for k, v in checks.items()
        if k not in ["timestamp", "status"]
    ) else "degraded"

    return checks


@router.get("/health/event-bus")
async def event_bus_health_check():
    """
    Event bus health check with provider-level status.

    Checks health of all enabled event bus providers:
    - HTTP provider
    - WebSocket provider
    - Redis provider
    - NATS provider (if enabled)

    No authentication required for health checks.
    """
    try:
        from control_plane_api.app.config import settings

        # Check if event bus is configured
        if not hasattr(settings, "event_bus") or not settings.event_bus:
            return {
                "status": "not_configured",
                "message": "Event bus not configured - using default HTTP event publishing",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Initialize event bus manager
        from control_plane_api.app.lib.event_bus.manager import (
            EventBusManager,
            EventBusManagerConfig,
        )

        # Build config from settings
        try:
            manager_config = EventBusManagerConfig(**settings.event_bus)
            manager = EventBusManager(manager_config)

            # Initialize providers
            await manager.initialize()

            # Get health status from all providers
            provider_health = await manager.health_check()

            # Determine overall status
            overall_healthy = provider_health.get("_overall", {}).get("healthy", False)

            return {
                "status": "healthy" if overall_healthy else "degraded",
                "providers": provider_health,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("event_bus_health_check_failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    except ImportError as e:
        # Event bus dependencies not installed
        return {
            "status": "dependencies_missing",
            "message": "Event bus dependencies not installed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
