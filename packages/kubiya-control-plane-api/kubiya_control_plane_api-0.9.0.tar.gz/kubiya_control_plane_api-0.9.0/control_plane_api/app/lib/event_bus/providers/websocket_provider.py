"""WebSocket-based event bus provider."""

from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone
import asyncio
import websockets
import json
import structlog
from pydantic import Field

from control_plane_api.app.lib.event_bus.base import EventBusProvider, EventBusConfig

logger = structlog.get_logger(__name__)


class WebSocketConfig(EventBusConfig):
    """Configuration for WebSocket event provider."""

    websocket_url: str = Field(..., description="WebSocket URL to connect to")
    worker_id: str = Field(..., description="Worker ID for identification")
    api_key: Optional[str] = Field(
        default=None, description="API key for authentication"
    )
    queue_size: int = Field(
        default=10000, description="Maximum event queue size"
    )
    connection_renewal_interval: int = Field(
        default=3600, description="Seconds between connection renewals"
    )
    reconnect_backoff_max: int = Field(
        default=60, description="Maximum reconnection backoff in seconds"
    )
    ping_interval: int = Field(
        default=20, description="WebSocket ping interval in seconds"
    )
    ping_timeout: int = Field(
        default=10, description="WebSocket ping timeout in seconds"
    )
    heartbeat_interval: int = Field(
        default=30, description="Heartbeat send interval in seconds"
    )


class WebSocketEventProvider(EventBusProvider):
    """WebSocket-based event publishing with persistent connection."""

    def __init__(self, config: WebSocketConfig):
        super().__init__(config)
        self.config: WebSocketConfig = config

        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.reconnect_attempts = 0
        self.connection_start_time: Optional[float] = None
        self.last_ping_time: Optional[float] = None
        self.last_pong_time: Optional[float] = None

        # Event queue for disconnection periods
        self.event_queue: asyncio.Queue = asyncio.Queue(
            maxsize=config.queue_size
        )

        # Background tasks
        self._connect_task: Optional[asyncio.Task] = None
        self._send_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False

        # Optional control message callback
        self._on_control_message: Optional[Callable] = None

    async def initialize(self) -> None:
        """Initialize WebSocket connection and background tasks."""
        if self._running:
            self.logger.warning(
                "websocket_provider_already_running",
                worker_id=self.config.worker_id[:8]
            )
            return

        self._running = True
        self._connect_task = asyncio.create_task(self._connect_loop())
        self._send_task = asyncio.create_task(self._send_loop())
        self._receive_task = asyncio.create_task(self._receive_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        self.logger.info(
            "websocket_provider_initialized",
            worker_id=self.config.worker_id[:8],
            url=self.config.websocket_url,
            queue_size=self.config.queue_size,
        )

    async def publish_event(
        self,
        execution_id: str,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Queue event for sending via WebSocket (non-blocking).

        Args:
            execution_id: Execution ID
            event_type: Event type (message_chunk, tool_started, etc.)
            data: Event payload
            metadata: Optional metadata

        Returns:
            True if queued successfully, False if queue is full
        """
        event = {
            "message_type": "event",
            "worker_id": self.config.worker_id,
            "execution_id": execution_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Add metadata if provided
        if metadata:
            event["metadata"] = metadata

        try:
            self.event_queue.put_nowait(event)

            # Log warning if queue is getting full (70% capacity)
            queue_size = self.event_queue.qsize()
            if queue_size > (self.config.queue_size * 0.7):
                self.logger.warning(
                    "websocket_event_queue_high_capacity",
                    worker_id=self.config.worker_id[:8],
                    queue_size=queue_size,
                    capacity_percent=int((queue_size / self.config.queue_size) * 100),
                )

            return True

        except asyncio.QueueFull:
            self.logger.warning(
                "websocket_event_queue_full",
                worker_id=self.config.worker_id[:8],
                execution_id=execution_id,
                event_type=event_type,
            )
            return False

    async def subscribe(
        self, pattern: str, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to control messages from control plane.

        Args:
            pattern: Not used for WebSocket (receives all control messages)
            callback: Callback function for control messages
        """
        self._on_control_message = callback
        self.logger.info(
            "websocket_control_message_callback_registered",
            worker_id=self.config.worker_id[:8],
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check WebSocket provider health.

        Returns:
            Dict with health status and connection info
        """
        current_time = asyncio.get_event_loop().time()

        health = {
            "healthy": self.connected,
            "websocket_url": self.config.websocket_url,
            "connected": self.connected,
            "queue_size": self.event_queue.qsize(),
            "queue_capacity": self.config.queue_size,
            "reconnect_attempts": self.reconnect_attempts,
        }

        if self.connection_start_time:
            connection_age = current_time - self.connection_start_time
            health["connection_age_seconds"] = int(connection_age)

        if self.last_pong_time:
            time_since_pong = current_time - self.last_pong_time
            health["seconds_since_last_pong"] = int(time_since_pong)
            health["pong_healthy"] = time_since_pong < 60

        return health

    async def shutdown(self) -> None:
        """Shutdown WebSocket provider and cleanup resources."""
        self._running = False

        # Cancel background tasks
        tasks = [
            self._connect_task,
            self._send_task,
            self._receive_task,
            self._heartbeat_task,
            self._health_check_task,
        ]

        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close connection
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                self.logger.warning(
                    "websocket_close_error",
                    error=str(e),
                    worker_id=self.config.worker_id[:8],
                )

        self.logger.info(
            "websocket_provider_shutdown",
            worker_id=self.config.worker_id[:8]
        )

    # --- Internal Implementation ---

    async def _connect_loop(self):
        """Maintain connection with auto-reconnection and exponential backoff."""
        while self._running:
            if not self.connected:
                try:
                    # Exponential backoff: 2s, 4s, 8s, 16s, 32s, 60s (max)
                    backoff = min(
                        2 ** self.reconnect_attempts,
                        self.config.reconnect_backoff_max
                    )

                    if self.reconnect_attempts > 0:
                        self.logger.info(
                            "websocket_reconnecting",
                            worker_id=self.config.worker_id[:8],
                            attempt=self.reconnect_attempts,
                            backoff_seconds=backoff,
                        )
                        await asyncio.sleep(backoff)

                    # Log connection attempt
                    self.logger.info(
                        "websocket_connecting",
                        worker_id=self.config.worker_id[:8],
                        url=self.config.websocket_url,
                    )

                    # Connect with authentication header and ping settings
                    headers = {}
                    if self.config.api_key:
                        headers["Authorization"] = f"Bearer {self.config.api_key}"

                    self.websocket = await websockets.connect(
                        self.config.websocket_url,
                        additional_headers=headers,
                        ping_interval=self.config.ping_interval,
                        ping_timeout=self.config.ping_timeout,
                    )

                    self.connected = True
                    self.reconnect_attempts = 0
                    self.connection_start_time = asyncio.get_event_loop().time()
                    self.last_ping_time = self.connection_start_time
                    self.last_pong_time = self.connection_start_time

                    self.logger.info(
                        "websocket_connected",
                        worker_id=self.config.worker_id[:8],
                        url=self.config.websocket_url,
                    )

                except Exception as e:
                    self.reconnect_attempts += 1
                    self.logger.warning(
                        "websocket_connect_failed",
                        error=str(e),
                        worker_id=self.config.worker_id[:8],
                        attempts=self.reconnect_attempts,
                    )

            await asyncio.sleep(1)

    async def _send_loop(self):
        """Send queued events to control plane."""
        while self._running:
            try:
                # Wait for connection
                if not self.connected:
                    await asyncio.sleep(0.1)
                    continue

                # Get event from queue (timeout to check connection periodically)
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Send event
                await self.websocket.send(json.dumps(event))

            except websockets.exceptions.ConnectionClosed:
                self.connected = False
                # Re-queue the event (put back)
                try:
                    await self.event_queue.put(event)
                except Exception:
                    self.logger.warning(
                        "websocket_failed_to_requeue_event",
                        worker_id=self.config.worker_id[:8],
                    )

            except Exception as e:
                self.logger.warning(
                    "websocket_send_error",
                    error=str(e),
                    worker_id=self.config.worker_id[:8],
                )

    async def _receive_loop(self):
        """Receive and handle messages from control plane."""
        while self._running:
            try:
                # Wait for connection
                if not self.connected:
                    await asyncio.sleep(0.1)
                    continue

                # Receive message
                message_str = await self.websocket.recv()
                message = json.loads(message_str)

                message_type = message.get("message_type")

                if message_type == "control":
                    # Handle control message
                    await self._handle_control_message(message)

                elif message_type == "pong":
                    # Heartbeat acknowledgment - update last pong time
                    self.last_pong_time = asyncio.get_event_loop().time()

                elif message_type == "ping":
                    # Respond to server ping
                    await self.websocket.send(
                        json.dumps({
                            "message_type": "pong",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    )

                elif message_type == "connected":
                    # Connection acknowledgment
                    self.logger.info(
                        "websocket_handshake_complete",
                        worker_id=self.config.worker_id[:8],
                        features=message.get("features", []),
                    )

            except websockets.exceptions.ConnectionClosed:
                self.connected = False
                self.logger.info(
                    "websocket_connection_closed",
                    worker_id=self.config.worker_id[:8]
                )

            except json.JSONDecodeError as e:
                self.logger.warning(
                    "websocket_invalid_json",
                    error=str(e),
                    worker_id=self.config.worker_id[:8],
                )

            except Exception as e:
                self.logger.warning(
                    "websocket_receive_error",
                    error=str(e),
                    worker_id=self.config.worker_id[:8],
                )

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to maintain connection."""
        while self._running:
            await asyncio.sleep(self.config.heartbeat_interval)

            if self.connected:
                try:
                    await self.websocket.send(
                        json.dumps({
                            "message_type": "heartbeat",
                            "worker_id": self.config.worker_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    )
                    self.last_ping_time = asyncio.get_event_loop().time()
                except Exception as e:
                    self.logger.warning(
                        "websocket_heartbeat_send_failed",
                        error=str(e),
                        worker_id=self.config.worker_id[:8],
                    )
                    self.connected = False

    async def _health_check_loop(self):
        """
        Monitor connection health and trigger reconnection if needed.

        Checks for:
        1. Stale connections (no pong received in 60 seconds)
        2. Connection renewal (connection age exceeds renewal interval)
        """
        while self._running:
            await asyncio.sleep(10)  # Check every 10 seconds

            if self.connected and self.connection_start_time:
                current_time = asyncio.get_event_loop().time()

                # Check for stale connection (no pong in 60 seconds)
                if self.last_pong_time and (current_time - self.last_pong_time) > 60:
                    self.logger.warning(
                        "websocket_stale_connection_detected",
                        worker_id=self.config.worker_id[:8],
                        seconds_since_pong=int(current_time - self.last_pong_time),
                    )
                    # Force reconnection
                    self.connected = False
                    if self.websocket:
                        try:
                            await self.websocket.close()
                        except Exception:
                            pass
                    continue

                # Check if connection needs renewal
                connection_age = current_time - self.connection_start_time
                if connection_age > self.config.connection_renewal_interval:
                    self.logger.info(
                        "websocket_connection_renewal",
                        worker_id=self.config.worker_id[:8],
                        connection_age_seconds=int(connection_age),
                        renewal_interval=self.config.connection_renewal_interval,
                    )
                    # Gracefully close and reconnect
                    self.connected = False
                    if self.websocket:
                        try:
                            await self.websocket.close()
                        except Exception:
                            pass

    async def _handle_control_message(self, message: Dict[str, Any]):
        """
        Handle control message from control plane.

        Args:
            message: Control message with command, execution_id, and data
        """
        try:
            command = message.get("command")
            execution_id = message.get("execution_id")

            self.logger.info(
                "websocket_control_message_received",
                command=command,
                execution_id=execution_id[:8] if execution_id else None,
                worker_id=self.config.worker_id[:8],
            )

            # Call registered handler if set
            if self._on_control_message:
                result = self._on_control_message(message)
                if asyncio.iscoroutine(result):
                    await result

        except Exception as e:
            self.logger.error(
                "websocket_control_message_handler_error",
                error=str(e),
                worker_id=self.config.worker_id[:8],
            )
