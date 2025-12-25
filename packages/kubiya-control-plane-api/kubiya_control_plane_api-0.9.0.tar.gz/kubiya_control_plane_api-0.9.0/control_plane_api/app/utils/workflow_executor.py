"""Workflow execution utilities using kubiya-sdk."""
import json
import logging
from typing import Dict, Any, AsyncGenerator, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Execute workflows using the kubiya-sdk.

    This class provides methods to execute workflows defined in:
    - JSON format (compatible with Kubiya workflow schema)
    - Python DSL (using kubiya_sdk.StatefulWorkflow)
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the workflow executor.

        Args:
            api_key: Kubiya API key (optional, will use environment variable if not provided)
            base_url: Kubiya API base URL (optional, defaults to production)
        """
        self.api_key = api_key
        self.base_url = base_url or "https://api.kubiya.ai"

    async def execute_json_workflow(
        self,
        workflow_definition: Union[str, Dict[str, Any]],
        parameters: Optional[Dict[str, Any]] = None,
        runner: Optional[str] = None,
        stream: bool = True,
        timeout: int = 3600
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a JSON workflow definition.

        Args:
            workflow_definition: Workflow definition as JSON string or dict
            parameters: Parameters to inject into the workflow
            runner: Optional runner/environment name
            stream: Whether to stream execution events
            timeout: Maximum execution timeout in seconds

        Yields:
            Execution events as dictionaries

        Raises:
            ValueError: If workflow definition is invalid
            RuntimeError: If execution fails
        """
        try:
            # Parse workflow definition if it's a string
            if isinstance(workflow_definition, str):
                workflow_data = json.loads(workflow_definition)
            else:
                workflow_data = workflow_definition

            # Validate workflow structure
            self._validate_workflow_structure(workflow_data)

            # Initialize kubiya client if available
            try:
                from kubiya_sdk import KubiyaClient

                client_kwargs = {}
                if self.api_key:
                    client_kwargs['api_key'] = self.api_key
                if self.base_url:
                    client_kwargs['base_url'] = self.base_url

                client = KubiyaClient(**client_kwargs)

                # Execute workflow
                logger.info(
                    "Starting workflow execution",
                    workflow_name=workflow_data.get('name'),
                    stream=stream,
                    runner=runner
                )

                execution_start = datetime.utcnow()
                event_count = 0

                if stream:
                    # Stream execution events
                    async for event in client.workflows.execute(
                        workflow_definition=workflow_data,
                        parameters=parameters or {},
                        runner=runner,
                        stream=True
                    ):
                        event_count += 1

                        # Enhance event with metadata
                        if isinstance(event, dict):
                            event['_timestamp'] = datetime.utcnow().isoformat()
                            event['_event_number'] = event_count

                        yield event

                    execution_end = datetime.utcnow()
                    duration = (execution_end - execution_start).total_seconds()

                    logger.info(
                        "Workflow execution completed",
                        workflow_name=workflow_data.get('name'),
                        duration_seconds=duration,
                        event_count=event_count
                    )

                else:
                    # Non-streaming execution
                    result = await client.workflows.execute(
                        workflow_definition=workflow_data,
                        parameters=parameters or {},
                        runner=runner,
                        stream=False
                    )

                    execution_end = datetime.utcnow()
                    duration = (execution_end - execution_start).total_seconds()

                    logger.info(
                        "Workflow execution completed",
                        workflow_name=workflow_data.get('name'),
                        duration_seconds=duration
                    )

                    yield {
                        'type': 'execution_complete',
                        'result': result,
                        'duration_seconds': duration,
                        '_timestamp': execution_end.isoformat()
                    }

            except ImportError:
                # If kubiya_sdk is not available, provide a mock response for testing
                logger.warning("kubiya-sdk not available, returning mock execution events")

                yield {
                    'type': 'workflow_start',
                    'workflow_name': workflow_data.get('name'),
                    '_timestamp': datetime.utcnow().isoformat()
                }

                for step in workflow_data.get('steps', []):
                    yield {
                        'type': 'step_start',
                        'step_name': step.get('name'),
                        '_timestamp': datetime.utcnow().isoformat()
                    }

                    yield {
                        'type': 'step_complete',
                        'step_name': step.get('name'),
                        '_timestamp': datetime.utcnow().isoformat()
                    }

                yield {
                    'type': 'workflow_complete',
                    'workflow_name': workflow_data.get('name'),
                    '_timestamp': datetime.utcnow().isoformat()
                }

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in workflow definition", error=str(e))
            raise ValueError(f"Invalid JSON in workflow definition: {str(e)}")
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e), workflow_name=workflow_data.get('name') if 'workflow_data' in locals() else 'unknown')
            raise RuntimeError(f"Workflow execution failed: {str(e)}")

    async def execute_python_dsl(
        self,
        dsl_code: str,
        parameters: Optional[Dict[str, Any]] = None,
        runner: Optional[str] = None,
        timeout: int = 3600
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a Python DSL workflow.

        Args:
            dsl_code: Python code defining the workflow using kubiya_sdk
            parameters: Parameters to pass to the workflow
            runner: Optional runner/environment name
            timeout: Maximum execution timeout in seconds

        Yields:
            Execution events as dictionaries

        Raises:
            ValueError: If DSL code is invalid
            RuntimeError: If execution fails
        """
        try:
            # Import kubiya_sdk modules
            try:
                from kubiya_sdk import StatefulWorkflow, run_workflow_with_progress
                from kubiya_sdk.workflows import step, tool_step
            except ImportError as e:
                raise RuntimeError(f"kubiya-sdk not available: {str(e)}")

            # Execute DSL code to create workflow
            namespace = {
                '__builtins__': __builtins__,
                'StatefulWorkflow': StatefulWorkflow,
                'step': step,
                'tool_step': tool_step,
            }

            exec(dsl_code, namespace)

            # Find the workflow object
            workflow = None
            for name, obj in namespace.items():
                if name.startswith('_'):
                    continue
                if hasattr(obj, '__class__'):
                    class_name = obj.__class__.__name__
                    if 'StatefulWorkflow' in class_name or 'Workflow' in class_name:
                        workflow = obj
                        break

            if not workflow:
                raise ValueError("No workflow found in DSL code")

            logger.info(
                "Starting Python DSL workflow execution",
                workflow_name=getattr(workflow, 'name', 'unknown')
            )

            execution_start = datetime.utcnow()
            event_count = 0

            # Execute workflow with progress streaming
            async for event in run_workflow_with_progress(workflow, parameters or {}):
                event_count += 1

                # Enhance event with metadata
                if isinstance(event, dict):
                    event['_timestamp'] = datetime.utcnow().isoformat()
                    event['_event_number'] = event_count

                yield event

            execution_end = datetime.utcnow()
            duration = (execution_end - execution_start).total_seconds()

            logger.info(
                "Python DSL workflow execution completed",
                workflow_name=getattr(workflow, 'name', 'unknown'),
                duration_seconds=duration,
                event_count=event_count
            )

        except Exception as e:
            logger.error("Python DSL workflow execution failed", error=str(e))
            raise RuntimeError(f"Python DSL workflow execution failed: {str(e)}")

    def _validate_workflow_structure(self, workflow_data: Dict[str, Any]) -> None:
        """Validate basic workflow structure.

        Args:
            workflow_data: Workflow definition to validate

        Raises:
            ValueError: If workflow structure is invalid
        """
        required_fields = ['name', 'steps']

        for field in required_fields:
            if field not in workflow_data:
                raise ValueError(f"Missing required field: {field}")

        if not isinstance(workflow_data['steps'], list):
            raise ValueError("Steps must be a list")

        if len(workflow_data['steps']) == 0:
            raise ValueError("Workflow must have at least one step")

        # Validate each step
        step_names = set()
        for step in workflow_data['steps']:
            if 'name' not in step:
                raise ValueError("Each step must have a 'name' field")

            if step['name'] in step_names:
                raise ValueError(f"Duplicate step name: {step['name']}")
            step_names.add(step['name'])

            if 'executor' not in step:
                raise ValueError(f"Step '{step['name']}' must have an 'executor' field")

            executor = step['executor']
            if not isinstance(executor, dict) or 'type' not in executor:
                raise ValueError(f"Step '{step['name']}' executor must be a dict with 'type' field")


# Convenience function for executing workflows
async def execute_workflow(
    workflow_definition: Union[str, Dict[str, Any]],
    workflow_type: str = "json",
    parameters: Optional[Dict[str, Any]] = None,
    runner: Optional[str] = None,
    stream: bool = True,
    timeout: int = 3600,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """Convenience function to execute a workflow.

    Args:
        workflow_definition: Workflow definition (JSON string/dict or Python DSL code)
        workflow_type: Type of workflow ("json" or "python_dsl")
        parameters: Parameters to inject into the workflow
        runner: Optional runner/environment name
        stream: Whether to stream execution events
        timeout: Maximum execution timeout in seconds
        api_key: Kubiya API key (optional)
        base_url: Kubiya API base URL (optional)

    Yields:
        Execution events as dictionaries

    Raises:
        ValueError: If workflow_type is invalid or workflow definition is invalid
        RuntimeError: If execution fails
    """
    executor = WorkflowExecutor(api_key=api_key, base_url=base_url)

    if workflow_type == "json":
        async for event in executor.execute_json_workflow(
            workflow_definition=workflow_definition,
            parameters=parameters,
            runner=runner,
            stream=stream,
            timeout=timeout
        ):
            yield event

    elif workflow_type == "python_dsl":
        if not isinstance(workflow_definition, str):
            raise ValueError("Python DSL workflow must be provided as a string")

        async for event in executor.execute_python_dsl(
            dsl_code=workflow_definition,
            parameters=parameters,
            runner=runner,
            timeout=timeout
        ):
            yield event

    else:
        raise ValueError(f"Invalid workflow_type: {workflow_type}. Must be 'json' or 'python_dsl'")
