"""
Analytics router for execution metrics and reporting.

This router provides endpoints for:
1. Persisting analytics data from workers (turns, tool calls, tasks)
2. Querying aggregated analytics for reporting
3. Organization-level metrics and cost tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import structlog
import uuid as uuid_lib
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from sqlalchemy.inspection import inspect

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from control_plane_api.app.models.execution import Execution
from control_plane_api.app.models.analytics import ExecutionTurn, ExecutionToolCall, ExecutionTask

# Initialize logger first, before using it in import error handling
logger = structlog.get_logger()

# Initialize state transition variables at module level (before import)
# This ensures they are always defined, preventing UnboundLocalError
StateTransitionService = None
update_execution_state_safe = None
STATE_TRANSITION_AVAILABLE = False

# Import state transition utilities at module level to avoid scope issues
try:
    from control_plane_api.app.services.state_transition_service import StateTransitionService, update_execution_state_safe
    STATE_TRANSITION_AVAILABLE = True
except ImportError as e:
    logger.warning("state_transition_service_not_available", error=str(e))
    # Variables already initialized above, no need to set to None again

router = APIRouter()


# Helper function to convert SQLAlchemy objects to dictionaries
def model_to_dict(obj):
    """Convert SQLAlchemy model instance to dictionary"""
    if obj is None:
        return None
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


# ============================================================================
# Pydantic Schemas for Analytics Data
# ============================================================================

class TurnMetricsCreate(BaseModel):
    """Schema for creating a turn metrics record"""
    execution_id: str
    turn_number: int
    turn_id: Optional[str] = None
    model: str
    model_provider: Optional[str] = None
    started_at: str  # ISO timestamp
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    total_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    cache_read_cost: float = 0.0
    cache_creation_cost: float = 0.0
    total_cost: float = 0.0
    finish_reason: Optional[str] = None
    response_preview: Optional[str] = None
    tools_called_count: int = 0
    tools_called_names: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    metrics: dict = Field(default_factory=dict)
    # Agentic Engineering Minutes (AEM) fields
    runtime_minutes: float = 0.0
    model_weight: float = 1.0
    tool_calls_weight: float = 1.0
    aem_value: float = 0.0
    aem_cost: float = 0.0


class ToolCallCreate(BaseModel):
    """Schema for creating a tool call record"""
    execution_id: str
    turn_id: Optional[str] = None  # UUID of the turn (if available)
    tool_name: str
    tool_use_id: Optional[str] = None
    started_at: str  # ISO timestamp
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[str] = None
    tool_output_size: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class TaskCreate(BaseModel):
    """Schema for creating a task record"""
    execution_id: str
    task_number: Optional[int] = None
    task_id: Optional[str] = None
    task_description: str
    task_type: Optional[str] = None
    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class TaskUpdate(BaseModel):
    """Schema for updating a task's status"""
    status: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    result: Optional[str] = None
    error_message: Optional[str] = None


class BatchAnalyticsCreate(BaseModel):
    """Schema for batch creating analytics data (used by workers to send all data at once)"""
    execution_id: str
    turns: List[TurnMetricsCreate] = Field(default_factory=list)
    tool_calls: List[ToolCallCreate] = Field(default_factory=list)
    tasks: List[TaskCreate] = Field(default_factory=list)


# ============================================================================
# Data Persistence Endpoints (Used by Workers)
# ============================================================================

@router.post("/turns", status_code=status.HTTP_201_CREATED)
async def create_turn_metrics(
    turn_data: TurnMetricsCreate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Create a turn metrics record.

    This endpoint is called by workers to persist per-turn LLM metrics
    including tokens, cost, duration, and tool usage.
    """
    try:
        # Verify execution belongs to organization
        execution = db.query(Execution).filter(
            Execution.id == turn_data.execution_id,
            Execution.organization_id == organization["id"]
        ).first()
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        turn_record = ExecutionTurn(
            id=uuid_lib.uuid4(),
            organization_id=organization["id"],
            execution_id=turn_data.execution_id,
            turn_number=turn_data.turn_number,
            turn_id=turn_data.turn_id,
            model=turn_data.model,
            model_provider=turn_data.model_provider,
            started_at=turn_data.started_at,
            completed_at=turn_data.completed_at,
            duration_ms=turn_data.duration_ms,
            input_tokens=turn_data.input_tokens,
            output_tokens=turn_data.output_tokens,
            cache_read_tokens=turn_data.cache_read_tokens,
            cache_creation_tokens=turn_data.cache_creation_tokens,
            total_tokens=turn_data.total_tokens,
            input_cost=turn_data.input_cost,
            output_cost=turn_data.output_cost,
            cache_read_cost=turn_data.cache_read_cost,
            cache_creation_cost=turn_data.cache_creation_cost,
            total_cost=turn_data.total_cost,
            finish_reason=turn_data.finish_reason,
            response_preview=turn_data.response_preview[:500] if turn_data.response_preview else None,
            tools_called_count=turn_data.tools_called_count,
            tools_called_names=turn_data.tools_called_names,
            error_message=turn_data.error_message,
            metrics=turn_data.metrics,
            runtime_minutes=turn_data.runtime_minutes,
            model_weight=turn_data.model_weight,
            tool_calls_weight=turn_data.tool_calls_weight,
            aem_value=turn_data.aem_value,
            aem_cost=turn_data.aem_cost,
        )

        db.add(turn_record)
        db.commit()
        db.refresh(turn_record)

        logger.info(
            "turn_metrics_created",
            execution_id=turn_data.execution_id,
            turn_number=turn_data.turn_number,
            model=turn_data.model,
            tokens=turn_data.total_tokens,
            cost=turn_data.total_cost,
            org_id=organization["id"]
        )

        # Trigger intelligent state transition asynchronously
        if STATE_TRANSITION_AVAILABLE and StateTransitionService:
            try:
                transition_service = StateTransitionService(organization_id=organization["id"])

                # Analyze and transition (async, with timeout)
                decision = await asyncio.wait_for(
                    transition_service.analyze_and_transition(
                        execution_id=turn_data.execution_id,
                        turn_number=turn_data.turn_number,
                        turn_data=turn_data,
                    ),
                    timeout=5.0  # 5 second max
                )

                logger.info(
                    "state_transition_decision",
                    execution_id=turn_data.execution_id,
                    turn_number=turn_data.turn_number,
                    from_state="running",
                    to_state=decision.recommended_state,
                    confidence=decision.confidence,
                    reasoning=decision.reasoning[:200],
                )

            except asyncio.TimeoutError:
                logger.warning(
                    "state_transition_timeout",
                    execution_id=turn_data.execution_id,
                    turn_number=turn_data.turn_number,
                )
                # Fallback: default to waiting_for_input
                if update_execution_state_safe:
                    try:
                        await update_execution_state_safe(
                            execution_id=turn_data.execution_id,
                            state="waiting_for_input",
                            reasoning="AI decision timed out - defaulting to safe state",
                        )
                    except Exception as fallback_error:
                        logger.warning("state_transition_fallback_failed", error=str(fallback_error))
            except Exception as e:
                logger.error(
                    "state_transition_failed",
                    execution_id=turn_data.execution_id,
                    error=str(e),
                )
                # Fallback: default to waiting_for_input
                if update_execution_state_safe:
                    try:
                        await update_execution_state_safe(
                            execution_id=turn_data.execution_id,
                            state="waiting_for_input",
                            reasoning=f"AI decision failed: {str(e)[:200]}",
                        )
                    except Exception as fallback_error:
                        logger.warning("state_transition_fallback_failed", error=str(fallback_error))
        else:
            logger.warning(
                "state_transition_service_unavailable",
                execution_id=turn_data.execution_id,
                note="Falling back to default status update"
            )
            # CRITICAL FIX: Even if state transition service is unavailable,
            # we MUST update the status to prevent infinite workflow loops
            if update_execution_state_safe:
                try:
                    await update_execution_state_safe(
                        execution_id=turn_data.execution_id,
                        state="waiting_for_input",
                        reasoning="State transition service unavailable - using safe default",
                    )
                    logger.info(
                        "fallback_status_update_success",
                        execution_id=turn_data.execution_id,
                        status="waiting_for_input"
                    )
                except Exception as fallback_error:
                    logger.error(
                        "fallback_status_update_failed",
                        execution_id=turn_data.execution_id,
                        error=str(fallback_error),
                        note="CRITICAL: Status may remain 'running' - workflow may loop"
                    )
            else:
                # Last resort: direct database update using SQLAlchemy
                logger.warning(
                    "using_direct_db_update",
                    execution_id=turn_data.execution_id,
                    note="update_execution_state_safe not available - using direct database access"
                )
                try:
                    execution.status = "waiting_for_input"
                    db.commit()
                    logger.info(
                        "direct_db_update_success",
                        execution_id=turn_data.execution_id,
                        status="waiting_for_input"
                    )
                except Exception as db_error:
                    logger.error(
                        "direct_db_update_failed",
                        execution_id=turn_data.execution_id,
                        error=str(db_error),
                        note="CRITICAL: Status remains 'running' - workflow will loop indefinitely"
                    )

        return {"success": True, "turn_id": str(turn_record.id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("turn_metrics_create_failed", error=str(e), execution_id=turn_data.execution_id)
        raise HTTPException(status_code=500, detail=f"Failed to create turn metrics: {str(e)}")


@router.post("/tool-calls", status_code=status.HTTP_201_CREATED)
async def create_tool_call(
    tool_call_data: ToolCallCreate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Create a tool call record.

    This endpoint is called by workers to persist tool execution details
    including timing, success/failure, and error information.
    """
    try:
        # Verify execution belongs to organization
        execution = db.query(Execution).filter(
            Execution.id == tool_call_data.execution_id,
            Execution.organization_id == organization["id"]
        ).first()
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Truncate tool_output if too large (store first 10KB)
        tool_output = tool_call_data.tool_output
        tool_output_size = len(tool_output) if tool_output else 0
        if tool_output and len(tool_output) > 10000:
            tool_output = tool_output[:10000] + "... [truncated]"

        tool_call_record = ExecutionToolCall(
            id=uuid_lib.uuid4(),
            organization_id=organization["id"],
            execution_id=tool_call_data.execution_id,
            turn_id=tool_call_data.turn_id,
            tool_name=tool_call_data.tool_name,
            tool_use_id=tool_call_data.tool_use_id,
            started_at=tool_call_data.started_at,
            completed_at=tool_call_data.completed_at,
            duration_ms=tool_call_data.duration_ms,
            tool_input=tool_call_data.tool_input,
            tool_output=tool_output,
            tool_output_size=tool_output_size,
            success=tool_call_data.success,
            error_message=tool_call_data.error_message,
            error_type=tool_call_data.error_type,
            metadata_=tool_call_data.metadata,
        )

        db.add(tool_call_record)
        db.commit()
        db.refresh(tool_call_record)

        logger.info(
            "tool_call_created",
            execution_id=tool_call_data.execution_id,
            tool_name=tool_call_data.tool_name,
            success=tool_call_data.success,
            duration_ms=tool_call_data.duration_ms,
            org_id=organization["id"]
        )

        return {"success": True, "tool_call_id": str(tool_call_record.id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("tool_call_create_failed", error=str(e), execution_id=tool_call_data.execution_id)
        raise HTTPException(status_code=500, detail=f"Failed to create tool call: {str(e)}")


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Create a task record.

    This endpoint is called by workers to persist task tracking information.
    """
    try:
        # Verify execution belongs to organization
        execution = db.query(Execution).filter(
            Execution.id == task_data.execution_id,
            Execution.organization_id == organization["id"]
        ).first()
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        task_record = ExecutionTask(
            id=uuid_lib.uuid4(),
            organization_id=organization["id"],
            execution_id=task_data.execution_id,
            task_number=task_data.task_number,
            task_id=task_data.task_id,
            task_description=task_data.task_description,
            task_type=task_data.task_type,
            status=task_data.status,
            started_at=task_data.started_at,
            completed_at=task_data.completed_at,
            duration_ms=task_data.duration_ms,
            result=task_data.result,
            error_message=task_data.error_message,
            custom_metadata=task_data.metadata,
        )

        db.add(task_record)
        db.commit()
        db.refresh(task_record)

        logger.info(
            "task_created",
            execution_id=task_data.execution_id,
            task_description=task_data.task_description[:100],
            status=task_data.status,
            org_id=organization["id"]
        )

        return {"success": True, "task_id": str(task_record.id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("task_create_failed", error=str(e), execution_id=task_data.execution_id)
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def create_batch_analytics(
    batch_data: BatchAnalyticsCreate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Create analytics data in batch.

    This endpoint allows workers to send all analytics data (turns, tool calls, tasks)
    in a single request, reducing round trips and improving performance.
    """
    try:
        # Verify execution belongs to organization
        execution = db.query(Execution).filter(
            Execution.id == batch_data.execution_id,
            Execution.organization_id == organization["id"]
        ).first()
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        results = {
            "turns_created": 0,
            "tool_calls_created": 0,
            "tasks_created": 0,
            "errors": []
        }

        # Create turns
        if batch_data.turns:
            for turn in batch_data.turns:
                try:
                    turn_record = ExecutionTurn(
                        id=uuid_lib.uuid4(),
                        organization_id=organization["id"],
                        execution_id=batch_data.execution_id,
                        turn_number=turn.turn_number,
                        turn_id=turn.turn_id,
                        model=turn.model,
                        model_provider=turn.model_provider,
                        started_at=turn.started_at,
                        completed_at=turn.completed_at,
                        duration_ms=turn.duration_ms,
                        input_tokens=turn.input_tokens,
                        output_tokens=turn.output_tokens,
                        cache_read_tokens=turn.cache_read_tokens,
                        cache_creation_tokens=turn.cache_creation_tokens,
                        total_tokens=turn.total_tokens,
                        input_cost=turn.input_cost,
                        output_cost=turn.output_cost,
                        cache_read_cost=turn.cache_read_cost,
                        cache_creation_cost=turn.cache_creation_cost,
                        total_cost=turn.total_cost,
                        finish_reason=turn.finish_reason,
                        response_preview=turn.response_preview[:500] if turn.response_preview else None,
                        tools_called_count=turn.tools_called_count,
                        tools_called_names=turn.tools_called_names,
                        error_message=turn.error_message,
                        metrics=turn.metrics,
                        runtime_minutes=turn.runtime_minutes,
                        model_weight=turn.model_weight,
                        tool_calls_weight=turn.tool_calls_weight,
                        aem_value=turn.aem_value,
                        aem_cost=turn.aem_cost,
                    )
                    db.add(turn_record)
                    results["turns_created"] += 1
                except Exception as e:
                    results["errors"].append(f"Turn {turn.turn_number}: {str(e)}")

        # Create tool calls
        if batch_data.tool_calls:
            for tool_call in batch_data.tool_calls:
                try:
                    tool_output = tool_call.tool_output
                    tool_output_size = len(tool_output) if tool_output else 0
                    if tool_output and len(tool_output) > 10000:
                        tool_output = tool_output[:10000] + "... [truncated]"

                    tool_call_record = ExecutionToolCall(
                        id=uuid_lib.uuid4(),
                        organization_id=organization["id"],
                        execution_id=batch_data.execution_id,
                        turn_id=tool_call.turn_id,
                        tool_name=tool_call.tool_name,
                        tool_use_id=tool_call.tool_use_id,
                        started_at=tool_call.started_at,
                        completed_at=tool_call.completed_at,
                        duration_ms=tool_call.duration_ms,
                        tool_input=tool_call.tool_input,
                        tool_output=tool_output,
                        tool_output_size=tool_output_size,
                        success=tool_call.success,
                        error_message=tool_call.error_message,
                        error_type=tool_call.error_type,
                        metadata_=tool_call.metadata,
                    )
                    db.add(tool_call_record)
                    results["tool_calls_created"] += 1
                except Exception as e:
                    results["errors"].append(f"Tool call {tool_call.tool_name}: {str(e)}")

        # Create tasks
        if batch_data.tasks:
            for task in batch_data.tasks:
                try:
                    task_record = ExecutionTask(
                        id=uuid_lib.uuid4(),
                        organization_id=organization["id"],
                        execution_id=batch_data.execution_id,
                        task_number=task.task_number,
                        task_id=task.task_id,
                        task_description=task.task_description,
                        task_type=task.task_type,
                        status=task.status,
                        started_at=task.started_at,
                        completed_at=task.completed_at,
                        duration_ms=task.duration_ms,
                        result=task.result,
                        error_message=task.error_message,
                        custom_metadata=task.metadata,
                    )
                    db.add(task_record)
                    results["tasks_created"] += 1
                except Exception as e:
                    results["errors"].append(f"Task {task.task_description[:50]}: {str(e)}")

        # Commit all records at once
        db.commit()

        logger.info(
            "batch_analytics_created",
            execution_id=batch_data.execution_id,
            turns_created=results["turns_created"],
            tool_calls_created=results["tool_calls_created"],
            tasks_created=results["tasks_created"],
            errors=len(results["errors"]),
            org_id=organization["id"]
        )

        return {
            "success": len(results["errors"]) == 0,
            "execution_id": batch_data.execution_id,
            **results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("batch_analytics_create_failed", error=str(e), execution_id=batch_data.execution_id)
        raise HTTPException(status_code=500, detail=f"Failed to create batch analytics: {str(e)}")


@router.patch("/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Update a task's status and completion information.

    This endpoint is called by workers to update task progress.
    """
    try:
        # Find the task
        task = db.query(ExecutionTask).filter(
            ExecutionTask.id == task_id,
            ExecutionTask.organization_id == organization["id"]
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Update fields
        if task_update.status is not None:
            task.status = task_update.status
        if task_update.completed_at is not None:
            task.completed_at = task_update.completed_at
        if task_update.duration_ms is not None:
            task.duration_ms = task_update.duration_ms
        if task_update.result is not None:
            task.result = task_update.result
        if task_update.error_message is not None:
            task.error_message = task_update.error_message

        task.updated_at = datetime.utcnow()

        db.commit()

        logger.info(
            "task_updated",
            task_id=task_id,
            status=task_update.status,
            org_id=organization["id"]
        )

        return {"success": True, "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("task_update_failed", error=str(e), task_id=task_id)
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")


# ============================================================================
# Reporting Endpoints (For Analytics Dashboard)
# ============================================================================

@router.get("/executions/{execution_id}/details")
async def get_execution_analytics(
    execution_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive analytics for a specific execution.

    Returns:
    - Execution summary
    - Per-turn metrics
    - Tool call details
    - Task breakdown
    - Total costs and token usage
    """
    try:
        # Get execution
        execution = db.query(Execution).filter(
            Execution.id == execution_id,
            Execution.organization_id == organization["id"]
        ).first()
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Get turns
        turns = db.query(ExecutionTurn).filter(
            ExecutionTurn.execution_id == execution_id,
            ExecutionTurn.organization_id == organization["id"]
        ).order_by(ExecutionTurn.turn_number).all()

        # Get tool calls
        tool_calls = db.query(ExecutionToolCall).filter(
            ExecutionToolCall.execution_id == execution_id,
            ExecutionToolCall.organization_id == organization["id"]
        ).order_by(ExecutionToolCall.started_at).all()

        # Get tasks
        tasks = db.query(ExecutionTask).filter(
            ExecutionTask.execution_id == execution_id,
            ExecutionTask.organization_id == organization["id"]
        ).order_by(ExecutionTask.task_number).all()

        # Convert to dicts
        turns_data = [model_to_dict(turn) for turn in turns]
        tool_calls_data = [model_to_dict(tc) for tc in tool_calls]
        tasks_data = [model_to_dict(task) for task in tasks]

        # Calculate aggregated metrics
        total_turns = len(turns)
        total_tokens = sum(turn.total_tokens or 0 for turn in turns)
        total_cost = sum(turn.total_cost or 0.0 for turn in turns)
        total_duration_ms = sum(turn.duration_ms or 0 for turn in turns)

        total_tool_calls = len(tool_calls)
        successful_tool_calls = sum(1 for tc in tool_calls if tc.success)
        failed_tool_calls = total_tool_calls - successful_tool_calls

        unique_tools_used = list(set(tc.tool_name for tc in tool_calls))

        # Task statistics
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == "completed")
        failed_tasks = sum(1 for task in tasks if task.status == "failed")
        pending_tasks = sum(1 for task in tasks if task.status in ["pending", "in_progress"])

        return {
            "execution": model_to_dict(execution),
            "summary": {
                "execution_id": execution_id,
                "total_turns": total_turns,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "total_duration_ms": total_duration_ms,
                "total_tool_calls": total_tool_calls,
                "successful_tool_calls": successful_tool_calls,
                "failed_tool_calls": failed_tool_calls,
                "unique_tools_used": unique_tools_used,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "pending_tasks": pending_tasks,
            },
            "turns": turns_data,
            "tool_calls": tool_calls_data,
            "tasks": tasks_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_execution_analytics_failed", error=str(e), execution_id=execution_id)
        raise HTTPException(status_code=500, detail=f"Failed to get execution analytics: {str(e)}")


@router.get("/summary")
async def get_organization_analytics_summary(
    request: Request,
    organization: dict = Depends(get_current_organization),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include in the summary"),
    db: Session = Depends(get_db),
):
    """
    Get aggregated analytics summary for the organization.

    Returns high-level metrics over the specified time period:
    - Total executions
    - Total cost
    - Total tokens used
    - Model usage breakdown
    - Tool usage statistics
    - Success rates
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get executions in date range
        executions = db.query(Execution).filter(
            Execution.organization_id == organization["id"],
            Execution.created_at >= start_date
        ).all()

        if not executions:
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_executions": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "total_turns": 0,
                "total_tool_calls": 0,
                "models_used": {},
                "tools_used": {},
                "success_rate": 0.0,
            }

        # Get all turns for these executions
        turns = db.query(ExecutionTurn).filter(
            ExecutionTurn.organization_id == organization["id"],
            ExecutionTurn.created_at >= start_date
        ).all()

        # Get all tool calls for these executions
        tool_calls = db.query(ExecutionToolCall).filter(
            ExecutionToolCall.organization_id == organization["id"],
            ExecutionToolCall.created_at >= start_date
        ).all()

        # Calculate aggregates
        total_executions = len(executions)
        successful_executions = sum(1 for exec in executions if exec.status == "completed")
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0.0

        total_turns = len(turns)
        total_tokens = sum(turn.total_tokens or 0 for turn in turns)
        total_cost = sum(turn.total_cost or 0.0 for turn in turns)

        # Model usage breakdown
        models_used = {}
        for turn in turns:
            model = turn.model or "unknown"
            if model not in models_used:
                models_used[model] = {
                    "count": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                }
            models_used[model]["count"] += 1
            models_used[model]["total_tokens"] += turn.total_tokens or 0
            models_used[model]["total_cost"] += turn.total_cost or 0.0

        # Tool usage breakdown
        tools_used = {}
        total_tool_calls = len(tool_calls)
        for tool_call in tool_calls:
            tool_name = tool_call.tool_name or "unknown"
            if tool_name not in tools_used:
                tools_used[tool_name] = {
                    "count": 0,
                    "success_count": 0,
                    "fail_count": 0,
                    "avg_duration_ms": 0,
                    "total_duration_ms": 0,
                }
            tools_used[tool_name]["count"] += 1
            if tool_call.success:
                tools_used[tool_name]["success_count"] += 1
            else:
                tools_used[tool_name]["fail_count"] += 1

            duration = tool_call.duration_ms or 0
            tools_used[tool_name]["total_duration_ms"] += duration

        # Calculate average durations
        for tool_name, stats in tools_used.items():
            if stats["count"] > 0:
                stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["count"]

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": total_executions - successful_executions,
            "success_rate": round(success_rate, 2),
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "total_turns": total_turns,
            "total_tool_calls": total_tool_calls,
            "models_used": models_used,
            "tools_used": tools_used,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_analytics_summary_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(status_code=500, detail=f"Failed to get analytics summary: {str(e)}")


@router.get("/costs")
async def get_cost_breakdown(
    request: Request,
    organization: dict = Depends(get_current_organization),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
    group_by: str = Query(default="day", regex="^(day|week|month)$", description="Group costs by time period"),
    db: Session = Depends(get_db),
):
    """
    Get detailed cost breakdown over time.

    Returns cost metrics grouped by the specified time period.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get all turns in date range
        turns = db.query(ExecutionTurn).filter(
            ExecutionTurn.organization_id == organization["id"],
            ExecutionTurn.created_at >= start_date
        ).order_by(ExecutionTurn.created_at).all()

        # Group by time period
        cost_by_period = {}
        for turn in turns:
            created_at = turn.created_at.replace(tzinfo=None) if turn.created_at else datetime.utcnow()

            # Determine period key
            if group_by == "day":
                period_key = created_at.strftime("%Y-%m-%d")
            elif group_by == "week":
                period_key = created_at.strftime("%Y-W%U")
            else:  # month
                period_key = created_at.strftime("%Y-%m")

            if period_key not in cost_by_period:
                cost_by_period[period_key] = {
                    "period": period_key,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "turn_count": 0,
                    "models": {},
                }

            cost_by_period[period_key]["total_cost"] += turn.total_cost or 0.0
            cost_by_period[period_key]["total_tokens"] += turn.total_tokens or 0
            cost_by_period[period_key]["total_input_tokens"] += turn.input_tokens or 0
            cost_by_period[period_key]["total_output_tokens"] += turn.output_tokens or 0
            cost_by_period[period_key]["turn_count"] += 1

            # Track by model
            model = turn.model or "unknown"
            if model not in cost_by_period[period_key]["models"]:
                cost_by_period[period_key]["models"][model] = {
                    "cost": 0.0,
                    "tokens": 0,
                    "turns": 0,
                }
            cost_by_period[period_key]["models"][model]["cost"] += turn.total_cost or 0.0
            cost_by_period[period_key]["models"][model]["tokens"] += turn.total_tokens or 0
            cost_by_period[period_key]["models"][model]["turns"] += 1

        # Convert to list and sort
        cost_breakdown = sorted(cost_by_period.values(), key=lambda x: x["period"])

        # Calculate totals
        total_cost = sum(period["total_cost"] for period in cost_breakdown)
        total_tokens = sum(period["total_tokens"] for period in cost_breakdown)

        return {
            "period_days": days,
            "group_by": group_by,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "breakdown": cost_breakdown,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_cost_breakdown_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(status_code=500, detail=f"Failed to get cost breakdown: {str(e)}")


@router.get("/aem/summary")
async def get_aem_summary(
    request: Request,
    organization: dict = Depends(get_current_organization),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db),
):
    """
    Get Agentic Engineering Minutes (AEM) summary.

    Returns:
    - Total AEM consumed
    - Total AEM cost
    - Breakdown by model tier (Premium, Mid, Basic) - provider-agnostic classification
    - Average runtime, model weight, tool complexity
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get all turns with AEM data
        turns = db.query(ExecutionTurn).filter(
            ExecutionTurn.organization_id == organization["id"],
            ExecutionTurn.created_at >= start_date
        ).all()

        if not turns:
            return {
                "period_days": days,
                "total_aem": 0.0,
                "total_aem_cost": 0.0,
                "total_runtime_minutes": 0.0,
                "turn_count": 0,
                "by_model_tier": {},
                "average_model_weight": 0.0,
                "average_tool_complexity": 0.0,
            }

        # Calculate totals
        total_aem = sum(turn.aem_value or 0.0 for turn in turns)
        total_aem_cost = sum(turn.aem_cost or 0.0 for turn in turns)
        total_runtime_minutes = sum(turn.runtime_minutes or 0.0 for turn in turns)
        total_model_weight = sum(turn.model_weight or 1.0 for turn in turns)
        total_tool_weight = sum(turn.tool_calls_weight or 1.0 for turn in turns)

        # Breakdown by model tier (using provider-agnostic naming)
        by_tier = {}
        for turn in turns:
            weight = turn.model_weight or 1.0

            # Classify into universal tiers
            if weight >= 1.5:
                tier = "premium"  # Most capable models
            elif weight >= 0.8:
                tier = "mid"      # Balanced models
            else:
                tier = "basic"    # Fast/efficient models

            if tier not in by_tier:
                by_tier[tier] = {
                    "tier": tier,
                    "turn_count": 0,
                    "total_aem": 0.0,
                    "total_aem_cost": 0.0,
                    "total_runtime_minutes": 0.0,
                    "total_tokens": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cache_read_tokens": 0,
                    "total_cache_creation_tokens": 0,
                    "total_token_cost": 0.0,
                    "models": set(),
                }

            by_tier[tier]["turn_count"] += 1
            by_tier[tier]["total_aem"] += turn.aem_value or 0.0
            by_tier[tier]["total_aem_cost"] += turn.aem_cost or 0.0
            by_tier[tier]["total_runtime_minutes"] += turn.runtime_minutes or 0.0
            by_tier[tier]["total_tokens"] += turn.total_tokens or 0
            by_tier[tier]["total_input_tokens"] += turn.input_tokens or 0
            by_tier[tier]["total_output_tokens"] += turn.output_tokens or 0
            by_tier[tier]["total_cache_read_tokens"] += turn.cache_read_tokens or 0
            by_tier[tier]["total_cache_creation_tokens"] += turn.cache_creation_tokens or 0
            by_tier[tier]["total_token_cost"] += turn.total_cost or 0.0
            by_tier[tier]["models"].add(turn.model or "unknown")

        # Convert sets to lists for JSON serialization
        for tier_data in by_tier.values():
            tier_data["models"] = list(tier_data["models"])

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_aem": round(total_aem, 2),
            "total_aem_cost": round(total_aem_cost, 2),
            "total_runtime_minutes": round(total_runtime_minutes, 2),
            "turn_count": len(turns),
            "average_aem_per_turn": round(total_aem / len(turns), 2) if turns else 0.0,
            "average_model_weight": round(total_model_weight / len(turns), 2) if turns else 0.0,
            "average_tool_complexity": round(total_tool_weight / len(turns), 2) if turns else 0.0,
            "by_model_tier": by_tier,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_aem_summary_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(status_code=500, detail=f"Failed to get AEM summary: {str(e)}")


@router.get("/aem/trends")
async def get_aem_trends(
    request: Request,
    organization: dict = Depends(get_current_organization),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
    group_by: str = Query(default="day", regex="^(day|week|month)$", description="Group by time period"),
    db: Session = Depends(get_db),
):
    """
    Get AEM trends over time.

    Returns AEM consumption grouped by time period for trend analysis.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get all turns with AEM data
        turns = db.query(ExecutionTurn).filter(
            ExecutionTurn.organization_id == organization["id"],
            ExecutionTurn.created_at >= start_date
        ).order_by(ExecutionTurn.created_at).all()

        # Group by time period
        aem_by_period = {}
        for turn in turns:
            created_at = turn.created_at.replace(tzinfo=None) if turn.created_at else datetime.utcnow()

            # Determine period key
            if group_by == "day":
                period_key = created_at.strftime("%Y-%m-%d")
            elif group_by == "week":
                period_key = created_at.strftime("%Y-W%U")
            else:  # month
                period_key = created_at.strftime("%Y-%m")

            if period_key not in aem_by_period:
                aem_by_period[period_key] = {
                    "period": period_key,
                    "total_aem": 0.0,
                    "total_aem_cost": 0.0,
                    "total_runtime_minutes": 0.0,
                    "turn_count": 0,
                    "average_model_weight": 0.0,
                    "average_tool_complexity": 0.0,
                }

            aem_by_period[period_key]["total_aem"] += turn.aem_value or 0.0
            aem_by_period[period_key]["total_aem_cost"] += turn.aem_cost or 0.0
            aem_by_period[period_key]["total_runtime_minutes"] += turn.runtime_minutes or 0.0
            aem_by_period[period_key]["turn_count"] += 1

        # Calculate averages
        for period_data in aem_by_period.values():
            if period_data["turn_count"] > 0:
                # Get turns for this period to calculate weighted averages
                period_turns = [t for t in turns if (t.created_at.replace(tzinfo=None) if t.created_at else datetime.utcnow()).strftime(
                    "%Y-%m-%d" if group_by == "day" else "%Y-W%U" if group_by == "week" else "%Y-%m"
                ) == period_data["period"]]

                total_weight = sum(t.model_weight or 1.0 for t in period_turns)
                total_tool_weight = sum(t.tool_calls_weight or 1.0 for t in period_turns)

                period_data["average_model_weight"] = round(total_weight / len(period_turns), 2)
                period_data["average_tool_complexity"] = round(total_tool_weight / len(period_turns), 2)

        # Convert to list and sort
        aem_trends = sorted(aem_by_period.values(), key=lambda x: x["period"])

        # Calculate totals
        total_aem = sum(period["total_aem"] for period in aem_trends)
        total_aem_cost = sum(period["total_aem_cost"] for period in aem_trends)

        return {
            "period_days": days,
            "group_by": group_by,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_aem": round(total_aem, 2),
            "total_aem_cost": round(total_aem_cost, 2),
            "trends": aem_trends,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_aem_trends_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(status_code=500, detail=f"Failed to get AEM trends: {str(e)}")


@router.get("/storage/summary")
async def get_storage_analytics_summary(
    request: Request,
    organization: dict = Depends(get_current_organization),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
):
    """
    Get storage usage analytics summary.

    Returns:
    - Current storage usage and quota
    - File count and type breakdown
    - Storage growth trend over time
    - Upload/download bandwidth statistics
    """
    try:
        client = get_supabase()

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        start_date_iso = start_date.isoformat()

        # Get current usage from storage_usage table
        usage_result = client.table("storage_usage").select("*").eq(
            "organization_id", organization["id"]
        ).execute()

        if not usage_result.data or len(usage_result.data) == 0:
            # No storage usage yet
            current_usage = {
                "total_bytes_used": 0,
                "total_files_count": 0,
                "quota_bytes": 1073741824,  # 1GB default
                "total_bytes_uploaded": 0,
                "total_bytes_downloaded": 0
            }
        else:
            current_usage = usage_result.data[0]

        # Get file type breakdown from storage_files
        files_result = client.table("storage_files").select(
            "content_type, file_size_bytes, created_at"
        ).eq("organization_id", organization["id"]).is_("deleted_at", "null").execute()

        files = files_result.data if files_result.data else []

        # Calculate file type breakdown
        type_breakdown = {}
        for file in files:
            content_type = file.get("content_type", "unknown")
            if content_type not in type_breakdown:
                type_breakdown[content_type] = {
                    "count": 0,
                    "total_bytes": 0
                }
            type_breakdown[content_type]["count"] += 1
            type_breakdown[content_type]["total_bytes"] += file.get("file_size_bytes", 0)

        # Get storage growth trend (files created over time)
        files_in_period = [f for f in files if f.get("created_at") and f["created_at"] >= start_date_iso]

        # Group by day
        growth_by_day = {}
        for file in files_in_period:
            created_at = datetime.fromisoformat(file["created_at"].replace("Z", "+00:00"))
            day_key = created_at.strftime("%Y-%m-%d")

            if day_key not in growth_by_day:
                growth_by_day[day_key] = {
                    "date": day_key,
                    "files_added": 0,
                    "bytes_added": 0
                }

            growth_by_day[day_key]["files_added"] += 1
            growth_by_day[day_key]["bytes_added"] += file.get("file_size_bytes", 0)

        # Convert to sorted list
        storage_growth_trend = sorted(growth_by_day.values(), key=lambda x: x["date"])

        # Calculate usage percentage
        usage_percentage = (
            (current_usage["total_bytes_used"] / current_usage["quota_bytes"]) * 100
            if current_usage["quota_bytes"] > 0 else 0
        )

        logger.info(
            "storage_analytics_retrieved",
            organization_id=organization["id"],
            total_files=current_usage["total_files_count"],
            usage_percentage=round(usage_percentage, 2)
        )

        return {
            "period_days": days,
            "start_date": start_date_iso,
            "end_date": end_date.isoformat(),
            "current_usage": {
                "total_bytes_used": current_usage["total_bytes_used"],
                "total_files_count": current_usage["total_files_count"],
                "quota_bytes": current_usage["quota_bytes"],
                "remaining_bytes": current_usage["quota_bytes"] - current_usage["total_bytes_used"],
                "usage_percentage": round(usage_percentage, 2),
            },
            "bandwidth_usage": {
                "total_bytes_uploaded": current_usage.get("total_bytes_uploaded", 0),
                "total_bytes_downloaded": current_usage.get("total_bytes_downloaded", 0),
            },
            "file_type_breakdown": type_breakdown,
            "storage_growth_trend": storage_growth_trend,
            "total_file_types": len(type_breakdown),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_storage_analytics_failed", error=str(e), org_id=organization["id"])
        raise HTTPException(status_code=500, detail=f"Failed to get storage analytics: {str(e)}")
