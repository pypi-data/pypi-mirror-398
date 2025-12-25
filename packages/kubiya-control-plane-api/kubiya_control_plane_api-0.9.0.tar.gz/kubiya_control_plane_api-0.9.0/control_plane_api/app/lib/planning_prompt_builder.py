"""
Shared Planning Prompt Builder

Builds the rich, detailed planning prompt used by ALL strategies (Agno, Claude Code SDK, etc.)
This ensures 100% identical prompts across all implementations.
"""

import json
from typing import List
from control_plane_api.app.models.task_planning import TaskPlanRequest, AgentInfo, TeamInfo
from control_plane_api.app.lib.task_planning.helpers import REFINEMENT_INSTRUCTIONS


def build_planning_prompt(
    request: TaskPlanRequest,
    agents_to_use: List[dict],
    teams_to_use: List[dict],
    pricing_context: str,
) -> str:
    """
    Build the complete planning prompt with full context.

    This is the SAME prompt used by both Agno and Claude Code SDK to ensure
    100% identical results.

    Args:
        request: Task plan request
        agents_to_use: Prepared agents data (JSON-serializable)
        teams_to_use: Prepared teams data (JSON-serializable)
        pricing_context: Model pricing information

    Returns:
        Complete planning prompt string
    """
    # Build environments context
    environments_context = (
        "\n".join(
            [
                f"- **{e.name}** (ID: `{e.id}`)\n"
                f"  - **Type**: {e.type}\n"
                f"  - **Status**: {e.status}"
                for e in request.environments
            ]
        )
        if request.environments
        else "No execution environments specified"
    )

    # Build worker queues context
    worker_queues_context = (
        "\n".join(
            [
                f"- **{q.name}** (ID: `{q.id}`)\n"
                f"  - **Environment**: {q.environment_id or 'Not specified'}\n"
                f"  - **Active Workers**: {q.active_workers}\n"
                f"  - **Status**: {q.status}\n"
                f"  - **Capacity**: {'Available' if q.active_workers > 0 and q.status == 'active' else 'Limited or Inactive'}"
                for q in request.worker_queues
            ]
        )
        if request.worker_queues
        else "No worker queues specified"
    )

    # System capabilities (condensed)
    system_capabilities = "**System**: Code execution (Python/Bash/JS), Cloud (AWS/Azure/GCP), APIs, Kubernetes, Docker, Databases, Monitoring, Security, DevOps/IaC"

    # Check conversation context
    has_conversation_history = bool(request.conversation_context and request.conversation_context.strip())
    should_be_decisive = request.iteration > 1 or has_conversation_history

    # Build the complete prompt
    planning_prompt = f"""
# Task Planning Request - Iteration #{request.iteration}

## Task Description
{request.description}

## Priority
{request.priority.upper()}

{"## Previous Conversation (USE THIS CONTEXT)" if has_conversation_history else ""}
{request.conversation_context if has_conversation_history else ""}

{"## User Feedback for Refinement" if request.refinement_feedback else ""}
{request.refinement_feedback if request.refinement_feedback else ""}

{"## Previous Plan (to be refined)" if request.previous_plan else ""}
{json.dumps(request.previous_plan, indent=2) if request.previous_plan else ""}

{REFINEMENT_INSTRUCTIONS.format(iteration=request.iteration) if request.previous_plan and request.refinement_feedback else ""}

## Available Resources

**IMPORTANT**: Agent and team data below is provided as complete JSON with ALL details including:
- execution_environment (secrets, env_vars, integration_ids)
- skills (with full configuration)
- projects and environments
- capabilities and runtime info

Use this rich data to make informed decisions about agent/team selection and task planning.

### Agents
{json.dumps(agents_to_use, indent=2) if agents_to_use else "No agents available"}

### Teams
{json.dumps(teams_to_use, indent=2) if teams_to_use else "No teams available"}

### Execution Environments
{environments_context}

### Worker Queues
{worker_queues_context}

{system_capabilities}

{pricing_context}

## Your Task

{'**BE DECISIVE**: You have conversation history showing the user has already provided context. DO NOT ask more questions. Use the information provided in the conversation history above to create a reasonable plan. Make sensible assumptions where needed and proceed with planning.' if should_be_decisive else '**FIRST ITERATION**: Review if you have enough context. ONLY ask questions if you are missing CRITICAL information that makes planning impossible (like completely unknown technology stack or domain). If the task is reasonably clear, proceed with planning and make reasonable assumptions.'}

{'**IMPORTANT**: DO NOT ask questions. The user wants a plan now. Use the conversation history above and create a comprehensive plan.' if should_be_decisive else 'If you need CRITICAL information to proceed, set has_questions=true and provide 1-2 critical questions in the questions array. Otherwise, proceed with planning.'}

Analyze this task and provide a comprehensive plan.

**Key Planning Guidelines:**

1. **Agent/Team Selection**: Choose the most capable entity from the lists above based on:
   - Task complexity and requirements → Agent/team capabilities
   - Single agent sufficient? Use agent. Multi-domain? Use team.
   - Match agent model (from model_id) to task complexity

2. **Environment & Queue**: Select environment matching task needs (prod/staging/dev). Choose worker queue with capacity (active_workers > 0, status='active'). Match queue to environment when possible.

3. **Cost Breakdown** (use pricing above):
   - **Token estimates** by complexity: Simple (1-3 pts): 2-5K in/1-2K out. Medium (5-8): 5-10K in/2-5K out. Complex (13-21): 10-20K in/5-10K out
   - **Model costs**: Calculate from token estimates × pricing (Sonnet 4: $0.003/1K in, $0.015/1K out)
   - **Tool costs**: AWS APIs $0.0004-0.001/call, DB queries $0.0001/call, Free tools $0
   - **Runtime**: Time estimate × $0.10/hr
   - **agent_cost** per agent: model_cost + tool_costs
   - **estimated_cost_usd**: Sum all costs

4. **Realized Savings**:
   - **Manual**: Use realistic hourly rates (Senior: $120-200/hr, Mid: $80-120/hr, Jr: $50-80/hr) × estimated manual time
   - **AI**: Use calculated estimated_cost_usd and time
   - **Savings**: money_saved, time_saved_hours, time_saved_percentage
   - **Summary**: Compelling narrative showing concrete savings

5. Use exact IDs from lists. Be specific and actionable. Output valid JSON only.
"""

    return planning_prompt
