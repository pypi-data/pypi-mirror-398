"""
Agent Communication Skill

Provides agent-to-agent and agent-to-team communication capabilities.
"""
from typing import Dict, Any, List, Union, Literal, Optional
from pydantic import BaseModel, Field, validator
from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant
from control_plane_api.app.skills.registry import register_skill


class AgentCommunicationConfiguration(BaseModel):
    """Configuration for Agent Communication Skill"""

    allowed_operations: List[Literal[
        "execute_agent",
        "execute_team",
        "followup_execution",
        "get_execution_status"
    ]] = Field(
        default=["get_execution_status"],
        description="List of allowed tool operations"
    )

    allowed_agents: Union[List[str], Literal["*"]] = Field(
        default=[],
        description="List of agent IDs that can be called, or '*' for all"
    )

    allowed_teams: Union[List[str], Literal["*"]] = Field(
        default=[],
        description="List of team IDs that can be called, or '*' for all"
    )

    max_execution_depth: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Maximum nesting depth for child executions (0 = monitoring only)"
    )

    timeout: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Maximum wait time for child execution in seconds"
    )

    wait_for_completion: bool = Field(
        default=True,
        description="Whether to wait for child execution to complete (sync vs async)"
    )

    inherit_context: bool = Field(
        default=True,
        description="Whether to pass parent execution context to child"
    )

    max_concurrent_calls: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum number of concurrent child executions"
    )

    allow_session_continuation: bool = Field(
        default=True,
        description="Allow following up on existing sessions"
    )

    streaming_enabled: bool = Field(
        default=True,
        description="Stream child execution events to parent"
    )

    @validator('allowed_agents', 'allowed_teams')
    def validate_allowed_entities(cls, v):
        """Validate allowed entities format"""
        if v == "*":
            return v
        if not isinstance(v, list):
            raise ValueError("Must be a list of IDs or '*'")
        return v


class AgentCommunicationSkill(SkillDefinition):
    """Agent communication skill - orchestrate hierarchical agent execution"""

    @property
    def type(self) -> SkillType:
        return SkillType.AGENT_COMMUNICATION

    @property
    def name(self) -> str:
        return "Agent Communication"

    @property
    def description(self) -> str:
        return "Enable agents to call other agents or teams, creating hierarchical execution workflows"

    @property
    def icon(self) -> str:
        return "Network"

    def get_variants(self) -> List[SkillVariant]:
        return [
            SkillVariant(
                id="agent_communication_read_only",
                name="Agent Communication - Read Only",
                description="Monitor execution status only. Cannot initiate agent calls. Safe for observability.",
                category=SkillCategory.COMMON,
                badge="Safe",
                icon="Eye",
                configuration={
                    "allowed_operations": ["get_execution_status"],
                    "allowed_agents": [],
                    "allowed_teams": [],
                    "max_execution_depth": 0,
                    "timeout": 30,
                    "wait_for_completion": False,
                    "inherit_context": True,
                    "max_concurrent_calls": 1,
                    "allow_session_continuation": False,
                    "streaming_enabled": True,
                },
                is_default=False,
            ),
            SkillVariant(
                id="agent_communication_limited",
                name="Agent Communication - Limited",
                description="Call specific approved agents and teams with safeguards. Recommended for most use cases.",
                category=SkillCategory.COMMON,
                badge="Recommended",
                icon="Network",
                configuration={
                    "allowed_operations": ["execute_agent", "execute_team", "followup_execution", "get_execution_status"],
                    "allowed_agents": [],  # Must be explicitly configured
                    "allowed_teams": [],   # Must be explicitly configured
                    "max_execution_depth": 2,
                    "timeout": 300,
                    "wait_for_completion": True,
                    "inherit_context": True,
                    "max_concurrent_calls": 3,
                    "allow_session_continuation": True,
                    "streaming_enabled": True,
                },
                is_default=True,
            ),
            SkillVariant(
                id="agent_communication_full",
                name="Agent Communication - Full Orchestration",
                description="Unrestricted agent orchestration for complex workflows. Advanced use cases only.",
                category=SkillCategory.ADVANCED,
                badge="Advanced",
                icon="Workflow",
                configuration={
                    "allowed_operations": ["execute_agent", "execute_team", "followup_execution", "get_execution_status"],
                    "allowed_agents": "*",
                    "allowed_teams": "*",
                    "max_execution_depth": 5,
                    "timeout": 600,
                    "wait_for_completion": True,
                    "inherit_context": True,
                    "max_concurrent_calls": 10,
                    "allow_session_continuation": True,
                    "streaming_enabled": True,
                },
                is_default=False,
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate agent communication configuration"""
        try:
            # Validate using Pydantic model
            validated_config = AgentCommunicationConfiguration(**config)
            return validated_config.dict()
        except Exception as e:
            # Fallback to manual validation
            validated = {}

            # allowed_operations
            allowed_ops = config.get("allowed_operations", ["get_execution_status"])
            if not isinstance(allowed_ops, list):
                allowed_ops = ["get_execution_status"]
            validated["allowed_operations"] = allowed_ops

            # allowed_agents
            allowed_agents = config.get("allowed_agents", [])
            if allowed_agents == "*":
                validated["allowed_agents"] = "*"
            elif isinstance(allowed_agents, list):
                validated["allowed_agents"] = allowed_agents
            else:
                validated["allowed_agents"] = []

            # allowed_teams
            allowed_teams = config.get("allowed_teams", [])
            if allowed_teams == "*":
                validated["allowed_teams"] = "*"
            elif isinstance(allowed_teams, list):
                validated["allowed_teams"] = allowed_teams
            else:
                validated["allowed_teams"] = []

            # max_execution_depth
            validated["max_execution_depth"] = max(0, min(10, config.get("max_execution_depth", 2)))

            # timeout
            validated["timeout"] = max(30, min(3600, config.get("timeout", 300)))

            # wait_for_completion
            validated["wait_for_completion"] = bool(config.get("wait_for_completion", True))

            # inherit_context
            validated["inherit_context"] = bool(config.get("inherit_context", True))

            # max_concurrent_calls
            validated["max_concurrent_calls"] = max(1, min(20, config.get("max_concurrent_calls", 3)))

            # allow_session_continuation
            validated["allow_session_continuation"] = bool(config.get("allow_session_continuation", True))

            # streaming_enabled
            validated["streaming_enabled"] = bool(config.get("streaming_enabled", True))

            return validated

    def get_default_configuration(self) -> Dict[str, Any]:
        """Default: limited agent calling with safeguards"""
        return {
            "allowed_operations": ["execute_agent", "execute_team", "followup_execution", "get_execution_status"],
            "allowed_agents": [],
            "allowed_teams": [],
            "max_execution_depth": 2,
            "timeout": 300,
            "wait_for_completion": True,
            "inherit_context": True,
            "max_concurrent_calls": 3,
            "allow_session_continuation": True,
            "streaming_enabled": True,
        }


# Auto-register this skill
register_skill(AgentCommunicationSkill())
