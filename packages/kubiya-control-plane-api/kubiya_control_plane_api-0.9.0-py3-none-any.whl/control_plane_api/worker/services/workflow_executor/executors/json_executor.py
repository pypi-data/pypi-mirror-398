"""
JSON workflow executor.

This module implements workflow execution for JSON-defined workflows.
"""

import structlog
from typing import Any

from .base import BaseWorkflowExecutor
from ..models import WorkflowExecutionContext

logger = structlog.get_logger()


class JsonWorkflowExecutor(BaseWorkflowExecutor):
    """
    Executor for JSON-defined workflows.

    Executes workflows defined in JSON format using the Kubiya SDK.
    """

    def _execute_workflow(self, context: WorkflowExecutionContext) -> Any:
        """
        Execute JSON workflow and return event stream.

        Args:
            context: Workflow execution context

        Returns:
            Iterable event stream from Kubiya SDK

        Raises:
            Exception: If workflow execution fails
        """
        logger.info(
            "executing_json_workflow",
            workflow_name=context.workflow_config.name,
            runner=context.workflow_config.runner,
            execution_id=context.execution_id[:8]
        )

        # Execute workflow using Kubiya SDK
        response = self.kubiya_client.execute_workflow(
            workflow_definition=context.workflow_config.definition,
            parameters=context.workflow_config.parameters,
            stream=True
        )

        return response
