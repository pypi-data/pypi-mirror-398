"""
Multi-tenant agents router with Temporal workflow integration.

This router handles agent CRUD operations and execution submissions.
All operations are scoped to the authenticated organization.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import structlog
import uuid
import httpx
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from control_plane_api.app.lib.temporal_client import get_temporal_client
from control_plane_api.app.lib.mcp_validation import validate_execution_environment_mcp, MCPValidationError
from control_plane_api.app.workflows.agent_execution import AgentExecutionWorkflow, AgentExecutionInput
from control_plane_api.app.routers.projects import get_default_project_id
from control_plane_api.app.lib.validation import validate_agent_for_runtime
from control_plane_api.app.schemas.mcp_schemas import MCPServerConfig
from control_plane_api.app.models import (
    Agent, AgentStatus, Execution, ExecutionStatus, ExecutionType,
    ExecutionTriggerSource, ExecutionParticipant, ParticipantRole,
    Skill, SkillAssociation, AgentEnvironment, Environment, Project,
    ProjectAgent, WorkerQueue
)
from control_plane_api.app.lib.sqlalchemy_utils import model_to_dict, models_to_dict_list

logger = structlog.get_logger()

router = APIRouter()


class ExecutionEnvironment(BaseModel):
    """Execution environment configuration for agents/teams"""
    working_dir: str | None = Field(None, description="Working directory for execution (overrides default workspace)")
    env_vars: dict[str, str] = Field(default_factory=dict, description="Environment variables (key-value pairs)")
    secrets: list[str] = Field(default_factory=list, description="Secret names from Kubiya vault")
    integration_ids: list[str] = Field(default_factory=list, description="Integration UUIDs for delegated credentials")
    mcp_servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict,
        description="MCP (Model Context Protocol) server configurations. Supports stdio, HTTP, and SSE transports."
    )


def get_agent_projects(db: Session, agent_id: str) -> list[dict]:
    """Get all projects an agent belongs to"""
    try:
        # Query project_agents join table with Project relationship
        project_agents = (
            db.query(ProjectAgent)
            .join(Project, ProjectAgent.project_id == Project.id)
            .filter(ProjectAgent.agent_id == agent_id)
            .all()
        )

        projects = []
        for pa in project_agents:
            if pa.project:
                projects.append({
                    "id": str(pa.project.id),
                    "name": pa.project.name,
                    "key": pa.project.key,
                    "description": pa.project.description,
                })

        return projects
    except Exception as e:
        logger.warning("failed_to_fetch_agent_projects", error=str(e), agent_id=agent_id)
        return []


def get_agent_environments(db: Session, agent_id: str) -> list[dict]:
    """Get all environments an agent is assigned to"""
    try:
        # Query agent_environments join table with Environment relationship
        agent_envs = (
            db.query(AgentEnvironment)
            .join(Environment, AgentEnvironment.environment_id == Environment.id)
            .filter(AgentEnvironment.agent_id == agent_id)
            .all()
        )

        environments = []
        for ae in agent_envs:
            env = db.query(Environment).filter(Environment.id == ae.environment_id).first()
            if env:
                environments.append({
                    "id": str(env.id),
                    "name": env.name,
                    "display_name": env.display_name,
                    "status": env.status,
                })

        return environments
    except Exception as e:
        logger.warning("failed_to_fetch_agent_environments", error=str(e), agent_id=agent_id)
        return []


def get_entity_skills(db: Session, organization_id: str, entity_type: str, entity_id: str) -> list[dict]:
    """Get skills associated with an entity"""
    try:
        # Get associations with joined skills
        skill_associations = (
            db.query(SkillAssociation)
            .join(Skill, SkillAssociation.skill_id == Skill.id)
            .filter(
                SkillAssociation.organization_id == organization_id,
                SkillAssociation.entity_type == entity_type,
                SkillAssociation.entity_id == entity_id
            )
            .all()
        )

        skills = []
        for assoc in skill_associations:
            skill = db.query(Skill).filter(Skill.id == assoc.skill_id).first()
            if skill and skill.enabled:
                # Merge configuration with override
                config = skill.configuration or {}
                override = assoc.configuration_override
                if override:
                    config = {**config, **override}

                skills.append({
                    "id": str(skill.id),
                    "name": skill.name,
                    "type": skill.skill_type,
                    "description": skill.description,
                    "enabled": skill.enabled,
                    "configuration": config,
                })

        return skills
    except Exception as e:
        logger.warning("failed_to_fetch_entity_skills", error=str(e), entity_type=entity_type, entity_id=entity_id)
        return []


def get_agent_skills_with_inheritance(db: Session, organization_id: str, agent_id: str, team_id: str | None) -> list[dict]:
    """
    Get all skills for an agent, including those inherited from the team.
    Team skills are inherited by all team members.

    Inheritance order (later overrides earlier):
    1. Team skills (if agent is part of a team)
    2. Agent skills
    """
    seen_ids = set()
    skills = []

    # 1. Get team skills first (if agent is part of a team)
    if team_id:
        try:
            team_skills = get_entity_skills(db, organization_id, "team", team_id)
            for skill in team_skills:
                if skill["id"] not in seen_ids:
                    skills.append(skill)
                    seen_ids.add(skill["id"])
        except Exception as e:
            logger.warning("failed_to_fetch_team_skills_for_agent", error=str(e), team_id=team_id, agent_id=agent_id)

    # 2. Get agent-specific skills (these override team skills if there's a conflict)
    try:
        agent_skills = get_entity_skills(db, organization_id, "agent", agent_id)
        for skill in agent_skills:
            if skill["id"] not in seen_ids:
                skills.append(skill)
                seen_ids.add(skill["id"])
    except Exception as e:
        logger.warning("failed_to_fetch_agent_skills", error=str(e), agent_id=agent_id)

    return skills


# Pydantic schemas
class AgentCreate(BaseModel):
    name: str = Field(..., description="Agent name")
    description: str | None = Field(None, description="Agent description")
    system_prompt: str | None = Field(None, description="System prompt for the agent")
    capabilities: list = Field(default_factory=list, description="Agent capabilities")
    configuration: dict = Field(default_factory=dict, description="Agent configuration")
    model_id: str | None = Field(None, description="LiteLLM model identifier")
    model: str | None = Field(None, description="Model identifier (alias for model_id)")
    llm_config: dict = Field(default_factory=dict, description="Model-specific configuration")
    runtime: str | None = Field(None, description="Runtime type: 'default' (Agno) or 'claude_code' (Claude Code SDK)")
    runner_name: str | None = Field(None, description="Preferred runner for this agent")
    team_id: str | None = Field(None, description="Team ID to assign this agent to")
    environment_ids: list[str] = Field(default_factory=list, description="Environment IDs to deploy this agent to")
    skill_ids: list[str] = Field(default_factory=list, description="Tool set IDs to associate with this agent")
    skill_configurations: dict[str, dict] = Field(default_factory=dict, description="Tool set configurations keyed by skill ID")
    execution_environment: ExecutionEnvironment | None = Field(None, description="Execution environment: env vars, secrets, integrations")


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    status: str | None = None
    capabilities: list | None = None
    configuration: dict | None = None
    state: dict | None = None
    model_id: str | None = None
    model: str | None = None  # Alias for model_id
    llm_config: dict | None = None
    runtime: str | None = None
    runner_name: str | None = None
    team_id: str | None = None
    environment_ids: list[str] | None = None
    skill_ids: list[str] | None = None
    skill_configurations: dict[str, dict] | None = None
    execution_environment: ExecutionEnvironment | None = None


class AgentResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: str | None
    system_prompt: str | None
    status: str
    capabilities: list
    configuration: dict
    model_id: str | None
    llm_config: dict
    runtime: str | None
    runner_name: str | None
    team_id: str | None
    created_at: str
    updated_at: str
    last_active_at: str | None
    state: dict
    error_message: str | None
    projects: list[dict] = Field(default_factory=list, description="Projects this agent belongs to")
    environments: list[dict] = Field(default_factory=list, description="Environments this agent is deployed to")
    skill_ids: list[str] | None = Field(default_factory=list, description="IDs of associated skills")
    skills: list[dict] | None = Field(default_factory=list, description="Associated skills with details")
    execution_environment: ExecutionEnvironment | None = None


class AgentExecutionRequest(BaseModel):
    prompt: str = Field(..., description="The prompt to execute")
    system_prompt: str | None = Field(None, description="Optional system prompt")
    stream: bool = Field(False, description="Whether to stream the response")
    worker_queue_id: str = Field(..., description="Worker queue ID (UUID) to route execution to - REQUIRED")
    user_metadata: dict | None = Field(None, description="User attribution metadata (optional, auto-filled from token)")
    execution_environment: ExecutionEnvironment | None = Field(None, description="Optional execution environment settings (working_dir, etc.)")


class AgentExecutionResponse(BaseModel):
    execution_id: str
    workflow_id: str
    status: str
    message: str


def get_or_create_default_shell_skill(db: Session, organization_id: str) -> Optional[str]:
    """
    Get or create the default shell skill for an organization.

    Args:
        db: Database session
        organization_id: Organization ID

    Returns:
        Shell skill ID if found/created, None if failed
    """
    try:
        # First, try to find existing shell skill
        existing_skill = (
            db.query(Skill)
            .filter(
                Skill.organization_id == organization_id,
                Skill.skill_type == "shell",
                Skill.enabled == True
            )
            .first()
        )

        if existing_skill:
            logger.info(
                "found_existing_shell_skill",
                skill_id=str(existing_skill.id),
                org_id=organization_id
            )
            return str(existing_skill.id)

        # Create default shell skill if none exists
        skill_id = uuid.uuid4()
        now = datetime.utcnow()

        skill = Skill(
            id=skill_id,
            organization_id=organization_id,
            name="Shell",
            skill_type="shell",
            description="Execute shell commands on the system",
            icon="Terminal",
            enabled=True,
            configuration={},
            created_at=now,
            updated_at=now,
        )

        db.add(skill)
        db.commit()
        db.refresh(skill)

        logger.info(
            "default_shell_skill_created",
            skill_id=str(skill_id),
            org_id=organization_id
        )

        return str(skill_id)
    except Exception as e:
        db.rollback()
        logger.error(
            "failed_to_get_or_create_shell_skill",
            error=str(e),
            org_id=organization_id
        )
        return None


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Create a new agent in the organization"""
    try:

        agent_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        # Handle model field - prefer 'model' over 'model_id' for backward compatibility
        model_id = agent_data.model or agent_data.model_id

        # Validate model_id against runtime type
        runtime = agent_data.runtime or "default"
        is_valid, errors = validate_agent_for_runtime(
            runtime_type=runtime,
            model_id=model_id,
            agent_config=agent_data.configuration,
            system_prompt=agent_data.system_prompt
        )
        if not is_valid:
            error_msg = "Agent validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
            logger.error(
                "agent_validation_failed",
                runtime=runtime,
                model_id=model_id,
                errors=errors,
                org_id=organization["id"]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Validate MCP server configuration if present
        if agent_data.execution_environment and agent_data.execution_environment.mcp_servers:
            try:
                mcp_validation = validate_execution_environment_mcp(
                    agent_data.execution_environment.model_dump(by_alias=True),
                    strict=False  # Non-strict: allow warnings for missing secrets/env vars
                )
                if not mcp_validation["valid"]:
                    error_msg = "MCP configuration validation failed:\n" + "\n".join(f"  - {err}" for err in mcp_validation["errors"])
                    logger.error(
                        "mcp_validation_failed",
                        errors=mcp_validation["errors"],
                        warnings=mcp_validation["warnings"],
                        org_id=organization["id"]
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_msg
                    )
                # Log warnings if any
                if mcp_validation["warnings"]:
                    logger.warning(
                        "mcp_validation_warnings",
                        warnings=mcp_validation["warnings"],
                        required_secrets=mcp_validation["required_secrets"],
                        required_env_vars=mcp_validation["required_env_vars"],
                        org_id=organization["id"]
                    )
            except MCPValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        # Store system_prompt in configuration for persistence
        configuration = agent_data.configuration.copy() if agent_data.configuration else {}
        if agent_data.system_prompt is not None:
            configuration["system_prompt"] = agent_data.system_prompt

        # Create Agent object
        agent = Agent(
            id=agent_id,
            organization_id=organization["id"],
            name=agent_data.name,
            description=agent_data.description,
            status=AgentStatus.IDLE,
            capabilities=agent_data.capabilities,
            configuration=configuration,
            model_id=model_id,
            model_config=agent_data.llm_config,
            runtime=agent_data.runtime or "default",
            runner_name=agent_data.runner_name,
            team_id=agent_data.team_id,
            execution_environment=agent_data.execution_environment.model_dump(by_alias=True) if agent_data.execution_environment else {},
            state={},
            created_at=now,
            updated_at=now,
        )

        db.add(agent)
        db.commit()
        db.refresh(agent)

        # Automatically assign agent to the default project
        default_project_id = get_default_project_id(db, organization)
        if default_project_id:
            try:
                project_agent = ProjectAgent(
                    id=uuid.uuid4(),
                    project_id=default_project_id,
                    agent_id=agent_id,
                    role=None,
                    added_at=now,
                    added_by=organization.get("user_id"),
                )
                db.add(project_agent)
                db.commit()
                logger.info(
                    "agent_added_to_default_project",
                    agent_id=str(agent_id),
                    project_id=default_project_id,
                    org_id=organization["id"]
                )
            except Exception as e:
                db.rollback()
                logger.warning(
                    "failed_to_add_agent_to_default_project",
                    error=str(e),
                    agent_id=str(agent_id),
                    org_id=organization["id"]
                )

        # VALIDATION: Ensure at least one skill is associated with the agent
        # Agents without skills are non-functional
        if not agent_data.skill_ids or len(agent_data.skill_ids) == 0:
            # Auto-add shell skill as default
            shell_skill_id = get_or_create_default_shell_skill(db, organization["id"])

            if shell_skill_id:
                agent_data.skill_ids = [shell_skill_id]
                logger.info(
                    "auto_added_shell_skill",
                    agent_id=str(agent_id),
                    org_id=organization["id"],
                    reason="no_skills_provided"
                )
            else:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one skill is required to create an agent. Unable to add default shell skill. Please add a skill manually."
                )

        # Create skill associations if skills were provided
        if agent_data.skill_ids:
            try:
                for skill_id in agent_data.skill_ids:
                    config_override = agent_data.skill_configurations.get(skill_id, {})

                    skill_association = SkillAssociation(
                        id=uuid.uuid4(),
                        organization_id=organization["id"],
                        skill_id=skill_id,
                        entity_type="agent",
                        entity_id=agent_id,
                        configuration_override=config_override,
                        created_at=now,
                    )
                    db.add(skill_association)

                db.commit()
                logger.info(
                    "agent_skills_associated",
                    agent_id=str(agent_id),
                    skill_count=len(agent_data.skill_ids),
                    org_id=organization["id"]
                )
            except Exception as e:
                db.rollback()
                logger.warning(
                    "failed_to_associate_agent_skills",
                    error=str(e),
                    agent_id=str(agent_id),
                    org_id=organization["id"]
                )

        # Create environment associations if environments were provided
        if agent_data.environment_ids:
            try:
                for environment_id in agent_data.environment_ids:
                    agent_env = AgentEnvironment(
                        id=uuid.uuid4(),
                        agent_id=agent_id,
                        environment_id=environment_id,
                        organization_id=organization["id"],
                        assigned_at=now,
                        assigned_by=organization.get("user_id"),
                    )
                    db.add(agent_env)

                db.commit()
                logger.info(
                    "agent_environments_associated",
                    agent_id=str(agent_id),
                    environment_count=len(agent_data.environment_ids),
                    org_id=organization["id"]
                )
            except Exception as e:
                db.rollback()
                logger.warning(
                    "failed_to_associate_agent_environments",
                    error=str(e),
                    agent_id=str(agent_id),
                    org_id=organization["id"]
                )

        logger.info(
            "agent_created",
            agent_id=str(agent_id),
            agent_name=agent_data.name,
            org_id=organization["id"],
            org_slug=organization["slug"]
        )

        # Get skills with team inheritance
        team_id = str(agent.team_id) if agent.team_id else None
        skills = get_agent_skills_with_inheritance(db, organization["id"], str(agent_id), team_id)

        # Extract system_prompt from configuration
        configuration = agent.configuration or {}
        system_prompt = configuration.get("system_prompt")

        return AgentResponse(
            id=str(agent.id),
            organization_id=agent.organization_id,
            name=agent.name,
            description=agent.description,
            system_prompt=system_prompt,
            status=agent.status,
            capabilities=agent.capabilities,
            configuration=agent.configuration,
            model_id=agent.model_id,
            llm_config=agent.model_config or {},
            runtime=agent.runtime,
            runner_name=agent.runner_name,
            team_id=str(agent.team_id) if agent.team_id else None,
            created_at=agent.created_at.isoformat() if agent.created_at else None,
            updated_at=agent.updated_at.isoformat() if agent.updated_at else None,
            last_active_at=agent.last_active_at.isoformat() if agent.last_active_at else None,
            state=agent.state or {},
            error_message=agent.error_message,
            projects=get_agent_projects(db, str(agent_id)),
            environments=get_agent_environments(db, str(agent_id)),
            skill_ids=[ts["id"] for ts in skills],
            skills=skills,
            execution_environment=(
                ExecutionEnvironment(**agent.execution_environment)
                if agent.execution_environment
                else None
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("agent_creation_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status_filter: str | None = None,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List all agents in the organization"""
    try:
        # Query agents for this organization
        query = db.query(Agent).filter(Agent.organization_id == organization["id"])

        if status_filter:
            query = query.filter(Agent.status == status_filter)

        agents_list = query.order_by(Agent.created_at.desc()).offset(skip).limit(limit).all()

        if not agents_list:
            return []

        # Batch fetch all agent-project relationships in one query
        agent_ids = [str(agent.id) for agent in agents_list]
        from sqlalchemy import UUID as SQLUUID
        agent_project_associations = (
            db.query(ProjectAgent)
            .join(Project, ProjectAgent.project_id == Project.id)
            .filter(ProjectAgent.agent_id.in_([agent.id for agent in agents_list]))
            .all()
        )

        # Group projects by agent_id
        projects_by_agent = {}
        for pa in agent_project_associations:
            agent_id = str(pa.agent_id)
            if pa.project:
                if agent_id not in projects_by_agent:
                    projects_by_agent[agent_id] = []
                projects_by_agent[agent_id].append({
                    "id": str(pa.project.id),
                    "name": pa.project.name,
                    "key": pa.project.key,
                    "description": pa.project.description,
                })

        # Batch fetch environments for all agents
        agent_env_associations = (
            db.query(AgentEnvironment)
            .join(Environment, AgentEnvironment.environment_id == Environment.id)
            .filter(AgentEnvironment.agent_id.in_([agent.id for agent in agents_list]))
            .all()
        )

        # Group environments by agent_id
        environments_by_agent = {}
        for ae in agent_env_associations:
            agent_id = str(ae.agent_id)
            env = db.query(Environment).filter(Environment.id == ae.environment_id).first()
            if env:
                if agent_id not in environments_by_agent:
                    environments_by_agent[agent_id] = []
                environments_by_agent[agent_id].append({
                    "id": str(env.id),
                    "name": env.name,
                    "display_name": env.display_name,
                    "status": env.status,
                })

        # Batch fetch skills for all agents (including team inheritance)
        # Collect all unique team IDs
        team_ids = set()
        for agent in agents_list:
            if agent.team_id:
                team_ids.add(agent.team_id)

        # BATCH FETCH: Get all team skills in one query
        team_skills = {}
        if team_ids:
            team_skill_associations = (
                db.query(SkillAssociation)
                .join(Skill, SkillAssociation.skill_id == Skill.id)
                .filter(
                    SkillAssociation.organization_id == organization["id"],
                    SkillAssociation.entity_type == "team",
                    SkillAssociation.entity_id.in_(team_ids)
                )
                .all()
            )

            for assoc in team_skill_associations:
                team_id = str(assoc.entity_id)
                skill = db.query(Skill).filter(Skill.id == assoc.skill_id).first()
                if skill and skill.enabled:
                    if team_id not in team_skills:
                        team_skills[team_id] = []

                    config = skill.configuration or {}
                    override = assoc.configuration_override
                    if override:
                        config = {**config, **override}

                    team_skills[team_id].append({
                        "id": str(skill.id),
                        "name": skill.name,
                        "type": skill.skill_type,
                        "description": skill.description,
                        "enabled": skill.enabled,
                        "configuration": config,
                    })

        # BATCH FETCH: Get all agent skills in one query
        agent_skill_associations = (
            db.query(SkillAssociation)
            .join(Skill, SkillAssociation.skill_id == Skill.id)
            .filter(
                SkillAssociation.organization_id == organization["id"],
                SkillAssociation.entity_type == "agent",
                SkillAssociation.entity_id.in_([agent.id for agent in agents_list])
            )
            .all()
        )

        agent_direct_skills = {}
        for assoc in agent_skill_associations:
            agent_id = str(assoc.entity_id)
            skill = db.query(Skill).filter(Skill.id == assoc.skill_id).first()
            if skill and skill.enabled:
                if agent_id not in agent_direct_skills:
                    agent_direct_skills[agent_id] = []

                config = skill.configuration or {}
                override = assoc.configuration_override
                if override:
                    config = {**config, **override}

                agent_direct_skills[agent_id].append({
                    "id": str(skill.id),
                    "name": skill.name,
                    "type": skill.skill_type,
                    "description": skill.description,
                    "enabled": skill.enabled,
                    "configuration": config,
                })

        # Combine team and agent skills with proper inheritance
        skills_by_agent = {}
        for agent in agents_list:
            agent_id = str(agent.id)
            team_id = str(agent.team_id) if agent.team_id else None

            # Start with empty list
            combined_skills = []
            seen_ids = set()

            # Add team skills first (if agent is part of a team)
            if team_id and team_id in team_skills:
                for skill in team_skills[team_id]:
                    if skill["id"] not in seen_ids:
                        combined_skills.append(skill)
                        seen_ids.add(skill["id"])

            # Add agent-specific skills (these override team skills)
            if agent_id in agent_direct_skills:
                for skill in agent_direct_skills[agent_id]:
                    if skill["id"] not in seen_ids:
                        combined_skills.append(skill)
                        seen_ids.add(skill["id"])

            skills_by_agent[agent_id] = combined_skills

        agents = []
        for agent in agents_list:
            # Extract system_prompt from configuration
            configuration = agent.configuration or {}
            system_prompt = configuration.get("system_prompt")

            agent_id = str(agent.id)

            agents.append(AgentResponse(
                id=agent_id,
                organization_id=agent.organization_id,
                name=agent.name,
                description=agent.description,
                system_prompt=system_prompt,
                status=agent.status,
                capabilities=agent.capabilities,
                configuration=agent.configuration,
                model_id=agent.model_id,
                llm_config=agent.model_config or {},
                runtime=agent.runtime,
                runner_name=agent.runner_name,
                team_id=str(agent.team_id) if agent.team_id else None,
                created_at=agent.created_at.isoformat() if agent.created_at else None,
                updated_at=agent.updated_at.isoformat() if agent.updated_at else None,
                last_active_at=agent.last_active_at.isoformat() if agent.last_active_at else None,
                state=agent.state or {},
                error_message=agent.error_message,
                projects=projects_by_agent.get(agent_id, []),
                environments=environments_by_agent.get(agent_id, []),
                skill_ids=[ts["id"] for ts in skills_by_agent.get(agent_id, [])],
                skills=skills_by_agent.get(agent_id, []),
                execution_environment=(
                    ExecutionEnvironment(**agent.execution_environment)
                    if agent.execution_environment
                    else None
                ),
            ))

        logger.info(
            "agents_listed",
            count=len(agents),
            org_id=organization["id"],
            org_slug=organization["slug"]
        )

        return agents

    except Exception as e:
        logger.error("agents_list_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get a specific agent by ID"""
    try:
        # Query agent
        agent = db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.organization_id == organization["id"]
        ).first()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # DIAGNOSTIC: Log raw agent data from database
        logger.info(
            "get_agent_database_result",
            agent_id=agent_id,
            has_execution_environment=agent.execution_environment is not None,
            execution_environment_type=type(agent.execution_environment).__name__ if agent.execution_environment else None,
            execution_environment_keys=list(agent.execution_environment.keys()) if isinstance(agent.execution_environment, dict) else None,
            has_mcp_servers=bool(agent.execution_environment.get("mcp_servers")) if isinstance(agent.execution_environment, dict) else False,
            org_id=organization["id"]
        )

        # Get skills with team inheritance
        team_id = str(agent.team_id) if agent.team_id else None
        skills = get_agent_skills_with_inheritance(db, organization["id"], str(agent_id), team_id)

        # Parse execution_environment if it exists
        execution_env = None
        if agent.execution_environment:
            try:
                execution_env = ExecutionEnvironment(**agent.execution_environment)
                # DIAGNOSTIC: Log parsed execution_environment
                logger.info(
                    "get_agent_execution_env_parsed",
                    agent_id=agent_id,
                    has_mcp_servers=bool(execution_env.mcp_servers) if execution_env else False,
                    mcp_server_count=len(execution_env.mcp_servers) if execution_env and execution_env.mcp_servers else 0,
                    org_id=organization["id"]
                )
            except Exception as e:
                logger.error(
                    "get_agent_execution_env_parse_failed",
                    agent_id=agent_id,
                    error=str(e),
                    raw_value=agent.execution_environment,
                    org_id=organization["id"]
                )
                execution_env = None

        # Extract system_prompt from configuration
        configuration = agent.configuration or {}
        system_prompt = configuration.get("system_prompt")

        return AgentResponse(
            id=str(agent.id),
            organization_id=agent.organization_id,
            name=agent.name,
            description=agent.description,
            system_prompt=system_prompt,
            status=agent.status,
            capabilities=agent.capabilities,
            configuration=agent.configuration,
            model_id=agent.model_id,
            llm_config=agent.model_config or {},
            runtime=agent.runtime,
            runner_name=agent.runner_name,
            team_id=str(agent.team_id) if agent.team_id else None,
            created_at=agent.created_at.isoformat() if agent.created_at else None,
            updated_at=agent.updated_at.isoformat() if agent.updated_at else None,
            last_active_at=agent.last_active_at.isoformat() if agent.last_active_at else None,
            state=agent.state or {},
            error_message=agent.error_message,
            projects=get_agent_projects(db, str(agent_id)),
            environments=get_agent_environments(db, str(agent_id)),
            skill_ids=[ts["id"] for ts in skills],
            skills=skills,
            execution_environment=execution_env,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("agent_get_failed", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent: {str(e)}"
        )


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Update an agent"""
    try:
        # Check if agent exists and belongs to organization
        agent = db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.organization_id == organization["id"]
        ).first()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Build update dict
        update_data = agent_data.model_dump(exclude_unset=True)

        # DIAGNOSTIC: Log full request data
        logger.info(
            "update_agent_request",
            agent_id=agent_id,
            has_execution_environment="execution_environment" in update_data,
            execution_environment_keys=list(update_data.get("execution_environment", {}).keys()) if isinstance(update_data.get("execution_environment"), dict) else None,
            has_mcp_servers=bool(update_data.get("execution_environment", {}).get("mcp_servers")) if isinstance(update_data.get("execution_environment"), dict) else False,
            mcp_server_count=len(update_data.get("execution_environment", {}).get("mcp_servers", {})) if isinstance(update_data.get("execution_environment"), dict) else 0,
            org_id=organization["id"]
        )

        # Extract skill data before database update
        skill_ids = update_data.pop("skill_ids", None)
        skill_configurations = update_data.pop("skill_configurations", None)

        # Extract environment data before database update (many-to-many via junction table)
        environment_ids = update_data.pop("environment_ids", None)

        # Extract system_prompt and store it in configuration
        system_prompt = update_data.pop("system_prompt", None)
        if system_prompt is not None:
            # Merge system_prompt into existing configuration
            existing_config = agent.configuration or {}
            merged_config = {**existing_config, "system_prompt": system_prompt}
            update_data["configuration"] = merged_config

        # Handle model field - prefer 'model' over 'model_id' for backward compatibility
        if "model" in update_data and update_data["model"]:
            update_data["model_id"] = update_data.pop("model")
        elif "model" in update_data:
            # Remove null model field
            update_data.pop("model")

        # Map llm_config to model_config for database
        if "llm_config" in update_data:
            update_data["model_config"] = update_data.pop("llm_config")

        # Validate model_id and runtime if being updated
        if "model_id" in update_data or "runtime" in update_data:
            # Merge updates with existing values
            final_model_id = update_data.get("model_id", agent.model_id)
            final_runtime = update_data.get("runtime", agent.runtime or "default")
            final_config = update_data.get("configuration", agent.configuration or {})

            is_valid, errors = validate_agent_for_runtime(
                runtime_type=final_runtime,
                model_id=final_model_id,
                agent_config=final_config,
                system_prompt=system_prompt
            )
            if not is_valid:
                error_msg = "Agent validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
                logger.error(
                    "agent_validation_failed",
                    runtime=final_runtime,
                    model_id=final_model_id,
                    errors=errors,
                    org_id=organization["id"]
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

        # Handle execution_environment - convert to dict if present
        if "execution_environment" in update_data and update_data["execution_environment"]:
            if isinstance(update_data["execution_environment"], ExecutionEnvironment):
                update_data["execution_environment"] = update_data["execution_environment"].model_dump(by_alias=True)
            # If None, keep as None to preserve existing value

        # Validate MCP server configuration if being updated
        if "execution_environment" in update_data and update_data["execution_environment"]:
            exec_env_dict = update_data["execution_environment"]
            if exec_env_dict and exec_env_dict.get("mcp_servers"):
                try:
                    mcp_validation = validate_execution_environment_mcp(
                        exec_env_dict,
                        strict=False
                    )

                    if not mcp_validation["valid"]:
                        error_msg = "MCP configuration validation failed:\n" + "\n".join(
                            f"  - {err}" for err in mcp_validation["errors"]
                        )
                        logger.error(
                            "mcp_validation_failed",
                            agent_id=agent_id,
                            errors=mcp_validation["errors"],
                            org_id=organization["id"]
                        )
                        raise HTTPException(status_code=400, detail=error_msg)

                    if mcp_validation["warnings"]:
                        logger.warning(
                            "mcp_validation_warnings",
                            agent_id=agent_id,
                            warnings=mcp_validation["warnings"],
                            required_secrets=mcp_validation.get("required_secrets", []),
                            required_env_vars=mcp_validation.get("required_env_vars", []),
                            org_id=organization["id"]
                        )

                    logger.info(
                        "mcp_validation_passed",
                        agent_id=agent_id,
                        server_count=len(exec_env_dict.get("mcp_servers", {})),
                        required_secrets=mcp_validation.get("required_secrets", []),
                        required_env_vars=mcp_validation.get("required_env_vars", []),
                        org_id=organization["id"]
                    )
                except MCPValidationError as e:
                    logger.error(
                        "mcp_validation_error",
                        agent_id=agent_id,
                        error=str(e),
                        org_id=organization["id"]
                    )
                    raise HTTPException(status_code=400, detail=str(e))

        # Note: skill_ids is not stored in agents table - skills are tracked via skill_associations junction table
        # The skill associations will be updated separately below if skill_ids was provided

        update_data["updated_at"] = datetime.utcnow()

        # DIAGNOSTIC: Log what's being sent to database
        logger.info(
            "update_agent_database_update",
            agent_id=agent_id,
            update_keys=list(update_data.keys()),
            has_execution_environment="execution_environment" in update_data,
            execution_environment_value=update_data.get("execution_environment"),
            org_id=organization["id"]
        )

        # Update agent fields
        for key, value in update_data.items():
            setattr(agent, key, value)

        db.commit()
        db.refresh(agent)

        # DIAGNOSTIC: Log database result
        logger.info(
            "update_agent_database_result",
            agent_id=agent_id,
            success=True,
            returned_execution_environment=agent.execution_environment,
            org_id=organization["id"]
        )

        # Update skill associations if skill_ids was provided
        if skill_ids is not None:
            # VALIDATION: Prevent removing all skills from an agent
            if len(skill_ids) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove all skills from an agent. At least one skill is required for agent functionality."
                )

            try:
                # Delete existing associations (scoped to organization)
                db.query(SkillAssociation).filter(
                    SkillAssociation.organization_id == organization["id"],
                    SkillAssociation.entity_type == "agent",
                    SkillAssociation.entity_id == agent_id
                ).delete()

                # Create new associations
                now = datetime.utcnow()
                for skill_id in skill_ids:
                    config_override = (skill_configurations or {}).get(skill_id, {})

                    skill_association = SkillAssociation(
                        id=uuid.uuid4(),
                        organization_id=organization["id"],
                        skill_id=skill_id,
                        entity_type="agent",
                        entity_id=agent_id,
                        configuration_override=config_override,
                        created_at=now,
                    )
                    db.add(skill_association)

                db.commit()
                logger.info(
                    "agent_skills_updated",
                    agent_id=agent_id,
                    skill_count=len(skill_ids),
                    org_id=organization["id"]
                )
            except Exception as e:
                db.rollback()
                logger.error(
                    "failed_to_update_agent_skills",
                    error=str(e),
                    agent_id=agent_id,
                    org_id=organization["id"]
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update agent skills: {str(e)}"
                )

        # Update environment associations if environment_ids was provided
        if environment_ids is not None:
            try:
                # Delete existing environment associations
                db.query(AgentEnvironment).filter(
                    AgentEnvironment.agent_id == agent_id
                ).delete()

                # Create new environment associations
                for environment_id in environment_ids:
                    agent_env = AgentEnvironment(
                        id=uuid.uuid4(),
                        agent_id=agent_id,
                        environment_id=environment_id,
                        organization_id=organization["id"],
                        assigned_at=datetime.utcnow(),
                    )
                    db.add(agent_env)

                db.commit()
                logger.info(
                    "agent_environments_updated",
                    agent_id=agent_id,
                    environment_count=len(environment_ids),
                    org_id=organization["id"]
                )
            except Exception as e:
                db.rollback()
                logger.warning(
                    "failed_to_update_agent_environments",
                    error=str(e),
                    agent_id=agent_id,
                    org_id=organization["id"]
                )

        logger.info(
            "agent_updated",
            agent_id=agent_id,
            org_id=organization["id"],
            fields_updated=list(update_data.keys())
        )

        # Get skills with team inheritance
        team_id = str(agent.team_id) if agent.team_id else None
        skills = get_agent_skills_with_inheritance(db, organization["id"], agent_id, team_id)

        # Parse execution_environment if it exists
        execution_env = None
        if agent.execution_environment:
            try:
                execution_env = ExecutionEnvironment(**agent.execution_environment)
            except Exception:
                execution_env = None

        # Extract system_prompt from configuration
        configuration = agent.configuration or {}
        system_prompt = configuration.get("system_prompt")

        return AgentResponse(
            id=str(agent.id),
            organization_id=agent.organization_id,
            name=agent.name,
            description=agent.description,
            system_prompt=system_prompt,
            status=agent.status,
            capabilities=agent.capabilities,
            configuration=agent.configuration,
            model_id=agent.model_id,
            llm_config=agent.model_config or {},
            runtime=agent.runtime,
            runner_name=agent.runner_name,
            team_id=str(agent.team_id) if agent.team_id else None,
            created_at=agent.created_at.isoformat() if agent.created_at else None,
            updated_at=agent.updated_at.isoformat() if agent.updated_at else None,
            last_active_at=agent.last_active_at.isoformat() if agent.last_active_at else None,
            state=agent.state or {},
            error_message=agent.error_message,
            projects=get_agent_projects(db, agent_id),
            environments=get_agent_environments(db, agent_id),
            skill_ids=[ts["id"] for ts in skills],
            skills=skills,
            execution_environment=execution_env,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("agent_update_failed", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Delete an agent"""
    try:
        # Find the agent first
        agent = db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.organization_id == organization["id"]
        ).first()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Delete the agent (cascading deletes will handle related records)
        db.delete(agent)
        db.commit()

        logger.info("agent_deleted", agent_id=agent_id, org_id=organization["id"])

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error("agent_delete_failed", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {str(e)}"
        )


@router.post("/{agent_id}/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    agent_id: str,
    execution_request: AgentExecutionRequest,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Execute an agent by submitting to Temporal workflow.

    This creates an execution record and starts a Temporal workflow.
    The actual execution happens asynchronously on the Temporal worker.

    The runner_name should come from the Composer UI where user selects
    from available runners (fetched from Kubiya API /api/v1/runners).
    """
    try:
        # Get agent details
        agent = db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.organization_id == organization["id"]
        ).first()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Create execution record
        execution_id = uuid.uuid4()
        now = datetime.utcnow()

        # Validate and get worker queue
        worker_queue_id = execution_request.worker_queue_id

        worker_queue = db.query(WorkerQueue).filter(
            WorkerQueue.id == worker_queue_id,
            WorkerQueue.organization_id == organization["id"]
        ).first()

        if not worker_queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Worker queue '{worker_queue_id}' not found. Please select a valid worker queue."
            )

        # Check if queue has active workers
        if worker_queue.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Worker queue '{worker_queue.name}' is not active"
            )

        # Extract user metadata - ALWAYS use JWT-decoded organization data as source of truth
        user_metadata = execution_request.user_metadata or {}
        # Override with JWT data (user can't spoof their identity)
        user_metadata["user_id"] = organization.get("user_id")
        user_metadata["user_email"] = organization.get("user_email")
        user_metadata["user_name"] = organization.get("user_name")
        # Keep user_avatar from request if provided (not in JWT)
        if not user_metadata.get("user_avatar"):
            user_metadata["user_avatar"] = None

        execution = Execution(
            id=execution_id,
            organization_id=organization["id"],
            execution_type=ExecutionType.AGENT,
            entity_id=agent_id,
            entity_name=agent.name,
            prompt=execution_request.prompt,
            system_prompt=execution_request.system_prompt,
            status=ExecutionStatus.PENDING,
            worker_queue_id=worker_queue_id,
            runner_name=worker_queue.name,  # Store queue name for display
            user_id=user_metadata.get("user_id"),
            user_name=user_metadata.get("user_name"),
            user_email=user_metadata.get("user_email"),
            user_avatar=user_metadata.get("user_avatar"),
            usage={},
            execution_metadata={
                "kubiya_org_id": organization["id"],
                "kubiya_org_name": organization["name"],
                "worker_queue_name": worker_queue.display_name or worker_queue.name,
            },
            created_at=now,
            updated_at=now,
        )

        db.add(execution)
        db.commit()
        db.refresh(execution)

        # Add creator as the first participant (owner role) for multiplayer support
        user_id = user_metadata.get("user_id")
        if user_id:
            try:
                participant = ExecutionParticipant(
                    id=uuid.uuid4(),
                    execution_id=execution_id,
                    organization_id=organization["id"],
                    user_id=user_id,
                    user_name=user_metadata.get("user_name"),
                    user_email=user_metadata.get("user_email"),
                    user_avatar=user_metadata.get("user_avatar"),
                    role=ParticipantRole.OWNER,
                )
                db.add(participant)
                db.commit()
                logger.info(
                    "owner_participant_added",
                    execution_id=str(execution_id),
                    user_id=user_id,
                )
            except Exception as participant_error:
                db.rollback()
                logger.warning(
                    "failed_to_add_owner_participant",
                    error=str(participant_error),
                    execution_id=str(execution_id),
                )
                # Don't fail execution creation if participant tracking fails

        # Get resolved execution environment with templates compiled
        # This includes MCP servers with all {{.secret.x}} and {{.env.X}} resolved
        # Call internal function directly to avoid HTTP/auth issues
        resolved_env = {}  # Initialize to empty dict to avoid UnboundLocalError
        try:
            from control_plane_api.app.routers.execution_environment import resolve_agent_execution_environment_internal

            # Get token from request
            token = request.state.kubiya_token

            resolved_env = await resolve_agent_execution_environment_internal(
                agent_id=agent_id,
                org_id=organization["id"],
                db=db,
                token=token
            )

            mcp_servers = resolved_env.get("mcp_servers", {})
            resolved_system_prompt = resolved_env.get("system_prompt")
            resolved_description = resolved_env.get("description")

            # DEBUG: Log detailed MCP server info
            logger.info(
                "🔍 DEBUG: execution_environment_resolved_for_execution",
                agent_id=agent_id[:8],
                mcp_server_count=len(mcp_servers),
                mcp_server_names=list(mcp_servers.keys()) if mcp_servers else [],
                has_resolved_prompt=bool(resolved_system_prompt)
            )

            if mcp_servers:
                for server_name, server_config in mcp_servers.items():
                    logger.info(
                        "🔍 DEBUG: MCP server config from API",
                        server_name=server_name,
                        has_url="url" in server_config,
                        has_headers="headers" in server_config,
                        has_transport="transport_type" in server_config or "type" in server_config
                    )
            else:
                logger.warning(
                    "🔍 DEBUG: NO MCP SERVERS returned from execution env resolution",
                    agent_id=agent_id[:8],
                    resolved_env_keys=list(resolved_env.keys())
                )

        except Exception as e:
            logger.error(
                "execution_environment_resolution_error",
                agent_id=agent_id[:8],
                error=str(e),
                exc_info=True
            )
            # Don't fallback to old configuration.mcpServers format
            # MCP servers should only come from execution_environment.mcp_servers
            agent_configuration = agent.configuration or {}
            if "mcpServers" in agent_configuration:
                logger.warning(
                    "ignoring_legacy_mcp_servers_in_configuration",
                    agent_id=agent_id[:8],
                    legacy_servers=list(agent_configuration.get("mcpServers", {}).keys()),
                    recommendation="Move MCP servers to execution_environment.mcp_servers"
                )
            mcp_servers = {}  # Don't use old format
            resolved_system_prompt = None
            resolved_description = None

        # Use resolved system prompt if available, otherwise use original
        agent_configuration = agent.configuration or {}

        # Override agent_config with execution_environment.working_dir if provided
        if execution_request.execution_environment and execution_request.execution_environment.working_dir:
            agent_configuration = agent_configuration.copy()
            agent_configuration["cwd"] = execution_request.execution_environment.working_dir
            logger.info(
                "execution_working_dir_override",
                execution_id=str(execution_id),
                working_dir=execution_request.execution_environment.working_dir,
            )

        # Submit to Temporal workflow
        # Task queue is the worker queue UUID
        task_queue = str(worker_queue_id)

        # Get org-specific Temporal credentials and client
        from control_plane_api.app.lib.temporal_credentials_service import get_temporal_credentials_for_org
        from control_plane_api.app.lib.temporal_client import get_temporal_client_for_org

        token = request.state.kubiya_token
        temporal_credentials = await get_temporal_credentials_for_org(
            org_id=organization["id"],
            token=token,
            use_fallback=True  # Enable fallback during migration
        )

        # Create org-specific Temporal client
        temporal_client = await get_temporal_client_for_org(
            namespace=temporal_credentials["namespace"],
            api_key=temporal_credentials["api_key"],
            host=temporal_credentials["host"],
        )

        # Start workflow
        # Use resolved system prompt (with templates compiled) if available
        # Priority: request > resolved > configuration > agent.system_prompt
        system_prompt = (
            execution_request.system_prompt or
            resolved_system_prompt or
            agent_configuration.get("system_prompt") or
            agent.system_prompt
        )

        # Get API key from Authorization header
        auth_header = request.headers.get("authorization", "")
        api_key = auth_header.replace("UserKey ", "").replace("Bearer ", "") if auth_header else None

        # Get control plane URL from request
        control_plane_url = str(request.base_url).rstrip("/")

        # CRITICAL: Use real-time timestamp for initial message to ensure chronological ordering
        # This prevents timestamp mismatches between initial and follow-up messages
        initial_timestamp = datetime.now(timezone.utc).isoformat()

        workflow_input = AgentExecutionInput(
            execution_id=str(execution_id),
            agent_id=str(agent_id),
            organization_id=organization["id"],
            prompt=execution_request.prompt,
            system_prompt=system_prompt,
            model_id=agent.model_id,
            model_config=agent.model_config or {},
            agent_config=agent_configuration,
            mcp_servers=mcp_servers,
            user_metadata=user_metadata,
            runtime_type=agent.runtime or "default",
            control_plane_url=control_plane_url,
            api_key=api_key,
            initial_message_timestamp=initial_timestamp,
            graph_api_url=resolved_env.get("graph_api_url"),
            dataset_name=resolved_env.get("dataset_name"),
        )

        # DEBUG: Log workflow input MCP servers
        logger.info(
            "🔍 DEBUG: Starting workflow with MCP servers",
            execution_id=str(execution_id),
            mcp_servers_count=len(mcp_servers),
            mcp_servers_type=str(type(mcp_servers)),
            mcp_server_names=list(mcp_servers.keys()) if mcp_servers else []
        )

        workflow_handle = await temporal_client.start_workflow(
            AgentExecutionWorkflow.run,
            workflow_input,
            id=f"agent-execution-{execution_id}",
            task_queue=task_queue,
        )

        logger.info(
            "agent_execution_submitted",
            execution_id=str(execution_id),
            agent_id=str(agent_id),
            workflow_id=workflow_handle.id,
            task_queue=task_queue,
            temporal_namespace=temporal_credentials["namespace"],
            worker_queue_id=str(worker_queue_id),
            worker_queue_name=worker_queue.name,
            org_id=organization["id"],
            org_name=organization["name"],
        )

        return AgentExecutionResponse(
            execution_id=str(execution_id),
            workflow_id=workflow_handle.id,
            status="PENDING",
            message=f"Execution submitted to worker queue: {worker_queue.name}",
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "agent_execution_failed",
            error=str(e),
            agent_id=str(agent_id),
            org_id=organization["id"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute agent: {str(e)}"
        )
