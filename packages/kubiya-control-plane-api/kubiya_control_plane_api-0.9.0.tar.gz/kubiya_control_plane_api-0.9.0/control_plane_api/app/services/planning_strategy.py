"""
Planning Strategy Pattern

Defines the interface for different task planning implementations (Agno, Claude Code SDK, etc.)
Like choosing transportation: train, walk, or flight - same destination, different approaches.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator
from sqlalchemy.orm import Session

from control_plane_api.app.models.task_planning import TaskPlanResponse


class PlanningStrategy(ABC):
    """
    Abstract base class for task planning strategies.

    Each strategy implements the same interface but uses different underlying
    technology (Agno, Claude Code SDK, etc.)
    """

    def __init__(self, db: Session, organization_id: str = None, api_token: str = None):
        """
        Initialize strategy.

        Args:
            db: Database session
            organization_id: Organization ID
            api_token: API token for authentication
        """
        self.db = db
        self.organization_id = organization_id
        self.api_token = api_token

    @abstractmethod
    async def plan_task(self, planning_prompt: str) -> TaskPlanResponse:
        """
        Generate a task plan (non-streaming).

        Args:
            planning_prompt: The complete planning prompt

        Returns:
            TaskPlanResponse with the generated plan
        """
        pass

    @abstractmethod
    async def plan_task_stream(self, planning_prompt: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate a task plan with streaming events.

        Args:
            planning_prompt: The complete planning prompt

        Yields:
            Dict with event type and data for SSE streaming
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the strategy name for logging"""
        pass
