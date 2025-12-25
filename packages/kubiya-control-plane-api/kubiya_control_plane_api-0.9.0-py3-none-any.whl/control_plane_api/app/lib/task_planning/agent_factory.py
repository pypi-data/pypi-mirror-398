"""
Task Planning Agent Factory
"""
from typing import Optional, Callable
from sqlalchemy.orm import Session
import structlog
import os

from agno.agent import Agent
from agno.models.litellm import LiteLLM
from control_plane_api.app.models.task_planning import TaskPlanResponse
from control_plane_api.app.lib.planning_tools import (
    AgentsContextTools,
    TeamsContextTools,
    EnvironmentsContextTools,
    ResourcesContextTools,
    KnowledgeContextTools,
)
from control_plane_api.app.lib.planning_tools.context_graph_tools import ContextGraphPlanningTools

logger = structlog.get_logger()


def create_planning_agent(
    organization_id: Optional[str] = None,
    db: Optional[Session] = None,
    api_token: str = None,
    tool_hook: Optional[Callable] = None,
    quick_mode: bool = False
) -> Agent:
    """
    Create an Agno agent for task planning using LiteLLM with context tools

    Args:
        organization_id: Optional organization ID for filtering resources
        db: Database session to pass to tools
        api_token: API token for accessing organizational knowledge (required)
        tool_hook: Optional hook to capture tool executions for streaming
        quick_mode: If True, use faster, cheaper model for quick planning (Haiku instead of Sonnet)
    """
    # Get LiteLLM configuration
    litellm_api_url = (
        os.getenv("LITELLM_API_URL") or
        os.getenv("LITELLM_API_BASE") or
        "https://llm-proxy.kubiya.ai"
    ).strip()

    litellm_api_key = os.getenv("LITELLM_API_KEY", "").strip()

    if not litellm_api_key:
        raise ValueError("LITELLM_API_KEY environment variable not set")

    # Use same model for both modes (Sonnet 4)
    # Note: quick_mode parameter kept for future use if needed
    model = os.getenv("LITELLM_DEFAULT_MODEL", "kubiya/claude-sonnet-4").strip()
    logger.info("creating_planning_agent", model=model, quick_mode=quick_mode)

    logger.info(
        "creating_agno_planning_agent_with_tools",
        litellm_api_url=litellm_api_url,
        model=model,
        has_api_key=bool(litellm_api_key),
        organization_id=organization_id,
    )

    # Initialize context tools with database session
    # NOTE: Keep agents_tools and teams_tools for backward compatibility,
    # but planning agent should primarily use context_graph_tools for intelligent discovery
    agents_tools = AgentsContextTools(db=db, organization_id=organization_id)
    teams_tools = TeamsContextTools(db=db, organization_id=organization_id)
    environments_tools = EnvironmentsContextTools(db=db, organization_id=organization_id)
    resources_tools = ResourcesContextTools(db=db, organization_id=organization_id)
    knowledge_tools = KnowledgeContextTools(db=db, organization_id=organization_id, api_token=api_token)

    # NEW: Add context graph tools for intelligent resource discovery
    context_graph_tools = ContextGraphPlanningTools(
        db=db,
        organization_id=organization_id,
        api_token=api_token
    )

    # Build tools list with context graph tools FIRST (higher priority for tool-based discovery)
    tools_list = [
        context_graph_tools,  # Primary discovery method via context graph
        agents_tools,         # Fallback for direct agent queries
        teams_tools,          # Fallback for direct team queries
        environments_tools,
        resources_tools,
        knowledge_tools,      # Include knowledge tools for comprehensive planning
    ]

    logger.info("planning_agent_tools_initialized",
                tools_count=len(tools_list),
                has_context_graph=True,
                has_knowledge=True,
                has_api_token=bool(api_token))

    # Create fast planning agent optimized for speed
    planning_agent = Agent(
        name="Task Planning Agent",
        role="Expert project manager and task planner",
        model=LiteLLM(
            id=f"openai/{model}",
            api_base=litellm_api_url,
            api_key=litellm_api_key,
            request_params={
                "timeout": 120,  # 2 minute timeout for LiteLLM requests
            },
        ),
        # NOTE: output_schema blocks reasoning streams! Removed to enable real-time streaming.
        # We'll parse the JSON response manually after streaming completes.
        # output_schema=TaskPlanResponse,
        tools=tools_list,
        tool_hooks=[tool_hook] if tool_hook else None,  # FIX: Agno expects tool_hooks (plural) as a list
        instructions=[
            "You are a CONCISE task planning analyst producing KEY INSIGHTS for structured output conversion.",
            "",
            "**CRITICAL - Be CONCISE:**",
            "- You are Agent 1 in a two-agent workflow - provide KEY POINTS ONLY",
            "- Agent 2 will convert your analysis to JSON - keep it SHORT and FOCUSED",
            "- DO NOT produce verbose reasoning - focus on ESSENTIAL insights",
            "- DO NOT return JSON - return brief analysis that answers: WHO, WHAT, HOW, WHEN",
            "",
            "**Required Analysis (Keep Each Section Brief):**",
            "",
            "1. **Task Summary** (2-3 sentences):",
            "   - What needs to be done and why",
            "",
            "2. **Recommended Agent/Team** (1-2 sentences):",
            "   - Which agent/team should handle this",
            "   - Key reason: relevant skills + available secrets/env_vars",
            "",
            "3. **Complexity Assessment** (1 sentence):",
            "   - Story points (1-20) and justification",
            "",
            "4. **Task Breakdown** (List format):",
            "   - Task 1: [title] - [what to do] - [which skills/secrets to use]",
            "   - Task 2: [title] - [what to do] - [dependencies: task 1]",
            "   - Keep each task description to 1-2 sentences max",
            "",
            "5. **Prerequisites** (bullet list if any):",
            "   - Required setup or dependencies",
            "",
            "6. **Risks** (bullet list if any):",
            "   - Key risks to be aware of",
            "",
            "**Available Tools** (use sparingly):",
            "- list_agents() - Get available agents",
            "- get_agent_details(id) - Get specific agent info",
            "- query_knowledge(q) - Search knowledge base",
            "",
            "**Agent Context Format:**",
            "- Agent skills: agent['skills'] array",
            "- Secrets: agent['execution_environment']['secrets'] keys",
            "- Env vars: agent['execution_environment']['env_vars'] keys",
            "",
            "**Example Output Format:**",
            "```",
            "Task: Deploy auth service to production",
            "",
            "Recommended: DevOps Agent",
            "Reason: Has aws_ec2 skill and AWS_ACCESS_KEY_ID secret",
            "",
            "Complexity: 8 story points (multi-step deployment)",
            "",
            "Tasks:",
            "1. Validate deployment config - check YAML syntax - uses kubectl skill",
            "2. Deploy to staging - run kubectl apply - uses KUBECONFIG env var - depends on task 1",
            "3. Run smoke tests - verify endpoints - uses curl",
            "4. Promote to prod - kubectl apply to prod namespace - depends on tasks 2,3",
            "",
            "Prerequisites:",
            "- Valid kubeconfig for target cluster",
            "",
            "Risks:",
            "- Downtime during deployment",
            "```",
            "",
            "REMEMBER: Keep it SHORT. Agent 2 handles JSON structuring.",
        ],
        description="Fast task planner for AI agent teams",
        markdown=False,
        add_history_to_context=False,  # Disable for speed
        retries=3,  # Increased retries for reliability
    )

    return planning_agent


def create_structuring_agent() -> Agent:
    """
    Create a fast structuring agent that converts reasoning output to structured JSON.

    This is Agent 2 in the two-agent workflow:
    1. Agent 1 (planning_agent) streams reasoning/thinking
    2. Agent 2 (structuring_agent) converts reasoning to TaskPlanResponse

    Returns:
        Agent configured with output_schema for structured JSON output
    """
    # Get LiteLLM configuration
    litellm_api_url = (
        os.getenv("LITELLM_API_URL") or
        os.getenv("LITELLM_API_BASE") or
        "https://llm-proxy.kubiya.ai"
    ).strip()

    litellm_api_key = os.getenv("LITELLM_API_KEY", "").strip()

    if not litellm_api_key:
        raise ValueError("LITELLM_API_KEY environment variable not set")

    # Use same model as Agent 1 for structuring (Sonnet 4)
    # Can be overridden with LITELLM_STRUCTURING_MODEL env var if Haiku is available
    model = os.getenv("LITELLM_STRUCTURING_MODEL", os.getenv("LITELLM_DEFAULT_MODEL", "kubiya/claude-sonnet-4")).strip()
    logger.info("creating_structuring_agent", model=model)

    structuring_agent = Agent(
        name="Task Structuring Agent",
        role="Expert at converting task planning analysis into structured JSON",
        model=LiteLLM(
            id=f"openai/{model}",
            api_base=litellm_api_url,
            api_key=litellm_api_key,
            request_params={
                "timeout": 60,  # 1 minute timeout for structuring
            },
        ),
        output_schema=TaskPlanResponse,  # IMPORTANT: This enforces structured output
        tools=[],  # No tools needed for structuring
        instructions=[
            "You are a task structuring agent that converts planning analysis into structured JSON.",
            "",
            "**Your Job:**",
            "- You will receive detailed planning analysis and reasoning from another agent",
            "- Extract all the key information from that analysis",
            "- Convert it into a properly structured TaskPlanResponse JSON object",
            "",
            "**CRITICAL Requirements:**",
            "- You MUST return valid JSON matching the TaskPlanResponse schema",
            "- DO NOT add any reasoning, explanations, or markdown",
            "- ONLY return the structured JSON object",
            "- Ensure all required fields are populated with data from the analysis",
            "",
            "**Task Breakdown Fields:**",
            "- Extract tasks with: id, title, description, details, test_strategy, priority, dependencies",
            "- Extract skills_to_use, env_vars_to_use, secrets_to_use, knowledge_references from the analysis",
            "- Ensure task IDs are sequential integers starting from 1",
            "- Set dependencies as arrays of task IDs ([] if no dependencies)",
            "",
            "**If Information is Missing:**",
            "- Use reasonable defaults based on the task description",
            "- Set array fields to [] if not specified (never null)",
            "- Provide basic but complete task breakdowns even if analysis is sparse",
        ],
        description="Fast structuring agent for converting analysis to JSON",
        markdown=False,
        add_history_to_context=False,
    )

    logger.info("structuring_agent_created", model=model)
    return structuring_agent


def create_planning_workflow(
    organization_id: Optional[str] = None,
    db: Optional[Session] = None,
    api_token: str = None,
    tool_hook: Optional[Callable] = None,
) -> "Workflow":
    """
    Create an Agno Workflow that chains the reasoning agent → structuring agent.

    This implements the proper two-agent workflow:
    1. Agent 1 (reasoning): Analyzes task, uses tools, streams thinking
    2. Agent 2 (structuring): Converts analysis to TaskPlanResponse JSON

    Args:
        organization_id: Optional organization ID for filtering resources
        db: Database session to pass to tools
        api_token: API token for accessing organizational knowledge
        tool_hook: Optional hook to capture tool executions for streaming

    Returns:
        Workflow with two steps: reasoning → structuring
    """
    from agno.workflow import Workflow

    # Create Agent 1 (reasoning with tools)
    reasoning_agent = create_planning_agent(
        organization_id=organization_id,
        db=db,
        api_token=api_token,
        tool_hook=tool_hook
    )

    # Create Agent 2 (structuring without tools)
    structuring_agent = create_structuring_agent()

    # Chain them in a workflow
    workflow = Workflow(
        name="Task Planning Workflow",
        steps=[reasoning_agent, structuring_agent],
        description="Two-step workflow: analyze task → structure output"
    )

    logger.info("planning_workflow_created", steps=2)
    return workflow
