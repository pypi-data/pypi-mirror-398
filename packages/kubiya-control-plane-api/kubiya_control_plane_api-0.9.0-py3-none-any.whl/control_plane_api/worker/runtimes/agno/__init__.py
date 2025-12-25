"""
Agno runtime module for Agent Control Plane.

This module provides a refactored, production-grade Agno framework integration
with proper separation of concerns:

- runtime.py: Main AgnoRuntime class
- config.py: LiteLLM configuration builder
- hooks.py: Tool execution hooks
- utils.py: Helper functions

The Agno runtime provides:
- LiteLLM-based model execution
- Real-time tool execution hooks
- Event batching for performance
- Conversation history support
- Structured logging

Usage:
    from control_plane_api.worker.runtimes.agno import AgnoRuntime

    runtime = AgnoRuntime(
        control_plane_client=client,
        cancellation_manager=manager
    )

    result = await runtime.execute(context)
"""

from .runtime import AgnoRuntime

__all__ = ["AgnoRuntime"]

__version__ = "1.0.0"  # Refactored modular version
