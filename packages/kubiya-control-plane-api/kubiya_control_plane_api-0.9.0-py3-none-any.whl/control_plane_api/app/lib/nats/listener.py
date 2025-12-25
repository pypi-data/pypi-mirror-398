"""NATS event listener for control plane."""

import json
from typing import Dict, Any, Optional, Set
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class NATSEventListener:
    """
    Control plane listener for NATS events from workers.

    Subscribes to org-specific subjects and processes events by storing them
    in Redis for UI consumption (same flow as HTTP/WebSocket events).
    """

    def __init__(
        self,
        nats_url: str,
        credentials_file: str,
        jetstream_enabled: bool = True,
        stream_name: str = "EVENTS",
    ):
        """
        Initialize NATS event listener.

        Args:
            nats_url: NATS server URL
            credentials_file: Path to control plane NATS credentials file
            jetstream_enabled: Enable JetStream for durable consumers
            stream_name: JetStream stream name
        """
        self.nats_url = nats_url
        self.credentials_file = credentials_file
        self.jetstream_enabled = jetstream_enabled
        self.stream_name = stream_name

        self.nc = None  # NATS connection
        self.js = None  # JetStream context
        self.subscriptions: Dict[str, Any] = {}  # org_id -> subscription
        self._running = False

    async def start(self) -> None:
        """Start NATS listener and connect to server."""
        if self._running:
            logger.warning("nats_listener_already_running")
            return

        try:
            # Import nats-py
            try:
                import nats
                from nats.errors import TimeoutError, NoServersError
            except ImportError:
                raise ImportError(
                    "nats-py is required for NATS listener. "
                    "Install it with: pip install nats-py"
                )

            # Connect to NATS
            self.nc = await nats.connect(
                servers=[self.nats_url],
                user_credentials=self.credentials_file,
                max_reconnect_attempts=-1,  # Infinite reconnects
                reconnect_time_wait=2,
                ping_interval=20,
                max_outstanding_pings=3,
            )

            # Initialize JetStream if enabled
            if self.jetstream_enabled:
                self.js = self.nc.jetstream()

            self._running = True

            logger.info(
                "nats_listener_started",
                url=self.nats_url,
                jetstream_enabled=self.jetstream_enabled,
                credentials_file=self.credentials_file,
            )

        except ImportError as e:
            logger.error(
                "nats_listener_dependency_missing",
                error=str(e),
            )
            raise

        except Exception as e:
            logger.error(
                "nats_listener_start_failed",
                error=str(e),
                url=self.nats_url,
            )
            raise

    async def subscribe_organization(self, organization_id: str) -> None:
        """
        Subscribe to all events for an organization.

        Subject: events.{organization_id}.>

        Args:
            organization_id: Organization ID to subscribe to

        Raises:
            RuntimeError: If listener not started
            Exception: If subscription fails
        """
        if not self._running or not self.nc:
            raise RuntimeError("NATS listener not started")

        if organization_id in self.subscriptions:
            logger.warning(
                "nats_org_already_subscribed",
                organization_id=organization_id,
            )
            return

        subject = f"events.{organization_id}.>"

        try:
            async def message_handler(msg):
                """Handle incoming NATS message."""
                try:
                    # Parse message
                    event_data = json.loads(msg.data.decode())

                    # Process event (store in Redis)
                    await self._process_event(event_data)

                    # Acknowledge message
                    if hasattr(msg, "ack"):
                        await msg.ack()

                except json.JSONDecodeError as e:
                    logger.error(
                        "nats_message_invalid_json",
                        error=str(e),
                        subject=msg.subject,
                    )
                    # Negative acknowledgment for retry
                    if hasattr(msg, "nak"):
                        await msg.nak()

                except Exception as e:
                    logger.error(
                        "nats_message_process_error",
                        error=str(e),
                        subject=msg.subject,
                    )
                    # Negative acknowledgment for retry
                    if hasattr(msg, "nak"):
                        await msg.nak()

            if self.jetstream_enabled and self.js:
                # Subscribe with JetStream (durable consumer)
                consumer_name = f"control-plane-{organization_id}"

                sub = await self.js.subscribe(
                    subject,
                    durable=consumer_name,
                    cb=message_handler,
                    manual_ack=True,
                )

                logger.info(
                    "nats_jetstream_org_subscribed",
                    organization_id=organization_id,
                    subject=subject,
                    consumer=consumer_name,
                )
            else:
                # Subscribe without JetStream
                sub = await self.nc.subscribe(subject, cb=message_handler)

                logger.info(
                    "nats_org_subscribed",
                    organization_id=organization_id,
                    subject=subject,
                )

            self.subscriptions[organization_id] = sub

        except Exception as e:
            logger.error(
                "nats_org_subscribe_failed",
                error=str(e),
                organization_id=organization_id,
                subject=subject,
            )
            raise

    async def unsubscribe_organization(self, organization_id: str) -> None:
        """
        Unsubscribe from organization events.

        Args:
            organization_id: Organization ID to unsubscribe from
        """
        if organization_id not in self.subscriptions:
            logger.warning(
                "nats_org_not_subscribed",
                organization_id=organization_id,
            )
            return

        try:
            sub = self.subscriptions[organization_id]
            await sub.unsubscribe()
            del self.subscriptions[organization_id]

            logger.info(
                "nats_org_unsubscribed",
                organization_id=organization_id,
            )

        except Exception as e:
            logger.error(
                "nats_org_unsubscribe_failed",
                error=str(e),
                organization_id=organization_id,
            )

    async def _process_event(self, event_data: Dict[str, Any]) -> None:
        """
        Process event received from NATS.

        Stores event in Redis for UI consumption (same as HTTP/WebSocket flow).

        Args:
            event_data: Event data from NATS message
        """
        try:
            # Extract event fields
            execution_id = event_data.get("execution_id")
            event_type = event_data.get("event_type")
            data = event_data.get("data")
            timestamp = event_data.get("timestamp")
            worker_id = event_data.get("worker_id")
            organization_id = event_data.get("organization_id")

            if not all([execution_id, event_type, data]):
                logger.warning(
                    "nats_event_missing_required_fields",
                    event_data=event_data,
                )
                return

            # Get Redis client
            from control_plane_api.app.lib.redis_client import get_redis_client

            redis_client = get_redis_client()
            if not redis_client:
                logger.warning("nats_event_redis_not_available")
                return

            # Build message for Redis
            message = {
                "event_type": event_type,
                "data": data,
                "timestamp": timestamp,
            }

            message_json = json.dumps(message)

            # Redis keys
            list_key = f"execution:{execution_id}:events"
            channel = f"execution:{execution_id}:stream"

            # Store in Redis list for replay
            await redis_client.lpush(list_key, message_json)
            await redis_client.ltrim(list_key, 0, 999)  # Keep last 1000
            await redis_client.expire(list_key, 3600)  # 1 hour TTL

            # Publish to Redis pub/sub for real-time UI
            await redis_client.publish(channel, message_json)

            logger.debug(
                "nats_event_processed",
                execution_id=execution_id,
                event_type=event_type,
                worker_id=worker_id[:8] if worker_id else None,
                organization_id=organization_id,
            )

        except Exception as e:
            logger.error(
                "nats_event_process_failed",
                error=str(e),
                event_data=event_data,
            )
            raise

    async def stop(self) -> None:
        """Stop NATS listener and cleanup resources."""
        if not self._running:
            return

        self._running = False

        logger.info("nats_listener_stopping")

        # Unsubscribe from all organizations
        for org_id in list(self.subscriptions.keys()):
            try:
                await self.unsubscribe_organization(org_id)
            except Exception as e:
                logger.warning(
                    "nats_org_unsubscribe_on_stop_failed",
                    error=str(e),
                    organization_id=org_id,
                )

        # Close NATS connection
        if self.nc:
            try:
                await self.nc.drain()
                await self.nc.close()
            except Exception as e:
                logger.warning("nats_connection_close_error", error=str(e))

        logger.info("nats_listener_stopped")

    def is_running(self) -> bool:
        """Check if listener is running."""
        return self._running and self.nc is not None and self.nc.is_connected

    def get_subscribed_organizations(self) -> Set[str]:
        """Get set of currently subscribed organization IDs."""
        return set(self.subscriptions.keys())

    async def health_check(self) -> Dict[str, Any]:
        """
        Check NATS listener health.

        Returns:
            Dict with health status
        """
        if not self.nc:
            return {
                "healthy": False,
                "error": "nats_listener_not_initialized",
            }

        health = {
            "healthy": self.nc.is_connected,
            "running": self._running,
            "nats_url": self.nats_url,
            "jetstream_enabled": self.jetstream_enabled,
            "subscribed_organizations": len(self.subscriptions),
            "organizations": list(self.subscriptions.keys()),
        }

        if self.nc.is_connected:
            health["connected_url"] = (
                self.nc.connected_url.netloc
                if self.nc.connected_url
                else None
            )

            # Add stats if available
            if hasattr(self.nc, "stats"):
                stats = self.nc.stats
                health["stats"] = {
                    "in_msgs": stats.get("in_msgs", 0),
                    "out_msgs": stats.get("out_msgs", 0),
                    "reconnects": stats.get("reconnects", 0),
                }

        return health
