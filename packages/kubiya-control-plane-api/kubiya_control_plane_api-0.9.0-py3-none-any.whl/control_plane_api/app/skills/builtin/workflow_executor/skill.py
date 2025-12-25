"""Workflow Executor Skill - Execute workflows defined via JSON or Python DSL."""
import json
import sys
import traceback
from io import StringIO
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant, SkillRequirements


class WorkflowStepConfig(BaseModel):
    """Configuration for a workflow step."""
    name: str = Field(..., description="Step name")
    description: Optional[str] = Field(None, description="Step description")
    executor: Dict[str, Any] = Field(..., description="Executor configuration (type, config)")
    depends_on: Optional[List[str]] = Field(None, description="Step dependencies")


class WorkflowTriggerConfig(BaseModel):
    """Configuration for a workflow trigger."""
    type: str = Field(..., description="Trigger type (manual, cron, webhook)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Trigger configuration")
    runner: Optional[str] = Field(None, description="Runner/environment name")


class WorkflowDefinitionConfig(BaseModel):
    """Workflow definition in JSON format."""
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    steps: List[Dict[str, Any]] = Field(..., min_items=1, description="Workflow steps")
    triggers: Optional[List[Dict[str, Any]]] = Field(None, description="Workflow triggers")
    runner: Optional[str] = Field(None, description="Default runner/environment")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameter schema - defines available parameters (name, type, description). Agent fills values dynamically at runtime."
    )

    @validator('steps')
    def validate_steps(cls, steps):
        """Validate that steps have required fields."""
        if not steps:
            raise ValueError("Workflow must have at least one step")

        step_names = set()
        for step in steps:
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

        return steps


class WorkflowExecutorConfiguration(BaseModel):
    """Configuration for the Workflow Executor skill."""

    workflows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Collection of workflow definitions. Each workflow becomes a separate tool."
    )

    validation_enabled: bool = Field(
        True,
        description="Enable workflow validation before saving"
    )

    default_runner: Optional[str] = Field(
        None,
        description="Default runner/environment for workflow execution"
    )

    timeout: int = Field(
        3600,
        ge=30,
        le=7200,
        description="Maximum workflow execution timeout in seconds (30s - 2h)"
    )

    default_parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Default parameter values (optional). Used only if agent doesn't provide values at runtime."
    )

    # Legacy fields for backwards compatibility
    workflow_type: Optional[str] = Field(
        None,
        description="LEGACY: Type of workflow definition: 'json' or 'python_dsl'"
    )

    workflow_definition: Optional[str] = Field(
        None,
        description="LEGACY: JSON workflow definition as a string"
    )

    python_dsl_code: Optional[str] = Field(
        None,
        description="LEGACY: Python DSL code for workflow definition"
    )

    @validator('workflows')
    def validate_workflows(cls, v, values):
        """Validate workflows collection."""
        if not v:
            # Check if using legacy fields
            if values.get('workflow_definition') or values.get('python_dsl_code'):
                return v  # Allow empty if using legacy mode
            raise ValueError("At least one workflow must be defined in 'workflows' array")

        validation_enabled = values.get('validation_enabled', True)

        workflow_names = set()
        for idx, workflow in enumerate(v):
            # Each workflow must have required fields
            if 'name' not in workflow:
                raise ValueError(f"Workflow at index {idx} missing 'name' field")

            if 'type' not in workflow:
                raise ValueError(f"Workflow '{workflow['name']}' missing 'type' field (json or python_dsl)")

            # Check for duplicate names
            name = workflow['name']
            if name in workflow_names:
                raise ValueError(f"Duplicate workflow name: {name}")
            workflow_names.add(name)

            # Validate based on type
            wf_type = workflow['type']
            if wf_type not in ['json', 'python_dsl']:
                raise ValueError(f"Workflow '{name}' has invalid type: {wf_type}")

            if wf_type == 'json':
                if 'definition' not in workflow:
                    raise ValueError(f"JSON workflow '{name}' missing 'definition' field")

                if validation_enabled:
                    try:
                        # Validate JSON structure
                        if isinstance(workflow['definition'], str):
                            workflow_data = json.loads(workflow['definition'])
                        else:
                            workflow_data = workflow['definition']

                        # Validate using WorkflowDefinitionConfig
                        WorkflowDefinitionConfig(**workflow_data)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Workflow '{name}' has invalid JSON: {str(e)}")
                    except Exception as e:
                        raise ValueError(f"Workflow '{name}' validation failed: {str(e)}")

            elif wf_type == 'python_dsl':
                if 'code' not in workflow:
                    raise ValueError(f"Python DSL workflow '{name}' missing 'code' field")

                if validation_enabled:
                    try:
                        compile(workflow['code'], f'<workflow:{name}>', 'exec')
                    except SyntaxError as e:
                        raise ValueError(f"Workflow '{name}' has invalid Python syntax: {str(e)}")

        return v

    @validator('workflow_type')
    def validate_workflow_type(cls, v):
        """Validate workflow type (legacy)."""
        if v and v not in ['json', 'python_dsl']:
            raise ValueError("workflow_type must be 'json' or 'python_dsl'")
        return v

    @validator('workflow_definition')
    def validate_workflow_definition(cls, v, values):
        """Validate JSON workflow definition (legacy)."""
        if v and values.get('validation_enabled', True):
            try:
                workflow_data = json.loads(v)
                # Validate using WorkflowDefinitionConfig
                WorkflowDefinitionConfig(**workflow_data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in workflow_definition: {str(e)}")
            except Exception as e:
                raise ValueError(f"Invalid workflow definition: {str(e)}")
        return v

    @validator('python_dsl_code')
    def validate_python_dsl_code(cls, v, values):
        """Validate Python DSL code (legacy)."""
        if v and values.get('validation_enabled', True):
            try:
                compile(v, '<workflow>', 'exec')
            except SyntaxError as e:
                raise ValueError(f"Invalid Python syntax in DSL code: {str(e)}")
        return v


class WorkflowExecutorSkill(SkillDefinition):
    """Workflow Executor Skill - Execute workflows defined via JSON or Python DSL.

    This skill allows defining and executing workflows using either:
    1. JSON workflow definitions with steps and executors
    2. Python DSL using the kubiya-sdk

    Workflows are validated before saving and can be executed via the control plane.
    """

    @property
    def type(self) -> SkillType:
        """Return the skill type."""
        return SkillType.WORKFLOW_EXECUTOR

    @property
    def name(self) -> str:
        """Return the skill name."""
        return "Workflow Executor"

    @property
    def description(self) -> str:
        """Return the skill description."""
        return (
            "Execute workflows defined via JSON or Python DSL. "
            "Supports complex multi-step workflows with dependencies, "
            "conditional execution, and various executor types."
        )

    @property
    def icon(self) -> str:
        """Return the skill icon."""
        return "Workflow"

    @property
    def icon_type(self) -> str:
        """Return the icon type."""
        return "lucide"

    def get_variants(self) -> List[SkillVariant]:
        """Return single workflow executor variant with empty configuration for user to fill."""
        return [
            SkillVariant(
                id="workflow_executor",
                name="Workflow Executor",
                description="Execute workflows with dynamic parameters. Agent fills parameter values at runtime based on user requests.",
                category=SkillCategory.ADVANCED,
                configuration={
                    "workflows": [
                        {
                            "name": "deploy-app",
                            "type": "json",
                            "definition": {
                                "name": "deploy-app",
                                "description": "Deploy application to specified environment",
                                "runner": "kubiya-prod",
                                "parameters": {
                                    "app_name": {
                                        "type": "string",
                                        "description": "Application name to deploy"
                                    },
                                    "environment": {
                                        "type": "string",
                                        "description": "Target environment (dev, staging, prod)"
                                    },
                                    "version": {
                                        "type": "string",
                                        "description": "Version to deploy"
                                    }
                                },
                                "steps": [
                                    {
                                        "name": "deploy",
                                        "description": "Deploy application",
                                        "executor": {
                                            "type": "shell",
                                            "config": {
                                                "command": "kubectl apply -f deploy.yaml --namespace={{environment}} && kubectl set image deployment/{{app_name}} app={{app_name}}:{{version}}"
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    ],
                    "validation_enabled": True,
                    "default_runner": "kubiya-prod",
                    "timeout": 3600,
                    "default_parameters": {
                        "environment": "staging"
                    }
                },
                icon="Workflow",
                is_default=True
            )
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the workflow executor configuration.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validated and normalized configuration

        Raises:
            ValueError: If configuration is invalid
        """
        try:
            # Use Pydantic model for validation
            validated = WorkflowExecutorConfiguration(**config)

            # Additional validation for workflow execution
            if validated.workflow_type == 'json' and validated.workflow_definition:
                workflow_data = json.loads(validated.workflow_definition)
                # Ensure step dependencies are valid
                step_names = {step['name'] for step in workflow_data.get('steps', [])}
                for step in workflow_data.get('steps', []):
                    depends_on = step.get('depends_on', [])
                    if depends_on:
                        for dep in depends_on:
                            if dep not in step_names:
                                raise ValueError(
                                    f"Step '{step['name']}' depends on non-existent step: {dep}"
                                )

            elif validated.workflow_type == 'python_dsl' and validated.python_dsl_code:
                # Try to execute the DSL code to validate it can create a workflow
                if validated.validation_enabled:
                    self._validate_python_dsl(validated.python_dsl_code)

            return validated.dict()

        except Exception as e:
            raise ValueError(f"Workflow executor configuration validation failed: {str(e)}")

    def _validate_python_dsl(self, dsl_code: str) -> None:
        """Validate Python DSL code by attempting to compile and check imports.

        Args:
            dsl_code: Python DSL code to validate

        Raises:
            ValueError: If DSL code is invalid
        """
        try:
            # First check if kubiya_sdk is available
            try:
                import kubiya_sdk
            except ImportError:
                raise ValueError(
                    "kubiya-sdk is not installed. Please install it to use Python DSL workflows."
                )

            # Compile the code to check for syntax errors
            try:
                compile(dsl_code, '<workflow>', 'exec')
            except SyntaxError as e:
                raise ValueError(f"Python syntax error in DSL code: {str(e)}")

            # Create a restricted execution environment
            namespace = {
                '__builtins__': __builtins__,
            }

            # Import kubiya_sdk modules for validation
            try:
                from kubiya_sdk import StatefulWorkflow, Tool
                from kubiya_sdk.workflows import step, tool_step
                namespace.update({
                    'StatefulWorkflow': StatefulWorkflow,
                    'Tool': Tool,
                    'step': step,
                    'tool_step': tool_step,
                })
            except ImportError as e:
                raise ValueError(f"Failed to import kubiya_sdk modules: {str(e)}")

            # Capture stdout/stderr during validation
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = StringIO()
            stderr_capture = StringIO()

            try:
                sys.stdout = stdout_capture
                sys.stderr = stderr_capture

                # Execute the DSL code
                exec(dsl_code, namespace)

                # Check if a workflow was created
                workflow_found = False
                for name, obj in namespace.items():
                    if name.startswith('_'):
                        continue
                    # Check for StatefulWorkflow instance
                    if hasattr(obj, '__class__'):
                        class_name = obj.__class__.__name__
                        if 'StatefulWorkflow' in class_name or 'Workflow' in class_name:
                            workflow_found = True
                            break

                if not workflow_found:
                    raise ValueError(
                        "Python DSL code must create a StatefulWorkflow instance. "
                        "Example: workflow = StatefulWorkflow(name='my-workflow', description='...')"
                    )

            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            # Check for any errors in stderr
            stderr_output = stderr_capture.getvalue()
            if stderr_output and 'error' in stderr_output.lower():
                raise ValueError(f"Python DSL execution produced errors: {stderr_output}")

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Python DSL validation failed: {str(e)}\n{traceback.format_exc()}")

    def get_default_configuration(self) -> Dict[str, Any]:
        """Return the default configuration."""
        return {
            "workflow_type": "json",
            "validation_enabled": True,
            "timeout": 3600,
            "workflow_definition": json.dumps({
                "name": "new-workflow",
                "description": "New workflow",
                "steps": [
                    {
                        "name": "step-1",
                        "description": "First step",
                        "executor": {
                            "type": "shell",
                            "config": {
                                "command": "echo 'Hello World'"
                            }
                        }
                    }
                ]
            }, indent=2)
        }

    def get_framework_class_name(self) -> str:
        """Return the framework class name for this skill."""
        return "WorkflowExecutorTool"

    def get_requirements(self) -> SkillRequirements:
        """Return the skill requirements."""
        return SkillRequirements(
            supported_os=["linux", "darwin", "win32"],
            min_python_version="3.10",
            python_packages=["kubiya-sdk"],
            required_env_vars=[],
            notes="Optional env vars: KUBIYA_API_KEY, KUBIYA_API_URL for workflow execution"
        )


# Auto-register this skill
from control_plane_api.app.skills.registry import register_skill
register_skill(WorkflowExecutorSkill())
