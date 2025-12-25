"""
Task Plan Response Validator

Validates planner output quality and completeness to ensure reliable plans.
"""

from typing import List, Tuple
from control_plane_api.app.models.task_planning import TaskPlanResponse, TaskPlanRequest
import structlog

logger = structlog.get_logger()


def validate_plan_response(
    plan: TaskPlanResponse,
    request: TaskPlanRequest
) -> Tuple[bool, List[str]]:
    """
    Validate plan quality and completeness.

    Args:
        plan: The generated task plan
        request: The original planning request

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # 1. Check required fields
    if not plan.title or len(plan.title.strip()) == 0:
        errors.append("Missing or empty title")

    if not plan.summary or len(plan.summary.strip()) < 10:
        errors.append("Summary is missing or too short (minimum 10 characters)")

    if not plan.recommended_execution or not plan.recommended_execution.entity_id:
        errors.append("Missing recommended execution entity")

    # 2. Validate entity exists in provided list
    if plan.recommended_execution and plan.recommended_execution.entity_id:
        entity_type = plan.recommended_execution.entity_type
        entity_id = plan.recommended_execution.entity_id

        if entity_type == "agent":
            valid_ids = [a.id for a in request.agents]
            if entity_id not in valid_ids:
                errors.append(
                    f"Selected agent '{entity_id}' not in available agents list. "
                    f"Valid IDs: {valid_ids[:5]}{'...' if len(valid_ids) > 5 else ''}"
                )
        elif entity_type == "team":
            valid_ids = [t.id for t in request.teams]
            if entity_id not in valid_ids:
                errors.append(
                    f"Selected team '{entity_id}' not in available teams list. "
                    f"Valid IDs: {valid_ids[:5]}{'...' if len(valid_ids) > 5 else ''}"
                )
        else:
            errors.append(f"Invalid entity_type: '{entity_type}'. Must be 'agent' or 'team'")

    # 3. Check complexity is reasonable
    if plan.complexity:
        story_points = plan.complexity.story_points
        if not (1 <= story_points <= 21):
            errors.append(
                f"Invalid story points: {story_points}. Must be between 1 and 21 (Fibonacci sequence)"
            )

        if not plan.complexity.confidence or plan.complexity.confidence not in ["low", "medium", "high"]:
            errors.append(
                f"Invalid confidence level: '{plan.complexity.confidence}'. Must be 'low', 'medium', or 'high'"
            )
    else:
        errors.append("Missing complexity information")

    # 4. Check cost is non-zero and reasonable
    if plan.cost_estimate:
        cost = plan.cost_estimate.estimated_cost_usd
        if cost <= 0:
            errors.append("Cost estimate must be positive (greater than 0)")
        if cost > 100:
            errors.append(
                f"Cost estimate seems too high: ${cost:.2f}. "
                "Review token estimates and tool costs. Typical tasks cost $0.01-$10."
            )
    else:
        errors.append("Missing cost estimate")

    # 5. Check reasoning quality
    if plan.recommended_execution:
        reasoning = plan.recommended_execution.execution_reasoning
        if not reasoning or len(reasoning.strip()) < 20:
            errors.append(
                "Execution reasoning is too short or missing. "
                "Need clear explanation (minimum 20 characters) of why this agent/team was selected."
            )

    # 6. Validate team breakdown exists and has content
    if not plan.team_breakdown or len(plan.team_breakdown) == 0:
        errors.append("Missing team breakdown - at least one team member entry required")

    # 7. Check environment/queue selection if provided in request
    if request.environments and len(request.environments) > 0:
        if not plan.recommended_execution.recommended_environment_id:
            errors.append(
                "Environments were provided but none was selected. "
                "Must select an environment from the available list."
            )

    # 8. Validate realized savings calculations make sense
    if plan.realized_savings:
        savings = plan.realized_savings
        if savings.with_kubiya_cost > savings.without_kubiya_cost:
            errors.append(
                f"Invalid savings calculation: with_kubiya_cost (${savings.with_kubiya_cost:.2f}) "
                f"is greater than without_kubiya_cost (${savings.without_kubiya_cost:.2f}). "
                "Kubiya should save money, not cost more."
            )

        calculated_savings = savings.without_kubiya_cost - savings.with_kubiya_cost
        if abs(calculated_savings - savings.money_saved) > 0.01:
            errors.append(
                f"Savings calculation mismatch: money_saved (${savings.money_saved:.2f}) "
                f"does not match without_kubiya_cost - with_kubiya_cost (${calculated_savings:.2f})"
            )

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(
            "plan_validation_failed",
            error_count=len(errors),
            errors=errors,
            title=plan.title if plan.title else "N/A"
        )
    else:
        logger.info("plan_validation_succeeded", title=plan.title)

    return (is_valid, errors)


def format_validation_errors_for_retry(errors: List[str]) -> str:
    """
    Format validation errors into a prompt enhancement for retry.

    Args:
        errors: List of validation error messages

    Returns:
        Formatted string to append to prompt
    """
    error_bullets = "\n".join(f"- {error}" for error in errors)

    return f"""

**⚠️ PREVIOUS ATTEMPT FAILED VALIDATION**

The previous plan had the following issues that must be fixed:

{error_bullets}

**CRITICAL**: Please address ALL of the above issues in your new plan.
Ensure all required fields are present, IDs match exactly from the provided lists,
and all calculations are correct.
"""
