"""Event bus manager for orchestrating multiple providers."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import asyncio
import structlog

from control_plane_api.app.lib.event_bus.base import EventBusProvider

logger = structlog.get_logger(__name__)


class EventBusManagerConfig(BaseModel):
    """Configuration for event bus manager with all providers."""

    # Import provider configs (will be defined in provider modules)
    http: Optional[Any] = Field(default=None, description="HTTP provider config")
    websocket: Optional[Any] = Field(
        default=None, description="WebSocket provider config"
    )
    redis: Optional[Any] = Field(default=None, description="Redis provider config")
    nats: Optional[Any] = Field(default=None, description="NATS provider config")


class EventBusManager:
    """
    Manages multiple event bus providers with fallback support.
    Publishes to all enabled providers simultaneously.
    """

    def __init__(self, config: EventBusManagerConfig):
        self.config = config
        self.providers: Dict[str, EventBusProvider] = {}
        self.logger = structlog.get_logger(__name__)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all enabled providers."""
        if self._initialized:
            self.logger.warning("event_bus_manager_already_initialized")
            return

        initialized_providers = []

        # HTTP Provider
        if self.config.http and self.config.http.enabled:
            try:
                from control_plane_api.app.lib.event_bus.providers.http_provider import (
                    HTTPEventProvider,
                )

                self.providers["http"] = HTTPEventProvider(self.config.http)
                await self.providers["http"].initialize()
                initialized_providers.append("http")
                self.logger.info("http_provider_initialized")
            except Exception as e:
                self.logger.error("http_provider_init_failed", error=str(e))
                # HTTP is critical, re-raise
                raise

        # WebSocket Provider
        if self.config.websocket and self.config.websocket.enabled:
            try:
                from control_plane_api.app.lib.event_bus.providers.websocket_provider import (
                    WebSocketEventProvider,
                )

                self.providers["websocket"] = WebSocketEventProvider(
                    self.config.websocket
                )
                await self.providers["websocket"].initialize()
                initialized_providers.append("websocket")
                self.logger.info("websocket_provider_initialized")
            except Exception as e:
                self.logger.warning(
                    "websocket_provider_init_failed_continuing", error=str(e)
                )
                # WebSocket is optional, continue without it

        # Redis Provider
        if self.config.redis and self.config.redis.enabled:
            try:
                from control_plane_api.app.lib.event_bus.providers.redis_provider import (
                    RedisEventProvider,
                )

                self.providers["redis"] = RedisEventProvider(self.config.redis)
                await self.providers["redis"].initialize()
                initialized_providers.append("redis")
                self.logger.info("redis_provider_initialized")
            except Exception as e:
                self.logger.warning(
                    "redis_provider_init_failed_continuing", error=str(e)
                )
                # Redis is optional, continue without it

        # NATS Provider (Optional)
        if self.config.nats and self.config.nats.enabled:
            try:
                from control_plane_api.app.lib.event_bus.providers.nats_provider import (
                    NATSEventProvider,
                )

                self.providers["nats"] = NATSEventProvider(self.config.nats)
                await self.providers["nats"].initialize()
                initialized_providers.append("nats")
                self.logger.info("nats_provider_initialized")
            except Exception as e:
                self.logger.warning(
                    "nats_provider_init_failed_optional", error=str(e)
                )
                # NATS is optional, continue without it

        if not self.providers:
            raise RuntimeError("No event bus providers initialized")

        self._initialized = True
        self.logger.info(
            "event_bus_manager_initialized",
            providers=initialized_providers,
            count=len(self.providers),
        )

    async def publish_event(
        self,
        execution_id: str,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Publish event to all enabled providers in parallel.

        Args:
            execution_id: Unique execution identifier
            event_type: Type of event
            data: Event payload
            metadata: Optional metadata

        Returns:
            Dict mapping provider name to success status
        """
        if not self._initialized:
            self.logger.error("event_bus_manager_not_initialized")
            return {}

        # Log start of publishing
        self.logger.info(
            "event_bus_publishing_start",
            execution_id=execution_id,
            event_type=event_type,
            providers=list(self.providers.keys()),
            provider_count=len(self.providers)
        )

        # Create tasks for all providers
        tasks = []
        provider_names = []

        for name, provider in self.providers.items():
            # Create task directly to avoid unawaited coroutine warnings
            # Don't store the coroutine separately - wrap it immediately
            task = asyncio.create_task(
                provider.publish_event(execution_id, event_type, data, metadata)
            )
            tasks.append(task)
            provider_names.append(name)

        # Execute all in parallel and ensure all tasks complete
        try:
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            # If gather fails, cancel any pending tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            # Re-raise to let caller handle
            raise

        # Map results back to provider names
        results = {}
        for name, result in zip(provider_names, results_list):
            if isinstance(result, Exception):
                self.logger.error(
                    "provider_publish_exception",
                    provider=name,
                    error=str(result),
                    execution_id=execution_id,
                    event_type=event_type,
                )
                results[name] = False
            else:
                results[name] = result
                # Log individual provider result
                if result:
                    self.logger.info(
                        "provider_publish_success",
                        provider=name,
                        execution_id=execution_id,
                        event_type=event_type
                    )
                else:
                    self.logger.warning(
                        "provider_publish_failed",
                        provider=name,
                        execution_id=execution_id,
                        event_type=event_type
                    )

        # Log overall status
        success_count = sum(1 for success in results.values() if success)
        if success_count == 0:
            self.logger.error(
                "event_bus_all_providers_failed",
                execution_id=execution_id,
                event_type=event_type,
                results=results,
            )
        elif success_count < len(results):
            self.logger.warning(
                "event_bus_partial_success",
                execution_id=execution_id,
                event_type=event_type,
                success_count=success_count,
                total_count=len(results),
                results=results,
            )
        else:
            self.logger.info(
                "event_bus_all_providers_success",
                execution_id=execution_id,
                event_type=event_type,
                provider_count=len(results),
                providers=list(results.keys())
            )

        return results

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all providers.

        Returns:
            Dict with health status for each provider
        """
        health = {}

        for name, provider in self.providers.items():
            try:
                provider_health = await provider.health_check()
                health[name] = provider_health
            except Exception as e:
                self.logger.error(
                    "provider_health_check_failed", provider=name, error=str(e)
                )
                health[name] = {"healthy": False, "error": str(e)}

        # Overall status
        healthy_count = sum(
            1 for h in health.values() if h.get("healthy", False)
        )
        health["_overall"] = {
            "healthy": healthy_count > 0,  # At least one provider healthy
            "total_providers": len(self.providers),
            "healthy_providers": healthy_count,
        }

        return health

    async def shutdown(self) -> None:
        """Shutdown all providers gracefully."""
        if not self._initialized:
            return

        self.logger.info("shutting_down_event_bus_manager")

        # Shutdown all providers in parallel
        tasks = []
        for name, provider in self.providers.items():
            tasks.append(self._shutdown_provider(name, provider))

        await asyncio.gather(*tasks, return_exceptions=True)

        self.providers.clear()
        self._initialized = False
        self.logger.info("event_bus_manager_shutdown_complete")

    async def _shutdown_provider(
        self, name: str, provider: EventBusProvider
    ) -> None:
        """Shutdown a single provider with error handling."""
        try:
            await provider.shutdown()
            self.logger.info("provider_shutdown", provider=name)
        except Exception as e:
            self.logger.error(
                "provider_shutdown_failed", provider=name, error=str(e)
            )

    def is_initialized(self) -> bool:
        """Check if manager is initialized."""
        return self._initialized

    def get_provider_names(self) -> list[str]:
        """Get list of initialized provider names."""
        return list(self.providers.keys())
