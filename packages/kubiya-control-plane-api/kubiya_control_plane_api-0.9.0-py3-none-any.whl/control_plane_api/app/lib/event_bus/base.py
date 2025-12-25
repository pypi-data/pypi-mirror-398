"""Base classes and interfaces for event bus providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class EventBusConfig(BaseModel):
    """Base configuration for event bus providers."""

    enabled: bool = Field(default=True, description="Whether this provider is enabled")
    timeout_seconds: int = Field(
        default=30, description="Timeout for operations in seconds"
    )
    retry_attempts: int = Field(
        default=3, description="Number of retry attempts on failure"
    )
    retry_backoff_seconds: float = Field(
        default=0.5, description="Backoff time between retries in seconds"
    )


class EventBusProvider(ABC):
    """Abstract base class for event bus providers."""

    def __init__(self, config: EventBusConfig):
        self.config = config
        self.logger = structlog.get_logger(
            __name__, provider=self.__class__.__name__
        )

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize provider connection/resources.

        Raises:
            Exception: If initialization fails
        """
        pass

    @abstractmethod
    async def publish_event(
        self,
        execution_id: str,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Publish event to the bus.

        Args:
            execution_id: Unique execution identifier
            event_type: Type of event (e.g., "message_chunk", "tool_started")
            data: Event payload data
            metadata: Optional metadata (organization_id, worker_id, etc.)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def subscribe(
        self, pattern: str, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to events matching pattern.

        Args:
            pattern: Pattern to match events (provider-specific format)
            callback: Async callback function to handle events
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health status.

        Returns:
            Dict with health info: {"healthy": bool, "details": {...}}
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup resources and close connections."""
        pass

    async def _retry_operation(
        self, operation: Callable, operation_name: str
    ) -> Any:
        """
        Retry an operation with exponential backoff.

        Args:
            operation: Async operation to retry
            operation_name: Name for logging

        Returns:
            Result of operation

        Raises:
            Last exception if all retries fail
        """
        import asyncio

        last_exception = None
        for attempt in range(self.config.retry_attempts):
            try:
                return await operation()
            except Exception as e:
                last_exception = e
                if attempt < self.config.retry_attempts - 1:
                    backoff = self.config.retry_backoff_seconds * (2**attempt)
                    self.logger.warning(
                        f"{operation_name}_retry",
                        attempt=attempt + 1,
                        max_attempts=self.config.retry_attempts,
                        backoff_seconds=backoff,
                        error=str(e),
                    )
                    await asyncio.sleep(backoff)
                else:
                    self.logger.error(
                        f"{operation_name}_failed_all_retries",
                        attempts=self.config.retry_attempts,
                        error=str(e),
                    )

        raise last_exception
