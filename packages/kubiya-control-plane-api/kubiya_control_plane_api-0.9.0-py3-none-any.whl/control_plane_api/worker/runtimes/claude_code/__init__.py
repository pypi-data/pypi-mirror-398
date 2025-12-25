"""
Claude Code runtime module for Agent Control Plane.

This module provides a refactored, production-grade Claude Code SDK integration
with proper separation of concerns:

- runtime.py: Main runtime class
- config.py: Configuration builder
- tool_mapper.py: Skill to tool mapping
- mcp_builder.py: MCP server construction
- hooks.py: Tool execution hooks
- utils.py: Helper functions

All 7 critical bugs have been fixed:
1. Added metadata = {} initialization
2. Replaced print() with logger.debug()
3. Made MCP fallback patterns explicit
4. Added session_id validation
5. Added explicit disconnect() calls
6. Added tool name validation
7. Removed debug output

Usage:
    from control_plane_api.worker.runtimes.claude_code import ClaudeCodeRuntime

    runtime = ClaudeCodeRuntime(
        control_plane_client=client,
        cancellation_manager=manager
    )

    result = await runtime.execute(context)
"""

from .runtime import ClaudeCodeRuntime

__all__ = ["ClaudeCodeRuntime"]

__version__ = "2.0.0"  # Refactored version with all bug fixes
