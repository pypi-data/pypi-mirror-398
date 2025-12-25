"""
Clean streaming router using ExecutionStreamer architecture.

This module provides a clean FastAPI router for execution streaming
that replaces the monolithic ~2,100 line inline implementation with
the modular ExecutionStreamer class.

Architecture:
- Immediate connection acknowledgment (<50ms)
- Progressive historical message loading
- Live event streaming with gap recovery
- Graceful degradation when services unavailable
- Last-Event-ID resumption support

The endpoint uses ExecutionStreamer which orchestrates:
- HistoryLoader: Database message loading with Temporal fallback
- LiveEventSource: Redis event streaming with workflow state polling
- MessageDeduplicator: Deduplication across history and live phases
- EventBuffer: Gap detection and replay for reconnection
- EventFormatter: Consistent SSE formatting
- WorkerHealthChecker: Graceful degradation mode detection

Test Strategy:
- Integration test with real execution IDs
- Test all event types are emitted correctly
- Test Last-Event-ID resumption works
- Test graceful degradation modes
- Test backward compatibility with existing clients
"""

import asyncio
import uuid as uuid_module
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from control_plane_api.app.database import get_db
from control_plane_api.app.lib.redis_client import get_redis_client
from control_plane_api.app.lib.temporal_client import get_temporal_client
from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.models.execution import Execution

from .streaming import ExecutionStreamer
from .services.worker_health import WorkerHealthChecker

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/{execution_id}/stream")
async def stream_execution(
    execution_id: str,
    request: Request,
    last_event_id: Optional[str] = None,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """
    Stream execution updates using Server-Sent Events (SSE).

    This endpoint provides real-time execution updates by combining:
    1. Historical messages from database (last 200 messages)
    2. Live events from Redis (sub-second latency)
    3. Workflow state from Temporal (200ms polling)

    The endpoint supports:
    - Progressive history loading (no blocking on full history)
    - Last-Event-ID resumption for reconnection
    - Gap detection and notification
    - Graceful degradation when services unavailable
    - Backward compatible with existing clients

    Architecture:
    This endpoint uses the ExecutionStreamer class which orchestrates
    all phases of streaming:
    1. Immediate connection (<50ms)
    2. History loading (progressive, one message at a time)
    3. History completion notification
    4. Live event streaming (until workflow completes or timeout)

    Gap Recovery:
    - Supports Last-Event-ID pattern for reconnection
    - Client sends last_event_id query param or Last-Event-ID header
    - Server resumes from that point or detects gaps
    - Buffered events replayed if available
    - Client notified if gap unrecoverable

    SSE Event Types:
    - connected: Initial connection acknowledgment
    - message: Chat message (history or live)
    - message_chunk: Streaming message chunk
    - member_message_chunk: Team member message chunk
    - history_complete: All historical messages sent
    - status: Execution status update
    - tool_started: Tool execution started
    - tool_completed: Tool execution completed
    - degraded: Service degradation notification
    - recovered: Service recovery notification
    - gap_detected: Gap in event stream detected
    - error: Error occurred
    - keepalive: Connection keepalive (comment)

    SSE Format:
    - id: {execution_id}_{counter}_{timestamp_micros}
    - event: {event_type}
    - data: {json object}

    Args:
        execution_id: Execution ID to stream
        request: FastAPI request object (for headers)
        last_event_id: Last event ID received by client (for resumption)
        organization: Authenticated organization (injected by auth middleware)
        db: Database session (injected by dependency)

    Returns:
        StreamingResponse with text/event-stream content

    Raises:
        HTTPException 404: Execution not found or not authorized
        HTTPException 500: Critical initialization error
    """

    # ========== AUTHENTICATION & AUTHORIZATION ==========
    # Already handled by get_current_organization dependency
    logger.info(
        "stream_request_received",
        execution_id=execution_id[:8],
        organization_id=organization["id"][:8],
        has_last_event_id=bool(last_event_id or request.headers.get("Last-Event-ID")),
    )

    # ========== GET EXECUTION TYPE FROM DATABASE ==========
    # This determines the workflow ID format:
    # - TEAM: "team-execution-{id}"
    # - AGENT: "agent-execution-{id}" (default)
    try:
        execution_record = db.query(Execution).filter(
            Execution.id == uuid_module.UUID(execution_id),
            Execution.organization_id == organization["id"]
        ).first()

        if not execution_record:
            raise HTTPException(
                status_code=404,
                detail=f"Execution {execution_id} not found or not authorized"
            )

        execution_type = execution_record.execution_type or "AGENT"

        logger.info(
            "execution_type_determined",
            execution_id=execution_id[:8],
            execution_type=execution_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "failed_to_query_execution",
            execution_id=execution_id[:8],
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query execution: {str(e)}"
        )

    # ========== INITIALIZE INFRASTRUCTURE CLIENTS ==========
    # Get clients with graceful degradation support
    # - Temporal client: 2s timeout to fail fast when worker down
    # - Redis client: Can be None if not configured
    # - Database session: Already available from dependency

    # Redis client (optional, graceful degradation if None)
    redis_client = get_redis_client()
    if not redis_client:
        logger.warning(
            "redis_not_configured",
            execution_id=execution_id[:8],
            note="Live streaming will be unavailable"
        )

    # Temporal client with fast timeout (optional, graceful degradation)
    temporal_client = None
    try:
        temporal_client = await asyncio.wait_for(
            get_temporal_client(),
            timeout=2.0  # Fail fast - don't block streaming
        )
        logger.info(
            "temporal_client_connected",
            execution_id=execution_id[:8],
        )
    except asyncio.TimeoutError:
        logger.warning(
            "temporal_connection_timeout",
            execution_id=execution_id[:8],
            timeout_seconds=2.0,
            note="Workflow queries will be unavailable"
        )
    except Exception as temporal_error:
        logger.warning(
            "temporal_connection_failed",
            execution_id=execution_id[:8],
            error=str(temporal_error),
            error_type=type(temporal_error).__name__,
            note="Continuing without Temporal support"
        )

    # ========== PARSE LAST-EVENT-ID ==========
    # Check both query param and header (EventSource sets header automatically)
    parsed_last_event_id = last_event_id or request.headers.get("Last-Event-ID")

    if parsed_last_event_id:
        logger.info(
            "resumption_requested",
            execution_id=execution_id[:8],
            last_event_id=parsed_last_event_id,
        )

    # ========== CREATE WORKER HEALTH CHECKER ==========
    # This determines degradation mode based on service availability
    health_checker = WorkerHealthChecker(
        temporal_client=temporal_client,
        redis_client=redis_client,
        db_session=db,
    )

    # ========== INSTANTIATE EXECUTION STREAMER ==========
    # This orchestrates all phases of streaming:
    # 1. Immediate connection
    # 2. Resumption (if Last-Event-ID provided)
    # 3. Historical message loading
    # 4. History completion notification
    # 5. Live event streaming
    try:
        streamer = ExecutionStreamer(
            execution_id=execution_id,
            organization_id=organization["id"],
            db_session=db,
            redis_client=redis_client,
            temporal_client=temporal_client,
            last_event_id=parsed_last_event_id,
            timeout_seconds=0,  # 0 = no timeout, stream until task completes
            execution_type=execution_type,
            health_checker=health_checker,
        )

        logger.info(
            "streamer_initialized",
            execution_id=execution_id[:8],
            execution_type=execution_type,
            has_redis=bool(redis_client),
            has_temporal=bool(temporal_client),
            has_last_event_id=bool(parsed_last_event_id),
        )

    except Exception as e:
        logger.error(
            "failed_to_initialize_streamer",
            execution_id=execution_id[:8],
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize streaming: {str(e)}"
        )

    # ========== RETURN STREAMING RESPONSE ==========
    # StreamingResponse will call streamer.stream() which yields SSE events
    return StreamingResponse(
        streamer.stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for real-time
        }
    )
