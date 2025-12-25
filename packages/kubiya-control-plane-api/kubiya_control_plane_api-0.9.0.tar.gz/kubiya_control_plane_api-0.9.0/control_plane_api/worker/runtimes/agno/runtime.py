"""
Agno runtime implementation.

This is the main runtime class that provides Agno framework integration
for the Agent Control Plane.
"""

import asyncio
import queue
import threading
import time
import structlog
from typing import Dict, Any, Optional, AsyncIterator, Callable, TYPE_CHECKING

from ..base import (
    RuntimeType,
    RuntimeExecutionResult,
    RuntimeExecutionContext,
    RuntimeCapabilities,
    BaseRuntime,
    RuntimeRegistry,
)
from control_plane_api.worker.services.event_publisher import (
    EventPublisher,
    EventPublisherConfig,
    EventPriority,
)
from control_plane_api.worker.utils.tool_validation import (
    validate_and_sanitize_tools,
    sanitize_tool_name,
)

from .config import build_agno_agent_config
from .hooks import create_tool_hook_for_streaming, create_tool_hook_with_callback
from .mcp_builder import build_agno_mcp_tools
from .utils import (
    build_conversation_messages,
    extract_usage,
    extract_tool_messages,
    extract_response_content,
)

if TYPE_CHECKING:
    from control_plane_client import ControlPlaneClient
    from services.cancellation_manager import CancellationManager

logger = structlog.get_logger(__name__)


@RuntimeRegistry.register(RuntimeType.DEFAULT)
class AgnoRuntime(BaseRuntime):
    """
    Runtime implementation using Agno framework.

    This runtime wraps the Agno-based agent execution logic,
    providing a clean interface that conforms to the AgentRuntime protocol.

    Features:
    - LiteLLM-based model execution
    - Real-time streaming with event batching
    - Tool execution hooks
    - Conversation history support
    - Comprehensive usage tracking
    """

    def __init__(
        self,
        control_plane_client: "ControlPlaneClient",
        cancellation_manager: "CancellationManager",
        **kwargs,
    ):
        """
        Initialize the Agno runtime.

        Args:
            control_plane_client: Client for Control Plane API
            cancellation_manager: Manager for execution cancellation
            **kwargs: Additional configuration options
        """
        super().__init__(control_plane_client, cancellation_manager, **kwargs)
        self._custom_tools: Dict[str, Any] = {}  # tool_id -> tool instance

    def get_runtime_type(self) -> RuntimeType:
        """Return RuntimeType.DEFAULT."""
        return RuntimeType.DEFAULT

    def get_capabilities(self) -> RuntimeCapabilities:
        """Return Agno runtime capabilities."""
        return RuntimeCapabilities(
            streaming=True,
            tools=True,
            mcp=True,  # Agno supports MCP via MCPTools
            hooks=True,
            cancellation=True,
            conversation_history=True,
            custom_tools=True  # Agno supports custom Python tools
        )

    def _validate_mcp_tool_names(self, mcp_tool: Any, execution_id: str) -> Any:
        """
        Validate and sanitize MCP tool function names.

        This ensures MCP tools from external servers meet universal LLM provider requirements.
        Agno's MCPTools.functions property contains the actual tool definitions.

        Args:
            mcp_tool: Connected MCPTools instance
            execution_id: Execution ID for logging

        Returns:
            The MCP tool instance with validated function names
        """
        if not hasattr(mcp_tool, 'functions') or not mcp_tool.functions:
            return mcp_tool

        server_name = getattr(mcp_tool, '_server_name', mcp_tool.name)

        # Convert functions dict to list of Function objects for validation
        # mcp_tool.functions is a Dict[str, Function], we need to validate the Function objects
        functions_list = list(mcp_tool.functions.values())

        # Validate and sanitize the function names
        validated_functions, validation_report = validate_and_sanitize_tools(
            functions_list,
            tool_name_getter=lambda f: getattr(f, 'name', str(f)),
            auto_fix=True,
            provider_context=f"agno_mcp_{server_name}"
        )

        # Log validation results
        sanitized_count = sum(1 for r in validation_report if r['action'] == 'sanitized')
        filtered_count = sum(1 for r in validation_report if r['action'] == 'filtered')

        if sanitized_count > 0:
            self.logger.warning(
                "mcp_tool_names_sanitized",
                server_name=server_name,
                execution_id=execution_id,
                sanitized_count=sanitized_count,
                total_functions=len(mcp_tool.functions),
                details=[r for r in validation_report if r['action'] == 'sanitized'][:5]  # Limit details
            )

        if filtered_count > 0:
            self.logger.error(
                "mcp_tool_names_filtered",
                server_name=server_name,
                execution_id=execution_id,
                filtered_count=filtered_count,
                total_functions=len(mcp_tool.functions),
                details=[r for r in validation_report if r['action'] == 'filtered']
            )

        # Reconstruct the functions dict from validated Function objects
        # Preserve the Dict[str, Function] structure that Agno expects
        from collections import OrderedDict
        validated_functions_dict = OrderedDict()
        for func in validated_functions:
            func_name = getattr(func, 'name', str(func))
            validated_functions_dict[func_name] = func

        # Update the MCP tool with validated functions dict
        mcp_tool.functions = validated_functions_dict

        return mcp_tool

    async def _execute_impl(
        self, context: RuntimeExecutionContext
    ) -> RuntimeExecutionResult:
        """
        Execute agent using Agno framework without streaming.

        Args:
            context: Execution context with prompt, history, config

        Returns:
            RuntimeExecutionResult with response and metadata
        """
        mcp_tools_instances = []

        try:
            # Build MCP tools from context
            mcp_tools_instances = build_agno_mcp_tools(context.mcp_servers)

            # Connect MCP tools
            connected_mcp_tools = []
            for mcp_tool in mcp_tools_instances:
                try:
                    await mcp_tool.connect()

                    # Verify the tool is actually initialized (agno doesn't raise on failure)
                    if not mcp_tool.initialized:
                        server_name = getattr(mcp_tool, '_server_name', mcp_tool.name)
                        error_msg = f"Failed to initialize MCP tool: {server_name}"
                        self.logger.error(
                            "mcp_tool_initialization_failed",
                            server_name=server_name,
                            execution_id=context.execution_id,
                            error=error_msg,
                        )
                        raise RuntimeError(error_msg)

                    # Verify it has tools available
                    if not mcp_tool.functions:
                        server_name = getattr(mcp_tool, '_server_name', mcp_tool.name)
                        error_msg = f"MCP tool {server_name} has no functions available"
                        self.logger.error(
                            "mcp_tool_has_no_functions",
                            server_name=server_name,
                            execution_id=context.execution_id,
                            error=error_msg,
                        )
                        raise RuntimeError(error_msg)

                    self.logger.info(
                        "mcp_tool_connected",
                        execution_id=context.execution_id,
                        server_name=getattr(mcp_tool, '_server_name', mcp_tool.name),
                        function_count=len(mcp_tool.functions),
                    )

                    # UNIVERSAL VALIDATION: Validate MCP tool names
                    validated_mcp_tool = self._validate_mcp_tool_names(mcp_tool, context.execution_id)
                    connected_mcp_tools.append(validated_mcp_tool)

                except Exception as e:
                    server_name = getattr(mcp_tool, '_server_name', mcp_tool.name)
                    self.logger.error(
                        "mcp_tool_connection_failed",
                        error=str(e),
                        error_type=type(e).__name__,
                        server_name=server_name,
                        execution_id=context.execution_id,
                    )
                    import traceback
                    self.logger.debug(
                        "mcp_tool_connection_error_traceback",
                        traceback=traceback.format_exc(),
                        execution_id=context.execution_id,
                    )

                    # Publish MCP connection error event
                    try:
                        from control_plane_api.worker.utils.error_publisher import (
                            ErrorEventPublisher, ErrorSeverity, ErrorCategory
                        )
                        error_publisher = ErrorEventPublisher(self.control_plane)
                        await error_publisher.publish_error(
                            execution_id=context.execution_id,
                            exception=e,
                            severity=ErrorSeverity.WARNING,
                            category=ErrorCategory.MCP_CONNECTION,
                            stage="initialization",
                            component="mcp_server",
                            operation=f"connect_{server_name}",
                            metadata={"server_name": server_name},
                            recovery_actions=[
                                "Verify MCP server is running and accessible",
                                "Check MCP server configuration",
                                "Review network connectivity",
                            ],
                        )
                    except Exception as publish_error:
                        # Log warning but don't block execution
                        self.logger.warning(
                            f"Failed to publish MCP connection error: {publish_error}",
                            execution_id=context.execution_id,
                        )

                    # Continue with other MCP tools even if one fails

            # Use only successfully connected tools
            mcp_tools_instances = connected_mcp_tools

            # Merge regular skills with custom tools
            # IMPORTANT: Deep copy skills to isolate Function objects between executions
            # This prevents schema corruption from shared mutable state in Function.parameters
            from copy import deepcopy

            all_skills = []
            if context.skills:
                for skill in context.skills:
                    try:
                        # Deep copy the skill to ensure Function objects are isolated
                        # This prevents process_entrypoint() from modifying shared state
                        if hasattr(skill, 'functions') and hasattr(skill.functions, 'items'):
                            copied_skill = deepcopy(skill)
                            all_skills.append(copied_skill)
                            self.logger.debug(
                                "skill_deep_copied",
                                skill_name=getattr(skill, 'name', 'unknown'),
                                function_count=len(skill.functions) if hasattr(skill, 'functions') else 0,
                                execution_id=context.execution_id,
                            )
                        else:
                            # For non-Toolkit skills, use as-is
                            all_skills.append(skill)
                    except Exception as e:
                        # If deep copy fails, fall back to original skill and log warning
                        self.logger.warning(
                            "skill_deep_copy_failed_using_original",
                            skill_name=getattr(skill, 'name', 'unknown'),
                            error=str(e),
                            error_type=type(e).__name__,
                            execution_id=context.execution_id,
                        )
                        all_skills.append(skill)

            # Add custom tools
            if self._custom_tools:
                for tool_id, custom_tool in self._custom_tools.items():
                    try:
                        # Get toolkit from custom tool
                        toolkit = custom_tool.get_tools()

                        # Extract tools - handle both Toolkit objects and iterables
                        if hasattr(toolkit, 'tools'):
                            all_skills.extend(toolkit.tools)
                        elif hasattr(toolkit, '__iter__'):
                            all_skills.extend(toolkit)
                        else:
                            all_skills.append(toolkit)

                        self.logger.debug(
                            "custom_tool_loaded",
                            tool_id=tool_id,
                            execution_id=context.execution_id
                        )
                    except Exception as e:
                        self.logger.error(
                            "custom_tool_load_failed",
                            tool_id=tool_id,
                            error=str(e),
                            execution_id=context.execution_id
                        )

            # Extract metadata for Langfuse tracking
            user_id = None
            session_id = None
            agent_name = None

            if context.user_metadata:
                user_id = context.user_metadata.get("user_email") or context.user_metadata.get("user_id")
                session_id = context.user_metadata.get("session_id") or context.execution_id
                agent_name = context.user_metadata.get("agent_name") or context.agent_id

            # DEBUG: Log metadata extraction
            self.logger.warning(
                "🔍 DEBUG: AGNO RUNTIME (_execute_impl) - METADATA EXTRACTION",
                context_user_metadata=context.user_metadata,
                extracted_user_id=user_id,
                extracted_session_id=session_id,
                extracted_agent_name=agent_name,
                organization_id=context.organization_id,
            )

            # Create Agno agent with all tools (skills + MCP tools) and metadata
            agent = build_agno_agent_config(
                agent_id=context.agent_id,
                system_prompt=context.system_prompt,
                model_id=context.model_id,
                skills=all_skills,
                mcp_tools=mcp_tools_instances,
                tool_hooks=None,
                user_id=user_id,
                session_id=session_id,
                organization_id=context.organization_id,
                agent_name=agent_name,
                skill_configs=context.skill_configs,
            )

            # Register for cancellation
            self.cancellation_manager.register(
                execution_id=context.execution_id,
                instance=agent,
                instance_type="agent",
            )

            # Log tool schema snapshots for debugging
            # This helps detect schema inconsistencies and parameter mismatches
            if context.execution_id:
                for skill in all_skills:
                    if hasattr(skill, 'functions') and hasattr(skill.functions, 'items'):
                        skill_name = getattr(skill, 'name', 'unknown')
                        for func_name, func_obj in skill.functions.items():
                            if hasattr(func_obj, 'parameters') and isinstance(func_obj.parameters, dict):
                                param_names = list(func_obj.parameters.get('properties', {}).keys())
                                self.logger.debug(
                                    "tool_schema_snapshot",
                                    execution_id=context.execution_id,
                                    skill_name=skill_name,
                                    tool_name=func_name,
                                    parameters=param_names,
                                )

            # Build conversation context
            messages = build_conversation_messages(context.conversation_history)

            # Determine if we need async execution (when MCP tools are present)
            has_async_tools = len(mcp_tools_instances) > 0

            # Execute without streaming
            if has_async_tools:
                # Use async agent.arun() for MCP tools
                if messages:
                    result = await agent.arun(context.prompt, stream=False, messages=messages)
                else:
                    result = await agent.arun(context.prompt, stream=False)
            else:
                # Use sync agent.run() for non-MCP tools
                def run_agent():
                    if messages:
                        return agent.run(context.prompt, stream=False, messages=messages)
                    else:
                        return agent.run(context.prompt, stream=False)

                # Run in thread pool to avoid blocking
                result = await asyncio.to_thread(run_agent)

            # Cleanup
            self.cancellation_manager.unregister(context.execution_id)

            # Extract response and metadata
            response_content = extract_response_content(result)
            usage = extract_usage(result)
            tool_messages = extract_tool_messages(result)

            return RuntimeExecutionResult(
                response=response_content,
                usage=usage,
                success=True,
                finish_reason="stop",
                run_id=getattr(result, "run_id", None),
                model=context.model_id,
                tool_messages=tool_messages,
            )

        except asyncio.CancelledError:
            # Handle cancellation
            self.cancellation_manager.cancel(context.execution_id)
            self.cancellation_manager.unregister(context.execution_id)
            raise

        except Exception as e:
            self.logger.error(
                "agno_execution_failed",
                execution_id=context.execution_id,
                error=str(e),
            )
            self.cancellation_manager.unregister(context.execution_id)

            # Publish error event
            try:
                from control_plane_api.worker.utils.error_publisher import (
                    ErrorEventPublisher, ErrorSeverity, ErrorCategory
                )
                error_publisher = ErrorEventPublisher(self.control_plane)
                await error_publisher.publish_error(
                    execution_id=context.execution_id,
                    exception=e,
                    severity=ErrorSeverity.CRITICAL,
                    category=ErrorCategory.UNKNOWN,
                    stage="execution",
                    component="agno_runtime",
                    operation="agent_execution",
                    include_stack_trace=True,
                )
            except Exception:
                pass  # Never break execution flow

            return RuntimeExecutionResult(
                response="",
                usage={},
                success=False,
                error=str(e),
            )

        finally:
            # Close MCP tool connections
            for mcp_tool in mcp_tools_instances:
                try:
                    await mcp_tool.close()
                    self.logger.debug(
                        "mcp_tool_closed",
                        execution_id=context.execution_id,
                    )
                except Exception as e:
                    self.logger.error(
                        "mcp_tool_close_failed",
                        error=str(e),
                        execution_id=context.execution_id,
                    )

    async def _stream_execute_impl(
        self,
        context: RuntimeExecutionContext,
        event_callback: Optional[Callable[[Dict], None]] = None,
    ) -> AsyncIterator[RuntimeExecutionResult]:
        """
        Execute agent with streaming using Agno framework with efficient event batching.

        This implementation uses the EventPublisher service to batch message chunks,
        reducing HTTP requests by 90-96% while keeping tool events immediate.

        Args:
            context: Execution context
            event_callback: Optional callback for real-time events

        Yields:
            RuntimeExecutionResult chunks as they arrive in real-time
        """
        # Create event publisher with batching
        event_publisher = EventPublisher(
            control_plane=self.control_plane,
            execution_id=context.execution_id,
            config=EventPublisherConfig.from_env(),
        )

        mcp_tools_instances = []

        try:
            # Build MCP tools from context
            mcp_tools_instances = build_agno_mcp_tools(context.mcp_servers)

            # Connect MCP tools
            connected_mcp_tools = []
            for mcp_tool in mcp_tools_instances:
                try:
                    await mcp_tool.connect()

                    # Verify the tool is actually initialized (agno doesn't raise on failure)
                    if not mcp_tool.initialized:
                        server_name = getattr(mcp_tool, '_server_name', mcp_tool.name)
                        error_msg = f"Failed to initialize MCP tool: {server_name}"
                        self.logger.error(
                            "mcp_tool_initialization_failed",
                            server_name=server_name,
                            execution_id=context.execution_id,
                            error=error_msg,
                        )
                        raise RuntimeError(error_msg)

                    # Verify it has tools available
                    if not mcp_tool.functions:
                        server_name = getattr(mcp_tool, '_server_name', mcp_tool.name)
                        error_msg = f"MCP tool {server_name} has no functions available"
                        self.logger.error(
                            "mcp_tool_has_no_functions",
                            server_name=server_name,
                            execution_id=context.execution_id,
                            error=error_msg,
                        )
                        raise RuntimeError(error_msg)

                    self.logger.info(
                        "mcp_tool_connected_streaming",
                        execution_id=context.execution_id,
                        server_name=getattr(mcp_tool, '_server_name', mcp_tool.name),
                        function_count=len(mcp_tool.functions),
                    )

                    # UNIVERSAL VALIDATION: Validate MCP tool names
                    validated_mcp_tool = self._validate_mcp_tool_names(mcp_tool, context.execution_id)
                    connected_mcp_tools.append(validated_mcp_tool)

                except Exception as e:
                    self.logger.error(
                        "mcp_tool_connection_failed_streaming",
                        error=str(e),
                        error_type=type(e).__name__,
                        server_name=getattr(mcp_tool, '_server_name', mcp_tool.name),
                        execution_id=context.execution_id,
                    )
                    import traceback
                    self.logger.debug(
                        "mcp_tool_connection_error_traceback",
                        traceback=traceback.format_exc(),
                        execution_id=context.execution_id,
                    )
                    # Continue with other MCP tools even if one fails

            # Use only successfully connected tools
            mcp_tools_instances = connected_mcp_tools

            # Build conversation context
            messages = build_conversation_messages(context.conversation_history)

            # Determine if we need async execution (when MCP tools are present)
            has_async_tools = len(mcp_tools_instances) > 0

            # Stream execution - publish events INSIDE the thread (like old code)
            accumulated_response = ""
            run_result = None

            # Create queue for streaming chunks from thread to async
            chunk_queue = queue.Queue()

            # Generate unique message ID
            message_id = f"{context.execution_id}_msg_{int(time.time() * 1000000)}"

            # Merge regular skills with custom tools
            all_skills = list(context.skills) if context.skills else []

            # Add custom tools
            if self._custom_tools:
                for tool_id, custom_tool in self._custom_tools.items():
                    try:
                        # Get toolkit from custom tool
                        toolkit = custom_tool.get_tools()

                        # Extract tools - handle both Toolkit objects and iterables
                        if hasattr(toolkit, 'tools'):
                            all_skills.extend(toolkit.tools)
                        elif hasattr(toolkit, '__iter__'):
                            all_skills.extend(toolkit)
                        else:
                            all_skills.append(toolkit)

                        self.logger.debug(
                            "custom_tool_loaded_streaming",
                            tool_id=tool_id,
                            execution_id=context.execution_id
                        )
                    except Exception as e:
                        self.logger.error(
                            "custom_tool_load_failed_streaming",
                            tool_id=tool_id,
                            error=str(e),
                            execution_id=context.execution_id
                        )

            # Initialize enforcement service
            enforcement_context = {
                "organization_id": context.organization_id,
                "user_email": context.user_email,
                "user_id": context.user_id,
                "user_roles": context.user_roles or [],
                "team_id": context.team_id,
                "team_name": context.team_name,
                "agent_id": context.agent_id,
                "environment": context.environment,
                "model_id": context.model_id,
            }

            # Import enforcement dependencies
            from control_plane_api.app.lib.policy_enforcer_client import create_policy_enforcer_client
            from control_plane_api.worker.services.tool_enforcement import ToolEnforcementService
            import os

            # Get enforcer client (using the same token as the control plane)
            enforcer_client = None
            enforcement_service = None

            # Check if enforcement is enabled (opt-in via environment variable)
            enforcement_enabled = os.environ.get("KUBIYA_ENFORCE_ENABLED", "").lower() in ("true", "1", "yes")

            if not enforcement_enabled:
                self.logger.info(
                    "policy_enforcement_disabled",
                    reason="KUBIYA_ENFORCE_ENABLED not set",
                    execution_id=context.execution_id[:8],
                    note="Set KUBIYA_ENFORCE_ENABLED=true to enable policy enforcement"
                )
            else:
                try:
                    # Get enforcer URL - default to control plane enforcer proxy
                    enforcer_url = os.environ.get("ENFORCER_SERVICE_URL")
                    if not enforcer_url:
                        # Use control plane's enforcer proxy as default
                        control_plane_url = os.environ.get("CONTROL_PLANE_URL", "http://localhost:8000")
                        enforcer_url = f"{control_plane_url.rstrip('/')}/api/v1/enforcer"
                        self.logger.debug(
                            "using_control_plane_enforcer_proxy",
                            enforcer_url=enforcer_url,
                            execution_id=context.execution_id[:8],
                        )

                    # Use async context manager properly (we're in an async function)
                    enforcer_client_context = create_policy_enforcer_client(
                        enforcer_url=enforcer_url,
                        api_key=self.control_plane.api_key,
                        auth_type="UserKey"
                    )
                    enforcer_client = await enforcer_client_context.__aenter__()
                    if enforcer_client:
                        enforcement_service = ToolEnforcementService(enforcer_client)
                        self.logger.info(
                            "policy_enforcement_enabled",
                            enforcer_url=enforcer_url,
                            execution_id=context.execution_id[:8],
                        )
                except Exception as e:
                    self.logger.warning(
                        "enforcement_service_init_failed",
                        error=str(e),
                        execution_id=context.execution_id[:8],
                    )

            # Create tool hook that publishes directly to Control Plane with enforcement
            tool_hook = create_tool_hook_for_streaming(
                control_plane=self.control_plane,
                execution_id=context.execution_id,
                message_id=message_id,  # Link tools to this assistant message turn
                enforcement_context=enforcement_context,
                enforcement_service=enforcement_service,
            )

            # Extract metadata for Langfuse tracking
            user_id = None
            session_id = None
            agent_name = None

            if context.user_metadata:
                user_id = context.user_metadata.get("user_email") or context.user_metadata.get("user_id")
                session_id = context.user_metadata.get("session_id") or context.execution_id
                agent_name = context.user_metadata.get("agent_name") or context.agent_id

            # DEBUG: Log metadata extraction
            self.logger.warning(
                "🔍 DEBUG: AGNO RUNTIME (_stream_execute_impl) - METADATA EXTRACTION",
                context_user_metadata=context.user_metadata,
                extracted_user_id=user_id,
                extracted_session_id=session_id,
                extracted_agent_name=agent_name,
                organization_id=context.organization_id,
            )

            # Create Agno agent with all tools (skills + MCP tools), tool hooks, and metadata
            agent = build_agno_agent_config(
                agent_id=context.agent_id,
                system_prompt=context.system_prompt,
                model_id=context.model_id,
                skills=all_skills,
                mcp_tools=mcp_tools_instances,
                tool_hooks=[tool_hook],
                user_id=user_id,
                session_id=session_id,
                organization_id=context.organization_id,
                agent_name=agent_name,
                skill_configs=context.skill_configs,
            )

            # Register for cancellation
            self.cancellation_manager.register(
                execution_id=context.execution_id,
                instance=agent,
                instance_type="agent",
            )

            # Cache execution metadata
            self.control_plane.cache_metadata(context.execution_id, "AGENT")

            def stream_agent_run():
                """
                Run agent with streaming and publish events directly to Control Plane.
                This runs in a thread pool, so blocking HTTP calls are OK here.
                Put chunks in queue for async iterator to yield in real-time.
                """
                nonlocal accumulated_response, run_result
                run_id_published = False

                # Use thread-local event loop from control_plane client
                # This ensures all async operations (tool hooks, event publishing) share the same loop
                # and it persists until explicitly cleaned up at the end of execution
                thread_loop = self.control_plane._get_thread_event_loop()

                try:
                    # Use async streaming for MCP tools, sync for others
                    if has_async_tools:
                        # For async tools (MCP), we need to use agent.arun() in an async context
                        # Use the thread-local event loop instead of creating a new one
                        if messages:
                            stream_response = thread_loop.run_until_complete(
                                agent.arun(context.prompt, stream=True, messages=messages)
                            )
                        else:
                            stream_response = thread_loop.run_until_complete(
                                agent.arun(context.prompt, stream=True)
                            )
                    else:
                        # Use sync agent.run() for non-MCP tools
                        if messages:
                            stream_response = agent.run(
                                context.prompt,
                                stream=True,
                                messages=messages,
                            )
                        else:
                            stream_response = agent.run(context.prompt, stream=True)

                    # Iterate over streaming chunks and publish IMMEDIATELY
                    for chunk in stream_response:
                        # Capture run_id for cancellation (first chunk)
                        if not run_id_published and hasattr(chunk, "run_id") and chunk.run_id:
                            self.cancellation_manager.set_run_id(
                                context.execution_id, chunk.run_id
                            )

                            # Publish run_id event
                            self.control_plane.publish_event(
                                execution_id=context.execution_id,
                                event_type="run_started",
                                data={
                                    "run_id": chunk.run_id,
                                    "execution_id": context.execution_id,
                                    "cancellable": True,
                                }
                            )
                            run_id_published = True

                        # Extract content
                        chunk_content = ""
                        if hasattr(chunk, "content") and chunk.content:
                            if isinstance(chunk.content, str):
                                chunk_content = chunk.content
                            elif hasattr(chunk.content, "text"):
                                chunk_content = chunk.content.text

                        # Filter out whitespace-only chunks to prevent "(no content)" in UI
                        if chunk_content and chunk_content.strip():
                            accumulated_response += chunk_content

                            # Queue chunk for batched publishing (via EventPublisher in async context)
                            # This reduces 300 HTTP requests → 12 requests (96% reduction)
                            chunk_queue.put(("chunk", chunk_content, message_id))

                    # Store final result
                    run_result = stream_response

                    # Signal completion
                    chunk_queue.put(("done", run_result))

                except Exception as e:
                    self.logger.error("streaming_error", error=str(e))
                    chunk_queue.put(("error", e))
                    raise

            # Start streaming in background thread
            stream_thread = threading.Thread(target=stream_agent_run, daemon=True)
            stream_thread.start()

            # Yield chunks as they arrive in the queue and publish via EventPublisher
            while True:
                try:
                    # Non-blocking get with short timeout for responsiveness
                    queue_item = await asyncio.to_thread(chunk_queue.get, timeout=0.1)

                    if queue_item[0] == "chunk":
                        # Unpack chunk data
                        _, chunk_content, msg_id = queue_item

                        # Publish chunk via EventPublisher (batched, non-blocking)
                        await event_publisher.publish(
                            event_type="message_chunk",
                            data={
                                "role": "assistant",
                                "content": chunk_content,
                                "is_chunk": True,
                                "message_id": msg_id,
                            },
                            priority=EventPriority.NORMAL,  # Batched
                        )

                        # Yield chunk immediately to iterator
                        yield RuntimeExecutionResult(
                            response=chunk_content,
                            usage={},
                            success=True,
                        )
                    elif queue_item[0] == "done":
                        # Final result - extract metadata and break
                        run_result = queue_item[1]
                        break
                    elif queue_item[0] == "error":
                        # Error occurred in thread
                        raise queue_item[1]

                except queue.Empty:
                    # Queue empty, check if thread is still alive
                    if not stream_thread.is_alive():
                        # Thread died without putting "done" - something went wrong
                        break
                    # Thread still running, continue waiting
                    continue

            # Wait for thread to complete
            await asyncio.to_thread(stream_thread.join, timeout=5.0)

            # Yield final result with complete metadata
            usage = extract_usage(run_result) if run_result else {}
            tool_messages = extract_tool_messages(run_result) if run_result else []

            yield RuntimeExecutionResult(
                response=accumulated_response,  # Full accumulated response
                usage=usage,
                success=True,
                finish_reason="stop",
                run_id=getattr(run_result, "run_id", None) if run_result else None,
                model=context.model_id,
                tool_messages=tool_messages,
                metadata={"accumulated_response": accumulated_response},
            )

        finally:
            # Flush and close event publisher to ensure all batched events are sent
            await event_publisher.flush()
            await event_publisher.close()

            # Clean up thread-local event loop used by tool hooks
            # This prevents resource leaks and "await wasn't used with future" errors
            self.control_plane.close_thread_event_loop()

            # Close MCP tool connections
            for mcp_tool in mcp_tools_instances:
                try:
                    await mcp_tool.close()
                    self.logger.debug(
                        "mcp_tool_closed_streaming",
                        execution_id=context.execution_id,
                    )
                except Exception as e:
                    self.logger.error(
                        "mcp_tool_close_failed_streaming",
                        error=str(e),
                        execution_id=context.execution_id,
                    )

            # Close enforcer client context manager (fix resource leak)
            if 'enforcer_client_context' in locals() and enforcer_client_context is not None:
                try:
                    await enforcer_client_context.__aexit__(None, None, None)
                    self.logger.debug(
                        "enforcer_client_closed",
                        execution_id=context.execution_id[:8],
                    )
                except Exception as e:
                    self.logger.warning(
                        "enforcer_client_close_failed",
                        error=str(e),
                        execution_id=context.execution_id[:8],
                    )

            # Cleanup
            self.cancellation_manager.unregister(context.execution_id)

    # ==================== Custom Tool Extension API ====================

    def get_custom_tool_requirements(self) -> Dict[str, Any]:
        """
        Get requirements for creating custom tools for Agno runtime.

        Returns:
            Dictionary with format, examples, and documentation for Agno custom tools
        """
        return {
            "format": "python_class",
            "description": "Python class with get_tools() method returning Agno Toolkit",
            "example_code": '''
from agno.tools import Toolkit

class MyCustomTool:
    """Custom tool for Agno runtime."""

    def get_tools(self) -> Toolkit:
        """Return Agno toolkit with custom functions."""
        return Toolkit(
            name="my_tool",
            tools=[self.my_function]
        )

    def my_function(self, arg: str) -> str:
        """Tool function description."""
        return f"Result: {arg}"
            ''',
            "documentation_url": "https://docs.agno.ai/custom-tools",
            "required_methods": ["get_tools"],
            "schema": {
                "type": "object",
                "required": ["get_tools"],
                "properties": {
                    "get_tools": {
                        "type": "method",
                        "returns": "Toolkit"
                    }
                }
            }
        }

    def validate_custom_tool(self, tool: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a custom tool for Agno runtime.

        Args:
            tool: Tool instance to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for get_tools method
        if not hasattr(tool, 'get_tools'):
            return False, "Tool must have get_tools() method"

        if not callable(getattr(tool, 'get_tools')):
            return False, "get_tools must be callable"

        # Try calling to validate return type
        try:
            toolkit = tool.get_tools()

            # Check if it's a Toolkit-like object (has tools attribute or is iterable)
            if not (hasattr(toolkit, 'tools') or hasattr(toolkit, '__iter__')):
                return False, f"get_tools() must return Toolkit or iterable, got {type(toolkit)}"

        except Exception as e:
            return False, f"get_tools() failed: {str(e)}"

        return True, None

    def register_custom_tool(self, tool: Any, metadata: Optional[Dict] = None) -> str:
        """
        Register a custom tool with Agno runtime.

        Args:
            tool: Tool instance with get_tools() method
            metadata: Optional metadata (name, description, etc.)

        Returns:
            Tool identifier for this registered tool

        Raises:
            ValueError: If tool validation fails
        """
        # Validate first
        is_valid, error = self.validate_custom_tool(tool)
        if not is_valid:
            raise ValueError(f"Invalid custom tool: {error}")

        # Generate tool ID
        tool_name = metadata.get("name") if metadata else tool.__class__.__name__
        tool_id = f"custom_{tool_name}_{id(tool)}"

        # Store tool instance
        self._custom_tools[tool_id] = tool

        self.logger.info(
            "custom_tool_registered",
            tool_id=tool_id,
            tool_class=tool.__class__.__name__,
            tool_name=tool_name
        )

        return tool_id

    def get_registered_custom_tools(self) -> list[str]:
        """
        Get list of registered custom tool identifiers.

        Returns:
            List of tool IDs
        """
        return list(self._custom_tools.keys())
