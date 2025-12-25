"""
Workflow Executor Tools for Agent Control Plane Worker

This module provides tools for agents to execute workflows defined via
JSON or Python DSL. Agents can call these tools to run multi-step workflows
with parameter injection and streaming execution.

Workflows execute remotely on specified runners using the Kubiya SDK.
"""

import json
import structlog
import asyncio
import os
import hashlib
from typing import Optional, Callable, Dict, Any, List
from agno.tools import Toolkit
from control_plane_api.worker.skills.builtin.schema_fix_mixin import SchemaFixMixin

logger = structlog.get_logger(__name__)


class WorkflowExecutorTools(SchemaFixMixin, Toolkit):
    """
    Workflow Executor toolkit for running workflows from agents.

    Agents can use these tools to:
    - Execute JSON-defined workflows with parameters
    - Run Python DSL workflows
    - Stream workflow execution events
    - Get workflow execution status
    """

    def __init__(
        self,
        name: Optional[str] = None,
        workflows: Optional[List[Dict[str, Any]]] = None,
        validation_enabled: bool = True,
        default_runner: Optional[str] = None,
        timeout: int = 3600,
        default_parameters: Optional[Dict[str, Any]] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        kubiya_api_key: Optional[str] = None,
        kubiya_api_base: Optional[str] = None,
        execution_id: Optional[str] = None,  # Add execution_id parameter
        # Legacy parameters for backwards compatibility
        workflow_type: Optional[str] = None,
        workflow_definition: Optional[str] = None,
        python_dsl_code: Optional[str] = None,
    ):
        """
        Initialize WorkflowExecutorTools.

        Args:
            name: Skill instance name (defaults to "workflow_executor")
            workflows: List of workflow definitions. Each workflow becomes a separate tool.
                      Format: [{"name": "analyze-logs", "type": "json", "definition": {...}}, ...]
            validation_enabled: Enable pre-execution validation
            default_runner: Default runner/environment name
            timeout: Maximum execution timeout in seconds
            default_parameters: Default parameter values to use for all workflows
            stream_callback: Optional callback for streaming output
            kubiya_api_key: Kubiya API key (defaults to KUBIYA_API_KEY env var)
            kubiya_api_base: Kubiya API base URL (defaults to KUBIYA_API_BASE env var)
            workflow_type: LEGACY - Type of workflow ("json" or "python_dsl")
            workflow_definition: LEGACY - JSON workflow definition string
            python_dsl_code: LEGACY - Python DSL code string
        """
        super().__init__(name=name or "workflow_executor")

        self.validation_enabled = validation_enabled
        self.default_runner = default_runner or "default"
        self.timeout = timeout
        self.default_parameters = default_parameters or {}
        self.stream_callback = stream_callback
        self.execution_id = execution_id or os.environ.get("EXECUTION_ID")  # Store execution_id

        print(f"\n🔍 WORKFLOW EXECUTOR __init__ DEBUG:")
        print(f"   Received execution_id param: {execution_id}")
        print(f"   EXECUTION_ID env var: {os.environ.get('EXECUTION_ID')}")
        print(f"   Final self.execution_id: {self.execution_id}\n")

        # Get Kubiya API credentials from parameters or environment
        self.kubiya_api_key = kubiya_api_key or os.environ.get("KUBIYA_API_KEY")
        self.kubiya_api_base = kubiya_api_base or os.environ.get("KUBIYA_API_BASE", "https://api.kubiya.ai")

        if not self.kubiya_api_key:
            logger.warning("No KUBIYA_API_KEY provided - workflow execution will fail")

        # Get control plane client for publishing events
        try:
            from control_plane_api.worker.control_plane_client import get_control_plane_client
            self.control_plane = get_control_plane_client()
        except Exception as e:
            logger.warning(f"Failed to get control plane client: {e}")
            self.control_plane = None

        # Initialize Kubiya SDK client for remote execution
        self.kubiya_client = None
        if self.kubiya_api_key:
            try:
                from kubiya import KubiyaClient

                self.kubiya_client = KubiyaClient(
                    api_key=self.kubiya_api_key,
                    base_url=self.kubiya_api_base,
                    runner=self.default_runner,
                    timeout=self.timeout
                )
                logger.info(f"Initialized Kubiya SDK client for remote workflow execution (runner: {self.default_runner})")
            except ImportError as e:
                logger.error(f"Failed to import Kubiya SDK: {e}. Install with: pip install git+https://github.com/kubiyabot/sdk-py.git@main")
                self.kubiya_client = None

        # Handle legacy single workflow format
        if workflow_definition or python_dsl_code:
            logger.info("Using legacy single-workflow format")

            legacy_workflow = {
                "name": "default",
                "type": workflow_type or "json",
            }
            if workflow_type == "json" and workflow_definition:
                legacy_workflow["definition"] = workflow_definition
            elif workflow_type == "python_dsl" and python_dsl_code:
                legacy_workflow["code"] = python_dsl_code

            workflows = [legacy_workflow]

            # Store legacy attributes for backward compatibility
            self.workflow_type = workflow_type
            self.workflow_definition = workflow_definition
            self.python_dsl_code = python_dsl_code

            # Parse workflow data for legacy JSON workflows
            if workflow_type == "json" and workflow_definition:
                try:
                    self.workflow_data = json.loads(workflow_definition) if isinstance(workflow_definition, str) else workflow_definition
                except Exception as e:
                    logger.error(f"Failed to parse legacy workflow definition: {e}")
                    self.workflow_data = None
            else:
                self.workflow_data = None
        else:
            # Not using legacy format - no legacy attributes
            self.workflow_type = None
            self.workflow_definition = None
            self.python_dsl_code = None
            self.workflow_data = None

        # Store workflows collection
        self.workflows = workflows or []

        # Dynamically register a tool for each workflow
        for workflow in self.workflows:
            self._register_workflow_tool(workflow)

        # If no workflows registered (empty or legacy format), register default execution tool
        if not self.workflows or len(self.workflows) == 0:
            logger.warning("No workflows configured in WorkflowExecutorTools")

        # Register helper tools
        self.register(self.list_all_workflows)
        self.register(self.get_workflow_info)

        # Fix: Rebuild function schemas with proper parameters
        self._rebuild_function_schemas()

    def _register_workflow_tool(self, workflow: Dict[str, Any]):
        """
        Dynamically register a tool method for a specific workflow.

        Creates a method named after the workflow that executes it on the configured runner.

        Args:
            workflow: Workflow definition dict with name, type, and definition/code
        """
        workflow_name = workflow.get("name", "unknown")
        workflow_type = workflow.get("type", "json")

        # Use clean workflow name as method name (replace hyphens/spaces with underscores)
        # For "analyze-logs" workflow → method name "analyze_logs"
        # For "default" workflow (legacy) → use the toolkit name
        safe_name = workflow_name.replace("-", "_").replace(" ", "_").lower()

        # If this is the default workflow, use the skill name
        if workflow_name == "default" and self.name != "workflow_executor":
            method_name = self.name
        else:
            method_name = safe_name

        # Create a closure that captures the workflow definition
        def workflow_executor(parameters: Optional[Dict[str, Any]] = None) -> str:
            f"""
            Execute the '{workflow_name}' workflow on the configured runner.

            This workflow executes on the runner specified in the workflow definition
            using the Kubiya SDK. All steps are executed in dependency order.

            Args:
                parameters: Dictionary of parameters to inject into the workflow.
                           Parameters can be referenced in workflow steps using {{{{param_name}}}} syntax.

            Returns:
                str: Formatted workflow execution results including step outputs and status.

            Examples:
                # Execute workflow with parameters
                {method_name}(parameters={{"environment": "production", "version": "v1.2.3"}})
            """
            return self._execute_specific_workflow(workflow, parameters)

        # Set proper docstring
        workflow_executor.__doc__ = f"""
Execute the '{workflow_name}' workflow on the configured runner.

Type: {workflow_type}
Runner: Specified in workflow definition or default_runner config

Args:
    parameters: Optional dictionary of parameters to inject into workflow steps.
                Reference parameters in steps using {{{{param_name}}}} syntax.

Returns:
    str: Workflow execution results including all step outputs.
"""

        # Set method name for proper tool registration
        workflow_executor.__name__ = method_name

        # Register as a tool
        self.register(workflow_executor)

        # Also set as attribute on self for direct access
        setattr(self, method_name, workflow_executor)

        logger.info(f"Registered workflow tool: {method_name} for workflow '{workflow_name}'")

    def _execute_specific_workflow(
        self,
        workflow: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Execute a specific workflow from the collection.

        Args:
            workflow: Workflow definition
            parameters: Execution parameters

        Returns:
            str: Formatted execution result
        """
        try:
            workflow_name = workflow.get("name", "unknown")
            workflow_type = workflow.get("type", "json")

            # Merge default parameters with runtime parameters
            # Runtime parameters override defaults
            params = {**self.default_parameters, **(parameters or {})}

            # Determine runner
            effective_runner = self.default_runner
            if workflow_type == "json":
                workflow_def = workflow.get("definition")
                if isinstance(workflow_def, str):
                    workflow_data = json.loads(workflow_def)
                else:
                    workflow_data = workflow_def

                effective_runner = workflow_data.get("runner") or self.default_runner
            else:
                effective_runner = self.default_runner

            # Stream start message
            if self.stream_callback:
                self.stream_callback(
                    f"🚀 Starting workflow: {workflow_name}\n"
                    f"   Type: {workflow_type}\n"
                    f"   Parameters: {json.dumps(params, indent=2)}\n"
                    f"   Runner: {effective_runner}\n\n"
                )

            # Execute based on workflow type
            if workflow_type == "json":
                result = self._execute_json_workflow_specific(workflow, params, effective_runner)
            elif workflow_type == "python_dsl":
                result = self._execute_python_dsl_workflow_specific(workflow, params, effective_runner)
            else:
                raise ValueError(f"Unsupported workflow type: {workflow_type}")

            # Stream completion message
            if self.stream_callback:
                self.stream_callback(f"\n✅ Workflow '{workflow_name}' completed successfully\n")

            return result

        except Exception as e:
            error_msg = f"❌ Workflow '{workflow.get('name', 'unknown')}' execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            if self.stream_callback:
                self.stream_callback(f"\n{error_msg}\n")

            return error_msg

    def _execute_json_workflow_specific(
        self,
        workflow: Dict[str, Any],
        parameters: Dict[str, Any],
        runner: str
    ) -> str:
        """Execute a JSON workflow."""
        workflow_def = workflow.get("definition")
        if isinstance(workflow_def, str):
            workflow_data = json.loads(workflow_def)
        else:
            workflow_data = workflow_def

        if not workflow_data:
            raise ValueError("No workflow definition available")

        if not self.kubiya_client:
            raise RuntimeError("Kubiya SDK client not initialized")

        # Ensure runner is set
        workflow_data["runner"] = runner

        # Remove 'triggers' key if it exists - not needed for direct execution
        # The DAG builder rejects this key when executing workflows directly
        if "triggers" in workflow_data:
            logger.debug(f"Removing 'triggers' key from workflow definition (not needed for execution)")
            workflow_data.pop("triggers")

        # Execute remotely
        from datetime import datetime
        import time
        start_time = datetime.utcnow()

        # Generate unique message_id for workflow streaming
        workflow_message_id = f"{self.execution_id}_{int(time.time() * 1000000)}" if self.execution_id else None

        if self.stream_callback:
            self.stream_callback(f"▶️  Submitting to runner '{runner}'...\n\n")

        # Publish workflow start to control plane
        print(f"\n{'='*80}")
        print(f"📡 WORKFLOW STREAMING DEBUG")
        print(f"{'='*80}")
        print(f"control_plane exists: {self.control_plane is not None}")
        print(f"execution_id: {self.execution_id}")
        print(f"workflow_message_id: {workflow_message_id}")
        print(f"{'='*80}\n")

        if self.control_plane and self.execution_id and workflow_message_id:
            try:
                print(f"📡 Publishing workflow start to control plane...")
                self.control_plane.publish_event(
                    execution_id=self.execution_id,
                    event_type="message_chunk",
                    data={
                        "role": "assistant",
                        "content": f"🚀 Starting workflow: {workflow_data.get('name', 'unknown')}\n▶️  Submitting to runner '{runner}'...\n\n",
                        "is_chunk": True,
                        "message_id": workflow_message_id,
                        "source": "workflow",
                    }
                )
                print(f"✅ Successfully published workflow start to control plane\n")
            except Exception as e:
                print(f"❌ Failed to publish workflow start: {e}\n")
                logger.error(f"❌ Failed to publish workflow start: {e}", exc_info=True)
        else:
            print(f"⚠️  Skipping control plane publish (one or more required fields is None)\n")

        # ✅ Enable streaming to capture real-time workflow output
        response = self.kubiya_client.execute_workflow(
            workflow_definition=workflow_data,
            parameters=parameters,
            stream=True
        )

        # Accumulate streaming results
        accumulated_output = []
        event_count = 0
        step_outputs = {}
        current_step = None
        seen_events = set()  # Track event hashes to prevent duplicates

        # Register workflow for cancellation tracking
        from control_plane_api.app.services.workflow_cancellation_manager import workflow_cancellation_manager
        cancellation_event = workflow_cancellation_manager.register_workflow(self.execution_id, workflow_message_id)

        # Iterate over streaming results (SDK yields JSON strings)
        for event in response:
            event_count += 1

            # Check for cancellation FIRST (immediate response)
            if cancellation_event.is_set():
                logger.warning("⚠️  Workflow execution cancelled by user")
                workflow_cancellation_manager.clear_cancellation(self.execution_id, workflow_message_id)
                return f"❌ Workflow execution cancelled by user\n\nWorkflow: {workflow_data.get('name', 'unknown')}\nCancelled at: {datetime.utcnow().isoformat()}"

            # Skip None/empty events
            if event is None:
                logger.debug(f"⏭️  Skipping None event #{event_count}")
                continue

            # 🔍 DEBUG: Print raw event to understand SDK response format
            print(f"\n{'='*80}")
            print(f"🔍 RAW SDK EVENT #{event_count}")
            print(f"{'='*80}")
            print(f"Type: {type(event).__name__}")
            print(f"Length: {len(str(event)) if event else 0}")
            print(f"Repr: {repr(event)[:500]}")
            if isinstance(event, (str, bytes)):
                print(f"First 200 chars: {str(event)[:200]}")
            print(f"{'='*80}\n")

            # Debug: Log raw event with actual content
            event_repr = repr(event)[:500]  # Use repr to see exact content
            logger.info(f"📦 Received event #{event_count} (type={type(event).__name__}, length={len(str(event)) if event else 0})")
            logger.debug(f"   Raw content: {event_repr}")

            # Parse the event (SDK yields JSON strings or bytes)
            try:
                if isinstance(event, bytes):
                    # Skip empty bytes
                    if not event:
                        logger.debug(f"   ⏭️  Skipping empty bytes")
                        continue

                    # Decode bytes to string first
                    logger.debug(f"   🔄 Decoding bytes to string...")
                    event = event.decode('utf-8')
                    logger.debug(f"   ✅ Decoded to string (length={len(event)})")

                if isinstance(event, str):
                    # Skip empty strings
                    if not event.strip():
                        logger.debug(f"   ⏭️  Skipping empty string event")
                        continue

                    # Handle SSE (Server-Sent Events) format: "data: 2:{json}"
                    # The SDK sometimes returns events with this prefix
                    if event.startswith("data: "):
                        logger.debug(f"   🔄 Stripping SSE 'data: ' prefix...")
                        event = event[6:]  # Remove "data: " prefix (6 chars)

                        # Also strip the message ID prefix like "2:"
                        if ":" in event and event.split(":", 1)[0].isdigit():
                            logger.debug(f"   🔄 Stripping message ID prefix...")
                            event = event.split(":", 1)[1]  # Remove "2:" or similar prefix

                        logger.debug(f"   ✅ Cleaned SSE event (length={len(event)})")

                    # Try to parse as JSON
                    logger.debug(f"   🔄 Parsing JSON string...")
                    event_data = json.loads(event)
                    logger.debug(f"   ✅ Parsed JSON: type={event_data.get('type', 'unknown')}")
                elif isinstance(event, dict):
                    # Already a dict
                    logger.debug(f"   ✅ Already a dict: type={event.get('type', 'unknown')}")
                    event_data = event
                else:
                    # Unknown type, treat as plain text
                    logger.warning(f"   ⚠️  Unknown event type: {type(event).__name__}, treating as plain text")
                    event_str = str(event)
                    if event_str.strip():  # Only add non-empty text
                        accumulated_output.append(event_str)
                        if self.stream_callback:
                            self.stream_callback(f"{event_str}\n")
                    continue
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                # If not valid JSON or can't decode, treat as plain text
                logger.warning(f"   ⚠️  Failed to parse event: {e}, treating as plain text")
                event_str = str(event)
                if event_str.strip():  # Only add non-empty text
                    accumulated_output.append(event_str)
                    if self.stream_callback:
                        self.stream_callback(f"{event_str}\n")
                continue

            # Extract meaningful content based on event type
            event_type = event_data.get("type", "unknown")
            logger.info(f"   🎯 Event type: {event_type}")

            # Handle actual Kubiya workflow event types
            if event_type == "step_output":
                # step_output contains the actual workflow output in step.output
                step = event_data.get("step", {})
                step_name = step.get("name", "unknown")
                output = step.get("output", "")

                if output.strip():
                    # Deduplicate events - SDK sends same event twice (plain JSON + SSE format)
                    event_hash = hashlib.md5(f"{step_name}:{output}".encode()).hexdigest()
                    if event_hash in seen_events:
                        print(f"      ⏭️  Skipping duplicate event: {step_name} - {output[:50]}")
                        logger.info(f"      ⏭️  Skipping duplicate event: {step_name} - {output[:50]}")
                        continue
                    seen_events.add(event_hash)

                    logger.info(f"      📝 Step output: {step_name} - {output[:100]}")

                    # Format for display
                    formatted_output = f"```\n{output}\n```\n"

                    # Stream to callback if provided
                    if self.stream_callback:
                        self.stream_callback(formatted_output)

                    # Publish to control plane as message chunk
                    if self.control_plane and self.execution_id and workflow_message_id:
                        try:
                            print(f"📡 Publishing step output to control plane (len={len(formatted_output)})")
                            result = self.control_plane.publish_event(
                                execution_id=self.execution_id,
                                event_type="message_chunk",
                                data={
                                    "role": "assistant",
                                    "content": formatted_output,
                                    "is_chunk": True,
                                    "message_id": workflow_message_id,
                                    "source": "workflow",
                                    "metadata": {
                                        "step_name": step_name,
                                        "event_type": "step_output",
                                    }
                                }
                            )
                            print(f"✅ Published step output: {result}")
                        except Exception as e:
                            print(f"❌ Failed to publish workflow output: {e}")
                            logger.error(f"Failed to publish workflow output to control plane: {e}", exc_info=True)

                    accumulated_output.append(output)

                    # Track by step
                    if step_name not in step_outputs:
                        step_outputs[step_name] = []
                    step_outputs[step_name].append(output)

            elif event_type == "step_running":
                # Step is starting
                step = event_data.get("step", {})
                step_name = step.get("name", "unknown")
                current_step = step_name
                formatted = f"\n▶️  Step: {step_name}"
                logger.info(f"      ▶️  Starting step: {step_name}")
                accumulated_output.append(formatted)
                if self.stream_callback:
                    self.stream_callback(f"{formatted}\n")

                # Publish to control plane as message chunk
                if self.control_plane and self.execution_id and workflow_message_id:
                    try:
                        self.control_plane.publish_event(
                            execution_id=self.execution_id,
                            event_type="message_chunk",
                            data={
                                "role": "assistant",
                                "content": formatted,
                                "is_chunk": True,
                                "message_id": workflow_message_id,
                                "source": "workflow",
                                "metadata": {
                                    "step_name": step_name,
                                    "event_type": "step_start",
                                }
                            }
                        )
                    except Exception as e:
                        logger.debug(f"Failed to publish step_running to control plane: {e}")

            elif event_type == "step_complete":
                # Step finished
                step = event_data.get("step", {})
                step_name = step.get("name", "unknown")
                status = step.get("status", "unknown")
                icon = "✅" if status == "finished" else "❌"
                formatted = f"{icon} Step '{step_name}' {status}"
                logger.info(f"      {icon} Step completed: {step_name} ({status})")
                accumulated_output.append(formatted)
                current_step = None
                if self.stream_callback:
                    self.stream_callback(f"{formatted}\n")

                # Publish to control plane as message chunk
                if self.control_plane and self.execution_id and workflow_message_id:
                    try:
                        self.control_plane.publish_event(
                            execution_id=self.execution_id,
                            event_type="message_chunk",
                            data={
                                "role": "assistant",
                                "content": formatted,
                                "is_chunk": True,
                                "message_id": workflow_message_id,
                                "source": "workflow",
                                "metadata": {
                                    "step_name": step_name,
                                    "status": status,
                                    "event_type": "step_complete",
                                }
                            }
                        )
                    except Exception as e:
                        logger.debug(f"Failed to publish step_complete to control plane: {e}")

            elif event_type == "workflow_complete":
                # Workflow finished
                dag_name = event_data.get("dagName", "unknown")
                status = event_data.get("status", "unknown")
                success = event_data.get("success", False)
                icon = "✅" if success else "❌"
                formatted = f"{icon} Workflow '{dag_name}' {status}"
                logger.info(f"      {icon} Workflow completed: {dag_name} ({status}, success={success})")
                accumulated_output.append(formatted)
                if self.stream_callback:
                    self.stream_callback(f"{formatted}\n")

            elif event_type == "log":
                # Filter out noisy internal workflow runner logs
                message = event_data.get("message", "")
                level = event_data.get("level", "info")

                # Skip internal/noisy log messages
                noisy_patterns = [
                    "[SSE]",
                    "Published workflow stream event",
                    "Stored workflow data",
                    "Emitting log event",
                    "msg=status requestId",
                ]

                # Check if message contains any noisy pattern
                if any(pattern in message for pattern in noisy_patterns):
                    logger.debug(f"      🔇 Skipping noisy log: {message[:50]}")
                    continue

                # Only show meaningful log messages
                formatted = f"[{level.upper()}] {message}"
                logger.info(f"      💬 Log message: {message[:100]}")
                accumulated_output.append(formatted)
                if self.stream_callback:
                    self.stream_callback(f"{formatted}\n")

            elif event_type == "error":
                error_msg = event_data.get("message", str(event_data))
                formatted = f"❌ Error: {error_msg}"
                logger.error(f"      ❌ Workflow error: {error_msg}")
                accumulated_output.append(formatted)
                if self.stream_callback:
                    self.stream_callback(f"{formatted}\n")

            elif event_type == "heartbeat":
                # Skip heartbeat events in output
                logger.debug(f"      💓 Heartbeat (skipping)")
                continue

            else:
                # For unknown event types, log but don't show to user
                logger.info(f"      ❓ Unknown event type: {event_type}")
                logger.debug(f"      Raw data: {json.dumps(event_data)[:200]}")
                # Skip unknown events instead of showing raw JSON
                continue

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Format complete results for Claude to see
        result_text = f"\n{'='*60}\n"
        result_text += f"Workflow Execution: {workflow_data.get('name', 'unknown')}\n"
        result_text += f"{'='*60}\n\n"
        result_text += f"Status: ✅ Completed\n"
        result_text += f"Duration: {duration:.2f}s\n"
        result_text += f"Runner: {runner}\n"
        result_text += f"Parameters: {json.dumps(parameters, indent=2)}\n"
        result_text += f"\nTotal Events: {event_count}\n"

        # Include all captured output in the result
        if accumulated_output:
            result_text += f"\n{'='*60}\n"
            result_text += f"Workflow Output:\n"
            result_text += f"{'='*60}\n\n"
            result_text += "\n".join(accumulated_output)
            logger.info(f"✅ Workflow execution complete: {event_count} events processed, {len(accumulated_output)} output lines accumulated")
        else:
            logger.warning(f"⚠️  No workflow output accumulated (received {event_count} events but none produced output)")

        logger.debug(f"Final result preview: {result_text[:500]}")

        # Close the workflow streaming message (empty content marks end of stream)
        # The agent will process the workflow result and generate its OWN response
        # with a different message_id - that's the next message the user sees
        if self.control_plane and self.execution_id and workflow_message_id:
            try:
                print(f"\n📡 Closing workflow streaming message...")
                self.control_plane.publish_event(
                    execution_id=self.execution_id,
                    event_type="message_chunk",
                    data={
                        "role": "assistant",
                        "content": "",  # Empty - just marks end of workflow stream
                        "is_chunk": False,  # Final chunk - closes the streaming message
                        "message_id": workflow_message_id,
                        "source": "workflow",
                        "metadata": {
                            "event_type": "workflow_stream_end",
                            "duration": duration,
                            "total_events": event_count,
                        }
                    }
                )
                print(f"✅ Workflow stream closed\n")
            except Exception as e:
                logger.debug(f"Failed to close workflow stream: {e}")

        # Return result to agent - agent will process and respond with its OWN message_id
        return result_text

    def _execute_python_dsl_workflow_specific(
        self,
        workflow: Dict[str, Any],
        parameters: Dict[str, Any],
        runner: str
    ) -> str:
        """Execute a Python DSL workflow."""
        python_code = workflow.get("code")
        if not python_code:
            raise ValueError("No Python DSL code available")

        if not self.kubiya_client:
            raise RuntimeError("Kubiya SDK client not initialized")

        workflow_name = workflow.get("name", "python-dsl-workflow")

        # Create workflow definition for remote execution
        workflow_definition = {
            "name": workflow_name,
            "description": f"Python DSL workflow: {workflow_name}",
            "runner": runner,
            "steps": [
                {
                    "name": "execute_python_dsl",
                    "description": "Execute Python DSL workflow code",
                    "executor": {
                        "type": "python_dsl",
                        "config": {"code": python_code}
                    }
                }
            ]
        }

        from datetime import datetime
        start_time = datetime.utcnow()

        if self.stream_callback:
            self.stream_callback(f"▶️  Submitting to runner '{runner}'...\n\n")

        # ✅ Enable streaming to capture real-time workflow output
        response = self.kubiya_client.execute_workflow(
            workflow_definition=workflow_definition,
            parameters=parameters,
            stream=True
        )

        # Accumulate streaming results
        accumulated_output = []
        event_count = 0
        step_outputs = {}
        current_step = None
        seen_events = set()  # Track event hashes to prevent duplicates

        # Register workflow for cancellation tracking
        from control_plane_api.app.services.workflow_cancellation_manager import workflow_cancellation_manager
        cancellation_event = workflow_cancellation_manager.register_workflow(self.execution_id, workflow_message_id)

        # Iterate over streaming results (SDK yields JSON strings)
        for event in response:
            event_count += 1

            # Check for cancellation FIRST (immediate response)
            if cancellation_event.is_set():
                logger.warning("⚠️  Workflow execution cancelled by user")
                workflow_cancellation_manager.clear_cancellation(self.execution_id, workflow_message_id)
                return f"❌ Workflow execution cancelled by user\n\nWorkflow: {workflow_data.get('name', 'unknown')}\nCancelled at: {datetime.utcnow().isoformat()}"

            # Skip None/empty events
            if event is None:
                logger.debug(f"⏭️  Skipping None event #{event_count}")
                continue

            # 🔍 DEBUG: Print raw event to understand SDK response format
            print(f"\n{'='*80}")
            print(f"🔍 RAW SDK EVENT #{event_count}")
            print(f"{'='*80}")
            print(f"Type: {type(event).__name__}")
            print(f"Length: {len(str(event)) if event else 0}")
            print(f"Repr: {repr(event)[:500]}")
            if isinstance(event, (str, bytes)):
                print(f"First 200 chars: {str(event)[:200]}")
            print(f"{'='*80}\n")

            # Debug: Log raw event with actual content
            event_repr = repr(event)[:500]  # Use repr to see exact content
            logger.info(f"📦 Received event #{event_count} (type={type(event).__name__}, length={len(str(event)) if event else 0})")
            logger.debug(f"   Raw content: {event_repr}")

            # Parse the event (SDK yields JSON strings or bytes)
            try:
                if isinstance(event, bytes):
                    # Skip empty bytes
                    if not event:
                        logger.debug(f"   ⏭️  Skipping empty bytes")
                        continue

                    # Decode bytes to string first
                    logger.debug(f"   🔄 Decoding bytes to string...")
                    event = event.decode('utf-8')
                    logger.debug(f"   ✅ Decoded to string (length={len(event)})")

                if isinstance(event, str):
                    # Skip empty strings
                    if not event.strip():
                        logger.debug(f"   ⏭️  Skipping empty string event")
                        continue

                    # Handle SSE (Server-Sent Events) format: "data: 2:{json}"
                    # The SDK sometimes returns events with this prefix
                    if event.startswith("data: "):
                        logger.debug(f"   🔄 Stripping SSE 'data: ' prefix...")
                        event = event[6:]  # Remove "data: " prefix (6 chars)

                        # Also strip the message ID prefix like "2:"
                        if ":" in event and event.split(":", 1)[0].isdigit():
                            logger.debug(f"   🔄 Stripping message ID prefix...")
                            event = event.split(":", 1)[1]  # Remove "2:" or similar prefix

                        logger.debug(f"   ✅ Cleaned SSE event (length={len(event)})")

                    # Try to parse as JSON
                    logger.debug(f"   🔄 Parsing JSON string...")
                    event_data = json.loads(event)
                    logger.debug(f"   ✅ Parsed JSON: type={event_data.get('type', 'unknown')}")
                elif isinstance(event, dict):
                    # Already a dict
                    logger.debug(f"   ✅ Already a dict: type={event.get('type', 'unknown')}")
                    event_data = event
                else:
                    # Unknown type, treat as plain text
                    logger.warning(f"   ⚠️  Unknown event type: {type(event).__name__}, treating as plain text")
                    event_str = str(event)
                    if event_str.strip():  # Only add non-empty text
                        accumulated_output.append(event_str)
                        if self.stream_callback:
                            self.stream_callback(f"{event_str}\n")
                    continue
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                # If not valid JSON or can't decode, treat as plain text
                logger.warning(f"   ⚠️  Failed to parse event: {e}, treating as plain text")
                event_str = str(event)
                if event_str.strip():  # Only add non-empty text
                    accumulated_output.append(event_str)
                    if self.stream_callback:
                        self.stream_callback(f"{event_str}\n")
                continue

            # Extract meaningful content based on event type
            event_type = event_data.get("type", "unknown")
            logger.info(f"   🎯 Event type: {event_type}")

            # Handle actual Kubiya workflow event types
            if event_type == "step_output":
                # step_output contains the actual workflow output in step.output
                step = event_data.get("step", {})
                step_name = step.get("name", "unknown")
                output = step.get("output", "")

                if output.strip():
                    # Deduplicate events - SDK sends same event twice (plain JSON + SSE format)
                    event_hash = hashlib.md5(f"{step_name}:{output}".encode()).hexdigest()
                    if event_hash in seen_events:
                        print(f"      ⏭️  Skipping duplicate event: {step_name} - {output[:50]}")
                        logger.info(f"      ⏭️  Skipping duplicate event: {step_name} - {output[:50]}")
                        continue
                    seen_events.add(event_hash)

                    logger.info(f"      📝 Step output: {step_name} - {output[:100]}")

                    # Format for display
                    formatted_output = f"```\n{output}\n```\n"

                    # Stream to callback if provided
                    if self.stream_callback:
                        self.stream_callback(formatted_output)

                    # Publish to control plane as message chunk
                    if self.control_plane and self.execution_id and workflow_message_id:
                        try:
                            print(f"📡 Publishing step output to control plane (len={len(formatted_output)})")
                            result = self.control_plane.publish_event(
                                execution_id=self.execution_id,
                                event_type="message_chunk",
                                data={
                                    "role": "assistant",
                                    "content": formatted_output,
                                    "is_chunk": True,
                                    "message_id": workflow_message_id,
                                    "source": "workflow",
                                    "metadata": {
                                        "step_name": step_name,
                                        "event_type": "step_output",
                                    }
                                }
                            )
                            print(f"✅ Published step output: {result}")
                        except Exception as e:
                            print(f"❌ Failed to publish workflow output: {e}")
                            logger.error(f"Failed to publish workflow output to control plane: {e}", exc_info=True)

                    accumulated_output.append(output)

                    # Track by step
                    if step_name not in step_outputs:
                        step_outputs[step_name] = []
                    step_outputs[step_name].append(output)

            elif event_type == "step_running":
                # Step is starting
                step = event_data.get("step", {})
                step_name = step.get("name", "unknown")
                current_step = step_name
                formatted = f"\n▶️  Step: {step_name}"
                logger.info(f"      ▶️  Starting step: {step_name}")
                accumulated_output.append(formatted)
                if self.stream_callback:
                    self.stream_callback(f"{formatted}\n")

                # Publish to control plane as message chunk
                if self.control_plane and self.execution_id and workflow_message_id:
                    try:
                        self.control_plane.publish_event(
                            execution_id=self.execution_id,
                            event_type="message_chunk",
                            data={
                                "role": "assistant",
                                "content": formatted,
                                "is_chunk": True,
                                "message_id": workflow_message_id,
                                "source": "workflow",
                                "metadata": {
                                    "step_name": step_name,
                                    "event_type": "step_start",
                                }
                            }
                        )
                    except Exception as e:
                        logger.debug(f"Failed to publish step_running to control plane: {e}")

            elif event_type == "step_complete":
                # Step finished
                step = event_data.get("step", {})
                step_name = step.get("name", "unknown")
                status = step.get("status", "unknown")
                icon = "✅" if status == "finished" else "❌"
                formatted = f"{icon} Step '{step_name}' {status}"
                logger.info(f"      {icon} Step completed: {step_name} ({status})")
                accumulated_output.append(formatted)
                current_step = None
                if self.stream_callback:
                    self.stream_callback(f"{formatted}\n")

                # Publish to control plane as message chunk
                if self.control_plane and self.execution_id and workflow_message_id:
                    try:
                        self.control_plane.publish_event(
                            execution_id=self.execution_id,
                            event_type="message_chunk",
                            data={
                                "role": "assistant",
                                "content": formatted,
                                "is_chunk": True,
                                "message_id": workflow_message_id,
                                "source": "workflow",
                                "metadata": {
                                    "step_name": step_name,
                                    "status": status,
                                    "event_type": "step_complete",
                                }
                            }
                        )
                    except Exception as e:
                        logger.debug(f"Failed to publish step_complete to control plane: {e}")

            elif event_type == "workflow_complete":
                # Workflow finished
                dag_name = event_data.get("dagName", "unknown")
                status = event_data.get("status", "unknown")
                success = event_data.get("success", False)
                icon = "✅" if success else "❌"
                formatted = f"{icon} Workflow '{dag_name}' {status}"
                logger.info(f"      {icon} Workflow completed: {dag_name} ({status}, success={success})")
                accumulated_output.append(formatted)
                if self.stream_callback:
                    self.stream_callback(f"{formatted}\n")

            elif event_type == "log":
                # Filter out noisy internal workflow runner logs
                message = event_data.get("message", "")
                level = event_data.get("level", "info")

                # Skip internal/noisy log messages
                noisy_patterns = [
                    "[SSE]",
                    "Published workflow stream event",
                    "Stored workflow data",
                    "Emitting log event",
                    "msg=status requestId",
                ]

                # Check if message contains any noisy pattern
                if any(pattern in message for pattern in noisy_patterns):
                    logger.debug(f"      🔇 Skipping noisy log: {message[:50]}")
                    continue

                # Only show meaningful log messages
                formatted = f"[{level.upper()}] {message}"
                logger.info(f"      💬 Log message: {message[:100]}")
                accumulated_output.append(formatted)
                if self.stream_callback:
                    self.stream_callback(f"{formatted}\n")

            elif event_type == "error":
                error_msg = event_data.get("message", str(event_data))
                formatted = f"❌ Error: {error_msg}"
                logger.error(f"      ❌ Workflow error: {error_msg}")
                accumulated_output.append(formatted)
                if self.stream_callback:
                    self.stream_callback(f"{formatted}\n")

            elif event_type == "heartbeat":
                # Skip heartbeat events in output
                logger.debug(f"      💓 Heartbeat (skipping)")
                continue

            else:
                # For unknown event types, log but don't show to user
                logger.info(f"      ❓ Unknown event type: {event_type}")
                logger.debug(f"      Raw data: {json.dumps(event_data)[:200]}")
                # Skip unknown events instead of showing raw JSON
                continue

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        result_text = f"\n{'='*60}\n"
        result_text += f"Python DSL Workflow: {workflow_name}\n"
        result_text += f"{'='*60}\n\n"
        result_text += f"Status: ✅ Completed\n"
        result_text += f"Duration: {duration:.2f}s\n"
        result_text += f"Runner: {runner}\n"
        result_text += f"\nTotal Events: {event_count}\n"

        # Include all captured output in the result
        if accumulated_output:
            result_text += f"\n{'='*60}\n"
            result_text += f"Workflow Output:\n"
            result_text += f"{'='*60}\n\n"
            result_text += "\n".join(accumulated_output)
            logger.info(f"✅ Workflow execution complete: {event_count} events processed, {len(accumulated_output)} output lines accumulated")
        else:
            logger.warning(f"⚠️  No workflow output accumulated (received {event_count} events but none produced output)")

        logger.debug(f"Final result preview: {result_text[:500]}")

        # Close the workflow streaming message (empty content marks end of stream)
        # The agent will process the workflow result and generate its OWN response
        # with a different message_id - that's the next message the user sees
        if self.control_plane and self.execution_id and workflow_message_id:
            try:
                print(f"\n📡 Closing workflow streaming message...")
                self.control_plane.publish_event(
                    execution_id=self.execution_id,
                    event_type="message_chunk",
                    data={
                        "role": "assistant",
                        "content": "",  # Empty - just marks end of workflow stream
                        "is_chunk": False,  # Final chunk - closes the streaming message
                        "message_id": workflow_message_id,
                        "source": "workflow",
                        "metadata": {
                            "event_type": "workflow_stream_end",
                            "duration": duration,
                            "total_events": event_count,
                        }
                    }
                )
                print(f"✅ Workflow stream closed\n")
            except Exception as e:
                logger.debug(f"Failed to close workflow stream: {e}")

        # Return result to agent - agent will process and respond with its OWN message_id
        return result_text

    def list_all_workflows(self) -> str:
        """
        List all available workflows in this skill instance.

        Returns:
            str: Formatted list of all workflows with their names, types, and descriptions.

        Examples:
            # List all workflows
            list_all_workflows()
        """
        if not self.workflows:
            return "No workflows defined in this skill instance."

        result = f"\n📋 Available Workflows ({len(self.workflows)}):\n"
        result += "=" * 60 + "\n\n"

        for idx, workflow in enumerate(self.workflows, 1):
            name = workflow.get("name", "unknown")
            wf_type = workflow.get("type", "unknown")
            safe_name = name.replace("-", "_").replace(" ", "_").lower()

            result += f"{idx}. {name} ({wf_type})\n"
            result += f"   Tool: execute_workflow_{safe_name}()\n"

            # Get description from workflow definition
            if wf_type == "json":
                wf_def = workflow.get("definition")
                if isinstance(wf_def, str):
                    try:
                        wf_data = json.loads(wf_def)
                        desc = wf_data.get("description", "No description")
                        steps = len(wf_data.get("steps", []))
                        result += f"   Description: {desc}\n"
                        result += f"   Steps: {steps}\n"
                    except:
                        pass
                elif isinstance(wf_def, dict):
                    desc = wf_def.get("description", "No description")
                    steps = len(wf_def.get("steps", []))
                    result += f"   Description: {desc}\n"
                    result += f"   Steps: {steps}\n"

            result += "\n"

        return result

    def execute_workflow(
        self,
        parameters: Optional[Dict[str, Any]] = None,
        override_timeout: Optional[int] = None,
    ) -> str:
        """
        Execute the first configured workflow with the provided parameters.

        LEGACY METHOD: For backward compatibility with single-workflow format.
        For multi-workflow skills, use execute_workflow_<name>() methods instead.

        This tool allows agents to run multi-step workflows by providing
        parameter values. The workflow will execute all steps in dependency
        order and return the results.

        The runner/environment is determined from the workflow definition itself,
        not passed as a parameter. This ensures workflows execute in their
        intended environments.

        Args:
            parameters: Dictionary of parameters to inject into the workflow.
                       These can be referenced in workflow steps using {{param_name}} syntax.
            override_timeout: Optional timeout override in seconds.
                            If not provided, uses the timeout from configuration.

        Returns:
            str: A formatted string containing the workflow execution results,
                 including step outputs and any errors encountered.

        Examples:
            # Execute a deployment workflow with environment parameter
            execute_workflow(parameters={"environment": "production", "version": "v1.2.3"})

            # Execute with timeout override
            execute_workflow(
                parameters={"data_source": "s3://bucket/data"},
                override_timeout=7200
            )
        """
        try:
            # For multi-workflow format, execute the first workflow
            if self.workflows:
                if len(self.workflows) > 1:
                    logger.warning(
                        "Multiple workflows defined but execute_workflow() called. "
                        "Executing first workflow. Use execute_workflow_<name>() for specific workflows."
                    )
                return self._execute_specific_workflow(self.workflows[0], parameters)

            # Legacy single-workflow format
            # Use provided parameters or empty dict
            params = parameters or {}

            # Determine runner from workflow definition or use default_runner/default_runner from config
            effective_runner = None
            if hasattr(self, 'workflow_type') and self.workflow_type == "json" and hasattr(self, 'workflow_data') and self.workflow_data:
                # Get runner from workflow definition first, then step-level, then default
                effective_runner = self.workflow_data.get("runner") or self.default_runner
            else:
                effective_runner = self.default_runner

            # Determine timeout
            effective_timeout = override_timeout or self.timeout

            # Stream start message
            if self.stream_callback:
                self.stream_callback(
                    f"🚀 Starting workflow execution...\n"
                    f"   Workflow Type: {getattr(self, 'workflow_type', 'unknown')}\n"
                    f"   Parameters: {json.dumps(params, indent=2)}\n"
                    f"   Runner: {effective_runner or 'default'}\n"
                    f"   Timeout: {effective_timeout}s\n\n"
                )

            # Execute based on workflow type
            if hasattr(self, 'workflow_type'):
                if self.workflow_type == "json":
                    result = self._execute_json_workflow(params, effective_runner, effective_timeout)
                elif self.workflow_type == "python_dsl":
                    result = self._execute_python_dsl_workflow(params, effective_runner, effective_timeout)
                else:
                    raise ValueError(f"Unsupported workflow type: {self.workflow_type}")
            else:
                raise ValueError("No workflow configured")

            # Stream completion message
            if self.stream_callback:
                self.stream_callback(f"\n✅ Workflow execution completed successfully\n")

            return result

        except Exception as e:
            error_msg = f"❌ Workflow execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            if self.stream_callback:
                self.stream_callback(f"\n{error_msg}\n")

            return error_msg

    def _execute_json_workflow(
        self,
        parameters: Dict[str, Any],
        runner: Optional[str],
        timeout: int
    ) -> str:
        """Execute a JSON workflow using kubiya SDK (remote execution)."""
        if not self.workflow_data:
            raise ValueError("No workflow definition available")

        if not self.kubiya_client:
            raise RuntimeError("Kubiya SDK client not initialized - cannot execute workflow remotely")

        workflow_name = self.workflow_data.get("name", "unknown")
        steps = self.workflow_data.get("steps", [])

        if self.stream_callback:
            self.stream_callback(f"📋 Workflow: {workflow_name}\n")
            self.stream_callback(f"   Steps: {len(steps)}\n")
            self.stream_callback(f"   Runner: {runner or self.default_runner}\n\n")

        try:
            # Execute workflow remotely using Kubiya SDK
            from datetime import datetime
            start_time = datetime.utcnow()

            if self.stream_callback:
                self.stream_callback(f"▶️  Submitting to runner '{runner or self.default_runner}'...\n\n")

            # Submit workflow definition to remote runner
            # The workflow_data already contains the complete workflow definition
            workflow_def = dict(self.workflow_data)

            # Ensure runner is set correctly
            workflow_def["runner"] = runner or self.default_runner

            # Remove 'triggers' key if it exists - not needed for direct execution
            # The DAG builder rejects this key when executing workflows directly
            if "triggers" in workflow_def:
                logger.debug(f"Removing 'triggers' key from workflow definition (not needed for execution)")
                workflow_def.pop("triggers")

            # ✅ Enable streaming to capture real-time workflow output
            response = self.kubiya_client.execute_workflow(
                workflow_definition=workflow_def,
                parameters=parameters,
                stream=True
            )

            # Accumulate streaming results
            accumulated_output = []
            event_count = 0

            # Iterate over streaming results
            for event in response:
                event_count += 1

                # Stream to user in real-time
                if self.stream_callback:
                    if isinstance(event, str):
                        self.stream_callback(f"{event}\n")
                        accumulated_output.append(event)
                    elif isinstance(event, dict):
                        event_type = event.get("type", "event")
                        event_data = event.get("data", event)
                        formatted_event = f"[{event_type}] {json.dumps(event_data, indent=2)}"
                        self.stream_callback(f"{formatted_event}\n")
                        accumulated_output.append(formatted_event)
                    else:
                        formatted_event = str(event)
                        self.stream_callback(f"{formatted_event}\n")
                        accumulated_output.append(formatted_event)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Format results
            result_text = f"\n{'='*60}\n"
            result_text += f"Workflow Execution Summary\n"
            result_text += f"{'='*60}\n\n"
            result_text += f"Workflow: {workflow_name}\n"
            result_text += f"Runner: {runner or self.default_runner}\n"
            result_text += f"Status: ✅ Completed\n"
            result_text += f"Duration: {duration:.2f}s\n"
            result_text += f"Steps: {len(steps)}\n"
            result_text += f"Parameters: {json.dumps(parameters, indent=2)}\n"
            result_text += f"\nTotal Events: {event_count}\n"

            # Include all captured output in the result
            if accumulated_output:
                result_text += f"\n{'='*60}\n"
                result_text += f"Workflow Output:\n"
                result_text += f"{'='*60}\n\n"
                result_text += "\n".join(accumulated_output)

            if self.stream_callback:
                self.stream_callback(f"\n✅ Workflow execution completed in {duration:.2f}s\n")

            return result_text

        except Exception as e:
            error_msg = f"JSON workflow execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)

    def _execute_python_dsl_workflow(
        self,
        parameters: Dict[str, Any],
        runner: Optional[str],
        timeout: int
    ) -> str:
        """Execute a Python DSL workflow using kubiya SDK (remote execution)."""
        if not self.python_dsl_code:
            raise ValueError("No Python DSL code available")

        if not self.kubiya_client:
            raise RuntimeError("Kubiya SDK client not initialized - cannot execute workflow remotely")

        if self.stream_callback:
            self.stream_callback(f"🐍 Submitting Python DSL workflow for remote execution...\n\n")

        try:
            # Parse the Python DSL code to extract workflow name
            # For now, we'll create a workflow definition that the runner can execute
            workflow_name = "python-dsl-workflow"

            # Try to extract workflow name from code
            if "name=" in self.python_dsl_code:
                try:
                    import re
                    match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', self.python_dsl_code)
                    if match:
                        workflow_name = match.group(1)
                except:
                    pass

            if self.stream_callback:
                self.stream_callback(f"📋 Workflow: {workflow_name}\n")
                self.stream_callback(f"   Runner: {runner or self.default_runner}\n")
                self.stream_callback(f"   Parameters: {json.dumps(parameters)}\n\n")

            # Create workflow definition for remote execution
            # The runner will execute the Python DSL code
            workflow_definition = {
                "name": workflow_name,
                "description": "Python DSL workflow",
                "runner": runner or self.default_runner,
                "steps": [
                    {
                        "name": "execute_python_dsl",
                        "description": "Execute Python DSL workflow code",
                        "executor": {
                            "type": "python_dsl",
                            "config": {
                                "code": self.python_dsl_code
                            }
                        }
                    }
                ]
            }

            # Execute workflow remotely using Kubiya SDK
            from datetime import datetime
            start_time = datetime.utcnow()

            if self.stream_callback:
                self.stream_callback(f"▶️  Submitting to runner '{runner or self.default_runner}'...\n\n")

            # ✅ Enable streaming to capture real-time workflow output
            response = self.kubiya_client.execute_workflow(
                workflow_definition=workflow_definition,
                parameters=parameters,
                stream=True
            )

            # Accumulate streaming results
            accumulated_output = []
            event_count = 0

            # Iterate over streaming results
            for event in response:
                event_count += 1

                # Stream to user in real-time
                if self.stream_callback:
                    if isinstance(event, str):
                        self.stream_callback(f"{event}\n")
                        accumulated_output.append(event)
                    elif isinstance(event, dict):
                        event_type = event.get("type", "event")
                        event_data = event.get("data", event)
                        formatted_event = f"[{event_type}] {json.dumps(event_data, indent=2)}"
                        self.stream_callback(f"{formatted_event}\n")
                        accumulated_output.append(formatted_event)
                    else:
                        formatted_event = str(event)
                        self.stream_callback(f"{formatted_event}\n")
                        accumulated_output.append(formatted_event)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Format results
            result_text = f"\n{'='*60}\n"
            result_text += f"Python DSL Workflow Execution Summary\n"
            result_text += f"{'='*60}\n\n"
            result_text += f"Workflow: {workflow_name}\n"
            result_text += f"Runner: {runner or self.default_runner}\n"
            result_text += f"Status: ✅ Completed\n"
            result_text += f"Duration: {duration:.2f}s\n"
            result_text += f"Parameters: {json.dumps(parameters, indent=2)}\n"
            result_text += f"\nTotal Events: {event_count}\n"

            # Include all captured output in the result
            if accumulated_output:
                result_text += f"\n{'='*60}\n"
                result_text += f"Workflow Output:\n"
                result_text += f"{'='*60}\n\n"
                result_text += "\n".join(accumulated_output)

            if self.stream_callback:
                self.stream_callback(f"\n✅ Workflow execution completed in {duration:.2f}s\n")

            return result_text

        except Exception as e:
            error_msg = f"Python DSL workflow execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)

    def _inject_parameters(self, config: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Inject parameters into configuration values."""
        result = {}

        for key, value in config.items():
            if isinstance(value, str):
                # Replace {{param_name}} with parameter value
                for param_name, param_value in parameters.items():
                    value = value.replace(f"{{{{{param_name}}}}}", str(param_value))
                result[key] = value
            elif isinstance(value, dict):
                result[key] = self._inject_parameters(value, parameters)
            elif isinstance(value, list):
                result[key] = [
                    self._inject_parameters(item, parameters) if isinstance(item, dict)
                    else str(item).replace(f"{{{{{pn}}}}}", str(pv)) if isinstance(item, str) else item
                    for item in value
                    for pn, pv in [(pn, pv)]
                    for pn, pv in [(list(parameters.keys())[0] if parameters else "", list(parameters.values())[0] if parameters else "")]
                ][:len(value)]
                # Simplified version
                result[key] = value
            else:
                result[key] = value

        return result

    def list_workflow_steps(self, workflow_name: Optional[str] = None) -> str:
        """
        List all steps in the configured workflow(s).

        LEGACY METHOD: For multi-workflow skills, this lists all workflows.
        For legacy single-workflow format, lists steps of that workflow.

        Args:
            workflow_name: Optional workflow name to filter by (multi-workflow only)

        Returns:
            str: A formatted string listing all workflow steps with their
                 descriptions, executor types, and dependencies.

        Examples:
            # List all steps in the workflow
            list_workflow_steps()
        """
        try:
            # Multi-workflow format
            if self.workflows:
                if workflow_name:
                    # Find specific workflow
                    workflow = next((w for w in self.workflows if w.get("name") == workflow_name), None)
                    if not workflow:
                        return f"❌ Workflow '{workflow_name}' not found"
                    workflows_to_show = [workflow]
                else:
                    workflows_to_show = self.workflows

                result = f"\n📋 Workflows: {len(workflows_to_show)}\n"
                result += "=" * 60 + "\n\n"

                for wf in workflows_to_show:
                    wf_name = wf.get("name", "unknown")
                    wf_type = wf.get("type", "unknown")

                    result += f"Workflow: {wf_name} ({wf_type})\n"

                    if wf_type == "json":
                        wf_def = wf.get("definition")
                        if isinstance(wf_def, str):
                            try:
                                wf_data = json.loads(wf_def)
                            except:
                                result += "   ❌ Invalid JSON definition\n\n"
                                continue
                        else:
                            wf_data = wf_def

                        if wf_data:
                            workflow_desc = wf_data.get("description", "No description")
                            steps = wf_data.get("steps", [])

                            result += f"   Description: {workflow_desc}\n"
                            result += f"   Total Steps: {len(steps)}\n\n"

                            if steps:
                                result += "   Steps:\n"
                                for idx, step in enumerate(steps, 1):
                                    step_name = step.get("name", "unknown")
                                    step_desc = step.get("description", "")
                                    executor = step.get("executor", {})
                                    executor_type = executor.get("type", "unknown")
                                    depends_on = step.get("depends_on", [])

                                    result += f"   {idx}. {step_name}\n"
                                    if step_desc:
                                        result += f"      Description: {step_desc}\n"
                                    result += f"      Executor: {executor_type}\n"
                                    if depends_on:
                                        result += f"      Depends on: {', '.join(depends_on)}\n"
                            else:
                                result += "   (No steps defined)\n"

                    elif wf_type == "python_dsl":
                        result += "   Type: Python DSL\n"
                        result += "   (To view steps, execute the workflow)\n"

                    result += "\n"

                return result

            # Legacy single-workflow format
            if self.workflow_type == "json":
                if not self.workflow_data:
                    return "❌ No workflow definition available"

                workflow_name_legacy = self.workflow_data.get("name", "unknown")
                workflow_desc = self.workflow_data.get("description", "No description")
                steps = self.workflow_data.get("steps", [])

                result = f"\n📋 Workflow: {workflow_name_legacy}\n"
                result += f"   Description: {workflow_desc}\n"
                result += f"   Total Steps: {len(steps)}\n\n"

                if not steps:
                    result += "   (No steps defined)\n"
                    return result

                result += "Steps:\n"
                for idx, step in enumerate(steps, 1):
                    step_name = step.get("name", "unknown")
                    step_desc = step.get("description", "")
                    executor = step.get("executor", {})
                    executor_type = executor.get("type", "unknown")
                    depends_on = step.get("depends_on", [])

                    result += f"\n{idx}. {step_name}\n"
                    if step_desc:
                        result += f"   Description: {step_desc}\n"
                    result += f"   Executor: {executor_type}\n"
                    if depends_on:
                        result += f"   Depends on: {', '.join(depends_on)}\n"

                return result

            elif self.workflow_type == "python_dsl":
                return f"\n🐍 Python DSL Workflow\n\nTo view steps, execute the workflow.\n"

            else:
                return "❌ No workflow configured"

        except Exception as e:
            logger.error(f"Failed to list workflow steps: {e}", exc_info=True)
            return f"❌ Error listing workflow steps: {str(e)}"

    def get_workflow_info(self) -> str:
        """
        Get detailed information about the configured workflow(s).

        This tool provides comprehensive information about the workflow
        including its name, description, type, number of steps, triggers,
        and configuration.

        For multi-workflow skills, lists all workflows with their configurations.
        For legacy single-workflow format, shows that workflow's information.

        Returns:
            str: A formatted string with complete workflow information.

        Examples:
            # Get workflow information
            get_workflow_info()
        """
        try:
            result = f"\n{'='*60}\n"
            result += f"Workflow Executor Information\n"
            result += f"{'='*60}\n\n"

            result += f"Validation Enabled: {self.validation_enabled}\n"
            result += f"Timeout: {self.timeout}s\n"
            result += f"Default Runner: {self.default_runner or 'None'}\n"
            result += f"Total Workflows: {len(self.workflows)}\n\n"

            # Multi-workflow format
            if self.workflows:
                result += "Configured Workflows:\n"
                result += "-" * 60 + "\n\n"

                for idx, workflow in enumerate(self.workflows, 1):
                    wf_name = workflow.get("name", "unknown")
                    wf_type = workflow.get("type", "unknown")
                    safe_name = wf_name.replace("-", "_").replace(" ", "_").lower()

                    result += f"{idx}. {wf_name}\n"
                    result += f"   Type: {wf_type}\n"
                    result += f"   Tool: execute_workflow_{safe_name}()\n"

                    if wf_type == "json":
                        wf_def = workflow.get("definition")
                        if isinstance(wf_def, str):
                            try:
                                wf_data = json.loads(wf_def)
                            except:
                                result += "   ❌ Invalid JSON definition\n\n"
                                continue
                        else:
                            wf_data = wf_def

                        if wf_data:
                            workflow_desc = wf_data.get("description", "No description")
                            steps = wf_data.get("steps", [])
                            triggers = wf_data.get("triggers", [])
                            workflow_runner = wf_data.get("runner")

                            result += f"   Description: {workflow_desc}\n"
                            result += f"   Steps: {len(steps)}\n"
                            result += f"   Triggers: {len(triggers)}\n"

                            # Show runner hierarchy
                            if workflow_runner:
                                result += f"   Runner: {workflow_runner} (specified in workflow)\n"
                            elif self.default_runner:
                                result += f"   Runner: {self.default_runner} (from skill config)\n"
                            else:
                                result += f"   Runner: default (no runner specified)\n"

                    elif wf_type == "python_dsl":
                        python_code = workflow.get("code", "")
                        result += f"   Code Length: {len(python_code)} characters\n"

                    result += "\n"

                return result

            # Legacy single-workflow format
            result += f"Type: {self.workflow_type or 'none'}\n\n"

            if self.workflow_type == "json" and self.workflow_data:
                workflow_name = self.workflow_data.get("name", "unknown")
                workflow_desc = self.workflow_data.get("description", "No description")
                steps = self.workflow_data.get("steps", [])
                triggers = self.workflow_data.get("triggers", [])
                workflow_runner = self.workflow_data.get("runner")

                result += f"Name: {workflow_name}\n"
                result += f"Description: {workflow_desc}\n"
                result += f"Steps: {len(steps)}\n"
                result += f"Triggers: {len(triggers)}\n"

                # Show runner hierarchy
                if workflow_runner:
                    result += f"Workflow Runner: {workflow_runner} (will be used for execution)\n"
                elif self.default_runner:
                    result += f"Workflow Runner: {self.default_runner} (from skill config)\n"
                else:
                    result += f"Workflow Runner: default (no runner specified)\n"

            elif self.workflow_type == "python_dsl":
                result += f"Python DSL Workflow\n"
                result += f"Code Length: {len(self.python_dsl_code or '')} characters\n"

            return result

        except Exception as e:
            logger.error(f"Failed to get workflow info: {e}", exc_info=True)
            return f"❌ Error getting workflow info: {str(e)}"
