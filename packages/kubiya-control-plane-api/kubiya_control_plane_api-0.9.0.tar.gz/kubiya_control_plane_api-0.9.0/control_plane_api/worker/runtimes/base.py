"""
Base runtime abstraction with proper ABC, registry, and Control Plane integration.

This module provides:
- Abstract base class for all runtimes
- Runtime registry for discovery and instantiation
- Lifecycle hooks for extensibility
- Control Plane integration helpers
- Configuration validation framework
"""

from typing import AsyncIterator, Dict, Any, Optional, List, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import structlog

logger = structlog.get_logger(__name__)


class RuntimeType(str, Enum):
    """Enumeration of supported runtime types."""

    DEFAULT = "default"  # Agno-based runtime
    CLAUDE_CODE = "claude_code"  # Claude Code SDK runtime
    # Easy to add more: LANGCHAIN = "langchain", CREWAI = "crewai", etc.


@dataclass
class RuntimeExecutionResult:
    """
    Standardized result structure from any runtime.

    This ensures all runtimes return consistent data structures that can
    be consumed by the workflow and activity layers.

    Analytics Integration:
    The `usage` field provides standardized token usage metrics that are
    automatically extracted and submitted to the analytics system.
    """

    response: str
    """The main response text from the agent."""

    usage: Dict[str, Any]
    """
    Token usage metrics with standardized fields:
    - input_tokens (int): Number of input/prompt tokens
    - output_tokens (int): Number of output/completion tokens
    - total_tokens (int): Total tokens used
    - cache_read_tokens (int, optional): Cached tokens read (Anthropic)
    - cache_creation_tokens (int, optional): Tokens used for cache creation (Anthropic)
    - prompt_tokens_details (dict, optional): Detailed breakdown from provider

    Runtimes should populate this from their native usage tracking.
    """

    success: bool
    """Whether the execution succeeded."""

    finish_reason: Optional[str] = None
    """Reason the execution finished (e.g., 'stop', 'length', 'tool_use')."""

    run_id: Optional[str] = None
    """Unique identifier for this execution run."""

    model: Optional[str] = None
    """Model identifier used for this execution."""

    tool_execution_messages: Optional[List[Dict]] = None
    """
    Tool execution messages for UI display and analytics.
    Format: [{"tool": "Bash", "input": {...}, "output": {...}, "success": bool, "duration_ms": int}, ...]

    Analytics Integration:
    These are automatically tracked in the execution_tool_calls table.
    """

    tool_messages: Optional[List[Dict]] = None
    """
    Detailed tool messages with execution metadata.
    Format: [{"role": "tool", "content": "...", "tool_use_id": "..."}, ...]
    """

    error: Optional[str] = None
    """Error message if execution failed."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """
    Additional runtime-specific metadata.

    Can include:
    - turn_duration_ms (int): Duration of this turn in milliseconds
    - model_provider (str): Provider name (anthropic, openai, google, etc.)
    - tasks (list): Task tracking data for analytics
    - any runtime-specific metrics
    """


@dataclass
class RuntimeExecutionContext:
    """
    Context passed to runtime for execution.

    This contains all the information needed for an agent to execute,
    regardless of which runtime implementation is used.
    """

    execution_id: str
    """Unique identifier for this execution."""

    agent_id: str
    """Unique identifier for the agent being executed."""

    organization_id: str
    """Organization context for this execution."""

    prompt: str
    """User's input prompt/message."""

    system_prompt: Optional[str] = None
    """System-level instructions for the agent."""

    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    """
    Previous conversation messages.
    Format: [{"role": "user|assistant|system", "content": "..."}, ...]
    """

    model_id: Optional[str] = None
    """LiteLLM model identifier (e.g., 'gpt-4', 'claude-3-opus')."""

    model_config: Optional[Dict[str, Any]] = None
    """Model-specific configuration (temperature, top_p, etc.)."""

    agent_config: Optional[Dict[str, Any]] = None
    """Agent-specific configuration."""

    skills: List[Any] = field(default_factory=list)
    """Resolved skills available to the agent."""

    skill_configs: List[Dict[str, Any]] = field(default_factory=list)
    """Original skill configuration dictionaries (before instantiation)."""

    mcp_servers: Optional[Dict[str, Any]] = None
    """MCP server configurations."""

    user_metadata: Optional[Dict[str, Any]] = None
    """User-provided metadata for this execution."""

    runtime_config: Optional[Dict[str, Any]] = None
    """Runtime-specific configuration options."""

    runtime_type: Optional[RuntimeType] = None
    """Runtime type for this execution."""

    # Enforcement context fields
    user_email: Optional[str] = None
    """User email for enforcement context."""

    user_id: Optional[str] = None
    """User ID for enforcement context."""

    user_roles: List[str] = field(default_factory=list)
    """User roles for enforcement context."""

    team_id: Optional[str] = None
    """Team ID for enforcement context."""

    team_name: Optional[str] = None
    """Team name for enforcement context."""

    environment: str = "production"
    """Environment for enforcement context (dev/staging/production)."""

    workspace_directory: Optional[str] = None
    """
    Execution workspace directory (e.g., .kubiya/workspaces/<execution-id>).
    Used by runtimes and skills for file operations.
    """


@dataclass
class RuntimeCapabilities:
    """Runtime capabilities metadata."""

    streaming: bool = False
    """Supports streaming execution."""

    tools: bool = False
    """Supports tool calling."""

    mcp: bool = False
    """Supports MCP servers."""

    hooks: bool = False
    """Supports lifecycle hooks."""

    cancellation: bool = False
    """Supports execution cancellation."""

    conversation_history: bool = False
    """Supports multi-turn conversations."""

    custom_tools: bool = False
    """Supports custom tool registration."""


class BaseRuntime(ABC):
    """
    Abstract base class for all agent runtimes.

    This class provides:
    - Standard interface for all runtimes
    - Lifecycle hooks for extensibility
    - Control Plane integration helpers
    - Configuration validation
    - Error handling patterns

    To create a new runtime:
    1. Inherit from BaseRuntime
    2. Implement abstract methods
    3. Register via @RuntimeRegistry.register()
    4. Override lifecycle hooks as needed
    """

    def __init__(
        self,
        control_plane_client: Any,
        cancellation_manager: Any,
        **kwargs,
    ):
        """
        Initialize the runtime.

        Args:
            control_plane_client: Client for Control Plane API
            cancellation_manager: Manager for execution cancellation
            **kwargs: Additional configuration options
        """
        self.control_plane = control_plane_client
        self.cancellation_manager = cancellation_manager
        self.logger = structlog.get_logger(self.__class__.__name__)
        self.config = kwargs

        # Track active executions for cleanup
        self._active_executions: Dict[str, Any] = {}

    # ==================== Abstract Methods (Must Implement) ====================

    @abstractmethod
    async def _execute_impl(
        self, context: RuntimeExecutionContext
    ) -> RuntimeExecutionResult:
        """
        Core execution logic (non-streaming).

        Implement the actual execution logic here without worrying about
        lifecycle hooks, Control Plane integration, or error handling.
        The base class handles those concerns.

        Args:
            context: Execution context

        Returns:
            RuntimeExecutionResult
        """
        pass

    @abstractmethod
    async def _stream_execute_impl(
        self,
        context: RuntimeExecutionContext,
        event_callback: Optional[Callable[[Dict], None]] = None,
    ) -> AsyncIterator[RuntimeExecutionResult]:
        """
        Core streaming execution logic.

        Implement the actual streaming logic here. The base class
        handles lifecycle hooks and error handling.

        Args:
            context: Execution context
            event_callback: Optional callback for events

        Yields:
            RuntimeExecutionResult chunks
        """
        pass

    @abstractmethod
    def get_runtime_type(self) -> RuntimeType:
        """Return the runtime type identifier."""
        pass

    @abstractmethod
    def get_capabilities(self) -> RuntimeCapabilities:
        """Return runtime capabilities."""
        pass

    # ==================== Public Interface (Don't Override) ====================

    async def execute(
        self, context: RuntimeExecutionContext
    ) -> RuntimeExecutionResult:
        """
        Execute agent with full lifecycle management.

        This method orchestrates the entire execution lifecycle:
        1. Validate configuration
        2. Call before_execute hook
        3. Cache metadata in Control Plane
        4. Execute via _execute_impl
        5. Call after_execute hook
        6. Handle errors via on_error hook
        7. Cleanup

        Args:
            context: Execution context

        Returns:
            RuntimeExecutionResult
        """
        execution_id = context.execution_id

        try:
            # 1. Validate configuration
            self._validate_config(context)

            # 2. Before execute hook
            await self.before_execute(context)

            # 3. Cache metadata in Control Plane
            self._cache_execution_metadata(context)

            # 4. Register for cancellation
            if self.get_capabilities().cancellation:
                self.cancellation_manager.register(
                    execution_id=execution_id,
                    instance=self,
                    instance_type=self.__class__.__name__,
                )

            # 5. Execute implementation
            self.logger.info(
                "🚀 Runtime execution started",
                execution_id=execution_id,
                runtime=self.get_runtime_type().value,
                model=context.model_id or "default",
                stream=False
            )

            result = await self._execute_impl(context)

            # 6. After execute hook
            await self.after_execute(context, result)

            self.logger.info(
                "runtime_execute_complete",
                execution_id=execution_id[:8],
                success=result.success,
            )

            return result

        except Exception as e:
            # 7. Error hook
            error_result = await self.on_error(context, e)
            return error_result

        finally:
            # 8. Cleanup
            if self.get_capabilities().cancellation:
                self.cancellation_manager.unregister(execution_id)
            self._active_executions.pop(execution_id, None)

    async def stream_execute(
        self,
        context: RuntimeExecutionContext,
        event_callback: Optional[Callable[[Dict], None]] = None,
    ) -> AsyncIterator[RuntimeExecutionResult]:
        """
        Execute agent with streaming and full lifecycle management.

        Args:
            context: Execution context
            event_callback: Optional callback for events

        Yields:
            RuntimeExecutionResult chunks
        """
        execution_id = context.execution_id

        try:
            # 1. Validate configuration
            self._validate_config(context)

            # 2. Before execute hook
            await self.before_execute(context)

            # 3. Cache metadata in Control Plane
            self._cache_execution_metadata(context)

            # 4. Register for cancellation
            if self.get_capabilities().cancellation:
                self.cancellation_manager.register(
                    execution_id=execution_id,
                    instance=self,
                    instance_type=self.__class__.__name__,
                )

            # 5. Stream implementation
            self.logger.info(
                "🚀 Runtime streaming execution started",
                execution_id=execution_id,
                runtime=self.get_runtime_type().value,
                model=context.model_id or "default",
                stream=True
            )

            final_result = None
            async for chunk in self._stream_execute_impl(context, event_callback):
                yield chunk
                if chunk.finish_reason:
                    final_result = chunk

            # 6. After execute hook
            if final_result:
                await self.after_execute(context, final_result)

            self.logger.info(
                "runtime_stream_complete",
                execution_id=execution_id[:8],
            )

        except Exception as e:
            # 7. Error hook
            error_result = await self.on_error(context, e)
            yield error_result

        finally:
            # 8. Cleanup
            if self.get_capabilities().cancellation:
                self.cancellation_manager.unregister(execution_id)
            self._active_executions.pop(execution_id, None)

    async def cancel(self, execution_id: str) -> bool:
        """
        Cancel an in-progress execution.

        Override _cancel_impl() to provide runtime-specific cancellation logic.

        Args:
            execution_id: ID of execution to cancel

        Returns:
            True if cancellation succeeded
        """
        if not self.get_capabilities().cancellation:
            self.logger.warning(
                "runtime_cancel_not_supported",
                runtime=self.get_runtime_type().value,
            )
            return False

        try:
            return await self._cancel_impl(execution_id)
        except Exception as e:
            self.logger.error(
                "runtime_cancel_failed",
                execution_id=execution_id[:8],
                error=str(e),
            )
            return False

    async def get_usage(self, execution_id: str) -> Dict[str, Any]:
        """
        Get usage metrics for an execution.

        Override _get_usage_impl() to provide runtime-specific usage tracking.

        Args:
            execution_id: ID of execution

        Returns:
            Usage metrics dict
        """
        try:
            return await self._get_usage_impl(execution_id)
        except Exception as e:
            self.logger.error(
                "runtime_get_usage_failed",
                execution_id=execution_id[:8],
                error=str(e),
            )
            return {}

    # ==================== Capabilities API ====================

    def supports_streaming(self) -> bool:
        """Whether this runtime supports streaming execution."""
        return self.get_capabilities().streaming

    def supports_tools(self) -> bool:
        """Whether this runtime supports tool calling."""
        return self.get_capabilities().tools

    def supports_mcp(self) -> bool:
        """Whether this runtime supports MCP servers."""
        return self.get_capabilities().mcp

    def supports_custom_tools(self) -> bool:
        """Whether this runtime supports custom tool extensions."""
        return self.get_capabilities().custom_tools

    def get_runtime_info(self) -> Dict[str, Any]:
        """
        Get information about this runtime implementation.

        Override to provide additional metadata.

        Returns:
            Dict with runtime metadata
        """
        caps = self.get_capabilities()
        return {
            "runtime_type": self.get_runtime_type().value,
            "supports_streaming": caps.streaming,
            "supports_tools": caps.tools,
            "supports_mcp": caps.mcp,
            "supports_hooks": caps.hooks,
            "supports_cancellation": caps.cancellation,
            "supports_conversation_history": caps.conversation_history,
            "supports_custom_tools": caps.custom_tools,
        }

    # ==================== Lifecycle Hooks (Override as Needed) ====================

    async def before_execute(self, context: RuntimeExecutionContext) -> None:
        """
        Hook called before execution starts.

        Override to:
        - Validate additional configuration
        - Setup resources
        - Initialize connections
        - Log execution start

        Args:
            context: Execution context
        """
        pass

    async def after_execute(
        self, context: RuntimeExecutionContext, result: RuntimeExecutionResult
    ) -> None:
        """
        Hook called after successful execution.

        Override to:
        - Cleanup resources
        - Log metrics
        - Update statistics
        - Trigger webhooks

        Args:
            context: Execution context
            result: Execution result
        """
        pass

    async def on_error(
        self, context: RuntimeExecutionContext, error: Exception
    ) -> RuntimeExecutionResult:
        """
        Hook called when execution fails.

        Override to:
        - Custom error handling
        - Error reporting
        - Cleanup
        - Fallback logic

        Args:
            context: Execution context
            error: Exception that occurred

        Returns:
            RuntimeExecutionResult with error details
        """
        self.logger.error(
            "runtime_execution_failed",
            execution_id=context.execution_id[:8],
            runtime=self.get_runtime_type().value,
            error=str(error),
            error_type=type(error).__name__,
        )

        return RuntimeExecutionResult(
            response="",
            usage={},
            success=False,
            error=f"{type(error).__name__}: {str(error)}",
            finish_reason="error",
        )

    # ==================== Helper Methods (Override as Needed) ====================

    async def _cancel_impl(self, execution_id: str) -> bool:
        """
        Runtime-specific cancellation implementation.

        Override to provide custom cancellation logic.

        Args:
            execution_id: ID of execution to cancel

        Returns:
            True if successful
        """
        return False

    async def _get_usage_impl(self, execution_id: str) -> Dict[str, Any]:
        """
        Runtime-specific usage tracking implementation.

        Override to provide usage metrics.

        Args:
            execution_id: ID of execution

        Returns:
            Usage metrics dict
        """
        return {}

    def _validate_config(self, context: RuntimeExecutionContext) -> None:
        """
        Validate runtime configuration.

        Override to add custom validation logic.
        Raise ValueError if configuration is invalid.

        Args:
            context: Execution context

        Raises:
            ValueError: If configuration is invalid
        """
        # Base validation
        if not context.prompt:
            raise ValueError("Prompt is required")
        if not context.execution_id:
            raise ValueError("Execution ID is required")

        # Runtime-specific requirements validation
        try:
            from control_plane_api.worker.runtimes.validation import RuntimeRequirementsRegistry

            is_valid, errors = RuntimeRequirementsRegistry.validate_for_runtime(
                self.get_runtime_type(), context
            )

            if not is_valid:
                error_msg = "Runtime validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
                raise ValueError(error_msg)

        except ImportError:
            # Validation module not available - skip validation
            self.logger.warning("Runtime validation module not available, skipping validation")
        except Exception as e:
            self.logger.error(
                "Runtime validation error",
                error=str(e),
                runtime=self.get_runtime_type().value,
            )
            raise

    def _cache_execution_metadata(self, context: RuntimeExecutionContext) -> None:
        """
        Cache execution metadata in Control Plane.

        This enables:
        - Execution tracking
        - Real-time monitoring
        - Analytics

        Args:
            context: Execution context
        """
        try:
            self.control_plane.cache_metadata(
                context.execution_id,
                "AGENT",
            )
        except Exception as e:
            self.logger.warning(
                "failed_to_cache_metadata",
                execution_id=context.execution_id[:8],
                error=str(e),
            )

    # ==================== Custom Tool Extension API ====================

    def get_custom_tool_requirements(self) -> Dict[str, Any]:
        """
        Get requirements/documentation for creating custom tools for this runtime.

        Override this method to document how developers should create custom tools
        for your runtime.

        Returns:
            Dictionary with:
            - format: Tool format (e.g., "python_class", "mcp_server")
            - description: Human-readable description
            - example_code: Example implementation
            - documentation_url: Link to detailed docs
            - required_methods: List of required methods/attributes
            - schema: JSON schema for validation

        Raises:
            NotImplementedError: If runtime doesn't support custom tools
        """
        if not self.supports_custom_tools():
            raise NotImplementedError(
                f"Runtime {self.get_runtime_type().value} does not support custom tools"
            )
        return {
            "format": "unknown",
            "description": "No documentation available",
            "example_code": "",
            "documentation_url": "",
            "required_methods": [],
            "schema": {}
        }

    def validate_custom_tool(self, tool: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a custom tool for this runtime.

        Override this method to implement runtime-specific validation logic.

        Args:
            tool: Custom tool object (format depends on runtime)

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if tool is valid
            - error_message: Error description if invalid, None if valid

        Raises:
            NotImplementedError: If runtime doesn't support custom tools
        """
        if not self.supports_custom_tools():
            raise NotImplementedError(
                f"Runtime {self.get_runtime_type().value} does not support custom tools"
            )
        return False, "Validation not implemented"

    def register_custom_tool(self, tool: Any, metadata: Optional[Dict] = None) -> str:
        """
        Register a custom tool with this runtime.

        Override this method to implement runtime-specific registration logic.

        Args:
            tool: Custom tool object (format depends on runtime)
            metadata: Optional metadata (name, description, etc.)

        Returns:
            Tool identifier for referencing this tool

        Raises:
            ValueError: If tool is invalid
            NotImplementedError: If runtime doesn't support custom tools
        """
        if not self.supports_custom_tools():
            raise NotImplementedError(
                f"Runtime {self.get_runtime_type().value} does not support custom tools"
            )

        # Validate first
        is_valid, error = self.validate_custom_tool(tool)
        if not is_valid:
            raise ValueError(f"Invalid custom tool: {error}")

        raise NotImplementedError("Custom tool registration not implemented")

    def get_registered_custom_tools(self) -> List[str]:
        """
        Get list of registered custom tool identifiers.

        Override this method to return the list of tools registered with this runtime.

        Returns:
            List of tool identifiers
        """
        return []


class RuntimeRegistry:
    """
    Registry for runtime discovery and instantiation.

    This registry allows runtimes to be:
    - Automatically discovered
    - Registered via decorator
    - Instantiated by name or type
    - Listed for discoverability
    """

    _registry: Dict[RuntimeType, Type[BaseRuntime]] = {}

    @classmethod
    def register(cls, runtime_type: RuntimeType):
        """
        Decorator to register a runtime.

        Usage:
            @RuntimeRegistry.register(RuntimeType.CLAUDE_CODE)
            class ClaudeCodeRuntime(BaseRuntime):
                ...

        Args:
            runtime_type: Type identifier for this runtime

        Returns:
            Decorator function
        """

        def decorator(runtime_class: Type[BaseRuntime]):
            cls._registry[runtime_type] = runtime_class
            logger.info(
                "runtime_registered",
                runtime_type=runtime_type.value,
                runtime_class=runtime_class.__name__,
            )
            return runtime_class

        return decorator

    @classmethod
    def get(cls, runtime_type: RuntimeType) -> Type[BaseRuntime]:
        """
        Get runtime class by type.

        Args:
            runtime_type: Runtime type to get

        Returns:
            Runtime class

        Raises:
            ValueError: If runtime type not found
        """
        if runtime_type not in cls._registry:
            raise ValueError(
                f"Runtime type '{runtime_type.value}' not registered. "
                f"Available: {list(cls._registry.keys())}"
            )
        return cls._registry[runtime_type]

    @classmethod
    def create(
        cls,
        runtime_type: RuntimeType,
        control_plane_client: Any,
        cancellation_manager: Any,
        **kwargs,
    ) -> BaseRuntime:
        """
        Create runtime instance.

        Args:
            runtime_type: Type of runtime to create
            control_plane_client: Control Plane client
            cancellation_manager: Cancellation manager
            **kwargs: Additional configuration

        Returns:
            Runtime instance

        Raises:
            ValueError: If runtime type not found
        """
        runtime_class = cls.get(runtime_type)
        return runtime_class(
            control_plane_client=control_plane_client,
            cancellation_manager=cancellation_manager,
            **kwargs,
        )

    @classmethod
    def list_available(cls) -> List[RuntimeType]:
        """
        List all registered runtime types.

        Returns:
            List of available runtime types
        """
        return list(cls._registry.keys())

    @classmethod
    def get_runtime_info_all(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered runtimes.

        Returns:
            Dict mapping runtime type to info dict
        """
        info = {}
        for runtime_type, runtime_class in cls._registry.items():
            # Instantiate temporarily to get info (mock dependencies)
            try:
                from unittest.mock import MagicMock

                temp_instance = runtime_class(
                    control_plane_client=MagicMock(),
                    cancellation_manager=MagicMock(),
                )
                info[runtime_type.value] = temp_instance.get_runtime_info()
            except Exception as e:
                info[runtime_type.value] = {"error": str(e)}

        return info
