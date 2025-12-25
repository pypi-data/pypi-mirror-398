"""
Multi-tenant skills router.

This router handles skill CRUD operations and associations with agents/teams/environments.
All operations are scoped to the authenticated organization.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import structlog
import uuid

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.inspection import inspect
from control_plane_api.app.models.skill import Skill, SkillAssociation
from control_plane_api.app.models.agent import Agent
from control_plane_api.app.models.team import Team
from control_plane_api.app.models.environment import Environment
from control_plane_api.app.models.associations import AgentEnvironment, TeamEnvironment
from control_plane_api.app.lib.kubiya_client import get_kubiya_client
from control_plane_api.app.skills import get_all_skills, get_skill, SkillType

logger = structlog.get_logger()

router = APIRouter()


# Pydantic schemas
class ToolSetConfiguration(BaseModel):
    """Configuration for a skill"""
    # File System
    base_dir: Optional[str] = None
    enable_save_file: Optional[bool] = None
    enable_read_file: Optional[bool] = None
    enable_list_files: Optional[bool] = None
    enable_search_files: Optional[bool] = None

    # Shell
    allowed_commands: Optional[List[str]] = None
    blocked_commands: Optional[List[str]] = None
    timeout: Optional[int] = None

    # Docker
    enable_container_management: Optional[bool] = None
    enable_image_management: Optional[bool] = None
    enable_volume_management: Optional[bool] = None
    enable_network_management: Optional[bool] = None

    # Python
    enable_code_execution: Optional[bool] = None
    allowed_imports: Optional[List[str]] = None
    blocked_imports: Optional[List[str]] = None

    # File Generation
    enable_json_generation: Optional[bool] = None
    enable_csv_generation: Optional[bool] = None
    enable_pdf_generation: Optional[bool] = None
    enable_txt_generation: Optional[bool] = None
    output_directory: Optional[str] = None

    # Data Visualization
    max_diagram_size: Optional[int] = None
    enable_flowchart: Optional[bool] = None
    enable_sequence: Optional[bool] = None
    enable_class_diagram: Optional[bool] = None
    enable_er_diagram: Optional[bool] = None
    enable_gantt: Optional[bool] = None
    enable_pie_chart: Optional[bool] = None
    enable_state_diagram: Optional[bool] = None
    enable_git_graph: Optional[bool] = None
    enable_user_journey: Optional[bool] = None
    enable_quadrant_chart: Optional[bool] = None

    # Workflow Executor
    workflow_type: Optional[str] = Field(None, description="Workflow type: 'json' or 'python_dsl'")
    workflow_definition: Optional[str] = Field(None, description="JSON workflow definition as string")
    python_dsl_code: Optional[str] = Field(None, description="Python DSL code for workflow")
    validation_enabled: Optional[bool] = Field(None, description="Enable workflow validation")
    default_runner: Optional[str] = Field(None, description="Default runner/environment name")

    # Custom
    custom_class: Optional[str] = None
    custom_config: Optional[dict] = None


class ToolSetCreate(BaseModel):
    name: str = Field(..., description="Skill name")
    type: str = Field(..., description="Skill type (file_system, shell, docker, python, etc.)")
    description: Optional[str] = Field(None, description="Skill description")
    icon: Optional[str] = Field("Wrench", description="Icon name")
    enabled: bool = Field(True, description="Whether skill is enabled")
    configuration: ToolSetConfiguration = Field(default_factory=ToolSetConfiguration)


class ToolSetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    enabled: Optional[bool] = None
    configuration: Optional[ToolSetConfiguration] = None


class ToolSetResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    type: str  # Aliased from skill_type in SQL query
    description: Optional[str]
    icon: str
    enabled: bool
    configuration: dict
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    def ensure_id_is_string(cls, v):
        if v is None:
            return None
        return str(v)


class ToolSetAssociationCreate(BaseModel):
    skill_id: str = Field(..., description="Skill ID to associate")
    configuration_override: Optional[ToolSetConfiguration] = Field(None, description="Entity-specific config overrides")


class ResolvedToolSet(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str]
    icon: str
    enabled: bool
    configuration: dict
    source: str  # "environment", "team", "agent"
    inherited: bool


# Helper functions
def get_skill_by_id(db: Session, organization_id: str, skill_id: str) -> dict:
    """Get a skill by ID, scoped to organization"""
    skill = db.query(Skill).filter(
        Skill.organization_id == organization_id,
        Skill.id == skill_id
    ).first()

    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill {skill_id} not found")

    # Convert to dict and alias skill_type as type
    skill_dict = {c.key: getattr(skill, c.key) for c in inspect(skill).mapper.column_attrs}
    # Convert UUID fields to strings for Pydantic validation
    if "id" in skill_dict and skill_dict["id"] is not None:
        skill_dict["id"] = str(skill_dict["id"])
    skill_dict["type"] = skill_dict.pop("skill_type")
    return skill_dict


def get_entity_skills(db: Session, organization_id: str, entity_type: str, entity_id: str) -> List[dict]:
    """Get skills associated with an entity"""
    # Get associations with joined skills
    associations = db.query(SkillAssociation).join(Skill).filter(
        SkillAssociation.organization_id == organization_id,
        SkillAssociation.entity_type == entity_type,
        SkillAssociation.entity_id == entity_id,
        Skill.enabled == True
    ).all()

    skills = []
    for assoc in associations:
        skill = assoc.skill
        # Convert skill to dict and alias skill_type as type
        skill_dict = {c.key: getattr(skill, c.key) for c in inspect(skill).mapper.column_attrs}
        # Convert UUID fields to strings for Pydantic validation
        if "id" in skill_dict and skill_dict["id"] is not None:
            skill_dict["id"] = str(skill_dict["id"])
        skill_dict["type"] = skill_dict.pop("skill_type")

        # Merge configuration with override
        config = skill_dict.get("configuration", {})
        override = assoc.configuration_override
        if override:
            config = {**config, **override}

        skill_dict["configuration"] = config
        skills.append(skill_dict)

    return skills


def merge_configurations(base: dict, override: dict) -> dict:
    """Merge two configuration dictionaries, with override taking precedence"""
    result = base.copy()
    for key, value in override.items():
        if value is not None:
            result[key] = value
    return result


async def validate_workflow_runner(config: dict, token: str, org_id: str) -> None:
    """
    Validate that runners specified in workflow configuration exist.

    Args:
        config: Workflow executor configuration
        token: Kubiya API token
        org_id: Organization ID

    Raises:
        HTTPException: If runner validation fails
    """
    import json as json_lib

    # Extract runners to validate
    runners_to_check = []

    # Check default_runner
    if config.get("default_runner"):
        runners_to_check.append(("default_runner", config["default_runner"]))

    # Check workflow-level runner in JSON workflows
    if config.get("workflow_type") == "json" and config.get("workflow_definition"):
        try:
            workflow_data = json_lib.loads(config["workflow_definition"])
            if workflow_data.get("runner"):
                runners_to_check.append(("workflow.runner", workflow_data["runner"]))
        except json_lib.JSONDecodeError:
            # Invalid JSON - will be caught by skill validation
            pass

    if not runners_to_check:
        # No runners specified, will use default
        return

    # Fetch available runners from Kubiya API
    try:
        kubiya_client = get_kubiya_client()
        available_runners = await kubiya_client.get_runners(token, org_id)

        if not available_runners:
            logger.warning(
                "no_runners_available_skipping_validation",
                org_id=org_id
            )
            return

        # Extract runner names/IDs from the response
        runner_names = set()
        for runner in available_runners:
            if isinstance(runner, dict):
                # Add both 'name' and 'id' to the set
                if runner.get("name"):
                    runner_names.add(runner["name"])
                if runner.get("id"):
                    runner_names.add(runner["id"])

        # Validate each runner
        for field_name, runner_value in runners_to_check:
            if runner_value not in runner_names:
                available_list = sorted(list(runner_names))
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid runner '{runner_value}' specified in {field_name}. "
                        f"Available runners: {', '.join(available_list) if available_list else 'none'}"
                    )
                )

        logger.info(
            "workflow_runners_validated",
            runners_checked=[r[1] for r in runners_to_check],
            available_count=len(runner_names)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "runner_validation_failed",
            error=str(e),
            org_id=org_id
        )
        # Don't fail skill creation if runner validation fails
        # This allows offline/testing scenarios
        logger.warning("skipping_runner_validation_due_to_error")


# API Endpoints

@router.post("", response_model=ToolSetResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: ToolSetCreate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Create a new skill in the organization"""
    try:
        skill_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Validate skill type
        valid_types = ["file_system", "shell", "python", "docker", "sleep", "file_generation", "data_visualization", "workflow_executor", "custom"]
        if skill_data.type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid skill type. Must be one of: {', '.join(valid_types)}"
            )

        # Validate workflow_executor runner if applicable
        if skill_data.type == "workflow_executor":
            config_dict = skill_data.configuration.dict(exclude_none=True)
            token = request.state.kubiya_token
            await validate_workflow_runner(config_dict, token, organization["id"])

        skill = Skill(
            id=skill_id,
            organization_id=organization["id"],
            name=skill_data.name,
            skill_type=skill_data.type,
            description=skill_data.description,
            icon=skill_data.icon,
            enabled=skill_data.enabled,
            configuration=skill_data.configuration.dict(exclude_none=True),
            created_at=now,
            updated_at=now,
        )

        db.add(skill)
        db.commit()
        db.refresh(skill)

        logger.info(
            "skill_created",
            skill_id=skill_id,
            name=skill_data.name,
            type=skill_data.type,
            organization_id=organization["id"]
        )

        # Convert to dict and alias skill_type as type
        skill_dict = {c.key: getattr(skill, c.key) for c in inspect(skill).mapper.column_attrs}
        skill_dict["type"] = skill_dict.pop("skill_type")

        return ToolSetResponse(**skill_dict)

    except Exception as e:
        logger.error("skill_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ToolSetResponse])
async def list_skills(
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List all skills for the organization"""
    try:
        skills = db.query(Skill).filter(
            Skill.organization_id == organization["id"]
        ).order_by(desc(Skill.created_at)).all()

        # Convert to list of dicts with aliased skill_type as type
        skills_data = []
        for skill in skills:
            skill_dict = {c.key: getattr(skill, c.key) for c in inspect(skill).mapper.column_attrs}
            skill_dict["type"] = skill_dict.pop("skill_type")
            skills_data.append(ToolSetResponse(**skill_dict))

        return skills_data

    except Exception as e:
        logger.error("skill_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}", response_model=ToolSetResponse)
async def get_skill_endpoint(
    skill_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get a specific skill"""
    try:
        skill = get_skill_by_id(db, organization["id"], skill_id)
        return ToolSetResponse(**skill)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("skill_get_failed", error=str(e), skill_id=skill_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{skill_id}", response_model=ToolSetResponse)
async def update_skill(
    skill_id: str,
    skill_data: ToolSetUpdate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Update a skill"""
    try:
        # Verify skill exists
        skill = db.query(Skill).filter(
            Skill.id == skill_id,
            Skill.organization_id == organization["id"]
        ).first()

        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill {skill_id} not found")

        # Build update dict
        update_data = skill_data.dict(exclude_none=True)
        if "configuration" in update_data:
            update_data["configuration"] = update_data["configuration"]
        update_data["updated_at"] = datetime.utcnow()

        # Validate workflow_executor runner if updating configuration
        if skill.skill_type == "workflow_executor" and "configuration" in update_data:
            # Merge existing config with updates for complete validation
            merged_config = {**(skill.configuration or {}), **update_data["configuration"]}
            token = request.state.kubiya_token
            await validate_workflow_runner(merged_config, token, organization["id"])

        # Apply updates
        for key, value in update_data.items():
            setattr(skill, key, value)

        db.commit()
        db.refresh(skill)

        logger.info("skill_updated", skill_id=skill_id, organization_id=organization["id"])

        # Convert to dict and alias skill_type as type
        skill_dict = {c.key: getattr(skill, c.key) for c in inspect(skill).mapper.column_attrs}
        skill_dict["type"] = skill_dict.pop("skill_type")

        return ToolSetResponse(**skill_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("skill_update_failed", error=str(e), skill_id=skill_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Delete a skill"""
    try:
        # Verify skill exists
        skill = db.query(Skill).filter(
            Skill.id == skill_id,
            Skill.organization_id == organization["id"]
        ).first()

        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill {skill_id} not found")

        # Delete skill (cascade will handle associations)
        db.delete(skill)
        db.commit()

        logger.info("skill_deleted", skill_id=skill_id, organization_id=organization["id"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error("skill_delete_failed", error=str(e), skill_id=skill_id)
        raise HTTPException(status_code=500, detail=str(e))


# Association endpoints for agents
@router.post("/associations/{entity_type}/{entity_id}/skills", status_code=status.HTTP_201_CREATED)
async def associate_skill(
    entity_type: str,
    entity_id: str,
    association_data: ToolSetAssociationCreate,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Associate a skill with an entity (agent, team, environment)"""
    try:
        # Validate entity type
        if entity_type not in ["agent", "team", "environment"]:
            raise HTTPException(status_code=400, detail="Invalid entity type. Must be: agent, team, or environment")

        # Verify skill exists
        get_skill_by_id(db, organization["id"], association_data.skill_id)

        # Verify entity exists (check appropriate table)
        entity_model = None
        if entity_type == "agent":
            entity_model = Agent
        elif entity_type == "team":
            entity_model = Team
        elif entity_type == "environment":
            entity_model = Environment

        entity = db.query(entity_model).filter(
            entity_model.id == entity_id,
            entity_model.organization_id == organization["id"]
        ).first()

        if not entity:
            raise HTTPException(status_code=404, detail=f"{entity_type.capitalize()} {entity_id} not found")

        # Create association
        association_id = str(uuid.uuid4())
        association = SkillAssociation(
            id=association_id,
            organization_id=organization["id"],
            skill_id=association_data.skill_id,
            entity_type=entity_type,
            entity_id=entity_id,
            configuration_override=association_data.configuration_override.dict(exclude_none=True) if association_data.configuration_override else {},
            created_at=datetime.utcnow(),
        )

        db.add(association)

        # Also update denormalized skill_ids array (only for teams)
        # Agents and environments don't have a skill_ids column - they only use the skill_associations junction table
        # Teams have a denormalized skill_ids array for performance
        if entity_type == "team":
            current_ids = entity.skill_ids or []
            if association_data.skill_id not in current_ids:
                updated_ids = current_ids + [association_data.skill_id]
                entity.skill_ids = updated_ids

        db.commit()

        logger.info(
            "skill_associated",
            skill_id=association_data.skill_id,
            entity_type=entity_type,
            entity_id=entity_id,
            organization_id=organization["id"]
        )

        return {"message": "Skill associated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("skill_association_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/associations/{entity_type}/{entity_id}/skills", response_model=List[ToolSetResponse])
async def list_entity_skills(
    entity_type: str,
    entity_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List skills associated with an entity"""
    try:
        if entity_type not in ["agent", "team", "environment"]:
            raise HTTPException(status_code=400, detail="Invalid entity type")

        skills = get_entity_skills(db, organization["id"], entity_type, entity_id)
        return [ToolSetResponse(**skill) for skill in skills]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_entity_skills_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/associations/{entity_type}/{entity_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def dissociate_skill(
    entity_type: str,
    entity_id: str,
    skill_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Remove a skill association from an entity"""
    try:
        if entity_type not in ["agent", "team", "environment"]:
            raise HTTPException(status_code=400, detail="Invalid entity type")

        # Delete association
        db.query(SkillAssociation).filter(
            SkillAssociation.skill_id == skill_id,
            SkillAssociation.entity_type == entity_type,
            SkillAssociation.entity_id == entity_id
        ).delete()

        # Update denormalized skill_ids array (only for teams)
        # Agents and environments don't have a skill_ids column - they only use the skill_associations junction table
        # Teams have a denormalized skill_ids array for performance
        if entity_type == "team":
            team = db.query(Team).filter(Team.id == entity_id).first()
            if team:
                current_ids = team.skill_ids or []
                updated_ids = [tid for tid in current_ids if tid != skill_id]
                team.skill_ids = updated_ids

        db.commit()

        logger.info(
            "skill_dissociated",
            skill_id=skill_id,
            entity_type=entity_type,
            entity_id=entity_id,
            organization_id=organization["id"]
        )

    except Exception as e:
        logger.error("skill_dissociation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/associations/agents/{agent_id}/skills/resolved", response_model=List[ResolvedToolSet])
async def resolve_agent_skills(
    agent_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Resolve all skills for an agent (including inherited from ALL environments and team).

    Inheritance order (with deduplication):
    1. All agent environments
    2. All team environments (if agent has team)
    3. Team skills
    4. Agent skills

    Later layers override earlier ones if there are conflicts.
    """
    try:
        # Get agent details
        agent = db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.organization_id == organization["id"]
        ).first()

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        resolved_skills = []
        seen_ids = set()

        # 1. Load skills from ALL agent environments (many-to-many)
        agent_envs = db.query(AgentEnvironment).filter(
            AgentEnvironment.agent_id == agent_id
        ).all()

        agent_environment_ids = [str(env.environment_id) for env in agent_envs]

        for environment_id in agent_environment_ids:
            env_skills = get_entity_skills(db, organization["id"], "environment", environment_id)
            for skill in env_skills:
                if skill["id"] not in seen_ids:
                    resolved_skills.append(ResolvedToolSet(
                        **skill,
                        source="environment",
                        inherited=True
                    ))
                    seen_ids.add(skill["id"])

        # 2. Load skills from ALL team environments (if agent has team)
        team_id = agent.team_id
        team_environment_ids = []
        if team_id:
            team_envs = db.query(TeamEnvironment).filter(
                TeamEnvironment.team_id == team_id
            ).all()

            team_environment_ids = [str(env.environment_id) for env in team_envs]

            for environment_id in team_environment_ids:
                env_skills = get_entity_skills(db, organization["id"], "environment", environment_id)
                for skill in env_skills:
                    if skill["id"] not in seen_ids:
                        resolved_skills.append(ResolvedToolSet(
                            **skill,
                            source="environment",
                            inherited=True
                        ))
                        seen_ids.add(skill["id"])

            # 3. Load team skills
            team_skills = get_entity_skills(db, organization["id"], "team", str(team_id))
            for skill in team_skills:
                if skill["id"] not in seen_ids:
                    resolved_skills.append(ResolvedToolSet(
                        **skill,
                        source="team",
                        inherited=True
                    ))
                    seen_ids.add(skill["id"])

        # 4. Load agent skills (highest priority)
        agent_skills = get_entity_skills(db, organization["id"], "agent", agent_id)
        for skill in agent_skills:
            if skill["id"] not in seen_ids:
                resolved_skills.append(ResolvedToolSet(
                    **skill,
                    source="agent",
                    inherited=False
                ))
                seen_ids.add(skill["id"])

        logger.info(
            "agent_skills_resolved",
            agent_id=agent_id,
            skill_count=len(resolved_skills),
            agent_env_count=len(agent_environment_ids),
            team_env_count=len(team_environment_ids) if team_id else 0,
            organization_id=organization["id"]
        )

        return resolved_skills

    except HTTPException:
        raise
    except Exception as e:
        logger.error("resolve_agent_skills_failed", error=str(e), agent_id=agent_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/associations/agents/{agent_id}/toolsets/resolved", response_model=List[ResolvedToolSet])
async def resolve_agent_toolsets_legacy(
    agent_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    DEPRECATED: Legacy endpoint for backward compatibility.
    Use /associations/agents/{agent_id}/skills/resolved instead.

    This endpoint redirects to the new skills endpoint.
    """
    logger.warning(
        "deprecated_toolsets_endpoint_used",
        agent_id=agent_id,
        endpoint="/associations/agents/{agent_id}/toolsets/resolved",
        new_endpoint="/associations/agents/{agent_id}/skills/resolved"
    )
    return await resolve_agent_skills(agent_id, organization, db)


@router.get("/associations/teams/{team_id}/skills/resolved", response_model=List[ResolvedToolSet])
async def resolve_team_skills(
    team_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Resolve all skills for a team (including inherited from ALL environments).

    Inheritance order (with deduplication):
    1. All team environments
    2. Team skills

    Later layers override earlier ones if there are conflicts.
    """
    try:
        # Get team details
        team = db.query(Team).filter(
            Team.id == team_id,
            Team.organization_id == organization["id"]
        ).first()

        if not team:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

        resolved_skills = []
        seen_ids = set()

        # 1. Load skills from ALL team environments (many-to-many)
        team_envs = db.query(TeamEnvironment).filter(
            TeamEnvironment.team_id == team_id
        ).all()

        team_environment_ids = [str(env.environment_id) for env in team_envs]

        for environment_id in team_environment_ids:
            env_skills = get_entity_skills(db, organization["id"], "environment", environment_id)
            for skill in env_skills:
                if skill["id"] not in seen_ids:
                    resolved_skills.append(ResolvedToolSet(
                        **skill,
                        source="environment",
                        inherited=True
                    ))
                    seen_ids.add(skill["id"])

        # 2. Load team skills (highest priority)
        team_skills = get_entity_skills(db, organization["id"], "team", team_id)
        for skill in team_skills:
            if skill["id"] not in seen_ids:
                resolved_skills.append(ResolvedToolSet(
                    **skill,
                    source="team",
                    inherited=False
                ))
                seen_ids.add(skill["id"])

        logger.info(
            "team_skills_resolved",
            team_id=team_id,
            skill_count=len(resolved_skills),
            team_env_count=len(team_environment_ids),
            organization_id=organization["id"]
        )

        return resolved_skills

    except HTTPException:
        raise
    except Exception as e:
        logger.error("resolve_team_skills_failed", error=str(e), team_id=team_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/associations/teams/{team_id}/toolsets/resolved", response_model=List[ResolvedToolSet])
async def resolve_team_toolsets_legacy(
    team_id: str,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    DEPRECATED: Legacy endpoint for backward compatibility.
    Use /associations/teams/{team_id}/skills/resolved instead.

    This endpoint redirects to the new skills endpoint.
    """
    logger.warning(
        "deprecated_toolsets_endpoint_used",
        team_id=team_id,
        endpoint="/associations/teams/{team_id}/toolsets/resolved",
        new_endpoint="/associations/teams/{team_id}/skills/resolved"
    )
    return await resolve_team_skills(team_id, organization, db)


@router.get("/types")
async def get_skill_types():
    """Get available skill types and their descriptions"""
    return {
        "types": [
            {
                "type": "file_system",
                "name": "File System",
                "description": "Read, write, list, and search files",
                "icon": "FileText"
            },
            {
                "type": "shell",
                "name": "Shell",
                "description": "Execute shell commands",
                "icon": "Terminal"
            },
            {
                "type": "docker",
                "name": "Docker",
                "description": "Manage containers, images, volumes, and networks",
                "icon": "Container"
            },
            {
                "type": "python",
                "name": "Python",
                "description": "Execute Python code",
                "icon": "Code"
            },
            {
                "type": "file_generation",
                "name": "File Generation",
                "description": "Generate JSON, CSV, PDF, and TXT files",
                "icon": "FileOutput"
            },
            {
                "type": "sleep",
                "name": "Sleep",
                "description": "Pause execution for a specified duration",
                "icon": "Clock"
            },
            {
                "type": "workflow_executor",
                "name": "Workflow Executor",
                "description": "Execute workflows defined via JSON or Python DSL",
                "icon": "Workflow"
            },
            {
                "type": "custom",
                "name": "Custom",
                "description": "User-defined custom skill",
                "icon": "Wrench"
            }
        ]
    }


@router.get("/templates")
async def get_skill_templates(
    request: Request,
    organization: dict = Depends(get_current_organization),
):
    """
    Get detailed skill templates with variants and configuration schemas.

    This endpoint returns all available skill templates including their variants,
    configuration schemas, default values, and available runners for workflow executor skills.
    Useful for UI forms and skill creation.
    """
    templates = []

    # Get all registered skills from the skill system
    all_skills = get_all_skills()

    # Fetch available runners for workflow executor validation
    runners_list = []
    try:
        kubiya_client = get_kubiya_client()
        token = request.state.kubiya_token
        available_runners = await kubiya_client.get_runners(token, organization["id"])

        if available_runners:
            for runner in available_runners:
                if isinstance(runner, dict):
                    runners_list.append({
                        "id": runner.get("id"),
                        "name": runner.get("name"),
                        "status": runner.get("status"),
                        "capabilities": runner.get("capabilities", []),
                    })

        logger.info(
            "runners_fetched_for_templates",
            org_id=organization["id"],
            runner_count=len(runners_list)
        )
    except Exception as e:
        logger.warning(
            "failed_to_fetch_runners_for_templates",
            error=str(e),
            org_id=organization["id"]
        )
        # Continue without runners - they're optional

    for skill_def in all_skills:
        try:
            # Get skill metadata
            template = {
                "type": skill_def.type.value,
                "name": skill_def.name,
                "description": skill_def.description,
                "icon": skill_def.icon,
                "icon_type": skill_def.icon_type,
                "category": skill_def.get_category().value,
                "default_configuration": skill_def.get_default_configuration(),
                "requirements": {
                    "supported_os": skill_def.get_requirements().supported_os,
                    "min_python_version": skill_def.get_requirements().min_python_version,
                    "python_packages": skill_def.get_requirements().python_packages,
                    "required_env_vars": skill_def.get_requirements().required_env_vars,
                    "notes": skill_def.get_requirements().notes,
                } if skill_def.get_requirements() else None,
                "variants": []
            }

            # Add available runners for workflow executor skills
            if skill_def.type.value == "workflow_executor":
                template["available_runners"] = runners_list

            # Get variants for this skill
            variants = skill_def.get_variants()
            for variant in variants:
                template["variants"].append({
                    "id": variant.id,
                    "name": variant.name,
                    "description": variant.description,
                    "category": variant.category.value,
                    "icon": variant.icon,
                    "is_default": variant.is_default,
                    "configuration": variant.configuration,
                    "tags": variant.tags,
                })

            templates.append(template)

        except Exception as e:
            logger.error(
                "failed_to_build_skill_template",
                skill_type=skill_def.type.value if hasattr(skill_def, 'type') else 'unknown',
                error=str(e)
            )
            continue

    return {
        "templates": templates,
        "count": len(templates),
        "runners": runners_list  # Also return at root level for easy access
    }
