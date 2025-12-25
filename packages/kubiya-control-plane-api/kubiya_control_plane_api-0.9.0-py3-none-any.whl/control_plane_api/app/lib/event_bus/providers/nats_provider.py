"""NATS-based event bus provider with JetStream support."""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
import json
import structlog
from pydantic import Field

from control_plane_api.app.lib.event_bus.base import EventBusProvider, EventBusConfig

logger = structlog.get_logger(__name__)


class NATSConfig(EventBusConfig):
    """Configuration for NATS event provider."""

    nats_url: str = Field(..., description="NATS server URL")
    credentials_file: Optional[str] = Field(
        default=None, description="Path to NATS credentials file (.creds)"
    )
    organization_id: str = Field(..., description="Organization ID for subject prefix")
    worker_id: str = Field(..., description="Worker ID for subject")
    jetstream_enabled: bool = Field(
        default=True, description="Enable JetStream for durable delivery"
    )
    stream_name: str = Field(
        default="EVENTS", description="JetStream stream name"
    )
    max_reconnect_attempts: int = Field(
        default=-1, description="Max reconnection attempts (-1 = infinite)"
    )
    reconnect_time_wait: int = Field(
        default=2, description="Initial reconnect backoff in seconds"
    )
    ping_interval: int = Field(
        default=20, description="Ping interval in seconds"
    )
    max_outstanding_pings: int = Field(
        default=3, description="Max outstanding pings before disconnect"
    )
    publish_timeout: float = Field(
        default=5.0, description="Publish timeout in seconds"
    )


class NATSEventProvider(EventBusProvider):
    """NATS-based event publishing with JetStream (optional, high-performance)."""

    def __init__(self, config: NATSConfig):
        super().__init__(config)
        self.config: NATSConfig = config
        self.nc = None  # NATS connection
        self.js = None  # JetStream context

    async def initialize(self) -> None:
        """Initialize NATS connection and JetStream."""
        try:
            # Import nats-py
            try:
                import nats
                from nats.errors import TimeoutError, NoServersError
            except ImportError:
                raise ImportError(
                    "nats-py is required for NATS provider. "
                    "Install it with: pip install nats-py"
                )

            # Build connection options
            connect_opts = {
                "servers": [self.config.nats_url],
                "max_reconnect_attempts": self.config.max_reconnect_attempts,
                "reconnect_time_wait": self.config.reconnect_time_wait,
                "ping_interval": self.config.ping_interval,
                "max_outstanding_pings": self.config.max_outstanding_pings,
            }

            # Add credentials if provided
            if self.config.credentials_file:
                connect_opts["user_credentials"] = self.config.credentials_file

            # Connect to NATS
            self.nc = await nats.connect(**connect_opts)

            # Initialize JetStream if enabled
            if self.config.jetstream_enabled:
                self.js = self.nc.jetstream()

            self.logger.info(
                "nats_provider_initialized",
                url=self.config.nats_url,
                jetstream_enabled=self.config.jetstream_enabled,
                organization_id=self.config.organization_id,
                worker_id=self.config.worker_id[:8],
            )

        except ImportError as e:
            self.logger.warning(
                "nats_provider_dependency_missing",
                error=str(e),
                message="Install nats-py to enable NATS provider"
            )
            raise

        except Exception as e:
            self.logger.error(
                "nats_provider_init_failed",
                error=str(e),
                url=self.config.nats_url,
            )
            raise

    async def publish_event(
        self,
        execution_id: str,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Publish event to NATS subject with JetStream.

        Subject format: events.{org_id}.{worker_id}.{execution_id}

        Args:
            execution_id: Execution ID
            event_type: Event type
            data: Event payload
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if not self.nc or not self.nc.is_connected:
            self.logger.warning(
                "nats_not_connected",
                execution_id=execution_id,
                event_type=event_type,
            )
            return False

        # Build subject: events.{org_id}.{worker_id}.{execution_id}
        subject = (
            f"events.{self.config.organization_id}."
            f"{self.config.worker_id}.{execution_id}"
        )

        # Build message
        message = {
            "event_type": event_type,
            "data": data,
            "execution_id": execution_id,
            "worker_id": self.config.worker_id,
            "organization_id": self.config.organization_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            message["metadata"] = metadata

        message_json = json.dumps(message).encode()

        try:
            if self.config.jetstream_enabled and self.js:
                # Publish with JetStream (at-least-once delivery)
                ack = await self.js.publish(
                    subject,
                    message_json,
                    timeout=self.config.publish_timeout,
                )

                self.logger.debug(
                    "nats_jetstream_event_published",
                    execution_id=execution_id,
                    event_type=event_type,
                    subject=subject,
                    stream=ack.stream if hasattr(ack, "stream") else None,
                    seq=ack.seq if hasattr(ack, "seq") else None,
                )
            else:
                # Publish without JetStream (fire-and-forget)
                await self.nc.publish(subject, message_json)

                self.logger.debug(
                    "nats_event_published",
                    execution_id=execution_id,
                    event_type=event_type,
                    subject=subject,
                )

            return True

        except Exception as e:
            self.logger.error(
                "nats_publish_failed",
                error=str(e),
                execution_id=execution_id,
                event_type=event_type,
                subject=subject,
            )
            return False

    async def subscribe(
        self, pattern: str, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to NATS subjects (control plane side).

        Args:
            pattern: Subject pattern (e.g., "events.{org_id}.>")
            callback: Async callback function for messages
        """
        if not self.nc or not self.nc.is_connected:
            raise RuntimeError("NATS not connected")

        async def message_handler(msg):
            """Internal message handler with ack support."""
            try:
                # Parse message
                data = json.loads(msg.data.decode())

                # Call user callback
                result = callback(data)
                if result and hasattr(result, "__await__"):
                    await result

                # Acknowledge if JetStream message
                if hasattr(msg, "ack"):
                    await msg.ack()

            except Exception as e:
                self.logger.error(
                    "nats_message_handler_error",
                    error=str(e),
                    subject=msg.subject,
                )
                # Negative acknowledgment for retry
                if hasattr(msg, "nak"):
                    await msg.nak()

        if self.config.jetstream_enabled and self.js:
            # Subscribe with JetStream (durable consumer)
            consumer_name = f"control-plane-{self.config.organization_id}"

            sub = await self.js.subscribe(
                pattern,
                durable=consumer_name,
                cb=message_handler,
                manual_ack=True,
            )

            self.logger.info(
                "nats_jetstream_subscribed",
                pattern=pattern,
                consumer=consumer_name,
            )
        else:
            # Subscribe without JetStream
            sub = await self.nc.subscribe(pattern, cb=message_handler)

            self.logger.info(
                "nats_subscribed",
                pattern=pattern,
            )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check NATS provider health.

        Returns:
            Dict with health status and connection info
        """
        if not self.nc:
            return {
                "healthy": False,
                "error": "nats_not_initialized",
            }

        health = {
            "healthy": self.nc.is_connected,
            "nats_url": self.config.nats_url,
            "connected": self.nc.is_connected,
            "jetstream_enabled": self.config.jetstream_enabled,
            "organization_id": self.config.organization_id,
            "worker_id": self.config.worker_id[:8],
        }

        if self.nc.is_connected:
            health["connected_url"] = (
                self.nc.connected_url.netloc
                if self.nc.connected_url
                else None
            )
            health["max_payload"] = self.nc.max_payload

            # Add stats if available
            if hasattr(self.nc, "stats"):
                stats = self.nc.stats
                health["stats"] = {
                    "in_msgs": stats.get("in_msgs", 0),
                    "out_msgs": stats.get("out_msgs", 0),
                    "reconnects": stats.get("reconnects", 0),
                }

        return health

    async def shutdown(self) -> None:
        """Shutdown NATS connection gracefully."""
        if self.nc:
            try:
                # Drain pending messages before closing
                await self.nc.drain()
                await self.nc.close()

                self.logger.info(
                    "nats_provider_shutdown",
                    organization_id=self.config.organization_id,
                    worker_id=self.config.worker_id[:8],
                )

            except Exception as e:
                self.logger.warning(
                    "nats_shutdown_error",
                    error=str(e),
                )
