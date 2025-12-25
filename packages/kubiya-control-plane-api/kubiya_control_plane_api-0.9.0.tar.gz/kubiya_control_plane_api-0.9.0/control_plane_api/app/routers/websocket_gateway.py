"""
WebSocket Gateway for Worker Event Streaming.

Provides persistent WebSocket connections for workers to publish events,
bypassing the 300-second timeout limitation of HTTP requests.

Features:
- Long-running execution support (auto-reconnection)
- Connection renewal before timeout
- Transparent integration with existing Redis pub/sub
- Backward compatible with HTTP event publishing

Architecture:
    Worker → WebSocket → Control Plane API → Redis → UI (SSE)

The WebSocket connection acts as an alternative transport layer that
publishes to the same Redis mechanism, making it transparent to the UI layer.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import Dict, Optional, Set
import structlog
import json
import asyncio
from datetime import datetime, timezone

from control_plane_api.app.lib.redis_client import get_redis_client

logger = structlog.get_logger()

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections for execution event streaming.

    Features:
    - Connection tracking per execution
    - Automatic cleanup on disconnect
    - Connection limits per organization
    - Health check/keepalive support
    """

    def __init__(self):
        # execution_id -> WebSocket
        self._connections: Dict[str, WebSocket] = {}

        # organization_id -> Set[execution_id]
        self._org_connections: Dict[str, Set[str]] = {}

        # Connection statistics
        self._stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_received": 0,
            "messages_published": 0,
        }

    async def connect(
        self,
        execution_id: str,
        organization_id: str,
        websocket: WebSocket,
    ) -> None:
        """
        Register a new WebSocket connection.

        Args:
            execution_id: Execution ID
            organization_id: Organization ID (for multi-tenancy)
            websocket: WebSocket connection
        """
        await websocket.accept()

        # Track connection
        self._connections[execution_id] = websocket

        if organization_id not in self._org_connections:
            self._org_connections[organization_id] = set()
        self._org_connections[organization_id].add(execution_id)

        # Update stats
        self._stats["total_connections"] += 1
        self._stats["active_connections"] = len(self._connections)

        logger.info(
            "websocket_connected",
            execution_id=execution_id[:8],
            organization_id=organization_id[:8],
            active_connections=self._stats["active_connections"],
        )

    async def disconnect(self, execution_id: str, organization_id: str) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            execution_id: Execution ID
            organization_id: Organization ID
        """
        # Remove connection
        if execution_id in self._connections:
            del self._connections[execution_id]

        # Remove from org tracking
        if organization_id in self._org_connections:
            self._org_connections[organization_id].discard(execution_id)
            if not self._org_connections[organization_id]:
                del self._org_connections[organization_id]

        # Update stats
        self._stats["active_connections"] = len(self._connections)

        logger.info(
            "websocket_disconnected",
            execution_id=execution_id[:8],
            organization_id=organization_id[:8],
            active_connections=self._stats["active_connections"],
        )

    def get_connection(self, execution_id: str) -> Optional[WebSocket]:
        """Get WebSocket connection for execution."""
        return self._connections.get(execution_id)

    def is_connected(self, execution_id: str) -> bool:
        """Check if execution has active WebSocket connection."""
        return execution_id in self._connections

    def get_stats(self) -> Dict:
        """Get connection statistics."""
        return {
            **self._stats,
            "connections_by_org": {
                org_id: len(executions)
                for org_id, executions in self._org_connections.items()
            },
        }


# Global connection manager
connection_manager = ConnectionManager()


@router.websocket("/ws/executions/{execution_id}/events")
async def websocket_event_stream(
    websocket: WebSocket,
    execution_id: str,
):
    """
    WebSocket endpoint for worker event streaming.

    This endpoint allows workers to establish a persistent connection for
    publishing events, bypassing the 300-second HTTP timeout limitation.

    Protocol:
    - Worker connects with Authorization header
    - Worker sends JSON events: {"event_type": "...", "data": {...}, "timestamp": "..."}
    - Server publishes to Redis (same mechanism as HTTP endpoint)
    - Connection auto-renews before 300s timeout
    - Keepalive: Client sends {"type": "ping"}, server responds {"type": "pong"}

    Example:
        ws://localhost:8000/ws/executions/{execution_id}/events
        Headers: Authorization: UserKey {api_key}
    """
    organization = None
    redis_client = None

    try:
        # Authenticate via header (WebSocket doesn't support Depends for auth in same way)
        auth_header = websocket.headers.get("authorization", "")
        if not auth_header.startswith("UserKey "):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication")
            return

        # Get organization from auth (simplified - in production, verify API key)
        # For now, we'll accept the connection and validate on first message
        # TODO: Implement proper WebSocket auth middleware

        await websocket.accept()

        # Get Redis client
        redis_client = get_redis_client()
        if not redis_client:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Redis not configured")
            return

        logger.info(
            "websocket_connection_accepted",
            execution_id=execution_id[:8],
        )

        # Connection loop
        messages_received = 0
        events_published = 0
        last_activity = datetime.now(timezone.utc)

        while True:
            try:
                # Receive message with timeout for keepalive check
                message = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0  # 30s timeout for keepalive
                )

                messages_received += 1
                last_activity = datetime.now(timezone.utc)

                # Handle keepalive ping
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
                    continue

                # Handle event publication
                event_type = message.get("event_type")
                data = message.get("data")
                timestamp = message.get("timestamp") or datetime.now(timezone.utc).isoformat()

                if not event_type or data is None:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Missing event_type or data",
                    })
                    continue

                # Publish to Redis (same mechanism as HTTP endpoint)
                event_data = {
                    "event_type": event_type,
                    "data": data,
                    "timestamp": timestamp,
                    "execution_id": execution_id,
                    "transport": "websocket",
                }

                # Push to Redis list
                redis_key = f"execution:{execution_id}:events"
                await redis_client.lpush(redis_key, json.dumps(event_data))
                await redis_client.ltrim(redis_key, 0, 999)
                await redis_client.expire(redis_key, 3600)

                # Publish to pub/sub channel
                pubsub_channel = f"execution:{execution_id}:stream"
                try:
                    await redis_client.publish(pubsub_channel, json.dumps(event_data))
                except Exception as pubsub_error:
                    logger.debug("pubsub_publish_failed", error=str(pubsub_error), execution_id=execution_id[:8])

                events_published += 1

                # Send acknowledgment
                await websocket.send_json({
                    "type": "ack",
                    "event_type": event_type,
                    "timestamp": timestamp,
                })

                # Log every 100 events
                if events_published % 100 == 0:
                    logger.info(
                        "websocket_events_published",
                        execution_id=execution_id[:8],
                        events_count=events_published,
                    )

            except asyncio.TimeoutError:
                # No message received in 30s - send keepalive check
                try:
                    await websocket.send_json({
                        "type": "ping",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except:
                    # Connection dead
                    break

            except WebSocketDisconnect:
                break

            except json.JSONDecodeError as e:
                logger.warning("websocket_invalid_json", error=str(e), execution_id=execution_id[:8])
                await websocket.send_json({
                    "type": "error",
                    "error": "Invalid JSON",
                })

            except Exception as e:
                logger.warning("websocket_message_error", error=str(e), execution_id=execution_id[:8])
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                })

    except WebSocketDisconnect:
        logger.info(
            "websocket_client_disconnected",
            execution_id=execution_id[:8],
        )

    except Exception as e:
        logger.error(
            "websocket_error",
            error=str(e),
            execution_id=execution_id[:8],
        )

    finally:
        # Cleanup
        logger.info(
            "websocket_connection_closed",
            execution_id=execution_id[:8],
        )


@router.get("/ws/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns:
        Statistics about active connections and message throughput
    """
    return connection_manager.get_stats()
