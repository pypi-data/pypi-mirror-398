"""
Unified Context Management System for Agent Control Plane.

Manages contextual settings (knowledge, resources, policies) across all entity types:
- Environments
- Teams
- Projects
- Agents

Provides layered context resolution: Environment → Team → Project → Agent
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import structlog
import uuid

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from sqlalchemy.orm import Session
from control_plane_api.app.models.context import (
    AgentContext, EnvironmentContext, ProjectContext, TeamContext
)
from control_plane_api.app.models.agent import Agent
from control_plane_api.app.models.environment import Environment
from control_plane_api.app.models.project import Project
from control_plane_api.app.models.team import Team
from control_plane_api.app.models.associations import AgentEnvironment, TeamEnvironment

logger = structlog.get_logger()

router = APIRouter()

# Entity types that support context
EntityType = Literal["environment", "team", "project", "agent"]

# Pydantic schemas
class ContextData(BaseModel):
    """Generic context data structure"""
    knowledge_uuids: List[str] = Field(default_factory=list, description="Knowledge base UUIDs")
    resource_ids: List[str] = Field(default_factory=list, description="Resource IDs from Meilisearch")
    policy_ids: List[str] = Field(default_factory=list, description="OPA policy IDs")


class UpdateContextRequest(BaseModel):
    """Request to update context for any entity"""
    knowledge_uuids: List[str] = Field(default_factory=list)
    resource_ids: List[str] = Field(default_factory=list)
    policy_ids: List[str] = Field(default_factory=list)


class ContextResponse(BaseModel):
    """Generic context response"""
    id: str
    entity_type: str
    entity_id: str
    organization_id: str
    knowledge_uuids: List[str]
    resource_ids: List[str]
    policy_ids: List[str]
    created_at: str
    updated_at: str


class ResolvedContextResponse(BaseModel):
    """Resolved context with inheritance from all layers"""
    entity_id: str
    entity_type: str
    environment_id: Optional[str] = None
    team_id: Optional[str] = None
    project_id: Optional[str] = None

    # Aggregated context from all layers
    knowledge_uuids: List[str] = Field(description="Merged knowledge from all layers")
    resource_ids: List[str] = Field(description="Merged resources from all layers")
    policy_ids: List[str] = Field(description="Merged policies from all layers")

    # Layer breakdown for debugging
    layers: Dict[str, ContextData] = Field(description="Context breakdown by layer")


# Model mapping for context models
CONTEXT_MODEL_MAP = {
    "environment": EnvironmentContext,
    "team": TeamContext,
    "project": ProjectContext,
    "agent": AgentContext,
}

# Entity model mapping (for validation)
ENTITY_MODEL_MAP = {
    "environment": Environment,
    "team": Team,
    "project": Project,
    "agent": Agent,
}


async def _verify_entity_exists(
    db: Session, entity_type: EntityType, entity_id: str, org_id: str
) -> bool:
    """Verify that an entity exists for the organization"""
    entity_model = ENTITY_MODEL_MAP.get(entity_type)
    if not entity_model:
        return False

    entity = db.query(entity_model).filter(
        entity_model.id == uuid.UUID(entity_id),
        entity_model.organization_id == org_id
    ).first()

    return entity is not None


async def _get_or_create_context(
    db: Session, entity_type: EntityType, entity_id: str, org_id: str
) -> Dict[str, Any]:
    """Get existing context or create a default one"""
    context_model = CONTEXT_MODEL_MAP.get(entity_type)
    if not context_model:
        raise ValueError(f"Invalid entity type: {entity_type}")

    # Build filter dynamically based on entity type
    entity_id_field = getattr(context_model, f"{entity_type}_id")

    # Try to get existing context
    context = db.query(context_model).filter(
        entity_id_field == uuid.UUID(entity_id),
        context_model.organization_id == uuid.UUID(org_id)
    ).first()

    if context:
        # Convert to dict
        return {
            "id": str(context.id),
            f"{entity_type}_id": str(getattr(context, f"{entity_type}_id")),
            "entity_type": context.entity_type,
            "organization_id": str(context.organization_id),
            "knowledge_uuids": context.knowledge_uuids or [],
            "resource_ids": context.resource_ids or [],
            "policy_ids": context.policy_ids or [],
            "created_at": context.created_at.isoformat() if context.created_at else datetime.utcnow().isoformat(),
            "updated_at": context.updated_at.isoformat() if context.updated_at else datetime.utcnow().isoformat(),
        }

    # Create default context
    context_data = {
        f"{entity_type}_id": uuid.UUID(entity_id),
        "entity_type": entity_type,
        "organization_id": uuid.UUID(org_id),
        "knowledge_uuids": [],
        "resource_ids": [],
        "policy_ids": [],
    }

    new_context = context_model(**context_data)
    db.add(new_context)
    db.commit()
    db.refresh(new_context)

    logger.info(
        "context_created",
        entity_type=entity_type,
        entity_id=entity_id,
        org_id=org_id,
    )

    return {
        "id": str(new_context.id),
        f"{entity_type}_id": str(getattr(new_context, f"{entity_type}_id")),
        "entity_type": new_context.entity_type,
        "organization_id": str(new_context.organization_id),
        "knowledge_uuids": new_context.knowledge_uuids or [],
        "resource_ids": new_context.resource_ids or [],
        "policy_ids": new_context.policy_ids or [],
        "created_at": new_context.created_at.isoformat() if new_context.created_at else datetime.utcnow().isoformat(),
        "updated_at": new_context.updated_at.isoformat() if new_context.updated_at else datetime.utcnow().isoformat(),
    }


@router.get("/context/{entity_type}/{entity_id}", response_model=ContextResponse)
async def get_context(
    entity_type: EntityType,
    entity_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get context configuration for any entity type"""
    try:
        org_id = organization["id"]

        # Verify entity exists
        if not await _verify_entity_exists(db, entity_type, entity_id, org_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_type.capitalize()} not found"
            )

        # Get or create context
        context_data = await _get_or_create_context(db, entity_type, entity_id, org_id)

        return ContextResponse(**context_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_context_failed", error=str(e), entity_type=entity_type, entity_id=entity_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get {entity_type} context: {str(e)}"
        )


@router.put("/context/{entity_type}/{entity_id}", response_model=ContextResponse)
async def update_context(
    entity_type: EntityType,
    entity_id: str,
    context_data: UpdateContextRequest,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Update context configuration for any entity type"""
    try:
        org_id = organization["id"]

        # Verify entity exists
        if not await _verify_entity_exists(db, entity_type, entity_id, org_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_type.capitalize()} not found"
            )

        context_model = CONTEXT_MODEL_MAP[entity_type]
        entity_id_field = getattr(context_model, f"{entity_type}_id")

        # Check if context exists
        existing = db.query(context_model).filter(
            entity_id_field == uuid.UUID(entity_id),
            context_model.organization_id == uuid.UUID(org_id)
        ).first()

        if existing:
            # Update existing
            existing.knowledge_uuids = context_data.knowledge_uuids
            existing.resource_ids = context_data.resource_ids
            existing.policy_ids = context_data.policy_ids
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            context = existing
        else:
            # Create new
            new_context_data = {
                f"{entity_type}_id": uuid.UUID(entity_id),
                "entity_type": entity_type,
                "organization_id": uuid.UUID(org_id),
                "knowledge_uuids": context_data.knowledge_uuids,
                "resource_ids": context_data.resource_ids,
                "policy_ids": context_data.policy_ids,
            }
            context = context_model(**new_context_data)
            db.add(context)
            db.commit()
            db.refresh(context)

        logger.info(
            "context_updated",
            entity_type=entity_type,
            entity_id=entity_id,
            knowledge_count=len(context_data.knowledge_uuids),
            resource_count=len(context_data.resource_ids),
            policy_count=len(context_data.policy_ids),
            org_id=org_id,
        )

        return ContextResponse(
            id=str(context.id),
            entity_type=context.entity_type,
            entity_id=str(getattr(context, f"{entity_type}_id")),
            organization_id=str(context.organization_id),
            knowledge_uuids=context.knowledge_uuids or [],
            resource_ids=context.resource_ids or [],
            policy_ids=context.policy_ids or [],
            created_at=context.created_at.isoformat() if context.created_at else datetime.utcnow().isoformat(),
            updated_at=context.updated_at.isoformat() if context.updated_at else datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_context_failed", error=str(e), entity_type=entity_type, entity_id=entity_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update {entity_type} context: {str(e)}"
        )


@router.delete("/context/{entity_type}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_context(
    entity_type: EntityType,
    entity_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Clear all context for an entity"""
    try:
        org_id = organization["id"]

        context_model = CONTEXT_MODEL_MAP[entity_type]
        entity_id_field = getattr(context_model, f"{entity_type}_id")

        # Find and update the context
        context = db.query(context_model).filter(
            entity_id_field == uuid.UUID(entity_id),
            context_model.organization_id == uuid.UUID(org_id)
        ).first()

        if context:
            context.knowledge_uuids = []
            context.resource_ids = []
            context.policy_ids = []
            context.updated_at = datetime.utcnow()
            db.commit()

        logger.info("context_cleared", entity_type=entity_type, entity_id=entity_id, org_id=org_id)
        return None

    except Exception as e:
        logger.error("clear_context_failed", error=str(e), entity_type=entity_type, entity_id=entity_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear {entity_type} context: {str(e)}"
        )


@router.get("/context/resolve/{entity_type}/{entity_id}", response_model=ResolvedContextResponse)
async def resolve_context(
    entity_type: EntityType,
    entity_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Resolve context with inheritance from all layers.

    Resolution order (each layer adds to the previous):
    1. ALL Environments (many-to-many for agents/teams)
    2. Team (if member of a team)
    3. ALL Team Environments (if agent is part of team)
    4. Project (if assigned to a project)
    5. Agent/Entity itself

    Returns merged context with full layer breakdown.
    """
    try:
        org_id = organization["id"]

        # Verify entity exists
        if not await _verify_entity_exists(db, entity_type, entity_id, org_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_type.capitalize()} not found"
            )

        layers: Dict[str, ContextData] = {}
        team_id: Optional[str] = None
        project_id: Optional[str] = None
        environment_ids: List[str] = []

        # Collect context from all layers
        all_knowledge: List[str] = []
        all_resources: List[str] = []
        all_policies: List[str] = []

        # 1. Get entity relationships (team, project)
        entity_model = ENTITY_MODEL_MAP[entity_type]
        entity = db.query(entity_model).filter(
            entity_model.id == uuid.UUID(entity_id),
            entity_model.organization_id == org_id
        ).first()

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_type.capitalize()} not found"
            )

        # Extract relationships
        team_id = str(entity.team_id) if hasattr(entity, 'team_id') and entity.team_id else None
        project_id = str(entity.project_id) if hasattr(entity, 'project_id') and entity.project_id else None

        # 2. Layer 1: Get ALL agent/team environments (many-to-many)
        if entity_type == "agent":
            # Get all agent environments
            agent_envs = db.query(AgentEnvironment).filter(
                AgentEnvironment.agent_id == uuid.UUID(entity_id)
            ).all()
            environment_ids = [str(env.environment_id) for env in agent_envs]

        elif entity_type == "team":
            # Get all team environments
            team_envs = db.query(TeamEnvironment).filter(
                TeamEnvironment.team_id == uuid.UUID(entity_id)
            ).all()
            environment_ids = [str(env.environment_id) for env in team_envs]

        # Merge context from ALL environments
        for idx, env_id in enumerate(environment_ids):
            try:
                env_context = await _get_or_create_context(db, "environment", env_id, org_id)
                layer_key = f"environment_{idx+1}" if len(environment_ids) > 1 else "environment"
                layers[layer_key] = ContextData(
                    knowledge_uuids=env_context.get("knowledge_uuids", []),
                    resource_ids=env_context.get("resource_ids", []),
                    policy_ids=env_context.get("policy_ids", []),
                )
                all_knowledge.extend(layers[layer_key].knowledge_uuids)
                all_resources.extend(layers[layer_key].resource_ids)
                all_policies.extend(layers[layer_key].policy_ids)
            except Exception as e:
                logger.warning("failed_to_get_environment_context", error=str(e), environment_id=env_id)

        # 3. Layer 2: Team context
        if team_id:
            try:
                team_context = await _get_or_create_context(db, "team", team_id, org_id)
                layers["team"] = ContextData(
                    knowledge_uuids=team_context.get("knowledge_uuids", []),
                    resource_ids=team_context.get("resource_ids", []),
                    policy_ids=team_context.get("policy_ids", []),
                )
                all_knowledge.extend(layers["team"].knowledge_uuids)
                all_resources.extend(layers["team"].resource_ids)
                all_policies.extend(layers["team"].policy_ids)
            except Exception as e:
                logger.warning("failed_to_get_team_context", error=str(e), team_id=team_id)

            # 3b. Get ALL team environments (if agent has team)
            if entity_type == "agent":
                team_envs = db.query(TeamEnvironment).filter(
                    TeamEnvironment.team_id == uuid.UUID(team_id)
                ).all()
                team_environment_ids = [str(env.environment_id) for env in team_envs]

                for idx, env_id in enumerate(team_environment_ids):
                    # Skip if already processed in agent environments
                    if env_id in environment_ids:
                        continue
                    try:
                        env_context = await _get_or_create_context(db, "environment", env_id, org_id)
                        layer_key = f"team_environment_{idx+1}"
                        layers[layer_key] = ContextData(
                            knowledge_uuids=env_context.get("knowledge_uuids", []),
                            resource_ids=env_context.get("resource_ids", []),
                            policy_ids=env_context.get("policy_ids", []),
                        )
                        all_knowledge.extend(layers[layer_key].knowledge_uuids)
                        all_resources.extend(layers[layer_key].resource_ids)
                        all_policies.extend(layers[layer_key].policy_ids)
                    except Exception as e:
                        logger.warning("failed_to_get_team_environment_context", error=str(e), environment_id=env_id)

        # 4. Layer 3: Project context
        if project_id:
            try:
                project_context = await _get_or_create_context(db, "project", project_id, org_id)
                layers["project"] = ContextData(
                    knowledge_uuids=project_context.get("knowledge_uuids", []),
                    resource_ids=project_context.get("resource_ids", []),
                    policy_ids=project_context.get("policy_ids", []),
                )
                all_knowledge.extend(layers["project"].knowledge_uuids)
                all_resources.extend(layers["project"].resource_ids)
                all_policies.extend(layers["project"].policy_ids)
            except Exception as e:
                logger.warning("failed_to_get_project_context", error=str(e), project_id=project_id)

        # 5. Layer 4: Entity's own context
        try:
            entity_context = await _get_or_create_context(db, entity_type, entity_id, org_id)
            layers[entity_type] = ContextData(
                knowledge_uuids=entity_context.get("knowledge_uuids", []),
                resource_ids=entity_context.get("resource_ids", []),
                policy_ids=entity_context.get("policy_ids", []),
            )
            all_knowledge.extend(layers[entity_type].knowledge_uuids)
            all_resources.extend(layers[entity_type].resource_ids)
            all_policies.extend(layers[entity_type].policy_ids)
        except Exception as e:
            logger.warning("failed_to_get_entity_context", error=str(e), entity_type=entity_type, entity_id=entity_id)

        # Deduplicate while preserving order
        unique_knowledge = list(dict.fromkeys(all_knowledge))
        unique_resources = list(dict.fromkeys(all_resources))
        unique_policies = list(dict.fromkeys(all_policies))

        logger.info(
            "context_resolved",
            entity_type=entity_type,
            entity_id=entity_id,
            layers_count=len(layers),
            environment_count=len(environment_ids),
            total_knowledge=len(unique_knowledge),
            total_resources=len(unique_resources),
            total_policies=len(unique_policies),
            org_id=org_id,
        )

        return ResolvedContextResponse(
            entity_id=entity_id,
            entity_type=entity_type,
            environment_id=environment_ids[0] if environment_ids else None,
            team_id=team_id,
            project_id=project_id,
            knowledge_uuids=unique_knowledge,
            resource_ids=unique_resources,
            policy_ids=unique_policies,
            layers=layers,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("resolve_context_failed", error=str(e), entity_type=entity_type, entity_id=entity_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve {entity_type} context: {str(e)}"
        )


# Convenience endpoints for workers
@router.get("/agents/{agent_id}/context/resolved", response_model=ResolvedContextResponse)
async def resolve_agent_context(
    agent_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Convenience endpoint to resolve full context for an agent.

    Fetches and merges context from:
    1. ALL agent environments (many-to-many)
    2. Team (if agent belongs to a team)
    3. ALL team environments
    4. Project (if assigned)
    5. Agent's own context

    Workers should call this endpoint to get all knowledge, resources, and policies.
    """
    return await resolve_context("agent", agent_id, request, organization, db)


@router.get("/teams/{team_id}/context/resolved", response_model=ResolvedContextResponse)
async def resolve_team_context(
    team_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Convenience endpoint to resolve full context for a team.

    Fetches and merges context from:
    1. ALL team environments (many-to-many)
    2. Project (if assigned)
    3. Team's own context

    Workers should call this endpoint to get all knowledge, resources, and policies.
    """
    return await resolve_context("team", team_id, request, organization, db)
