"""Runners endpoint - proxies to Kubiya API"""

from fastapi import APIRouter, Depends, Request, HTTPException, Query
from typing import List, Dict, Any, Optional
import structlog
import httpx
import asyncio

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.lib.kubiya_client import get_kubiya_client
from control_plane_api.app.config import settings

logger = structlog.get_logger()

router = APIRouter()

# Valid component names for filtering
VALID_COMPONENTS = [
    "workflow_engine",
    "workflow-engine",
    "workflowEngine",
    "tool-manager",
    "tool_manager",
    "toolManager",
    "agent-manager",
    "agent_manager",
    "agentManager",
]


@router.get("")
async def list_runners(
    request: Request,
    organization: dict = Depends(get_current_organization),
    component: Optional[str] = Query(
        None,
        description="Filter runners by healthy component (e.g., 'workflow_engine', 'tool-manager'). If not specified, returns all runners with health data.",
    ),
):
    """
    List available runners for the organization.
    Fetches health data for each runner and optionally filters by component health.

    Query Parameters:
    - component: Optional component name to filter by (workflow_engine, tool-manager, etc.)

    Returns only runners with the specified healthy component, or all runners if no filter specified.
    """
    # Validate component parameter if provided
    if component and component not in VALID_COMPONENTS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid component '{component}'",
                "valid_components": VALID_COMPONENTS,
                "message": f"Valid choices are: {', '.join(VALID_COMPONENTS)}",
            },
        )

    try:
        kubiya_client = get_kubiya_client()
        token = request.state.kubiya_token

        runners = await kubiya_client.get_runners(token, organization["id"])

        # Fetch health for each runner in parallel
        kubiya_api_base = settings.kubiya_api_base

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create health check tasks for all runners
            health_tasks = []
            for runner in runners:
                runner_name = runner.get("name")
                if runner_name:
                    health_tasks.append(_fetch_runner_health(client, kubiya_api_base, token, runner_name))
                else:
                    health_tasks.append(None)

            # Execute all health checks in parallel
            health_results = await asyncio.gather(*health_tasks, return_exceptions=True)

        # Combine runners with their health data and optionally filter by component
        filtered_runners = []
        for runner, health_data in zip(runners, health_results):
            runner_name = runner.get("name")

            # Determine if we should include this runner
            should_include = False
            status = "unknown"

            # If no component filter specified, include all runners
            if not component:
                should_include = True
                # Determine status from health data if available
                if health_data and not isinstance(health_data, Exception):
                    runner["health_data"] = health_data
                    status = _determine_runner_status_from_health(runner, health_data)
                else:
                    # No health data or error - mark as unknown or active
                    status = "unknown" if isinstance(health_data, Exception) else "active"
            else:
                # Component filter specified - only include if component is healthy
                if health_data and not isinstance(health_data, Exception):
                    runner["health_data"] = health_data
                    should_include = _has_healthy_component(health_data, component)
                    if should_include:
                        status = _determine_runner_status_from_health(runner, health_data)
                else:
                    should_include = False
                    logger.debug(
                        "runner_health_check_failed",
                        runner_name=runner_name,
                        component=component,
                        error=str(health_data) if isinstance(health_data, Exception) else "No health data",
                    )

            # Add runner to filtered list if it should be included
            if should_include:
                normalized_runner = {
                    **runner,  # Keep all original fields
                    "id": runner.get("name") or runner.get("id"),
                    "status": status,
                }
                filtered_runners.append(normalized_runner)

                logger.debug(
                    "runner_included",
                    runner_name=runner_name,
                    status=status,
                    component_filter=component,
                )
            elif component:
                logger.debug(
                    "runner_filtered_out",
                    runner_name=runner_name,
                    component=component,
                    reason="component_not_healthy",
                )

        logger.info(
            "runners_listed",
            org_id=organization["id"],
            total_runners=len(runners),
            filtered_runners=len(filtered_runners),
            component_filter=component,
        )

        return {
            "runners": filtered_runners,
            "count": len(filtered_runners),
        }

    except Exception as e:
        logger.error("runners_list_failed", error=str(e), org_id=organization["id"])
        # Return empty list if Kubiya API fails
        return {
            "runners": [],
            "count": 0,
            "error": "Failed to fetch runners from Kubiya API"
        }


@router.get("/{runner_name}/health")
async def get_runner_health(
    runner_name: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
):
    """
    Get health status for a specific runner.

    Proxies to Kubiya API /api/v3/runners/{runner_name}/health
    Checks workflow_engine component health specifically.
    """
    try:
        token = request.state.kubiya_token
        kubiya_api_base = settings.kubiya_api_base

        # Determine auth method from request state
        auth_type = getattr(request.state, "kubiya_auth_type", "Bearer")
        auth_header = f"{auth_type} {token}"

        # Call Kubiya API health endpoint
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try Bearer first, fallback to UserKey
            response = await client.get(
                f"{kubiya_api_base}/api/v3/runners/{runner_name}/health",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code == 401:
                # Try UserKey if Bearer fails
                response = await client.get(
                    f"{kubiya_api_base}/api/v3/runners/{runner_name}/health",
                    headers={"Authorization": f"UserKey {token}"},
                )

            if response.status_code == 200:
                health_data = response.json()

                logger.info(
                    "runner_health_fetched",
                    runner_name=runner_name,
                    status=health_data.get("status"),
                    org_id=organization["id"],
                )

                return health_data
            else:
                logger.warning(
                    "runner_health_failed",
                    runner_name=runner_name,
                    status_code=response.status_code,
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch runner health: {response.status_code}"
                )

    except httpx.TimeoutException:
        logger.error("runner_health_timeout", runner_name=runner_name)
        raise HTTPException(status_code=504, detail="Health check timeout")
    except Exception as e:
        logger.error("runner_health_error", runner_name=runner_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def _fetch_runner_health(
    client: httpx.AsyncClient,
    kubiya_api_base: str,
    token: str,
    runner_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Fetch health data for a specific runner from Kubiya API.
    Tries Bearer auth first, then UserKey.
    """
    try:
        # Try Bearer first
        response = await client.get(
            f"{kubiya_api_base}/api/v3/runners/{runner_name}/health",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Fallback to UserKey if Bearer fails
        if response.status_code == 401:
            response = await client.get(
                f"{kubiya_api_base}/api/v3/runners/{runner_name}/health",
                headers={"Authorization": f"UserKey {token}"},
            )

        if response.status_code == 200:
            return response.json()

        return None

    except Exception as e:
        logger.debug(
            "runner_health_fetch_error",
            runner_name=runner_name,
            error=str(e),
        )
        return None


def _has_healthy_component(health_data: Dict[str, Any], component_name: str) -> bool:
    """
    Check if the runner has a healthy component with the specified name.

    Health data structure:
    {
      "checks": [
        {"name": "workflow-engine", "status": "ok", ...},
        {"name": "tool-manager", "status": "ok", ...},
        ...
      ]
    }

    Args:
        health_data: Health data from Kubiya API
        component_name: Component name to check (supports multiple naming conventions)

    Returns:
        True if component is found and healthy, False otherwise
    """
    checks = health_data.get("checks", [])

    # Normalize component name to check against multiple naming conventions
    component_variants = _get_component_name_variants(component_name)

    for check in checks:
        check_name = check.get("name", "")
        if check_name in component_variants:
            status = check.get("status", "")
            # Consider "ok" or "healthy" as valid
            if status in ["ok", "healthy"]:
                return True

    return False


def _get_component_name_variants(component_name: str) -> List[str]:
    """
    Get all possible naming variants for a component name.

    Examples:
    - "workflow_engine" → ["workflow_engine", "workflow-engine", "workflowEngine"]
    - "tool-manager" → ["tool-manager", "tool_manager", "toolManager"]
    - "workflowEngine" → ["workflow_engine", "workflow-engine", "workflowEngine"]

    Args:
        component_name: Component name in any format

    Returns:
        List of possible naming variants
    """
    import re

    # Detect if input is camelCase and split it
    # Insert underscore before uppercase letters (except first char)
    snake_from_camel = re.sub(r"(?<!^)(?=[A-Z])", "_", component_name)

    # Convert to lowercase base
    base = snake_from_camel.lower().replace("-", "_").replace(" ", "_")

    # Generate camelCase: first word lowercase, rest capitalized
    words = base.split("_")
    if len(words) > 1:
        camel_case = words[0] + "".join(word.capitalize() for word in words[1:])
    else:
        camel_case = words[0]

    # Generate variants
    variants = [
        base,  # workflow_engine
        base.replace("_", "-"),  # workflow-engine
        camel_case,  # workflowEngine
    ]

    # Also include the original input
    variants.append(component_name)

    return list(set(variants))


def _determine_runner_status_from_health(runner: Dict[str, Any], health_data: Dict[str, Any]) -> str:
    """
    Determine runner status based on health check data.

    Returns: "active", "degraded", "unhealthy"
    """
    # Check if managed cloud (always active)
    if runner.get("runner_type") == "managed_cloud" or runner.get("isManagedCloud"):
        return "active"

    # Check overall health status
    overall_status = health_data.get("status", "")
    if overall_status == "ok":
        return "active"

    # Check individual component health
    checks = health_data.get("checks", [])
    healthy_count = 0
    total_count = len(checks)

    for check in checks:
        if check.get("status") == "ok":
            healthy_count += 1

    # All components healthy
    if total_count > 0 and healthy_count == total_count:
        return "active"

    # Some components healthy
    if healthy_count > 0:
        return "degraded"

    # No healthy components
    return "unhealthy"
