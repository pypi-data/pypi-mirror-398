"""Workflow Executor skill implementation for agno runtime."""
from control_plane_api.worker.services.workflow_executor_tools import WorkflowExecutorTools as BaseWorkflowExecutorTools
from control_plane_api.worker.skills.builtin.schema_fix_mixin import SchemaFixMixin



class WorkflowExecutorTools(BaseWorkflowExecutorTools):
    """
    Workflow executor tools using existing WorkflowExecutorTools.

    Wraps the existing workflow executor implementation.
    """

    def __init__(
        self,
        workflows: list = None,
        workflow_type: str = None,
        workflow_definition: str = None,
        python_dsl_code: str = None,
        validation_enabled: bool = True,
        default_runner: str = None,
        timeout: int = 3600,
        default_parameters: dict = None,
        kubiya_api_key: str = None,
        kubiya_api_base: str = None,
        execution_id: str = None,
        **kwargs
    ):
        """
        Initialize workflow executor tools.

        Args:
            workflows: Collection of workflow definitions
            workflow_type: LEGACY - Workflow type (json or python_dsl)
            workflow_definition: LEGACY - JSON workflow definition
            python_dsl_code: LEGACY - Python DSL code
            validation_enabled: Enable validation
            default_runner: Default runner/environment
            timeout: Execution timeout
            default_parameters: Default parameters
            kubiya_api_key: Kubiya API key
            kubiya_api_base: Kubiya API base URL
            execution_id: Execution ID for streaming
            **kwargs: Additional configuration
        """
        # Import os here to get env vars if not provided
        import os

        super().__init__(
            name=kwargs.get("name", "workflow-executor"),
            workflows=workflows or [],
            workflow_type=workflow_type,
            workflow_definition=workflow_definition,
            python_dsl_code=python_dsl_code,
            validation_enabled=validation_enabled,
            default_runner=default_runner,
            timeout=timeout,
            default_parameters=default_parameters,
            kubiya_api_key=kubiya_api_key or os.environ.get("KUBIYA_API_KEY"),
            kubiya_api_base=kubiya_api_base or os.environ.get("KUBIYA_API_BASE", "https://api.kubiya.ai"),
            execution_id=execution_id,
        )
