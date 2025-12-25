from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from control_plane_api.app.database import get_db
from control_plane_api.app.models.workflow import Workflow, WorkflowStatus
from pydantic import BaseModel, Field

router = APIRouter()


# Pydantic schemas
class WorkflowCreate(BaseModel):
    name: str = Field(..., description="Workflow name")
    description: str | None = Field(None, description="Workflow description")
    steps: list = Field(default_factory=list, description="Workflow steps")
    configuration: dict = Field(default_factory=dict, description="Workflow configuration")
    team_id: str | None = Field(None, description="Team ID")


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: WorkflowStatus | None = None
    steps: list | None = None
    current_step: str | None = None
    configuration: dict | None = None
    state: dict | None = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str | None
    status: WorkflowStatus
    steps: list
    current_step: str | None
    configuration: dict
    team_id: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    state: dict
    error_message: str | None

    class Config:
        from_attributes = True


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(workflow_data: WorkflowCreate, db: Session = Depends(get_db)):
    """Create a new workflow"""
    workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        steps=workflow_data.steps,
        configuration=workflow_data.configuration,
        team_id=workflow_data.team_id,
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


@router.get("", response_model=List[WorkflowResponse])
def list_workflows(
    skip: int = 0,
    limit: int = 100,
    status_filter: WorkflowStatus | None = None,
    team_id: str | None = None,
    db: Session = Depends(get_db),
):
    """List all workflows"""
    query = db.query(Workflow)
    if status_filter:
        query = query.filter(Workflow.status == status_filter)
    if team_id:
        query = query.filter(Workflow.team_id == team_id)
    workflows = query.offset(skip).limit(limit).all()
    return workflows


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Get a specific workflow by ID"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(workflow_id: str, workflow_data: WorkflowUpdate, db: Session = Depends(get_db)):
    """Update a workflow"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    update_data = workflow_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)

    workflow.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(workflow)
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Delete a workflow"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    db.delete(workflow)
    db.commit()
    return None


@router.post("/{workflow_id}/start", response_model=WorkflowResponse)
def start_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Start a workflow"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.status == WorkflowStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Workflow is already running")

    workflow.status = WorkflowStatus.RUNNING
    workflow.started_at = datetime.utcnow()
    workflow.error_message = None
    if workflow.steps and len(workflow.steps) > 0:
        workflow.current_step = workflow.steps[0].get("id", workflow.steps[0].get("name"))
    db.commit()
    db.refresh(workflow)
    return workflow


@router.post("/{workflow_id}/pause", response_model=WorkflowResponse)
def pause_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Pause a workflow"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.status != WorkflowStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Can only pause running workflows")

    workflow.status = WorkflowStatus.PAUSED
    db.commit()
    db.refresh(workflow)
    return workflow


@router.post("/{workflow_id}/resume", response_model=WorkflowResponse)
def resume_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Resume a paused workflow"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.status != WorkflowStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Can only resume paused workflows")

    workflow.status = WorkflowStatus.RUNNING
    db.commit()
    db.refresh(workflow)
    return workflow


@router.post("/{workflow_id}/cancel", response_model=WorkflowResponse)
def cancel_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Cancel a workflow"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Workflow is already completed or cancelled")

    workflow.status = WorkflowStatus.CANCELLED
    workflow.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(workflow)
    return workflow


@router.post("/{workflow_id}/complete", response_model=WorkflowResponse)
def complete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Mark a workflow as completed"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.status = WorkflowStatus.COMPLETED
    workflow.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(workflow)
    return workflow
