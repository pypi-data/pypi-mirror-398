"""HTTP-based event bus provider."""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
import httpx
import structlog
from pydantic import Field

from control_plane_api.app.lib.event_bus.base import EventBusProvider, EventBusConfig

logger = structlog.get_logger(__name__)


class HTTPConfig(EventBusConfig):
    """Configuration for HTTP event provider."""

    base_url: str = Field(..., description="Base URL for control plane API")
    batching_enabled: bool = Field(
        default=True, description="Enable event batching"
    )
    batch_window_ms: int = Field(
        default=100, description="Batch window in milliseconds"
    )
    batch_max_size_bytes: int = Field(
        default=1000, description="Maximum batch size in bytes"
    )
    api_key: Optional[str] = Field(
        default=None, description="API key for authentication"
    )


class HTTPEventProvider(EventBusProvider):
    """HTTP-based event publishing (default provider)."""

    def __init__(self, config: HTTPConfig):
        super().__init__(config)
        self.config: HTTPConfig = config
        self.base_url = config.base_url.rstrip("/")
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout_seconds,
            follow_redirects=False,  # Fail fast on redirects
        )
        self.logger.info(
            "http_provider_initialized",
            base_url=self.base_url,
            batching_enabled=self.config.batching_enabled,
        )

    async def publish_event(
        self,
        execution_id: str,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Publish event via HTTP POST.

        Args:
            execution_id: Execution ID
            event_type: Event type
            data: Event data
            metadata: Optional metadata

        Returns:
            True if successful (202 Accepted)
        """
        if not self.client:
            self.logger.error("http_client_not_initialized")
            return False

        url = f"{self.base_url}/api/v1/executions/{execution_id}/events"

        payload = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        headers = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        try:
            response = await self.client.post(url, json=payload, headers=headers)

            if response.status_code == 202:
                self.logger.debug(
                    "http_event_published",
                    execution_id=execution_id,
                    event_type=event_type,
                )
                return True
            else:
                self.logger.warning(
                    "http_event_publish_failed",
                    execution_id=execution_id,
                    event_type=event_type,
                    status_code=response.status_code,
                    response=response.text[:200],
                )
                return False

        except httpx.TimeoutException:
            self.logger.error(
                "http_event_publish_timeout",
                execution_id=execution_id,
                event_type=event_type,
                timeout=self.config.timeout_seconds,
            )
            return False
        except Exception as e:
            self.logger.error(
                "http_event_publish_exception",
                execution_id=execution_id,
                event_type=event_type,
                error=str(e),
            )
            return False

    async def subscribe(
        self, pattern: str, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """HTTP provider does not support subscriptions."""
        self.logger.warning(
            "http_provider_subscribe_not_supported", pattern=pattern
        )
        raise NotImplementedError(
            "HTTP provider does not support subscriptions"
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check HTTP client health."""
        if not self.client:
            return {
                "healthy": False,
                "error": "client_not_initialized",
            }

        try:
            # Try to make a simple request to health endpoint
            health_url = f"{self.base_url}/api/health"
            response = await self.client.get(health_url, timeout=5.0)

            return {
                "healthy": response.status_code == 200,
                "base_url": self.base_url,
                "status_code": response.status_code,
            }
        except Exception as e:
            return {
                "healthy": False,
                "base_url": self.base_url,
                "error": str(e),
            }

    async def shutdown(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
            self.logger.info("http_provider_shutdown")
