"""
Task Planning Models - Pydantic schemas for workflow steps

This module contains all Pydantic models used in the task planning workflow:
- Step output schemas (TaskAnalysisOutput, ResourceDiscoveryOutput, etc.)
- Validation logic to prevent hallucinated IDs
- Fast selection schema for --local mode
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
import uuid
import structlog

logger = structlog.get_logger()


# ============================================================================
# Step 1: Task Analysis Output
# ============================================================================

class TaskAnalysisOutput(BaseModel):
    """Output from Step 1: Task Analysis"""

    task_summary: str = Field(description="Clear 1-2 sentence summary of what needs to be done")
    required_capabilities: List[str] = Field(
        description="List of required capabilities (e.g., 'aws_s3', 'kubectl', 'python')"
    )
    task_type: str = Field(
        description="Type of task: deployment, analysis, automation, migration, monitoring, etc."
    )
    complexity_estimate: str = Field(
        description="Initial complexity assessment: simple, moderate, complex"
    )
    story_points_estimate: int = Field(
        description="Story points estimate (1-21 Fibonacci scale)",
        ge=1,
        le=21
    )
    needs_multi_agent: bool = Field(
        description="Whether this task requires multiple agents (team) or single agent"
    )
    reasoning: str = Field(
        description="Explanation of analysis and why these capabilities are needed"
    )


# ============================================================================
# Step 2: Resource Discovery Output
# ============================================================================

class ResourceDiscoveryOutput(BaseModel):
    """Output from Step 2: Resource Discovery

    CRITICAL: recommended_entity_id MUST come from discovered_agents or discovered_teams.
    This validator ensures no hallucinated IDs.
    """

    discovered_agents: List[Dict[str, Any]] = Field(
        description="REQUIRED: List of agents found using tools. Must call list_agents() or search_agents_by_capability().",
        min_length=0
    )
    discovered_teams: List[Dict[str, Any]] = Field(
        description="REQUIRED: List of teams found using tools. Must call list_teams() or search_teams_by_capability().",
        min_length=0
    )
    recommended_entity_type: Optional[str] = Field(
        default=None,
        description="Either 'agent' or 'team' based on task needs (None if no resources available)"
    )
    recommended_entity_id: Optional[str] = Field(
        default=None,
        description="ID of the recommended agent or team - MUST exist in discovered_agents or discovered_teams (None if no resources available)"
    )
    recommended_entity_name: Optional[str] = Field(
        default=None,
        description="Name of the recommended agent or team - MUST match the name from tool results (None if no resources available)"
    )
    reasoning: str = Field(
        description="Why this agent/team was selected as best match from the discovered options"
    )
    discovered_environments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of environments found using list_environments() tool. Required if recommending environment."
    )
    discovered_worker_queues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of worker queues found using list_worker_queues() tool. Required if recommending queue."
    )
    recommended_environment_id: Optional[str] = Field(
        default=None,
        description="UUID of the recommended environment - MUST exist in discovered_environments (not a name!)"
    )
    recommended_environment_name: Optional[str] = Field(
        default=None,
        description="Name of the recommended environment - MUST match the name from discovered_environments"
    )
    recommended_worker_queue_id: Optional[str] = Field(
        default=None,
        description="UUID of the recommended worker queue - MUST exist in discovered_worker_queues (not a name!)"
    )
    recommended_worker_queue_name: Optional[str] = Field(
        default=None,
        description="Name of the recommended worker queue - MUST match the name from discovered_worker_queues"
    )

    @field_validator('discovered_agents', 'discovered_teams')
    @classmethod
    def validate_discovered_not_empty(cls, v, info):
        """At least one of discovered_agents or discovered_teams must have results"""
        return v

    @field_validator('recommended_entity_id')
    @classmethod
    def validate_entity_id_exists(cls, v, info):
        """CRITICAL: Validate that recommended ID is a UUID and exists in discovered lists"""
        if v is None:
            return v

        # Validate UUID format
        try:
            uuid.UUID(v)
        except (ValueError, AttributeError, TypeError):
            raise ValueError(
                f"recommended_entity_id '{v}' is NOT a valid UUID! "
                f"You MUST use the 'id' field (UUID) from tool results, NOT the 'name' field!"
            )

        discovered_agents = info.data.get('discovered_agents', [])
        discovered_teams = info.data.get('discovered_teams', [])
        entity_type = info.data.get('recommended_entity_type', '')

        if not discovered_agents and not discovered_teams:
            raise ValueError(
                "Cannot recommend an entity when no agents or teams were discovered."
            )

        if entity_type == 'agent':
            agent_ids = [str(a.get('id', '')) for a in discovered_agents if a.get('id')]
            if v not in agent_ids:
                raise ValueError(
                    f"Recommended agent_id '{v}' does not exist in discovered_agents. "
                    f"Available: {agent_ids}"
                )
        elif entity_type == 'team':
            team_ids = [str(t.get('id', '')) for t in discovered_teams if t.get('id')]
            if v not in team_ids:
                raise ValueError(
                    f"Recommended team_id '{v}' does not exist in discovered_teams. "
                    f"Available: {team_ids}"
                )
        else:
            raise ValueError(f"recommended_entity_type must be 'agent' or 'team', got '{entity_type}'")

        return v

    @field_validator('recommended_entity_name')
    @classmethod
    def validate_entity_name_matches(cls, v, info):
        """Validate that recommended name matches the entity from discovered lists"""
        if v is None:
            return v

        discovered_agents = info.data.get('discovered_agents', [])
        discovered_teams = info.data.get('discovered_teams', [])
        entity_type = info.data.get('recommended_entity_type', '')
        entity_id = info.data.get('recommended_entity_id', '')

        if entity_type == 'agent':
            for agent in discovered_agents:
                if str(agent.get('id')) == entity_id:
                    actual_name = agent.get('name', '')
                    if v != actual_name:
                        raise ValueError(f"Name '{v}' doesn't match agent name '{actual_name}'")
                    break
        elif entity_type == 'team':
            for team in discovered_teams:
                if str(team.get('id')) == entity_id:
                    actual_name = team.get('name', '')
                    if v != actual_name:
                        raise ValueError(f"Name '{v}' doesn't match team name '{actual_name}'")
                    break

        return v

    @field_validator('recommended_environment_id')
    @classmethod
    def validate_environment_id_exists(cls, v, info):
        """Validate environment ID exists in discovered list"""
        if v is None:
            return v

        discovered_environments = info.data.get('discovered_environments', [])
        if not discovered_environments:
            raise ValueError("Cannot recommend environment when none were discovered.")

        env_ids = [str(e.get('id', '')) for e in discovered_environments if e.get('id')]
        if v not in env_ids:
            raise ValueError(f"Environment ID '{v}' not in discovered list: {env_ids}")

        return v

    @field_validator('recommended_environment_name')
    @classmethod
    def validate_environment_name_matches(cls, v, info):
        """Validate environment name matches the ID"""
        if v is None:
            return v

        discovered_environments = info.data.get('discovered_environments', [])
        environment_id = info.data.get('recommended_environment_id', '')

        for env in discovered_environments:
            if str(env.get('id')) == environment_id:
                actual_name = env.get('name', '')
                if v != actual_name:
                    raise ValueError(f"Environment name '{v}' doesn't match '{actual_name}'")
                break

        return v

    @field_validator('recommended_worker_queue_id')
    @classmethod
    def validate_worker_queue_id_exists(cls, v, info):
        """Validate worker queue ID exists in discovered list"""
        if v is None:
            return v

        discovered_worker_queues = info.data.get('discovered_worker_queues', [])
        if not discovered_worker_queues:
            raise ValueError("Cannot recommend queue when none were discovered.")

        queue_ids = [str(q.get('id', '')) for q in discovered_worker_queues if q.get('id')]
        if v not in queue_ids:
            raise ValueError(f"Queue ID '{v}' not in discovered list: {queue_ids}")

        return v

    @field_validator('recommended_worker_queue_name')
    @classmethod
    def validate_worker_queue_name_matches(cls, v, info):
        """Validate worker queue name matches the ID"""
        if v is None:
            return v

        discovered_worker_queues = info.data.get('discovered_worker_queues', [])
        queue_id = info.data.get('recommended_worker_queue_id', '')

        for queue in discovered_worker_queues:
            if str(queue.get('id')) == queue_id:
                actual_name = queue.get('name', '')
                if v != actual_name:
                    raise ValueError(f"Queue name '{v}' doesn't match '{actual_name}'")
                break

        return v


# ============================================================================
# Fast Selection Output (--local mode)
# ============================================================================

class FastSelectionOutput(BaseModel):
    """
    Fast selection output for --local mode - minimal fields for quick execution.
    Uses same validators as ResourceDiscoveryOutput to prevent hallucination.
    """

    discovered_agents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of agents found"
    )
    discovered_teams: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of teams found"
    )
    discovered_environments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of environments found"
    )
    discovered_worker_queues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of worker queues found"
    )

    recommended_entity_type: str = Field(..., description="'agent' or 'team'")
    recommended_entity_id: str = Field(..., description="UUID of agent/team from discovered list")
    recommended_entity_name: str = Field(..., description="Name of agent/team from discovered list")

    selected_agent_runtime: Optional[str] = Field(
        None,
        description="Runtime of selected agent ('default' or 'claude_code')"
    )
    selected_agent_model_id: Optional[str] = Field(
        None,
        description="Model ID of selected agent"
    )

    recommended_environment_id: Optional[str] = Field(None, description="UUID of environment")
    recommended_environment_name: Optional[str] = Field(None, description="Name of environment")
    recommended_worker_queue_id: Optional[str] = Field(None, description="UUID of worker queue")
    recommended_worker_queue_name: Optional[str] = Field(None, description="Name of worker queue")

    reasoning: str = Field(..., description="Brief explanation of selection")

    # Reuse validators from ResourceDiscoveryOutput
    @field_validator('recommended_entity_id')
    @classmethod
    def validate_entity_id_exists(cls, v, info):
        """Validate entity ID is UUID and exists in discovered lists"""
        try:
            uuid.UUID(v)
        except (ValueError, AttributeError, TypeError):
            raise ValueError(f"'{v}' is NOT a valid UUID!")

        discovered_agents = info.data.get('discovered_agents', [])
        discovered_teams = info.data.get('discovered_teams', [])
        entity_type = info.data.get('recommended_entity_type', '')

        if not discovered_agents and not discovered_teams:
            raise ValueError("No agents or teams were discovered.")

        if entity_type == 'agent':
            agent_ids = [str(a.get('id', '')) for a in discovered_agents if a.get('id')]
            if v not in agent_ids:
                raise ValueError(f"Agent ID '{v}' not found. Available: {agent_ids}")
        elif entity_type == 'team':
            team_ids = [str(t.get('id', '')) for t in discovered_teams if t.get('id')]
            if v not in team_ids:
                raise ValueError(f"Team ID '{v}' not found. Available: {team_ids}")
        else:
            raise ValueError(f"Entity type must be 'agent' or 'team', got '{entity_type}'")

        return v

    @field_validator('recommended_entity_name')
    @classmethod
    def validate_entity_name_matches(cls, v, info):
        """Validate entity name matches the ID"""
        discovered_agents = info.data.get('discovered_agents', [])
        discovered_teams = info.data.get('discovered_teams', [])
        entity_type = info.data.get('recommended_entity_type', '')
        entity_id = info.data.get('recommended_entity_id', '')

        if entity_type == 'agent':
            for agent in discovered_agents:
                if str(agent.get('id')) == entity_id:
                    actual_name = agent.get('name', '')
                    if v != actual_name:
                        raise ValueError(f"Name '{v}' doesn't match '{actual_name}'")
                    break
        elif entity_type == 'team':
            for team in discovered_teams:
                if str(team.get('id')) == entity_id:
                    actual_name = team.get('name', '')
                    if v != actual_name:
                        raise ValueError(f"Name '{v}' doesn't match '{actual_name}'")
                    break

        return v

    @field_validator('recommended_environment_id')
    @classmethod
    def validate_environment_id_exists(cls, v, info):
        """Validate environment ID if provided"""
        if v is None:
            return v

        discovered_environments = info.data.get('discovered_environments', [])
        if not discovered_environments:
            raise ValueError("No environments discovered.")

        env_ids = [str(e.get('id', '')) for e in discovered_environments if e.get('id')]
        if v not in env_ids:
            raise ValueError(f"Environment ID '{v}' not found. Available: {env_ids}")

        return v

    @field_validator('recommended_worker_queue_id')
    @classmethod
    def validate_worker_queue_id_exists(cls, v, info):
        """Validate worker queue ID if provided"""
        if v is None:
            return v

        discovered_worker_queues = info.data.get('discovered_worker_queues', [])
        if not discovered_worker_queues:
            raise ValueError("No worker queues discovered.")

        queue_ids = [str(q.get('id', '')) for q in discovered_worker_queues if q.get('id')]
        if v not in queue_ids:
            raise ValueError(f"Queue ID '{v}' not found. Available: {queue_ids}")

        return v


# ============================================================================
# Cost Estimation Output
# ============================================================================

class CostEstimationOutput(BaseModel):
    """Output from Step 3: Cost Estimation"""

    estimated_tokens_input: int = Field(description="Estimated input tokens")
    estimated_tokens_output: int = Field(description="Estimated output tokens")
    estimated_llm_cost: float = Field(description="Estimated LLM API cost in USD")
    estimated_tool_cost: float = Field(description="Estimated tool execution cost in USD")
    estimated_runtime_cost: float = Field(description="Estimated worker runtime cost in USD")
    total_cost: float = Field(description="Total estimated cost in USD")
    estimated_time_hours: float = Field(description="Estimated execution time in hours")

    # Savings calculation
    manual_cost: float = Field(description="Cost if done manually by humans")
    manual_time_hours: float = Field(description="Time if done manually in hours")
    money_saved: float = Field(description="Money saved by using AI")
    time_saved_hours: float = Field(description="Time saved in hours")
    savings_percentage: float = Field(description="Percentage of time saved")

    reasoning: str = Field(description="Explanation of cost calculations")


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_resource_discovery(output: ResourceDiscoveryOutput) -> None:
    """
    Explicitly validate ResourceDiscoveryOutput to catch issues.

    This is a safety net in case Pydantic validation is bypassed.
    Raises ValueError with detailed diagnostics.
    """
    # Check discovered lists are populated
    if not output.discovered_agents and not output.discovered_teams:
        raise ValueError(
            "Both discovered_agents and discovered_teams are empty. "
            "You MUST call list_agents() or list_teams() tools!"
        )

    if output.recommended_entity_id is None:
        logger.warning(
            "no_entity_recommended",
            discovered_agents=len(output.discovered_agents),
            discovered_teams=len(output.discovered_teams)
        )
        return

    # Validate UUID format
    try:
        uuid.UUID(output.recommended_entity_id)
    except (ValueError, AttributeError) as e:
        # Try to fix by finding matching entity
        if output.recommended_entity_type == 'agent':
            matching = next(
                (a for a in output.discovered_agents if a.get('name') == output.recommended_entity_id),
                None
            )
            if matching:
                logger.warning(
                    "entity_id_was_name_fixed",
                    provided_name=output.recommended_entity_id,
                    correct_uuid=matching.get('id')
                )
                output.recommended_entity_id = str(matching.get('id'))
                output.recommended_entity_name = matching.get('name')
            else:
                raise ValueError(f"'{output.recommended_entity_id}' is not a valid UUID and no matching agent found")
        elif output.recommended_entity_type == 'team':
            matching = next(
                (t for t in output.discovered_teams if t.get('name') == output.recommended_entity_id),
                None
            )
            if matching:
                logger.warning(
                    "entity_id_was_name_fixed",
                    provided_name=output.recommended_entity_id,
                    correct_uuid=matching.get('id')
                )
                output.recommended_entity_id = str(matching.get('id'))
                output.recommended_entity_name = matching.get('name')
            else:
                raise ValueError(f"'{output.recommended_entity_id}' is not a valid UUID and no matching team found")

    # Validate ID exists in appropriate list
    if output.recommended_entity_type == 'agent':
        agent_ids = [str(a.get('id', '')) for a in output.discovered_agents if a.get('id')]
        if output.recommended_entity_id not in agent_ids:
            raise ValueError(
                f"Entity ID '{output.recommended_entity_id}' not in discovered_agents: {agent_ids}"
            )
    elif output.recommended_entity_type == 'team':
        team_ids = [str(t.get('id', '')) for t in output.discovered_teams if t.get('id')]
        if output.recommended_entity_id not in team_ids:
            raise ValueError(
                f"Entity ID '{output.recommended_entity_id}' not in discovered_teams: {team_ids}"
            )

    logger.info(
        "resource_discovery_validation_passed",
        entity_type=output.recommended_entity_type,
        entity_id=output.recommended_entity_id[:12] if output.recommended_entity_id else None,
        entity_name=output.recommended_entity_name
    )
