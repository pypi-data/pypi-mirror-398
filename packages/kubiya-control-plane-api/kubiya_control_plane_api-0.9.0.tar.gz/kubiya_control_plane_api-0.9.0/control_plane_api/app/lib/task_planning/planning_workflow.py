"""
Task Planning Workflow - Multi-step deterministic planning using Agno Workflows

This module implements a structured, multi-agent workflow for task planning:
1. Task Analysis - Understand requirements and identify needed capabilities
2. Resource Discovery - Find matching agents/teams using context graph
3. Cost Estimation - Calculate time and cost estimates
4. Plan Generation - Create final structured execution plan

Each step has clear inputs/outputs and can be streamed for real-time progress updates.

NOTE: This module has been refactored into smaller modules for maintainability:
- models.py: Pydantic schemas
- cache.py: Pre-fetch caching
- agents.py: Agent factory functions
- hooks.py: Validation hooks
- workflow.py: Workflow factory
- runner.py: Workflow execution

This file maintains backward compatibility by re-exporting from new modules
and keeping legacy code that hasn't been migrated yet.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import structlog
import os
import json
import time
import uuid

from agno.agent import Agent
from agno.workflow import Workflow
from agno.models.litellm import LiteLLM
from pydantic import BaseModel, Field, field_validator, ValidationError

from control_plane_api.app.models.task_planning import (
    TaskPlanResponse,
    TaskPlanRequest,
    AnalysisAndSelectionOutput,
)
from control_plane_api.app.lib.planning_tools.agno_toolkit import PlanningToolkit

# NOTE: New modular alternatives are available in:
# - .cache: get_cached_prefetch, set_cached_prefetch, PrefetchCache
# - .models: TaskAnalysisOutput, ResourceDiscoveryOutput, FastSelectionOutput
# - .agents: create_analysis_and_selection_agent, create_plan_generation_agent
# - .hooks: validate_step1_output, validate_step2_output
# - .workflow: create_planning_workflow (refactored version)
# - .runner: run_workflow_stream, execute_step
# Import from __init__ for the new API

logger = structlog.get_logger()


# ============================================================================
# In-Memory Cache for Pre-fetched Resources (5-minute TTL)
# NOTE: Now using cache.py module - these are kept for backward compatibility
# ============================================================================
_PREFETCH_CACHE: Dict[str, Dict[str, Any]] = {}
_PREFETCH_CACHE_TTL = 300  # 5 minutes


def get_cached_prefetch(organization_id: str) -> Optional[Dict[str, Any]]:
    """Get cached pre-fetched data for an organization if still valid."""
    cache_key = f"prefetch_{organization_id}"
    cached = _PREFETCH_CACHE.get(cache_key)
    if cached and time.time() - cached.get("timestamp", 0) < _PREFETCH_CACHE_TTL:
        logger.info("prefetch_cache_hit", organization_id=organization_id[:8])
        return cached.get("data")
    return None


def set_cached_prefetch(organization_id: str, data: Dict[str, Any]) -> None:
    """Cache pre-fetched data for an organization."""
    cache_key = f"prefetch_{organization_id}"
    _PREFETCH_CACHE[cache_key] = {
        "timestamp": time.time(),
        "data": data
    }
    logger.info("prefetch_cache_set", organization_id=organization_id[:8])


# ============================================================================
# Step Output Models - Define what each step produces
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
        # This will be checked after both fields are set
        return v

    @field_validator('recommended_entity_id')
    @classmethod
    def validate_entity_id_exists(cls, v, info):
        """CRITICAL: Validate that recommended ID is a UUID and exists in discovered lists"""
        # Allow None recommendations (edge case: no suitable resources found)
        if v is None:
            return v

        # CRITICAL: Validate UUID format first
        try:
            uuid.UUID(v)
        except (ValueError, AttributeError, TypeError):
            raise ValueError(
                f"recommended_entity_id '{v}' is NOT a valid UUID! "
                f"It appears to be a name instead of an ID. "
                f"You MUST use the 'id' field (UUID) from tool results, NOT the 'name' field! "
                f"Common mistake: using agent['name'] instead of agent['id']. "
                f"UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (36 characters with dashes)"
            )

        discovered_agents = info.data.get('discovered_agents', [])
        discovered_teams = info.data.get('discovered_teams', [])
        entity_type = info.data.get('recommended_entity_type', '')

        # Check if at least one discovery was made
        if not discovered_agents and not discovered_teams:
            raise ValueError(
                "Cannot recommend an entity when no agents or teams were discovered. "
                "You MUST call list_agents() or list_teams() or search tools first!"
            )

        # Validate ID exists in the appropriate list
        if entity_type == 'agent':
            agent_ids = [str(a.get('id', '')) for a in discovered_agents if a.get('id')]
            if v not in agent_ids:
                raise ValueError(
                    f"Recommended agent_id '{v}' does not exist in discovered_agents. "
                    f"Available agent IDs: {agent_ids}. "
                    f"You MUST choose from the agents returned by tools, not make up an ID!"
                )
        elif entity_type == 'team':
            team_ids = [str(t.get('id', '')) for t in discovered_teams if t.get('id')]
            if v not in team_ids:
                raise ValueError(
                    f"Recommended team_id '{v}' does not exist in discovered_teams. "
                    f"Available team IDs: {team_ids}. "
                    f"You MUST choose from the teams returned by tools, not make up an ID!"
                )
        else:
            raise ValueError(
                f"recommended_entity_type must be 'agent' or 'team', got '{entity_type}'"
            )

        return v

    @field_validator('recommended_entity_name')
    @classmethod
    def validate_entity_name_matches(cls, v, info):
        """Validate that recommended name matches the entity from discovered lists"""
        # Allow None recommendations (edge case: no suitable resources found)
        if v is None:
            return v

        discovered_agents = info.data.get('discovered_agents', [])
        discovered_teams = info.data.get('discovered_teams', [])
        entity_type = info.data.get('recommended_entity_type', '')
        entity_id = info.data.get('recommended_entity_id', '')

        # Find the entity and verify name matches
        if entity_type == 'agent':
            for agent in discovered_agents:
                if str(agent.get('id')) == entity_id:
                    actual_name = agent.get('name', '')
                    if v != actual_name:
                        raise ValueError(
                            f"Recommended name '{v}' does not match actual agent name '{actual_name}'. "
                            f"You MUST use the exact name from tool results!"
                        )
                    break
        elif entity_type == 'team':
            for team in discovered_teams:
                if str(team.get('id')) == entity_id:
                    actual_name = team.get('name', '')
                    if v != actual_name:
                        raise ValueError(
                            f"Recommended name '{v}' does not match actual team name '{actual_name}'. "
                            f"You MUST use the exact name from tool results!"
                        )
                    break

        return v

    @field_validator('recommended_environment_id')
    @classmethod
    def validate_environment_id_exists(cls, v, info):
        """CRITICAL: Validate that recommended environment ID exists in discovered list"""
        if v is None:
            return v  # Optional field

        discovered_environments = info.data.get('discovered_environments', [])

        if not discovered_environments:
            raise ValueError(
                "Cannot recommend an environment when no environments were discovered. "
                "You MUST call list_environments() tool first!"
            )

        env_ids = [str(e.get('id', '')) for e in discovered_environments if e.get('id')]
        if v not in env_ids:
            raise ValueError(
                f"CRITICAL: recommended_environment_id '{v}' does NOT exist in discovered_environments! "
                f"Available environment IDs (UUIDs): {env_ids}. "
                f"You MUST use an actual UUID from the list_environments() tool result, NOT a name! "
                f"This is a hallucination - copy the 'id' field EXACTLY from the tool response!"
            )

        return v

    @field_validator('recommended_environment_name')
    @classmethod
    def validate_environment_name_matches(cls, v, info):
        """Validate that recommended environment name matches the ID from discovered list"""
        if v is None:
            return v  # Optional field

        discovered_environments = info.data.get('discovered_environments', [])
        environment_id = info.data.get('recommended_environment_id', '')

        # Find the environment and verify name matches
        for env in discovered_environments:
            if str(env.get('id')) == environment_id:
                actual_name = env.get('name', '')
                if v != actual_name:
                    raise ValueError(
                        f"Recommended environment name '{v}' does not match actual name '{actual_name}' for ID {environment_id}. "
                        f"You MUST use the exact name from list_environments() tool results!"
                    )
                break

        return v

    @field_validator('recommended_worker_queue_id')
    @classmethod
    def validate_worker_queue_id_exists(cls, v, info):
        """CRITICAL: Validate that recommended worker queue ID exists in discovered list"""
        if v is None:
            return v  # Optional field

        discovered_worker_queues = info.data.get('discovered_worker_queues', [])

        if not discovered_worker_queues:
            raise ValueError(
                "Cannot recommend a worker queue when no queues were discovered. "
                "You MUST call list_worker_queues() tool first!"
            )

        queue_ids = [str(q.get('id', '')) for q in discovered_worker_queues if q.get('id')]
        if v not in queue_ids:
            raise ValueError(
                f"CRITICAL: recommended_worker_queue_id '{v}' does NOT exist in discovered_worker_queues! "
                f"Available worker queue IDs (UUIDs): {queue_ids}. "
                f"You MUST use an actual UUID from the list_worker_queues() tool result, NOT a name! "
                f"This is a hallucination - copy the 'id' field EXACTLY from the tool response!"
            )

        return v

    @field_validator('recommended_worker_queue_name')
    @classmethod
    def validate_worker_queue_name_matches(cls, v, info):
        """Validate that recommended worker queue name matches the ID from discovered list"""
        if v is None:
            return v  # Optional field

        discovered_worker_queues = info.data.get('discovered_worker_queues', [])
        queue_id = info.data.get('recommended_worker_queue_id', '')

        # Find the queue and verify name matches
        for queue in discovered_worker_queues:
            if str(queue.get('id')) == queue_id:
                actual_name = queue.get('name', '')
                if v != actual_name:
                    raise ValueError(
                        f"Recommended worker queue name '{v}' does not match actual name '{actual_name}' for ID {queue_id}. "
                        f"You MUST use the exact name from list_worker_queues() tool results!"
                    )
                break

        return v


def _validate_resource_discovery(output: ResourceDiscoveryOutput) -> None:
    """
    Explicitly validate ResourceDiscoveryOutput to catch issues that Agno might suppress.

    This is a safety net in case Pydantic validation is bypassed or silently caught
    by the Agno framework. Raises ValueError with detailed diagnostics.

    Args:
        output: ResourceDiscoveryOutput to validate

    Raises:
        ValueError: If validation fails with detailed error message
    """
    # Check discovered lists are populated
    if not output.discovered_agents and not output.discovered_teams:
        raise ValueError(
            "ResourceDiscoveryOutput validation failed: "
            "Both discovered_agents and discovered_teams are empty. "
            "You MUST call list_agents() or list_teams() tools and populate these fields!"
        )

    # If recommendation is None, that's OK (edge case: no suitable resources found)
    if output.recommended_entity_id is None:
        logger.warning("no_entity_recommended",
                      discovered_agents=len(output.discovered_agents),
                      discovered_teams=len(output.discovered_teams))
        return

    # CRITICAL: Validate that entity_id is a valid UUID format
    try:
        uuid.UUID(output.recommended_entity_id)
        logger.info(
            "entity_id_uuid_validation_passed",
            entity_id=output.recommended_entity_id,
            entity_type=output.recommended_entity_type
        )
    except (ValueError, AttributeError) as e:
        # entity_id is not a valid UUID - it might be a name instead!
        logger.error(
            "entity_id_not_uuid",
            entity_id=output.recommended_entity_id,
            entity_type=output.recommended_entity_type,
            error=str(e)
        )

        # Try to fix it by finding the matching entity and using its ID
        if output.recommended_entity_type == 'agent':
            # Look for an agent with this name
            matching_agent = next(
                (a for a in output.discovered_agents
                 if a.get('name') == output.recommended_entity_id),
                None
            )
            if matching_agent:
                correct_id = matching_agent.get('id')
                logger.warning(
                    "entity_id_was_name_fixed",
                    provided_name=output.recommended_entity_id,
                    correct_uuid=correct_id,
                    entity_type='agent'
                )
                # Fix the output by replacing name with UUID
                output.recommended_entity_id = str(correct_id)
                output.recommended_entity_name = matching_agent.get('name')
            else:
                raise ValueError(
                    f"CRITICAL UUID VALIDATION ERROR: recommended_entity_id '{output.recommended_entity_id}' "
                    f"is NOT a valid UUID! It appears to be an agent name, but no matching agent was found. "
                    f"You MUST use the 'id' field (UUID) from tool results, NOT the 'name' field! "
                    f"Available agents: {[a.get('name') for a in output.discovered_agents]}"
                )
        elif output.recommended_entity_type == 'team':
            # Look for a team with this name
            matching_team = next(
                (t for t in output.discovered_teams
                 if t.get('name') == output.recommended_entity_id),
                None
            )
            if matching_team:
                correct_id = matching_team.get('id')
                logger.warning(
                    "entity_id_was_name_fixed",
                    provided_name=output.recommended_entity_id,
                    correct_uuid=correct_id,
                    entity_type='team'
                )
                # Fix the output by replacing name with UUID
                output.recommended_entity_id = str(correct_id)
                output.recommended_entity_name = matching_team.get('name')
            else:
                raise ValueError(
                    f"CRITICAL UUID VALIDATION ERROR: recommended_entity_id '{output.recommended_entity_id}' "
                    f"is NOT a valid UUID! It appears to be a team name, but no matching team was found. "
                    f"You MUST use the 'id' field (UUID) from tool results, NOT the 'name' field! "
                    f"Available teams: {[t.get('name') for t in output.discovered_teams]}"
                )

    # Validate ID exists in appropriate list
    if output.recommended_entity_type == 'agent':
        agent_ids = [str(a.get('id', '')) for a in output.discovered_agents if a.get('id')]
        if output.recommended_entity_id not in agent_ids:
            raise ValueError(
                f"CRITICAL VALIDATION ERROR: recommended_entity_id '{output.recommended_entity_id}' "
                f"does NOT exist in discovered_agents list! "
                f"Available agent IDs: {agent_ids}. "
                f"This is a hallucination - you MUST use an ID from the tool results!"
            )
    elif output.recommended_entity_type == 'team':
        team_ids = [str(t.get('id', '')) for t in output.discovered_teams if t.get('id')]
        if output.recommended_entity_id not in team_ids:
            raise ValueError(
                f"CRITICAL VALIDATION ERROR: recommended_entity_id '{output.recommended_entity_id}' "
                f"does NOT exist in discovered_teams list! "
                f"Available team IDs: {team_ids}. "
                f"This is a hallucination - you MUST use an ID from the tool results!"
            )

    # Validate name matches
    if output.recommended_entity_type == 'agent':
        for agent in output.discovered_agents:
            if str(agent.get('id')) == output.recommended_entity_id:
                actual_name = agent.get('name', '')
                if output.recommended_entity_name != actual_name:
                    raise ValueError(
                        f"CRITICAL VALIDATION ERROR: recommended_entity_name '{output.recommended_entity_name}' "
                        f"does NOT match actual agent name '{actual_name}' for ID {output.recommended_entity_id}!"
                    )
                break
    elif output.recommended_entity_type == 'team':
        for team in output.discovered_teams:
            if str(team.get('id')) == output.recommended_entity_id:
                actual_name = team.get('name', '')
                if output.recommended_entity_name != actual_name:
                    raise ValueError(
                        f"CRITICAL VALIDATION ERROR: recommended_entity_name '{output.recommended_entity_name}' "
                        f"does NOT match actual team name '{actual_name}' for ID {output.recommended_entity_id}!"
                    )
                break

    logger.info(
        "resource_discovery_validation_passed",
        entity_type=output.recommended_entity_type,
        entity_id=output.recommended_entity_id[:12] if output.recommended_entity_id else None,
        entity_name=output.recommended_entity_name,
        validation_checks_passed=["uuid_format", "id_exists", "name_matches"]
    )


class FastSelectionOutput(BaseModel):
    """
    Fast selection output for --local mode - minimal fields for quick execution.
    Reuses the same validators as ResourceDiscoveryOutput to prevent hallucination.

    This schema is used by the 1-step fast workflow for CLI --local mode.
    """

    discovered_agents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of agents found using list_agents() tool (optional if outer context provided)"
    )
    discovered_teams: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of teams found using list_teams() tool (optional if outer context provided)"
    )
    discovered_environments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of environments found using list_environments() tool"
    )
    discovered_worker_queues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of worker queues found using list_worker_queues() tool"
    )

    recommended_entity_type: str = Field(..., description="'agent' or 'team'")
    recommended_entity_id: str = Field(..., description="UUID of agent/team from discovered list")
    recommended_entity_name: str = Field(..., description="Name of agent/team from discovered list")

    # Agent runtime and model info (extracted from selected agent)
    selected_agent_runtime: Optional[str] = Field(None, description="Runtime of selected agent ('default' or 'claude_code') - prefer claude_code for complex tasks")
    selected_agent_model_id: Optional[str] = Field(None, description="Model ID of selected agent (e.g., 'claude-sonnet-4')")

    recommended_environment_id: Optional[str] = Field(None, description="UUID of environment from discovered list (optional - use outer context if available)")
    recommended_environment_name: Optional[str] = Field(None, description="Name of environment from discovered list (optional - use outer context if available)")

    recommended_worker_queue_id: Optional[str] = Field(None, description="UUID of worker queue from discovered list (optional)")
    recommended_worker_queue_name: Optional[str] = Field(None, description="Name of worker queue from discovered list (optional)")

    reasoning: str = Field(..., description="Brief 1-sentence explanation of selection")

    # Reuse the same validators from ResourceDiscoveryOutput to prevent hallucination!

    @field_validator('recommended_entity_id')
    @classmethod
    def validate_entity_id_exists(cls, v, info):
        """CRITICAL: Validate that recommended ID is a UUID and exists in discovered lists"""
        # CRITICAL: Validate UUID format first
        try:
            uuid.UUID(v)
        except (ValueError, AttributeError, TypeError):
            raise ValueError(
                f"recommended_entity_id '{v}' is NOT a valid UUID! "
                f"It appears to be a name instead of an ID. "
                f"You MUST use the 'id' field (UUID) from tool results or outer context, NOT the 'name' field! "
                f"Common mistake: using agent['name'] instead of agent['id']. "
                f"UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (36 characters with dashes)"
            )

        discovered_agents = info.data.get('discovered_agents', [])
        discovered_teams = info.data.get('discovered_teams', [])
        entity_type = info.data.get('recommended_entity_type', '')

        # Check if at least one discovery was made
        if not discovered_agents and not discovered_teams:
            raise ValueError(
                "Cannot recommend an entity when no agents or teams were discovered. "
                "You MUST call list_agents() or list_teams() or use outer context!"
            )

        # Validate ID exists in the appropriate list
        if entity_type == 'agent':
            agent_ids = [str(a.get('id', '')) for a in discovered_agents if a.get('id')]
            if v not in agent_ids:
                raise ValueError(
                    f"Recommended agent_id '{v}' does not exist in discovered_agents. "
                    f"Available agent IDs: {agent_ids}. "
                    f"You MUST choose from the agents returned by tools, not make up an ID!"
                )
        elif entity_type == 'team':
            team_ids = [str(t.get('id', '')) for t in discovered_teams if t.get('id')]
            if v not in team_ids:
                raise ValueError(
                    f"Recommended team_id '{v}' does not exist in discovered_teams. "
                    f"Available team IDs: {team_ids}. "
                    f"You MUST choose from the teams returned by tools, not make up an ID!"
                )
        else:
            raise ValueError(
                f"recommended_entity_type must be 'agent' or 'team', got '{entity_type}'"
            )

        return v

    @field_validator('recommended_entity_name')
    @classmethod
    def validate_entity_name_matches(cls, v, info):
        """Validate that recommended name matches the entity from discovered lists"""
        discovered_agents = info.data.get('discovered_agents', [])
        discovered_teams = info.data.get('discovered_teams', [])
        entity_type = info.data.get('recommended_entity_type', '')
        entity_id = info.data.get('recommended_entity_id', '')

        # Find the entity and verify name matches
        if entity_type == 'agent':
            for agent in discovered_agents:
                if str(agent.get('id')) == entity_id:
                    actual_name = agent.get('name', '')
                    if v != actual_name:
                        raise ValueError(
                            f"Recommended name '{v}' does not match actual agent name '{actual_name}'. "
                            f"You MUST use the exact name from tool results!"
                        )
                    break
        elif entity_type == 'team':
            for team in discovered_teams:
                if str(team.get('id')) == entity_id:
                    actual_name = team.get('name', '')
                    if v != actual_name:
                        raise ValueError(
                            f"Recommended name '{v}' does not match actual team name '{actual_name}'. "
                            f"You MUST use the exact name from tool results!"
                        )
                    break

        return v

    @field_validator('recommended_environment_id')
    @classmethod
    def validate_environment_id_exists(cls, v, info):
        """CRITICAL: Validate that recommended environment ID exists in discovered list"""
        if v is None:
            return v  # Optional field - allow None

        discovered_environments = info.data.get('discovered_environments', [])

        if not discovered_environments:
            raise ValueError(
                "Cannot recommend an environment when no environments were discovered. "
                "Either call list_environments() tool or use outer context environments!"
            )

        env_ids = [str(e.get('id', '')) for e in discovered_environments if e.get('id')]
        if v not in env_ids:
            raise ValueError(
                f"CRITICAL: recommended_environment_id '{v}' does NOT exist in discovered_environments! "
                f"Available environment IDs (UUIDs): {env_ids}. "
                f"You MUST use an actual UUID from the discovered list, NOT a name!"
            )

        return v

    @field_validator('recommended_environment_name')
    @classmethod
    def validate_environment_name_matches(cls, v, info):
        """Validate that recommended environment name matches the ID from discovered list"""
        if v is None:
            return v  # Optional field - allow None

        discovered_environments = info.data.get('discovered_environments', [])
        environment_id = info.data.get('recommended_environment_id', '')

        # Find the environment and verify name matches
        for env in discovered_environments:
            if str(env.get('id')) == environment_id:
                actual_name = env.get('name', '')
                if v != actual_name:
                    raise ValueError(
                        f"Recommended environment name '{v}' does not match actual name '{actual_name}' for ID {environment_id}. "
                        f"You MUST use the exact name from list_environments() tool results!"
                    )
                break

        return v

    @field_validator('recommended_worker_queue_id')
    @classmethod
    def validate_worker_queue_id_exists(cls, v, info):
        """CRITICAL: Validate that recommended worker queue ID exists in discovered list"""
        if v is None:
            return v  # Optional field

        discovered_worker_queues = info.data.get('discovered_worker_queues', [])

        if not discovered_worker_queues:
            raise ValueError(
                "Cannot recommend a worker queue when no queues were discovered. "
                "You MUST call list_worker_queues() tool first!"
            )

        queue_ids = [str(q.get('id', '')) for q in discovered_worker_queues if q.get('id')]
        if v not in queue_ids:
            raise ValueError(
                f"CRITICAL: recommended_worker_queue_id '{v}' does NOT exist in discovered_worker_queues! "
                f"Available worker queue IDs (UUIDs): {queue_ids}. "
                f"You MUST use an actual UUID from the list_worker_queues() tool result, NOT a name!"
            )

        return v

    @field_validator('recommended_worker_queue_name')
    @classmethod
    def validate_worker_queue_name_matches(cls, v, info):
        """Validate that recommended worker queue name matches the ID from discovered list"""
        if v is None:
            return v  # Optional field

        discovered_worker_queues = info.data.get('discovered_worker_queues', [])
        queue_id = info.data.get('recommended_worker_queue_id', '')

        # Find the queue and verify name matches
        for queue in discovered_worker_queues:
            if str(queue.get('id')) == queue_id:
                actual_name = queue.get('name', '')
                if v != actual_name:
                    raise ValueError(
                        f"Recommended worker queue name '{v}' does not match actual name '{actual_name}' for ID {queue_id}. "
                        f"You MUST use the exact name from list_worker_queues() tool results!"
                    )
                break

        return v


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
# Workflow Step Agents
# ============================================================================

def create_analysis_and_selection_agent(
    model: LiteLLM,
    planning_toolkit: 'PlanningToolkit',
    outer_context: Optional[Dict[str, Any]] = None
) -> Agent:
    """
    NEW Step 1: Task Analysis & Resource Selection (2-Step Workflow)

    Combines old Step 1 (Task Analyzer) + Step 2 (Resource Discoverer)
    into single efficient agent for the simplified 2-step workflow.

    Pre-fetched data (top 20 agents/teams/envs) provided in outer_context.
    Tools available if agent needs to search for more specific matches.

    This function replaces:
    - create_task_analysis_agent() (old Step 1)
    - create_resource_discovery_agent() (old Step 2)
    """
    from agno.tools.function import Function
    import json
    from control_plane_api.app.lib.planning_tools.agno_toolkit import PlanningToolkit

    # Provide hybrid approach: pre-fetched data + tool access
    toolkit_tools = []

    # Add synthetic tools for pre-fetched data (instant access)
    if outer_context:
        if outer_context.get("agents"):
            def get_top_agents() -> str:
                """Get top 20 pre-fetched agents (instant, no API call).
                Use this first before calling search tools."""
                return json.dumps({
                    "success": True,
                    "data": {
                        "agents": outer_context["agents"],
                        "count": len(outer_context["agents"]),
                        "note": "Top 20 agents. Use search_agents_by_capability() if you need more."
                    }
                }, indent=2)
            toolkit_tools.append(Function.from_callable(get_top_agents))

        if outer_context.get("teams"):
            def get_top_teams() -> str:
                """Get top 20 pre-fetched teams (instant, no API call).
                Use this first before calling search tools."""
                return json.dumps({
                    "success": True,
                    "data": {
                        "teams": outer_context["teams"],
                        "count": len(outer_context["teams"]),
                        "note": "Top 20 teams. Use search_teams_by_capability() if you need more."
                    }
                }, indent=2)
            toolkit_tools.append(Function.from_callable(get_top_teams))

        if outer_context.get("environments"):
            def get_top_environments() -> str:
                """Get top 20 pre-fetched environments (instant, no API call)."""
                return json.dumps({
                    "success": True,
                    "data": {
                        "environments": outer_context["environments"],
                        "count": len(outer_context["environments"]),
                        "note": "Top 20 environments."
                    }
                }, indent=2)
            toolkit_tools.append(Function.from_callable(get_top_environments))

        if outer_context.get("worker_queues"):
            def get_top_worker_queues() -> str:
                """Get top 20 pre-fetched worker queues (instant, no API call)."""
                return json.dumps({
                    "success": True,
                    "data": {
                        "worker_queues": outer_context["worker_queues"],
                        "count": len(outer_context["worker_queues"]),
                        "note": "Top 20 worker queues."
                    }
                }, indent=2)
            toolkit_tools.append(Function.from_callable(get_top_worker_queues))

    # Also add real search tools for when top 20 isn't enough
    if planning_toolkit and hasattr(planning_toolkit, 'functions'):
        if "search_agents_by_capability" in planning_toolkit.functions:
            toolkit_tools.append(planning_toolkit.functions["search_agents_by_capability"])
        if "search_teams_by_capability" in planning_toolkit.functions:
            toolkit_tools.append(planning_toolkit.functions["search_teams_by_capability"])
        if "get_agent_details" in planning_toolkit.functions:
            toolkit_tools.append(planning_toolkit.functions["get_agent_details"])
        if "get_team_details" in planning_toolkit.functions:
            toolkit_tools.append(planning_toolkit.functions["get_team_details"])
        # PHASE 1 IMPROVEMENT: Add fallback tool to ensure agent never returns None
        if "get_fallback_agent" in planning_toolkit.functions:
            toolkit_tools.append(planning_toolkit.functions["get_fallback_agent"])

    # Extract preferred_runtime from outer_context if provided
    preferred_runtime = None
    if outer_context:
        preferred_runtime = outer_context.get("preferred_runtime")

    # Build runtime preference instruction
    if preferred_runtime:
        runtime_instruction = f"MANDATORY: Select agents with runtime='{preferred_runtime}' (user override)"
    else:
        runtime_instruction = "MANDATORY: Select agents with runtime='claude_code' OVER 'default' when both have the capability. claude_code agents are more capable."

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
            "FALLBACK: Use get_fallback_agent() if no match",
            "",
            "OUTPUT: Pure JSON only, start with {",
        ],
        markdown=False,
    )


async def create_analysis_and_selection_agent_claude_code(
    planning_toolkit: 'PlanningToolkit',
    model_name: str = "claude-sonnet-4",
    outer_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Step 1 using Claude Code SDK: Task Analysis & Resource Selection

    Uses Claude Code SDK instead of Agno for more intelligent tool usage and better
    instruction following. Claude Code has proven better at complex tool orchestration.

    Returns the AnalysisAndSelectionOutput as a dictionary.
    """
    try:
        from claude_agent_sdk import ClaudeSDKClient
        from claude_agent_sdk.types import ClaudeAgentOptions
    except ImportError as e:
        logger.error("claude_sdk_not_available", error=str(e))
        raise ValueError(f"Claude Code SDK not available: {e}")

    # Build system prompt with clear instructions
    system_prompt = """You are an intelligent agent selection system. Your goal is to analyze tasks and select the BEST agent or team to execute them.

## Your Process:

1. **Analyze the task**:
   - Identify required capabilities (e.g., kubernetes, aws, python)
   - Estimate complexity (story points 1-21)
   - Determine if single agent or team needed

2. **Discover available resources**:
   - Use search_agents_by_capability(skill) to find agents
   - Use search_teams_by_capability(skill) to find teams
   - Use get_fallback_agent() if no matches found

3. **Select the best match**:
   - NEVER return None for selected_entity_id
   - ALWAYS use ACTUAL UUIDs from tool results
   - NEVER invent or hallucinate IDs
   - If no perfect match: use get_fallback_agent()

4. **Return structured output**:
   You MUST return a JSON object with these fields:
   {
     "task_summary": "Brief summary",
     "required_capabilities": ["skill1", "skill2"],
     "task_type": "deployment|investigation|automation",
     "complexity_estimate": "simple|moderate|complex",
     "story_points_estimate": 1-21,
     "needs_multi_agent": false,
     "selected_entity_type": "agent|team",
     "selected_entity_id": "ACTUAL-UUID-FROM-TOOL-RESULT",
     "selected_entity_name": "Name from tool result",
     "selection_reasoning": "Why you chose this agent/team",
     "selected_agent_runtime": "claude_code or default - from agent's runtime field",
     "selected_agent_model_id": "from agent's model_id field",
     "selected_environment_id": null,
     "selected_environment_name": null,
     "selected_worker_queue_id": null,
     "selected_worker_queue_name": null,
     "estimated_cost_usd": 0.05,
     "estimated_time_hours": 0.5,
     "discovered_agents": [],
     "discovered_teams": []
   }

## RUNTIME SELECTION PREFERENCE:
- **PREFER 'claude_code' runtime** - more capable for complex tasks
- For COMPLEX tasks (8+ story points): STRONGLY prefer agents with runtime='claude_code'
- For MODERATE tasks (5-7 points): Prefer claude_code if available with matching capabilities
- When multiple agents match, prefer claude_code runtime over default

## CRITICAL RULES:

- Use get_fallback_agent() if searches return empty
- Copy EXACT UUID from tool results (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
- NEVER invent IDs like 'fallback-general-agent' or 'agent-001'
- selected_entity_id MUST be a valid UUID from tool results
- ALWAYS include selected_agent_runtime and selected_agent_model_id from the chosen agent"""

    # Build MCP server from planning toolkit
    mcp_servers = {}
    if planning_toolkit:
        # Convert planning toolkit to simple MCP server configuration
        tools_list = []
        for tool_name in ['search_agents_by_capability', 'search_teams_by_capability',
                          'get_agent_details', 'get_team_details', 'get_fallback_agent']:
            if tool_name in planning_toolkit.functions:
                tool_func = planning_toolkit.functions[tool_name]
                tools_list.append({
                    "name": tool_name,
                    "function": tool_func
                })

        logger.info("claude_code_step1_tools_prepared", tool_count=len(tools_list))

    # Create Claude options with tools as native Python functions
    # For simplicity, we'll use tools directly instead of MCP servers
    from agno.tools.function import Function

    # Get tools from planning toolkit
    toolkit_tools = []
    if planning_toolkit:
        for tool_name in ['search_agents_by_capability', 'search_teams_by_capability',
                          'get_agent_details', 'get_team_details', 'get_fallback_agent']:
            if tool_name in planning_toolkit.functions:
                toolkit_tools.append(planning_toolkit.functions[tool_name])

    logger.info("claude_code_step1_starting",
                tool_count=len(toolkit_tools),
                model=model_name)

    # For now, return None to indicate Claude Code is not yet fully implemented
    # We'll continue using Agno until Claude Code integration is complete
    return None


def create_task_analysis_agent(model: LiteLLM) -> Agent:
    """
    Step 1: Task Analysis Agent

    Analyzes the task description and identifies:
    - Required capabilities and skills
    - Task type and complexity
    - Whether multi-agent coordination is needed
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
            "- 5-8 points: Medium tasks (deployments, multi-step operations, data processing)",
            "- 13-21 points: Complex tasks (multi-system integrations, migrations, deep analysis)",
            "",
            "**Multi-Agent Assessment:**",
            "- Single agent: Task has clear single domain (just AWS, just Kubernetes, etc.)",
            "- Team needed: Task spans multiple domains (AWS + Kubernetes, monitoring + alerting, etc.)",
            "",
            "**Output:**",
            "Provide a clear analysis with reasoning so the next step knows what to search for.",
        ],
        markdown=False,
    )


def create_resource_discovery_agent(
    model: LiteLLM,
    db: Session,
    organization_id: str,
    api_token: str,
    outer_context: Optional[Dict[str, Any]] = None
) -> Agent:
    """
    Step 2: Resource Discovery Agent

    Uses planning toolkit to find agents/teams with required capabilities.
    Takes output from Task Analysis step.

    If outer_context is provided (from CLI), uses pre-filtered agents/teams instead of discovery.
    This supports --local mode and explicit agent selection.

    CRITICAL: Tools use direct DB access (no HTTP self-calls) for performance.
    Context graph still uses HTTP to external service (correct pattern).
    """
    # Create planning toolkit with DB access (internal services, no HTTP)
    planning_toolkit = PlanningToolkit(
        db=db,
        organization_id=organization_id,
        api_token=api_token
    )

    # Extract individual Function objects from toolkit (CRITICAL!)
    # This is how Agno expects tools - as a list of Function objects
    toolkit_tools = list(planning_toolkit.functions.values()) if hasattr(planning_toolkit, 'functions') else []

    # Check if outer context is provided with pre-filtered resources
    has_outer_agents = outer_context and outer_context.get("agents")
    has_outer_teams = outer_context and outer_context.get("teams")
    has_outer_context = has_outer_agents or has_outer_teams

    # Optimization: Skip environment/queue tools when in local mode with outer context
    # Local mode will create ephemeral queue automatically, so discovery is unnecessary
    if has_outer_context:
        toolkit_tools = [
            t for t in toolkit_tools
            if t.name not in ["list_environments", "list_worker_queues"]
        ]
        logger.info("conditional_tools_filtered", removed=["list_environments", "list_worker_queues"])

    logger.info(
        "resource_discovery_agent_created",
        tool_count=len(toolkit_tools),
        has_outer_context=has_outer_context,
        outer_agents_count=len(outer_context.get("agents", [])) if outer_context else 0,
        outer_teams_count=len(outer_context.get("teams", [])) if outer_context else 0,
        organization_id=organization_id[:8]
    )

    # Build instructions based on whether outer context is provided
    base_instructions = [
        "You find the best agents or teams for a task and select from available options.",
        "",
        "🚨 CRITICAL VALIDATION 🚨",
        "Your output is STRICTLY VALIDATED:",
        "1. recommended_entity_id MUST be a UUID (36-char format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)",
        "2. recommended_entity_id MUST come from the 'id' field (NOT the 'name' field!) of discovered entities",
        "3. recommended_entity_name MUST come from the 'name' field and exactly match the entity's name",
        "4. discovered_agents/discovered_teams MUST contain actual data from tool calls",
        "5. If you use 'name' for entity_id, or hallucinate ANY ID/name, your response will be REJECTED",
        "",
        "⚠️  COMMON MISTAKE: Using agent.name for entity_id instead of agent.id",
        "✅  CORRECT: entity_id = agent['id'] (UUID), entity_name = agent['name']",
        "❌  WRONG: entity_id = agent['name'] (this will fail UUID validation!)",
        "",
    ]

    # Add mode-specific instructions
    if has_outer_context:
        # Selection Mode: User provided pre-filtered agents/teams
        workflow_instructions = [
            "🎯 SELECTION MODE: The user has provided a PRE-FILTERED list of agents/teams.",
            "",
            "**CRITICAL: DO NOT call list_agents() or list_teams() tools!**",
            "The user has already done the filtering. You MUST select from this provided list:",
            "",
        ]

        # Format provided agents
        if has_outer_agents:
            workflow_instructions.append("**Available Agents (provided by user):**")
            for agent in outer_context.get("agents", []):
                workflow_instructions.append(
                    f"  - ID: {agent.get('id')}, Name: {agent.get('name')}, "
                    f"Capabilities: {agent.get('capabilities', [])}, Status: {agent.get('status', 'active')}"
                )
            workflow_instructions.append("")

        # Format provided teams
        if has_outer_teams:
            workflow_instructions.append("**Available Teams (provided by user):**")
            for team in outer_context.get("teams", []):
                workflow_instructions.append(
                    f"  - ID: {team.get('id')}, Name: {team.get('name')}, "
                    f"Agent Count: {team.get('agent_count', 0)}, Status: {team.get('status', 'active')}"
                )
            workflow_instructions.append("")

        workflow_instructions.extend([
            "**YOUR WORKFLOW:**",
            "1. Set discovered_agents = (list of agents from above - use the exact objects as shown)",
            "2. Set discovered_teams = (list of teams from above - use the exact objects as shown)",
            "3. SELECT the best match based on task requirements and capabilities",
            "4. Set recommended_entity_id = selected_entity['id']  ← MUST be UUID from 'id' field",
            "5. Set recommended_entity_name = selected_entity['name']  ← From 'name' field",
            "6. DO NOT call list_agents() or list_teams() - everything is already provided!",
            "7. Still call list_environments() and list_worker_queues() to select environment and queue",
            "",
        ])
    else:
        # Discovery Mode: Call tools to discover agents/teams
        workflow_instructions = [
            "**WORKFLOW (YOU MUST FOLLOW THIS EXACTLY):**",
            "",
            "Step 1: CALL TOOLS to discover agents/teams",
            "   - For single-domain tasks: call list_agents() or search_agents_by_capability('skill_name')",
            "   - For multi-domain tasks: call list_teams() or search_teams_by_capability('skill_name')",
            "   - Tools return JSON with 'data' field containing agents/teams",
            "   - Each entity has BOTH: 'id' (UUID string) AND 'name' (display name)",
            "",
            "Step 2: PARSE tool results",
            "   - Extract the 'agents' or 'teams' array from tool response data",
            "   - Each agent/team object has: {'id': '<UUID>', 'name': '<name>', 'description': '...', ...}",
            "   - Store complete objects in discovered_agents or discovered_teams field",
            "",
            "Step 3: SELECT best match",
            "   - Compare agents/teams from tool results based on capabilities",
            "   - Once you pick an entity, extract BOTH fields:",
            "     • recommended_entity_id = selected_entity['id']  ← UUID from 'id' field",
            "     • recommended_entity_name = selected_entity['name']  ← Name from 'name' field",
            "   - ⚠️  DO NOT use selected_entity['name'] for entity_id!",
            "",
            "Step 4: VALIDATE before returning",
            "   - Double-check: Is recommended_entity_id a UUID? (36 chars with dashes)",
            "   - Double-check: Is the recommended_entity_id in your discovered list's 'id' fields?",
            "   - Double-check: Does recommended_entity_name exactly match the entity's 'name' field?",
            "   - If not, GO BACK and fix it using actual tool data",
            "",
        ]

    # Conditional instructions for environment and worker queue selection
    # Only include when NOT in local mode (outer_context present means local/CLI execution)
    if has_outer_context:
        # Local mode: ephemeral queue will be created automatically, skip env/queue discovery
        environment_queue_instructions = []
    else:
        # Production mode: need to discover and select environment/queue
        environment_queue_instructions = [
            "**Environment & Worker Queue Selection:**",
            "Call list_environments() and list_worker_queues() to discover options.",
            "Select environment (active, suitable for task) and queue (active, has workers).",
            "Use EXACT UUIDs (36-char format) and names from tool results for recommended IDs/names.",
            "Store full lists in discovered_environments and discovered_worker_queues.",
            "",
        ]

    # Validation reminders (always needed)
    validation_reminders = [
        "",
        "🚨 AUTOMATED VALIDATION (2 retries if failed):",
        "",
        "Your response is validated automatically:",
        "1. discovered lists must have data (call tools first)",
        "2. recommended_entity_id must be a valid UUID format (not a name!)",
        "3. recommended_entity_id must come from the 'id' field of discovered entities",
        "4. recommended_entity_name must come from the 'name' field and match exactly",
        "5. All IDs must be UUIDs from tool results (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx format)",
        "",
        "✅ SUCCESS: Use EXACT field mapping from tool results",
        "   Example: Tool returns {\"id\": \"550e8400-e29b-41d4-a716-446655440000\", \"name\": \"DevOps Agent\"}",
        "   → CORRECT: recommended_entity_id = \"550e8400-e29b-41d4-a716-446655440000\" (from 'id')",
        "   →          recommended_entity_name = \"DevOps Agent\" (from 'name')",
        "",
        "❌ FAILURE EXAMPLES:",
        "   • Using agent['name'] for entity_id → UUID validation will fail!",
        "   • Making up IDs/names not from tool results → existence check will fail!",
        "   • Typos in names → name matching validation will fail!",
        "",
        "If validation fails, you get error message and ONE MORE CHANCE to fix using exact tool data.",
        "After 2 failures, workflow terminates.",
        "",
    ]

    # Combine all instructions
    final_instructions = base_instructions + workflow_instructions + environment_queue_instructions + validation_reminders

    return Agent(
        name="Resource Discoverer",
        role="Expert at finding the right agents and teams for tasks",
        model=model,
        output_schema=ResourceDiscoveryOutput,
        tools=toolkit_tools,  # Pass individual Function objects from toolkit
        instructions=final_instructions,
        markdown=False,
    )


def create_cost_estimation_agent(model: LiteLLM) -> Agent:
    """
    Step 3: Cost Estimation Agent

    Calculates time and cost estimates based on task analysis and selected resources.
    """
    return Agent(
        name="Cost Estimator",
        role="Expert at estimating time and cost for AI agent tasks",
        model=model,
        output_schema=CostEstimationOutput,
        instructions=[
            "You calculate realistic time and cost estimates for AI agent execution.",
            "",
            "**Your Input:**",
            "- Task analysis with complexity and capabilities",
            "- Selected agent/team details",
            "",
            "**Pricing Reference:**",
            "- Claude Sonnet 4: $0.003/1K input, $0.015/1K output tokens",
            "- Claude Haiku: $0.00025/1K input, $0.00125/1K output tokens",
            "- GPT-4o: $0.0025/1K input, $0.01/1K output tokens",
            "- GPT-4o Mini: $0.00015/1K input, $0.0006/1K output tokens",
            "- Tool calls: $0.0001 - $0.001 per call",
            "- Worker runtime: $0.10/hour",
            "",
            "**Token Estimation Guidelines:**",
            "- Simple tasks (1-3 points): 2-5K input, 1-2K output tokens",
            "- Medium tasks (5-8 points): 5-10K input, 2-5K output tokens",
            "- Complex tasks (13-21 points): 10-20K input, 5-10K output tokens",
            "",
            "**Time Estimation Guidelines:**",
            "- Simple tasks: 0.1 - 0.5 hours",
            "- Medium tasks: 0.5 - 2 hours",
            "- Complex tasks: 2 - 8 hours",
            "",
            "**Savings Calculation:**",
            "- Manual cost = time_hours × hourly_rate (use $100-150/hr for senior engineers)",
            "- AI cost = LLM + tools + runtime",
            "- Savings = manual_cost - ai_cost",
            "",
            "**Output:**",
            "Provide detailed cost breakdown with reasoning for your estimates.",
        ],
        markdown=False,
    )


def create_plan_generation_agent(model: LiteLLM) -> Agent:
    """
    NEW Step 2: Structured Plan Generation (2-Step Workflow)
    Generates TaskPlanResponse from Step 1 output using Agno's output_schema.
    Relies on the Pydantic model's JSON schema for field requirements.
    """
    return Agent(
        name="Plan Generator",
        role="Generate structured execution plan",
        model=model,
        output_schema=TaskPlanResponse,
        instructions=[
            "Generate a complete TaskPlanResponse based on Step 1 analysis.",
            "",
            "Use Step 1 output for: entity_id, entity_name, entity_type, runtime, model_id, cost/time estimates.",
            "",
            "IMPORTANT: team_breakdown[].tasks MUST be an empty array: tasks: []",
            "Fill ALL required fields including: estimated_time_hours in team_breakdown, without_kubiya_resources array in realized_savings.",
        ],
        markdown=False,
    )


# ============================================================================
# Workflow Factory
# ============================================================================

def create_planning_workflow(
    db: Session,
    organization_id: str,
    api_token: str,
    quick_mode: bool = False,
    outer_context: Optional[Dict[str, Any]] = None
) -> Workflow:
    """
    Create the task planning workflow with 4 steps.

    NOTE: For fast planning (--local mode), use create_fast_planning_workflow() instead.
    This function always creates the full 4-step workflow regardless of quick_mode.

    Args:
        db: Database session for internal service access
        organization_id: Organization ID for resource filtering (REQUIRED)
        api_token: Org-scoped API token for context graph access (REQUIRED)
        quick_mode: DEPRECATED - no longer used, kept for backwards compatibility
        outer_context: Optional pre-filtered context from CLI (agents, teams, etc.)

    Returns:
        Configured Workflow instance with 4 steps
    """
    if not organization_id:
        raise ValueError("organization_id is required for planning workflow")

    if not api_token:
        raise ValueError("api_token is required for planning workflow")

    # Get LiteLLM configuration
    litellm_api_url = (
        os.getenv("LITELLM_API_URL") or
        os.getenv("LITELLM_API_BASE") or
        "https://llm-proxy.kubiya.ai"
    ).strip()

    litellm_api_key = os.getenv("LITELLM_API_KEY", "").strip()

    if not litellm_api_key:
        raise ValueError("LITELLM_API_KEY environment variable not set")

    # PERFORMANCE OPTIMIZATION: Sonnet for both steps
    # Haiku struggles with complex structured output schemas - Sonnet is more reliable
    # Target: <30 seconds total
    step1_model_id = os.getenv("STEP1_MODEL", "kubiya/claude-sonnet-4").strip()
    step2_model_id = os.getenv("STEP2_MODEL", "kubiya/claude-sonnet-4").strip()

    logger.info("model_configuration",
                step1_model=step1_model_id,
                step2_model=step2_model_id,
                message="Using Sonnet for both steps (reliable structured output)")

    # Create model instances with appropriate timeouts
    # Step 1: Tool calling with Sonnet - target 10-15 seconds
    step1_model = LiteLLM(
        id=f"openai/{step1_model_id}",
        api_base=litellm_api_url,
        api_key=litellm_api_key,
        request_params={"timeout": 60}  # Sonnet needs time for tool calls
    )

    # Step 2: Structured output with Sonnet - target 15-20 seconds
    step2_model = LiteLLM(
        id=f"openai/{step2_model_id}",
        api_base=litellm_api_url,
        api_key=litellm_api_key,
        request_params={"timeout": 60}  # Sonnet for reliable structured output
    )

    # Log outer context if provided
    if outer_context:
        logger.info(
            "outer_context_provided",
            agents_count=len(outer_context.get("agents", [])),
            teams_count=len(outer_context.get("teams", [])),
            environments_count=len(outer_context.get("environments", [])),
            worker_queues_count=len(outer_context.get("worker_queues", [])),
            organization_id=organization_id[:8]
        )

    logger.info(
        "creating_planning_workflow",
        step1_model=step1_model_id,
        step2_model=step2_model_id,
        has_outer_context=bool(outer_context),
        organization_id=organization_id[:8]
    )

    # PRE-FETCH OPTIMIZATION: Get top 20 most-used resources with CACHING
    # Limits context window bloat while providing enough data for 90% of cases
    # Cache avoids repeated DB calls (5-minute TTL)

    # Check cache first
    cached_data = get_cached_prefetch(organization_id)
    if cached_data and not outer_context:
        # Use cached data
        outer_context = cached_data.copy()
        logger.info("using_cached_prefetch", organization_id=organization_id[:8])
    else:
        # Fetch fresh data
        logger.info("pre_fetching_top_resources", organization_id=organization_id[:8])

        from control_plane_api.app.lib.planning_tools.planning_service import PlanningService

        planning_service = PlanningService(db, organization_id, api_token)

        # Execute pre-fetch SEQUENTIALLY to avoid SQLAlchemy session concurrency issues
        try:
            agents_data = planning_service.list_agents(limit=20, status=None)
            teams_data = planning_service.list_teams(limit=20, status=None)
            # Don't filter by status - environments may have status="ready" or "active"
            envs_data = planning_service.list_environments(status=None, limit=20)
            queues_data = planning_service.list_worker_queues(limit=20)

            logger.info(
                "pre_fetch_completed",
                agents_count=len(agents_data),
                teams_count=len(teams_data),
                envs_count=len(envs_data),
                queues_count=len(queues_data),
                message="Pre-fetched top 20 of each type. Tools still available for more."
            )

            # Store in outer_context with limited data (only update missing/empty fields)
            if outer_context is None:
                outer_context = {}

            # Only update fields that are missing or empty (don't overwrite CLI-provided data)
            if not outer_context.get("agents"):
                outer_context["agents"] = agents_data[:20]
            if not outer_context.get("teams"):
                outer_context["teams"] = teams_data[:20]
            if not outer_context.get("environments"):
                outer_context["environments"] = envs_data[:20]
            if not outer_context.get("worker_queues"):
                # Sort worker queues by active_workers DESC (queues with active workers first!)
                sorted_queues = sorted(
                    queues_data[:20],
                    key=lambda q: q.get("active_workers", 0),
                    reverse=True
                )
                outer_context["worker_queues"] = sorted_queues
                logger.info(
                    "worker_queues_sorted",
                    total=len(sorted_queues),
                    with_active_workers=len([q for q in sorted_queues if q.get("active_workers", 0) > 0]),
                    message="Worker queues sorted by active_workers (DESC)"
                )

            outer_context["pre_fetch_note"] = "Top 20 most common resources. Use tools if you need more specific matches."

            # Cache the data for subsequent requests
            set_cached_prefetch(organization_id, outer_context)

        except Exception as e:
            import traceback
            logger.warning("pre_fetch_failed", error=str(e), traceback=traceback.format_exc(), message="Continuing without pre-fetched data")
            # Continue without pre-fetched data - agent will use tools instead

    # Create workflow steps (SIMPLIFIED 2-STEP WORKFLOW)
    # Create planning toolkit for Step 1 tools
    planning_toolkit = PlanningToolkit(db, organization_id, api_token)

    # NEW Step 1: Analysis + Resource Selection (combines old Steps 1+2)
    # PHASE 3: Uses Opus for better reasoning and tool usage
    step1_analysis_and_selection = create_analysis_and_selection_agent(
        model=step1_model,  # Opus for intelligent selection
        planning_toolkit=planning_toolkit,
        outer_context=outer_context
    )

    # NEW Step 2: Full Plan Generation with Cost Estimation (combines old Steps 3+4)
    # Uses Sonnet for faster generation
    step2_plan_generation = create_plan_generation_agent(step2_model)  # Sonnet for speed

    # Create 2-step workflow
    workflow = Workflow(
        name="Task Planning Workflow",
        steps=[
            step1_analysis_and_selection,
            step2_plan_generation,
        ],
        description="Simplified 2-step task planning: (1) Analysis & Resource Selection, (2) Full Plan Generation with Costs",
    )

    # PHASE 1 IMPROVEMENT: Store planning_toolkit for validation
    workflow._planning_toolkit = planning_toolkit
    # Store outer_context for runtime access (e.g., auto-populating runtime/model_id)
    workflow._outer_context = outer_context

    logger.info(
        "planning_workflow_created",
        steps=2,  # Down from 4!
        pre_fetched_data=bool(outer_context),
        message="Simplified 2-step workflow with smart pre-fetching and Phase 1 improvements"
    )

    return workflow


def create_fast_selection_agent(
    model: LiteLLM,
    db: Session,
    organization_id: str,
    api_token: str,
    outer_context: Optional[Dict[str, Any]] = None
) -> Agent:
    """
    Creates a fast selection agent for --local mode that does everything in one shot:
    1. Select agent/team (from outer context or DB)
    2. Select environment (from outer context or DB)
    3. Select worker queue (from outer context or DB)
    4. Return minimal response

    This is the ONLY agent in the fast workflow - no analysis, no cost estimation.
    """
    import json
    from agno.tools.function import Function

    # Get full toolkit but we'll filter to only essential tools
    planning_toolkit = PlanningToolkit(db, organization_id, api_token)

    # ONLY give agent the tools it needs for fast selection
    essential_tools = []

    # If outer_context provided, create synthetic tools (NO API calls needed!)
    if outer_context:
        # Synthetic tool for agents from outer context
        if outer_context.get("agents"):
            def get_outer_context_agents() -> str:
                """Get pre-filtered agents provided by CLI (outer context).

                INSTANT - no API call needed, data already fetched by CLI.
                Returns structured JSON with agent data.

                Returns:
                    JSON string with agents list
                """
                return json.dumps({
                    "type": "tool_result",
                    "tool": "get_outer_context_agents",
                    "success": True,
                    "data": {
                        "agents": outer_context.get("agents", []),
                        "count": len(outer_context.get("agents", []))
                    },
                    "human_readable": f"Found {len(outer_context.get('agents', []))} agents from CLI context (instant)"
                }, indent=2)

            essential_tools.append(Function.from_callable(get_outer_context_agents))
        else:
            # Fallback: need to fetch from DB
            if "list_agents" in planning_toolkit.functions:
                essential_tools.append(planning_toolkit.functions["list_agents"])

        # Synthetic tool for teams from outer context
        if outer_context.get("teams"):
            def get_outer_context_teams() -> str:
                """Get pre-filtered teams provided by CLI (outer context).

                INSTANT - no API call needed, data already fetched by CLI.
                Returns structured JSON with team data.

                Returns:
                    JSON string with teams list
                """
                return json.dumps({
                    "type": "tool_result",
                    "tool": "get_outer_context_teams",
                    "success": True,
                    "data": {
                        "teams": outer_context.get("teams", []),
                        "count": len(outer_context.get("teams", []))
                    },
                    "human_readable": f"Found {len(outer_context.get('teams', []))} teams from CLI context (instant)"
                }, indent=2)

            essential_tools.append(Function.from_callable(get_outer_context_teams))
        else:
            # Fallback: need to fetch from DB
            if "list_teams" in planning_toolkit.functions:
                essential_tools.append(planning_toolkit.functions["list_teams"])

        # Synthetic tool for environments from outer context
        if outer_context.get("environments"):
            def get_outer_context_environments() -> str:
                """Get pre-filtered environments provided by CLI (outer context).

                INSTANT - no API call needed, data already fetched by CLI.
                Returns structured JSON with environment data.

                Returns:
                    JSON string with environments list
                """
                return json.dumps({
                    "type": "tool_result",
                    "tool": "get_outer_context_environments",
                    "success": True,
                    "data": {
                        "environments": outer_context.get("environments", []),
                        "count": len(outer_context.get("environments", []))
                    },
                    "human_readable": f"Found {len(outer_context.get('environments', []))} environments from CLI context (instant)"
                }, indent=2)

            essential_tools.append(Function.from_callable(get_outer_context_environments))
    else:
        # No outer context - use real API tools
        if "list_teams" in planning_toolkit.functions:
            essential_tools.append(planning_toolkit.functions["list_teams"])
        if "list_agents" in planning_toolkit.functions:
            essential_tools.append(planning_toolkit.functions["list_agents"])

    toolkit_tools = essential_tools

    # Build simple step-by-step instructions
    has_outer_agents = outer_context and outer_context.get("agents")
    has_outer_teams = outer_context and outer_context.get("teams")
    has_outer_envs = outer_context and outer_context.get("environments")

    instructions = [
        "⚡ ULTRA-FAST SELECTOR - INSTANT DATA ⚡",
        "",
        "CLI already fetched all data! Just call the tools and pick FIRST available.",
        "",
    ]

    # Instructions for getting agents/teams
    if has_outer_agents and has_outer_teams:
        instructions.extend([
            "## STEP 1: Get pre-fetched data (INSTANT - no API calls!)",
            "  Call get_outer_context_agents() → populate discovered_agents",
            "  Call get_outer_context_teams() → populate discovered_teams",
            "",
        ])
    elif has_outer_agents:
        instructions.extend([
            "## STEP 1: Get pre-fetched agents (INSTANT)",
            "  Call get_outer_context_agents() → populate discovered_agents",
            "  discovered_teams = []",
            "",
        ])
    elif has_outer_teams:
        instructions.extend([
            "## STEP 1: Get pre-fetched teams (INSTANT)",
            "  Call get_outer_context_teams() → populate discovered_teams",
            "  discovered_agents = []",
            "",
        ])
    else:
        instructions.extend([
            "## STEP 1: Fetch agents AND teams from API",
            "  Call list_agents() → populate discovered_agents",
            "  Call list_teams() → populate discovered_teams",
            "",
        ])

    instructions.extend([
        "## STEP 2: Pick FIRST available (NO comparison)",
        "  If teams found: Pick FIRST team → entity_type='team'",
        "  Else if agents found: Pick FIRST agent → entity_type='agent'",
        "  Set: entity_id=<UUID>, entity_name=<name>",
        "",
    ])

    if has_outer_envs:
        instructions.extend([
            "## STEP 3: Get pre-fetched environments (INSTANT)",
            "  Call get_outer_context_environments()",
            "  Parse JSON → populate discovered_environments",
            "  Pick FIRST environment → environment_id=<UUID>, environment_name=<name>",
            "",
        ])
    else:
        instructions.extend([
            "## STEP 3: No environments",
            "  Set: environment_id=None, environment_name=None, discovered_environments=[]",
            "",
        ])

    instructions.extend([
        "## STEP 4: Set worker queues to None (CLI creates ephemeral queue)",
        "  Set: worker_queue_id=None, worker_queue_name=None, discovered_worker_queues=[]",
        "",
        "## STEP 5: Return output",
        "  Set reasoning to: 'Fast local execution'",
        "",
        "🚨 SPEED RULES:",
        "  - Call list_agents() + list_teams() in PARALLEL (both at once)",
        "  - Pick FIRST available (no analysis, no comparison)",
        "  - Keep reasoning SHORT: 1-3 words only",
        "  - Target: < 10 seconds total",
    ])

    return Agent(
        name="Fast Selector",
        role="Quick agent and environment selection for local testing",
        model=model,
        output_schema=FastSelectionOutput,
        tools=toolkit_tools,
        instructions=instructions,
        markdown=False
    )


def create_fast_planning_workflow(
    db: Session,
    organization_id: str,
    api_token: str,
    outer_context: Optional[Dict[str, Any]] = None
) -> Workflow:
    """
    Create a FAST 1-step planning workflow for --local mode.

    This workflow:
    - Skips task analysis (no complexity assessment)
    - Skips cost estimation (no detailed calculations)
    - Skips detailed plan generation (no task breakdown)
    - Just selects: agent/team + environment + worker queue

    Returns minimal FastSelectionOutput that gets converted to TaskPlanResponse.

    Args:
        db: Database session for internal service access
        organization_id: Organization ID for resource filtering (REQUIRED)
        api_token: Org-scoped API token for context graph access (REQUIRED)
        outer_context: Optional pre-filtered context from CLI (agents, teams, etc.)

    Returns:
        Configured Workflow with single fast selection agent
    """
    if not organization_id:
        raise ValueError("organization_id is required for fast planning workflow")

    if not api_token:
        raise ValueError("api_token is required for fast planning workflow")

    # Get LiteLLM configuration
    litellm_api_url = (
        os.getenv("LITELLM_API_URL") or
        os.getenv("LITELLM_API_BASE") or
        "https://llm-proxy.kubiya.ai"
    ).strip()

    litellm_api_key = os.getenv("LITELLM_API_KEY", "").strip()

    if not litellm_api_key:
        raise ValueError("LITELLM_API_KEY environment variable not set")

    # Use fast model for local execution
    # Override with env var if needed: LITELLM_FAST_MODEL=kubiya/claude-sonnet-4
    model_id = os.getenv("LITELLM_FAST_MODEL", "kubiya/claude-sonnet-4").strip()

    # Create model instance with reasonable timeout for Sonnet
    model = LiteLLM(
        id=f"openai/{model_id}",
        api_base=litellm_api_url,
        api_key=litellm_api_key,
        request_params={"timeout": 120}  # 2 minutes for Sonnet (would be 60s for Haiku)
    )

    # Log outer context if provided
    if outer_context:
        logger.info(
            "fast_workflow_outer_context",
            agents_count=len(outer_context.get("agents", [])),
            teams_count=len(outer_context.get("teams", [])),
            environments_count=len(outer_context.get("environments", [])),
            worker_queues_count=len(outer_context.get("worker_queues", [])),
            organization_id=organization_id[:8]
        )

    logger.info(
        "creating_fast_planning_workflow",
        model=model_id,
        has_outer_context=bool(outer_context),
        organization_id=organization_id[:8]
    )

    # Create single fast selection agent
    fast_agent = create_fast_selection_agent(
        model, db, organization_id, api_token, outer_context
    )

    # Workflow with just 1 step!
    workflow = Workflow(
        name="Fast Planning Workflow",
        steps=[fast_agent],  # Just ONE step
        description="Fast agent/team selection for local execution (1-step, no analysis/cost-estimation)"
    )

    logger.info("fast_planning_workflow_created", steps=1)

    return workflow


def convert_fast_output_to_plan(
    fast_output: FastSelectionOutput,
    request: TaskPlanRequest
) -> TaskPlanResponse:
    """
    Convert minimal FastSelectionOutput to full TaskPlanResponse.
    Fills in required fields with sensible defaults for --local mode.

    Args:
        fast_output: Minimal selection from fast workflow
        request: Original planning request for context

    Returns:
        Complete TaskPlanResponse with defaults for fields not in fast output
    """
    from control_plane_api.app.models.task_planning import (
        ComplexityInfo,
        TeamBreakdownItem,
        RecommendedExecution,
        CostEstimate,
        RealizedSavings,
        HumanResourceCost
    )

    logger.info(
        "converting_fast_output_to_plan",
        entity_type=fast_output.recommended_entity_type,
        entity_id=fast_output.recommended_entity_id[:12],
        entity_name=fast_output.recommended_entity_name
    )

    return TaskPlanResponse(
        title=f"Execute: {request.description[:50]}",
        summary=request.description,

        # Minimal complexity (don't analyze in fast mode)
        complexity=ComplexityInfo(
            story_points=3,  # Default medium
            confidence="medium",
            reasoning="Fast selection for local execution - no detailed complexity analysis"
        ),

        # Single team breakdown (minimal)
        team_breakdown=[TeamBreakdownItem(
            team_id=fast_output.recommended_entity_id if fast_output.recommended_entity_type == "team" else None,
            team_name=fast_output.recommended_entity_name if fast_output.recommended_entity_type == "team" else "",
            agent_id=fast_output.recommended_entity_id if fast_output.recommended_entity_type == "agent" else None,
            agent_name=fast_output.recommended_entity_name if fast_output.recommended_entity_type == "agent" else None,
            responsibilities=[request.description],
            estimated_time_hours=1.0,
            agent_cost=0.10,
            tasks=[]  # No detailed tasks for fast mode
        )],

        # Recommended execution (THE KEY PART!)
        recommended_execution=RecommendedExecution(
            entity_type=fast_output.recommended_entity_type,
            entity_id=fast_output.recommended_entity_id,
            entity_name=fast_output.recommended_entity_name,
            reasoning=fast_output.reasoning,
            recommended_environment_id=fast_output.recommended_environment_id,
            recommended_environment_name=fast_output.recommended_environment_name,
            recommended_worker_queue_id=fast_output.recommended_worker_queue_id,
            recommended_worker_queue_name=fast_output.recommended_worker_queue_name,
            execution_reasoning="Fast selection for local execution"
        ),

        # Minimal cost (don't calculate in fast mode)
        cost_estimate=CostEstimate(
            estimated_cost_usd=0.10,
            breakdown=[]
        ),

        # Minimal savings (don't calculate in fast mode)
        realized_savings=RealizedSavings(
            without_kubiya_cost=10.0,
            without_kubiya_hours=1.0,
            without_kubiya_resources=[
                HumanResourceCost(
                    role="DevOps Engineer",
                    hourly_rate=100.0,
                    estimated_hours=1.0,
                    total_cost=100.0
                )
            ],
            with_kubiya_cost=0.10,
            with_kubiya_hours=0.1,
            money_saved=9.90,
            time_saved_hours=0.9,
            time_saved_percentage=90,
            savings_summary="Fast local execution - estimated 90% time savings"
        ),

        risks=[],
        prerequisites=[],
        success_criteria=["Task execution completes successfully"],
        has_questions=False,

        # Top-level environment fields for convenience
        selected_environment_id=fast_output.recommended_environment_id,
        selected_environment_name=fast_output.recommended_environment_name,

        # Agent runtime and model info
        selected_agent_runtime=getattr(fast_output, 'selected_agent_runtime', None),
        selected_agent_model_id=getattr(fast_output, 'selected_agent_model_id', None)
    )


# ============================================================================
# Workflow Runner with Streaming
# ============================================================================

# Step descriptions for real-time progress updates (2-STEP WORKFLOW)
STEP_DESCRIPTIONS = {
    1: "🔍 Discovering available agents and teams in your organization and selecting the best match for your task",
    2: "📋 Creating detailed execution plan with cost estimates, risks, and success criteria (will run on your local session)"
}

# Stage names for CLI/UI display (compatible with UI's hardcoded stages)
# UI expects: 'initializing', 'discovering', 'analyzing', 'generating', 'calculating', 'finalizing'
STEP_STAGE_NAMES = {
    1: "analyzing",      # Step 1: Analysis & Resource Selection
    2: "generating"      # Step 2: Plan Generation
}

# Progress milestones for each step (percentage) (2-STEP WORKFLOW)
STEP_PROGRESS_MAP = {
    1: 50,   # Analysis & Resource Selection (combines old Steps 1+2)
    2: 95    # Full Plan Generation with Costs (combines old Steps 3+4)
}


def create_tool_wrapper(tool, publish_event, step_number):
    """
    Wrap a tool to emit events before/after execution.

    Args:
        tool: The Agno tool to wrap
        publish_event: Callback to emit streaming events
        step_number: Current workflow step number (1-4)

    Returns:
        Wrapped tool that emits events
    """
    import uuid
    from datetime import datetime
    import copy

    # Get the original function from the tool
    # Agno tools have 'entrypoint' attribute, not 'function'
    if hasattr(tool, 'entrypoint'):
        original_func = tool.entrypoint
    elif hasattr(tool, 'function'):
        original_func = tool.function
    elif callable(tool):
        original_func = tool
    else:
        logger.warning("tool_wrapper_skip", tool=str(tool), reason="not_callable")
        return tool

    def wrapped_function(*args, **kwargs):
        tool_id = str(uuid.uuid4())
        tool_name = getattr(tool, 'name', getattr(original_func, '__name__', 'unknown_tool'))
        tool_description = getattr(tool, 'description', None)

        # DEBUG: Log that wrapped function is being called
        logger.info("WRAPPED_FUNCTION_CALLED", tool_name=tool_name, step=step_number, args_count=len(args), kwargs_count=len(kwargs))

        # Handle Agno's quirk: sometimes it passes both 'args' and 'kwargs' as keyword arguments
        # e.g., function(args=['kubernetes'], kwargs={'limit': 10})
        if 'args' in kwargs:
            args_from_kwargs = kwargs.pop('args')
            if isinstance(args_from_kwargs, list) and not args:
                args = tuple(args_from_kwargs)
            logger.info("converted_args_kwarg", tool_name=tool_name, args=args)

        if 'kwargs' in kwargs:
            kwargs_from_kwargs = kwargs.pop('kwargs')
            if isinstance(kwargs_from_kwargs, dict):
                # Merge the nested kwargs with the outer kwargs
                kwargs.update(kwargs_from_kwargs)
            logger.info("converted_kwargs_kwarg", tool_name=tool_name, kwargs=kwargs)

        # Emit tool_call event
        try:
            # Combine args and kwargs for the event
            event_args = {
                'args': list(args) if args else [],
                **kwargs
            }
            publish_event({
                "event": "tool_call",
                "data": {
                    "tool_id": tool_id,
                    "tool_name": tool_name,
                    "tool_description": tool_description,
                    "arguments": event_args,
                    "step": step_number,
                    "timestamp": datetime.now().isoformat()
                }
            })
            logger.info("tool_call_event_published", tool_name=tool_name, tool_id=tool_id)
        except Exception as e:
            logger.warning("failed_to_emit_tool_call", error=str(e), exc_info=True)

        start_time = time.time()

        try:
            # Execute actual tool
            result = original_func(*args, **kwargs)
            duration = time.time() - start_time

            # Emit tool_result event with success
            try:
                # Truncate large results to avoid overwhelming the stream
                result_str = str(result)[:1000] if result else ""

                publish_event({
                    "event": "tool_result",
                    "data": {
                        "tool_id": tool_id,
                        "tool_name": tool_name,
                        "status": "success",
                        "result": result_str,
                        "duration": duration,
                        "step": step_number,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                logger.info("tool_result_event_published", tool_name=tool_name, tool_id=tool_id, status="success")
            except Exception as e:
                logger.warning("failed_to_emit_tool_result", error=str(e), exc_info=True)

            return result

        except Exception as e:
            duration = time.time() - start_time

            # Emit tool_result event with error
            try:
                publish_event({
                    "event": "tool_result",
                    "data": {
                        "tool_id": tool_id,
                        "tool_name": tool_name,
                        "status": "failed",
                        "error": str(e),
                        "duration": duration,
                        "step": step_number,
                        "timestamp": datetime.now().isoformat()
                    }
                })
            except Exception as emit_error:
                logger.warning("failed_to_emit_tool_error", error=str(emit_error))

            # Re-raise the original exception
            raise

    # Create a copy of the tool with the wrapped function
    try:
        if hasattr(tool, '__dict__'):
            wrapped_tool = copy.copy(tool)
            # Agno tools use 'entrypoint', not 'function'
            if hasattr(tool, 'entrypoint'):
                wrapped_tool.entrypoint = wrapped_function
            elif hasattr(tool, 'function'):
                wrapped_tool.function = wrapped_function
            else:
                # Fallback: just return wrapped function
                return wrapped_function
            return wrapped_tool
        else:
            # If we can't copy it, just return a callable wrapper
            return wrapped_function
    except Exception as e:
        logger.warning("tool_copy_failed", error=str(e), tool=str(tool))
        return tool


def extract_json_from_mixed_content(content: str, logger) -> dict:
    """
    Extract JSON object from mixed text content using multiple strategies.

    This handles various LLM output patterns:
    1. Pure JSON (ideal case)
    2. Markdown code blocks (```json ... ```)
    3. Text with inline JSON (preamble + JSON)
    4. Text with JSON after common prefixes
    5. Last complete JSON object in text

    Args:
        content: Raw string content from LLM
        logger: Structlog logger for debugging

    Returns:
        Parsed JSON as Python dict

    Raises:
        ValueError: If no valid JSON found after all strategies
    """
    import json
    import re

    cleaned = content.strip()

    # Strategy 1: Try direct parse (best case - pure JSON)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.debug("strategy_1_failed", strategy="direct_parse")

    # Strategy 2: Extract from markdown code block
    if '```' in cleaned:
        # Match: ```json\n{...}\n``` or ```{...}```
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                logger.debug("strategy_2_failed", strategy="markdown_block")

    # Strategy 3: Find first { to last } (captures JSON in mixed text)
    # This handles: "Here's my analysis: {JSON_HERE} and that's it"
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        json_candidate = cleaned[first_brace:last_brace + 1]
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            logger.debug("strategy_3_failed", strategy="first_to_last_brace")

    # Strategy 4: Look for JSON after common prefixes
    # Handles: "Output:\n{JSON}" or "Result: {JSON}"
    common_prefixes = [
        r'(?:output|result|response|analysis|data):\s*(\{.*\})',
        r'(?:here is|here\'s).*?:\s*(\{.*\})',
    ]
    for pattern in common_prefixes:
        match = re.search(pattern, cleaned, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    # Strategy 5: Try each complete JSON object (handles multiple JSONs)
    # Find all {...} patterns and try parsing each
    for match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned, re.DOTALL):
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            continue

    # All strategies failed
    raise ValueError(
        f"Could not extract valid JSON from content after 5 extraction strategies. "
        f"Content preview: {cleaned[:300]}"
    )


def validate_and_fix_step1_output(
    output: 'AnalysisAndSelectionOutput',
    planning_toolkit: Optional['PlanningToolkit'] = None
) -> 'AnalysisAndSelectionOutput':
    """
    Validate and auto-correct Step 1 output to ensure it's always valid.

    If issues are found (None values, invalid UUIDs), attempt to fix them
    automatically using available tools.

    Args:
        output: Step 1 output to validate
        planning_toolkit: Optional toolkit for fetching fallback agent

    Returns:
        Validated and corrected output

    Raises:
        ValueError: If output cannot be corrected
    """
    import re

    logger.info("validating_step1_output",
               entity_id=output.selected_entity_id,
               entity_name=output.selected_entity_name)

    # Check 1: selected_entity_id is not None or "None" string
    if not output.selected_entity_id or output.selected_entity_id in ["None", "null", "undefined"]:
        logger.warning("step1_selected_none_entity",
                      message="Step 1 returned None/null for entity_id, attempting auto-correction")

        # Try to auto-correct using fallback tool
        if planning_toolkit:
            try:
                import json
                fallback_result = planning_toolkit.get_fallback_agent()
                fallback_data = json.loads(fallback_result)

                if fallback_data.get("success") and fallback_data.get("data", {}).get("agent"):
                    fallback_agent = fallback_data["data"]["agent"]
                    output.selected_entity_id = fallback_agent["id"]
                    output.selected_entity_name = fallback_agent["name"]
                    output.selected_entity_type = "agent"
                    output.selection_reasoning += " (Auto-corrected: Used fallback agent due to None value)"

                    logger.info("step1_auto_corrected",
                               new_entity_id=output.selected_entity_id,
                               message="Successfully auto-corrected using fallback")
                else:
                    raise ValueError("Fallback tool did not return valid agent")

            except Exception as e:
                logger.error("step1_auto_correction_failed", error=str(e))
                raise ValueError(
                    f"Step 1 returned None for selected_entity_id and auto-correction failed: {str(e)}"
                )
        else:
            raise ValueError("Step 1 returned None for selected_entity_id and no planning_toolkit available for auto-correction")

    # Check 2: Entity ID is valid UUID format
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, output.selected_entity_id, re.IGNORECASE):
        logger.error("step1_invalid_uuid",
                    entity_id=output.selected_entity_id,
                    message="Invalid UUID format detected - this is likely hallucination")
        raise ValueError(
            f"Invalid entity_id format: '{output.selected_entity_id}'. "
            f"Must be valid UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx). "
            f"This looks like a hallucinated ID - the agent must use ACTUAL IDs from tool results."
        )

    # Check 3: Cost and time are reasonable (auto-correct if unreasonable)
    if output.estimated_cost_usd <= 0:
        logger.warning("step1_invalid_cost",
                      original_cost=output.estimated_cost_usd,
                      message="Cost was <= 0, setting to minimum $0.05")
        output.estimated_cost_usd = 0.05  # Minimum realistic cost

    if output.estimated_time_hours <= 0:
        logger.warning("step1_invalid_time",
                      original_time=output.estimated_time_hours,
                      message="Time was <= 0, setting to minimum 0.25 hours")
        output.estimated_time_hours = 0.25  # Minimum realistic time (15 minutes)

    # Check 4: Story points are in valid range
    if output.story_points_estimate < 1:
        logger.warning("step1_invalid_story_points_low",
                      original_points=output.story_points_estimate)
        output.story_points_estimate = 1

    if output.story_points_estimate > 21:
        logger.warning("step1_invalid_story_points_high",
                      original_points=output.story_points_estimate)
        output.story_points_estimate = 21

    # Check 5: Environment is selected (CRITICAL for local execution)
    if not output.selected_environment_id or output.selected_environment_id in ["None", "null", "undefined"]:
        logger.warning("step1_missing_environment",
                      message="Step 1 did not select an environment, attempting auto-correction")

        # Try to get first available environment
        if planning_toolkit:
            try:
                import json
                # Try to get environments from planning service
                environments = planning_toolkit.planning_service.list_environments(limit=20)

                if environments and len(environments) > 0:
                    first_env = environments[0]
                    output.selected_environment_id = first_env.get("id")
                    output.selected_environment_name = first_env.get("name", "Default Environment")
                    output.reasoning += " (Auto-corrected: Selected first available environment)"

                    logger.info("step1_environment_auto_corrected",
                               environment_id=output.selected_environment_id,
                               environment_name=output.selected_environment_name,
                               message="Successfully auto-corrected environment selection")
                else:
                    logger.warning("step1_no_environments_available",
                                 message="No environments available in organization")
                    # Don't fail - let execution fail later with better error message
            except Exception as e:
                logger.warning("step1_environment_auto_correction_failed", error=str(e))
                # Don't fail here - some execution modes might not need environment
        else:
            logger.warning("step1_no_toolkit_for_environment_correction")

    logger.info("step1_validation_passed",
               entity_id=output.selected_entity_id,
               entity_name=output.selected_entity_name,
               environment_id=output.selected_environment_id,
               cost=output.estimated_cost_usd,
               time=output.estimated_time_hours)

    return output


def execute_step_with_tool_tracking(
    step: Agent,
    input_data: str,
    publish_event: callable,
    step_number: int,
    max_retries: int = 1
) -> Any:
    """
    Execute a workflow step with validation and retry logic.

    Wraps the step's tools to emit events before/after execution.
    Validates outputs and retries with error feedback if validation fails.

    Args:
        step: The Agno Agent (workflow step) to execute
        input_data: Input string for the agent
        publish_event: Callback to emit streaming events
        step_number: Current workflow step number (1-4)
        max_retries: Maximum number of attempts (default: 1, no retries)

    Returns:
        The step's output (content from agent response)

    Raises:
        ValueError: If validation fails after all retries
    """
    from pydantic import ValidationError

    original_tools = None

    # Retry loop for validation failures
    for attempt in range(max_retries):
        try:
            # Wrap each tool in the step
            if hasattr(step, 'tools') and step.tools and original_tools is None:
                original_tools = step.tools
                wrapped_tools = []

                logger.info("wrapping_step_tools", step=step_number, tool_count=len(original_tools), attempt=attempt + 1)

                for tool in original_tools:
                    tool_name = getattr(tool, 'name', str(tool)[:50])
                    logger.info("wrapping_tool", step=step_number, tool_name=tool_name)
                    wrapped_tool = create_tool_wrapper(tool, publish_event, step_number)
                    wrapped_tools.append(wrapped_tool)

                # Temporarily replace tools
                step.tools = wrapped_tools
                logger.info("tools_replaced", step=step_number, original_count=len(original_tools), wrapped_count=len(wrapped_tools))

            # Execute the step (LiteLLM timeout at 240s provides protection)
            logger.info("executing_step", step=step_number, step_name=step.name, attempt=attempt + 1, max_retries=max_retries)

            # DEBUG: Log tool info before execution
            if hasattr(step, 'tools') and step.tools:
                tool_names = [getattr(t, 'name', str(t)[:30]) for t in step.tools[:5]]
                logger.info("step_tools_before_run", step=step_number, tool_count=len(step.tools), first_5_tools=tool_names)

            # Execute step directly
            result = step.run(input_data)

            logger.info("step_execution_completed", step=step_number, attempt=attempt + 1)

            # Extract reasoning from agent messages if available (skip in quick mode for speed)
            # Quick mode flag is passed from the workflow context
            skip_reasoning = getattr(step, '_quick_mode', False)
            if not skip_reasoning:
                try:
                    from datetime import datetime
                    if hasattr(result, 'messages') and result.messages:
                        for message in result.messages:
                            # Check for assistant messages with content (reasoning/thinking)
                            if hasattr(message, 'role') and message.role == 'assistant':
                                if hasattr(message, 'content') and message.content:
                                    # Extract text content (reasoning before tool calls)
                                    reasoning_text = message.content if isinstance(message.content, str) else str(message.content)
                                    if reasoning_text and len(reasoning_text) > 20:  # Filter out very short messages
                                        publish_event({
                                            "event": "thinking",
                                            "data": {
                                                "content": reasoning_text,
                                                "step": step_number,
                                                "step_name": step.name,
                                                "timestamp": datetime.now().isoformat()
                                            }
                                        })
                                        logger.info("reasoning_event_published", step=step_number, reasoning_length=len(reasoning_text))
                except Exception as e:
                    logger.warning("failed_to_extract_reasoning", error=str(e), exc_info=False)

            # Extract content from result
            content = result.content if hasattr(result, 'content') else result

            # CRITICAL VALIDATION: Check if Agno's parsing failed (returned None)
            if content is None:
                raise ValueError(
                    f"Step {step_number} ({step.name}) returned None. "
                    f"This indicates validation failed during Agno's parsing. "
                    f"The LLM output did not match the expected schema."
                )

            # UNIVERSAL FIX: If output is a string, try to parse it as JSON
            # This handles cases where Agno fails to parse LLM output
            if isinstance(content, str) and hasattr(step, 'output_schema'):
                logger.warning("step_output_is_string", step=step_number, message="Attempting manual JSON parsing")
                original_content = content  # Save original for logging
                try:
                    # Use multi-strategy JSON extraction
                    content_dict = extract_json_from_mixed_content(content, logger)

                    # Validate with Pydantic model
                    content = step.output_schema.model_validate(content_dict)
                    logger.info("manual_json_parsing_succeeded", step=step_number)

                    # Log if we had to extract from mixed content (indicates LLM didn't follow instructions)
                    if not original_content.strip().startswith('{'):
                        logger.warning(
                            "llm_added_preamble_text",
                            step=step_number,
                            message="LLM added text before JSON despite output_schema constraint"
                        )
                except ValueError as extract_error:
                    # JSON extraction failed
                    raise ValueError(
                        f"Step {step_number} output validation failed - could not extract valid JSON. "
                        f"Expected {step.output_schema.__name__}. "
                        f"Extraction error: {str(extract_error)}. "
                        f"Content preview: {str(content)[:500]}"
                    )
                except Exception as parse_error:
                    # Pydantic validation failed
                    raise ValueError(
                        f"Step {step_number} output validation failed - JSON extracted but schema validation failed. "
                        f"Expected {step.output_schema.__name__}. "
                        f"Validation error: {str(parse_error)}. "
                        f"Content preview: {str(content)[:500]}"
                    )

            # CRITICAL VALIDATION: For Step 2, explicitly validate entity IDs
            if step_number == 2 and hasattr(step, 'output_schema'):
                # Validate type after universal string parsing above
                if not isinstance(content, step.output_schema):
                    raise ValueError(
                        f"Step {step_number} output validation failed. "
                        f"Expected {step.output_schema.__name__}, got {type(content).__name__}. "
                        f"Content: {str(content)[:200]}"
                    )

                # Additional explicit validation for ResourceDiscoveryOutput
                if isinstance(content, ResourceDiscoveryOutput):
                    # Manually re-validate to catch any issues Agno suppressed
                    _validate_resource_discovery(content)

            logger.info("step_validation_passed", step=step_number, attempt=attempt + 1)
            return content  # Success!

        except (ValueError, ValidationError) as e:
            logger.warning(
                "step_validation_failed",
                step=step_number,
                attempt=attempt + 1,
                max_retries=max_retries,
                error=str(e),
                exc_info=True
            )

            # Emit validation error event for monitoring
            try:
                publish_event({
                    "event": "validation_error",
                    "data": {
                        "step": step_number,
                        "attempt": attempt + 1,
                        "error": str(e),
                        "retrying": attempt < max_retries - 1
                    }
                })
            except Exception as emit_error:
                logger.warning("failed_to_emit_validation_error", error=str(emit_error))

            if attempt < max_retries - 1:
                # Build retry input with explicit error feedback to the LLM
                retry_input = f"""
🚨 VALIDATION ERROR - Your previous output was REJECTED 🚨

Error Details:
{str(e)}

CRITICAL: You MUST output ONLY valid JSON, with NO explanatory text before or after.

Common mistakes to avoid:
❌ Adding reasoning before JSON: "Let me analyze this... {{json}}"
❌ Using markdown code blocks: ```json {{...}} ```
❌ Adding text after JSON: "{{json}} and that's my analysis"

✅ CORRECT FORMAT: Start your response directly with {{ and end with }}

Additional Requirements:
1. Using ONLY IDs from actual tool call results (do not invent or guess IDs)
2. NOT hallucinating any entity IDs or names
3. Copying the exact ID strings from tool outputs
4. Double-checking that your recommended_entity_id exists in discovered_agents/discovered_teams

Original Task:
{input_data}

OUTPUT FORMAT REMINDER: Your response must be PURE JSON starting with {{ and ending with }}

Try again with the corrections above. This is attempt {attempt + 2} of {max_retries}.
"""
                input_data = retry_input
                logger.info("retrying_step_with_feedback", step=step_number, attempt=attempt + 2)
                continue  # Retry with error feedback
            else:
                # Final attempt failed - raise with full context
                raise ValueError(
                    f"Step {step_number} ({step.name}) failed validation after {max_retries} attempts. "
                    f"Final error: {str(e)}"
                )

        except Exception as e:
            # Non-validation error (e.g., execution error)
            logger.error("step_execution_failed", step=step_number, error=str(e), exc_info=True)
            raise

        finally:
            # Restore original tools if we wrapped them
            if original_tools is not None and hasattr(step, 'tools'):
                step.tools = original_tools

    # Should never reach here
    raise ValueError(f"Step {step_number} execution logic error - exhausted all retries")


def run_planning_workflow_stream(
    workflow: Workflow,
    task_request: TaskPlanRequest,
    publish_event: callable,
    quick_mode: bool = False
) -> TaskPlanResponse:
    """
    Run the planning workflow with real-time step-by-step streaming and tool event tracking.

    This implementation manually executes each workflow step, intercepting tool calls
    to provide detailed real-time progress updates including:
    - Step start/complete events with structured outputs
    - Tool execution events (call + result) with timing
    - Actual progress based on step completion

    Args:
        workflow: The planning workflow instance
        task_request: Task plan request
        publish_event: Callback to emit streaming events

    Returns:
        TaskPlanResponse from the final workflow step
    """
    try:
        # Build workflow input
        workflow_input = f"""
Task: {task_request.description}
Priority: {task_request.priority}
Context: {task_request.conversation_context or 'New task'}

Analyze this task systematically through the workflow steps.
"""

        logger.info("workflow_runner_starting", input_length=len(workflow_input), steps=len(workflow.steps))

        # Emit initial progress with informative message
        publish_event({
            "event": "progress",
            "data": {
                "stage": "initializing",
                "message": "🚀 Initializing AI Task Planner - analyzing your request and preparing to discover available resources...",
                "progress": 10
            }
        })

        # Store outputs from each step
        step_outputs = {}
        current_input = workflow_input

        # Manually execute each step with tool tracking
        for i, step in enumerate(workflow.steps, 1):
            # Track step execution time for monitoring
            step_start_time = time.time()

            # Mark step with quick_mode flag if in quick mode (for skipping verbose reasoning)
            if quick_mode:
                step._quick_mode = True

            logger.info("starting_workflow_step", step=i, step_name=step.name, quick_mode=quick_mode)

            # Emit step_started event
            step_progress = STEP_PROGRESS_MAP.get(i, 10 + (i * 20))
            publish_event({
                "event": "step_started",
                "data": {
                    "step": i,
                    "step_name": step.name,
                    "step_description": STEP_DESCRIPTIONS.get(i, f"Executing {step.name}"),
                    "progress": step_progress
                }
            })

            # Also emit explicit progress event for better UX (with friendly stage names)
            publish_event({
                "event": "progress",
                "data": {
                    "stage": STEP_STAGE_NAMES.get(i, f"step_{i}"),  # Use friendly names like "analyzing", "planning"
                    "message": STEP_DESCRIPTIONS.get(i, f"Executing {step.name}"),
                    "progress": step_progress
                }
            })

            # Execute step with tool tracking AND validation (2-STEP WORKFLOW)
            # Step 1 (Analysis & Resource Selection) gets 2 retries for validation failures
            # Step 2 (Plan Generation) gets 1 attempt since it just generates plan from Step 1 output
            step_result = execute_step_with_tool_tracking(
                step=step,
                input_data=current_input,
                publish_event=publish_event,
                step_number=i,
                max_retries=2 if i == 1 else 1  # Step 1 (Analysis & Selection) gets 2 retries, Step 2 gets 1
            )

            # PHASE 1 IMPROVEMENT: Validate and auto-correct Step 1 output
            if i == 1:
                from control_plane_api.app.models.task_planning import AnalysisAndSelectionOutput
                if isinstance(step_result, AnalysisAndSelectionOutput):
                    try:
                        # Get planning toolkit from workflow context if available
                        planning_toolkit = None
                        if hasattr(workflow, '_planning_toolkit'):
                            planning_toolkit = workflow._planning_toolkit

                        # Validate and auto-correct if needed
                        step_result = validate_and_fix_step1_output(
                            output=step_result,
                            planning_toolkit=planning_toolkit
                        )
                        logger.info("step1_validated_successfully",
                                   entity_id=step_result.selected_entity_id)

                    except Exception as validation_error:
                        logger.error("step1_validation_failed",
                                    error=str(validation_error),
                                    exc_info=True)
                        # Re-raise to trigger retry or fail the workflow
                        raise ValueError(f"Step 1 validation failed: {str(validation_error)}")

            # Store the output
            step_outputs[f"step_{i}"] = step_result

            # Emit step_completed event with structured output
            try:
                # Try to convert output to dict for JSON serialization
                if hasattr(step_result, 'model_dump'):
                    output_dict = step_result.model_dump()
                elif hasattr(step_result, 'dict'):
                    output_dict = step_result.dict()
                elif isinstance(step_result, dict):
                    output_dict = step_result
                else:
                    output_dict = {"output": str(step_result)}

                # Calculate step execution time
                step_duration = time.time() - step_start_time

                # Build informative completion message
                completion_message = None
                if i == 1 and hasattr(step_result, 'selected_entity_name'):
                    # Step 1: Mention what was discovered and selected
                    entity_type = getattr(step_result, 'selected_entity_type', 'entity')
                    entity_name = getattr(step_result, 'selected_entity_name', 'Unknown')
                    completion_message = f"✅ Selected {entity_type}: {entity_name} for task execution"
                elif i == 2:
                    # Step 2: Mention plan is ready for local execution
                    completion_message = "✅ Execution plan ready - will run on your local session compute"

                event_data = {
                    "step": i,
                    "step_name": step.name,
                    "output": output_dict,
                    "progress": STEP_PROGRESS_MAP.get(i, 10 + (i * 20)),
                    "duration_seconds": round(step_duration, 2)
                }

                if completion_message:
                    event_data["message"] = completion_message

                publish_event({
                    "event": "step_completed",
                    "data": event_data
                })

                logger.info(
                    "workflow_step_completed",
                    step=i,
                    step_name=step.name,
                    duration_seconds=round(step_duration, 2)
                )

            except Exception as e:
                logger.warning("failed_to_emit_step_completed", step=i, error=str(e))

            # Build input for next step (combine previous context with new output)
            if i < len(workflow.steps):
                # Pass the output to the next step
                if hasattr(step_result, 'model_dump_json'):
                    step_output_str = step_result.model_dump_json(indent=2)
                elif isinstance(step_result, dict):
                    step_output_str = json.dumps(step_result, indent=2)
                else:
                    step_output_str = str(step_result)

                current_input = f"""
Original Task:
{workflow_input}

Previous Step Output ({step.name}):
{step_output_str}

Continue to the next step of the workflow.
"""

        # Extract final result from LAST step (could be step 1 for fast workflow or step 4 for full workflow)
        num_steps = len(workflow.steps)
        last_step_key = f"step_{num_steps}"
        final_result = step_outputs.get(last_step_key)

        if not final_result:
            logger.error("no_final_result", step_outputs_keys=list(step_outputs.keys()), expected_key=last_step_key)
            raise ValueError(f"Workflow completed but {last_step_key} returned no result")

        # Handle FastSelectionOutput (from 1-step fast workflow)
        if isinstance(final_result, FastSelectionOutput):
            # Convert FastSelectionOutput to TaskPlanResponse
            plan = convert_fast_output_to_plan(final_result, task_request)
            logger.info("converted_fast_output_to_plan", entity_type=final_result.recommended_entity_type)
        # Handle TaskPlanResponse (from 4-step full workflow)
        elif isinstance(final_result, TaskPlanResponse):
            plan = final_result
        elif isinstance(final_result, dict):
            # Try to detect if this is FastSelectionOutput dict
            if 'recommended_entity_type' in final_result and 'reasoning' in final_result and 'title' not in final_result:
                fast_output = FastSelectionOutput(**final_result)
                plan = convert_fast_output_to_plan(fast_output, task_request)
                logger.info("converted_fast_output_dict_to_plan")
            else:
                plan = TaskPlanResponse(**final_result)
        else:
            raise ValueError(f"Last step returned unexpected type: {type(final_result)}")

        # POST-PROCESSING: Ensure top-level environment/runtime fields are populated
        # Get Step 1 output for runtime/model info if available
        step1_output = step_outputs.get("step_1")
        # Get outer_context from workflow for fallback lookups
        outer_context = getattr(workflow, '_outer_context', None)

        # Populate selected_environment_* from recommended_execution if not set
        if not plan.selected_environment_id and plan.recommended_execution.recommended_environment_id:
            plan.selected_environment_id = plan.recommended_execution.recommended_environment_id
            logger.info("auto_populated_selected_environment_id",
                       value=plan.selected_environment_id)

        if not plan.selected_environment_name and plan.recommended_execution.recommended_environment_name:
            plan.selected_environment_name = plan.recommended_execution.recommended_environment_name
            logger.info("auto_populated_selected_environment_name",
                       value=plan.selected_environment_name)

        # Populate selected_agent_runtime/model_id from Step 1 output if available
        if step1_output:
            if not plan.selected_agent_runtime:
                runtime = getattr(step1_output, 'selected_agent_runtime', None)
                if runtime:
                    plan.selected_agent_runtime = runtime
                    logger.info("auto_populated_selected_agent_runtime", value=runtime)

            if not plan.selected_agent_model_id:
                model_id = getattr(step1_output, 'selected_agent_model_id', None)
                if model_id:
                    plan.selected_agent_model_id = model_id
                    logger.info("auto_populated_selected_agent_model_id", value=model_id)

        # FALLBACK: If runtime/model_id still not set, look up from outer_context or DB
        # This handles cases where the LLM didn't extract these fields
        selected_entity_id = plan.recommended_execution.entity_id if plan.recommended_execution else None
        logger.info("runtime_fallback_check",
                   selected_entity_id=selected_entity_id,
                   entity_type=plan.recommended_execution.entity_type if plan.recommended_execution else None,
                   current_runtime=plan.selected_agent_runtime,
                   current_model_id=plan.selected_agent_model_id,
                   has_outer_context=bool(outer_context))

        if selected_entity_id and plan.recommended_execution.entity_type == "agent":
            if not plan.selected_agent_runtime or not plan.selected_agent_model_id:
                # First try outer_context
                agent_found = False
                if outer_context:
                    for agent in outer_context.get("agents", []):
                        if agent.get("id") == selected_entity_id:
                            if not plan.selected_agent_runtime and agent.get("runtime"):
                                plan.selected_agent_runtime = agent.get("runtime")
                                logger.info("auto_populated_selected_agent_runtime_from_context",
                                           value=plan.selected_agent_runtime)
                            if not plan.selected_agent_model_id and agent.get("model_id"):
                                plan.selected_agent_model_id = agent.get("model_id")
                                logger.info("auto_populated_selected_agent_model_id_from_context",
                                           value=plan.selected_agent_model_id)
                            agent_found = True
                            break

                # If still not found, use planning_toolkit to fetch from DB
                if not agent_found and (not plan.selected_agent_runtime or not plan.selected_agent_model_id):
                    planning_toolkit = getattr(workflow, '_planning_toolkit', None)
                    if planning_toolkit:
                        try:
                            # get_agent_details returns a JSON string
                            agent_details_json = planning_toolkit.get_agent_details(selected_entity_id)
                            agent_details = json.loads(agent_details_json) if isinstance(agent_details_json, str) else agent_details_json
                            if agent_details.get("success") and agent_details.get("data", {}).get("agent"):
                                agent_data = agent_details["data"]["agent"]
                                if not plan.selected_agent_runtime and agent_data.get("runtime"):
                                    plan.selected_agent_runtime = agent_data.get("runtime")
                                    logger.info("auto_populated_selected_agent_runtime_from_db",
                                               value=plan.selected_agent_runtime)
                                if not plan.selected_agent_model_id and agent_data.get("model_id"):
                                    plan.selected_agent_model_id = agent_data.get("model_id")
                                    logger.info("auto_populated_selected_agent_model_id_from_db",
                                               value=plan.selected_agent_model_id)
                        except Exception as e:
                            logger.warning("failed_to_fetch_agent_details_for_runtime",
                                          error=str(e), agent_id=selected_entity_id)

        # Success
        logger.info("workflow_completed_successfully",
                   title=plan.title,
                   steps_executed=len(step_outputs),
                   selected_environment_id=plan.selected_environment_id,
                   selected_agent_runtime=plan.selected_agent_runtime)
        publish_event({
            "event": "progress",
            "data": {
                "stage": "completed",
                "message": f"✅ Execution plan '{plan.title}' generated successfully! Ready to run on your local session compute.",
                "progress": 100
            }
        })

        return plan

    except Exception as e:
        logger.error("workflow_failed", error=str(e), exc_info=True)
        publish_event({
            "event": "error",
            "data": {"message": f"Workflow failed: {str(e)}"}
        })
        raise
