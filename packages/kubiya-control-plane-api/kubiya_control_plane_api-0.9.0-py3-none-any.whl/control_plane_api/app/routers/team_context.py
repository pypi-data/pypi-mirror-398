"""
Team Context router - Manage contextual settings for teams.

Allows attaching knowledge and resources to teams for agent execution context.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.inspection import inspect
import structlog
import uuid

from sqlalchemy.orm import Session

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from control_plane_api.app.models.context import TeamContext
from control_plane_api.app.models.team import Team

logger = structlog.get_logger()

router = APIRouter()


# Pydantic schemas
class UpdateTeamContextRequest(BaseModel):
    knowledge_uuids: List[str] = Field(default_factory=list, description="Array of knowledge UUIDs")
    resource_ids: List[str] = Field(default_factory=list, description="Array of resource IDs from Meilisearch")


class TeamContextResponse(BaseModel):
    id: str
    team_id: str
    organization_id: str
    knowledge_uuids: List[str]
    resource_ids: List[str]
    created_at: str
    updated_at: str


@router.get("/teams/{team_id}/context", response_model=TeamContextResponse)
async def get_team_context(
    team_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get context configuration for a team"""
    try:
        org_id = organization["id"]

        # Verify team exists
        team = db.query(Team).filter(
            Team.id == team_id,
            Team.organization_id == org_id
        ).first()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        # Get or create context
        context = db.query(TeamContext).filter(
            TeamContext.team_id == team_id,
            TeamContext.organization_id == org_id
        ).first()

        if context:
            # Convert SQLAlchemy object to dict
            context_dict = {c.key: getattr(context, c.key) for c in inspect(context).mapper.column_attrs}
            # Convert UUIDs to strings
            context_dict["id"] = str(context_dict["id"])
            context_dict["team_id"] = str(context_dict["team_id"])
            context_dict["organization_id"] = str(context_dict["organization_id"])
            # Convert datetime to ISO format string
            context_dict["created_at"] = context_dict["created_at"].isoformat() if context_dict["created_at"] else None
            context_dict["updated_at"] = context_dict["updated_at"].isoformat() if context_dict["updated_at"] else None
            # Ensure arrays are not None
            context_dict["knowledge_uuids"] = context_dict.get("knowledge_uuids") or []
            context_dict["resource_ids"] = context_dict.get("resource_ids") or []
            return TeamContextResponse(**context_dict)

        # Create default context if it doesn't exist
        new_context = TeamContext(
            team_id=team_id,
            organization_id=org_id,
            knowledge_uuids=[],
            resource_ids=[],
        )

        db.add(new_context)
        db.commit()
        db.refresh(new_context)

        logger.info(
            "team_context_created",
            team_id=team_id,
            org_id=org_id,
        )

        # Convert SQLAlchemy object to dict
        context_dict = {c.key: getattr(new_context, c.key) for c in inspect(new_context).mapper.column_attrs}
        # Convert UUIDs to strings
        context_dict["id"] = str(context_dict["id"])
        context_dict["team_id"] = str(context_dict["team_id"])
        context_dict["organization_id"] = str(context_dict["organization_id"])
        # Convert datetime to ISO format string
        context_dict["created_at"] = context_dict["created_at"].isoformat() if context_dict["created_at"] else None
        context_dict["updated_at"] = context_dict["updated_at"].isoformat() if context_dict["updated_at"] else None
        # Ensure arrays are not None
        context_dict["knowledge_uuids"] = context_dict.get("knowledge_uuids") or []
        context_dict["resource_ids"] = context_dict.get("resource_ids") or []

        return TeamContextResponse(**context_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_team_context_failed", error=str(e), team_id=team_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team context: {str(e)}"
        )


@router.put("/teams/{team_id}/context", response_model=TeamContextResponse)
async def update_team_context(
    team_id: str,
    context_data: UpdateTeamContextRequest,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Update context configuration for a team"""
    try:
        org_id = organization["id"]

        # Verify team exists
        team = db.query(Team).filter(
            Team.id == team_id,
            Team.organization_id == org_id
        ).first()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        # Check if context exists
        existing_context = db.query(TeamContext).filter(
            TeamContext.team_id == team_id,
            TeamContext.organization_id == org_id
        ).first()

        if existing_context:
            # Update existing context
            existing_context.knowledge_uuids = context_data.knowledge_uuids
            existing_context.resource_ids = context_data.resource_ids
            existing_context.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(existing_context)

            logger.info(
                "team_context_updated",
                team_id=team_id,
                knowledge_count=len(context_data.knowledge_uuids),
                resource_count=len(context_data.resource_ids),
                org_id=org_id,
            )

            # Convert SQLAlchemy object to dict
            context_dict = {c.key: getattr(existing_context, c.key) for c in inspect(existing_context).mapper.column_attrs}
            # Convert UUIDs to strings
            context_dict["id"] = str(context_dict["id"])
            context_dict["team_id"] = str(context_dict["team_id"])
            context_dict["organization_id"] = str(context_dict["organization_id"])
            # Convert datetime to ISO format string
            context_dict["created_at"] = context_dict["created_at"].isoformat() if context_dict["created_at"] else None
            context_dict["updated_at"] = context_dict["updated_at"].isoformat() if context_dict["updated_at"] else None
            # Ensure arrays are not None
            context_dict["knowledge_uuids"] = context_dict.get("knowledge_uuids") or []
            context_dict["resource_ids"] = context_dict.get("resource_ids") or []

            return TeamContextResponse(**context_dict)
        else:
            # Create new context
            new_context = TeamContext(
                team_id=team_id,
                organization_id=org_id,
                knowledge_uuids=context_data.knowledge_uuids,
                resource_ids=context_data.resource_ids,
            )

            db.add(new_context)
            db.commit()
            db.refresh(new_context)

            logger.info(
                "team_context_created",
                team_id=team_id,
                knowledge_count=len(context_data.knowledge_uuids),
                resource_count=len(context_data.resource_ids),
                org_id=org_id,
            )

            # Convert SQLAlchemy object to dict
            context_dict = {c.key: getattr(new_context, c.key) for c in inspect(new_context).mapper.column_attrs}
            # Convert UUIDs to strings
            context_dict["id"] = str(context_dict["id"])
            context_dict["team_id"] = str(context_dict["team_id"])
            context_dict["organization_id"] = str(context_dict["organization_id"])
            # Convert datetime to ISO format string
            context_dict["created_at"] = context_dict["created_at"].isoformat() if context_dict["created_at"] else None
            context_dict["updated_at"] = context_dict["updated_at"].isoformat() if context_dict["updated_at"] else None
            # Ensure arrays are not None
            context_dict["knowledge_uuids"] = context_dict.get("knowledge_uuids") or []
            context_dict["resource_ids"] = context_dict.get("resource_ids") or []

            return TeamContextResponse(**context_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_team_context_failed", error=str(e), team_id=team_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update team context: {str(e)}"
        )


@router.delete("/teams/{team_id}/context", status_code=status.HTTP_204_NO_CONTENT)
async def clear_team_context(
    team_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Clear all context for a team (reset to empty arrays)"""
    try:
        org_id = organization["id"]

        # Update context to empty arrays
        context = db.query(TeamContext).filter(
            TeamContext.team_id == team_id,
            TeamContext.organization_id == org_id
        ).first()

        if context:
            context.knowledge_uuids = []
            context.resource_ids = []
            context.updated_at = datetime.utcnow()

            db.commit()

            logger.info(
                "team_context_cleared",
                team_id=team_id,
                org_id=org_id,
            )

        return None

    except Exception as e:
        logger.error("clear_team_context_failed", error=str(e), team_id=team_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear team context: {str(e)}"
        )
