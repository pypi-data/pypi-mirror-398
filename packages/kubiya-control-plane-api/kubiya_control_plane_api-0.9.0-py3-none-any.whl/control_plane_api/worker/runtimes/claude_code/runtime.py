"""
Claude Code runtime implementation using Claude Code SDK.

This runtime adapter integrates the Claude Code SDK to power agents with
advanced coding capabilities, file operations, and specialized tools.

ALL 7 BUGS FIXED:
- Bug #1: Added metadata = {} initialization
- Bug #2: Replaced print() with logger.debug()
- Bug #3: Made MCP fallback patterns explicit
- Bug #4: Added session_id validation
- Bug #5: Added explicit disconnect() calls with timeout
- Bug #6: Added tool name validation
- Bug #7: Removed debug output
"""

from typing import Dict, Any, Optional, AsyncIterator, Callable, TYPE_CHECKING
import structlog
import asyncio
import time
import os
from temporalio import activity

from ..base import (
    RuntimeType,
    RuntimeExecutionResult,
    RuntimeExecutionContext,
    RuntimeCapabilities,
    BaseRuntime,
    RuntimeRegistry,
)
from .config import build_claude_options
from .utils import (
    extract_usage_from_result_message,
    extract_session_id_from_result_message,
    build_prompt_with_history,
)
from .litellm_proxy import clear_execution_context
from .cleanup import cleanup_sdk_client
from .client_pool import ClaudeCodeClientPool

if TYPE_CHECKING:
    from control_plane_client import ControlPlaneClient
    from services.cancellation_manager import CancellationManager

logger = structlog.get_logger(__name__)

# ⚡ PERFORMANCE: Lazy load Claude SDK at module level (not per-execution)
# This imports the SDK once when the module loads, making subsequent executions faster
_CLAUDE_SDK_AVAILABLE = False
_CLAUDE_SDK_IMPORT_ERROR = None
_SDK_CLASSES = {}

try:
    from claude_agent_sdk import (
        ClaudeSDKClient,
        AssistantMessage,
        ResultMessage,
        TextBlock,
        ToolUseBlock,
        ToolResultBlock,
    )
    _CLAUDE_SDK_AVAILABLE = True
    _SDK_CLASSES = {
        'ClaudeSDKClient': ClaudeSDKClient,
        'AssistantMessage': AssistantMessage,
        'ResultMessage': ResultMessage,
        'TextBlock': TextBlock,
        'ToolUseBlock': ToolUseBlock,
        'ToolResultBlock': ToolResultBlock,
    }
    logger.info("claude_code_sdk_preloaded", status="success")
except ImportError as e:
    _CLAUDE_SDK_IMPORT_ERROR = str(e)
    logger.warning("claude_code_sdk_not_available", error=str(e))


@RuntimeRegistry.register(RuntimeType.CLAUDE_CODE)
class ClaudeCodeRuntime(BaseRuntime):
    """
    Runtime implementation using Claude Code SDK.

    This runtime leverages Claude Code's specialized capabilities for
    software engineering tasks, file operations, and developer workflows.

    Features:
    - Streaming execution with real-time updates
    - Conversation history support via ClaudeSDKClient
    - Custom tool integration via MCP
    - Hooks for tool execution monitoring
    - Cancellation support via interrupt()

    All critical bugs have been fixed in this refactored version.
    """

    def __init__(
        self,
        control_plane_client: "ControlPlaneClient",
        cancellation_manager: "CancellationManager",
        **kwargs,
    ):
        """
        Initialize the Claude Code runtime.

        Args:
            control_plane_client: Client for Control Plane API
            cancellation_manager: Manager for execution cancellation
            **kwargs: Additional configuration options
        """
        super().__init__(control_plane_client, cancellation_manager, **kwargs)

        # Track active SDK clients for cancellation
        self._active_clients: Dict[str, Any] = {}

        # Track custom MCP servers
        self._custom_mcp_servers: Dict[str, Any] = {}  # server_name -> mcp_server

        # Cache MCP discovery results (discovered once, reused per execution)
        # Format: {server_name: {tools: [...], resources: [...], prompts: [...], connected: bool}}
        self._mcp_discovery_cache: Dict[str, Any] = {}
        self._mcp_cache_lock = None  # Will be initialized on first use

    def get_runtime_type(self) -> RuntimeType:
        """Return RuntimeType.CLAUDE_CODE."""
        return RuntimeType.CLAUDE_CODE

    def get_capabilities(self) -> RuntimeCapabilities:
        """Return Claude Code runtime capabilities."""
        return RuntimeCapabilities(
            streaming=True,
            tools=True,
            mcp=True,
            hooks=True,
            cancellation=True,
            conversation_history=True,
            custom_tools=True,
        )

    async def _execute_impl(
        self, context: RuntimeExecutionContext
    ) -> RuntimeExecutionResult:
        """
        Execute agent using Claude Code SDK (non-streaming).

        Production-grade implementation with:
        - Comprehensive error handling
        - Proper resource cleanup
        - Detailed logging
        - Timeout management
        - Graceful degradation

        BUG FIX #1: Added metadata = {} initialization
        BUG FIX #5: Added explicit disconnect() call

        Args:
            context: Execution context with prompt, history, config

        Returns:
            RuntimeExecutionResult with response and metadata
        """
        client = None
        start_time = asyncio.get_event_loop().time()

        try:
            # ⚡ PERFORMANCE: Use pre-loaded SDK classes (loaded at module level)
            if not _CLAUDE_SDK_AVAILABLE:
                return RuntimeExecutionResult(
                    response="",
                    usage={},
                    success=False,
                    error=f"Claude Code SDK not available: {_CLAUDE_SDK_IMPORT_ERROR}",
                )

            ClaudeSDKClient = _SDK_CLASSES['ClaudeSDKClient']
            ResultMessage = _SDK_CLASSES['ResultMessage']

            self.logger.info(
                "starting_claude_code_non_streaming_execution",
                execution_id=context.execution_id,
                model=context.model_id,
                has_history=bool(context.conversation_history),
            )

            # Build options and create client
            options, _, _, _ = await build_claude_options(context, runtime=self)

            # Merge custom MCP servers
            if self._custom_mcp_servers:
                if not options.mcp_servers:
                    options.mcp_servers = {}

                for server_name, mcp_server in self._custom_mcp_servers.items():
                    options.mcp_servers[server_name] = mcp_server

                    # Add tool names to allowed_tools for permission
                    if hasattr(mcp_server, 'tools') and mcp_server.tools:
                        for tool in mcp_server.tools:
                            if hasattr(tool, 'name'):
                                tool_name = f"mcp__{server_name}__{tool.name}"
                                if tool_name not in options.allowed_tools:
                                    options.allowed_tools.append(tool_name)

                    self.logger.debug(
                        "custom_mcp_server_added_non_streaming",
                        server_name=server_name,
                        execution_id=context.execution_id
                    )

            # Suppress verbose MCP STDIO parsing error logs
            # These errors occur when MCP servers incorrectly log to stdout instead of stderr
            # The connection continues to work, but the SDK logs errors for each non-JSONRPC line
            import logging
            mcp_stdio_logger = logging.getLogger("mcp.client.stdio")
            original_stdio_level = mcp_stdio_logger.level
            mcp_stdio_logger.setLevel(logging.ERROR)  # Only show critical errors

            # Create and connect client
            client = ClaudeSDKClient(options=options)

            try:
                await client.connect()
            except Exception as e:
                error_msg = str(e)

                # Build comprehensive error message from all sources
                # The SDK wraps subprocess errors, so "No conversation found" may be in:
                # 1. The exception message itself
                # 2. The stderr attribute (if CalledProcessError)
                # 3. The output attribute
                # 4. The __cause__ chain
                full_error_context = error_msg
                if hasattr(e, 'stderr') and e.stderr:
                    stderr_content = e.stderr if isinstance(e.stderr, str) else e.stderr.decode('utf-8', errors='replace')
                    full_error_context += f" | stderr: {stderr_content}"
                if hasattr(e, 'output') and e.output:
                    output_content = e.output if isinstance(e.output, str) else e.output.decode('utf-8', errors='replace')
                    full_error_context += f" | output: {output_content}"
                if e.__cause__:
                    full_error_context += f" | cause: {str(e.__cause__)}"

                # Detect session-related errors:
                # 1. Explicit "No conversation found" in any error context
                # 2. "exit code 1" when we were trying to resume (likely session issue)
                is_session_error = (
                    "No conversation found" in full_error_context or
                    "conversation" in full_error_context.lower() or
                    # Fallback: exit code 1 during resume attempt is likely a session issue
                    (options.resume and "exit code 1" in error_msg.lower())
                )

                # Handle session-related errors gracefully by retrying without resume
                if is_session_error and options.resume:
                    logger.warning(
                        "session_resume_failed_retrying_without_resume",
                        execution_id=context.execution_id[:16],
                        error=error_msg,
                        full_error_context=full_error_context[:500],  # Truncate for logging
                        session_id=options.resume[:16] if options.resume else None,
                        note="Session doesn't exist or is invalid, creating new conversation"
                    )

                    # Retry without resume parameter
                    options.resume = None
                    session_resume_failed = True  # Track for prompt building
                    client = ClaudeSDKClient(options=options)
                    await client.connect()
                    logger.info(
                        "client_connected_without_resume",
                        execution_id=context.execution_id[:16]
                    )
                else:
                    # Different error, re-raise
                    raise
            else:
                session_resume_failed = False

            self._active_clients[context.execution_id] = client

            # Send prompt - include history in prompt if session resume failed
            # (since we can't rely on SDK's session continuity)
            if session_resume_failed and context.conversation_history:
                prompt = build_prompt_with_history(context)
                logger.info(
                    "using_prompt_with_history_fallback",
                    execution_id=context.execution_id[:16],
                    history_messages=len(context.conversation_history),
                    note="Session resume failed, including history in prompt"
                )
            else:
                prompt = context.prompt

            self.logger.debug(
                "sending_query_to_claude_code_sdk",
                execution_id=context.execution_id,
                prompt_length=len(prompt),
                using_session_resume=bool(options.resume),
            )

            await client.query(prompt)

            # Collect complete response
            response_text = ""
            usage = {}
            tool_messages = []
            finish_reason = None
            message_count = 0
            last_heartbeat = asyncio.get_event_loop().time()  # Track last heartbeat for Temporal activity liveness

            # BUG FIX #1: Initialize metadata before use
            metadata = {}

            # Use receive_response() to get messages until ResultMessage
            async for message in client.receive_response():
                message_count += 1

                # Send heartbeat every 5 seconds or every 10 messages
                current_time = asyncio.get_event_loop().time()
                if current_time - last_heartbeat > 5 or message_count % 10 == 0:
                    try:
                        activity.heartbeat({
                            "status": "processing",
                            "messages_received": message_count,
                            "response_length": len(response_text),
                            "elapsed_seconds": int(current_time - last_heartbeat)
                        })
                        last_heartbeat = current_time
                    except Exception as e:
                        # Non-fatal: heartbeat failure should not break execution
                        self.logger.warning("heartbeat_failed_non_fatal", execution_id=context.execution_id, error=str(e))

                # Extract content from AssistantMessage
                if hasattr(message, "content"):
                    for block in message.content:
                        if hasattr(block, "text"):
                            response_text += block.text
                        elif hasattr(block, "name"):  # ToolUseBlock
                            tool_messages.append(
                                {
                                    "tool": block.name,
                                    "input": getattr(block, "input", {}),
                                    "tool_use_id": getattr(block, "id", None),
                                }
                            )

                # Extract usage, finish reason, and session_id from ResultMessage
                if isinstance(message, ResultMessage):
                    usage = extract_usage_from_result_message(message)

                    if usage:
                        self.logger.info(
                            "claude_code_usage_extracted",
                            execution_id=context.execution_id[:8],
                            input_tokens=usage["input_tokens"],
                            output_tokens=usage["output_tokens"],
                            cache_read=usage["cache_read_tokens"],
                        )

                    finish_reason = message.subtype  # "success" or "error"

                    # BUG FIX #4: Extract and validate session_id
                    session_id = extract_session_id_from_result_message(
                        message, context.execution_id
                    )

                    if session_id:
                        # BUG FIX #1: metadata is now properly initialized
                        metadata["claude_code_session_id"] = session_id

                    self.logger.info(
                        "claude_code_execution_completed",
                        execution_id=context.execution_id[:8],
                        finish_reason=finish_reason,
                        message_count=message_count,
                        response_length=len(response_text),
                        tool_count=len(tool_messages),
                        tokens=usage.get("total_tokens", 0),
                        has_session_id=bool(session_id),
                    )
                    break

            elapsed_time = asyncio.get_event_loop().time() - start_time

            # Merge metadata with execution stats
            final_metadata = {
                **metadata,  # Includes claude_code_session_id if present
                "elapsed_time": elapsed_time,
                "message_count": message_count,
            }

            return RuntimeExecutionResult(
                response=response_text,
                usage=usage,
                success=finish_reason == "success",
                finish_reason=finish_reason or "stop",
                tool_execution_messages=tool_messages,  # Use standard field name for analytics
                tool_messages=tool_messages,  # Keep for backward compatibility
                model=context.model_id,
                metadata=final_metadata,
            )

        except ImportError as e:
            self.logger.error(
                "claude_code_sdk_not_installed",
                execution_id=context.execution_id,
                error=str(e),
            )

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
                    category=ErrorCategory.RUNTIME_INIT,
                    stage="initialization",
                    component="claude_code_runtime",
                    operation="sdk_import",
                    recovery_actions=[
                        "Install Claude Code SDK: pip install claude-agent-sdk",
                        "Verify SDK version is compatible",
                        "Check Python environment configuration",
                    ],
                )
            except Exception as publish_error:
                # Log error publishing failure but don't let it break execution flow
                self.logger.error(
                    "error_publish_failed",
                    error=str(publish_error),
                    error_type=type(publish_error).__name__,
                    original_error="Claude Code SDK not available",
                    execution_id=context.execution_id
                )

            return RuntimeExecutionResult(
                response="",
                usage={},
                success=False,
                error=f"Claude Code SDK not available: {str(e)}",
            )

        except asyncio.TimeoutError:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(
                "claude_code_execution_timeout",
                execution_id=context.execution_id,
                elapsed_time=elapsed_time,
            )

            # Publish timeout error event
            try:
                from control_plane_api.worker.utils.error_publisher import (
                    ErrorEventPublisher, ErrorSeverity, ErrorCategory
                )
                error_publisher = ErrorEventPublisher(self.control_plane)
                await error_publisher.publish_error(
                    execution_id=context.execution_id,
                    exception=asyncio.TimeoutError("Execution timeout exceeded"),
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.TIMEOUT,
                    stage="execution",
                    component="claude_code_runtime",
                    operation="agent_execution",
                    metadata={"elapsed_time": elapsed_time},
                    recovery_actions=[
                        "Simplify the prompt or reduce complexity",
                        "Increase timeout settings if appropriate",
                        "Check system resources and load",
                    ],
                )
            except Exception as publish_error:
                # Log error publishing failure but don't let it break execution flow
                self.logger.error(
                    "error_publish_failed",
                    error=str(publish_error),
                    error_type=type(publish_error).__name__,
                    original_error="Execution timeout",
                    execution_id=context.execution_id
                )

            return RuntimeExecutionResult(
                response="",
                usage={},
                success=False,
                error="Execution timeout exceeded",
            )

        except asyncio.CancelledError:
            self.logger.warning(
                "claude_code_execution_cancelled_gracefully",
                execution_id=context.execution_id,
            )
            # DURABILITY FIX: Do NOT re-raise! Handle cancellation gracefully
            # Return partial result to allow workflow to handle interruption
            return RuntimeExecutionResult(
                response="",  # No response accumulated in non-streaming mode
                usage={},
                success=False,  # Non-streaming cancellation is a failure (no partial state)
                error="Execution was cancelled",
                finish_reason="cancelled",
                metadata={"interrupted": True, "can_resume": False},
            )

        except Exception as e:
            self.logger.error(
                "claude_code_execution_failed",
                execution_id=context.execution_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )

            # Publish generic error event with stack trace
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
                    component="claude_code_runtime",
                    operation="agent_execution",
                    include_stack_trace=True,
                )
            except Exception as publish_error:
                # Log error publishing failure but don't let it break execution flow
                self.logger.error(
                    "error_publish_failed",
                    error=str(publish_error),
                    error_type=type(publish_error).__name__,
                    original_error=f"{type(e).__name__}: {str(e)}",
                    execution_id=context.execution_id
                )

            return RuntimeExecutionResult(
                response="",
                usage={},
                success=False,
                error=f"{type(e).__name__}: {str(e)}",
            )

        finally:
            # Clear execution context from proxy (with delay to allow in-flight SDK requests)
            try:
                clear_execution_context(
                    context.execution_id,
                    immediate=False,  # Use delayed cleanup
                    delay_seconds=5.0  # Wait for in-flight SDK requests
                )
            except Exception as e:
                self.logger.warning(
                    "failed_to_clear_proxy_context",
                    execution_id=context.execution_id,
                    error=str(e),
                )

            # Restore MCP STDIO log level
            try:
                import logging
                mcp_stdio_logger = logging.getLogger("mcp.client.stdio")
                if 'original_stdio_level' in locals():
                    mcp_stdio_logger.setLevel(original_stdio_level)
            except Exception as log_level_error:
                # Log but ignore errors restoring log level - this is non-critical cleanup
                self.logger.debug(
                    "failed_to_restore_log_level",
                    error=str(log_level_error),
                    execution_id=context.execution_id
                )

            # CRITICAL: Cleanup SDK client
            if context.execution_id in self._active_clients:
                client = self._active_clients.pop(context.execution_id)
                cleanup_sdk_client(client, context.execution_id, self.logger)

    async def _stream_execute_impl(
        self,
        context: RuntimeExecutionContext,
        event_callback: Optional[Callable[[Dict], None]] = None,
    ) -> AsyncIterator[RuntimeExecutionResult]:
        """
        Production-grade streaming execution with Claude Code SDK.

        This implementation provides:
        - Comprehensive error handling with specific exception types
        - Detailed structured logging at each stage
        - Proper resource cleanup with finally blocks
        - Real-time event callbacks for tool execution
        - Accumulated metrics and metadata tracking

        BUG FIX #5: Added explicit disconnect() call
        BUG FIX #7: Removed all debug output

        Args:
            context: Execution context with prompt, history, config
            event_callback: Optional callback for real-time events

        Yields:
            RuntimeExecutionResult chunks as they arrive, ending with final metadata
        """
        client = None
        start_time = asyncio.get_event_loop().time()
        chunk_count = 0

        try:
            # ⚡ PERFORMANCE: Use pre-loaded SDK classes (loaded at module level)
            if not _CLAUDE_SDK_AVAILABLE:
                yield RuntimeExecutionResult(
                    response="",
                    usage={},
                    success=False,
                    error=f"Claude Code SDK not available: {_CLAUDE_SDK_IMPORT_ERROR}",
                    finish_reason="error",
                    tool_messages=[],
                    tool_execution_messages=[],
                )
                return

            ClaudeSDKClient = _SDK_CLASSES['ClaudeSDKClient']
            AssistantMessage = _SDK_CLASSES['AssistantMessage']
            ResultMessage = _SDK_CLASSES['ResultMessage']
            TextBlock = _SDK_CLASSES['TextBlock']
            ToolUseBlock = _SDK_CLASSES['ToolUseBlock']
            ToolResultBlock = _SDK_CLASSES['ToolResultBlock']

            self.logger.info(
                "starting_claude_code_streaming_execution",
                execution_id=context.execution_id,
                model=context.model_id,
                has_history=bool(context.conversation_history),
                has_callback=event_callback is not None,
            )

            # Build options and create client
            options, active_tools, started_tools, completed_tools = await build_claude_options(context, event_callback, runtime=self)

            # Merge custom MCP servers
            if self._custom_mcp_servers:
                if not options.mcp_servers:
                    options.mcp_servers = {}

                for server_name, mcp_server in self._custom_mcp_servers.items():
                    options.mcp_servers[server_name] = mcp_server

                    # Add tool names to allowed_tools for permission
                    if hasattr(mcp_server, 'tools') and mcp_server.tools:
                        for tool in mcp_server.tools:
                            if hasattr(tool, 'name'):
                                tool_name = f"mcp__{server_name}__{tool.name}"
                                if tool_name not in options.allowed_tools:
                                    options.allowed_tools.append(tool_name)

                    self.logger.debug(
                        "custom_mcp_server_added_streaming",
                        server_name=server_name,
                        execution_id=context.execution_id
                    )

            self.logger.info(
                "created_claude_code_sdk_options",
                execution_id=context.execution_id,
                has_tools=bool(context.skills),
                has_mcp=(
                    len(options.mcp_servers) > 0
                    if hasattr(options, "mcp_servers")
                    else False
                ),
                has_custom_mcp=len(self._custom_mcp_servers) > 0,
                has_hooks=bool(options.hooks) if hasattr(options, "hooks") else False,
                has_event_callback=event_callback is not None,
            )

            # Suppress verbose MCP STDIO parsing error logs
            # These errors occur when MCP servers incorrectly log to stdout instead of stderr
            # The connection continues to work, but the SDK logs errors for each non-JSONRPC line
            import logging
            mcp_stdio_logger = logging.getLogger("mcp.client.stdio")
            original_stdio_level = mcp_stdio_logger.level
            mcp_stdio_logger.setLevel(logging.ERROR)  # Only show critical errors

            # Create and connect client
            client = ClaudeSDKClient(options=options)

            try:
                await client.connect()
            except Exception as e:
                error_msg = str(e)

                # Build comprehensive error message from all sources
                # The SDK wraps subprocess errors, so "No conversation found" may be in:
                # 1. The exception message itself
                # 2. The stderr attribute (if CalledProcessError)
                # 3. The output attribute
                # 4. The __cause__ chain
                full_error_context = error_msg
                if hasattr(e, 'stderr') and e.stderr:
                    stderr_content = e.stderr if isinstance(e.stderr, str) else e.stderr.decode('utf-8', errors='replace')
                    full_error_context += f" | stderr: {stderr_content}"
                if hasattr(e, 'output') and e.output:
                    output_content = e.output if isinstance(e.output, str) else e.output.decode('utf-8', errors='replace')
                    full_error_context += f" | output: {output_content}"
                if e.__cause__:
                    full_error_context += f" | cause: {str(e.__cause__)}"

                # Detect session-related errors:
                # 1. Explicit "No conversation found" in any error context
                # 2. "exit code 1" when we were trying to resume (likely session issue)
                is_session_error = (
                    "No conversation found" in full_error_context or
                    "conversation" in full_error_context.lower() or
                    # Fallback: exit code 1 during resume attempt is likely a session issue
                    (options.resume and "exit code 1" in error_msg.lower())
                )

                # Handle session-related errors gracefully by retrying without resume
                if is_session_error and options.resume:
                    logger.warning(
                        "session_resume_failed_retrying_without_resume_streaming",
                        execution_id=context.execution_id[:16],
                        error=error_msg,
                        full_error_context=full_error_context[:500],  # Truncate for logging
                        session_id=options.resume[:16] if options.resume else None,
                        note="Session doesn't exist or is invalid, creating new conversation"
                    )

                    # Retry without resume parameter
                    options.resume = None
                    session_resume_failed = True  # Track for prompt building
                    client = ClaudeSDKClient(options=options)
                    await client.connect()
                    logger.info(
                        "client_connected_without_resume_streaming",
                        execution_id=context.execution_id[:16]
                    )
                else:
                    # Different error, re-raise
                    raise
            else:
                session_resume_failed = False

            self._active_clients[context.execution_id] = client

            # Cache execution metadata
            try:
                self.control_plane.cache_metadata(context.execution_id, "AGENT")
            except Exception as cache_error:
                self.logger.warning(
                    "failed_to_cache_metadata_non_fatal",
                    execution_id=context.execution_id,
                    error=str(cache_error),
                )

            # Send prompt - include history in prompt if session resume failed
            # (since we can't rely on SDK's session continuity)
            if session_resume_failed and context.conversation_history:
                prompt = build_prompt_with_history(context)
                logger.info(
                    "using_prompt_with_history_fallback_streaming",
                    execution_id=context.execution_id[:16],
                    history_messages=len(context.conversation_history),
                    note="Session resume failed, including history in prompt"
                )
            else:
                prompt = context.prompt

            self.logger.debug(
                "sending_streaming_query_to_claude_code_sdk",
                execution_id=context.execution_id,
                prompt_length=len(prompt),
                using_session_resume=bool(options.resume),
            )

            await client.query(prompt)

            # Stream messages
            accumulated_response = ""
            accumulated_usage = {}
            tool_messages = []
            message_count = 0
            received_stream_events = False  # Track if we got streaming events
            session_id = None  # Initialize to avoid UnboundLocalError in exception handlers
            last_heartbeat = time.time()  # Track last heartbeat for Temporal activity liveness

            # completed_tools set is now passed from build_claude_options for tracking
            # which tool_use_ids have published completion events (prevents duplicates and detects missing)

            # Generate unique message_id for this turn
            message_id = f"{context.execution_id}_{int(time.time() * 1000000)}"

            # Track thinking state for extended thinking support
            current_thinking_block = None  # Tracks active thinking block index
            thinking_content_buffer = ""   # Accumulates thinking content for logging

            async for message in client.receive_response():
                message_count += 1
                message_type_name = type(message).__name__

                # Handle StreamEvent messages (partial chunks)
                if message_type_name == "StreamEvent":
                    if hasattr(message, "event") and message.event:
                        event_data = message.event

                        # Extract text from event data
                        content = None
                        if isinstance(event_data, dict):
                            event_type = event_data.get("type")

                            # Handle content_block_start events (detect thinking blocks)
                            if event_type == "content_block_start":
                                content_block = event_data.get("content_block", {})
                                block_type = content_block.get("type")
                                block_index = event_data.get("index", 0)

                                if block_type == "thinking":
                                    current_thinking_block = block_index
                                    thinking_content_buffer = ""

                                    # Emit thinking_start event
                                    if event_callback:
                                        try:
                                            event_callback({
                                                "type": "thinking_start",
                                                "message_id": message_id,
                                                "index": block_index,
                                                "execution_id": context.execution_id,
                                            })
                                        except Exception as callback_error:
                                            self.logger.warning(
                                                "thinking_start_callback_failed",
                                                execution_id=context.execution_id,
                                                error=str(callback_error),
                                            )
                                continue  # Don't process content_block_start further

                            # Handle content_block_delta events
                            if event_type == "content_block_delta":
                                delta = event_data.get("delta", {})
                                delta_type = delta.get("type") if isinstance(delta, dict) else None

                                # Handle thinking_delta events
                                if delta_type == "thinking_delta":
                                    thinking_text = delta.get("thinking", "")
                                    if thinking_text:
                                        thinking_content_buffer += thinking_text

                                        # Emit thinking_delta event
                                        if event_callback:
                                            try:
                                                event_callback({
                                                    "type": "thinking_delta",
                                                    "thinking": thinking_text,
                                                    "message_id": message_id,
                                                    "index": event_data.get("index", 0),
                                                    "execution_id": context.execution_id,
                                                })
                                            except Exception as callback_error:
                                                self.logger.warning(
                                                    "thinking_delta_callback_failed",
                                                    execution_id=context.execution_id,
                                                    error=str(callback_error),
                                                )
                                    continue  # Don't process thinking as regular content

                                # Handle signature_delta events (end of thinking block)
                                if delta_type == "signature_delta":
                                    signature = delta.get("signature", "")

                                    # Emit thinking_complete event
                                    if event_callback:
                                        try:
                                            event_callback({
                                                "type": "thinking_complete",
                                                "signature": signature,
                                                "message_id": message_id,
                                                "index": event_data.get("index", 0),
                                                "execution_id": context.execution_id,
                                            })
                                        except Exception as callback_error:
                                            self.logger.warning(
                                                "thinking_complete_callback_failed",
                                                execution_id=context.execution_id,
                                                error=str(callback_error),
                                            )

                                    # Log thinking summary
                                    if thinking_content_buffer:
                                        self.logger.debug(
                                            "thinking_block_completed",
                                            execution_id=context.execution_id,
                                            thinking_length=len(thinking_content_buffer),
                                            has_signature=bool(signature),
                                        )
                                    current_thinking_block = None
                                    thinking_content_buffer = ""
                                    continue  # Don't process signature as regular content

                                # Handle text_delta events (regular text content)
                                if isinstance(delta, dict):
                                    content = delta.get("text")
                                elif isinstance(delta, str):
                                    content = delta

                            # Fallback: try direct text extraction
                            if not content:
                                content = event_data.get("text") or event_data.get(
                                    "content"
                                )

                        elif isinstance(event_data, str):
                            content = event_data
                        elif hasattr(event_data, "content"):
                            content = event_data.content
                        elif hasattr(event_data, "text"):
                            content = event_data.text

                        if content:
                            received_stream_events = True
                            chunk_count += 1
                            accumulated_response += content

                            # Publish event
                            if event_callback:
                                try:
                                    event_callback(
                                        {
                                            "type": "content_chunk",
                                            "content": content,
                                            "message_id": message_id,
                                            "execution_id": context.execution_id,
                                        }
                                    )
                                except Exception as callback_error:
                                    self.logger.warning(
                                        "stream_event_callback_failed",
                                        execution_id=context.execution_id,
                                        error=str(callback_error),
                                    )

                            # Yield chunk with explicit empty arrays for frontend compatibility
                            # Frontend expects arrays, not None, to avoid R.map errors
                            yield RuntimeExecutionResult(
                                response=content,
                                usage={},
                                success=True,
                                tool_messages=[],
                                tool_execution_messages=[],
                            )

                            # Send heartbeat every 10 seconds or every 50 chunks (matches AgnoRuntime pattern)
                            current_time = time.time()
                            if current_time - last_heartbeat > 10 or chunk_count % 50 == 0:
                                try:
                                    activity.heartbeat({
                                        "status": "streaming",
                                        "chunks_received": chunk_count,
                                        "response_length": len(accumulated_response),
                                        "elapsed_seconds": int(current_time - last_heartbeat)
                                    })
                                    last_heartbeat = current_time
                                except Exception as e:
                                    # Non-fatal: heartbeat failure should not break execution
                                    self.logger.warning("heartbeat_failed_non_fatal", execution_id=context.execution_id, error=str(e))

                    continue  # Skip to next message

                # Handle assistant messages (final complete message)
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            # Skip if already streamed via StreamEvents
                            if received_stream_events:
                                continue

                            # Only send if we didn't receive StreamEvents
                            chunk_count += 1
                            accumulated_response += block.text

                            if event_callback:
                                try:
                                    event_callback(
                                        {
                                            "type": "content_chunk",
                                            "content": block.text,
                                            "message_id": message_id,
                                            "execution_id": context.execution_id,
                                        }
                                    )
                                except Exception as callback_error:
                                    self.logger.warning(
                                        "event_callback_failed_non_fatal",
                                        execution_id=context.execution_id,
                                        error=str(callback_error),
                                    )

                            # Frontend expects arrays, not None, to avoid R.map errors
                            yield RuntimeExecutionResult(
                                response=block.text,
                                usage={},
                                success=True,
                                tool_messages=[],
                                tool_execution_messages=[],
                            )

                            # Send heartbeat every 10 seconds or every 50 chunks (matches AgnoRuntime pattern)
                            current_time = time.time()
                            if current_time - last_heartbeat > 10 or chunk_count % 50 == 0:
                                try:
                                    activity.heartbeat({
                                        "status": "streaming",
                                        "chunks_received": chunk_count,
                                        "response_length": len(accumulated_response),
                                        "elapsed_seconds": int(current_time - last_heartbeat)
                                    })
                                    last_heartbeat = current_time
                                except Exception as e:
                                    # Non-fatal: heartbeat failure should not break execution
                                    self.logger.warning("heartbeat_failed_non_fatal", execution_id=context.execution_id, error=str(e))

                        elif isinstance(block, ToolUseBlock):
                            # Tool use event - Store for later lookup
                            tool_info = {
                                "tool": block.name,
                                "input": block.input,
                                "tool_use_id": block.id,
                            }
                            tool_messages.append(tool_info)
                            active_tools[block.id] = block.name

                        elif isinstance(block, ToolResultBlock):
                            # Tool result - Look up tool name from active_tools
                            tool_name = active_tools.get(block.tool_use_id, "unknown")
                            if tool_name == "unknown":
                                self.logger.warning(
                                    "could_not_find_tool_name_for_tool_use_id",
                                    execution_id=context.execution_id,
                                    tool_use_id=block.tool_use_id,
                                    active_tools_keys=list(active_tools.keys()),
                                )

                            status = "success" if not block.is_error else "failed"

                            # Publish via callback (with deduplication)
                            if event_callback and block.tool_use_id not in completed_tools:
                                try:
                                    event_callback(
                                        {
                                            "type": "tool_complete",
                                            "tool_name": tool_name,
                                            "tool_execution_id": block.tool_use_id,
                                            "status": status,
                                            "output": (
                                                str(block.content)[:1000]
                                                if block.content
                                                else None
                                            ),
                                            "error": (
                                                str(block.content)
                                                if block.is_error
                                                else None
                                            ),
                                            "execution_id": context.execution_id,
                                        }
                                    )
                                    # Mark as completed to prevent duplicate events
                                    completed_tools.add(block.tool_use_id)
                                    self.logger.debug(
                                        "tool_complete_published_via_stream",
                                        tool_use_id=block.tool_use_id,
                                        tool_name=tool_name,
                                    )
                                except Exception as callback_error:
                                    self.logger.error(
                                        "tool_complete_callback_failed",
                                        execution_id=context.execution_id,
                                        tool_name=tool_name,
                                        error=str(callback_error),
                                        exc_info=True,
                                    )
                            elif block.tool_use_id in completed_tools:
                                self.logger.debug(
                                    "tool_complete_already_published_via_hooks",
                                    tool_use_id=block.tool_use_id,
                                    tool_name=tool_name,
                                )

                # Handle result message (final)
                elif isinstance(message, ResultMessage):
                    accumulated_usage = extract_usage_from_result_message(message)

                    # BUG FIX #4: Extract and validate session_id
                    session_id = extract_session_id_from_result_message(
                        message, context.execution_id
                    )

                    elapsed_time = asyncio.get_event_loop().time() - start_time

                    # FALLBACK: Detect missing tool completion events
                    # Check if any tool_use_ids in tool_messages are not in completed_tools
                    missing_completions = []
                    for tool_info in tool_messages:
                        tool_use_id = tool_info.get("tool_use_id")
                        if tool_use_id and tool_use_id not in completed_tools:
                            missing_completions.append(tool_info)

                    if missing_completions:
                        # Categorize missing tools by type for better diagnostics
                        task_tools = [t for t in missing_completions if t.get("tool") == "Task"]
                        builtin_tools = [t for t in missing_completions if t.get("tool") in ["TodoWrite", "Bash", "Read", "Write", "Edit", "Glob", "Grep"]]
                        other_tools = [t for t in missing_completions if t not in task_tools and t not in builtin_tools]

                        # Use warning level only if unexpected tools are missing
                        # Task and builtin tools are expected to miss hooks sometimes
                        log_level = "warning" if other_tools else "info"

                        log_message = (
                            f"Publishing fallback completion events for {len(missing_completions)} tools. "
                            f"Task tools: {len(task_tools)} (expected - subagents execute in separate contexts), "
                            f"Built-in tools: {len(builtin_tools)} (expected - may use optimized execution paths), "
                            f"Other: {len(other_tools)} (unexpected - may indicate hook registration issue)"
                        )

                        getattr(self.logger, log_level)(
                            "detected_missing_tool_completion_events",
                            execution_id=context.execution_id,
                            missing_count=len(missing_completions),
                            task_tools_count=len(task_tools),
                            builtin_tools_count=len(builtin_tools),
                            other_tools_count=len(other_tools),
                            missing_tool_names=[t.get("tool") for t in missing_completions],
                            missing_tool_ids=[t.get("tool_use_id")[:12] for t in missing_completions],
                            task_tool_ids=[t.get("tool_use_id")[:12] for t in task_tools] if task_tools else [],
                            builtin_tool_ids=[t.get("tool_use_id")[:12] for t in builtin_tools] if builtin_tools else [],
                            other_tool_ids=[t.get("tool_use_id")[:12] for t in other_tools] if other_tools else [],
                            message=log_message,
                            note=(
                                "SubagentStop hook should reduce Task tool misses. "
                                "Built-in tools may skip hooks by design. "
                                "Investigate 'other' category if count > 0."
                            )
                        )

                        # Publish missing completion events
                        if event_callback:
                            for tool_info in missing_completions:
                                # Defensive: Validate tool_info has required fields
                                if not isinstance(tool_info, dict):
                                    self.logger.warning(
                                        "invalid_tool_info_type_in_fallback",
                                        tool_info_type=type(tool_info).__name__,
                                        note="Skipping invalid tool_info"
                                    )
                                    continue

                                tool_use_id = tool_info.get("tool_use_id")
                                tool_name = tool_info.get("tool", "unknown")

                                # Defensive: Skip if no tool_use_id
                                if not tool_use_id:
                                    self.logger.warning(
                                        "missing_tool_use_id_in_fallback",
                                        tool_name=tool_name,
                                        note="Cannot publish completion without tool_use_id"
                                    )
                                    continue

                                try:
                                    # Defensive: Safe slicing for logging
                                    tool_use_id_short = (
                                        tool_use_id[:12] if isinstance(tool_use_id, str) and len(tool_use_id) >= 12
                                        else str(tool_use_id)
                                    )

                                    event_callback(
                                        {
                                            "type": "tool_complete",
                                            "tool_name": tool_name,
                                            "tool_execution_id": tool_use_id,
                                            "status": "success",  # Assume success if no error was caught
                                            "output": None,  # No output available in fallback
                                            "error": None,
                                            "execution_id": context.execution_id,
                                        }
                                    )
                                    completed_tools.add(tool_use_id)
                                    self.logger.info(
                                        "published_fallback_tool_completion",
                                        tool_use_id=tool_use_id_short,
                                        tool_name=tool_name,
                                        note="Fallback completion event published successfully"
                                    )
                                except Exception as e:
                                    # Non-fatal: Log but continue processing other tools
                                    self.logger.error(
                                        "failed_to_publish_fallback_completion",
                                        tool_use_id=str(tool_use_id) if tool_use_id else "unknown",
                                        tool_name=tool_name,
                                        error=str(e),
                                        error_type=type(e).__name__,
                                        exc_info=True,
                                        note="Continuing with remaining tools despite failure"
                                    )

                    self.logger.info(
                        "claude_code_streaming_completed",
                        execution_id=context.execution_id,
                        finish_reason=message.subtype,
                        chunk_count=chunk_count,
                        message_count=message_count,
                        response_length=len(accumulated_response),
                        tool_count=len(tool_messages),
                        completed_tool_count=len(completed_tools),
                        missing_completions=len(missing_completions) if missing_completions else 0,
                        usage=accumulated_usage,
                        elapsed_time=f"{elapsed_time:.2f}s",
                        has_session_id=bool(session_id),
                    )

                    # Final result message
                    yield RuntimeExecutionResult(
                        response="",  # Already streamed
                        usage=accumulated_usage,
                        success=message.subtype == "success",
                        finish_reason=message.subtype,
                        tool_execution_messages=tool_messages,  # Use standard field name for analytics
                        tool_messages=tool_messages,  # Keep for backward compatibility
                        model=context.model_id,
                        metadata={
                            "accumulated_response": accumulated_response,
                            "elapsed_time": elapsed_time,
                            "chunk_count": chunk_count,
                            "message_count": message_count,
                            "claude_code_session_id": session_id,
                        },
                    )
                    break

        except ImportError as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(
                "claude_code_sdk_not_installed",
                execution_id=context.execution_id,
                error=str(e),
                elapsed_time=f"{elapsed_time:.2f}s",
            )
            yield RuntimeExecutionResult(
                response="",
                usage={},
                success=False,
                error=f"Claude Code SDK not available: {str(e)}",
                tool_messages=[],
                tool_execution_messages=[],
            )

        except asyncio.TimeoutError:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(
                "claude_code_streaming_timeout",
                execution_id=context.execution_id,
                elapsed_time=f"{elapsed_time:.2f}s",
                chunks_before_timeout=chunk_count,
            )
            yield RuntimeExecutionResult(
                response="",
                usage={},
                success=False,
                error="Streaming execution timeout exceeded",
                tool_messages=[],
                tool_execution_messages=[],
            )

        except asyncio.CancelledError:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.warning(
                "claude_code_streaming_cancelled_gracefully",
                execution_id=context.execution_id,
                elapsed_time=f"{elapsed_time:.2f}s",
                chunks_before_cancellation=chunk_count,
                accumulated_response_length=len(accumulated_response),
                session_id=session_id[:16] if session_id else None,
            )

            # DURABILITY FIX: Do NOT re-raise! Handle cancellation gracefully
            # Save partial state and allow workflow to resume from here
            # The workflow is durable and should handle interruptions

            # Yield partial success result with accumulated state
            yield RuntimeExecutionResult(
                response=accumulated_response,  # Return what we accumulated so far
                usage=accumulated_usage,
                success=True,  # Partial success, not a failure
                finish_reason="cancelled",
                tool_execution_messages=tool_messages,
                tool_messages=tool_messages,
                model=context.model_id,
                metadata={
                    "accumulated_response": accumulated_response,
                    "elapsed_time": elapsed_time,
                    "chunk_count": chunk_count,
                    "message_count": message_count,
                    "claude_code_session_id": session_id,
                    "interrupted": True,  # Flag that this was interrupted
                    "can_resume": bool(session_id),  # Can resume if we have session_id
                },
            )
            # NOTE: Do NOT re-raise - this would break Temporal durability!

        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(
                "claude_code_streaming_failed",
                execution_id=context.execution_id,
                error=str(e),
                error_type=type(e).__name__,
                elapsed_time=f"{elapsed_time:.2f}s",
                chunks_before_error=chunk_count,
                exc_info=True,
            )
            yield RuntimeExecutionResult(
                response="",
                usage={},
                success=False,
                error=f"{type(e).__name__}: {str(e)}",
                finish_reason="error",  # CRITICAL: Must set finish_reason so caller recognizes this as final result
                tool_messages=[],
                tool_execution_messages=[],
            )

        finally:
            # Clear execution context from proxy (with delay to allow in-flight SDK requests)
            try:
                clear_execution_context(
                    context.execution_id,
                    immediate=False,  # Use delayed cleanup
                    delay_seconds=5.0  # Wait for in-flight SDK requests
                )
            except Exception as e:
                self.logger.warning(
                    "failed_to_clear_proxy_context_streaming",
                    execution_id=context.execution_id,
                    error=str(e),
                )

            # Restore MCP STDIO log level
            try:
                import logging
                mcp_stdio_logger = logging.getLogger("mcp.client.stdio")
                if 'original_stdio_level' in locals():
                    mcp_stdio_logger.setLevel(original_stdio_level)
            except Exception as log_level_error:
                # Log but ignore errors restoring log level - this is non-critical cleanup
                self.logger.debug(
                    "failed_to_restore_log_level",
                    error=str(log_level_error),
                    execution_id=context.execution_id
                )

            # CRITICAL: Cleanup SDK client
            if context.execution_id in self._active_clients:
                client = self._active_clients.pop(context.execution_id)
                cleanup_sdk_client(client, context.execution_id, self.logger)

    async def cancel(self, execution_id: str) -> bool:
        """
        Cancel an in-progress execution via Claude SDK interrupt.

        Args:
            execution_id: ID of execution to cancel

        Returns:
            True if cancellation succeeded
        """
        if execution_id in self._active_clients:
            try:
                client = self._active_clients[execution_id]
                await client.interrupt()
                self.logger.info(
                    "claude_code_execution_interrupted", execution_id=execution_id
                )
                return True
            except Exception as e:
                self.logger.error(
                    "failed_to_interrupt_claude_code_execution",
                    execution_id=execution_id,
                    error=str(e),
                )
                return False
        return False

    # ==================== Custom Tool Extension API ====================

    def get_custom_tool_requirements(self) -> Dict[str, Any]:
        """
        Get requirements for creating custom MCP servers for Claude Code runtime.

        Returns:
            Dictionary with format, examples, and documentation for MCP servers
        """
        return {
            "format": "mcp_server",
            "description": "MCP server created with @tool decorator and create_sdk_mcp_server()",
            "example_code": '''
from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any

@tool("my_function", "Description of what this tool does", {"arg": str})
async def my_function(args: dict[str, Any]) -> dict[str, Any]:
    """Tool function implementation."""
    return {
        "content": [{
            "type": "text",
            "text": f"Result: {args['arg']}"
        }]
    }

# Create MCP server
mcp_server = create_sdk_mcp_server(
    name="my_tools",
    version="1.0.0",
    tools=[my_function]
)
            ''',
            "documentation_url": "https://docs.claude.ai/agent-sdk/custom-tools",
            "required_attributes": ["name", "version"],
            "schema": {
                "type": "mcp_server",
                "required": ["name", "version", "tools"]
            }
        }

    def validate_custom_tool(self, mcp_server: Any) -> tuple[bool, Optional[str]]:
        """
        Validate an MCP server for Claude Code runtime.

        Args:
            mcp_server: MCP server instance to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required attributes
        for attr in ['name', 'version']:
            if not hasattr(mcp_server, attr):
                return False, f"MCP server must have '{attr}' attribute"

        # Validate name
        if not isinstance(mcp_server.name, str) or not mcp_server.name:
            return False, "MCP server name must be non-empty string"

        # Check for tools (optional but recommended)
        if hasattr(mcp_server, 'tools'):
            if not mcp_server.tools:
                self.logger.warning(
                    "mcp_server_has_no_tools",
                    server_name=mcp_server.name
                )

        return True, None

    def register_custom_tool(self, mcp_server: Any, metadata: Optional[Dict] = None) -> str:
        """
        Register a custom MCP server with Claude Code runtime.

        Args:
            mcp_server: MCP server instance
            metadata: Optional metadata (ignored, server name is used)

        Returns:
            Server name (identifier for this MCP server)

        Raises:
            ValueError: If MCP server validation fails or name conflicts
        """
        # Validate first
        is_valid, error = self.validate_custom_tool(mcp_server)
        if not is_valid:
            raise ValueError(f"Invalid MCP server: {error}")

        server_name = mcp_server.name

        # Check for name conflicts
        if server_name in self._custom_mcp_servers:
            raise ValueError(f"MCP server '{server_name}' already registered")

        # Store MCP server
        self._custom_mcp_servers[server_name] = mcp_server

        # Extract tool names for logging
        tool_names = []
        if hasattr(mcp_server, 'tools') and mcp_server.tools:
            tool_names = [
                f"mcp__{server_name}__{t.name}"
                for t in mcp_server.tools
                if hasattr(t, 'name')
            ]

        self.logger.info(
            "custom_mcp_server_registered",
            server_name=server_name,
            tool_count=len(tool_names),
            tools=tool_names
        )

        return server_name

    def get_registered_custom_tools(self) -> list[str]:
        """
        Get list of registered custom MCP server names.

        Returns:
            List of server names
        """
        return list(self._custom_mcp_servers.keys())
