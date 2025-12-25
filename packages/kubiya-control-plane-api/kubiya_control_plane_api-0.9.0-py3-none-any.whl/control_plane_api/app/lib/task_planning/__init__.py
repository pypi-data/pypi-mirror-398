"""
Task Planning Library

This package provides utilities for AI-powered task planning including:
- Modular workflow components (agents, hooks, cache, runner)
- Helper functions for resource discovery and preparation
- Agent factory for creating planning agents
- SSE message formatting for streaming responses

Architecture:
- models.py: Pydantic schemas for step outputs
- cache.py: Pre-fetch caching with TTL
- agents.py: Agent factory functions
- hooks.py: Pre/post validation hooks
- workflow.py: Workflow factory
- runner.py: Workflow execution with streaming
"""

from .helpers import (
    make_json_serializable,
    save_planning_prompt_debug,
    format_sse_message,
)
from .agent_factory import create_planning_agent

# New modular API
from .cache import (
    get_cached_prefetch,
    set_cached_prefetch,
    invalidate_prefetch_cache,
    clear_prefetch_cache,
    get_prefetch_cache,
    PrefetchCache,
)
from .models import (
    TaskAnalysisOutput,
    ResourceDiscoveryOutput,
    FastSelectionOutput,
    CostEstimationOutput,
    validate_resource_discovery,
)
from .agents import (
    create_analysis_and_selection_agent,
    create_plan_generation_agent,
    create_fast_selection_agent,
    create_task_analysis_agent,
    create_cost_estimation_agent,
    build_prefetch_tools,
    build_search_tools,
)
from .hooks import (
    validate_task_input,
    validate_prefetch_context,
    validate_step1_output,
    validate_step2_output,
    InputValidationError,
    OutputValidationError,
    EntityNotFoundError,
    HallucinatedIdError,
)
from .workflow import (
    create_planning_workflow,
    create_fast_planning_workflow,
    create_workflow_with_config,
    WorkflowConfig,
    get_litellm_config,
    create_model,
    prefetch_resources,
)
from .runner import (
    run_workflow_stream,
    run_fast_workflow_stream,
    execute_step,
    extract_json_from_content,
    STEP_DESCRIPTIONS,
    STEP_STAGE_NAMES,
    STEP_PROGRESS_MAP,
)

__all__ = [
    # Legacy helpers
    "make_json_serializable",
    "save_planning_prompt_debug",
    "format_sse_message",
    "create_planning_agent",

    # Cache
    "get_cached_prefetch",
    "set_cached_prefetch",
    "invalidate_prefetch_cache",
    "clear_prefetch_cache",
    "get_prefetch_cache",
    "PrefetchCache",

    # Models
    "TaskAnalysisOutput",
    "ResourceDiscoveryOutput",
    "FastSelectionOutput",
    "CostEstimationOutput",
    "validate_resource_discovery",

    # Agents
    "create_analysis_and_selection_agent",
    "create_plan_generation_agent",
    "create_fast_selection_agent",
    "create_task_analysis_agent",
    "create_cost_estimation_agent",
    "build_prefetch_tools",
    "build_search_tools",

    # Hooks
    "validate_task_input",
    "validate_prefetch_context",
    "validate_step1_output",
    "validate_step2_output",
    "InputValidationError",
    "OutputValidationError",
    "EntityNotFoundError",
    "HallucinatedIdError",

    # Workflow
    "create_planning_workflow",
    "create_fast_planning_workflow",
    "create_workflow_with_config",
    "WorkflowConfig",
    "get_litellm_config",
    "create_model",
    "prefetch_resources",

    # Runner
    "run_workflow_stream",
    "run_fast_workflow_stream",
    "execute_step",
    "extract_json_from_content",
    "STEP_DESCRIPTIONS",
    "STEP_STAGE_NAMES",
    "STEP_PROGRESS_MAP",
]
