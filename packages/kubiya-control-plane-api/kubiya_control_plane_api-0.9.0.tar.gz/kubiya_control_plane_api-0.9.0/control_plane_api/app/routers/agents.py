from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from control_plane_api.app.database import get_db
from control_plane_api.app.models.agent import Agent, AgentStatus
from control_plane_api.app.models.execution import Execution, ExecutionStatus, ExecutionType
from control_plane_api.app.services.litellm_service import litellm_service
from pydantic import BaseModel, Field

router = APIRouter()


def agent_to_response(agent: Agent) -> dict:
    """Convert Agent model to response dict, mapping model_config to llm_config"""
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "status": agent.status,
        "capabilities": agent.capabilities,
        "configuration": agent.configuration,
        "model_id": agent.model_id,
        "llm_config": agent.model_config,
        "team_id": agent.team_id,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
        "last_active_at": agent.last_active_at,
        "state": agent.state,
        "error_message": agent.error_message,
    }


# Pydantic schemas
class AgentCreate(BaseModel):
    name: str = Field(..., description="Agent name")
    description: str | None = Field(None, description="Agent description")
    capabilities: list = Field(default_factory=list, description="Agent capabilities")
    configuration: dict = Field(default_factory=dict, description="Agent configuration")
    model_id: str | None = Field(None, description="LiteLLM model identifier")
    llm_config: dict = Field(default_factory=dict, description="Model-specific configuration")
    team_id: str | None = Field(None, description="Team ID to assign this agent to")


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: AgentStatus | None = None
    capabilities: list | None = None
    configuration: dict | None = None
    state: dict | None = None
    model_id: str | None = None
    llm_config: dict | None = None
    team_id: str | None = None


class AgentResponse(BaseModel):
    id: str
    name: str
    description: str | None
    status: AgentStatus
    capabilities: list
    configuration: dict
    model_id: str | None
    llm_config: dict
    team_id: str | None
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime | None
    state: dict
    error_message: str | None

    class Config:
        from_attributes = True


class AgentExecutionRequest(BaseModel):
    prompt: str = Field(..., description="The prompt to execute")
    system_prompt: str | None = Field(None, description="Optional system prompt")
    stream: bool = Field(False, description="Whether to stream the response")
    config: dict | None = Field(None, description="Optional configuration including user metadata")


class AgentExecutionResponse(BaseModel):
    execution_id: str
    success: bool
    response: str | None = None
    error: str | None = None
    model: str
    usage: dict | None = None
    finish_reason: str | None = None


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(agent_data: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent"""
    agent = Agent(
        name=agent_data.name,
        description=agent_data.description,
        capabilities=agent_data.capabilities,
        configuration=agent_data.configuration,
        model_id=agent_data.model_id,
        model_config=agent_data.llm_config,
        team_id=agent_data.team_id,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent_to_response(agent)


@router.get("", response_model=List[AgentResponse])
def list_agents(
    skip: int = 0,
    limit: int = 100,
    status_filter: AgentStatus | None = None,
    db: Session = Depends(get_db),
):
    """List all agents"""
    query = db.query(Agent)
    if status_filter:
        query = query.filter(Agent.status == status_filter)
    agents = query.offset(skip).limit(limit).all()
    return [agent_to_response(agent) for agent in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get a specific agent by ID"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent_to_response(agent)


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: str, agent_data: AgentUpdate, db: Session = Depends(get_db)):
    """Update an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    return agent_to_response(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db.delete(agent)
    db.commit()
    return None


@router.post("/{agent_id}/start", response_model=AgentResponse)
def start_agent(agent_id: str, db: Session = Depends(get_db)):
    """Start an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.status == AgentStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Agent is already running")

    agent.status = AgentStatus.RUNNING
    agent.last_active_at = datetime.utcnow()
    agent.error_message = None
    db.commit()
    db.refresh(agent)
    return agent_to_response(agent)


@router.post("/{agent_id}/stop", response_model=AgentResponse)
def stop_agent(agent_id: str, db: Session = Depends(get_db)):
    """Stop an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.status = AgentStatus.STOPPED
    agent.last_active_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    return agent_to_response(agent)


@router.post("/{agent_id}/pause", response_model=AgentResponse)
def pause_agent(agent_id: str, db: Session = Depends(get_db)):
    """Pause an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.status != AgentStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Can only pause running agents")

    agent.status = AgentStatus.PAUSED
    agent.last_active_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    return agent_to_response(agent)


@router.post("/{agent_id}/resume", response_model=AgentResponse)
def resume_agent(agent_id: str, db: Session = Depends(get_db)):
    """Resume a paused agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.status != AgentStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Can only resume paused agents")

    agent.status = AgentStatus.RUNNING
    agent.last_active_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    return agent_to_response(agent)


@router.post("/{agent_id}/execute", response_model=AgentExecutionResponse)
def execute_agent(
    agent_id: str,
    execution_request: AgentExecutionRequest,
    db: Session = Depends(get_db),
):
    """Execute an agent with a prompt using LiteLLM"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Extract user metadata from config if provided
    user_metadata = {}
    if execution_request.config and "user_metadata" in execution_request.config:
        user_metadata = execution_request.config["user_metadata"]

    # Create execution record
    execution = Execution(
        execution_type=ExecutionType.AGENT,
        entity_id=agent.id,
        entity_name=agent.name,
        prompt=execution_request.prompt,
        system_prompt=execution_request.system_prompt,
        status=ExecutionStatus.RUNNING,
        execution_metadata={
            "user_id": user_metadata.get("user_id"),
            "user_name": user_metadata.get("user_name"),
            "user_email": user_metadata.get("user_email"),
            "user_avatar": user_metadata.get("user_avatar"),
        },
    )
    db.add(execution)
    db.flush()  # Get execution ID without committing
    execution.started_at = datetime.utcnow()

    # Extract model configuration
    model = agent.model_id
    model_config = agent.model_config or {}

    # Get system prompt from configuration if not provided
    system_prompt = execution_request.system_prompt
    if not system_prompt and "system_prompt" in agent.configuration:
        system_prompt = agent.configuration["system_prompt"]

    try:
        # Execute using LiteLLM service
        result = litellm_service.execute_agent(
            prompt=execution_request.prompt,
            model=model,
            system_prompt=system_prompt,
            **model_config,
        )

        # Update execution record with results
        execution.response = result.get("response")
        execution.usage = result.get("usage", {})
        execution.execution_metadata = {
            "model": result.get("model"),
            "finish_reason": result.get("finish_reason"),
        }

        if result.get("success"):
            execution.status = ExecutionStatus.COMPLETED
            agent.status = AgentStatus.COMPLETED
        else:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = result.get("error")
            agent.status = AgentStatus.FAILED
            agent.error_message = result.get("error")

        execution.completed_at = datetime.utcnow()

    except Exception as e:
        # Handle execution errors
        execution.status = ExecutionStatus.FAILED
        execution.error_message = str(e)
        execution.completed_at = datetime.utcnow()
        agent.status = AgentStatus.FAILED
        agent.error_message = str(e)
        result = {
            "success": False,
            "error": str(e),
            "model": model,
            "usage": None,
            "finish_reason": None,
        }

    # Update agent state
    agent.last_active_at = datetime.utcnow()
    db.commit()

    return AgentExecutionResponse(
        execution_id=execution.id,
        **result
    )


@router.post("/{agent_id}/execute/stream")
def execute_agent_stream(
    agent_id: str,
    execution_request: AgentExecutionRequest,
    db: Session = Depends(get_db),
):
    """Execute an agent with a prompt using LiteLLM (streaming response)"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Extract model configuration
    model = agent.model_id
    model_config = agent.model_config or {}

    # Get system prompt from configuration if not provided
    system_prompt = execution_request.system_prompt
    if not system_prompt and "system_prompt" in agent.configuration:
        system_prompt = agent.configuration["system_prompt"]

    # Update agent state
    agent.last_active_at = datetime.utcnow()
    agent.status = AgentStatus.RUNNING
    db.commit()

    # Execute using LiteLLM service (streaming)
    return StreamingResponse(
        litellm_service.execute_agent_stream(
            prompt=execution_request.prompt,
            model=model,
            system_prompt=system_prompt,
            **model_config,
        ),
        media_type="text/event-stream",
    )
