"""
Runtime abstraction layer for agent execution.

This package provides a pluggable runtime system that allows agents to be
powered by different frameworks (Agno, Claude Code SDK, etc.) without changing
the core workflow and activity logic.
"""

from .base import (
    RuntimeType,
    RuntimeExecutionResult,
    RuntimeExecutionContext,
    RuntimeCapabilities,
    BaseRuntime,
    RuntimeRegistry,
)
from .factory import RuntimeFactory
from .agno import AgnoRuntime
from .claude_code import ClaudeCodeRuntime

# Backward compatibility: DefaultRuntime is now AgnoRuntime
DefaultRuntime = AgnoRuntime

__all__ = [
    "RuntimeType",
    "RuntimeExecutionResult",
    "RuntimeExecutionContext",
    "RuntimeCapabilities",
    "BaseRuntime",
    "RuntimeRegistry",
    "RuntimeFactory",
    "AgnoRuntime",
    "DefaultRuntime",  # Backward compatibility alias
    "ClaudeCodeRuntime",
]
