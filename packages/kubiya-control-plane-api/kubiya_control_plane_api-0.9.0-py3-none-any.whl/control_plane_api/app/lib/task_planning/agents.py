"""
Task Planning Agents - Agent factory functions for workflow steps

This module contains factory functions to create Agno agents for each
step in the task planning workflow:
- Step 1: Analysis & Selection Agent (tool calling + structured output)
- Step 2: Plan Generation Agent (structured output only)
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
import json
import structlog

from agno.agent import Agent
from agno.models.litellm import LiteLLM
from agno.tools.function import Function

from control_plane_api.app.models.task_planning import (
    TaskPlanResponse,
    AnalysisAndSelectionOutput,
)
from .models import (
    TaskAnalysisOutput,
    ResourceDiscoveryOutput,
    CostEstimationOutput,
    FastSelectionOutput,
)

if TYPE_CHECKING:
    from control_plane_api.app.lib.planning_tools.agno_toolkit import PlanningToolkit

logger = structlog.get_logger()


# ============================================================================
# Tool Builders for Pre-fetched Data
# ============================================================================

def build_prefetch_tools(outer_context: Optional[Dict[str, Any]]) -> List[Function]:
    """
    Build synthetic tools for pre-fetched data access.

    These tools provide instant access to cached data without API calls.

    Args:
        outer_context: Pre-fetched context with agents, teams, environments, queues

    Returns:
        List of Function objects for pre-fetched data access
    """
    tools = []

    if not outer_context:
        return tools

    if outer_context.get("agents"):
        agents_data = outer_context["agents"]

        def get_top_agents() -> str:
            """Get top 20 pre-fetched agents (instant, no API call).
            Use this first before calling search tools."""
            return json.dumps({
                "success": True,
                "data": {
                    "agents": agents_data,
                    "count": len(agents_data),
                    "note": "Top 20 agents. Use search_agents_by_capability() if you need more."
                }
            }, indent=2)

        tools.append(Function.from_callable(get_top_agents))

    if outer_context.get("teams"):
        teams_data = outer_context["teams"]

        def get_top_teams() -> str:
            """Get top 20 pre-fetched teams (instant, no API call).
            Use this first before calling search tools."""
            return json.dumps({
                "success": True,
                "data": {
                    "teams": teams_data,
                    "count": len(teams_data),
                    "note": "Top 20 teams. Use search_teams_by_capability() if you need more."
                }
            }, indent=2)

        tools.append(Function.from_callable(get_top_teams))

    if outer_context.get("environments"):
        envs_data = outer_context["environments"]

        def get_top_environments() -> str:
            """Get top 20 pre-fetched environments (instant, no API call)."""
            return json.dumps({
                "success": True,
                "data": {
                    "environments": envs_data,
                    "count": len(envs_data),
                    "note": "Top 20 environments."
                }
            }, indent=2)

        tools.append(Function.from_callable(get_top_environments))

    if outer_context.get("worker_queues"):
        queues_data = outer_context["worker_queues"]

        def get_top_worker_queues() -> str:
            """Get top 20 pre-fetched worker queues (instant, no API call)."""
            return json.dumps({
                "success": True,
                "data": {
                    "worker_queues": queues_data,
                    "count": len(queues_data),
                    "note": "Top 20 worker queues."
                }
            }, indent=2)

        tools.append(Function.from_callable(get_top_worker_queues))

    return tools


def build_search_tools(planning_toolkit: Optional['PlanningToolkit']) -> List[Function]:
    """
    Build search tools from planning toolkit.

    Args:
        planning_toolkit: Planning toolkit with search functions

    Returns:
        List of Function objects for searching
    """
    tools = []

    if not planning_toolkit or not hasattr(planning_toolkit, 'functions'):
        return tools

    search_tool_names = [
        "search_agents_by_capability",
        "search_teams_by_capability",
        "get_agent_details",
        "get_team_details",
        "get_fallback_agent",
    ]

    for tool_name in search_tool_names:
        if tool_name in planning_toolkit.functions:
            tools.append(planning_toolkit.functions[tool_name])

    return tools


# ============================================================================
# Step 1: Analysis & Selection Agent
# ============================================================================

def create_analysis_and_selection_agent(
    model: LiteLLM,
    planning_toolkit: Optional['PlanningToolkit'] = None,
    outer_context: Optional[Dict[str, Any]] = None
) -> Agent:
    """
    Create Step 1 agent: Task Analysis & Resource Selection.

    Combines task analysis and resource selection into a single efficient agent.
    Uses pre-fetched data for instant access + search tools for specific queries.

    Args:
        model: LiteLLM model instance for the agent
        planning_toolkit: Planning toolkit with search functions
        outer_context: Pre-fetched context (agents, teams, environments, queues)

    Returns:
        Configured Agent for analysis and selection
    """
    # Build tools: pre-fetched data + search tools
    toolkit_tools = build_prefetch_tools(outer_context)
    toolkit_tools.extend(build_search_tools(planning_toolkit))

    # Extract preferred_runtime from outer_context if provided
    preferred_runtime = outer_context.get("preferred_runtime") if outer_context else None

    # Build runtime preference instruction
    if preferred_runtime:
        runtime_instruction = f"MANDATORY: Select agents with runtime='{preferred_runtime}' (user override)"
    else:
        runtime_instruction = (
            "MANDATORY: Select agents with runtime='claude_code' OVER 'default' "
            "when both have the capability. claude_code agents are more capable."
        )

    return Agent(
        name="Task Analyzer & Resource Selector",
        role="Fast agent and environment selection",
        model=model,
        output_schema=AnalysisAndSelectionOutput,
        tools=toolkit_tools,
        instructions=[
            "Select best agent AND environment for task. BE EXTREMELY FAST.",
            "",
            "MANDATORY PROCESS (must call BOTH tools):",
            "1. FIRST: Call get_top_agents() → pick best agent match",
            "2. SECOND: Call get_top_environments() → pick first environment from list",
            "3. Return JSON with BOTH agent AND environment selections",
            "",
            f"CRITICAL RUNTIME RULE: {runtime_instruction}",
            "If multiple agents have the needed capability, ALWAYS pick the one with runtime='claude_code'.",
            "",
            "CRITICAL ENVIRONMENT RULE (DO NOT SKIP):",
            "You MUST call get_top_environments() and select the FIRST environment.",
            "Set selected_environment_id = first environment's 'id' field",
            "Set selected_environment_name = first environment's 'name' field",
            "NEVER leave environment fields null if environments exist!",
            "",
            "UUID: Use EXACT id from tool results, never invent",
            "FALLBACK: Use get_fallback_agent() if no agent match",
            "",
            "OUTPUT: Pure JSON only, start with {",
        ],
        markdown=False,
    )


# ============================================================================
# Step 2: Plan Generation Agent
# ============================================================================

def create_plan_generation_agent(model: LiteLLM) -> Agent:
    """
    Create Step 2 agent: Structured Plan Generation.

    Generates TaskPlanResponse from Step 1 output using Agno's output_schema.

    Args:
        model: LiteLLM model instance for the agent

    Returns:
        Configured Agent for plan generation
    """
    return Agent(
        name="Plan Generator",
        role="Generate structured execution plan",
        model=model,
        output_schema=TaskPlanResponse,
        instructions=[
            "Generate a complete TaskPlanResponse based on Step 1 analysis.",
            "",
            "COPY FROM STEP 1 INPUT:",
            "- entity_id → recommended_execution.entity_id",
            "- entity_name → recommended_execution.entity_name",
            "- entity_type → recommended_execution.entity_type",
            "- runtime, model_id → recommended_execution",
            "- selected_environment_id → recommended_execution.recommended_environment_id AND selected_environment_id",
            "- selected_environment_name → recommended_execution.recommended_environment_name AND selected_environment_name",
            "",
            "CRITICAL: Copy environment fields from Step 1!",
            "If Step 1 has selected_environment_id, you MUST set:",
            "  - recommended_execution.recommended_environment_id = <same value>",
            "  - recommended_execution.recommended_environment_name = <same value>",
            "  - selected_environment_id = <same value>",
            "  - selected_environment_name = <same value>",
            "",
            "IMPORTANT: team_breakdown[].tasks MUST be an empty array: tasks: []",
            "Fill ALL required fields including: estimated_time_hours in team_breakdown, without_kubiya_resources array in realized_savings.",
        ],
        markdown=False,
    )


# ============================================================================
# Legacy Agent Factories (for backward compatibility)
# ============================================================================

def create_task_analysis_agent(model: LiteLLM) -> Agent:
    """
    Legacy Step 1: Task Analysis Agent (deprecated).

    Use create_analysis_and_selection_agent() instead.
    """
    return Agent(
        name="Task Analyzer",
        role="Expert at understanding task requirements and complexity",
        model=model,
        output_schema=TaskAnalysisOutput,
        instructions=[
            "You analyze task descriptions to understand what's needed.",
            "",
            "**Your Responsibilities:**",
            "1. Read the task description carefully",
            "2. Identify what capabilities/skills are required (AWS, Kubernetes, Python, etc.)",
            "3. Determine the task type (deployment, analysis, automation, etc.)",
            "4. Assess complexity on the Fibonacci scale (1, 2, 3, 5, 8, 13, 21)",
            "5. Decide if this needs a single agent or multiple agents (team)",
            "",
            "**Complexity Guidelines:**",
            "- 1-3 points: Simple tasks (list files, basic queries, single API calls)",
            "- 5-8 points: Medium tasks (deployments, multi-step operations)",
            "- 13-21 points: Complex tasks (multi-system integrations, migrations)",
            "",
            "**Output:**",
            "Provide clear analysis with reasoning.",
        ],
        markdown=False,
    )


def create_cost_estimation_agent(model: LiteLLM) -> Agent:
    """
    Legacy Step 3: Cost Estimation Agent (deprecated).

    Cost estimation is now included in Step 2 (plan generation).
    """
    return Agent(
        name="Cost Estimator",
        role="Expert at estimating time and cost for AI agent tasks",
        model=model,
        output_schema=CostEstimationOutput,
        instructions=[
            "You calculate realistic time and cost estimates for AI agent execution.",
            "",
            "**Pricing Reference:**",
            "- Claude Sonnet 4: $0.003/1K input, $0.015/1K output tokens",
            "- Claude Haiku: $0.00025/1K input, $0.00125/1K output tokens",
            "- GPT-4o: $0.0025/1K input, $0.01/1K output tokens",
            "- Tool calls: $0.0001 - $0.001 per call",
            "- Worker runtime: $0.10/hour",
            "",
            "**Token Estimation:**",
            "- Simple tasks (1-3 points): 2-5K input, 1-2K output",
            "- Medium tasks (5-8 points): 5-10K input, 2-5K output",
            "- Complex tasks (13-21 points): 10-20K input, 5-10K output",
            "",
            "**Output:**",
            "Provide detailed cost breakdown with reasoning.",
        ],
        markdown=False,
    )


# ============================================================================
# Fast Selection Agent (--local mode)
# ============================================================================

def create_fast_selection_agent(
    model: LiteLLM,
    outer_context: Dict[str, Any]
) -> Agent:
    """
    Create fast selection agent for --local mode.

    Optimized for speed with minimal output schema and pre-fetched data only.

    Args:
        model: LiteLLM model instance
        outer_context: Pre-fetched context (required for fast mode)

    Returns:
        Configured Agent for fast selection
    """
    # Build only pre-fetched data tools (no API calls)
    toolkit_tools = build_prefetch_tools(outer_context)

    preferred_runtime = outer_context.get("preferred_runtime")
    if preferred_runtime:
        runtime_instruction = f"SELECT agents with runtime='{preferred_runtime}'"
    else:
        runtime_instruction = "PREFER runtime='claude_code' over 'default'"

    return Agent(
        name="Fast Selector",
        role="Quick agent and environment selection",
        model=model,
        output_schema=FastSelectionOutput,
        tools=toolkit_tools,
        instructions=[
            "Select best agent AND environment FAST. Use pre-fetched data only.",
            "",
            f"RUNTIME: {runtime_instruction}",
            "",
            "ENVIRONMENT: Call get_top_environments(), use first environment's id and name",
            "Set recommended_environment_id and recommended_environment_name",
            "",
            "UUID: Use EXACT id from tool results, never invent",
            "OUTPUT: Pure JSON only",
        ],
        markdown=False,
    )
