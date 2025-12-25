"""
Task Planning Workflow Factory - Creates and configures planning workflows

This module provides factory functions to create Agno workflows for task planning:
- create_planning_workflow(): Standard 2-step workflow
- create_fast_workflow(): Single-step workflow for --local mode

The workflow orchestrates agents through defined steps with:
- Pre-fetched data caching
- Model configuration (Sonnet for reliability)
- Validation hooks
"""

from typing import Optional, Dict, Any
import os
import structlog

from sqlalchemy.orm import Session
from agno.workflow import Workflow
from agno.models.litellm import LiteLLM

from .cache import get_cached_prefetch, set_cached_prefetch
from .agents import (
    create_analysis_and_selection_agent,
    create_plan_generation_agent,
    create_fast_selection_agent,
)
from .hooks import validate_prefetch_context

logger = structlog.get_logger()


# ============================================================================
# Model Configuration
# ============================================================================

def get_litellm_config() -> tuple[str, str]:
    """
    Get LiteLLM API configuration from environment.

    Returns:
        Tuple of (api_url, api_key)

    Raises:
        ValueError: If LITELLM_API_KEY is not set
    """
    api_url = (
        os.getenv("LITELLM_API_URL") or
        os.getenv("LITELLM_API_BASE") or
        "https://llm-proxy.kubiya.ai"
    ).strip()

    api_key = os.getenv("LITELLM_API_KEY", "").strip()
    if not api_key:
        raise ValueError("LITELLM_API_KEY environment variable not set")

    return api_url, api_key


def create_model(
    model_id: str,
    api_url: str,
    api_key: str,
    timeout: int = 60
) -> LiteLLM:
    """
    Create a LiteLLM model instance.

    Args:
        model_id: Model identifier (e.g., "kubiya/claude-sonnet-4")
        api_url: LiteLLM API base URL
        api_key: LiteLLM API key
        timeout: Request timeout in seconds

    Returns:
        Configured LiteLLM instance
    """
    return LiteLLM(
        id=f"openai/{model_id}",
        api_base=api_url,
        api_key=api_key,
        request_params={"timeout": timeout}
    )


# ============================================================================
# Pre-fetch Resources
# ============================================================================

def prefetch_resources(
    db: Session,
    organization_id: str,
    api_token: str,
    outer_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Pre-fetch organization resources with caching.

    Fetches top 20 of each resource type (agents, teams, environments, queues)
    and caches for 5 minutes to avoid repeated DB calls.

    Args:
        db: Database session
        organization_id: Organization ID
        api_token: API token for authentication
        outer_context: Optional pre-provided context (skips fetch)

    Returns:
        Dict with pre-fetched resources
    """
    # Check cache first
    cached = get_cached_prefetch(organization_id)
    if cached and not outer_context:
        logger.info("using_cached_prefetch", organization_id=organization_id[:8])
        return cached.copy()

    # Validate any provided outer_context
    if outer_context:
        outer_context = validate_prefetch_context(outer_context)
        # If outer_context has data, use it (don't override with DB fetch)
        if outer_context.get("agents") or outer_context.get("teams"):
            logger.info(
                "using_provided_context",
                agents=len(outer_context.get("agents", [])),
                teams=len(outer_context.get("teams", []))
            )
            return outer_context

    # Fetch fresh data from database
    logger.info("pre_fetching_top_resources", organization_id=organization_id[:8])

    from control_plane_api.app.lib.planning_tools.planning_service import PlanningService

    planning_service = PlanningService(db, organization_id, api_token)
    result = {}

    try:
        # Execute fetches SEQUENTIALLY to avoid SQLAlchemy session issues
        agents_data = planning_service.list_agents(limit=20, status=None)
        teams_data = planning_service.list_teams(limit=20, status=None)
        # Don't filter by status - environments may have status="ready" or "active"
        envs_data = planning_service.list_environments(status=None, limit=20)
        queues_data = planning_service.list_worker_queues(limit=20)

        result["agents"] = agents_data[:20]
        result["teams"] = teams_data[:20]
        result["environments"] = envs_data[:20]

        # Sort worker queues by active_workers DESC
        sorted_queues = sorted(
            queues_data[:20],
            key=lambda q: q.get("active_workers", 0),
            reverse=True
        )
        result["worker_queues"] = sorted_queues

        result["pre_fetch_note"] = "Top 20 resources. Use tools for more specific searches."

        logger.info(
            "pre_fetch_completed",
            agents_count=len(result["agents"]),
            teams_count=len(result["teams"]),
            envs_count=len(result["environments"]),
            queues_count=len(result["worker_queues"])
        )

        # Cache for subsequent requests
        set_cached_prefetch(organization_id, result)

    except Exception as e:
        import traceback
        logger.warning(
            "pre_fetch_failed",
            error=str(e),
            traceback=traceback.format_exc()
        )
        # Return empty context - agent will use tools instead
        result = {}

    return result


# ============================================================================
# Main Workflow Factory
# ============================================================================

def create_planning_workflow(
    db: Session,
    organization_id: str,
    api_token: str,
    quick_mode: bool = False,
    outer_context: Optional[Dict[str, Any]] = None
) -> Workflow:
    """
    Create the task planning workflow.

    Creates a 2-step workflow:
    - Step 1: Analysis & Resource Selection (tool calling + structured output)
    - Step 2: Plan Generation (structured output only)

    Args:
        db: Database session
        organization_id: Organization ID (required)
        api_token: API token (required)
        quick_mode: Deprecated, kept for compatibility
        outer_context: Optional pre-fetched context

    Returns:
        Configured Workflow instance

    Raises:
        ValueError: If required parameters are missing
    """
    if not organization_id:
        raise ValueError("organization_id is required")
    if not api_token:
        raise ValueError("api_token is required")

    # Get LiteLLM configuration
    api_url, api_key = get_litellm_config()

    # Get model IDs from environment
    step1_model_id = os.getenv("STEP1_MODEL", "kubiya/claude-sonnet-4").strip()
    step2_model_id = os.getenv("STEP2_MODEL", "kubiya/claude-sonnet-4").strip()

    logger.info(
        "model_configuration",
        step1_model=step1_model_id,
        step2_model=step2_model_id,
        message="Using Sonnet for both steps (reliable structured output)"
    )

    # Create model instances
    step1_model = create_model(step1_model_id, api_url, api_key, timeout=60)
    step2_model = create_model(step2_model_id, api_url, api_key, timeout=60)

    # Pre-fetch resources with caching
    outer_context = prefetch_resources(db, organization_id, api_token, outer_context)

    # Create planning toolkit for Step 1 tools
    from control_plane_api.app.lib.planning_tools.agno_toolkit import PlanningToolkit
    planning_toolkit = PlanningToolkit(db, organization_id, api_token)

    # Create agents
    step1_agent = create_analysis_and_selection_agent(
        model=step1_model,
        planning_toolkit=planning_toolkit,
        outer_context=outer_context
    )

    step2_agent = create_plan_generation_agent(step2_model)

    # Create 2-step workflow
    workflow = Workflow(
        name="Task Planning Workflow",
        steps=[step1_agent, step2_agent],
        description="2-step task planning: (1) Analysis & Selection, (2) Plan Generation"
    )

    # Store references for validation and runtime access
    workflow._planning_toolkit = planning_toolkit
    workflow._outer_context = outer_context
    workflow._organization_id = organization_id

    logger.info(
        "planning_workflow_created",
        steps=2,
        pre_fetched_data=bool(outer_context)
    )

    return workflow


# ============================================================================
# Fast Workflow Factory (--local mode)
# ============================================================================

def create_fast_planning_workflow(
    db: Session,
    organization_id: str,
    api_token: str,
    outer_context: Dict[str, Any]
) -> Workflow:
    """
    Create a fast single-step workflow for --local mode.

    Uses pre-fetched data only (no API calls) for maximum speed.

    Args:
        db: Database session
        organization_id: Organization ID
        api_token: API token
        outer_context: Pre-fetched context (required for fast mode)

    Returns:
        Configured single-step Workflow

    Raises:
        ValueError: If outer_context is empty
    """
    if not outer_context or (not outer_context.get("agents") and not outer_context.get("teams")):
        raise ValueError("outer_context with agents or teams is required for fast mode")

    # Get LiteLLM configuration
    api_url, api_key = get_litellm_config()

    # Use faster model for single-step
    model_id = os.getenv("FAST_MODEL", "kubiya/claude-sonnet-4").strip()
    model = create_model(model_id, api_url, api_key, timeout=30)

    # Validate context
    outer_context = validate_prefetch_context(outer_context)

    # Create fast selection agent
    fast_agent = create_fast_selection_agent(model, outer_context)

    # Create single-step workflow
    workflow = Workflow(
        name="Fast Selection Workflow",
        steps=[fast_agent],
        description="Single-step fast selection for --local mode"
    )

    workflow._outer_context = outer_context
    workflow._organization_id = organization_id

    logger.info(
        "fast_workflow_created",
        agents_count=len(outer_context.get("agents", [])),
        teams_count=len(outer_context.get("teams", []))
    )

    return workflow


# ============================================================================
# Workflow Configuration Helpers
# ============================================================================

class WorkflowConfig:
    """Configuration for task planning workflows."""

    def __init__(
        self,
        step1_model: str = "kubiya/claude-sonnet-4",
        step2_model: str = "kubiya/claude-sonnet-4",
        step1_timeout: int = 60,
        step2_timeout: int = 60,
        cache_ttl: int = 300,
        prefer_runtime: str = "claude_code"
    ):
        self.step1_model = step1_model
        self.step2_model = step2_model
        self.step1_timeout = step1_timeout
        self.step2_timeout = step2_timeout
        self.cache_ttl = cache_ttl
        self.prefer_runtime = prefer_runtime

    @classmethod
    def from_env(cls) -> 'WorkflowConfig':
        """Create config from environment variables."""
        return cls(
            step1_model=os.getenv("STEP1_MODEL", "kubiya/claude-sonnet-4"),
            step2_model=os.getenv("STEP2_MODEL", "kubiya/claude-sonnet-4"),
            step1_timeout=int(os.getenv("STEP1_TIMEOUT", "60")),
            step2_timeout=int(os.getenv("STEP2_TIMEOUT", "60")),
            cache_ttl=int(os.getenv("PREFETCH_CACHE_TTL", "300")),
            prefer_runtime=os.getenv("PREFER_RUNTIME", "claude_code")
        )


def create_workflow_with_config(
    db: Session,
    organization_id: str,
    api_token: str,
    config: WorkflowConfig,
    outer_context: Optional[Dict[str, Any]] = None
) -> Workflow:
    """
    Create workflow with explicit configuration.

    Args:
        db: Database session
        organization_id: Organization ID
        api_token: API token
        config: Workflow configuration
        outer_context: Optional pre-fetched context

    Returns:
        Configured Workflow
    """
    api_url, api_key = get_litellm_config()

    step1_model = create_model(config.step1_model, api_url, api_key, config.step1_timeout)
    step2_model = create_model(config.step2_model, api_url, api_key, config.step2_timeout)

    # Pre-fetch with config
    outer_context = prefetch_resources(db, organization_id, api_token, outer_context)

    # Add preferred runtime to context
    if outer_context and not outer_context.get("preferred_runtime"):
        outer_context["preferred_runtime"] = config.prefer_runtime

    from control_plane_api.app.lib.planning_tools.agno_toolkit import PlanningToolkit
    planning_toolkit = PlanningToolkit(db, organization_id, api_token)

    step1_agent = create_analysis_and_selection_agent(
        model=step1_model,
        planning_toolkit=planning_toolkit,
        outer_context=outer_context
    )
    step2_agent = create_plan_generation_agent(step2_model)

    workflow = Workflow(
        name="Task Planning Workflow",
        steps=[step1_agent, step2_agent],
        description="Configured 2-step task planning workflow"
    )

    workflow._planning_toolkit = planning_toolkit
    workflow._outer_context = outer_context
    workflow._config = config

    return workflow
