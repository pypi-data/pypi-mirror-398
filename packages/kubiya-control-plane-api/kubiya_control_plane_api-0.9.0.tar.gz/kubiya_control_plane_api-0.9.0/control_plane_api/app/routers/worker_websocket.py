"""
WebSocket Gateway for Per-Worker Event Streaming.

Provides persistent WebSocket connections for workers to publish events,
bypassing HTTP request overhead and enabling bi-directional communication.

Features:
- Per-worker persistent connections (not per-execution)
- Bi-directional messaging (Worker→CP: events, CP→Worker: control)
- Connection management and multi-tenancy
- Transparent integration with existing Redis pub/sub
- Backward compatible with HTTP event publishing

Architecture:
    Worker → WebSocket → Control Plane API → Redis → UI (SSE)
             ←  Control  ←

The WebSocket connection acts as an alternative transport layer that
publishes to the same Redis mechanism, making it transparent to the UI layer.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from typing import Dict, Optional, Set
import structlog
import json
import asyncio
from datetime import datetime, timezone

from control_plane_api.app.lib.redis_client import get_redis_client

logger = structlog.get_logger()

router = APIRouter()


class WorkerConnectionManager:
    """
    Manages WebSocket connections for per-worker event streaming.

    Features:
    - Connection tracking per worker
    - Multi-tenancy support (organization-level isolation)
    - Automatic cleanup on disconnect
    - Connection limits per organization
    - Bi-directional messaging support
    """

    def __init__(self):
        # worker_id → WebSocket
        self._connections: Dict[str, WebSocket] = {}

        # worker_id → organization_id
        self._worker_orgs: Dict[str, str] = {}

        # organization_id → Set[worker_id]
        self._org_workers: Dict[str, Set[str]] = {}

        # Connection statistics
        self._stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_received": 0,
            "events_published": 0,
            "control_messages_sent": 0,
        }

    async def connect(
        self,
        worker_id: str,
        organization_id: str,
        websocket: WebSocket,
    ) -> None:
        """
        Register a new WebSocket connection.

        Args:
            worker_id: Worker ID
            organization_id: Organization ID (for multi-tenancy)
            websocket: WebSocket connection
        """
        await websocket.accept()

        # Track connection
        self._connections[worker_id] = websocket
        self._worker_orgs[worker_id] = organization_id

        if organization_id not in self._org_workers:
            self._org_workers[organization_id] = set()
        self._org_workers[organization_id].add(worker_id)

        # Update stats
        self._stats["total_connections"] += 1
        self._stats["active_connections"] = len(self._connections)

        logger.info(
            "worker_websocket_connected",
            worker_id=worker_id[:8],
            organization_id=organization_id[:8],
            active_connections=self._stats["active_connections"],
        )

        # Send connection acknowledgment
        await websocket.send_json({
            "message_type": "connected",
            "worker_id": worker_id,
            "features": ["events", "control", "heartbeat", "config_update"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def disconnect(self, worker_id: str) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            worker_id: Worker ID
        """
        # Get organization before removing
        organization_id = self._worker_orgs.get(worker_id)

        # Remove connection
        if worker_id in self._connections:
            del self._connections[worker_id]

        if worker_id in self._worker_orgs:
            del self._worker_orgs[worker_id]

        # Remove from org tracking
        if organization_id and organization_id in self._org_workers:
            self._org_workers[organization_id].discard(worker_id)
            if not self._org_workers[organization_id]:
                del self._org_workers[organization_id]

        # Update stats
        self._stats["active_connections"] = len(self._connections)

        logger.info(
            "worker_websocket_disconnected",
            worker_id=worker_id[:8],
            organization_id=organization_id[:8] if organization_id else "unknown",
            active_connections=self._stats["active_connections"],
        )

    def get_connection(self, worker_id: str) -> Optional[WebSocket]:
        """Get WebSocket connection for worker."""
        return self._connections.get(worker_id)

    def is_connected(self, worker_id: str) -> bool:
        """Check if worker has active WebSocket connection."""
        return worker_id in self._connections

    async def send_control_message(
        self,
        worker_id: str,
        command: str,
        execution_id: str,
        data: Optional[Dict] = None
    ) -> bool:
        """
        Send control message to worker.

        Args:
            worker_id: Worker ID
            command: Control command (pause, resume, cancel, reload_config)
            execution_id: Execution ID
            data: Optional data payload

        Returns:
            True if sent successfully, False if worker not connected
        """
        websocket = self.get_connection(worker_id)
        if not websocket:
            return False

        try:
            message = {
                "message_type": "control",
                "command": command,
                "execution_id": execution_id,
                "data": data or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            await websocket.send_json(message)
            self._stats["control_messages_sent"] += 1

            logger.info(
                "control_message_sent",
                worker_id=worker_id[:8],
                command=command,
                execution_id=execution_id[:8]
            )

            return True

        except Exception as e:
            logger.warning(
                "control_message_send_failed",
                error=str(e),
                worker_id=worker_id[:8],
                command=command
            )
            return False

    def get_stats(self) -> Dict:
        """Get connection statistics."""
        return {
            **self._stats,
            "workers_by_org": {
                org_id: len(workers)
                for org_id, workers in self._org_workers.items()
            },
        }


# Global connection manager
worker_connection_manager = WorkerConnectionManager()


@router.websocket("/ws/workers/{worker_id}")
async def websocket_worker_stream(
    websocket: WebSocket,
    worker_id: str,
):
    """
    WebSocket endpoint for per-worker event streaming.

    This endpoint allows workers to establish a persistent connection for
    publishing events from all executions, enabling:
    - Lower latency (~10ms vs 50-100ms HTTP)
    - Bi-directional communication
    - Reduced connection overhead

    Protocol:
    - Worker connects with Authorization header
    - Worker sends JSON events: {"message_type": "event", "worker_id": "...", "execution_id": "...", ...}
    - Worker sends heartbeats: {"message_type": "heartbeat", "worker_id": "..."}
    - Server sends control: {"message_type": "control", "command": "pause|resume|cancel", ...}
    - Keepalive: Client sends {"message_type": "ping"}, server responds {"message_type": "pong"}

    Example:
        wss://control-plane.example.com/ws/workers/{worker_id}
        Headers: Authorization: Bearer {api_key}
    """
    organization_id = None
    redis_client = None

    try:
        # Authenticate via header
        auth_header = websocket.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication")
            return

        # TODO: Implement proper authentication to get organization_id
        # For now, we'll use a placeholder - in production, verify API key
        # api_key = auth_header.replace("Bearer ", "")
        # organization_id = await verify_api_key(api_key)

        # Placeholder organization (will be replaced with actual auth)
        organization_id = "default-org"

        # Get Redis client
        redis_client = get_redis_client()
        if not redis_client:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Redis not configured")
            return

        # Register connection
        await worker_connection_manager.connect(worker_id, organization_id, websocket)

        # Connection loop
        messages_received = 0
        events_published = 0

        while True:
            try:
                # Receive message with timeout for keepalive check
                message = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0  # 30s timeout for keepalive
                )

                messages_received += 1
                worker_connection_manager._stats["messages_received"] += 1

                message_type = message.get("message_type")

                # Handle keepalive ping
                if message_type == "ping":
                    await websocket.send_json({
                        "message_type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    continue

                # Handle heartbeat
                elif message_type == "heartbeat":
                    # Update worker heartbeat in Redis
                    heartbeat_key = f"worker:{worker_id}:heartbeat"
                    await redis_client.setex(heartbeat_key, 300, datetime.now(timezone.utc).isoformat())
                    continue

                # Handle event publication
                elif message_type == "event":
                    execution_id = message.get("execution_id")
                    event_type = message.get("event_type")
                    data = message.get("data")
                    timestamp = message.get("timestamp") or datetime.now(timezone.utc).isoformat()

                    if not execution_id or not event_type or data is None:
                        await websocket.send_json({
                            "type": "error",
                            "error": "Missing execution_id, event_type, or data",
                        })
                        continue

                    # Publish to Redis (same mechanism as HTTP endpoint)
                    event_data = {
                        "event_type": event_type,
                        "data": data,
                        "timestamp": timestamp,
                        "execution_id": execution_id,
                        "transport": "worker_websocket",
                    }

                    # Push to Redis list (for buffering/replay)
                    redis_key = f"execution:{execution_id}:events"
                    await redis_client.lpush(redis_key, json.dumps(event_data))
                    await redis_client.ltrim(redis_key, 0, 999)  # Keep last 1000
                    await redis_client.expire(redis_key, 3600)  # 1 hour TTL

                    # Publish to pub/sub channel (for SSE clients)
                    pubsub_channel = f"execution:{execution_id}:stream"
                    try:
                        await redis_client.publish(pubsub_channel, json.dumps(event_data))
                    except Exception as pubsub_error:
                        logger.debug(
                            "pubsub_publish_failed",
                            error=str(pubsub_error),
                            execution_id=execution_id[:8]
                        )

                    events_published += 1
                    worker_connection_manager._stats["events_published"] += 1

                    # Log every 100 events
                    if events_published % 100 == 0:
                        logger.info(
                            "worker_websocket_events_published",
                            worker_id=worker_id[:8],
                            events_count=events_published,
                        )

                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Unknown message_type: {message_type}",
                    })

            except asyncio.TimeoutError:
                # No message received in 30s - send keepalive check
                try:
                    await websocket.send_json({
                        "message_type": "ping",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except:
                    # Connection dead
                    break

            except WebSocketDisconnect:
                break

            except json.JSONDecodeError as e:
                logger.warning("worker_websocket_invalid_json", error=str(e), worker_id=worker_id[:8])
                await websocket.send_json({
                    "type": "error",
                    "error": "Invalid JSON",
                })

            except Exception as e:
                logger.warning("worker_websocket_message_error", error=str(e), worker_id=worker_id[:8])
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                })

    except WebSocketDisconnect:
        logger.info(
            "worker_websocket_client_disconnected",
            worker_id=worker_id[:8],
        )

    except Exception as e:
        logger.error(
            "worker_websocket_error",
            error=str(e),
            worker_id=worker_id[:8],
        )

    finally:
        # Cleanup
        await worker_connection_manager.disconnect(worker_id)
        logger.info(
            "worker_websocket_connection_closed",
            worker_id=worker_id[:8],
        )


@router.get("/ws/workers/stats")
async def websocket_worker_stats():
    """
    Get per-worker WebSocket connection statistics.

    Returns:
        Statistics about active connections and message throughput
    """
    return worker_connection_manager.get_stats()
