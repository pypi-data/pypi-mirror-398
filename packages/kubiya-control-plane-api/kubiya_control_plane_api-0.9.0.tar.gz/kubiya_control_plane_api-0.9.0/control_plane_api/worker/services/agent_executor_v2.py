"""
Refactored Agent executor service using runtime abstraction.

This version delegates execution to pluggable runtime implementations,
making the code more maintainable and extensible.
"""

from typing import Dict, Any, Optional, List
import structlog
import time
import os
from datetime import datetime, timezone

from control_plane_api.worker.control_plane_client import ControlPlaneClient
from control_plane_api.worker.services.session_service import SessionService
from control_plane_api.worker.services.cancellation_manager import CancellationManager
from control_plane_api.worker.services.analytics_service import AnalyticsService
from control_plane_api.worker.services.runtime_analytics import submit_runtime_analytics
from control_plane_api.worker.runtimes import (
    RuntimeFactory,
    RuntimeType,
    RuntimeExecutionContext,
)
from control_plane_api.worker.utils.streaming_utils import StreamingHelper
from control_plane_api.app.lib.templating.types import TemplateContext
from control_plane_api.app.lib.templating.resolver import resolve_templates
from control_plane_api.worker.utils.logging_config import sanitize_value

logger = structlog.get_logger()


class AgentExecutorServiceV2:
    """
    Service for executing agents using runtime abstraction.

    This service orchestrates agent execution by:
    1. Loading session history
    2. Selecting appropriate runtime based on agent config
    3. Delegating execution to the runtime
    4. Persisting session after execution
    """

    def __init__(
        self,
        control_plane: ControlPlaneClient,
        session_service: SessionService,
        cancellation_manager: CancellationManager,
    ):
        """
        Initialize the agent executor service.

        Args:
            control_plane: Control Plane API client
            session_service: Session management service
            cancellation_manager: Execution cancellation manager
        """
        self.control_plane = control_plane
        self.session_service = session_service
        self.cancellation_manager = cancellation_manager
        self.runtime_factory = RuntimeFactory()

        # Initialize analytics service for tracking LLM usage, tool calls, etc.
        control_plane_url = os.getenv("CONTROL_PLANE_URL", "http://localhost:8000")
        api_key = os.getenv("KUBIYA_API_KEY", "")
        self.analytics_service = AnalyticsService(control_plane_url, api_key)

    async def execute(self, input: Any) -> Dict[str, Any]:
        """
        Execute an agent using the configured runtime.

        This method:
        1. Loads session history
        2. Determines runtime type from agent config
        3. Creates runtime instance
        4. Executes agent via runtime
        5. Persists session
        6. Returns standardized result

        Args:
            input: AgentExecutionInput with execution details

        Returns:
            Dict with response, usage, success flag, runtime_type, etc.
        """
        execution_id = input.execution_id

        # print("\n" + "=" * 80)
        # print("=" * 80)
        # print(f"Execution ID: {execution_id}")
        # print(f"Agent ID: {input.agent_id}")
        # print(f"Organization: {input.organization_id}")
        # print(f"Model: {input.model_id or 'default'}")
        # print(f"Session ID: {input.session_id}")
        # print(
        #     f"Prompt: {input.prompt[:100]}..."
        #     if len(input.prompt) > 100
        #     else f"Prompt: {input.prompt}"
        # )
        # print("=" * 80 + "\n")

        logger.info(
            "agent_workflow_start",
            execution_id=execution_id[:8],
            agent_id=input.agent_id,
            organization_id=input.organization_id,
            model=input.model_id or "default",
            session_id=input.session_id,
        )

        try:
            # Capture timestamp at start of execution for accurate user message timestamp
            from datetime import datetime, timezone
            user_message_timestamp = datetime.now(timezone.utc).isoformat()

            # STEP 1: Load session history
            logger.info("loading_session_history", session_id=input.session_id)
            session_history = self.session_service.load_session(
                execution_id=execution_id, session_id=input.session_id
            )

            if session_history:
                # print(f"✅ Loaded {len(session_history)} messages from previous session\n")
                pass
            else:
                logger.info("starting_new_conversation")

            # STEP 2: Determine runtime type
            agent_config = input.agent_config or {}
            runtime_type_str = agent_config.get("runtime", "default")
            runtime_type = self.runtime_factory.parse_runtime_type(runtime_type_str)

            logger.info("runtime_type_selected",
                runtime_type=runtime_type.value,
                framework=self._get_framework_name(runtime_type))

            logger.info(
                "runtime_selected",
                execution_id=execution_id[:8],
                runtime=runtime_type.value,
            )

            # STEP 3: Create runtime instance
            # print(f"⚙️  Creating runtime instance...")
            runtime = self.runtime_factory.create_runtime(
                runtime_type=runtime_type,
                control_plane_client=self.control_plane,
                cancellation_manager=self.cancellation_manager,
            )
            # print(f"✅ Runtime created: {runtime.get_runtime_info()}\n")

            # STEP 4: Get skills (if runtime supports tools)
            skills = []
            if runtime.supports_tools():
                logger.info("fetching_skills")
                try:
                    skill_configs = self.control_plane.get_skills(input.agent_id)
                    if skill_configs:
                        logger.info("skills_resolved", count=len(skill_configs))
                        # Skill details logged in skills_resolved
                        # Skill details logged in skills_resolved
                        # Skill details logged in skills_resolved

                        # DEBUG: Show full config for workflow_executor skills
                        for cfg in skill_configs:
                            if cfg.get('type') in ['workflow_executor', 'workflow']:
                                logger.debug("workflow_executor_skill_config")
                                # print(f"   Name: {cfg.get('name')}")
                                # print(f"   Type: {cfg.get('type')}")
                                # Skill details logged in skills_resolved
                                # print(f"   Config Keys: {list(cfg.get('configuration', {}).keys())}\n")

                        # Always include built-in context_graph_search skill
                        builtin_skill_types = {'context_graph_search'}
                        existing_skill_types = {cfg.get('type') for cfg in skill_configs}

                        for builtin_type in builtin_skill_types:
                            if builtin_type not in existing_skill_types:
                                builtin_config = {
                                    'name': builtin_type,
                                    'type': builtin_type,
                                    'enabled': True,
                                    'configuration': {}
                                }
                                skill_configs.append(builtin_config)
                                logger.info("builtin_skill_included", skill_type=builtin_type)

                        # Import here to avoid circular dependency
                        from control_plane_api.worker.services.skill_factory import SkillFactory

                        # Create factory instance for the current runtime
                        skill_factory = SkillFactory(runtime_type=runtime_type.value)
                        skill_factory.initialize()

                        skills = skill_factory.create_skills_from_list(
                            skill_configs, execution_id=execution_id
                        )

                        if skills:
                            logger.info("skills_instantiated", count=len(skills))
                            # Show types of instantiated skills
                            skill_types = [type(s).__name__ for s in skills]
                            # Skill classes logged in skills_instantiated
                        else:
                            logger.warning("no_skills_instantiated")
                    else:
                        logger.warning("no_skills_found")
                        # Even if no skills configured, add built-in skills
                        skill_configs = []
                        builtin_skill_types = {'context_graph_search'}

                        for builtin_type in builtin_skill_types:
                            builtin_config = {
                                'name': builtin_type,
                                'type': builtin_type,
                                'enabled': True,
                                'configuration': {}
                            }
                            skill_configs.append(builtin_config)
                            logger.info("builtin_skill_included", skill_type=builtin_type)

                        if skill_configs:
                            # Import here to avoid circular dependency
                            from control_plane_api.worker.services.skill_factory import SkillFactory

                            # Create factory instance for the current runtime
                            skill_factory = SkillFactory(runtime_type=runtime_type.value)
                            skill_factory.initialize()

                            skills = skill_factory.create_skills_from_list(
                                skill_configs, execution_id=execution_id
                            )

                            if skills:
                                logger.info("skills_instantiated", count=len(skills))
                                skill_types = [type(s).__name__ for s in skills]
                                # Skill classes logged in skills_instantiated
                except Exception as e:
                    logger.warning("skill_fetch_error", error=str(e))
                    logger.error("skill_fetch_error", error=str(e), exc_info=True)

            # STEP 5: Inject environment variables into MCP servers (runtime-agnostic)
            logger.info("fetching_resolved_environment")
            from control_plane_api.worker.activities.runtime_activities import inject_env_vars_into_mcp_servers
            mcp_servers_with_env = inject_env_vars_into_mcp_servers(
                mcp_servers=input.mcp_servers,
                agent_config=agent_config,
                runtime_config=agent_config.get("runtime_config"),
                control_plane_client=self.control_plane,
                agent_id=input.agent_id,
            )

            # STEP 6: Compile system prompt templates
            logger.info("compiling_system_prompt_templates")
            compiled_system_prompt = input.system_prompt
            if input.system_prompt:
                try:
                    # Build template context with available variables
                    template_context = TemplateContext(
                        variables=input.user_metadata or {},
                        secrets=agent_config.get("secrets", {}),
                        env_vars=dict(os.environ),  # Make all env vars available
                        # Context graph API configuration for {{.graph.node-id}} templates
                        graph_api_base=os.environ.get("CONTEXT_GRAPH_API_BASE", "https://graph.kubiya.ai"),
                        graph_api_key=os.environ.get("KUBIYA_API_KEY"),
                        graph_org_id=os.environ.get("KUBIYA_ORG_ID") or input.organization_id
                    )

                    # Resolve templates in system prompt
                    compiled_system_prompt = resolve_templates(
                        input.system_prompt,
                        template_context,
                        strict=False,  # Don't fail on missing variables
                        skip_on_error=True  # Return original if compilation fails
                    )

                    if compiled_system_prompt != input.system_prompt:
                        logger.info(
                            "system_prompt_templates_compiled",
                            original_length=len(input.system_prompt),
                            compiled_length=len(compiled_system_prompt)
                        )
                        logger.info("system_prompt_templates_compiled")
                    else:
                        logger.info("no_templates_in_system_prompt")

                except Exception as e:
                    logger.warning(
                        "system_prompt_template_compilation_failed",
                        error=str(e),
                        exc_info=True
                    )
                    logger.warning("system_prompt_compilation_failed", error=str(e))
                    # Use original system prompt if compilation fails
                    compiled_system_prompt = input.system_prompt

            # STEP 6.5: Enhance system prompt with complete execution environment context
            execution_context_info = self._build_execution_context_info(
                runtime_config=agent_config.get("runtime_config", {}),
                skills=skills,
                mcp_servers=mcp_servers_with_env,
                agent_config=agent_config
            )
            if execution_context_info:
                if compiled_system_prompt:
                    compiled_system_prompt = compiled_system_prompt + "\n\n" + execution_context_info
                else:
                    compiled_system_prompt = execution_context_info
                logger.info("system_prompt_enhanced")

            # STEP 7: Build execution context
            logger.info("building_execution_context")
            context = RuntimeExecutionContext(
                execution_id=execution_id,
                agent_id=input.agent_id,
                organization_id=input.organization_id,
                prompt=input.prompt,
                system_prompt=compiled_system_prompt,
                conversation_history=session_history,
                model_id=input.model_id,
                model_config=input.model_config,
                agent_config=agent_config,
                skills=skills,
                skill_configs=skill_configs,  # Original skill configurations for prompt enhancement
                mcp_servers=mcp_servers_with_env,  # Use MCP servers with injected env vars
                user_metadata=input.user_metadata,
                runtime_config=agent_config.get("runtime_config"),
            )
            logger.info("execution_context_ready")

            # STEP 7: Publish user message to stream before execution
            # This ensures chronological ordering in UI
            turn_number = len(session_history) // 2 + 1
            user_message_id = f"{execution_id}_user_{turn_number}"
            self.control_plane.publish_event(
                execution_id=execution_id,
                event_type="message",
                data={
                    "role": "user",
                    "content": input.prompt,
                    "timestamp": user_message_timestamp,
                    "message_id": user_message_id,
                    "user_id": input.user_id,
                    "user_name": getattr(input, "user_name", None),
                    "user_email": getattr(input, "user_email", None),
                    "user_avatar": getattr(input, "user_avatar", None),
                }
            )
            logger.debug("user_message_published", message_id=user_message_id)

            # Publish status message chunk: Connecting to worker
            assistant_message_id = f"{execution_id}_assistant_{turn_number}"
            await self.control_plane.publish_event_async(
                execution_id=execution_id,
                event_type="message_chunk",
                data={
                    "role": "assistant",
                    "content": "Connecting to worker...\n",
                    "is_chunk": True,
                    "message_id": assistant_message_id,
                }
            )
            # print(f"   📤 Published status: 'Connecting to worker...'\n")

            # STEP 8: Execute via runtime (with streaming if supported)
            # print("⚡ Executing via runtime...\n")

            # Track turn start time for analytics
            turn_start_time = time.time()

            # Create streaming helper for tracking tool messages (used in both streaming and non-streaming)
            streaming_helper = StreamingHelper(
                control_plane_client=self.control_plane, execution_id=execution_id
            )

            if runtime.supports_streaming():
                result = await self._execute_streaming(runtime, context, input, streaming_helper)
            else:
                result = await runtime.execute(context)

            # Track turn end time
            turn_end_time = time.time()

            # print("\n✅ Runtime execution completed!")
            logger.info("response_length", length=len(result["response"]))
            # print(f"   Success: {result.success}\n")

            logger.info(
                "agent_execution_completed",
                execution_id=execution_id[:8],
                success=result.success,
                response_length=len(result.response),
            )

            # STEP 7.5: Submit analytics (non-blocking, fire-and-forget)
            if result.success and result.usage:
                try:
                    # Submit analytics in the background (doesn't block execution)
                    await submit_runtime_analytics(
                        result=result,
                        execution_id=execution_id,
                        turn_number=turn_number,
                        turn_start_time=turn_start_time,
                        turn_end_time=turn_end_time,
                        analytics_service=self.analytics_service,
                    )
                    logger.info(
                        "analytics_submitted",
                        execution_id=execution_id[:8],
                        tokens=result.usage.get("total_tokens", 0),
                    )
                except Exception as analytics_error:
                    # Analytics failures should not break execution
                    logger.warning(
                        "analytics_submission_failed",
                        execution_id=execution_id[:8],
                        error=str(analytics_error),
                    )

            # STEP 7: Persist session
            if result.success and result.response:
                logger.info("persisting_session_history")

                # Finalize streaming to transition to post-tool phase
                streaming_helper.finalize_streaming()

                # Build user message
                user_message = {
                    "role": "user",
                    "content": input.prompt,
                    "timestamp": user_message_timestamp,  # Use timestamp from start
                    "message_id": f"{execution_id}_user_{turn_number}",
                    "user_id": input.user_id,
                    "user_name": getattr(input, "user_name", None),
                    "user_email": getattr(input, "user_email", None),
                }

                # Build structured messages using StreamingHelper
                # This properly splits assistant messages around tool usage
                new_messages = streaming_helper.build_structured_messages(
                    execution_id=execution_id,
                    turn_number=turn_number,
                    user_message=user_message,
                )

                logger.debug("structured_messages_built", count=len(new_messages))
                if streaming_helper.has_any_tools:
                    logger.debug("assistant_message_split_into_phases")
                    assistant_parts = streaming_helper.get_assistant_message_parts()
                    for part in assistant_parts:
                        logger.debug("message_part", phase=part["phase"], length=len(part["content"]))

                # Combine with previous history
                complete_session = session_history + new_messages

                # CRITICAL: Deduplicate messages by message_id AND content to prevent duplicates
                # Use session_service.deduplicate_messages() which has enhanced two-level deduplication
                original_count = len(complete_session)
                complete_session = self.session_service.deduplicate_messages(complete_session)
                deduplicated_count = len(complete_session)

                # CRITICAL: Sort by timestamp to ensure chronological order
                # Tool messages happen DURING streaming, so they need to be interleaved with user/assistant messages
                complete_session.sort(key=lambda msg: msg.get("timestamp", ""))
                logger.info("messages_deduplicated", before=original_count, after=deduplicated_count, removed=original_count - deduplicated_count)

                success = self.session_service.persist_session(
                    execution_id=execution_id,
                    session_id=input.session_id or execution_id,
                    user_id=input.user_id,
                    messages=complete_session,
                    metadata={
                        "agent_id": input.agent_id,
                        "organization_id": input.organization_id,
                        "runtime_type": runtime_type.value,
                        "turn_count": len(complete_session),
                    },
                )

                if success:
                    # print(f"✅ Session persisted ({len(complete_session)} total messages)\n")
                    pass
                else:
                    logger.warning("session_persistence_failed")

            # STEP 8: Print usage metrics
            if result.usage:
                logger.info("token_usage",
                    prompt_tokens=result["usage"].get("prompt_tokens", 0),
                    completion_tokens=result["usage"].get("completion_tokens", 0),
                    total_tokens=result["usage"].get("total_tokens", 0))

            # print("=" * 80)
            logger.info("agent_execution_end")
            # print("=" * 80 + "\n")

            # Return standardized result
            return {
                "success": result.success,
                "response": result.response,
                "usage": result.usage,
                "model": result.model or input.model_id,
                "finish_reason": result.finish_reason or "stop",
                "run_id": result.run_id,
                "tool_messages": result.tool_messages or [],
                "runtime_type": runtime_type.value,
                "error": result.error,
            }

        except Exception as e:
            # print("\n" + "=" * 80)
            logger.error("agent_execution_failed")
            # print("=" * 80)
            logger.error("execution_error", error=str(e))
            # print("=" * 80 + "\n")

            logger.error(
                "agent_execution_failed", execution_id=execution_id[:8], error=str(e)
            )

            # Publish critical error as message to the stream
            try:
                error_message = f"❌ Critical Error: {str(e)}"
                turn_number = len(session_history) // 2 + 1 if "session_history" in locals() else 1
                assistant_message_id = f"{execution_id}_assistant_{turn_number}"

                self.control_plane.publish_event(
                    execution_id=execution_id,
                    event_type="message",
                    data={
                        "role": "assistant",
                        "content": error_message,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "message_id": assistant_message_id,
                        "is_error": True,
                    }
                )
                # print(f"   📤 Published critical error to stream\n")
            except Exception as publish_error:
                # Don't let error publishing break the error handling
                logger.warning(
                    "failed_to_publish_error_event",
                    execution_id=execution_id[:8],
                    error=str(publish_error)
                )

            return {
                "success": False,
                "error": str(e),
                "model": input.model_id,
                "usage": {},
                "finish_reason": "error",
                "runtime_type": runtime_type.value if "runtime_type" in locals() else "unknown",
            }

    async def _execute_streaming(
        self, runtime, context: RuntimeExecutionContext, input: Any, streaming_helper: StreamingHelper
    ) -> Any:
        """
        Execute with streaming and publish events to Control Plane.

        Args:
            runtime: Runtime instance
            context: Execution context
            input: Original input for additional metadata
            streaming_helper: StreamingHelper instance for tracking events

        Returns:
            Final RuntimeExecutionResult
        """
        # streaming_helper is now passed as parameter instead of created here

        accumulated_response = ""
        final_result = None

        # Define event callback for publishing to Control Plane
        def event_callback(event: Dict):
            """Callback to publish events to Control Plane SSE"""
            event_type = event.get("type")

            if event_type == "content_chunk":
                # Publish content chunk
                streaming_helper.publish_content_chunk(
                    content=event.get("content", ""),
                    message_id=event.get("message_id", context.execution_id),
                )
            elif event_type == "tool_start":
                # Publish tool start
                streaming_helper.publish_tool_start(
                    tool_name=event.get("tool_name"),
                    tool_execution_id=event.get("tool_execution_id"),
                    tool_args=event.get("tool_args", {}),
                    source="agent",
                )
            elif event_type == "tool_complete":
                # Publish tool completion
                streaming_helper.publish_tool_complete(
                    tool_name=event.get("tool_name"),
                    tool_execution_id=event.get("tool_execution_id"),
                    status=event.get("status", "success"),
                    output=event.get("output"),
                    error=event.get("error"),
                    source="agent",
                )

        # Stream execution
        async for chunk in runtime.stream_execute(context, event_callback):
            if chunk.response:
                accumulated_response += chunk.response
                # print(chunk.response, end="", flush=True)

            # Keep final result for metadata
            if chunk.usage or chunk.finish_reason:
                final_result = chunk

        # Empty line removed

        # Return final result with accumulated response
        if final_result:
            # Update response with accumulated content
            final_result.response = accumulated_response
            return final_result
        else:
            # Create final result if not provided
            from runtimes.base import RuntimeExecutionResult

            return RuntimeExecutionResult(
                response=accumulated_response,
                usage={},
                success=True,
                finish_reason="stop",
            )

    def _build_execution_context_info(
        self,
        runtime_config: Dict[str, Any],
        skills: List[Any],
        mcp_servers: Optional[Dict[str, Any]],
        agent_config: Dict[str, Any]
    ) -> str:
        """
        Build comprehensive execution environment context for system prompt.

        This provides the agent with awareness of:
        - Available environment variables (secrets, integrations, config)
        - Available skills/tools
        - MCP servers
        - Runtime configuration

        Args:
            runtime_config: Runtime configuration with env vars
            skills: List of available skills
            mcp_servers: Dictionary of MCP server configurations
            agent_config: Agent configuration

        Returns:
            Formatted execution context string for system prompt
        """
        context_parts = []
        context_parts.append("---")
        context_parts.append("")
        context_parts.append("# 🔧 Execution Environment Context")
        context_parts.append("")
        context_parts.append("You are running in a managed execution environment with the following resources available:")
        context_parts.append("")

        # 1. Environment Variables
        if runtime_config and "env" in runtime_config:
            available_env_vars = runtime_config["env"]

            # Categorize environment variables
            secrets = [k for k in available_env_vars.keys() if any(
                keyword in k.lower()
                for keyword in ["secret", "password", "credential", "api_key", "private_key"]
            ) and k not in ["KUBIYA_API_KEY", "KUBIYA_API_BASE", "ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL"]]

            integrations = [k for k in available_env_vars.keys() if any(
                prefix in k
                for prefix in ["GH_TOKEN", "GITHUB_", "JIRA_", "SLACK_", "AWS_", "GCP_", "AZURE_"]
            )]

            inherited_vars = [k for k in available_env_vars.keys()
                             if k not in secrets
                             and k not in integrations
                             and k not in ["KUBIYA_API_KEY", "KUBIYA_API_BASE", "ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "LITELLM_API_KEY", "LITELLM_API_BASE"]]

            context_parts.append("## 📦 Environment Variables")
            context_parts.append("")

            if secrets:
                context_parts.append("**Secrets & API Keys** (use these for authenticated operations):")
                for var in sorted(secrets):
                    context_parts.append(f"- `${var}` - Secret/credential available as environment variable")
                context_parts.append("")

            if integrations:
                context_parts.append("**Integration Tokens** (pre-configured service access):")
                for var in sorted(integrations):
                    service = var.split("_")[0].title() if "_" in var else var
                    context_parts.append(f"- `${var}` - {service} integration token")
                context_parts.append("")

            if inherited_vars:
                context_parts.append("**Configuration Variables** (inherited from environment):")
                # Limit to first 10 to avoid clutter
                for var in sorted(inherited_vars)[:10]:
                    context_parts.append(f"- `${var}`")
                if len(inherited_vars) > 10:
                    context_parts.append(f"- ... and {len(inherited_vars) - 10} more")
                context_parts.append("")

            if secrets or integrations or inherited_vars:
                context_parts.append("**Usage Examples:**")
                context_parts.append("```bash")
                context_parts.append("# Access in Bash commands")
                context_parts.append("echo $VARIABLE_NAME")
                context_parts.append("")
                if integrations:
                    example_token = sorted(integrations)[0]
                    if "GH" in example_token or "GITHUB" in example_token:
                        context_parts.append("# Use with GitHub API")
                        context_parts.append(f"curl -H \"Authorization: token ${example_token}\" https://api.github.com/user")
                    elif "JIRA" in example_token:
                        context_parts.append("# Use with Jira API")
                        context_parts.append(f"curl -H \"Authorization: Bearer ${example_token}\" https://yourinstance.atlassian.net/rest/api/3/myself")
                context_parts.append("```")
                context_parts.append("")

        # 2. Available Skills/Tools
        if skills:
            context_parts.append("## 🛠️  Available Skills/Tools")
            context_parts.append("")
            skill_names = []
            for skill in skills:
                if isinstance(skill, dict):
                    skill_names.append(skill.get("name", skill.get("type", "Unknown")))
                else:
                    skill_names.append(type(skill).__name__ if hasattr(skill, '__class__') else str(skill))

            if skill_names:
                context_parts.append(f"You have access to {len(skill_names)} skill(s):")
                for skill_name in sorted(set(skill_names))[:15]:  # Limit to 15 to avoid clutter
                    context_parts.append(f"- `{skill_name}`")
                if len(set(skill_names)) > 15:
                    context_parts.append(f"- ... and {len(set(skill_names)) - 15} more")
                context_parts.append("")

        # 3. MCP Servers
        if mcp_servers:
            context_parts.append("## 🔌 MCP Servers")
            context_parts.append("")
            context_parts.append(f"You have access to {len(mcp_servers)} MCP server(s):")
            for server_name in sorted(mcp_servers.keys())[:10]:  # Limit to 10
                context_parts.append(f"- `{server_name}`")
            if len(mcp_servers) > 10:
                context_parts.append(f"- ... and {len(mcp_servers) - 10} more")
            context_parts.append("")
            context_parts.append("**Note:** All environment variables listed above are automatically available to these MCP servers.")
            context_parts.append("")

        # 4. Best Practices
        context_parts.append("## 💡 Best Practices")
        context_parts.append("")
        context_parts.append("- **Environment Variables**: All listed variables are ready to use - no configuration needed")
        context_parts.append("- **Secrets**: Never log or display secret values in responses")
        context_parts.append("- **Integration Tokens**: These provide pre-authorized access to external services")
        context_parts.append("- **MCP Tools**: Prefer using MCP tools over Bash when available for better reliability")
        context_parts.append("")
        context_parts.append("---")

        logger.info(
            "execution_context_info_built",
            env_vars_count=len(runtime_config.get("env", {})) if runtime_config else 0,
            skills_count=len(skills) if skills else 0,
            mcp_servers_count=len(mcp_servers) if mcp_servers else 0
        )

        return "\n".join(context_parts)

    def _get_framework_name(self, runtime_type: RuntimeType) -> str:
        """
        Get friendly framework name for runtime type.

        Args:
            runtime_type: Runtime type enum

        Returns:
            Framework name string
        """
        mapping = {
            RuntimeType.DEFAULT: "Agno",
            RuntimeType.CLAUDE_CODE: "Claude Code SDK",
        }
        return mapping.get(runtime_type, "Unknown")
