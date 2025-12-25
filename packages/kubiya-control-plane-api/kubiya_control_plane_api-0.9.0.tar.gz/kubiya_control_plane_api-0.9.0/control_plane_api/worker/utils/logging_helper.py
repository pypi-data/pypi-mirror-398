"""Unified logging helper for clear and structured logs across the worker.

This module provides consistent logging utilities to make logs easy to read and understand.
"""

import structlog
from typing import Optional, Dict, Any
from datetime import datetime


class ExecutionLogger:
    """Unified logger for execution workflows with clear, human-readable output."""

    def __init__(self, logger_name: str = "worker"):
        self.logger = structlog.get_logger(logger_name)

    @staticmethod
    def _format_execution_id(execution_id: str) -> str:
        """Format execution ID for display (show first 8 chars)."""
        if not execution_id:
            return "unknown"
        return execution_id[:8] if len(execution_id) > 8 else execution_id

    @staticmethod
    def _get_emoji(status: str) -> str:
        """Get emoji for status."""
        emoji_map = {
            "started": "🚀",
            "running": "⚙️",
            "streaming": "📡",
            "waiting": "⏳",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🛑",
            "retry": "🔄",
            "warning": "⚠️",
            "info": "ℹ️",
        }
        return emoji_map.get(status.lower(), "•")

    def execution_started(
        self,
        execution_id: str,
        agent_id: Optional[str] = None,
        model: Optional[str] = None,
        runtime: Optional[str] = None,
    ):
        """Log execution start."""
        exec_short = self._format_execution_id(execution_id)
        msg = f"🚀 Execution Started: {exec_short}"

        details = []
        if agent_id:
            details.append(f"agent={agent_id[:8]}")
        if model:
            details.append(f"model={model}")
        if runtime:
            details.append(f"runtime={runtime}")

        if details:
            msg += f" ({', '.join(details)})"

        self.logger.info(msg, execution_id=execution_id)

        # Print clear separator to distinguish between executions
        print(f"\n{'─' * 80}")
        print(f"🚀 Execution Started: {exec_short}")
        if details:
            print(f"   {' | '.join(details)}")
        print(f"{'─' * 80}")

    def execution_completed(self, execution_id: str, duration_ms: Optional[int] = None):
        """Log execution completion."""
        exec_short = self._format_execution_id(execution_id)
        msg = f"✅ Execution Completed: {exec_short}"

        if duration_ms:
            duration_sec = duration_ms / 1000
            msg += f" (took {duration_sec:.2f}s)"

        self.logger.info(msg, execution_id=execution_id)

        # Print clear end separator
        print(f"\n{'─' * 80}")
        print(msg)
        print(f"{'─' * 80}\n")

    def execution_failed(
        self,
        execution_id: str,
        error: str,
        error_type: Optional[str] = None,
        recoverable: bool = False,
    ):
        """Log execution failure."""
        exec_short = self._format_execution_id(execution_id)

        if recoverable:
            msg = f"⚠️  Execution Error (Recoverable): {exec_short}"
        else:
            msg = f"❌ Execution Failed: {exec_short}"

        self.logger.error(
            msg,
            execution_id=execution_id,
            error=error,
            error_type=error_type,
        )

        # Print clear failure separator
        print(f"\n{'─' * 80}")
        print(msg)
        if error_type:
            print(f"   Error Type: {error_type}")
        print(f"   Error: {error}")
        print(f"{'─' * 80}\n")

    def activity_started(
        self,
        activity_name: str,
        execution_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log activity start."""
        exec_short = self._format_execution_id(execution_id)
        msg = f"⚙️  {activity_name}: {exec_short}"

        if details:
            detail_str = ", ".join([f"{k}={v}" for k, v in details.items()])
            msg += f" ({detail_str})"

        self.logger.info(msg, execution_id=execution_id, activity=activity_name)
        print(f"  → {msg}")

    def activity_completed(
        self,
        activity_name: str,
        execution_id: str,
        result: Optional[str] = None,
    ):
        """Log activity completion."""
        exec_short = self._format_execution_id(execution_id)
        msg = f"✅ {activity_name}: {exec_short}"

        if result:
            msg += f" - {result}"

        self.logger.info(msg, execution_id=execution_id, activity=activity_name)
        print(f"  ✓ {msg}")

    def activity_failed(
        self,
        activity_name: str,
        execution_id: str,
        error: str,
        will_retry: bool = False,
    ):
        """Log activity failure."""
        exec_short = self._format_execution_id(execution_id)

        if will_retry:
            msg = f"🔄 {activity_name} Failed (Retrying): {exec_short}"
        else:
            msg = f"❌ {activity_name} Failed: {exec_short}"

        self.logger.error(
            msg,
            execution_id=execution_id,
            activity=activity_name,
            error=error,
        )
        print(f"  ✗ {msg}")
        print(f"    Error: {error}")

    def streaming_started(self, execution_id: str):
        """Log streaming start."""
        exec_short = self._format_execution_id(execution_id)
        msg = f"📡 Streaming Response: {exec_short}"
        self.logger.info(msg, execution_id=execution_id)
        print(f"  → {msg}")

    def streaming_progress(
        self,
        execution_id: str,
        chunks_received: int,
        response_length: int,
    ):
        """Log streaming progress (only at milestones)."""
        exec_short = self._format_execution_id(execution_id)

        # Only log at milestones to avoid spam
        if chunks_received % 50 == 0 or chunks_received < 5:
            msg = f"📡 Streaming: {exec_short} - {chunks_received} chunks, {response_length} chars"
            self.logger.debug(msg, execution_id=execution_id)
            # Only print for first few chunks or milestones
            if chunks_received < 5:
                print(f"    {msg}")

    def status_update(
        self,
        execution_id: str,
        old_status: Optional[str],
        new_status: str,
        reason: Optional[str] = None,
    ):
        """Log status update."""
        exec_short = self._format_execution_id(execution_id)
        emoji = self._get_emoji(new_status)

        if old_status:
            msg = f"{emoji} Status Change: {exec_short} ({old_status} → {new_status})"
        else:
            msg = f"{emoji} Status: {exec_short} ({new_status})"

        if reason:
            msg += f" - {reason}"

        self.logger.info(msg, execution_id=execution_id, status=new_status)
        print(f"  {msg}")

    def workflow_signal(
        self,
        execution_id: str,
        signal_name: str,
        details: Optional[str] = None,
    ):
        """Log workflow signal received."""
        exec_short = self._format_execution_id(execution_id)
        msg = f"📨 Signal Received: {exec_short} ({signal_name})"

        if details:
            msg += f" - {details}"

        self.logger.info(msg, execution_id=execution_id, signal=signal_name)
        print(f"  {msg}")

    def turn_started(self, execution_id: str, turn_number: int):
        """Log conversation turn start."""
        exec_short = self._format_execution_id(execution_id)
        msg = f"💬 Turn {turn_number} Started: {exec_short}"
        self.logger.info(msg, execution_id=execution_id, turn=turn_number)
        print(f"\n  {msg}")

    def turn_completed(
        self,
        execution_id: str,
        turn_number: int,
        tokens_used: Optional[int] = None,
    ):
        """Log conversation turn completion."""
        exec_short = self._format_execution_id(execution_id)
        msg = f"💬 Turn {turn_number} Completed: {exec_short}"

        if tokens_used:
            msg += f" ({tokens_used} tokens)"

        self.logger.info(msg, execution_id=execution_id, turn=turn_number)
        print(f"  {msg}")

    def tool_call_started(
        self,
        execution_id: str,
        tool_name: str,
        tool_id: Optional[str] = None,
    ):
        """Log tool call start."""
        exec_short = self._format_execution_id(execution_id)
        msg = f"🔧 Tool Called: {tool_name}"

        if tool_id:
            msg += f" (id: {tool_id[:8]})"

        self.logger.info(
            msg,
            execution_id=execution_id,
            tool_name=tool_name,
            tool_id=tool_id,
        )
        print(f"    → {msg}")

    def tool_call_completed(
        self,
        execution_id: str,
        tool_name: str,
        success: bool,
        duration_ms: Optional[int] = None,
    ):
        """Log tool call completion."""
        exec_short = self._format_execution_id(execution_id)

        if success:
            emoji = "✅"
            status = "completed"
        else:
            emoji = "❌"
            status = "failed"

        msg = f"{emoji} Tool {status}: {tool_name}"

        if duration_ms:
            msg += f" (took {duration_ms}ms)"

        self.logger.info(
            msg,
            execution_id=execution_id,
            tool_name=tool_name,
            success=success,
        )
        print(f"    {msg}")

    def warning(self, execution_id: str, message: str, details: Optional[Dict] = None):
        """Log warning."""
        exec_short = self._format_execution_id(execution_id)
        msg = f"⚠️  Warning: {exec_short} - {message}"

        self.logger.warning(msg, execution_id=execution_id, **(details or {}))
        print(f"  {msg}")

    def debug(self, execution_id: str, message: str):
        """Log debug message (only in debug mode)."""
        exec_short = self._format_execution_id(execution_id)
        self.logger.debug(message, execution_id=execution_id)


# Global logger instance
execution_logger = ExecutionLogger()
