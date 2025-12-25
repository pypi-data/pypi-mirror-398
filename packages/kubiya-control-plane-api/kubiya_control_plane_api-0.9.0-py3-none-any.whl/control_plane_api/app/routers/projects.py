"""
Projects router - Jira-style multi-project management.

This router handles project CRUD operations and manages associations
between projects, agents, and teams.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import structlog
import uuid

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from control_plane_api.app.models.project import Project
from control_plane_api.app.models.project_management import ProjectAgent, ProjectTeam
from control_plane_api.app.models.agent import Agent
from control_plane_api.app.models.team import Team

logger = structlog.get_logger()

router = APIRouter()


# Pydantic schemas
class ProjectCreate(BaseModel):
    name: str = Field(..., description="Project name")
    key: str = Field(..., description="Short project key (e.g., JIRA, PROJ)", min_length=2, max_length=50)
    description: str | None = Field(None, description="Project description")
    goals: str | None = Field(None, description="Project goals and objectives")
    settings: dict = Field(default_factory=dict, description="Project settings")
    visibility: str = Field("private", description="Project visibility: private or org")
    restrict_to_environment: bool = Field(False, description="Restrict to specific runners/environment")
    policy_ids: List[str] = Field(default_factory=list, description="List of OPA policy IDs for access control")
    default_model: str | None = Field(None, description="Default LLM model for this project")


class ProjectUpdate(BaseModel):
    name: str | None = None
    key: str | None = None
    description: str | None = None
    goals: str | None = None
    settings: dict | None = None
    status: str | None = None
    visibility: str | None = None
    restrict_to_environment: bool | None = None
    policy_ids: List[str] | None = None
    default_model: str | None = None


class ProjectResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    key: str
    description: str | None
    goals: str | None
    settings: dict
    status: str
    visibility: str
    owner_id: str | None
    owner_email: str | None
    restrict_to_environment: bool = False
    policy_ids: List[str] = []
    default_model: str | None = None
    created_at: str
    updated_at: str
    archived_at: str | None

    # Counts
    agent_count: int = 0
    team_count: int = 0


class ProjectAgentAdd(BaseModel):
    agent_id: str = Field(..., description="Agent UUID to add to project")
    role: str | None = Field(None, description="Agent role in project")


class ProjectTeamAdd(BaseModel):
    team_id: str = Field(..., description="Team UUID to add to project")
    role: str | None = Field(None, description="Team role in project")


def ensure_default_project(db: Session, organization: dict) -> Optional[dict]:
    """
    Ensure the organization has a default project.
    Creates one if it doesn't exist.

    Returns the default project or None if creation failed.
    """
    try:
        # Check if default project exists
        existing = db.query(Project).filter(
            Project.organization_id == organization["id"],
            Project.key == "DEFAULT"
        ).first()

        if existing:
            return {
                "id": str(existing.id),
                "organization_id": str(existing.organization_id),
                "name": existing.name,
                "key": existing.key,
                "description": existing.description,
                "settings": existing.settings or {},
                "status": existing.status,
                "visibility": existing.visibility,
                "owner_id": existing.owner_id,
                "owner_email": existing.owner_email,
                "created_at": existing.created_at.isoformat() if existing.created_at else None,
                "updated_at": existing.updated_at.isoformat() if existing.updated_at else None,
                "archived_at": existing.archived_at.isoformat() if existing.archived_at else None,
            }

        # Create default project
        now = datetime.utcnow()

        default_project = Project(
            organization_id=organization["id"],
            name="Default",
            key="DEFAULT",
            description="Default project for agents and teams",
            settings={
                "policy_ids": [],
                "default_model": None,
                "goals": None,
                "restrict_to_environment": False
            },
            status="active",
            visibility="org",
            owner_id=organization.get("user_id"),
            owner_email=organization.get("user_email"),
            created_at=now,
            updated_at=now,
        )

        db.add(default_project)
        db.commit()
        db.refresh(default_project)

        logger.info(
            "default_project_created",
            project_id=str(default_project.id),
            org_id=organization["id"],
        )

        return {
            "id": str(default_project.id),
            "organization_id": str(default_project.organization_id),
            "name": default_project.name,
            "key": default_project.key,
            "description": default_project.description,
            "settings": default_project.settings or {},
            "status": default_project.status,
            "visibility": default_project.visibility,
            "owner_id": default_project.owner_id,
            "owner_email": default_project.owner_email,
            "created_at": default_project.created_at.isoformat() if default_project.created_at else None,
            "updated_at": default_project.updated_at.isoformat() if default_project.updated_at else None,
            "archived_at": default_project.archived_at.isoformat() if default_project.archived_at else None,
        }

    except Exception as e:
        logger.error("ensure_default_project_failed", error=str(e), org_id=organization.get("id"))
        db.rollback()
        return None


def get_default_project_id(db: Session, organization: dict) -> Optional[str]:
    """
    Get the default project ID for an organization.
    Creates the default project if it doesn't exist.

    Returns the project ID or None if creation failed.
    """
    project = ensure_default_project(db, organization)
    return project["id"] if project else None


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Create a new project"""
    try:
        # Check if key already exists for this organization
        existing = db.query(Project).filter(
            Project.organization_id == organization["id"],
            Project.key == project_data.key.upper()
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project with key '{project_data.key.upper()}' already exists"
            )

        now = datetime.utcnow()

        project = Project(
            organization_id=organization["id"],
            name=project_data.name,
            key=project_data.key.upper(),
            description=project_data.description,
            # Store policy_ids, default_model, goals, and restrict_to_environment in settings JSON field
            settings={
                **project_data.settings,
                "policy_ids": project_data.policy_ids,
                "default_model": project_data.default_model,
                "goals": project_data.goals,
                "restrict_to_environment": project_data.restrict_to_environment
            },
            status="active",
            visibility=project_data.visibility,
            owner_id=organization.get("user_id"),
            owner_email=organization.get("user_email"),
            created_at=now,
            updated_at=now,
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        logger.info(
            "project_created",
            project_id=str(project.id),
            project_key=project.key,
            org_id=organization["id"],
        )

        # Extract policy_ids, default_model, goals, and restrict_to_environment from settings for response
        settings = project.settings or {}
        policy_ids = settings.get("policy_ids", [])
        default_model = settings.get("default_model")
        goals = settings.get("goals")
        restrict_to_environment = settings.get("restrict_to_environment", False)

        return ProjectResponse(
            id=str(project.id),
            organization_id=str(project.organization_id),
            name=project.name,
            key=project.key,
            description=project.description,
            goals=goals,
            settings=settings,
            status=project.status,
            visibility=project.visibility,
            owner_id=project.owner_id,
            owner_email=project.owner_email,
            restrict_to_environment=restrict_to_environment,
            policy_ids=policy_ids,
            default_model=default_model,
            created_at=project.created_at.isoformat() if project.created_at else None,
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
            archived_at=project.archived_at.isoformat() if project.archived_at else None,
            agent_count=0,
            team_count=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("project_creation_failed", error=str(e), org_id=organization["id"])
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/default", response_model=ProjectResponse)
async def get_default_project(
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get the default project for the organization (creates if doesn't exist)"""
    try:
        # Ensure default project exists
        default_project = ensure_default_project(db, organization)

        if not default_project:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get or create default project"
            )

        # Get counts for the default project
        agent_count = db.query(func.count(ProjectAgent.id)).filter(
            ProjectAgent.project_id == default_project["id"]
        ).scalar() or 0

        team_count = db.query(func.count(ProjectTeam.id)).filter(
            ProjectTeam.project_id == default_project["id"]
        ).scalar() or 0

        # Extract settings fields
        settings = default_project.get("settings", {})
        policy_ids = settings.get("policy_ids", [])
        default_model = settings.get("default_model")
        goals = settings.get("goals")
        restrict_to_environment = settings.get("restrict_to_environment", False)

        return ProjectResponse(
            id=default_project["id"],
            organization_id=default_project["organization_id"],
            name=default_project["name"],
            key=default_project["key"],
            description=default_project["description"],
            goals=goals,
            settings=settings,
            status=default_project["status"],
            visibility=default_project["visibility"],
            owner_id=default_project["owner_id"],
            owner_email=default_project["owner_email"],
            restrict_to_environment=restrict_to_environment,
            policy_ids=policy_ids,
            default_model=default_model,
            created_at=default_project["created_at"],
            updated_at=default_project["updated_at"],
            archived_at=default_project.get("archived_at"),
            agent_count=agent_count,
            team_count=team_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_default_project_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get default project: {str(e)}"
        )


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    request: Request,
    status_filter: str | None = None,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List all projects in the organization"""
    try:
        # Ensure default project exists for this organization
        ensure_default_project(db, organization)

        # Query projects
        query = db.query(Project).filter(
            Project.organization_id == organization["id"]
        )

        if status_filter:
            query = query.filter(Project.status == status_filter)

        query = query.order_by(desc(Project.created_at))
        projects_objs = query.all()

        if not projects_objs:
            return []

        # Batch fetch all agent counts in one query
        project_ids = [str(project.id) for project in projects_objs]
        agent_counts = db.query(
            ProjectAgent.project_id,
            func.count(ProjectAgent.id).label("count")
        ).filter(
            ProjectAgent.project_id.in_(project_ids)
        ).group_by(ProjectAgent.project_id).all()

        # Build agent count map
        agent_count_map = {str(pc.project_id): pc.count for pc in agent_counts}

        # Batch fetch all team counts in one query
        team_counts = db.query(
            ProjectTeam.project_id,
            func.count(ProjectTeam.id).label("count")
        ).filter(
            ProjectTeam.project_id.in_(project_ids)
        ).group_by(ProjectTeam.project_id).all()

        # Build team count map
        team_count_map = {str(tc.project_id): tc.count for tc in team_counts}

        # Build response with pre-fetched counts
        projects = []
        for project in projects_objs:
            # Extract policy_ids, default_model, goals, and restrict_to_environment from settings for response
            settings = project.settings or {}
            policy_ids = settings.get("policy_ids", [])
            default_model = settings.get("default_model")
            goals = settings.get("goals")
            restrict_to_environment = settings.get("restrict_to_environment", False)

            projects.append(
                ProjectResponse(
                    id=str(project.id),
                    organization_id=str(project.organization_id),
                    name=project.name,
                    key=project.key,
                    description=project.description,
                    goals=goals,
                    settings=settings,
                    status=project.status,
                    visibility=project.visibility,
                    owner_id=project.owner_id,
                    owner_email=project.owner_email,
                    restrict_to_environment=restrict_to_environment,
                    policy_ids=policy_ids,
                    default_model=default_model,
                    created_at=project.created_at.isoformat() if project.created_at else None,
                    updated_at=project.updated_at.isoformat() if project.updated_at else None,
                    archived_at=project.archived_at.isoformat() if project.archived_at else None,
                    agent_count=agent_count_map.get(str(project.id), 0),
                    team_count=team_count_map.get(str(project.id), 0),
                )
            )

        logger.info(
            "projects_listed",
            count=len(projects),
            org_id=organization["id"],
        )

        return projects

    except Exception as e:
        logger.error("projects_list_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}"
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get a specific project by ID"""
    try:
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.organization_id == organization["id"]
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get counts
        agent_count = db.query(func.count(ProjectAgent.id)).filter(
            ProjectAgent.project_id == project_id
        ).scalar() or 0

        team_count = db.query(func.count(ProjectTeam.id)).filter(
            ProjectTeam.project_id == project_id
        ).scalar() or 0

        # Extract policy_ids, default_model, goals, and restrict_to_environment from settings for response
        settings = project.settings or {}
        policy_ids = settings.get("policy_ids", [])
        default_model = settings.get("default_model")
        goals = settings.get("goals")
        restrict_to_environment = settings.get("restrict_to_environment", False)

        return ProjectResponse(
            id=str(project.id),
            organization_id=str(project.organization_id),
            name=project.name,
            key=project.key,
            description=project.description,
            goals=goals,
            settings=settings,
            status=project.status,
            visibility=project.visibility,
            owner_id=project.owner_id,
            owner_email=project.owner_email,
            restrict_to_environment=restrict_to_environment,
            policy_ids=policy_ids,
            default_model=default_model,
            created_at=project.created_at.isoformat() if project.created_at else None,
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
            archived_at=project.archived_at.isoformat() if project.archived_at else None,
            agent_count=agent_count,
            team_count=team_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("project_get_failed", error=str(e), project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project: {str(e)}"
        )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Update a project"""
    try:
        # Check if project exists
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.organization_id == organization["id"]
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Build update dict
        update_data = project_data.model_dump(exclude_unset=True)

        # Handle policy_ids, default_model, goals, and restrict_to_environment - store in settings if provided
        settings_updates = {}
        if "policy_ids" in update_data:
            settings_updates["policy_ids"] = update_data.pop("policy_ids")
        if "default_model" in update_data:
            settings_updates["default_model"] = update_data.pop("default_model")
        if "goals" in update_data:
            settings_updates["goals"] = update_data.pop("goals")
        if "restrict_to_environment" in update_data:
            settings_updates["restrict_to_environment"] = update_data.pop("restrict_to_environment")

        # Apply settings updates if any
        if settings_updates:
            if "settings" in update_data:
                update_data["settings"].update(settings_updates)
            else:
                # Merge with existing settings
                existing_settings = project.settings or {}
                update_data["settings"] = {**existing_settings, **settings_updates}

        # Uppercase key if provided
        if "key" in update_data:
            update_data["key"] = update_data["key"].upper()

        # Apply updates to model
        for key, value in update_data.items():
            setattr(project, key, value)

        project.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(project)

        # Get counts
        agent_count = db.query(func.count(ProjectAgent.id)).filter(
            ProjectAgent.project_id == project_id
        ).scalar() or 0

        team_count = db.query(func.count(ProjectTeam.id)).filter(
            ProjectTeam.project_id == project_id
        ).scalar() or 0

        logger.info(
            "project_updated",
            project_id=project_id,
            org_id=organization["id"],
        )

        # Extract policy_ids, default_model, goals, and restrict_to_environment from settings for response
        settings = project.settings or {}
        policy_ids = settings.get("policy_ids", [])
        default_model = settings.get("default_model")
        goals = settings.get("goals")
        restrict_to_environment = settings.get("restrict_to_environment", False)

        return ProjectResponse(
            id=str(project.id),
            organization_id=str(project.organization_id),
            name=project.name,
            key=project.key,
            description=project.description,
            goals=goals,
            settings=settings,
            status=project.status,
            visibility=project.visibility,
            owner_id=project.owner_id,
            owner_email=project.owner_email,
            restrict_to_environment=restrict_to_environment,
            policy_ids=policy_ids,
            default_model=default_model,
            created_at=project.created_at.isoformat() if project.created_at else None,
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
            archived_at=project.archived_at.isoformat() if project.archived_at else None,
            agent_count=agent_count,
            team_count=team_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("project_update_failed", error=str(e), project_id=project_id)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Delete a project (cascades to associations)"""
    try:
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.organization_id == organization["id"]
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        db.delete(project)
        db.commit()

        logger.info("project_deleted", project_id=project_id, org_id=organization["id"])

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error("project_delete_failed", error=str(e), project_id=project_id)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )


# Agent associations
@router.post("/{project_id}/agents", status_code=status.HTTP_201_CREATED)
async def add_agent_to_project(
    project_id: str,
    agent_data: ProjectAgentAdd,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Add an agent to a project"""
    try:
        # Verify project exists
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.organization_id == organization["id"]
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify agent exists and belongs to org
        agent = db.query(Agent).filter(
            Agent.id == agent_data.agent_id,
            Agent.organization_id == organization["id"]
        ).first()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Add association
        now = datetime.utcnow()
        association = ProjectAgent(
            project_id=project_id,
            agent_id=agent_data.agent_id,
            role=agent_data.role,
            added_at=now,
            added_by=organization.get("user_id"),
        )

        db.add(association)
        db.commit()
        db.refresh(association)

        logger.info(
            "agent_added_to_project",
            project_id=project_id,
            agent_id=agent_data.agent_id,
            org_id=organization["id"],
        )

        return {
            "id": str(association.id),
            "project_id": str(association.project_id),
            "agent_id": str(association.agent_id),
            "role": association.role,
            "added_at": association.added_at.isoformat() if association.added_at else None,
            "added_by": association.added_by,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("add_agent_to_project_failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add agent: {str(e)}"
        )


@router.get("/{project_id}/agents")
async def list_project_agents(
    project_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List all agents in a project"""
    try:
        # Get project agents with agent details
        project_agents = db.query(ProjectAgent).options(
            joinedload(ProjectAgent.agent)
        ).filter(
            ProjectAgent.project_id == project_id
        ).all()

        # Build response with nested agent data
        result = []
        for pa in project_agents:
            agent_data = None
            if pa.agent:
                agent_data = {
                    "id": str(pa.agent.id),
                    "name": pa.agent.name,
                    "description": pa.agent.description,
                    "organization_id": str(pa.agent.organization_id),
                    "created_at": pa.agent.created_at.isoformat() if pa.agent.created_at else None,
                    "updated_at": pa.agent.updated_at.isoformat() if pa.agent.updated_at else None,
                }

            result.append({
                "id": str(pa.id),
                "project_id": str(pa.project_id),
                "agent_id": str(pa.agent_id),
                "role": pa.role,
                "added_at": pa.added_at.isoformat() if pa.added_at else None,
                "added_by": pa.added_by,
                "agents": agent_data,
            })

        logger.info(
            "project_agents_listed",
            project_id=project_id,
            count=len(result),
            org_id=organization["id"],
        )

        return result

    except Exception as e:
        logger.error("list_project_agents_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.delete("/{project_id}/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_agent_from_project(
    project_id: str,
    agent_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Remove an agent from a project"""
    try:
        association = db.query(ProjectAgent).filter(
            ProjectAgent.project_id == project_id,
            ProjectAgent.agent_id == agent_id
        ).first()

        if not association:
            raise HTTPException(status_code=404, detail="Association not found")

        db.delete(association)
        db.commit()

        logger.info(
            "agent_removed_from_project",
            project_id=project_id,
            agent_id=agent_id,
            org_id=organization["id"],
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error("remove_agent_from_project_failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove agent: {str(e)}"
        )


# Team associations (similar to agents)
@router.post("/{project_id}/teams", status_code=status.HTTP_201_CREATED)
async def add_team_to_project(
    project_id: str,
    team_data: ProjectTeamAdd,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Add a team to a project"""
    try:
        # Verify project exists
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.organization_id == organization["id"]
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify team exists and belongs to org
        team = db.query(Team).filter(
            Team.id == team_data.team_id,
            Team.organization_id == organization["id"]
        ).first()

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Add association
        now = datetime.utcnow()
        association = ProjectTeam(
            project_id=project_id,
            team_id=team_data.team_id,
            role=team_data.role,
            added_at=now,
            added_by=organization.get("user_id"),
        )

        db.add(association)
        db.commit()
        db.refresh(association)

        logger.info(
            "team_added_to_project",
            project_id=project_id,
            team_id=team_data.team_id,
            org_id=organization["id"],
        )

        return {
            "id": str(association.id),
            "project_id": str(association.project_id),
            "team_id": str(association.team_id),
            "role": association.role,
            "added_at": association.added_at.isoformat() if association.added_at else None,
            "added_by": association.added_by,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("add_team_to_project_failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add team: {str(e)}"
        )


@router.get("/{project_id}/teams")
async def list_project_teams(
    project_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """List all teams in a project"""
    try:
        # Get project teams with team details
        project_teams = db.query(ProjectTeam).options(
            joinedload(ProjectTeam.team)
        ).filter(
            ProjectTeam.project_id == project_id
        ).all()

        # Build response with nested team data
        result = []
        for pt in project_teams:
            team_data = None
            if pt.team:
                team_data = {
                    "id": str(pt.team.id),
                    "name": pt.team.name,
                    "description": pt.team.description,
                    "organization_id": str(pt.team.organization_id),
                    "created_at": pt.team.created_at.isoformat() if pt.team.created_at else None,
                    "updated_at": pt.team.updated_at.isoformat() if pt.team.updated_at else None,
                }

            result.append({
                "id": str(pt.id),
                "project_id": str(pt.project_id),
                "team_id": str(pt.team_id),
                "role": pt.role,
                "added_at": pt.added_at.isoformat() if pt.added_at else None,
                "added_by": pt.added_by,
                "teams": team_data,
            })

        logger.info(
            "project_teams_listed",
            project_id=project_id,
            count=len(result),
            org_id=organization["id"],
        )

        return result

    except Exception as e:
        logger.error("list_project_teams_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list teams: {str(e)}"
        )


@router.delete("/{project_id}/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_from_project(
    project_id: str,
    team_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Remove a team from a project"""
    try:
        association = db.query(ProjectTeam).filter(
            ProjectTeam.project_id == project_id,
            ProjectTeam.team_id == team_id
        ).first()

        if not association:
            raise HTTPException(status_code=404, detail="Association not found")

        db.delete(association)
        db.commit()

        logger.info(
            "team_removed_from_project",
            project_id=project_id,
            team_id=team_id,
            org_id=organization["id"],
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error("remove_team_from_project_failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove team: {str(e)}"
        )
