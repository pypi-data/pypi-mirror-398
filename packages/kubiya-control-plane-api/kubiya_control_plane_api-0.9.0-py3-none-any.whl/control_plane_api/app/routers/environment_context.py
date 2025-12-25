"""
Environment Context router - Manage contextual settings for environments.

Allows attaching knowledge and resources to environments for agent execution context.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel, Field
import structlog

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from control_plane_api.app.models.environment import Environment
from control_plane_api.app.models.context import EnvironmentContext

logger = structlog.get_logger()

router = APIRouter()


# Pydantic schemas
class UpdateEnvironmentContextRequest(BaseModel):
    knowledge_uuids: List[str] = Field(default_factory=list, description="Array of knowledge UUIDs")
    resource_ids: List[str] = Field(default_factory=list, description="Array of resource IDs from Meilisearch")


class EnvironmentContextResponse(BaseModel):
    id: str
    environment_id: str
    organization_id: str
    knowledge_uuids: List[str]
    resource_ids: List[str]
    created_at: str
    updated_at: str


@router.get("/environments/{environment_id}/context", response_model=EnvironmentContextResponse)
async def get_environment_context(
    environment_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Get context configuration for an environment"""
    try:
        org_id = organization["id"]

        # Verify environment exists
        env = db.query(Environment).filter(
            Environment.id == environment_id,
            Environment.organization_id == org_id
        ).first()

        if not env:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Environment not found"
            )

        # Get or create context
        context = db.query(EnvironmentContext).filter(
            EnvironmentContext.environment_id == environment_id,
            EnvironmentContext.organization_id == org_id
        ).first()

        if context:
            return EnvironmentContextResponse(
                id=str(context.id),
                environment_id=str(context.environment_id),
                organization_id=str(context.organization_id),
                knowledge_uuids=context.knowledge_uuids or [],
                resource_ids=context.resource_ids or [],
                created_at=context.created_at.isoformat(),
                updated_at=context.updated_at.isoformat(),
            )

        # Create default context if it doesn't exist
        new_context = EnvironmentContext(
            environment_id=environment_id,
            organization_id=org_id,
            knowledge_uuids=[],
            resource_ids=[],
        )

        db.add(new_context)
        db.commit()
        db.refresh(new_context)

        logger.info(
            "environment_context_created",
            environment_id=environment_id,
            org_id=org_id,
        )

        return EnvironmentContextResponse(
            id=str(new_context.id),
            environment_id=str(new_context.environment_id),
            organization_id=str(new_context.organization_id),
            knowledge_uuids=new_context.knowledge_uuids or [],
            resource_ids=new_context.resource_ids or [],
            created_at=new_context.created_at.isoformat(),
            updated_at=new_context.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_environment_context_failed", error=str(e), environment_id=environment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get environment context: {str(e)}"
        )


@router.put("/environments/{environment_id}/context", response_model=EnvironmentContextResponse)
async def update_environment_context(
    environment_id: str,
    context_data: UpdateEnvironmentContextRequest,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Update context configuration for an environment"""
    try:
        org_id = organization["id"]

        # Verify environment exists
        env = db.query(Environment).filter(
            Environment.id == environment_id,
            Environment.organization_id == org_id
        ).first()

        if not env:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Environment not found"
            )

        # Check if context exists
        existing_context = db.query(EnvironmentContext).filter(
            EnvironmentContext.environment_id == environment_id,
            EnvironmentContext.organization_id == org_id
        ).first()

        if existing_context:
            # Update existing context
            existing_context.knowledge_uuids = context_data.knowledge_uuids
            existing_context.resource_ids = context_data.resource_ids
            existing_context.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(existing_context)

            logger.info(
                "environment_context_updated",
                environment_id=environment_id,
                knowledge_count=len(context_data.knowledge_uuids),
                resource_count=len(context_data.resource_ids),
                org_id=org_id,
            )

            return EnvironmentContextResponse(
                id=str(existing_context.id),
                environment_id=str(existing_context.environment_id),
                organization_id=str(existing_context.organization_id),
                knowledge_uuids=existing_context.knowledge_uuids or [],
                resource_ids=existing_context.resource_ids or [],
                created_at=existing_context.created_at.isoformat(),
                updated_at=existing_context.updated_at.isoformat(),
            )
        else:
            # Create new context
            new_context = EnvironmentContext(
                environment_id=environment_id,
                organization_id=org_id,
                knowledge_uuids=context_data.knowledge_uuids,
                resource_ids=context_data.resource_ids,
            )

            db.add(new_context)
            db.commit()
            db.refresh(new_context)

            logger.info(
                "environment_context_created",
                environment_id=environment_id,
                knowledge_count=len(context_data.knowledge_uuids),
                resource_count=len(context_data.resource_ids),
                org_id=org_id,
            )

            return EnvironmentContextResponse(
                id=str(new_context.id),
                environment_id=str(new_context.environment_id),
                organization_id=str(new_context.organization_id),
                knowledge_uuids=new_context.knowledge_uuids or [],
                resource_ids=new_context.resource_ids or [],
                created_at=new_context.created_at.isoformat(),
                updated_at=new_context.updated_at.isoformat(),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_environment_context_failed", error=str(e), environment_id=environment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update environment context: {str(e)}"
        )


@router.delete("/environments/{environment_id}/context", status_code=status.HTTP_204_NO_CONTENT)
async def clear_environment_context(
    environment_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """Clear all context for an environment (reset to empty arrays)"""
    try:
        org_id = organization["id"]

        # Update context to empty arrays
        context = db.query(EnvironmentContext).filter(
            EnvironmentContext.environment_id == environment_id,
            EnvironmentContext.organization_id == org_id
        ).first()

        if context:
            context.knowledge_uuids = []
            context.resource_ids = []
            context.updated_at = datetime.utcnow()

            db.commit()

            logger.info(
                "environment_context_cleared",
                environment_id=environment_id,
                org_id=org_id,
            )

        return None

    except Exception as e:
        logger.error("clear_environment_context_failed", error=str(e), environment_id=environment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear environment context: {str(e)}"
        )
