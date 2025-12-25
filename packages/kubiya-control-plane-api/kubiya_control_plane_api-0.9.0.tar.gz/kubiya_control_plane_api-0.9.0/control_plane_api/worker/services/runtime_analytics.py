"""
Runtime-agnostic analytics extraction.

This module extracts analytics data from RuntimeExecutionResult objects,
working with any runtime (Agno, Claude Code, LiteLLM, etc.) that follows
the standard runtime contract.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import structlog
import time

from control_plane_api.worker.runtimes.base import RuntimeExecutionResult
from control_plane_api.worker.services.analytics_service import (
    TurnMetrics,
    ToolCallMetrics,
    AnalyticsService,
)

logger = structlog.get_logger()


class RuntimeAnalyticsExtractor:
    """
    Extracts analytics data from RuntimeExecutionResult.

    This works with any runtime that populates the standard fields:
    - usage: Token usage metrics
    - model: Model identifier
    - tool_execution_messages: Tool call tracking
    - metadata: Runtime-specific data
    """

    @staticmethod
    def extract_turn_metrics(
        result: RuntimeExecutionResult,
        execution_id: str,
        turn_number: int,
        turn_start_time: float,
        turn_end_time: Optional[float] = None,
    ) -> TurnMetrics:
        """
        Extract turn metrics from RuntimeExecutionResult.

        Works with any runtime that populates the usage field.

        Args:
            result: Runtime execution result
            execution_id: Execution ID
            turn_number: Turn sequence number
            turn_start_time: When turn started (timestamp)
            turn_end_time: When turn ended (timestamp, defaults to now)

        Returns:
            TurnMetrics ready for submission
        """
        if turn_end_time is None:
            turn_end_time = time.time()

        duration_ms = int((turn_end_time - turn_start_time) * 1000)

        # Extract usage - runtimes use different field names
        usage = result.usage or {}

        # Normalize field names from different providers
        input_tokens = (
            usage.get("input_tokens") or
            usage.get("prompt_tokens") or
            0
        )
        output_tokens = (
            usage.get("output_tokens") or
            usage.get("completion_tokens") or
            0
        )
        total_tokens = (
            usage.get("total_tokens") or
            (input_tokens + output_tokens)
        )

        # Cache tokens (Anthropic-specific, but other providers may add support)
        cache_read_tokens = usage.get("cache_read_tokens", 0)
        cache_creation_tokens = usage.get("cache_creation_tokens", 0)

        # Alternative: extract from prompt_tokens_details if present
        if "prompt_tokens_details" in usage:
            details = usage["prompt_tokens_details"]
            if isinstance(details, dict):
                cache_read_tokens = details.get("cached_tokens", cache_read_tokens)

        # Extract tool names from tool_execution_messages (needed for AEM calculation)
        tool_names = []
        tools_count = 0
        if result.tool_execution_messages:
            tool_names = [msg.get("tool") for msg in result.tool_execution_messages if msg.get("tool")]
            tools_count = len(tool_names)

        # Calculate costs
        model = result.model or "unknown"
        costs = AnalyticsService.calculate_token_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
            model=model,
        )

        # Calculate Agentic Engineering Minutes (AEM)
        aem_metrics = AnalyticsService.calculate_aem(
            duration_ms=duration_ms,
            model=model,
            tool_calls_count=tools_count,
        )

        # Extract model provider from metadata or infer from model name
        metadata = result.metadata or {}
        model_provider = metadata.get("model_provider") or RuntimeAnalyticsExtractor._infer_provider(model)

        # Response preview (first 500 chars)
        response_preview = result.response[:500] if result.response else None

        return TurnMetrics(
            execution_id=execution_id,
            turn_number=turn_number,
            model=model,
            model_provider=model_provider,
            started_at=datetime.fromtimestamp(turn_start_time, timezone.utc).isoformat(),
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
            finish_reason=result.finish_reason or "stop",
            response_preview=response_preview,
            tools_called_count=tools_count,
            tools_called_names=list(set(tool_names)),  # Unique tool names
            error_message=result.error,
            metrics=metadata,  # Include runtime-specific metrics
            # AEM metrics
            runtime_minutes=aem_metrics["runtime_minutes"],
            model_weight=aem_metrics["model_weight"],
            tool_calls_weight=aem_metrics["tool_calls_weight"],
            aem_value=aem_metrics["aem_value"],
            aem_cost=aem_metrics["aem_cost"],
        )

    @staticmethod
    def extract_tool_call_metrics(
        result: RuntimeExecutionResult,
        execution_id: str,
        turn_id: Optional[str] = None,
    ) -> List[ToolCallMetrics]:
        """
        Extract tool call metrics from RuntimeExecutionResult.

        Works with any runtime that populates tool_execution_messages.

        Args:
            result: Runtime execution result
            execution_id: Execution ID
            turn_id: Turn ID to link tool calls to

        Returns:
            List of ToolCallMetrics ready for submission
        """
        if not result.tool_execution_messages:
            return []

        tool_calls = []

        for tool_msg in result.tool_execution_messages:
            # Extract timing information
            # Runtimes should provide start_time/end_time or duration_ms
            duration_ms = tool_msg.get("duration_ms")
            start_time = tool_msg.get("start_time")
            end_time = tool_msg.get("end_time")

            # Calculate timestamps
            if start_time and end_time:
                started_at = datetime.fromtimestamp(start_time, timezone.utc).isoformat()
                completed_at = datetime.fromtimestamp(end_time, timezone.utc).isoformat()
                if duration_ms is None:
                    duration_ms = int((end_time - start_time) * 1000)
            else:
                # Fallback to current time if not provided
                now = datetime.now(timezone.utc).isoformat()
                started_at = now
                completed_at = now

            # Extract tool output
            tool_output = tool_msg.get("output") or tool_msg.get("result")
            if tool_output and not isinstance(tool_output, str):
                tool_output = str(tool_output)

            # Success status
            success = tool_msg.get("success", True)

            tool_call = ToolCallMetrics(
                execution_id=execution_id,
                turn_id=turn_id,
                tool_name=tool_msg.get("tool", "unknown"),
                tool_use_id=tool_msg.get("tool_use_id"),
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                tool_input=tool_msg.get("input"),
                tool_output=tool_output,
                tool_output_size=len(tool_output) if tool_output else 0,
                success=success,
                error_message=tool_msg.get("error"),
                error_type=tool_msg.get("error_type"),
                metadata=tool_msg.get("metadata", {}),
            )

            tool_calls.append(tool_call)

        return tool_calls

    @staticmethod
    def _infer_provider(model: str) -> str:
        """
        Infer provider from model identifier.

        Args:
            model: Model string

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
        elif "mistral" in model_lower:
            return "mistral"
        elif "command" in model_lower or "cohere" in model_lower:
            return "cohere"
        else:
            return "unknown"


async def submit_runtime_analytics(
    result: RuntimeExecutionResult,
    execution_id: str,
    turn_number: int,
    turn_start_time: float,
    analytics_service: AnalyticsService,
    turn_end_time: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Extract and submit all analytics from a RuntimeExecutionResult.

    This is the main entry point for submitting analytics after a runtime execution.
    It extracts turn metrics and tool call metrics and submits them asynchronously.

    Args:
        result: Runtime execution result
        execution_id: Execution ID
        turn_number: Turn sequence number
        turn_start_time: When turn started
        analytics_service: Analytics service instance
        turn_end_time: When turn ended (defaults to now)

    Returns:
        Dict with submission status
    """
    try:
        # Extract turn metrics
        turn_metrics = RuntimeAnalyticsExtractor.extract_turn_metrics(
            result=result,
            execution_id=execution_id,
            turn_number=turn_number,
            turn_start_time=turn_start_time,
            turn_end_time=turn_end_time,
        )

        # Submit turn metrics
        await analytics_service.record_turn(turn_metrics)

        # Extract and submit tool call metrics
        tool_call_metrics = RuntimeAnalyticsExtractor.extract_tool_call_metrics(
            result=result,
            execution_id=execution_id,
            turn_id=None,  # Could link to turn ID if available
        )

        for tool_call in tool_call_metrics:
            await analytics_service.record_tool_call(tool_call)

        logger.info(
            "runtime_analytics_submitted",
            execution_id=execution_id[:8],
            turn_number=turn_number,
            tokens=turn_metrics.total_tokens,
            cost=turn_metrics.total_cost,
            tool_calls=len(tool_call_metrics),
        )

        return {
            "success": True,
            "turn_submitted": True,
            "tool_calls_submitted": len(tool_call_metrics),
        }

    except Exception as e:
        logger.error(
            "runtime_analytics_submission_failed",
            error=str(e),
            execution_id=execution_id[:8],
        )
        return {
            "success": False,
            "error": str(e),
        }
