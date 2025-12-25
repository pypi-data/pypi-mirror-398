"""
Analytics service for collecting and sending execution metrics to Control Plane.

This service provides a clean interface for workers to track:
- Per-turn LLM metrics (tokens, cost, duration)
- Tool execution details
- Task progress
- Batch submission for efficient network usage
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import structlog
import httpx
from dataclasses import dataclass, field, asdict
import time

logger = structlog.get_logger()


@dataclass
class TurnMetrics:
    """Metrics for a single LLM turn/interaction"""
    execution_id: str
    turn_number: int
    model: str
    started_at: str  # ISO timestamp
    completed_at: Optional[str] = None
    turn_id: Optional[str] = None
    model_provider: Optional[str] = None
    duration_ms: Optional[int] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    total_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    cache_read_cost: float = 0.0
    cache_creation_cost: float = 0.0
    total_cost: float = 0.0
    finish_reason: Optional[str] = None
    response_preview: Optional[str] = None
    tools_called_count: int = 0
    tools_called_names: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    # Agentic Engineering Minutes (AEM) fields
    runtime_minutes: float = 0.0
    model_weight: float = 1.0
    tool_calls_weight: float = 1.0
    aem_value: float = 0.0
    aem_cost: float = 0.0


@dataclass
class ToolCallMetrics:
    """Metrics for a single tool execution"""
    execution_id: str
    tool_name: str
    started_at: str  # ISO timestamp
    completed_at: Optional[str] = None
    turn_id: Optional[str] = None
    tool_use_id: Optional[str] = None
    duration_ms: Optional[int] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[str] = None
    tool_output_size: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskMetrics:
    """Metrics for a task"""
    execution_id: str
    task_description: str
    task_number: Optional[int] = None
    task_id: Optional[str] = None
    task_type: Optional[str] = None
    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnalyticsService:
    """
    Service for collecting and submitting execution analytics to Control Plane.

    Workers use this service to track detailed execution metrics that are
    persisted to the database for reporting and analysis.

    Usage:
        analytics = AnalyticsService(control_plane_url, api_key)

        # Track a turn
        turn = TurnMetrics(
            execution_id=exec_id,
            turn_number=1,
            model="claude-sonnet-4",
            started_at=datetime.now(timezone.utc).isoformat(),
            input_tokens=100,
            output_tokens=200,
            ...
        )
        await analytics.record_turn(turn)

        # Or collect all metrics and send in batch at the end
        analytics.add_turn(turn)
        analytics.add_tool_call(tool_call)
        await analytics.flush()
    """

    def __init__(self, control_plane_url: str, api_key: str):
        self.control_plane_url = control_plane_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"UserKey {api_key}",
            "Content-Type": "application/json",
        }

        # Buffered metrics for batch submission
        self._turns: List[TurnMetrics] = []
        self._tool_calls: List[ToolCallMetrics] = []
        self._tasks: List[TaskMetrics] = []

        # HTTP client with reasonable timeouts
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_connections=10),
        )

    async def aclose(self):
        """Cleanup HTTP client"""
        await self._client.aclose()

    def add_turn(self, turn: TurnMetrics):
        """Add a turn to the buffer for batch submission"""
        self._turns.append(turn)

    def add_tool_call(self, tool_call: ToolCallMetrics):
        """Add a tool call to the buffer for batch submission"""
        self._tool_calls.append(tool_call)

    def add_task(self, task: TaskMetrics):
        """Add a task to the buffer for batch submission"""
        self._tasks.append(task)

    async def record_turn(self, turn: TurnMetrics) -> bool:
        """
        Immediately submit a turn to Control Plane.

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.control_plane_url}/api/v1/analytics/turns"
            payload = self._dataclass_to_dict(turn)

            response = await self._client.post(url, json=payload, headers=self.headers)

            if response.status_code not in (200, 201):
                # Try to get error details from response
                try:
                    error_detail = response.json() if response.text else "No response body"
                except:
                    error_detail = response.text[:500] if response.text else "No response body"

                logger.warning(
                    "turn_submission_failed",
                    status=response.status_code,
                    execution_id=turn.execution_id[:8],
                    error_detail=error_detail,
                )
                return False

            logger.info(
                "turn_submitted",
                execution_id=turn.execution_id[:8],
                turn_number=turn.turn_number,
                tokens=turn.total_tokens,
                cost=turn.total_cost,
            )
            return True

        except Exception as e:
            logger.error(
                "turn_submission_error",
                error=str(e),
                execution_id=turn.execution_id[:8],
            )
            return False

    async def record_tool_call(self, tool_call: ToolCallMetrics) -> bool:
        """
        Immediately submit a tool call to Control Plane.

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.control_plane_url}/api/v1/analytics/tool-calls"
            payload = self._dataclass_to_dict(tool_call)

            response = await self._client.post(url, json=payload, headers=self.headers)

            if response.status_code not in (200, 201):
                logger.warning(
                    "tool_call_submission_failed",
                    status=response.status_code,
                    execution_id=tool_call.execution_id[:8],
                )
                return False

            logger.info(
                "tool_call_submitted",
                execution_id=tool_call.execution_id[:8],
                tool_name=tool_call.tool_name,
                success=tool_call.success,
            )
            return True

        except Exception as e:
            logger.error(
                "tool_call_submission_error",
                error=str(e),
                execution_id=tool_call.execution_id[:8],
            )
            return False

    async def record_task(self, task: TaskMetrics) -> bool:
        """
        Immediately submit a task to Control Plane.

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.control_plane_url}/api/v1/analytics/tasks"
            payload = self._dataclass_to_dict(task)

            response = await self._client.post(url, json=payload, headers=self.headers)

            if response.status_code not in (200, 201):
                logger.warning(
                    "task_submission_failed",
                    status=response.status_code,
                    execution_id=task.execution_id[:8],
                )
                return False

            logger.info(
                "task_submitted",
                execution_id=task.execution_id[:8],
                task_description=task.task_description[:50],
            )
            return True

        except Exception as e:
            logger.error(
                "task_submission_error",
                error=str(e),
                execution_id=task.execution_id[:8],
            )
            return False

    async def flush(self, execution_id: str) -> Dict[str, Any]:
        """
        Submit all buffered metrics in a single batch request.

        This is more efficient than individual submissions when collecting
        multiple metrics throughout an execution.

        Args:
            execution_id: Execution ID (used for logging)

        Returns:
            Dict with submission results
        """
        if not self._turns and not self._tool_calls and not self._tasks:
            logger.info("analytics_flush_skipped_no_data", execution_id=execution_id[:8])
            return {
                "success": True,
                "turns_created": 0,
                "tool_calls_created": 0,
                "tasks_created": 0,
            }

        try:
            url = f"{self.control_plane_url}/api/v1/analytics/batch"

            payload = {
                "execution_id": execution_id,
                "turns": [self._dataclass_to_dict(t) for t in self._turns],
                "tool_calls": [self._dataclass_to_dict(tc) for tc in self._tool_calls],
                "tasks": [self._dataclass_to_dict(task) for task in self._tasks],
            }

            response = await self._client.post(url, json=payload, headers=self.headers)

            if response.status_code not in (200, 201):
                logger.warning(
                    "analytics_batch_submission_failed",
                    status=response.status_code,
                    execution_id=execution_id[:8],
                )
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                }

            result = response.json()

            logger.info(
                "analytics_batch_submitted",
                execution_id=execution_id[:8],
                turns=result.get("turns_created", 0),
                tool_calls=result.get("tool_calls_created", 0),
                tasks=result.get("tasks_created", 0),
            )

            # Clear buffers after successful submission
            self._turns.clear()
            self._tool_calls.clear()
            self._tasks.clear()

            return result

        except Exception as e:
            logger.error(
                "analytics_batch_submission_error",
                error=str(e),
                execution_id=execution_id[:8],
            )
            return {
                "success": False,
                "error": str(e),
            }

    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """Convert dataclass to dict, handling nested objects"""
        return asdict(obj)

    @staticmethod
    def calculate_duration_ms(start_time: float, end_time: float) -> int:
        """Calculate duration in milliseconds from timestamps"""
        return int((end_time - start_time) * 1000)

    @staticmethod
    def calculate_token_cost(
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
        model: str = "claude-sonnet-4",
    ) -> Dict[str, float]:
        """
        Calculate token costs based on model pricing.

        Uses centralized pricing configuration from model_pricing.py

        Returns dict with input_cost, output_cost, cache_read_cost, cache_creation_cost, total_cost
        """
        try:
            from control_plane_api.app.config.model_pricing import calculate_token_cost as calc_cost
            return calc_cost(model, input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens)
        except ImportError:
            # Fallback to simple calculation if config not available
            logger.warning("model_pricing_not_available_using_fallback", model=model)

            # Simplified pricing (per 1M tokens)
            pricing = {
                "input": 3.00,
                "output": 15.00,
                "cache_read": 0.30,
                "cache_creation": 3.75,
            }

            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            cache_read_cost = (cache_read_tokens / 1_000_000) * pricing["cache_read"]
            cache_creation_cost = (cache_creation_tokens / 1_000_000) * pricing["cache_creation"]

            return {
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "cache_read_cost": round(cache_read_cost, 6),
                "cache_creation_cost": round(cache_creation_cost, 6),
                "total_cost": round(input_cost + output_cost + cache_read_cost + cache_creation_cost, 6),
            }

    @staticmethod
    def calculate_aem(
        duration_ms: int,
        model: str,
        tool_calls_count: int,
        tool_calls_weight: float = 1.0,
    ) -> Dict[str, float]:
        """
        Calculate Agentic Engineering Minutes (AEM).

        Formula: Runtime (minutes) × Model Weight × Tool Calls Weight

        Args:
            duration_ms: Turn duration in milliseconds
            model: Model identifier
            tool_calls_count: Number of tool calls
            tool_calls_weight: Optional weight override

        Returns:
            Dict with AEM metrics (runtime_minutes, model_weight, tool_calls_weight, aem_value, aem_cost)
        """
        try:
            from control_plane_api.app.config.model_pricing import calculate_aem as calc_aem
            return calc_aem(duration_ms, model, tool_calls_count, tool_calls_weight)
        except ImportError:
            # Fallback calculation if config not available
            logger.warning("model_pricing_not_available_using_fallback_aem", model=model)

            runtime_minutes = duration_ms / 60_000.0
            model_weight = 1.0  # Default weight
            calculated_tool_weight = max(1.0, tool_calls_count / 50.0) if tool_calls_count > 0 else 1.0
            final_tool_weight = tool_calls_weight if tool_calls_weight != 1.0 else calculated_tool_weight

            aem_value = runtime_minutes * model_weight * final_tool_weight
            aem_cost = aem_value * 0.15  # $0.15/min default

            return {
                "runtime_minutes": round(runtime_minutes, 4),
                "model_weight": round(model_weight, 2),
                "tool_calls_weight": round(final_tool_weight, 2),
                "aem_value": round(aem_value, 4),
                "aem_cost": round(aem_cost, 4),
            }


# Singleton for convenience
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service(control_plane_url: str, api_key: str) -> AnalyticsService:
    """
    Get or create the analytics service singleton.

    Args:
        control_plane_url: Control Plane API URL
        api_key: Kubiya API key for authentication

    Returns:
        AnalyticsService instance
    """
    global _analytics_service

    if _analytics_service is None:
        _analytics_service = AnalyticsService(control_plane_url, api_key)
        logger.info("analytics_service_initialized")

    return _analytics_service
