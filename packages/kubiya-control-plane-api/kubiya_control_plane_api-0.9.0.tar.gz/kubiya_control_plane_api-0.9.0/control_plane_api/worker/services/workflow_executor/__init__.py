"""
Workflow Executor Skill

A well-architected skill for executing workflows from agent control plane.

This package provides:
- Type-safe Pydantic models for configurations and events
- Proper separation of concerns with dedicated components
- Strategy pattern for different workflow types
- Event-driven architecture for real-time streaming
- Comprehensive error handling and logging

Architecture:
- models.py: Pydantic models for type safety
- event_publisher.py: Publishes events to control plane
- event_processor.py: Processes streaming events from SDK
- executors/: Strategy pattern for workflow execution
  - base.py: Abstract base executor (template method pattern)
  - json_executor.py: JSON workflow execution
  - python_executor.py: Python DSL workflow execution

Usage:
    from control_plane_api.worker.services.workflow_executor import WorkflowExecutorTools

    # This will be the main skill class that agents use
"""

from .models import (
    WorkflowConfig,
    WorkflowExecutionContext,
    WorkflowEvent,
    WorkflowResult,
)
from .event_publisher import WorkflowEventPublisher
from .event_processor import WorkflowEventProcessor
from .executors import (
    BaseWorkflowExecutor,
    JsonWorkflowExecutor,
    PythonWorkflowExecutor,
)

__all__ = [
    "WorkflowConfig",
    "WorkflowExecutionContext",
    "WorkflowEvent",
    "WorkflowResult",
    "WorkflowEventPublisher",
    "WorkflowEventProcessor",
    "BaseWorkflowExecutor",
    "JsonWorkflowExecutor",
    "PythonWorkflowExecutor",
]
