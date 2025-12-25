"""Redis pub/sub based event bus provider."""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
import json
import structlog
from pydantic import Field

from control_plane_api.app.lib.event_bus.base import EventBusProvider, EventBusConfig
from control_plane_api.app.lib.redis_client import get_redis_client, RedisClient

logger = structlog.get_logger(__name__)


class RedisConfig(EventBusConfig):
    """Configuration for Redis event provider."""

    redis_url: Optional[str] = Field(
        default=None,
        description="Redis URL (uses REDIS_URL env var if not specified)"
    )
    list_max_size: int = Field(
        default=1000, description="Maximum events to keep in Redis list"
    )
    list_ttl_seconds: int = Field(
        default=3600, description="TTL for event lists in seconds"
    )
    channel_prefix: str = Field(
        default="execution", description="Prefix for Redis pub/sub channels"
    )


class RedisEventProvider(EventBusProvider):
    """Redis pub/sub based event publishing."""

    def __init__(self, config: RedisConfig):
        super().__init__(config)
        self.config: RedisConfig = config
        self.redis_client: Optional[RedisClient] = None

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        # Get Redis client using existing infrastructure
        self.redis_client = get_redis_client()

        if not self.redis_client:
            raise RuntimeError(
                "Redis client not configured. Set REDIS_URL or Upstash environment variables."
            )

        # Test connection
        try:
            ping_ok = await self.redis_client.ping()
            if not ping_ok:
                raise RuntimeError("Redis ping failed")

            self.logger.info(
                "redis_provider_initialized",
                list_max_size=self.config.list_max_size,
                list_ttl_seconds=self.config.list_ttl_seconds,
            )

        except Exception as e:
            self.logger.error("redis_provider_init_failed", error=str(e))
            raise

    async def publish_event(
        self,
        execution_id: str,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Publish event to Redis pub/sub and store in list.

        Publishes to:
        1. Redis list (execution:{id}:events) for replay - LPUSH + LTRIM
        2. Redis pub/sub channel (execution:{id}:stream) for real-time

        Args:
            execution_id: Execution ID
            event_type: Event type
            data: Event payload
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if not self.redis_client:
            self.logger.error("redis_client_not_initialized")
            return False

        # Build event message
        message = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            message["metadata"] = metadata

        message_json = json.dumps(message)

        # Redis keys
        list_key = f"{self.config.channel_prefix}:{execution_id}:events"
        channel = f"{self.config.channel_prefix}:{execution_id}:stream"

        try:
            # 1. Store in Redis list for replay (LPUSH + LTRIM)
            lpush_ok = await self.redis_client.lpush(list_key, message_json)
            if not lpush_ok:
                self.logger.warning(
                    "redis_lpush_failed",
                    execution_id=execution_id,
                    event_type=event_type,
                )
                return False

            # 2. Trim list to max size (keep last N events)
            ltrim_ok = await self.redis_client.ltrim(
                list_key, 0, self.config.list_max_size - 1
            )
            if not ltrim_ok:
                self.logger.warning(
                    "redis_ltrim_failed",
                    execution_id=execution_id,
                    list_key=list_key,
                )
                # Non-fatal, continue

            # 3. Set TTL on list
            expire_ok = await self.redis_client.expire(
                list_key, self.config.list_ttl_seconds
            )
            if not expire_ok:
                self.logger.warning(
                    "redis_expire_failed",
                    execution_id=execution_id,
                    list_key=list_key,
                )
                # Non-fatal, continue

            # 4. Publish to pub/sub channel for real-time delivery
            publish_ok = await self.redis_client.publish(channel, message_json)
            if not publish_ok:
                self.logger.warning(
                    "redis_publish_failed",
                    execution_id=execution_id,
                    channel=channel,
                )
                # List storage succeeded, so return True
                # Pub/sub is for real-time only, replay is available from list

            self.logger.debug(
                "redis_event_published",
                execution_id=execution_id,
                event_type=event_type,
                list_stored=lpush_ok,
                pubsub_published=publish_ok,
            )

            return True

        except Exception as e:
            self.logger.error(
                "redis_publish_event_exception",
                execution_id=execution_id,
                event_type=event_type,
                error=str(e),
            )
            return False

    async def subscribe(
        self, pattern: str, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to Redis pub/sub channels (control plane side).

        Note: This requires a dedicated Redis connection for blocking subscribe.
        This is typically used by the control plane to listen for events.

        Args:
            pattern: Channel pattern (e.g., "execution:*:stream")
            callback: Async callback for messages
        """
        self.logger.warning(
            "redis_subscribe_not_implemented",
            pattern=pattern,
            message="Redis subscribe requires dedicated connection and is typically "
                    "handled by control plane SSE streaming from Redis pub/sub"
        )
        raise NotImplementedError(
            "Redis subscribe is handled separately by control plane SSE streaming. "
            "Workers publish only."
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Redis provider health.

        Returns:
            Dict with health status
        """
        if not self.redis_client:
            return {
                "healthy": False,
                "error": "redis_client_not_initialized",
            }

        try:
            # Ping Redis
            ping_ok = await self.redis_client.ping()

            return {
                "healthy": ping_ok,
                "redis_type": "upstash" if hasattr(self.redis_client, "token") else "standard",
                "list_max_size": self.config.list_max_size,
                "list_ttl_seconds": self.config.list_ttl_seconds,
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }

    async def shutdown(self) -> None:
        """Shutdown Redis provider (connection managed globally)."""
        # Redis client is managed globally by get_redis_client()
        # No need to close connection here
        self.logger.info("redis_provider_shutdown")
