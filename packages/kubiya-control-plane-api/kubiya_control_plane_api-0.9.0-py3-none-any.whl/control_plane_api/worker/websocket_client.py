"""
WebSocket client for worker-to-control-plane communication.

Provides a persistent WebSocket connection with features:
- Auto-reconnection with exponential backoff
- Event queue for disconnection periods (10k max)
- Bi-directional messaging (events out, control messages in)
- Heartbeat management
- Graceful connection handling

Usage:
    client = WorkerWebSocketClient(
        worker_id="worker-123",
        websocket_url="wss://control-plane.example.com/ws/workers/worker-123",
        api_key="api-key-123",
        on_control_message=handle_control_message
    )

    await client.start()
    await client.send_event(execution_id, "message_chunk", {"content": "..."})
    await client.stop()
"""

import asyncio
import websockets
import json
from datetime import datetime, timezone
from typing import Optional, Callable, Dict, Any
import structlog

logger = structlog.get_logger()


class WorkerWebSocketClient:
    """
    Persistent WebSocket client for worker-to-control-plane communication.

    Features:
    - Auto-reconnection with exponential backoff
    - Event queue for disconnection periods (10k max)
    - Control message handling
    - Heartbeat management
    """

    def __init__(
        self,
        worker_id: str,
        websocket_url: str,
        api_key: str,
        on_control_message: Callable[[Dict[str, Any]], None],
        connection_renewal_interval: int = 3600  # Renew connection every hour
    ):
        """
        Initialize WebSocket client.

        Args:
            worker_id: Worker ID for identification
            websocket_url: WebSocket URL to connect to
            api_key: API key for authentication
            on_control_message: Callback for control messages from control plane
            connection_renewal_interval: Seconds between connection renewals (default: 3600 = 1 hour)
        """
        self.worker_id = worker_id
        self.websocket_url = websocket_url
        self.api_key = api_key
        self.on_control_message = on_control_message
        self.connection_renewal_interval = connection_renewal_interval

        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.reconnect_attempts = 0
        self.connection_start_time: Optional[float] = None
        self.last_ping_time: Optional[float] = None
        self.last_pong_time: Optional[float] = None

        # Event queue for disconnection periods
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)

        # Background tasks
        self._connect_task: Optional[asyncio.Task] = None
        self._send_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the WebSocket client background tasks."""
        if self._running:
            logger.warning("websocket_already_running", worker_id=self.worker_id[:8])
            return

        self._running = True
        self._connect_task = asyncio.create_task(self._connect_loop())
        self._send_task = asyncio.create_task(self._send_loop())
        self._receive_task = asyncio.create_task(self._receive_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info("websocket_client_started", worker_id=self.worker_id[:8])

    async def stop(self):
        """Stop the WebSocket client and cleanup resources."""
        self._running = False

        # Cancel background tasks
        for task in [self._connect_task, self._send_task, self._receive_task, self._heartbeat_task, self._health_check_task]:
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
            except:
                pass

        logger.info("websocket_client_stopped", worker_id=self.worker_id[:8])

    async def send_event(self, execution_id: str, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Queue event for sending (non-blocking).

        Args:
            execution_id: Execution ID
            event_type: Event type (message_chunk, tool_started, etc.)
            data: Event payload

        Returns:
            True if queued successfully, False if queue is full
        """
        event = {
            "message_type": "event",
            "worker_id": self.worker_id,
            "execution_id": execution_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            self.event_queue.put_nowait(event)

            # Log warning if queue is getting full (70% capacity)
            queue_size = self.event_queue.qsize()
            if queue_size > 7000:
                logger.warning(
                    "event_queue_high_capacity",
                    worker_id=self.worker_id[:8],
                    queue_size=queue_size,
                    capacity_percent=int(queue_size / 100)
                )

            return True
        except asyncio.QueueFull:
            logger.warning("event_queue_full", worker_id=self.worker_id[:8])
            return False

    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected."""
        return self.connected and self.websocket is not None

    async def _connect_loop(self):
        """Maintain connection with auto-reconnection and exponential backoff."""
        while self._running:
            if not self.connected:
                try:
                    # Exponential backoff: 2s, 4s, 8s, 16s, 32s, 60s (max)
                    backoff = min(2 ** self.reconnect_attempts, 60)

                    if self.reconnect_attempts > 0:
                        logger.info(
                            "websocket_reconnecting",
                            worker_id=self.worker_id[:8],
                            attempt=self.reconnect_attempts,
                            backoff_seconds=backoff
                        )
                        await asyncio.sleep(backoff)

                    # Log the URL we're connecting to for debugging
                    logger.info(
                        "websocket_connecting_to",
                        worker_id=self.worker_id[:8],
                        url=self.websocket_url
                    )

                    # Connect with authentication header and ping settings
                    self.websocket = await websockets.connect(
                        self.websocket_url,
                        additional_headers={
                            "Authorization": f"Bearer {self.api_key}"
                        },
                        ping_interval=20,  # Send ping every 20 seconds
                        ping_timeout=10   # Wait 10 seconds for pong
                    )

                    self.connected = True
                    self.reconnect_attempts = 0
                    self.connection_start_time = asyncio.get_event_loop().time()
                    self.last_ping_time = self.connection_start_time
                    self.last_pong_time = self.connection_start_time

                    logger.info(
                        "websocket_connected",
                        worker_id=self.worker_id[:8],
                        url=self.websocket_url,
                        attempt=self.reconnect_attempts if self.reconnect_attempts > 0 else "initial"
                    )

                except Exception as e:
                    self.reconnect_attempts += 1
                    logger.warning(
                        "websocket_connect_failed",
                        error=str(e),
                        worker_id=self.worker_id[:8],
                        attempts=self.reconnect_attempts
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
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Send event
                await self.websocket.send(json.dumps(event))

            except websockets.exceptions.ConnectionClosed:
                self.connected = False
                # Re-queue the event (put back)
                try:
                    await self.event_queue.put(event)
                except:
                    logger.warning("failed_to_requeue_event", worker_id=self.worker_id[:8])

            except Exception as e:
                logger.warning("websocket_send_error", error=str(e), worker_id=self.worker_id[:8])

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
                    await self.websocket.send(json.dumps({
                        "message_type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))

                elif message_type == "connected":
                    # Connection acknowledgment
                    logger.info(
                        "websocket_handshake_complete",
                        worker_id=self.worker_id[:8],
                        features=message.get("features", [])
                    )

            except websockets.exceptions.ConnectionClosed:
                self.connected = False
                logger.info("websocket_connection_closed", worker_id=self.worker_id[:8])

            except json.JSONDecodeError as e:
                logger.warning("websocket_invalid_json", error=str(e), worker_id=self.worker_id[:8])

            except Exception as e:
                logger.warning("websocket_receive_error", error=str(e), worker_id=self.worker_id[:8])

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to maintain connection."""
        while self._running:
            await asyncio.sleep(30)  # 30-second interval

            if self.connected:
                try:
                    await self.websocket.send(json.dumps({
                        "message_type": "heartbeat",
                        "worker_id": self.worker_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))
                    self.last_ping_time = asyncio.get_event_loop().time()
                except Exception as e:
                    logger.warning("heartbeat_send_failed", error=str(e), worker_id=self.worker_id[:8])
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
                    logger.warning(
                        "websocket_stale_connection_detected",
                        worker_id=self.worker_id[:8],
                        seconds_since_pong=int(current_time - self.last_pong_time)
                    )
                    # Force reconnection
                    self.connected = False
                    if self.websocket:
                        try:
                            await self.websocket.close()
                        except:
                            pass
                    continue

                # Check if connection needs renewal
                connection_age = current_time - self.connection_start_time
                if connection_age > self.connection_renewal_interval:
                    logger.info(
                        "websocket_connection_renewal",
                        worker_id=self.worker_id[:8],
                        connection_age_seconds=int(connection_age),
                        renewal_interval=self.connection_renewal_interval
                    )
                    # Gracefully close and reconnect
                    self.connected = False
                    if self.websocket:
                        try:
                            await self.websocket.close()
                        except:
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
            data = message.get("data", {})

            logger.info(
                "control_message_received",
                command=command,
                execution_id=execution_id[:8] if execution_id else None,
                worker_id=self.worker_id[:8]
            )

            # Call registered handler
            if self.on_control_message:
                # Handle async or sync callbacks
                result = self.on_control_message(message)
                if asyncio.iscoroutine(result):
                    await result

        except Exception as e:
            logger.error("control_message_handler_error", error=str(e), worker_id=self.worker_id[:8])
