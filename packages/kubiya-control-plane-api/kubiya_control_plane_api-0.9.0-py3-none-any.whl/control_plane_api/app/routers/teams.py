import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Union, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
import structlog
import uuid

from control_plane_api.app.database import get_db
from control_plane_api.app.models.team import Team, TeamStatus
from control_plane_api.app.models.agent import Agent
from control_plane_api.app.models.skill import Skill, SkillAssociation
from control_plane_api.app.models.project import Project
from control_plane_api.app.models.project_management import ProjectTeam
from control_plane_api.app.models.worker import WorkerQueue
from control_plane_api.app.models.execution import Execution
from control_plane_api.app.models.associations import ExecutionParticipant, TeamEnvironment
from control_plane_api.app.middleware.auth import get_current_organization
from sqlalchemy.orm import joinedload
from control_plane_api.app.lib.temporal_client import get_temporal_client
from control_plane_api.app.workflows.agent_execution import AgentExecutionWorkflow, TeamExecutionInput
from control_plane_api.app.workflows.team_execution import TeamExecutionWorkflow
from control_plane_api.app.routers.projects import get_default_project_id
from control_plane_api.app.routers.agents_v2 import ExecutionEnvironment
from control_plane_api.app.lib.mcp_validation import validate_execution_environment_mcp, MCPValidationError
from pydantic import BaseModel, Field, field_validator

logger = structlog.get_logger()

router = APIRouter()


def get_entity_skills(db: Session, organization_id: str, entity_type: str, entity_id: str) -> List[dict]:
    """Get skills associated with an entity"""
    # Get associations with joined skills
    associations = db.query(SkillAssociation).options(
        joinedload(SkillAssociation.skill)
    ).filter(
        SkillAssociation.organization_id == organization_id,
        SkillAssociation.entity_type == entity_type,
        SkillAssociation.entity_id == entity_id
    ).all()

    skills = []
    for assoc in associations:
        skill = assoc.skill
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


def get_team_projects(db: Session, team_id: str) -> list[dict]:
    """Get all projects a team belongs to"""
    try:
        # Query project_teams join table with joined projects
        project_teams = db.query(ProjectTeam).options(
            joinedload(ProjectTeam.project)
        ).filter(
            ProjectTeam.team_id == team_id
        ).all()

        projects = []
        for pt in project_teams:
            if pt.project:
                projects.append({
                    "id": str(pt.project.id),
                    "name": pt.project.name,
                    "key": pt.project.key,
                    "description": pt.project.description,
                })

        return projects
    except Exception as e:
        logger.warning("failed_to_fetch_team_projects", error=str(e), team_id=team_id)
        return []


# Enhanced Pydantic schemas aligned with Agno Team capabilities

class ReasoningConfig(BaseModel):
    """Reasoning configuration for the team"""
    enabled: bool = Field(False, description="Enable reasoning for the team")
    model: Optional[str] = Field(None, description="Model to use for reasoning")
    agent_id: Optional[str] = Field(None, description="Agent ID to use for reasoning")
    min_steps: Optional[int] = Field(1, description="Minimum reasoning steps", ge=1)
    max_steps: Optional[int] = Field(10, description="Maximum reasoning steps", ge=1, le=100)


class LLMConfig(BaseModel):
    """LLM configuration for the team"""
    model: Optional[str] = Field(None, description="Default model for the team")
    temperature: Optional[float] = Field(None, description="Temperature for generation", ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate", ge=1)
    top_p: Optional[float] = Field(None, description="Top-p sampling", ge=0.0, le=1.0)
    top_k: Optional[int] = Field(None, description="Top-k sampling", ge=0)
    stop: Optional[List[str]] = Field(None, description="Stop sequences")
    frequency_penalty: Optional[float] = Field(None, description="Frequency penalty", ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, description="Presence penalty", ge=-2.0, le=2.0)


class SessionConfig(BaseModel):
    """Session configuration for the team"""
    user_id: Optional[str] = Field(None, description="User ID for the session")
    session_id: Optional[str] = Field(None, description="Session ID")
    auto_save: bool = Field(True, description="Auto-save session state")
    persist: bool = Field(True, description="Persist session across runs")


class TeamConfiguration(BaseModel):
    """
    Comprehensive team configuration aligned with Agno's Team capabilities.
    This allows full control over team behavior, reasoning, tools, and LLM settings.
    """
    # Members
    member_ids: List[str] = Field(default_factory=list, description="List of agent IDs in the team")

    # Instructions
    instructions: Union[str, List[str]] = Field(
        default="",
        description="Instructions for the team - can be a single string or list of instructions"
    )

    # Reasoning
    reasoning: Optional[ReasoningConfig] = Field(None, description="Reasoning configuration")

    # LLM Configuration
    llm: Optional[LLMConfig] = Field(None, description="LLM configuration for the team")

    # Tools & Knowledge
    tools: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Tools available to the team - list of tool configurations"
    )
    knowledge_base: Optional[Dict[str, Any]] = Field(
        None,
        description="Knowledge base configuration (vector store, embeddings, etc.)"
    )

    # Session & State
    session: Optional[SessionConfig] = Field(None, description="Session configuration")
    dependencies: Dict[str, Any] = Field(
        default_factory=dict,
        description="External dependencies (databases, APIs, services)"
    )

    # Advanced Options
    markdown: bool = Field(True, description="Enable markdown formatting in responses")
    add_datetime_to_instructions: bool = Field(
        False,
        description="Automatically add current datetime to instructions"
    )
    structured_outputs: bool = Field(False, description="Enable structured outputs")
    response_model: Optional[str] = Field(None, description="Response model schema name")

    # Monitoring & Debugging
    debug_mode: bool = Field(False, description="Enable debug mode with verbose logging")
    monitoring: bool = Field(False, description="Enable monitoring and telemetry")

    # Custom Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom metadata for the team"
    )


class TeamCreate(BaseModel):
    """Create a new team with full Agno capabilities"""
    name: str = Field(..., description="Team name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Team description")
    runtime: Optional[str] = Field(
        "default",
        description="Runtime type for team leader: 'default' (Agno) or 'claude_code' (Claude Code SDK). Default: 'default'"
    )
    configuration: TeamConfiguration = Field(
        default_factory=TeamConfiguration,
        description="Team configuration aligned with Agno Team"
    )
    skill_ids: list[str] = Field(default_factory=list, description="Tool set IDs to associate with this team")
    skill_configurations: dict[str, dict] = Field(default_factory=dict, description="Tool set configurations keyed by skill ID")
    execution_environment: ExecutionEnvironment | None = Field(None, description="Execution environment: env vars, secrets, integrations")

    @field_validator('runtime')
    @classmethod
    def validate_runtime(cls, v: Optional[str]) -> Optional[str]:
        """Validate runtime is a valid value"""
        if v is not None and v not in ["default", "claude_code"]:
            raise ValueError(f"Invalid runtime type '{v}'. Must be 'default' or 'claude_code'.")
        return v


class TeamUpdate(BaseModel):
    """Update an existing team"""
    name: Optional[str] = Field(None, description="Team name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Team description")
    status: Optional[TeamStatus] = Field(None, description="Team status")
    runtime: Optional[str] = Field(None, description="Runtime type: 'default' (Agno) or 'claude_code' (Claude Code SDK)")
    configuration: Optional[TeamConfiguration] = Field(None, description="Team configuration")
    skill_ids: list[str] | None = None
    skill_configurations: dict[str, dict] | None = None
    environment_ids: list[str] | None = None
    execution_environment: ExecutionEnvironment | None = None

    @field_validator('runtime')
    @classmethod
    def validate_runtime(cls, v: Optional[str]) -> Optional[str]:
        """Validate runtime is a valid value"""
        if v is not None and v not in ["default", "claude_code"]:
            raise ValueError(f"Invalid runtime type '{v}'. Must be 'default' or 'claude_code'.")
        return v


class TeamResponse(BaseModel):
    """Team response with structured configuration"""
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    status: TeamStatus
    runtime: str = Field(
        default="default",
        description="Runtime type for team leader: 'default' (Agno) or 'claude_code' (Claude Code SDK)"
    )
    configuration: TeamConfiguration
    created_at: datetime
    updated_at: datetime
    projects: List[dict] = Field(default_factory=list, description="Projects this team belongs to")
    skill_ids: Optional[List[str]] = Field(default_factory=list, description="IDs of associated skills")
    skills: Optional[List[dict]] = Field(default_factory=list, description="Associated skills with details")
    execution_environment: ExecutionEnvironment | None = None

    class Config:
        from_attributes = True


class TeamWithAgentsResponse(TeamResponse):
    """Team response including member agents"""
    agents: List[dict]


class TeamExecutionRequest(BaseModel):
    prompt: str = Field(..., description="The prompt/task to execute")
    system_prompt: str | None = Field(None, description="Optional system prompt for team coordination")
    stream: bool = Field(False, description="Whether to stream the response")
    worker_queue_id: str = Field(..., description="Worker queue ID (UUID) to route execution to - REQUIRED")
    user_metadata: dict | None = Field(None, description="User attribution metadata (optional, auto-filled from token)")
    execution_environment: ExecutionEnvironment | None = Field(None, description="Optional execution environment overrides (working_dir, env_vars, etc.)")


class TeamExecutionResponse(BaseModel):
    execution_id: str
    workflow_id: str
    status: str
    message: str


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team_data: TeamCreate,
    request: Request,
    db: Session = Depends(get_db),
    organization: dict = Depends(get_current_organization),
):
    """
    Create a new team with full Agno capabilities.

    Supports comprehensive configuration including:
    - Member agents
    - Instructions and reasoning
    - Tools and knowledge bases
    - LLM settings
    - Session management
    """
    try:
        logger.info(
            "create_team_request",
            team_name=team_data.name,
            org_id=organization["id"],
            org_name=organization.get("name"),
            member_count=len(team_data.configuration.member_ids) if team_data.configuration.member_ids else 0,
            skill_count=len(team_data.skill_ids) if team_data.skill_ids else 0,
        )

        # Check if team name already exists in this organization
        existing_team = db.query(Team).filter(
            Team.name == team_data.name,
            Team.organization_id == organization["id"]
        ).first()
        if existing_team:
            logger.warning(
                "team_name_already_exists",
                team_name=team_data.name,
                org_id=organization["id"],
            )
            raise HTTPException(status_code=400, detail="Team with this name already exists in your organization")

        # Validate member_ids if provided
        if team_data.configuration.member_ids:
            logger.info(
                "validating_team_members",
                member_ids=team_data.configuration.member_ids,
                org_id=organization["id"],
            )
            for agent_id in team_data.configuration.member_ids:
                try:
                    # Query database for agent validation
                    agent = db.query(Agent).filter(
                        Agent.id == agent_id,
                        Agent.organization_id == organization["id"]
                    ).first()

                    logger.debug(
                        "agent_validation_result",
                        agent_id=agent_id,
                        found=agent is not None,
                    )

                    if not agent:
                        logger.warning(
                            "agent_not_found",
                            agent_id=agent_id,
                            org_id=organization["id"],
                        )
                        raise HTTPException(
                            status_code=400,
                            detail=f"Agent with ID '{agent_id}' not found. Please create the agent first."
                        )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(
                        "agent_validation_failed",
                        agent_id=agent_id,
                        error=str(e),
                        error_type=type(e).__name__,
                        org_id=organization["id"],
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to validate agent '{agent_id}': {str(e)}"
                    )

        # Validate runtime compatibility: Claude Code teams require all members to be Claude Code
        if team_data.runtime == "claude_code" and team_data.configuration.member_ids:
            logger.info(
                "validating_claude_code_team_runtime",
                team_name=team_data.name,
                member_count=len(team_data.configuration.member_ids),
            )

            non_claude_code_members = []

            for agent_id in team_data.configuration.member_ids:
                try:
                    # Fetch agent runtime
                    agent = db.query(Agent).filter(
                        Agent.id == agent_id,
                        Agent.organization_id == organization["id"]
                    ).first()

                    if agent:
                        agent_runtime = agent.runtime or "default"
                        agent_name = agent.name

                        if agent_runtime != "claude_code":
                            non_claude_code_members.append({
                                "id": str(agent_id),
                                "name": agent_name,
                                "runtime": agent_runtime
                            })
                            logger.warning(
                                "member_runtime_mismatch",
                                agent_id=str(agent_id),
                                agent_name=agent_name,
                                agent_runtime=agent_runtime,
                                team_runtime="claude_code",
                            )
                except Exception as e:
                    logger.error(
                        "runtime_validation_failed",
                        agent_id=agent_id,
                        error=str(e),
                    )
                    # Continue checking other members
                    continue

            if non_claude_code_members:
                member_details = ", ".join([
                    f"{m['name']} (runtime: {m['runtime']})"
                    for m in non_claude_code_members
                ])
                error_msg = (
                    f"Cannot create Claude Code team with non-Claude Code members. "
                    f"The following members must use 'claude_code' runtime: {member_details}. "
                    f"Either change the team runtime to 'default' or update all member agents to use 'claude_code' runtime."
                )
                logger.warning(
                    "claude_code_team_validation_failed",
                    team_name=team_data.name,
                    non_claude_code_count=len(non_claude_code_members),
                    non_claude_code_members=non_claude_code_members,
                )
                raise HTTPException(
                    status_code=400,
                    detail=error_msg
                )

            logger.info(
                "claude_code_team_validation_passed",
                team_name=team_data.name,
                all_members_claude_code=True,
            )

        # Validate MCP server configuration if present
        if team_data.execution_environment and team_data.execution_environment.mcp_servers:
            try:
                mcp_validation = validate_execution_environment_mcp(
                    team_data.execution_environment.model_dump(),
                    strict=False
                )

                if not mcp_validation["valid"]:
                    error_msg = "MCP configuration validation failed:\n" + "\n".join(
                        f"  - {err}" for err in mcp_validation["errors"]
                    )
                    logger.error(
                        "mcp_validation_failed",
                        team_name=team_data.name,
                        errors=mcp_validation["errors"],
                    )
                    raise HTTPException(status_code=400, detail=error_msg)

                if mcp_validation["warnings"]:
                    logger.warning(
                        "mcp_validation_warnings",
                        team_name=team_data.name,
                        warnings=mcp_validation["warnings"],
                        required_secrets=mcp_validation.get("required_secrets", []),
                        required_env_vars=mcp_validation.get("required_env_vars", []),
                    )

                logger.info(
                    "mcp_validation_passed",
                    team_name=team_data.name,
                    server_count=len(team_data.execution_environment.mcp_servers),
                    required_secrets=mcp_validation.get("required_secrets", []),
                    required_env_vars=mcp_validation.get("required_env_vars", []),
                )
            except MCPValidationError as e:
                logger.error(
                    "mcp_validation_error",
                    team_name=team_data.name,
                    error=str(e),
                )
                raise HTTPException(status_code=400, detail=str(e))

        # Convert TeamConfiguration to dict for JSON storage
        configuration_dict = team_data.configuration.model_dump(exclude_none=True)

        team = Team(
            organization_id=organization["id"],
            name=team_data.name,
            description=team_data.description,
            runtime=team_data.runtime or "default",  # Set runtime for team leader
            configuration=configuration_dict,
            skill_ids=team_data.skill_ids,
            execution_environment=team_data.execution_environment.model_dump() if team_data.execution_environment else {},
        )
        db.add(team)
        db.commit()
        db.refresh(team)

        logger.info(
            "team_created",
            team_id=str(team.id),
            team_name=team.name,
            org_id=organization["id"],
        )
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(
            "database_integrity_error",
            error=str(e),
            team_name=team_data.name,
            org_id=organization["id"],
        )
        raise HTTPException(
            status_code=400,
            detail=f"Database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(
            "team_creation_failed",
            error=str(e),
            error_type=type(e).__name__,
            team_name=team_data.name,
            org_id=organization["id"],
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create team: {str(e)}"
        )

    # Sync agent.team_id relationship for initial members
    if team_data.configuration.member_ids:
        for agent_id in team_data.configuration.member_ids:
            try:
                agent = db.query(Agent).filter(Agent.id == agent_id).first()
                if agent:
                    agent.team_id = team.id
                db.commit()
            except Exception as e:
                logger.warning(
                    "failed_to_sync_agent_team_id",
                    error=str(e),
                    agent_id=agent_id,
                    team_id=str(team.id)
                )
                db.rollback()

    # Automatically assign team to the default project
    default_project_id = get_default_project_id(db, organization)
    if default_project_id:
        try:
            project_team = ProjectTeam(
                project_id=default_project_id,
                team_id=team.id,
                role=None,
                added_by=organization.get("user_id"),
            )
            db.add(project_team)
            db.commit()
            logger.info(
                "team_added_to_default_project",
                team_id=str(team.id),
                project_id=default_project_id,
                org_id=organization["id"]
            )
        except Exception as e:
            logger.warning(
                "failed_to_add_team_to_default_project",
                error=str(e),
                team_id=str(team.id),
                org_id=organization["id"]
            )
            db.rollback()

    # Create skill associations if skills were provided
    if team_data.skill_ids:
        try:
            for skill_id in team_data.skill_ids:
                config_override = team_data.skill_configurations.get(skill_id, {})

                skill_assoc = SkillAssociation(
                    organization_id=organization["id"],
                    skill_id=skill_id,
                    entity_type="team",
                    entity_id=team.id,
                    configuration_override=config_override,
                )
                db.add(skill_assoc)

            db.commit()
            logger.info(
                "team_skills_associated",
                team_id=str(team.id),
                skill_count=len(team_data.skill_ids),
                org_id=organization["id"]
            )
        except Exception as e:
            logger.warning(
                "failed_to_associate_team_skills",
                error=str(e),
                team_id=str(team.id),
                org_id=organization["id"]
            )
            db.rollback()

    # Parse configuration back to TeamConfiguration for response
    response_team = TeamResponse(
        id=str(team.id),
        organization_id=team.organization_id,
        name=team.name,
        description=team.description,
        status=team.status,
        runtime=team.runtime.value if team.runtime else "default",  # Include runtime in response
        configuration=TeamConfiguration(**team.configuration),
        created_at=team.created_at,
        updated_at=team.updated_at,
        projects=get_team_projects(db, str(team.id)),
        skill_ids=team.skill_ids or [],  # Include skill_ids in response
        skills=[],  # Skills will be loaded separately if needed
    )
    return response_team


@router.get("", response_model=List[TeamWithAgentsResponse])
def list_teams(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[TeamStatus] = None,
    db: Session = Depends(get_db),
    organization: dict = Depends(get_current_organization),
):
    """
    List all teams with their configurations and member agents.

    Supports filtering by status and pagination.
    Only returns teams belonging to the current organization.
    """
    try:
        query = db.query(Team).filter(Team.organization_id == organization["id"])
        if status_filter:
            query = query.filter(Team.status == status_filter)
        teams = query.offset(skip).limit(limit).all()

        if not teams:
            return []

        team_ids = [team.id for team in teams]

        # BATCH 1: Fetch all projects for all teams in one query
        try:
            project_teams = db.query(ProjectTeam).options(
                joinedload(ProjectTeam.project)
            ).filter(
                ProjectTeam.team_id.in_(team_ids)
            ).all()
        except Exception as project_error:
            logger.error("failed_to_fetch_projects", error=str(project_error), org_id=organization["id"])
            project_teams = []

        # Group projects by team_id
        projects_by_team = {}
        for pt in project_teams:
            team_id_str = str(pt.team_id)
            if pt.project:
                if team_id_str not in projects_by_team:
                    projects_by_team[team_id_str] = []
                projects_by_team[team_id_str].append({
                    "id": str(pt.project.id),
                    "name": pt.project.name,
                    "key": pt.project.key,
                    "description": pt.project.description,
                })

        # BATCH 2: Fetch all skill associations for all teams in one query
        try:
            skill_associations = db.query(SkillAssociation).options(
                joinedload(SkillAssociation.skill)
            ).filter(
                SkillAssociation.organization_id == organization["id"],
                SkillAssociation.entity_type == "team",
                SkillAssociation.entity_id.in_(team_ids)
            ).all()
        except Exception as skill_error:
            logger.error("failed_to_fetch_skills", error=str(skill_error), org_id=organization["id"])
            skill_associations = []

        # Group skills by team_id
        skills_by_team = {}
        for assoc in skill_associations:
            team_id_str = str(assoc.entity_id)
            skill = assoc.skill
            if skill and skill.enabled:
                if team_id_str not in skills_by_team:
                    skills_by_team[team_id_str] = []

                # Merge configuration with override
                config = skill.configuration or {}
                override = assoc.configuration_override
                if override:
                    config = {**config, **override}

                skills_by_team[team_id_str].append({
                    "id": str(skill.id),
                    "name": skill.name,
                    "type": skill.skill_type,
                    "description": skill.description,
                    "enabled": skill.enabled,
                    "configuration": config,
                })

        # BATCH 3: Collect all unique agent IDs from all teams
        all_agent_ids = set()
        for team in teams:
            try:
                team_config = TeamConfiguration(**(team.configuration or {}))
                if team_config.member_ids:
                    all_agent_ids.update(team_config.member_ids)
            except Exception as config_error:
                logger.warning("failed_to_parse_team_config", error=str(config_error), team_id=str(team.id))

        # Fetch all agents in one query
        agents_by_id = {}
        if all_agent_ids:
            try:
                db_agents = db.query(Agent).filter(Agent.id.in_(list(all_agent_ids))).all()
                agents_by_id = {
                    str(agent.id): {
                        "id": str(agent.id),
                        "name": agent.name,
                        "status": agent.status,
                        "capabilities": agent.capabilities,
                        "description": agent.description,
                    }
                    for agent in db_agents
                }
            except Exception as agent_error:
                logger.error("failed_to_fetch_agents", error=str(agent_error), org_id=organization["id"])

        # Build response for each team
        result = []
        for team in teams:
            try:
                team_id = str(team.id)
                team_config = TeamConfiguration(**(team.configuration or {}))

                # Get agents for this team from the batched data
                agents = []
                if team_config.member_ids:
                    agents = [agents_by_id[agent_id] for agent_id in team_config.member_ids if agent_id in agents_by_id]

                # Get skills from batched data
                skills = skills_by_team.get(team_id, [])
                skill_ids = [ts["id"] for ts in skills]

                result.append(TeamWithAgentsResponse(
                    id=team_id,
                    organization_id=team.organization_id,
                    name=team.name,
                    description=team.description,
                    status=team.status,
                    runtime=team.runtime.value if team.runtime else "default",  # Include runtime in response
                    configuration=team_config,
                    created_at=team.created_at,
                    updated_at=team.updated_at,
                    projects=projects_by_team.get(team_id, []),
                    agents=agents,
                    skill_ids=skill_ids,
                    skills=skills,
                ))
            except Exception as team_error:
                logger.error("failed_to_build_team_response", error=str(team_error), team_id=str(team.id))
                # Skip this team and continue with others

        logger.info(
            "teams_listed_successfully",
            count=len(result),
            org_id=organization["id"],
        )

        return result

    except Exception as e:
        logger.error(
            "teams_list_failed",
            error=str(e),
            error_type=type(e).__name__,
            org_id=organization["id"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list teams: {str(e)}"
        )


@router.get("/{team_id}", response_model=TeamWithAgentsResponse)
def get_team(
    team_id: str,
    db: Session = Depends(get_db),
    organization: dict = Depends(get_current_organization),
):
    """
    Get a specific team by ID with full configuration and member agents.

    Returns the team with structured configuration and list of member agents.
    Only returns teams belonging to the current organization.
    """
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.organization_id == organization["id"]
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Parse configuration
    team_config = TeamConfiguration(**(team.configuration or {}))

    # Get agents from configuration.member_ids (source of truth)
    # instead of team.agents relationship to avoid ghost agents
    member_ids = team_config.member_ids
    agents = []
    if member_ids:
        # Query agents that actually exist in the database
        db_agents = db.query(Agent).filter(Agent.id.in_(member_ids)).all()
        agents = [
            {
                "id": str(agent.id),
                "name": agent.name,
                "status": agent.status,
                "capabilities": agent.capabilities,
                "description": agent.description,
            }
            for agent in db_agents
        ]

    # Get skills for this team
    skills = get_entity_skills(db, organization["id"], "team", team_id)
    skill_ids = [ts["id"] for ts in skills]

    # Include agents in response
    return TeamWithAgentsResponse(
        id=str(team.id),
        organization_id=team.organization_id,
        name=team.name,
        description=team.description,
        status=team.status,
        runtime=team.runtime.value if team.runtime else "default",  # Include runtime in response
        configuration=team_config,
        created_at=team.created_at,
        updated_at=team.updated_at,
        projects=get_team_projects(db, team_id),
        agents=agents,
        skill_ids=skill_ids,
        skills=skills,
    )


@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: str,
    team_data: TeamUpdate,
    db: Session = Depends(get_db),
    organization: dict = Depends(get_current_organization),
):
    """
    Update a team's configuration, name, description, or status.

    Supports partial updates - only provided fields are updated.
    Validates member_ids if configuration is being updated.
    Only allows updating teams belonging to the current organization.
    """
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.organization_id == organization["id"]
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    update_data = team_data.model_dump(exclude_unset=True)

    # Extract skill data before processing
    skill_ids = update_data.pop("skill_ids", None)
    skill_configurations = update_data.pop("skill_configurations", None)

    # Extract environment data before processing (many-to-many via junction table)
    environment_ids = update_data.pop("environment_ids", None)

    # Handle execution_environment - convert to dict if present
    if "execution_environment" in update_data and update_data["execution_environment"]:
        if isinstance(update_data["execution_environment"], ExecutionEnvironment):
            update_data["execution_environment"] = update_data["execution_environment"].model_dump()
        # If None, keep as None to preserve existing value

    logger.info(
        "team_update_request",
        team_id=team_id,
        has_skill_ids=skill_ids is not None,
        skill_count=len(skill_ids) if skill_ids else 0,
        skill_ids=skill_ids,
    )

    # Check if name is being updated and if it already exists
    if "name" in update_data and update_data["name"] != team.name:
        existing_team = db.query(Team).filter(Team.name == update_data["name"]).first()
        if existing_team:
            raise HTTPException(status_code=400, detail="Team with this name already exists")

    # Handle configuration update specially
    if "configuration" in update_data and update_data["configuration"]:
        new_config = update_data["configuration"]

        # new_config is already a dict from model_dump(exclude_unset=True)
        # Validate member_ids if provided and sync the agent.team_id relationship
        if isinstance(new_config, dict) and 'member_ids' in new_config:
            new_member_ids = set(new_config.get('member_ids', []))

            # Validate all agent IDs exist
            for agent_id in new_member_ids:
                agent = db.query(Agent).filter(
                    Agent.id == agent_id,
                    Agent.organization_id == organization["id"]
                ).first()
                if not agent:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Agent with ID '{agent_id}' not found. Please create the agent first."
                    )

            # Sync the agent.team_id relationship
            # Get current team members from configuration
            current_config = TeamConfiguration(**(team.configuration or {}))
            current_member_ids = set(current_config.member_ids or [])

            # Remove agents that are no longer in the team
            agents_to_remove = current_member_ids - new_member_ids
            for agent_id in agents_to_remove:
                try:
                    agent = db.query(Agent).filter(Agent.id == agent_id).first()
                    if agent:
                        agent.team_id = None
                    db.commit()
                except Exception as e:
                    logger.warning("failed_to_remove_agent_from_team", error=str(e), agent_id=agent_id)
                    db.rollback()

            # Add agents that are newly added to the team
            agents_to_add = new_member_ids - current_member_ids
            for agent_id in agents_to_add:
                try:
                    agent = db.query(Agent).filter(Agent.id == agent_id).first()
                    if agent:
                        agent.team_id = team_id
                    db.commit()
                except Exception as e:
                    logger.warning("failed_to_add_agent_to_team", error=str(e), agent_id=agent_id)
                    db.rollback()

        # new_config is already a dict, just assign it
        team.configuration = new_config
        del update_data["configuration"]

    # Validate runtime compatibility when updating runtime or members
    # Check if runtime is being set to claude_code
    final_runtime = update_data.get("runtime", team.runtime)

    # Get final member list (either from update or existing)
    if "configuration" in locals() and isinstance(new_config, dict) and 'member_ids' in new_config:
        final_member_ids = new_config.get('member_ids', [])
    else:
        current_config = TeamConfiguration(**(team.configuration or {}))
        final_member_ids = current_config.member_ids or []

    # Validate Claude Code team runtime requirements
    if final_runtime == "claude_code" and final_member_ids:
        logger.info(
            "validating_claude_code_team_runtime_on_update",
            team_id=team_id,
            member_count=len(final_member_ids),
        )

        non_claude_code_members = []

        for agent_id in final_member_ids:
            try:
                agent = db.query(Agent).filter(
                    Agent.id == agent_id,
                    Agent.organization_id == organization["id"]
                ).first()

                if agent:
                    agent_runtime = agent.runtime or "default"
                    agent_name = agent.name

                    if agent_runtime != "claude_code":
                        non_claude_code_members.append({
                            "id": str(agent_id),
                            "name": agent_name,
                            "runtime": agent_runtime
                        })
                        logger.warning(
                            "member_runtime_mismatch_on_update",
                            agent_id=str(agent_id),
                            agent_name=agent_name,
                            agent_runtime=agent_runtime,
                            team_runtime="claude_code",
                        )
            except Exception as e:
                logger.error(
                    "runtime_validation_failed_on_update",
                    agent_id=agent_id,
                    error=str(e),
                )
                continue

        if non_claude_code_members:
            member_details = ", ".join([
                f"{m['name']} (runtime: {m['runtime']})"
                for m in non_claude_code_members
            ])
            error_msg = (
                f"Cannot update to Claude Code team with non-Claude Code members. "
                f"The following members must use 'claude_code' runtime: {member_details}. "
                f"Either keep the team runtime as 'default' or update all member agents to use 'claude_code' runtime."
            )
            logger.warning(
                "claude_code_team_update_validation_failed",
                team_id=team_id,
                non_claude_code_count=len(non_claude_code_members),
            )
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )

        logger.info(
            "claude_code_team_update_validation_passed",
            team_id=team_id,
            all_members_claude_code=True,
        )

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
                        team_id=team_id,
                        errors=mcp_validation["errors"],
                    )
                    raise HTTPException(status_code=400, detail=error_msg)

                if mcp_validation["warnings"]:
                    logger.warning(
                        "mcp_validation_warnings",
                        team_id=team_id,
                        warnings=mcp_validation["warnings"],
                        required_secrets=mcp_validation.get("required_secrets", []),
                        required_env_vars=mcp_validation.get("required_env_vars", []),
                    )

                logger.info(
                    "mcp_validation_passed",
                    team_id=team_id,
                    server_count=len(exec_env_dict.get("mcp_servers", {})),
                    required_secrets=mcp_validation.get("required_secrets", []),
                    required_env_vars=mcp_validation.get("required_env_vars", []),
                )
            except MCPValidationError as e:
                logger.error(
                    "mcp_validation_error",
                    team_id=team_id,
                    error=str(e),
                )
                raise HTTPException(status_code=400, detail=str(e))

    # Update other fields
    for field, value in update_data.items():
        if hasattr(team, field):
            setattr(team, field, value)

    # Update skill_ids if provided
    if skill_ids is not None:
        team.skill_ids = skill_ids

    team.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(team)

    # Update skill associations if skill_ids was provided
    if skill_ids is not None:
        try:
            # Delete existing associations
            db.query(SkillAssociation).filter(
                SkillAssociation.entity_type == "team",
                SkillAssociation.entity_id == team_id
            ).delete()

            # Create new associations
            for skill_id in skill_ids:
                config_override = (skill_configurations or {}).get(skill_id, {})

                skill_assoc = SkillAssociation(
                    organization_id=organization["id"],
                    skill_id=skill_id,
                    entity_type="team",
                    entity_id=team_id,
                    configuration_override=config_override,
                )
                db.add(skill_assoc)

            db.commit()
            logger.info(
                "team_skills_updated",
                team_id=team_id,
                skill_count=len(skill_ids),
                org_id=organization["id"]
            )
        except Exception as e:
            db.rollback()
            logger.warning(
                "failed_to_update_team_skills",
                error=str(e),
                team_id=team_id,
                org_id=organization["id"]
            )

    # Update environment associations if environment_ids was provided
    if environment_ids is not None:
        try:
            # Delete existing environment associations
            db.query(TeamEnvironment).filter(
                TeamEnvironment.team_id == team_id
            ).delete()

            # Create new environment associations
            for environment_id in environment_ids:
                team_env = TeamEnvironment(
                    team_id=team_id,
                    environment_id=environment_id,
                    organization_id=organization["id"],
                )
                db.add(team_env)

            db.commit()
            logger.info(
                "team_environments_updated",
                team_id=team_id,
                environment_count=len(environment_ids),
                org_id=organization["id"]
            )
        except Exception as e:
            db.rollback()
            logger.warning(
                "failed_to_update_team_environments",
                error=str(e),
                team_id=team_id,
                org_id=organization["id"]
            )

    # Return with parsed configuration
    return TeamResponse(
        id=str(team.id),
        organization_id=team.organization_id,
        name=team.name,
        description=team.description,
        status=team.status,
        runtime=team.runtime.value if team.runtime else "default",  # Include runtime in response
        configuration=TeamConfiguration(**(team.configuration or {})),
        created_at=team.created_at,
        updated_at=team.updated_at,
        projects=get_team_projects(db, team_id),
        skill_ids=team.skill_ids or [],  # Include skill_ids in response
        skills=[],  # Skills will be loaded separately if needed
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: str,
    db: Session = Depends(get_db),
    organization: dict = Depends(get_current_organization),
):
    """Delete a team - only if it belongs to the current organization"""
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.organization_id == organization["id"]
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    db.delete(team)
    db.commit()
    return None


@router.post("/{team_id}/agents/{agent_id}", response_model=TeamWithAgentsResponse)
def add_agent_to_team(
    team_id: str,
    agent_id: str,
    db: Session = Depends(get_db),
    organization: dict = Depends(get_current_organization),
):
    """
    Add an agent to a team.

    This sets the agent's team_id foreign key. You can also manage members
    through the team's configuration.member_ids field.
    Only allows adding agents to teams belonging to the current organization.
    """
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.organization_id == organization["id"]
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == organization["id"]
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.team_id = team_id
    db.commit()
    db.refresh(team)

    # Parse configuration
    team_config = TeamConfiguration(**(team.configuration or {}))

    # Get agents from configuration.member_ids (source of truth)
    member_ids = team_config.member_ids
    agents = []
    if member_ids:
        db_agents = db.query(Agent).filter(Agent.id.in_(member_ids)).all()
        agents = [
            {
                "id": str(a.id),
                "name": a.name,
                "status": a.status,
                "capabilities": a.capabilities,
                "description": a.description,
            }
            for a in db_agents
        ]

    # Return team with agents
    return TeamWithAgentsResponse(
        id=str(team.id),
        organization_id=team.organization_id,
        name=team.name,
        description=team.description,
        status=team.status,
        configuration=team_config,
        created_at=team.created_at,
        updated_at=team.updated_at,
        agents=agents,
    )


@router.delete("/{team_id}/agents/{agent_id}", response_model=TeamWithAgentsResponse)
def remove_agent_from_team(
    team_id: str,
    agent_id: str,
    db: Session = Depends(get_db),
    organization: dict = Depends(get_current_organization),
):
    """
    Remove an agent from a team.

    This clears the agent's team_id foreign key.
    Only allows removing agents from teams belonging to the current organization.
    """
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.organization_id == organization["id"]
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.team_id == team_id,
        Agent.organization_id == organization["id"]
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found in this team")

    agent.team_id = None
    db.commit()
    db.refresh(team)

    # Parse configuration
    team_config = TeamConfiguration(**(team.configuration or {}))

    # Get agents from configuration.member_ids (source of truth)
    member_ids = team_config.member_ids
    agents = []
    if member_ids:
        db_agents = db.query(Agent).filter(Agent.id.in_(member_ids)).all()
        agents = [
            {
                "id": str(a.id),
                "name": a.name,
                "status": a.status,
                "capabilities": a.capabilities,
                "description": a.description,
            }
            for a in db_agents
        ]

    # Return team with agents
    return TeamWithAgentsResponse(
        id=str(team.id),
        organization_id=team.organization_id,
        name=team.name,
        description=team.description,
        status=team.status,
        configuration=team_config,
        created_at=team.created_at,
        updated_at=team.updated_at,
        agents=agents,
    )


@router.post("/{team_id}/execute", response_model=TeamExecutionResponse)
async def execute_team(
    team_id: str,
    execution_request: TeamExecutionRequest,
    request: Request,
    db: Session = Depends(get_db),
    organization: dict = Depends(get_current_organization),
):
    """
    Execute a team task by submitting to Temporal workflow.

    This creates an execution record and starts a Temporal workflow.
    The actual execution happens asynchronously on the Temporal worker.

    The runner_name should come from the Composer UI where user selects
    from available runners (fetched from Kubiya API /api/v1/runners).
    """
    try:
        # Get team details from local DB
        team = db.query(Team).filter(
            Team.id == team_id,
            Team.organization_id == organization["id"]
        ).first()

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # DEBUG: Log team runtime immediately after fetch
        print(f"🔍 DEBUG [execute_team]: Fetched team '{team.name}' (ID: {team.id})")
        print(f"🔍 DEBUG [execute_team]: team.runtime = {team.runtime} (type: {type(team.runtime)})")

        # Parse team configuration
        team_config = TeamConfiguration(**(team.configuration or {}))

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

        logger.info(
            "execution_user_metadata",
            user_id=user_metadata.get("user_id"),
            user_name=user_metadata.get("user_name"),
            user_email=user_metadata.get("user_email"),
            org_id=organization.get("id"),
        )

        # Create execution record in database
        execution_id = str(uuid.uuid4())

        execution = Execution(
            id=execution_id,
            organization_id=organization["id"],
            execution_type="TEAM",
            entity_id=team_id,
            entity_name=team.name,
            prompt=execution_request.prompt,
            system_prompt=execution_request.system_prompt,
            status="PENDING",
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
                "team_execution": True,
            },
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        # Add creator as the first participant (owner role) for multiplayer support
        user_id = user_metadata.get("user_id")
        if user_id:
            try:
                participant = ExecutionParticipant(
                    execution_id=execution_id,
                    organization_id=organization["id"],
                    user_id=user_id,
                    user_name=user_metadata.get("user_name"),
                    user_email=user_metadata.get("user_email"),
                    user_avatar=user_metadata.get("user_avatar"),
                    role="owner",
                )
                db.add(participant)
                db.commit()
                logger.info(
                    "owner_participant_added",
                    execution_id=execution_id,
                    user_id=user_id,
                )
            except Exception as participant_error:
                db.rollback()
                logger.warning(
                    "failed_to_add_owner_participant",
                    error=str(participant_error),
                    execution_id=execution_id,
                )
                # Don't fail execution creation if participant tracking fails

        # Get resolved execution environment with templates compiled
        resolved_env = {}  # Initialize to empty dict to avoid UnboundLocalError
        try:
            async with httpx.AsyncClient() as client:
                resolved_env_response = await client.get(
                    f"{str(request.base_url).rstrip('/')}/api/v1/execution-environment/teams/{team_id}/resolved/full",
                    headers={"Authorization": request.headers.get("authorization")}
                )
                if resolved_env_response.status_code == 200:
                    resolved_env = resolved_env_response.json()
                    mcp_servers = resolved_env.get("mcp_servers", {})
                    resolved_instructions = resolved_env.get("instructions")
                    resolved_description = resolved_env.get("description")
                    logger.info(
                        "execution_environment_resolved_for_team_execution",
                        team_id=team_id[:8],
                        mcp_server_count=len(mcp_servers),
                        has_resolved_instructions=bool(resolved_instructions)
                    )
                else:
                    logger.warning(
                        "failed_to_resolve_team_execution_environment",
                        team_id=team_id[:8],
                        status=resolved_env_response.status_code
                    )
                    # Fallback to non-resolved config
                    mcp_servers = team_config.metadata.get("mcpServers", {}) if team_config.metadata else {}
                    resolved_instructions = None
                    resolved_description = None
        except Exception as e:
            logger.error(
                "team_execution_environment_resolution_error",
                team_id=team_id[:8],
                error=str(e)
            )
            # Fallback to non-resolved config
            mcp_servers = team_config.metadata.get("mcpServers", {}) if team_config.metadata else {}
            resolved_instructions = None
            resolved_description = None

        # Use LLM config from team configuration if available
        model_id = team_config.llm.model if team_config.llm and team_config.llm.model else "kubiya/claude-sonnet-4"

        # Build model config from LLM configuration
        model_config = {}
        if team_config.llm:
            if team_config.llm.temperature is not None:
                model_config["temperature"] = team_config.llm.temperature
            if team_config.llm.max_tokens is not None:
                model_config["max_tokens"] = team_config.llm.max_tokens
            if team_config.llm.top_p is not None:
                model_config["top_p"] = team_config.llm.top_p
            if team_config.llm.stop is not None:
                model_config["stop"] = team_config.llm.stop
            if team_config.llm.frequency_penalty is not None:
                model_config["frequency_penalty"] = team_config.llm.frequency_penalty
            if team_config.llm.presence_penalty is not None:
                model_config["presence_penalty"] = team_config.llm.presence_penalty

        # Submit to Temporal workflow
        # Task queue is the worker queue UUID
        task_queue = worker_queue_id

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
        # Use resolved instructions (with templates compiled) if available
        # Priority: request > resolved > team_config.instructions
        system_prompt = execution_request.system_prompt
        if not system_prompt:
            if resolved_instructions:
                # Use resolved instructions with templates compiled
                if isinstance(resolved_instructions, list):
                    system_prompt = "\n".join(resolved_instructions)
                else:
                    system_prompt = resolved_instructions
            elif team_config.instructions:
                # Fallback to non-resolved instructions
                if isinstance(team_config.instructions, list):
                    system_prompt = "\n".join(team_config.instructions)
                else:
                    system_prompt = team_config.instructions

        # Get API key from Authorization header
        auth_header = request.headers.get("authorization", "")
        api_key = auth_header.replace("UserKey ", "").replace("Bearer ", "") if auth_header else None

        # Get control plane URL from request
        control_plane_url = str(request.base_url).rstrip("/")

        # CRITICAL: Use real-time timestamp for initial message to ensure chronological ordering
        # This prevents timestamp mismatches between initial and follow-up messages
        initial_timestamp = datetime.now(timezone.utc).isoformat()

        # Handle runtime type - SQLAlchemy may return enum or string
        runtime_value = team.runtime
        print(f"🔍 DEBUG [execute_team]: runtime_value = {runtime_value} (type: {type(runtime_value)})")
        print(f"🔍 DEBUG [execute_team]: hasattr(runtime_value, 'value') = {hasattr(runtime_value, 'value')}")
        if runtime_value:
            # If it's an enum, get its value; if it's already a string, use it
            runtime_type_str = runtime_value.value if hasattr(runtime_value, 'value') else str(runtime_value)
        else:
            runtime_type_str = "default"
        print(f"🔍 DEBUG [execute_team]: Final runtime_type_str = '{runtime_type_str}'")

        # Override team_config with execution_environment.working_dir if provided
        team_configuration = team.configuration or {}
        if execution_request.execution_environment and execution_request.execution_environment.working_dir:
            team_configuration = team_configuration.copy()
            team_configuration["cwd"] = execution_request.execution_environment.working_dir
            logger.info(
                "execution_working_dir_override",
                execution_id=execution_id,
                working_dir=execution_request.execution_environment.working_dir,
            )

        workflow_input = TeamExecutionInput(
            execution_id=execution_id,
            team_id=team_id,
            organization_id=organization["id"],
            prompt=execution_request.prompt,
            system_prompt=system_prompt,
            model_id=model_id,
            model_config=model_config,
            team_config=team_configuration,
            mcp_servers=mcp_servers,
            user_metadata=user_metadata,
            runtime_type=runtime_type_str,
            control_plane_url=control_plane_url,
            api_key=api_key,
            initial_message_timestamp=initial_timestamp,
            graph_api_url=resolved_env.get("graph_api_url"),
            dataset_name=resolved_env.get("dataset_name"),
        )

        workflow_handle = await temporal_client.start_workflow(
            TeamExecutionWorkflow.run,
            workflow_input,  # Pass TeamExecutionInput directly
            id=f"team-execution-{execution_id}",
            task_queue=task_queue,
        )

        logger.info(
            "team_execution_submitted",
            execution_id=execution_id,
            team_id=team_id,
            workflow_id=workflow_handle.id,
            task_queue=task_queue,
            temporal_namespace=temporal_credentials["namespace"],
            worker_queue_id=worker_queue_id,
            worker_queue_name=worker_queue.name,
            org_id=organization["id"],
            org_name=organization["name"],
        )

        return TeamExecutionResponse(
            execution_id=execution_id,
            workflow_id=workflow_handle.id,
            status="PENDING",
            message=f"Execution submitted to worker queue: {worker_queue.name}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "team_execution_failed",
            error=str(e),
            team_id=team_id,
            org_id=organization["id"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute team: {str(e)}"
        )


@router.post("/{team_id}/execute/stream")
def execute_team_stream(
    team_id: str,
    execution_request: TeamExecutionRequest,
    db: Session = Depends(get_db),
):
    """
    Execute a team task with streaming response.

    The team leader coordinates and delegates the task to appropriate team members.
    Results are streamed back in real-time.
    """
    from control_plane_api.app.services.litellm_service import litellm_service

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get team agents
    agents = team.agents
    if not agents:
        raise HTTPException(
            status_code=400,
            detail="Team has no agents. Add agents to the team before executing tasks."
        )

    # Build team coordination prompt
    agent_descriptions = []
    for agent in agents:
        caps = ", ".join(agent.capabilities) if agent.capabilities else "general"
        agent_descriptions.append(
            f"- {agent.name}: {agent.description or 'No description'} (Capabilities: {caps})"
        )

    # Create a coordination system prompt
    coordination_prompt = f"""You are a Team Coordinator managing a team with the following agents:

{chr(10).join(agent_descriptions)}

Your task is to:
1. Analyze the user's request
2. Determine which agent(s) are best suited for the task
3. Delegate or route the task appropriately
4. Synthesize and present the results

User Request: {execution_request.prompt}

Please coordinate the team to complete this request effectively."""

    # Parse team configuration
    team_config = TeamConfiguration(**(team.configuration or {}))

    # Use LLM config from team configuration if available
    model = team_config.llm.model if team_config.llm and team_config.llm.model else "kubiya/claude-sonnet-4"

    # Build LLM kwargs from configuration
    llm_kwargs = {}
    if team_config.llm:
        if team_config.llm.temperature is not None:
            llm_kwargs["temperature"] = team_config.llm.temperature
        if team_config.llm.max_tokens is not None:
            llm_kwargs["max_tokens"] = team_config.llm.max_tokens
        if team_config.llm.top_p is not None:
            llm_kwargs["top_p"] = team_config.llm.top_p
        if team_config.llm.stop is not None:
            llm_kwargs["stop"] = team_config.llm.stop
        if team_config.llm.frequency_penalty is not None:
            llm_kwargs["frequency_penalty"] = team_config.llm.frequency_penalty
        if team_config.llm.presence_penalty is not None:
            llm_kwargs["presence_penalty"] = team_config.llm.presence_penalty

    # Execute coordination using LiteLLM (streaming)
    return StreamingResponse(
        litellm_service.execute_agent_stream(
            prompt=coordination_prompt,
            model=model,
            system_prompt=execution_request.system_prompt or "You are an expert team coordinator. Delegate tasks efficiently and synthesize results clearly.",
            **llm_kwargs,
        ),
        media_type="text/event-stream",
    )
