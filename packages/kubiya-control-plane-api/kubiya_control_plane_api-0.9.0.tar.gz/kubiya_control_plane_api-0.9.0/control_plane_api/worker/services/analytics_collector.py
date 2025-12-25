"""
Analytics collector that integrates with runtime execution to track metrics.

This module provides hooks into the execution lifecycle to automatically
collect and submit analytics data without blocking execution.

Key features:
- Leverages LiteLLM and Agno native usage tracking
- Async fire-and-forget submission (doesn't block execution)
- Comprehensive error handling (failures don't break execution)
- Per-turn, tool call, and task tracking
- Automatic cost calculation
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import structlog
import asyncio
import time
from dataclasses import dataclass

from control_plane_api.worker.services.analytics_service import (
    AnalyticsService,
    TurnMetrics,
    ToolCallMetrics,
    TaskMetrics,
)

logger = structlog.get_logger()


@dataclass
class ExecutionContext:
    """Context for tracking execution metrics"""
    execution_id: str
    organization_id: str
    turn_number: int = 0
    turn_start_time: Optional[float] = None
    current_turn_id: Optional[str] = None
    tools_in_turn: List[str] = None

    def __post_init__(self):
        if self.tools_in_turn is None:
            self.tools_in_turn = []


class AnalyticsCollector:
    """
    Collects and submits analytics during execution.

    This collector integrates with the runtime to automatically track:
    - LLM turns with token usage and costs
    - Tool executions with timing and results
    - Task progress

    All submissions are async and failures are logged but don't break execution.
    """

    def __init__(self, analytics_service: AnalyticsService):
        self.analytics = analytics_service
        self._submission_tasks: List[asyncio.Task] = []

    def start_turn(self, ctx: ExecutionContext) -> ExecutionContext:
        """
        Mark the start of a new LLM turn.

        Args:
            ctx: Execution context

        Returns:
            Updated context with turn tracking
        """
        ctx.turn_number += 1
        ctx.turn_start_time = time.time()
        ctx.tools_in_turn = []

        logger.debug(
            "turn_started",
            execution_id=ctx.execution_id[:8],
            turn_number=ctx.turn_number,
        )

        return ctx

    def record_turn_from_litellm(
        self,
        ctx: ExecutionContext,
        response: Any,
        model: str,
        finish_reason: str = "stop",
        error_message: Optional[str] = None,
    ):
        """
        Record turn metrics from LiteLLM response.

        LiteLLM responses have `usage` attribute with token counts.

        Args:
            ctx: Execution context
            response: LiteLLM completion response
            model: Model identifier
            finish_reason: Why the turn finished
            error_message: Error if turn failed
        """
        if not ctx.turn_start_time:
            logger.warning("record_turn_called_without_start", execution_id=ctx.execution_id[:8])
            return

        turn_end_time = time.time()
        duration_ms = int((turn_end_time - ctx.turn_start_time) * 1000)

        # Extract usage from LiteLLM response
        usage = getattr(response, "usage", None)
        if not usage:
            logger.warning("litellm_response_missing_usage", execution_id=ctx.execution_id[:8])
            return

        input_tokens = getattr(usage, "prompt_tokens", 0)
        output_tokens = getattr(usage, "completion_tokens", 0)
        total_tokens = getattr(usage, "total_tokens", 0)

        # Anthropic-specific: cache tokens
        cache_read_tokens = getattr(usage, "prompt_tokens_details", {}).get("cached_tokens", 0) if hasattr(usage, "prompt_tokens_details") else 0
        cache_creation_tokens = 0  # LiteLLM doesn't expose this directly

        # Extract response content
        response_content = ""
        if hasattr(response, "choices") and response.choices:
            message = response.choices[0].message
            response_content = getattr(message, "content", "")

        # Calculate costs
        costs = AnalyticsService.calculate_token_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
            model=model,
        )

        # Determine model provider from model string
        model_provider = self._extract_provider(model)

        turn = TurnMetrics(
            execution_id=ctx.execution_id,
            turn_number=ctx.turn_number,
            model=model,
            model_provider=model_provider,
            started_at=datetime.fromtimestamp(ctx.turn_start_time, timezone.utc).isoformat(),
            completed_at=datetime.fromtimestamp(turn_end_time, timezone.utc).isoformat(),
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
            total_tokens=total_tokens,
            input_cost=costs["input_cost"],
            output_cost=costs["output_cost"],
            cache_read_cost=costs["cache_read_cost"],
            cache_creation_cost=costs["cache_creation_cost"],
            total_cost=costs["total_cost"],
            finish_reason=finish_reason,
            response_preview=response_content[:500] if response_content else None,
            tools_called_count=len(ctx.tools_in_turn),
            tools_called_names=list(set(ctx.tools_in_turn)),  # Unique tool names
            error_message=error_message,
        )

        # Submit async (fire-and-forget)
        self._submit_async(turn, "turn")

        # Reset turn context
        ctx.turn_start_time = None
        ctx.tools_in_turn = []

    def record_turn_from_agno(
        self,
        ctx: ExecutionContext,
        result: Any,
        model: str,
        finish_reason: str = "stop",
        error_message: Optional[str] = None,
    ):
        """
        Record turn metrics from Agno/phidata result.

        Agno results have `metrics` attribute with token counts.

        Args:
            ctx: Execution context
            result: Agno RunResponse
            model: Model identifier
            finish_reason: Why the turn finished
            error_message: Error if turn failed
        """
        if not ctx.turn_start_time:
            logger.warning("record_turn_called_without_start", execution_id=ctx.execution_id[:8])
            return

        turn_end_time = time.time()
        duration_ms = int((turn_end_time - ctx.turn_start_time) * 1000)

        # Extract usage from Agno result
        metrics = getattr(result, "metrics", None)
        if not metrics:
            logger.warning("agno_result_missing_metrics", execution_id=ctx.execution_id[:8])
            return

        input_tokens = getattr(metrics, "input_tokens", 0)
        output_tokens = getattr(metrics, "output_tokens", 0)
        total_tokens = getattr(metrics, "total_tokens", 0)

        # Anthropic-specific: Agno exposes cache tokens
        cache_read_tokens = getattr(metrics, "input_token_details", {}).get("cache_read", 0) if hasattr(metrics, "input_token_details") else 0
        cache_creation_tokens = getattr(metrics, "input_token_details", {}).get("cache_creation", 0) if hasattr(metrics, "input_token_details") else 0

        # Extract response content
        response_content = getattr(result, "content", "")

        # Calculate costs
        costs = AnalyticsService.calculate_token_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
            model=model,
        )

        # Determine model provider
        model_provider = self._extract_provider(model)

        turn = TurnMetrics(
            execution_id=ctx.execution_id,
            turn_number=ctx.turn_number,
            model=model,
            model_provider=model_provider,
            started_at=datetime.fromtimestamp(ctx.turn_start_time, timezone.utc).isoformat(),
            completed_at=datetime.fromtimestamp(turn_end_time, timezone.utc).isoformat(),
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
            total_tokens=total_tokens,
            input_cost=costs["input_cost"],
            output_cost=costs["output_cost"],
            cache_read_cost=costs["cache_read_cost"],
            cache_creation_cost=costs["cache_creation_cost"],
            total_cost=costs["total_cost"],
            finish_reason=finish_reason,
            response_preview=response_content[:500] if response_content else None,
            tools_called_count=len(ctx.tools_in_turn),
            tools_called_names=list(set(ctx.tools_in_turn)),
            error_message=error_message,
        )

        # Submit async (fire-and-forget)
        self._submit_async(turn, "turn")

        # Reset turn context
        ctx.turn_start_time = None
        ctx.tools_in_turn = []

    def record_tool_call(
        self,
        ctx: ExecutionContext,
        tool_name: str,
        tool_input: Optional[Dict[str, Any]],
        tool_output: Optional[str],
        start_time: float,
        end_time: float,
        success: bool = True,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        """
        Record a tool call.

        Args:
            ctx: Execution context
            tool_name: Name of the tool
            tool_input: Tool parameters
            tool_output: Tool result
            start_time: Start timestamp
            end_time: End timestamp
            success: Whether tool call succeeded
            error_message: Error if failed
            error_type: Type of error
        """
        # Track tool in current turn
        if ctx.tools_in_turn is not None:
            ctx.tools_in_turn.append(tool_name)

        duration_ms = int((end_time - start_time) * 1000)

        tool_call = ToolCallMetrics(
            execution_id=ctx.execution_id,
            turn_id=ctx.current_turn_id,
            tool_name=tool_name,
            started_at=datetime.fromtimestamp(start_time, timezone.utc).isoformat(),
            completed_at=datetime.fromtimestamp(end_time, timezone.utc).isoformat(),
            duration_ms=duration_ms,
            tool_input=tool_input,
            tool_output=tool_output,
            tool_output_size=len(tool_output) if tool_output else 0,
            success=success,
            error_message=error_message,
            error_type=error_type,
        )

        # Submit async (fire-and-forget)
        self._submit_async(tool_call, "tool_call")

    def record_task(
        self,
        ctx: ExecutionContext,
        task_description: str,
        task_number: Optional[int] = None,
        task_type: Optional[str] = None,
        status: str = "pending",
        started_at: Optional[str] = None,
    ) -> str:
        """
        Record a task creation.

        Args:
            ctx: Execution context
            task_description: Task description
            task_number: Sequential task number
            task_type: Type of task
            status: Initial status
            started_at: Start timestamp

        Returns:
            Task ID for later updates
        """
        task = TaskMetrics(
            execution_id=ctx.execution_id,
            task_number=task_number,
            task_description=task_description,
            task_type=task_type,
            status=status,
            started_at=started_at or datetime.now(timezone.utc).isoformat(),
        )

        # Submit async (fire-and-forget)
        self._submit_async(task, "task")

        # Return a synthetic task ID (in practice, you'd get this from the API response)
        return f"{ctx.execution_id}:{task_number or 0}"

    def _submit_async(self, metric: Any, metric_type: str):
        """
        Submit metric asynchronously without blocking execution.

        This uses fire-and-forget pattern - failures are logged but don't
        affect the execution flow.

        Args:
            metric: Metric data (TurnMetrics, ToolCallMetrics, or TaskMetrics)
            metric_type: Type of metric for logging
        """
        async def submit():
            try:
                if isinstance(metric, TurnMetrics):
                    await self.analytics.record_turn(metric)
                elif isinstance(metric, ToolCallMetrics):
                    await self.analytics.record_tool_call(metric)
                elif isinstance(metric, TaskMetrics):
                    await self.analytics.record_task(metric)
                else:
                    logger.error("unknown_metric_type", type=type(metric).__name__)
            except Exception as e:
                # Log error but don't re-raise - analytics failures shouldn't break execution
                logger.error(
                    "analytics_submission_failed",
                    metric_type=metric_type,
                    error=str(e),
                    execution_id=getattr(metric, "execution_id", "unknown")[:8],
                )

        # Create task and track it (for cleanup)
        task = asyncio.create_task(submit())
        self._submission_tasks.append(task)

        # Clean up completed tasks
        self._submission_tasks = [t for t in self._submission_tasks if not t.done()]

    async def wait_for_submissions(self, timeout: float = 5.0):
        """
        Wait for all pending analytics submissions to complete.

        Call this at the end of execution to ensure all analytics are submitted
        before the worker shuts down.

        Args:
            timeout: Maximum time to wait in seconds
        """
        if not self._submission_tasks:
            return

        try:
            await asyncio.wait_for(
                asyncio.gather(*self._submission_tasks, return_exceptions=True),
                timeout=timeout
            )
            logger.info(
                "analytics_submissions_completed",
                count=len(self._submission_tasks)
            )
        except asyncio.TimeoutError:
            logger.warning(
                "analytics_submissions_timeout",
                pending=len([t for t in self._submission_tasks if not t.done()])
            )
        except Exception as e:
            logger.error("analytics_wait_error", error=str(e))
        finally:
            self._submission_tasks.clear()

    def _extract_provider(self, model: str) -> str:
        """
        Extract provider from model identifier.

        Args:
            model: Model string like "claude-sonnet-4", "gpt-4", "openai/gpt-4"

        Returns:
            Provider name
        """
        model_lower = model.lower()

        if "claude" in model_lower or "anthropic" in model_lower:
            return "anthropic"
        elif "gpt" in model_lower or "openai" in model_lower:
            return "openai"
        elif "gemini" in model_lower or "google" in model_lower:
            return "google"
        elif "llama" in model_lower or "meta" in model_lower:
            return "meta"
        else:
            return "unknown"


def create_analytics_collector(control_plane_url: str, api_key: str) -> AnalyticsCollector:
    """
    Create an analytics collector instance.

    Args:
        control_plane_url: Control Plane API URL
        api_key: Kubiya API key

    Returns:
        Analytics collector instance
    """
    analytics_service = AnalyticsService(control_plane_url, api_key)
    return AnalyticsCollector(analytics_service)
