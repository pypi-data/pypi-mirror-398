"""
Pydantic models for planning tool responses

These models ensure type safety and consistent data structures
when tools return information to the planning agent.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AgentModel(BaseModel):
    """Agent information model with full context for planning"""
    id: str
    name: str
    model_id: Optional[str] = Field(default="default")
    description: Optional[str] = None
    status: str
    capabilities: Optional[List[str]] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    llm_config: Dict[str, Any] = Field(default_factory=dict)
    runtime: Optional[str] = None
    team_id: Optional[str] = None
    skills: List[Dict[str, Any]] = Field(default_factory=list)  # Full skill details
    skill_ids: List[str] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    environments: List[Dict[str, Any]] = Field(default_factory=list)
    execution_environment: Optional[Dict[str, Any]] = None  # env_vars, secrets, integration_ids
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    error_message: Optional[str] = None


class TeamMemberModel(BaseModel):
    """Team member information model"""
    id: str
    name: str
    model_id: str = Field(default="default")
    description: Optional[str] = None


class TeamModel(BaseModel):
    """Team information model"""
    id: str
    name: str
    description: Optional[str] = None
    status: str
    agent_count: int = 0
    agents: Optional[List[TeamMemberModel]] = None


class EnvironmentModel(BaseModel):
    """Environment information model"""
    id: str
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: str
    tags: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)


class WorkerQueueModel(BaseModel):
    """Worker queue information model"""
    id: str
    name: str
    display_name: Optional[str] = None
    environment_id: Optional[str] = None
    active_workers: int = 0
    status: str


class ExecutionHistoryModel(BaseModel):
    """Execution history summary model"""
    entity_id: str
    entity_type: str  # "agent" or "team"
    total_executions: int
    completed: int
    failed: int
    success_rate: float
    recent_executions: List[Dict[str, Any]] = Field(default_factory=list)


class SkillModel(BaseModel):
    """Skill/tool information model"""
    id: str
    name: str
    skill_type: str
    description: Optional[str] = None
    enabled: bool = True
    configuration: Dict[str, Any] = Field(default_factory=dict)
