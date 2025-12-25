"""
Task Planning Hooks - Pre/Post validation hooks for workflow stability

This module provides Agno-style hooks for validating workflow inputs and outputs.
Hooks run at specific points in the workflow lifecycle:

- Pre-hooks: Run before agent execution (input validation)
- Post-hooks: Run after agent execution (output validation)

Using hooks separates validation logic from agents, improving maintainability
and providing cleaner error handling.
"""

from typing import Dict, Any, Optional, List
import uuid
import structlog

logger = structlog.get_logger()


# ============================================================================
# Custom Exceptions
# ============================================================================

class InputValidationError(Exception):
    """Raised when input validation fails in a pre-hook."""
    pass


class OutputValidationError(Exception):
    """Raised when output validation fails in a post-hook."""
    pass


class EntityNotFoundError(Exception):
    """Raised when a selected entity doesn't exist."""
    pass


class HallucinatedIdError(Exception):
    """Raised when an LLM hallucinates an entity ID."""
    pass


# ============================================================================
# Pre-Hooks (Input Validation)
# ============================================================================

def validate_task_input(
    task_description: str,
    priority: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Pre-hook: Validate task planning input.

    Runs before Step 1 to ensure valid input.

    Args:
        task_description: The task to plan
        priority: Task priority level
        **kwargs: Additional input fields

    Returns:
        Validated input dict

    Raises:
        InputValidationError: If validation fails
    """
    if not task_description or not task_description.strip():
        raise InputValidationError("Task description cannot be empty")

    if len(task_description) > 10000:
        raise InputValidationError(
            f"Task description too long ({len(task_description)} chars). Max 10000."
        )

    valid_priorities = ["low", "medium", "high", "critical", None]
    if priority and priority.lower() not in valid_priorities:
        logger.warning(
            "invalid_priority_normalized",
            provided=priority,
            normalized="medium"
        )
        priority = "medium"

    logger.info(
        "input_validation_passed",
        description_length=len(task_description),
        priority=priority
    )

    return {
        "task_description": task_description.strip(),
        "priority": priority,
        **kwargs
    }


def validate_prefetch_context(
    outer_context: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pre-hook: Validate pre-fetched context data.

    Ensures outer_context has valid structure before workflow runs.

    Args:
        outer_context: Pre-fetched organization resources

    Returns:
        Validated context dict (empty if None)
    """
    if outer_context is None:
        return {}

    validated = {}

    # Validate agents list
    if "agents" in outer_context:
        agents = outer_context["agents"]
        if isinstance(agents, list):
            validated["agents"] = [
                a for a in agents
                if isinstance(a, dict) and a.get("id") and a.get("name")
            ]
            logger.debug("validated_agents", count=len(validated["agents"]))

    # Validate teams list
    if "teams" in outer_context:
        teams = outer_context["teams"]
        if isinstance(teams, list):
            validated["teams"] = [
                t for t in teams
                if isinstance(t, dict) and t.get("id") and t.get("name")
            ]
            logger.debug("validated_teams", count=len(validated["teams"]))

    # Validate environments list
    if "environments" in outer_context:
        envs = outer_context["environments"]
        if isinstance(envs, list):
            validated["environments"] = [
                e for e in envs
                if isinstance(e, dict) and e.get("id") and e.get("name")
            ]
            logger.debug("validated_environments", count=len(validated["environments"]))

    # Validate worker queues list
    if "worker_queues" in outer_context:
        queues = outer_context["worker_queues"]
        if isinstance(queues, list):
            validated["worker_queues"] = [
                q for q in queues
                if isinstance(q, dict) and q.get("id") and q.get("name")
            ]
            logger.debug("validated_worker_queues", count=len(validated["worker_queues"]))

    # Preserve other fields (preferred_runtime, etc.)
    for key in ["preferred_runtime", "pre_fetch_note"]:
        if key in outer_context:
            validated[key] = outer_context[key]

    return validated


# ============================================================================
# Post-Hooks (Output Validation)
# ============================================================================

def validate_step1_output(
    output: Dict[str, Any],
    outer_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Post-hook: Validate Step 1 (Analysis & Selection) output.

    Checks that:
    - Entity ID is a valid UUID
    - Entity ID exists in discovered resources
    - Entity name matches the ID
    - Runtime and model_id are populated

    Args:
        output: Step 1 output dict
        outer_context: Original pre-fetched context for validation

    Returns:
        Validated (and potentially corrected) output

    Raises:
        OutputValidationError: If validation fails and cannot be corrected
        HallucinatedIdError: If entity ID doesn't exist in discovered resources
    """
    entity_id = output.get("selected_entity_id")
    entity_type = output.get("selected_entity_type")
    entity_name = output.get("selected_entity_name")

    # Allow None for edge cases (no suitable resources)
    if entity_id is None:
        logger.warning("step1_no_entity_selected")
        return output

    # Validate UUID format
    try:
        uuid.UUID(entity_id)
    except (ValueError, TypeError):
        # Try to find matching entity by name
        corrected = _try_fix_entity_id(output, outer_context)
        if corrected:
            logger.warning(
                "step1_entity_id_corrected",
                original=entity_id,
                corrected=corrected["selected_entity_id"]
            )
            return corrected

        raise HallucinatedIdError(
            f"Entity ID '{entity_id}' is not a valid UUID. "
            f"LLM may have used name instead of ID."
        )

    # Validate entity exists in discovered lists
    discovered_agents = output.get("discovered_agents", [])
    discovered_teams = output.get("discovered_teams", [])

    if entity_type == "agent":
        agent_ids = [str(a.get("id", "")) for a in discovered_agents]
        if entity_id not in agent_ids:
            raise HallucinatedIdError(
                f"Agent ID '{entity_id}' not found in discovered_agents. "
                f"Available: {agent_ids}"
            )

        # Validate name matches
        for agent in discovered_agents:
            if str(agent.get("id")) == entity_id:
                actual_name = agent.get("name", "")
                if entity_name != actual_name:
                    logger.warning(
                        "step1_entity_name_corrected",
                        provided=entity_name,
                        actual=actual_name
                    )
                    output["selected_entity_name"] = actual_name

                # Auto-populate runtime and model_id if missing
                if not output.get("selected_agent_runtime"):
                    output["selected_agent_runtime"] = agent.get("runtime", "default")
                if not output.get("selected_agent_model_id"):
                    output["selected_agent_model_id"] = agent.get("model_id", "claude-sonnet-4")
                break

    elif entity_type == "team":
        team_ids = [str(t.get("id", "")) for t in discovered_teams]
        if entity_id not in team_ids:
            raise HallucinatedIdError(
                f"Team ID '{entity_id}' not found in discovered_teams. "
                f"Available: {team_ids}"
            )

        # Validate name matches
        for team in discovered_teams:
            if str(team.get("id")) == entity_id:
                actual_name = team.get("name", "")
                if entity_name != actual_name:
                    output["selected_entity_name"] = actual_name
                break

    logger.info(
        "step1_validation_passed",
        entity_type=entity_type,
        entity_id=entity_id[:12] if entity_id else None,
        entity_name=output.get("selected_entity_name")
    )

    return output


def validate_step2_output(
    output: Dict[str, Any],
    step1_output: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Post-hook: Validate Step 2 (Plan Generation) output.

    Checks that:
    - Required fields are present
    - Entity IDs match Step 1 selection
    - team_breakdown has valid structure
    - realized_savings has required fields

    Args:
        output: Step 2 output dict (TaskPlanResponse)
        step1_output: Step 1 output for consistency check

    Returns:
        Validated output

    Raises:
        OutputValidationError: If validation fails
    """
    # Check required top-level fields
    required_fields = ["title", "summary", "complexity", "team_breakdown", "recommended_execution"]
    missing = [f for f in required_fields if f not in output]
    if missing:
        raise OutputValidationError(f"Missing required fields: {missing}")

    # Validate recommended_execution matches Step 1
    if step1_output:
        rec_exec = output.get("recommended_execution", {})
        step1_entity_id = step1_output.get("selected_entity_id")
        step2_entity_id = rec_exec.get("entity_id")

        if step1_entity_id and step2_entity_id and step1_entity_id != step2_entity_id:
            logger.warning(
                "step2_entity_mismatch",
                step1_entity=step1_entity_id,
                step2_entity=step2_entity_id
            )
            # Correct to match Step 1
            rec_exec["entity_id"] = step1_entity_id
            rec_exec["entity_name"] = step1_output.get("selected_entity_name")
            rec_exec["entity_type"] = step1_output.get("selected_entity_type")

    # Validate team_breakdown structure
    team_breakdown = output.get("team_breakdown", [])
    if isinstance(team_breakdown, list):
        for i, team in enumerate(team_breakdown):
            # Ensure tasks is an empty array (not populated)
            if "tasks" in team and team["tasks"]:
                logger.warning(
                    "step2_tasks_cleared",
                    team_index=i,
                    task_count=len(team["tasks"])
                )
                team["tasks"] = []

            # Ensure estimated_time_hours is present
            if "estimated_time_hours" not in team:
                team["estimated_time_hours"] = 0.5

    # Validate realized_savings has without_kubiya_resources
    realized_savings = output.get("realized_savings", {})
    if isinstance(realized_savings, dict):
        if "without_kubiya_resources" not in realized_savings:
            realized_savings["without_kubiya_resources"] = [{
                "role": "DevOps Engineer",
                "hourly_rate": 100.0,
                "estimated_hours": 0.5,
                "total_cost": 50.0
            }]

    logger.info(
        "step2_validation_passed",
        title=output.get("title"),
        team_count=len(team_breakdown) if isinstance(team_breakdown, list) else 0
    )

    return output


# ============================================================================
# Helper Functions
# ============================================================================

def _try_fix_entity_id(
    output: Dict[str, Any],
    outer_context: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Try to fix an invalid entity ID by finding matching entity by name.

    Args:
        output: Output with potentially invalid entity_id
        outer_context: Pre-fetched context to search

    Returns:
        Corrected output dict, or None if cannot fix
    """
    entity_id = output.get("selected_entity_id", "")
    entity_type = output.get("selected_entity_type", "")

    # Search in discovered lists first
    discovered_agents = output.get("discovered_agents", [])
    discovered_teams = output.get("discovered_teams", [])

    # Then in outer_context
    if outer_context:
        if not discovered_agents:
            discovered_agents = outer_context.get("agents", [])
        if not discovered_teams:
            discovered_teams = outer_context.get("teams", [])

    # entity_id might actually be a name - try to find matching entity
    if entity_type == "agent":
        for agent in discovered_agents:
            if agent.get("name") == entity_id:
                output["selected_entity_id"] = str(agent.get("id"))
                output["selected_entity_name"] = agent.get("name")
                output["selected_agent_runtime"] = agent.get("runtime", "default")
                output["selected_agent_model_id"] = agent.get("model_id")
                return output

    elif entity_type == "team":
        for team in discovered_teams:
            if team.get("name") == entity_id:
                output["selected_entity_id"] = str(team.get("id"))
                output["selected_entity_name"] = team.get("name")
                return output

    return None


def validate_environment_selection(
    output: Dict[str, Any],
    discovered_environments: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate environment selection in output.

    Args:
        output: Output containing environment selection
        discovered_environments: List of valid environments

    Returns:
        Validated output
    """
    env_id = output.get("selected_environment_id")
    if env_id is None:
        return output

    env_ids = [str(e.get("id", "")) for e in discovered_environments]
    if env_id not in env_ids:
        logger.warning(
            "invalid_environment_cleared",
            provided_env_id=env_id,
            available=env_ids
        )
        output["selected_environment_id"] = None
        output["selected_environment_name"] = None

    return output


def validate_worker_queue_selection(
    output: Dict[str, Any],
    discovered_queues: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate worker queue selection in output.

    Args:
        output: Output containing queue selection
        discovered_queues: List of valid queues

    Returns:
        Validated output
    """
    queue_id = output.get("selected_worker_queue_id")
    if queue_id is None:
        return output

    queue_ids = [str(q.get("id", "")) for q in discovered_queues]
    if queue_id not in queue_ids:
        logger.warning(
            "invalid_queue_cleared",
            provided_queue_id=queue_id,
            available=queue_ids
        )
        output["selected_worker_queue_id"] = None
        output["selected_worker_queue_name"] = None

    return output
