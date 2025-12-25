"""
Task Planning Router - AI-powered task analysis and planning using Claude Code SDK or Agno
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import StreamingResponse
from typing import AsyncIterator, Optional
from sqlalchemy.orm import Session
import structlog
import os
import traceback
import json
import asyncio
import re
import time

from control_plane_api.app.database import get_db
from control_plane_api.app.lib.litellm_pricing import get_litellm_pricing

# Import all models from the new models package
from control_plane_api.app.models.task_planning import (
    TaskPlanRequest,
    TaskPlanResponse,
)

# Import public functions from task_planning library
from control_plane_api.app.lib.task_planning import format_sse_message
from control_plane_api.app.lib.task_planning.planning_workflow import (
    create_planning_workflow as create_multistep_workflow,
    run_planning_workflow_stream,
)

# Import private helper functions directly from helpers module
from control_plane_api.app.lib.task_planning.helpers import (
    _extract_organization_id_from_token,
    _get_organization_id_fallback,
)

# Import planning strategy factory
from control_plane_api.app.services.planning_strategy_factory import get_planning_strategy

# Import entity resolver for converting entity names to UUIDs
from control_plane_api.app.lib.task_planning.entity_resolver import resolve_plan_entities

router = APIRouter()
logger = structlog.get_logger()

# Planning timeout configuration (in seconds)
PLANNING_TIMEOUT = int(os.getenv("PLANNING_TIMEOUT_SECONDS", "180"))  # Default: 3 minutes

# Planning retry configuration
MAX_PLANNING_RETRIES = int(os.getenv("MAX_PLANNING_RETRIES", "2"))  # Default: 2 retries (3 total attempts)

# Planning Strategy Selection (defaults to "agno")
# Options: "claude_code_sdk", "agno"
# Like choosing transportation: train, walk, or flight!
PLANNING_STRATEGY = os.getenv("PLANNING_STRATEGY", "agno").lower()


@router.post("/tasks/plan")
async def plan_task(task_request: TaskPlanRequest, http_request: Request, db: Session = Depends(get_db)):
    """
    Generate an AI-powered task plan (non-streaming)

    Uses the same 2-step workflow as /tasks/plan/stream but returns the final plan directly.
    This endpoint is used by the CLI for fast planning mode.

    The 2-step workflow:
    - Step 1: Analysis & Resource Selection (discovers agents/teams, selects best match)
    - Step 2: Full Plan Generation (creates TaskPlanResponse with costs, risks, etc.)

    Benefits:
    - Faster than old 4-step workflow (45-55s vs 119s)
    - Consistent behavior with streaming endpoint
    - Smart pre-fetching of top 20 resources
    """
    # Extract API token from Authorization header
    auth_header = http_request.headers.get("authorization", "")
    api_token = auth_header.replace("UserKey ", "").replace("Bearer ", "") if auth_header else None

    # Extract organization ID from token (needed for entity resolution)
    organization_id = None
    if not api_token:
        logger.error("no_api_token_provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: No API token provided. Please configure your API token."
        )

    try:
        organization_id = _extract_organization_id_from_token(api_token)
        if not organization_id:
            raise ValueError("Token does not contain organization_id")
        logger.info("extracted_organization_id", organization_id=organization_id)
    except Exception as e:
        logger.error("failed_to_extract_organization_id", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: Could not extract organization from token. Error: {str(e)}"
        )

    try:
        logger.info(
            "task_planning_requested_nonstreaming",
            description=task_request.description[:100],
            quick_mode=task_request.quick_mode,
            organization_id=organization_id,
        )

        # Let the planner fetch everything from DB (no outer_context needed)
        outer_context = None

        # Create the unified 2-step workflow
        logger.info(
            "using_unified_2step_workflow_nonstreaming",
            message="Unified 2-step workflow (same as streaming endpoint)",
            quick_mode=task_request.quick_mode
        )
        workflow = create_multistep_workflow(
            db=db,
            organization_id=organization_id,
            api_token=api_token,
            quick_mode=task_request.quick_mode,
            outer_context=outer_context
        )

        # Run workflow without streaming (collect all events internally)
        logger.info("executing_workflow_nonstreaming")

        # Create a simple event collector (we don't need to stream events to client)
        events_collected = []
        def collect_event(event):
            events_collected.append(event)

        # Run the workflow
        plan = run_planning_workflow_stream(
            workflow,
            task_request,
            collect_event,  # Internal event collector
            task_request.quick_mode
        )

        # Resolve entity names to UUIDs before returning the plan
        await resolve_plan_entities(
            plan_response=plan,
            organization_id=organization_id,
            db=db
        )
        logger.info("plan_entities_resolved_nonstreaming", plan_title=plan.title)

        logger.info("task_plan_generated_nonstreaming", title=plan.title)
        return {"plan": plan}

    except ValueError as e:
        # Validation errors should return 422 (Unprocessable Entity)
        error_msg = str(e)
        if "validation" in error_msg.lower() or "does NOT exist" in error_msg or "does not exist" in error_msg:
            logger.error("task_planning_validation_error", error=error_msg, traceback=traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "validation_failed",
                    "message": "The task planner generated invalid output that failed validation",
                    "details": error_msg,
                    "suggestion": "This usually means the AI tried to use non-existent agents/teams. Please try again or check your available resources."
                }
            )
        else:
            # Other ValueError issues
            logger.error("task_planning_value_error", error=str(e), traceback=traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Task planning failed: {str(e)}")

    except Exception as e:
        logger.error("task_planning_error", error=str(e), traceback=traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Task planning failed: {str(e)}")


async def generate_task_plan_stream(
    request: TaskPlanRequest, db: Session, api_token: Optional[str] = None
) -> AsyncIterator[str]:
    """
    Generate task plan using unified 2-step Agno workflow

    This implementation uses a streamlined 2-step workflow with validated outputs:
    - Step 1: Task Analysis & Resource Selection (AnalysisAndSelectionOutput schema)
    - Step 2: Full Plan Generation with Costs (TaskPlanResponse schema)

    Benefits:
    - Faster than old 4-step workflow (45-55s vs 119s)
    - Type-safe communication between agents (no text parsing)
    - Validated outputs at each step (eliminates hallucination risk)
    - Smart pre-fetching of top 20 resources (limits context window)
    - Real-time progress updates via SSE
    - Single unified workflow for all cases (no fast/slow path split)
    """
    try:
        # Yield initial progress with informative message
        yield format_sse_message(
            "progress", {"stage": "initializing", "message": "🚀 Initializing AI Task Planner - preparing to discover available agents, teams, and resources...", "progress": 10}
        )

        logger.info(
            "task_planning_stream_v2_requested",
            description=request.description[:100],
            priority=request.priority,
        )

        # Extract organization ID from token (REQUIRED for entity resolution)
        organization_id = None
        if not api_token:
            logger.error("no_api_token_provided", message="API token is required for task planning")
            yield format_sse_message("error", {
                "message": "Authentication required: No API token provided. Please configure your API token."
            })
            return

        try:
            organization_id = _extract_organization_id_from_token(api_token)
            if not organization_id:
                raise ValueError("Token does not contain organization_id")
            logger.info("extracted_organization_id", organization_id=organization_id)
        except Exception as e:
            logger.error("failed_to_extract_organization_id", error=str(e))
            yield format_sse_message("error", {
                "message": f"Authentication failed: Could not extract organization from token. Error: {str(e)}"
            })
            return

        # SIMPLIFIED: Let the planner fetch everything from DB
        # CLI no longer needs to fetch agents/teams/environments/queues
        # This centralizes data fetching in the API where it belongs
        outer_context = None
        logger.info(
            "planner_will_fetch_resources",
            message="Planner will fetch all resources from database (agents, teams, environments, queues)"
        )

        # UNIFIED WORKFLOW: Always use the 2-step workflow (fast enough for all cases)
        # quick_mode is passed as an optimization hint but same workflow is used
        logger.info(
            "using_unified_2step_workflow",
            message="Unified 2-step workflow (fast enough for all cases)",
            quick_mode=request.quick_mode,
            has_outer_context=bool(outer_context)
        )
        workflow = create_multistep_workflow(
            db=db,
            organization_id=organization_id,
            api_token=api_token,
            quick_mode=request.quick_mode,  # Passed as optimization hint
            outer_context=outer_context
        )

        # Set up event queue for streaming progress updates
        event_queue = asyncio.Queue()

        # Capture the event loop before starting background work
        loop = asyncio.get_event_loop()

        def publish_event(event_dict):
            """Publish event to the queue (thread-safe)"""
            try:
                loop.call_soon_threadsafe(event_queue.put_nowait, event_dict)
            except Exception as e:
                logger.error("failed_to_publish_event", error=str(e), event=event_dict)

        # Run workflow in executor (blocking operation)
        logger.info("running_workflow_in_executor")

        workflow_complete = False
        workflow_result = None
        workflow_error = None

        async def run_workflow_async():
            """Run the workflow in a thread pool"""
            nonlocal workflow_complete, workflow_result, workflow_error
            try:
                # Run blocking workflow in thread pool
                result = await asyncio.to_thread(
                    run_planning_workflow_stream,
                    workflow,
                    request,
                    publish_event,
                    request.quick_mode  # Pass quick_mode to skip verbose reasoning
                )
                workflow_result = result
            except Exception as e:
                logger.error("workflow_execution_failed", error=str(e), exc_info=True)
                workflow_error = e
            finally:
                workflow_complete = True

        # Start workflow task
        workflow_task = asyncio.create_task(run_workflow_async())

        # Stream events from queue as they arrive
        while not workflow_complete:
            try:
                # Try to get event from queue (with short timeout for responsive UI)
                # 0.5s provides good balance between responsiveness and CPU usage
                event = await asyncio.wait_for(event_queue.get(), timeout=0.5)

                event_type = event.get("event")
                event_data = event.get("data", {})

                # Map workflow events to UI-compatible events for backward compatibility
                if event_type == "step_started":
                    # Map to progress event with step description
                    yield format_sse_message("progress", {
                        "message": event_data.get("step_description", "Processing..."),
                        "progress": event_data.get("progress", 0)
                    })
                elif event_type == "step_completed":
                    # Map to progress event showing completion
                    yield format_sse_message("progress", {
                        "message": f"{event_data.get('step_name', 'Step')} completed",
                        "progress": event_data.get("progress", 0)
                    })
                elif event_type == "tool_call":
                    # Pass through tool_call events for elegant UI display
                    # CLI will render these with nice formatting
                    yield format_sse_message("tool_call", {
                        "tool_name": event_data.get("tool_name", "unknown"),
                        "tool_id": event_data.get("tool_id"),
                        "step": event_data.get("step"),
                        "timestamp": event_data.get("timestamp"),
                    })
                elif event_type == "tool_result":
                    # Pass through tool_result for completion feedback
                    yield format_sse_message("tool_result", {
                        "tool_name": event_data.get("tool_name", "unknown"),
                        "tool_id": event_data.get("tool_id"),
                        "status": event_data.get("status", "success"),
                        "duration": event_data.get("duration"),
                        "step": event_data.get("step"),
                    })
                elif event_type == "validation_error":
                    # Map to error event
                    yield format_sse_message("error", {
                        "message": f"Validation error: {event_data.get('error', 'Unknown error')}"
                    })
                else:
                    # Pass through other events as-is (progress, error, etc.)
                    yield format_sse_message(event_type, event_data)

                await asyncio.sleep(0)  # Flush immediately

            except asyncio.TimeoutError:
                # No event in queue, check if workflow is done
                if workflow_task.done():
                    workflow_complete = True
                    break
                # Otherwise continue waiting
                continue

        # Drain any remaining events (with same mapping)
        while not event_queue.empty():
            try:
                event = event_queue.get_nowait()
                event_type = event.get("event")
                event_data = event.get("data", {})

                # Apply same event mapping as main loop
                if event_type == "step_started":
                    yield format_sse_message("progress", {
                        "message": event_data.get("step_description", "Processing..."),
                        "progress": event_data.get("progress", 0)
                    })
                elif event_type == "step_completed":
                    yield format_sse_message("progress", {
                        "message": f"{event_data.get('step_name', 'Step')} completed",
                        "progress": event_data.get("progress", 0)
                    })
                elif event_type == "tool_call":
                    yield format_sse_message("tool_call", {
                        "tool_name": event_data.get("tool_name", "unknown"),
                        "tool_id": event_data.get("tool_id"),
                        "step": event_data.get("step"),
                        "timestamp": event_data.get("timestamp"),
                    })
                elif event_type == "tool_result":
                    yield format_sse_message("tool_result", {
                        "tool_name": event_data.get("tool_name", "unknown"),
                        "tool_id": event_data.get("tool_id"),
                        "status": event_data.get("status", "success"),
                        "duration": event_data.get("duration"),
                        "step": event_data.get("step"),
                    })
                elif event_type == "validation_error":
                    yield format_sse_message("error", {
                        "message": f"Validation error: {event_data.get('error', 'Unknown error')}"
                    })
                else:
                    yield format_sse_message(event_type, event_data)

                await asyncio.sleep(0)
            except asyncio.QueueEmpty:
                break

        # Check for workflow errors
        if workflow_error:
            logger.error("workflow_failed", error=str(workflow_error))
            yield format_sse_message("error", {"message": f"Workflow failed: {str(workflow_error)}"})
            raise workflow_error

        # Validate result
        if not workflow_result:
            error_msg = "Workflow completed but returned no result"
            logger.error("workflow_no_result")
            yield format_sse_message("error", {"message": error_msg})
            raise ValueError(error_msg)

        # Validate result (always expecting TaskPlanResponse from 2-step workflow)
        from pydantic import ValidationError
        try:
            if isinstance(workflow_result, TaskPlanResponse):
                plan = workflow_result
            elif isinstance(workflow_result, dict):
                plan = TaskPlanResponse.model_validate(workflow_result)
            else:
                raise ValueError(f"Unexpected result type: {type(workflow_result)}")
        except ValidationError as e:
            logger.error("plan_validation_failed", errors=e.errors())
            yield format_sse_message("error", {"message": f"Invalid plan structure: {str(e)}"})
            raise

        # Resolve entity names to UUIDs before sending final plan
        # This is CRITICAL - without proper UUIDs, execution will fail
        # Note: organization_id was already extracted earlier in this function (line ~268)
        if not organization_id:
            # If no organization_id, fail early with clear error
            error_msg = "Failed to resolve entity IDs: No organization context available"
            logger.error("no_organization_id_for_entity_resolution_stream")
            yield format_sse_message("error", {"message": error_msg})
            return  # Stop here - don't send incomplete plan

        await resolve_plan_entities(
            plan_response=plan,
            organization_id=organization_id,
            db=db
        )
        logger.info("plan_entities_resolved_stream", plan_title=plan.title)

        # Yield final plan event with "complete" type (CLI expects this event type)
        logger.info("workflow_completed_successfully", title=plan.title)
        yield format_sse_message(
            "complete",
            {
                "plan": plan.model_dump(),
                "progress": 100,
                "message": "✅ Plan generated successfully!"
            }
        )

    except ValueError as e:
        # Validation errors - return structured error message in stream
        error_msg = str(e)
        error_type = "validation_error" if ("validation" in error_msg.lower() or "does NOT exist" in error_msg or "does not exist" in error_msg) else "value_error"

        logger.error(f"task_planning_stream_{error_type}", error=error_msg, exc_info=True)

        yield format_sse_message(
            "error",
            {
                "error": error_type,
                "message": "The task planner generated invalid output that failed validation" if error_type == "validation_error" else "Task planning failed",
                "details": error_msg,
                "suggestion": "This usually means the AI tried to use non-existent agents/teams. Please try again or check your available resources." if error_type == "validation_error" else None
            }
        )

    except Exception as e:
        from sqlalchemy.exc import OperationalError, DisconnectionError
        from control_plane_api.app.database import dispose_engine, IS_SERVERLESS

        error_type = type(e).__name__
        logger.error("task_planning_stream_v2_error", error=str(e), error_type=error_type, exc_info=True)

        # Specific handling for database connection errors
        if isinstance(e, (OperationalError, DisconnectionError)):
            error_msg = "Database connection lost. Please try again."
            if IS_SERVERLESS:
                dispose_engine()
        else:
            error_msg = f"Task planning failed: {str(e)}"

        yield format_sse_message("error", {"message": error_msg})
    finally:
        # Cleanup database connections in serverless
        from control_plane_api.app.database import dispose_engine, IS_SERVERLESS
        if IS_SERVERLESS:
            logger.info("cleaning_up_serverless_connections")
            dispose_engine()


@router.post("/tasks/plan/stream")
async def plan_task_stream(task_request: TaskPlanRequest, http_request: Request, db: Session = Depends(get_db)):
    """
    Generate an AI-powered task plan with streaming

    Uses a single intelligent agent with tool streaming for real-time progress updates.
    Streams: tool calls → thinking → plan generation → complete

    The agent has access to context graph tools for intelligent resource discovery.
    """
    # Extract API token from Authorization header
    auth_header = http_request.headers.get("authorization", "")
    api_token = auth_header.replace("UserKey ", "").replace("Bearer ", "") if auth_header else None

    logger.info("task_planning_stream_requested")

    # Use the robust 4-step workflow implementation
    return StreamingResponse(
        generate_task_plan_stream(task_request, db, api_token),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/tasks/plan/health")
async def planning_health():
    """Health check for task planning endpoint with strategy availability info"""
    available_strategies = []

    # Check Agno availability (should always be available)
    try:
        from control_plane_api.app.services.agno_planning_strategy import AgnoPlanningStrategy
        available_strategies.append("agno")
    except ImportError:
        pass

    # Check Claude Code SDK availability
    try:
        from claude_agent_sdk import ClaudeSDKClient
        # Check if Claude CLI binary is available
        import shutil
        if shutil.which("claude"):
            available_strategies.append("claude_code_sdk")
    except ImportError:
        pass

    current_strategy = os.getenv("PLANNING_STRATEGY", "agno")
    is_healthy = current_strategy in available_strategies
    environment_type = "serverless" if (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")) else "standard"

    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": "task_planning",
        "current_strategy": current_strategy,
        "available_strategies": available_strategies,
        "environment": environment_type,
        "recommended_strategy": "agno" if environment_type == "serverless" else current_strategy,
    }
