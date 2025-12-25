"""
Task Planning Runner - Workflow execution with streaming and validation

This module handles workflow execution with:
- Step-by-step streaming events
- Tool call/result tracking
- Post-hook validation
- Retry logic with error feedback
"""

from typing import Optional, Dict, Any, Callable, TYPE_CHECKING
import time
import uuid
import json
import re
import copy
from datetime import datetime
import structlog

from agno.agent import Agent
from agno.workflow import Workflow
from pydantic import ValidationError

from control_plane_api.app.models.task_planning import (
    TaskPlanRequest,
    TaskPlanResponse,
    AnalysisAndSelectionOutput,
)
from .hooks import (
    validate_step1_output,
    validate_step2_output,
    HallucinatedIdError,
    OutputValidationError,
)

if TYPE_CHECKING:
    from control_plane_api.app.lib.planning_tools.agno_toolkit import PlanningToolkit

logger = structlog.get_logger()


# ============================================================================
# Step Configuration
# ============================================================================

STEP_DESCRIPTIONS = {
    1: "Discovering available agents and teams in your organization and selecting the best match for your task",
    2: "Creating detailed execution plan with cost estimates, risks, and success criteria"
}

STEP_STAGE_NAMES = {
    1: "analyzing",
    2: "generating"
}

STEP_PROGRESS_MAP = {
    1: 50,
    2: 95
}


# ============================================================================
# Tool Wrapper for Event Streaming
# ============================================================================

def create_tool_wrapper(
    tool: Any,
    publish_event: Callable,
    step_number: int
) -> Any:
    """
    Wrap a tool to emit events before/after execution.

    Args:
        tool: The Agno tool to wrap
        publish_event: Callback to emit streaming events
        step_number: Current workflow step number

    Returns:
        Wrapped tool that emits events
    """
    # Get the original function
    if hasattr(tool, 'entrypoint'):
        original_func = tool.entrypoint
    elif hasattr(tool, 'function'):
        original_func = tool.function
    elif callable(tool):
        original_func = tool
    else:
        return tool

    def wrapped_function(*args, **kwargs):
        tool_id = str(uuid.uuid4())
        tool_name = getattr(tool, 'name', getattr(original_func, '__name__', 'unknown'))

        logger.info(
            "tool_call_started",
            tool_name=tool_name,
            step=step_number
        )

        # Handle Agno's nested args/kwargs
        if 'args' in kwargs:
            nested_args = kwargs.pop('args')
            if isinstance(nested_args, list) and not args:
                args = tuple(nested_args)

        if 'kwargs' in kwargs:
            nested_kwargs = kwargs.pop('kwargs')
            if isinstance(nested_kwargs, dict):
                kwargs.update(nested_kwargs)

        # Emit tool_call event
        try:
            publish_event({
                "event": "tool_call",
                "data": {
                    "tool_id": tool_id,
                    "tool_name": tool_name,
                    "arguments": {"args": list(args), **kwargs},
                    "step": step_number,
                    "timestamp": datetime.now().isoformat()
                }
            })
        except Exception as e:
            logger.warning("failed_to_emit_tool_call", error=str(e))

        start_time = time.time()

        try:
            result = original_func(*args, **kwargs)
            duration = time.time() - start_time

            # Emit success event
            try:
                publish_event({
                    "event": "tool_result",
                    "data": {
                        "tool_id": tool_id,
                        "tool_name": tool_name,
                        "status": "success",
                        "result": str(result)[:1000],
                        "duration": duration,
                        "step": step_number,
                        "timestamp": datetime.now().isoformat()
                    }
                })
            except Exception as e:
                logger.warning("failed_to_emit_tool_result", error=str(e))

            return result

        except Exception as e:
            duration = time.time() - start_time

            try:
                publish_event({
                    "event": "tool_result",
                    "data": {
                        "tool_id": tool_id,
                        "tool_name": tool_name,
                        "status": "failed",
                        "error": str(e),
                        "duration": duration,
                        "step": step_number,
                        "timestamp": datetime.now().isoformat()
                    }
                })
            except Exception:
                pass

            raise

    # Create wrapped copy
    try:
        wrapped_tool = copy.copy(tool)
        if hasattr(tool, 'entrypoint'):
            wrapped_tool.entrypoint = wrapped_function
        elif hasattr(tool, 'function'):
            wrapped_tool.function = wrapped_function
        else:
            return wrapped_function
        return wrapped_tool
    except Exception:
        return wrapped_function


# ============================================================================
# JSON Extraction from Mixed Content
# ============================================================================

def extract_json_from_content(content: str) -> dict:
    """
    Extract JSON object from mixed text content.

    Handles various LLM output patterns:
    1. Pure JSON
    2. Markdown code blocks
    3. Text with inline JSON

    Args:
        content: Raw string content from LLM

    Returns:
        Parsed JSON as dict

    Raises:
        ValueError: If no valid JSON found
    """
    cleaned = content.strip()

    # Strategy 1: Direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Markdown code block
    if '```' in cleaned:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

    # Strategy 3: First { to last }
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(cleaned[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    # Strategy 4: Find complete JSON objects
    for match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned, re.DOTALL):
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            continue

    raise ValueError(f"Could not extract JSON from: {cleaned[:300]}")


# ============================================================================
# Step Execution with Validation
# ============================================================================

def execute_step(
    step: Agent,
    input_data: str,
    publish_event: Callable,
    step_number: int,
    outer_context: Optional[Dict[str, Any]] = None,
    max_retries: int = 2
) -> Any:
    """
    Execute a workflow step with validation and retry logic.

    Args:
        step: The Agno Agent to execute
        input_data: Input string for the agent
        publish_event: Callback for streaming events
        step_number: Current step number
        outer_context: Context for validation
        max_retries: Maximum retry attempts

    Returns:
        Step output (validated)

    Raises:
        ValueError: If validation fails after all retries
    """
    original_tools = None

    for attempt in range(max_retries):
        try:
            # Wrap tools for event tracking
            if hasattr(step, 'tools') and step.tools and original_tools is None:
                original_tools = step.tools
                step.tools = [
                    create_tool_wrapper(tool, publish_event, step_number)
                    for tool in original_tools
                ]

            logger.info(
                "executing_step",
                step=step_number,
                step_name=step.name,
                attempt=attempt + 1
            )

            # Execute step
            result = step.run(input_data)
            content = result.content if hasattr(result, 'content') else result

            # Handle None output
            if content is None:
                raise ValueError(f"Step {step_number} returned None")

            # Parse string output if needed
            if isinstance(content, str) and hasattr(step, 'output_schema'):
                logger.warning("parsing_string_output", step=step_number)
                content_dict = extract_json_from_content(content)
                content = step.output_schema.model_validate(content_dict)

            # Post-hook validation
            if step_number == 1 and hasattr(content, 'model_dump'):
                content_dict = content.model_dump() if hasattr(content, 'model_dump') else vars(content)
                validated = validate_step1_output(content_dict, outer_context)
                # Update content with validated values
                for key, value in validated.items():
                    if hasattr(content, key):
                        setattr(content, key, value)

            elif step_number == 2 and hasattr(content, 'model_dump'):
                content_dict = content.model_dump() if hasattr(content, 'model_dump') else vars(content)
                validate_step2_output(content_dict)

            # Emit reasoning if available
            if hasattr(result, 'messages') and result.messages:
                for message in result.messages:
                    if hasattr(message, 'role') and message.role == 'assistant':
                        if hasattr(message, 'content') and message.content:
                            text = str(message.content)
                            if len(text) > 20:
                                publish_event({
                                    "event": "thinking",
                                    "data": {
                                        "content": text,
                                        "step": step_number,
                                        "step_name": step.name,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                })

            logger.info("step_validation_passed", step=step_number, attempt=attempt + 1)
            return content

        except (ValueError, ValidationError, HallucinatedIdError, OutputValidationError) as e:
            logger.warning(
                "step_validation_failed",
                step=step_number,
                attempt=attempt + 1,
                error=str(e)
            )

            publish_event({
                "event": "validation_error",
                "data": {
                    "step": step_number,
                    "attempt": attempt + 1,
                    "error": str(e),
                    "retrying": attempt < max_retries - 1
                }
            })

            if attempt < max_retries - 1:
                input_data = f"""
VALIDATION ERROR - Previous output was REJECTED:
{str(e)}

CRITICAL: Output ONLY valid JSON starting with {{ and ending with }}
Do NOT add any text before or after the JSON.
Use ONLY IDs from actual tool results.

Original Task:
{input_data}

Try again (attempt {attempt + 2} of {max_retries}).
"""
                continue

            raise ValueError(
                f"Step {step_number} failed after {max_retries} attempts: {e}"
            )

        except Exception as e:
            logger.error("step_execution_error", step=step_number, error=str(e))
            raise

        finally:
            if original_tools is not None:
                step.tools = original_tools


# ============================================================================
# Main Workflow Runner
# ============================================================================

def run_workflow_stream(
    workflow: Workflow,
    task_request: TaskPlanRequest,
    publish_event: Callable,
    quick_mode: bool = False
) -> TaskPlanResponse:
    """
    Run the planning workflow with streaming events.

    Executes each step sequentially with:
    - Progress events
    - Tool call/result tracking
    - Post-hook validation
    - Runtime/model_id auto-population

    Args:
        workflow: Planning workflow instance
        task_request: Task plan request
        publish_event: Event streaming callback
        quick_mode: Skip verbose reasoning (for --local mode)

    Returns:
        TaskPlanResponse from final step
    """
    # Build input
    workflow_input = f"""
Task: {task_request.description}
Priority: {task_request.priority}
Context: {task_request.conversation_context or 'New task'}

Analyze this task and select the best agent/team to execute it.
"""

    logger.info(
        "workflow_runner_starting",
        input_length=len(workflow_input),
        steps=len(workflow.steps)
    )

    # Initial progress
    publish_event({
        "event": "progress",
        "data": {
            "stage": "initializing",
            "message": "Initializing AI Task Planner - analyzing your request...",
            "progress": 10
        }
    })

    # Get outer context for validation
    outer_context = getattr(workflow, '_outer_context', None)

    step_outputs = {}
    current_input = workflow_input

    # Execute each step
    for i, step in enumerate(workflow.steps, 1):
        step_start = time.time()

        logger.info("starting_workflow_step", step=i, step_name=step.name)

        # Emit step progress
        progress = STEP_PROGRESS_MAP.get(i, 50)
        stage = STEP_STAGE_NAMES.get(i, "processing")
        description = STEP_DESCRIPTIONS.get(i, f"Executing {step.name}")

        publish_event({
            "event": "progress",
            "data": {
                "message": description,
                "progress": progress
            }
        })

        publish_event({
            "event": "progress",
            "data": {
                "stage": stage,
                "message": description,
                "progress": progress
            }
        })

        # Execute step with validation
        output = execute_step(
            step=step,
            input_data=current_input,
            publish_event=publish_event,
            step_number=i,
            outer_context=outer_context,
            max_retries=2 if i == 1 else 1  # More retries for Step 1
        )

        step_duration = time.time() - step_start
        step_outputs[i] = output

        # Step 1 post-processing: Extract runtime/model_id
        if i == 1 and hasattr(output, 'selected_entity_id'):
            entity_id = output.selected_entity_id
            entity_type = getattr(output, 'selected_entity_type', 'agent')

            # Try to get runtime/model_id from discovered agents
            runtime = getattr(output, 'selected_agent_runtime', None)
            model_id = getattr(output, 'selected_agent_model_id', None)

            if not runtime and entity_type == 'agent':
                discovered = getattr(output, 'discovered_agents', [])
                for agent in discovered:
                    if str(agent.get('id')) == entity_id:
                        runtime = agent.get('runtime', 'default')
                        model_id = agent.get('model_id', 'claude-sonnet-4')
                        break

            logger.info(
                "step1_entity_selected",
                entity_id=entity_id[:12] if entity_id else None,
                runtime=runtime,
                model_id=model_id
            )

        publish_event({
            "event": "progress",
            "data": {
                "message": f"{step.name} completed",
                "progress": progress
            }
        })

        logger.info(
            "workflow_step_completed",
            step=i,
            step_name=step.name,
            duration_seconds=round(step_duration, 2)
        )

        # Prepare input for next step
        if i < len(workflow.steps):
            if hasattr(output, 'model_dump'):
                current_input = json.dumps(output.model_dump(), indent=2)
            elif hasattr(output, '__dict__'):
                current_input = json.dumps(output.__dict__, indent=2)
            else:
                current_input = str(output)

    # Final output processing
    final_output = step_outputs.get(len(workflow.steps))

    # Auto-populate runtime/model_id/environment from Step 1 if missing
    if len(workflow.steps) >= 2:
        step1_output = step_outputs.get(1)
        if step1_output and final_output:
            # Propagate runtime
            if hasattr(step1_output, 'selected_agent_runtime'):
                runtime = step1_output.selected_agent_runtime
                if runtime and hasattr(final_output, 'selected_agent_runtime'):
                    if not final_output.selected_agent_runtime:
                        final_output.selected_agent_runtime = runtime

            # Propagate model_id
            if hasattr(step1_output, 'selected_agent_model_id'):
                model_id = step1_output.selected_agent_model_id
                if model_id and hasattr(final_output, 'selected_agent_model_id'):
                    if not final_output.selected_agent_model_id:
                        final_output.selected_agent_model_id = model_id

            # Propagate environment_id to recommended_execution and top-level fields
            env_id = getattr(step1_output, 'selected_environment_id', None)
            env_name = getattr(step1_output, 'selected_environment_name', None)

            if env_id:
                # Set top-level fields
                if hasattr(final_output, 'selected_environment_id') and not final_output.selected_environment_id:
                    final_output.selected_environment_id = env_id
                if hasattr(final_output, 'selected_environment_name') and not final_output.selected_environment_name:
                    final_output.selected_environment_name = env_name

                # Set recommended_execution fields (this is what CLI checks!)
                if hasattr(final_output, 'recommended_execution'):
                    rec_exec = final_output.recommended_execution
                    if hasattr(rec_exec, 'recommended_environment_id') and not rec_exec.recommended_environment_id:
                        rec_exec.recommended_environment_id = env_id
                    if hasattr(rec_exec, 'recommended_environment_name') and not rec_exec.recommended_environment_name:
                        rec_exec.recommended_environment_name = env_name

                logger.info(
                    "propagated_environment_from_step1",
                    env_id=env_id[:12] if env_id else None,
                    env_name=env_name
                )

    # Emit completion
    title = getattr(final_output, 'title', 'Task Plan')
    publish_event({
        "event": "progress",
        "data": {
            "stage": "completed",
            "message": f"Execution plan '{title}' generated successfully!",
            "progress": 100
        }
    })

    logger.info(
        "workflow_completed_successfully",
        title=title,
        steps_executed=len(workflow.steps)
    )

    return final_output


# ============================================================================
# Fast Workflow Runner (--local mode)
# ============================================================================

def run_fast_workflow_stream(
    workflow: Workflow,
    task_request: TaskPlanRequest,
    publish_event: Callable
) -> 'FastSelectionOutput':
    """
    Run fast single-step workflow for --local mode.

    Args:
        workflow: Fast workflow (single step)
        task_request: Task request
        publish_event: Event callback

    Returns:
        FastSelectionOutput
    """
    from .models import FastSelectionOutput

    workflow_input = f"Select best agent for: {task_request.description}"

    publish_event({
        "event": "progress",
        "data": {
            "stage": "selecting",
            "message": "Quick agent selection...",
            "progress": 50
        }
    })

    step = workflow.steps[0]
    outer_context = getattr(workflow, '_outer_context', None)

    output = execute_step(
        step=step,
        input_data=workflow_input,
        publish_event=publish_event,
        step_number=1,
        outer_context=outer_context,
        max_retries=1
    )

    publish_event({
        "event": "progress",
        "data": {
            "stage": "completed",
            "message": "Agent selected!",
            "progress": 100
        }
    })

    return output
