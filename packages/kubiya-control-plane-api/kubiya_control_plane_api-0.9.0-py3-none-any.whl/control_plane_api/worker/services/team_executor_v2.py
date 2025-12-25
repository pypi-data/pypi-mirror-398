"""
Team executor service with runtime abstraction support.

This version supports both Agno-based teams and Claude Code SDK runtime teams.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import structlog
import asyncio
import os
import time

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


class TeamExecutorServiceV2:
    """
    Service for executing teams using runtime abstraction.

    This service orchestrates team execution by:
    1. Loading session history
    2. Determining runtime type (Agno or Claude Code)
    3. Delegating execution to appropriate runtime
    4. Persisting session after execution

    For Claude Code runtime:
    - Team leader uses Claude Code SDK with Task tool
    - Team members are executed as subagents via Task tool
    - Streaming and tool hooks supported

    For Agno runtime:
    - Uses existing Agno Team implementation
    - Full multi-agent coordination support
    """

    def __init__(
        self,
        control_plane: ControlPlaneClient,
        session_service: SessionService,
        cancellation_manager: CancellationManager,
    ):
        """
        Initialize the team executor service.

        Args:
            control_plane: Control Plane API client
            session_service: Session management service
            cancellation_manager: Execution cancellation manager
        """
        self.control_plane = control_plane
        self.session_service = session_service
        self.cancellation_manager = cancellation_manager
        self.runtime_factory = RuntimeFactory()
        self.streaming_helper = None  # Will be set during execution for tool message tracking

        # Initialize analytics service for tracking LLM usage, tool calls, etc.
        control_plane_url = os.getenv("CONTROL_PLANE_URL", "http://localhost:8000")
        api_key = os.getenv("KUBIYA_API_KEY", "")
        self.analytics_service = AnalyticsService(control_plane_url, api_key)

    async def execute(self, input: Any) -> Dict[str, Any]:
        """
        Execute a team using the configured runtime.

        Args:
            input: TeamExecutionInput with execution details

        Returns:
            Dict with response, usage, success flag, runtime_type, etc.
        """
        execution_id = input.execution_id

        logger.info(
            "team_workflow_start",
            execution_id=execution_id,
            team_id=input.team_id,
            organization_id=input.organization_id,
            agent_count=len(input.agents),
            session_id=input.session_id,
            prompt_preview=input.prompt[:100] + "..." if len(input.prompt) > 100 else input.prompt
        )

        try:
            # Capture timestamp at start of execution for accurate user message timestamp
            from datetime import datetime, timezone
            user_message_timestamp = datetime.now(timezone.utc).isoformat()

            # STEP 1: Load session history
            logger.info("loading_session_history", session_id=input.session_id)
            session_history = self.session_service.load_session(
                execution_id=execution_id,
                session_id=input.session_id
            )

            if session_history:
                logger.info("session_history_loaded", message_count=len(session_history))
            else:
                logger.info("starting_new_conversation", session_id=input.session_id)

            # STEP 2: Determine runtime type
            # Priority: input.runtime_type (if explicitly set) > team_config.runtime > "default"
            runtime_type_str = getattr(input, "runtime_type", "default")
            team_config = getattr(input, "team_config", {}) or {}

            # Debug: Log what we received
            logger.debug("runtime_type_input", input_runtime_type=runtime_type_str)
            logger.debug("team_config_keys", keys=list(team_config.keys()))
            if "runtime" in team_config:
                logger.debug("team_config_runtime", runtime=team_config.get('runtime'))

            # If runtime_type is still "default", check team_config.runtime
            if runtime_type_str == "default" and "runtime" in team_config:
                runtime_type_str = team_config.get("runtime", "default")
                logger.debug("using_team_config_runtime", runtime=runtime_type_str)

            runtime_type = self.runtime_factory.parse_runtime_type(runtime_type_str)

            logger.info(
                "runtime_type_selected",
                runtime_type=runtime_type.value,
                framework=self._get_framework_name(runtime_type)
            )

            logger.info(
                "runtime_selected",
                execution_id=execution_id[:8],
                runtime=runtime_type.value,
            )

            # STEP 3: Publish user message to stream before execution
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

            # STEP 4: Execute based on runtime type
            if runtime_type == RuntimeType.CLAUDE_CODE:
                result = await self._execute_with_claude_code(input, session_history, runtime_type)
            else:
                # Fall back to Agno-based team execution
                from control_plane_api.worker.services.team_executor import TeamExecutorService

                agno_executor = TeamExecutorService(
                    self.control_plane,
                    self.session_service,
                    self.cancellation_manager
                )
                return await agno_executor.execute(input)

            logger.info("team_execution_completed")
            logger.info("execution_response_length", length=len(result['response']))
            logger.info("execution_success_status", success=result['success'])

            logger.info(
                "team_execution_completed",
                execution_id=execution_id[:8],
                success=result["success"],
                response_length=len(result["response"]),
            )

            # STEP 4: Persist session
            if result["success"] and result["response"]:
                logger.info("persisting_session_history")

                turn_number = len(session_history) // 2 + 1

                # Finalize streaming to transition to post-tool phase
                if self.streaming_helper:
                    self.streaming_helper.finalize_streaming()

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
                if self.streaming_helper:
                    new_messages = self.streaming_helper.build_structured_messages(
                        execution_id=execution_id,
                        turn_number=turn_number,
                        user_message=user_message,
                    )

                    logger.debug("structured_messages_built", count=len(new_messages))
                    if self.streaming_helper.has_any_tools:
                        logger.debug("assistant_message_split_into_phases")
                        assistant_parts = self.streaming_helper.get_assistant_message_parts()
                        for part in assistant_parts:
                            logger.debug("message_part", phase=part['phase'], length=len(part['content']))
                else:
                    # Fallback if no streaming helper (shouldn't happen)
                    assistant_message_timestamp = datetime.now(timezone.utc).isoformat()
                    new_messages = [
                        user_message,
                        {
                            "role": "assistant",
                            "content": result["response"],
                            "timestamp": assistant_message_timestamp,
                            "message_id": f"{execution_id}_assistant_{turn_number}",
                        },
                    ]

                # Combine with previous history
                complete_session = session_history + new_messages

                # CRITICAL: Deduplicate messages by message_id AND content to prevent duplicates
                # Use session_service.deduplicate_messages() which has enhanced two-level deduplication
                original_count = len(complete_session)
                complete_session = self.session_service.deduplicate_messages(complete_session)

                # CRITICAL: Sort by timestamp to ensure chronological order
                # Tool messages happen DURING streaming, so they need to be interleaved with user/assistant messages
                complete_session.sort(key=lambda msg: msg.get("timestamp", ""))
                logger.info("messages_deduplicated", before=original_count, after=len(complete_session))

                success = self.session_service.persist_session(
                    execution_id=execution_id,
                    session_id=input.session_id or execution_id,
                    user_id=input.user_id,
                    messages=complete_session,
                    metadata={
                        "team_id": input.team_id,
                        "organization_id": input.organization_id,
                        "runtime_type": runtime_type.value,
                        "turn_count": len(complete_session),
                        "member_count": len(input.agents),
                    },
                )

                if success:
                    logger.info("session_persisted", total_messages=len(complete_session))
                else:
                    logger.warning("session_persistence_failed")

            # STEP 5: Print usage metrics
            if result.get("usage"):
                logger.info("token_usage_summary",
                    prompt_tokens=result['usage'].get('prompt_tokens', 0),
                    completion_tokens=result['usage'].get('completion_tokens', 0),
                    total_tokens=result['usage'].get('total_tokens', 0))

            # Banner removed - using structured logging
            logger.info("team_execution_end")
            return result

        except Exception as e:
            logger.error("team_execution_failed")
            # Banner removed - using structured logging
            logger.error("execution_error", error=str(e))
            logger.error(
                "team_execution_failed",
                execution_id=execution_id[:8],
                error=str(e)
            )

            return {
                "success": False,
                "error": str(e),
                "model": input.model_id,
                "usage": {},
                "finish_reason": "error",
                "runtime_type": runtime_type_str if "runtime_type_str" in locals() else "unknown",
            }

    async def _execute_with_claude_code(
        self, input: Any, session_history: List[Dict], runtime_type: RuntimeType
    ) -> Dict[str, Any]:
        """
        Execute team using Claude Code SDK.

        Strategy (V2 with native subagents):
        - If all members are Claude Code → use native SDK subagents (optimal)
        - Otherwise → use Task tool delegation (current implementation)

        Args:
            input: TeamExecutionInput
            session_history: Previous conversation messages

        Returns:
            Result dict
        """
        execution_id = input.execution_id

        # Check if we can use native subagent support
        if input.agents and self._all_members_are_claude_code(input.agents):
            logger.info("native_subagent_path_detected")
            logger.info(
                "using_native_subagents",
                execution_id=execution_id[:8],
                member_count=len(input.agents),
            )
            return await self._execute_claude_code_team_with_native_subagents(input, session_history)

        # Fall back to Task tool delegation for mixed or non-Claude Code teams
        logger.info("creating_claude_code_team_leader")
        logger.info(
            "using_task_tool_delegation",
            execution_id=execution_id[:8],
            member_count=len(input.agents) if input.agents else 0,
        )

        # Create runtime instance
        runtime = self.runtime_factory.create_runtime(
            runtime_type=RuntimeType.CLAUDE_CODE,
            control_plane_client=self.control_plane,
            cancellation_manager=self.cancellation_manager,
        )

        logger.info("runtime_created", info=runtime.get_runtime_info())

        # STEP 1: Build team context for system prompt
        team_context = self._build_team_context(input.agents)

        system_prompt = f"""You are the team leader coordinating a team of specialized AI agents.

Your team members:
{team_context}

When you need a team member to perform a task:
1. Use the Task tool to delegate work to the appropriate agent
2. Provide clear instructions in the subagent_type parameter
3. Wait for their response before continuing
4. Synthesize the results into a cohesive answer

Your goal is to coordinate the team effectively to solve the user's request.
"""

        logger.info("team_context", member_count=len(input.agents))
        # Logged in team_context above
        for agent in input.agents:
                logger.debug("team_member_info", name=agent.get('name'), role=agent.get('role', 'No role specified')[:60])
        # Empty print removed

        # STEP 2: Get skills for team leader (must include Task tool)
        logger.info("fetching_skills_from_control_plane")
        skills = []
        try:
            # Get skills from first agent (team leader)
            if input.agents:
                leader_id = input.agents[0].get("id")
                if leader_id:
                    skill_configs = self.control_plane.get_skills(leader_id)
                    if skill_configs:
                        logger.info("skills_resolved", count=len(skill_configs))
                    else:
                        skill_configs = []

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
                            logger.info("builtin_skill_auto_included", skill_type=builtin_type)

                    if skill_configs:
                        from control_plane_api.worker.services.skill_factory import SkillFactory

                        # Create factory instance for the current runtime
                        logger.debug("creating_skill_factory", runtime_type=runtime_type.value)
                        skill_factory = SkillFactory(runtime_type=runtime_type.value)  # Use actual runtime
                        skill_factory.initialize()

                        skills = skill_factory.create_skills_from_list(skill_configs, execution_id=input.execution_id)

                        if skills:
                            logger.info("skills_instantiated", count=len(skills))
        except Exception as e:
            logger.warning("skill_fetch_error", error=str(e))
            logger.error("skill_fetch_error", error=str(e))

        # Always ensure Task tool is available for delegation
        task_skill = {"type": "task", "name": "Task"}
        if task_skill not in skills:
            skills.append(task_skill)
            logger.info("task_tool_added_for_coordination")

        # STEP 3: Inject environment variables into MCP servers (runtime-agnostic)
        logger.info("fetching_resolved_environment")
        from control_plane_api.worker.activities.runtime_activities import inject_env_vars_into_mcp_servers
        team_config = getattr(input, "team_config", {}) or {}
        mcp_servers_with_env = inject_env_vars_into_mcp_servers(
            mcp_servers=getattr(input, "mcp_servers", None),
            agent_config=team_config,
            runtime_config=team_config.get("runtime_config"),
            control_plane_client=self.control_plane,
            team_id=input.team_id,
        )

        # STEP 4: Compile system prompt templates
        logger.info("compiling_system_prompt_templates")
        compiled_system_prompt = system_prompt
        if system_prompt:
            try:
                # Build template context with available variables
                template_context = TemplateContext(
                    variables=getattr(input, "user_metadata", None) or {},
                    secrets=team_config.get("secrets", {}),
                    env_vars=dict(os.environ),  # Make all env vars available
                    # Context graph API configuration for {{.graph.node-id}} templates
                    graph_api_base=os.environ.get("CONTEXT_GRAPH_API_BASE", "https://graph.kubiya.ai"),
                    graph_api_key=os.environ.get("KUBIYA_API_KEY"),
                    graph_org_id=os.environ.get("KUBIYA_ORG_ID") or input.organization_id
                )

                # Resolve templates in system prompt
                compiled_system_prompt = resolve_templates(
                    system_prompt,
                    template_context,
                    strict=False,  # Don't fail on missing variables
                    skip_on_error=True  # Return original if compilation fails
                )

                if compiled_system_prompt != system_prompt:
                    logger.info(
                        "team_system_prompt_templates_compiled",
                        original_length=len(system_prompt),
                        compiled_length=len(compiled_system_prompt)
                    )
                    logger.info("system_prompt_templates_compiled")
                else:
                    logger.info("no_templates_in_system_prompt")

            except Exception as e:
                logger.warning(
                    "team_system_prompt_template_compilation_failed",
                    error=str(e),
                    exc_info=True
                )
                logger.warning("system_prompt_compilation_failed", error=str(e))
                # Use original system prompt if compilation fails
                compiled_system_prompt = system_prompt

        # STEP 4.5: Enhance system prompt with complete execution environment context
        execution_context_info = self._build_execution_context_info(
            runtime_config=team_config.get("runtime_config", {}),
            skills=skills,
            mcp_servers=mcp_servers_with_env,
            team_config=team_config
        )
        if execution_context_info:
            if compiled_system_prompt:
                compiled_system_prompt = compiled_system_prompt + "\n\n" + execution_context_info
            else:
                compiled_system_prompt = execution_context_info
            logger.info("system_prompt_enhanced_with_context")

        # STEP 5: Build execution context
        logger.info("building_execution_context")
        context = RuntimeExecutionContext(
            execution_id=execution_id,
            agent_id=input.team_id,  # Use team_id as agent_id
            organization_id=input.organization_id,
            prompt=input.prompt,
            system_prompt=compiled_system_prompt,
            conversation_history=session_history,
            model_id=input.model_id,
            model_config=getattr(input, "model_config", None),
            agent_config=team_config,
            skills=skills,
            mcp_servers=mcp_servers_with_env,  # Use MCP servers with injected env vars
            user_metadata=getattr(input, "user_metadata", None),
            runtime_config=team_config.get("runtime_config"),
        )
        logger.info("execution_context_ready")

        # STEP 5: Execute via runtime with streaming
        logger.info("executing_team_via_claude_code")

        # Track turn start time for analytics
        turn_start_time = time.time()
        turn_number = len(session_history) // 2 + 1  # Approximate turn number

        # Create streaming helper for tracking tool messages (used in both streaming and non-streaming)
        self.streaming_helper = StreamingHelper(
            control_plane_client=self.control_plane, execution_id=input.execution_id
        )

        if runtime.supports_streaming():
            result = await self._execute_streaming(runtime, context, input, self.streaming_helper)
        else:
            exec_result = await runtime.execute(context)
            from datetime import datetime, timezone
            result = {
                "success": exec_result.success,
                "response": exec_result.response,
                "response_timestamp": datetime.now(timezone.utc).isoformat(),
                "usage": exec_result.usage,
                "model": exec_result.model or input.model_id,
                "finish_reason": exec_result.finish_reason or "stop",
                "tool_messages": exec_result.tool_messages or [],
                "runtime_type": "claude_code",
                "error": exec_result.error,
                "team_member_count": len(input.agents),
            }

        # Track turn end time
        turn_end_time = time.time()

        # Submit analytics (non-blocking, fire-and-forget)
        if result.get("success") and result.get("usage"):
            try:
                # Convert result dict to RuntimeExecutionResult for analytics
                from runtimes.base import RuntimeExecutionResult
                runtime_result = RuntimeExecutionResult(
                    response=result["response"],
                    usage=result["usage"],
                    success=result["success"],
                    finish_reason=result.get("finish_reason", "stop"),
                    model=result.get("model"),
                    tool_messages=result.get("tool_messages", []),
                    error=result.get("error"),
                )

                # Submit analytics in the background (doesn't block execution)
                await submit_runtime_analytics(
                    result=runtime_result,
                    execution_id=execution_id,
                    turn_number=turn_number,
                    turn_start_time=turn_start_time,
                    turn_end_time=turn_end_time,
                    analytics_service=self.analytics_service,
                )
                logger.info(
                    "team_analytics_submitted",
                    execution_id=execution_id[:8],
                    tokens=result["usage"].get("total_tokens", 0),
                )
            except Exception as analytics_error:
                # Analytics failures should not break execution
                logger.warning(
                    "team_analytics_submission_failed",
                    execution_id=execution_id[:8],
                    error=str(analytics_error),
                )

        return result

    async def _execute_streaming(
        self, runtime, context: RuntimeExecutionContext, input: Any, streaming_helper: StreamingHelper
    ) -> Dict[str, Any]:
        """
        Execute with streaming and publish events to Control Plane.

        Args:
            runtime: Runtime instance
            context: Execution context
            input: Original input for additional metadata
            streaming_helper: StreamingHelper instance for tracking events

        Returns:
            Result dict
        """
        # streaming_helper is now passed as parameter instead of created here
        from temporalio import activity

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
                    source="team_leader",
                )
            elif event_type == "tool_complete":
                # Publish tool completion
                streaming_helper.publish_tool_complete(
                    tool_name=event.get("tool_name"),
                    tool_execution_id=event.get("tool_execution_id"),
                    status=event.get("status", "success"),
                    output=event.get("output"),
                    error=event.get("error"),
                    source="team_leader",
                )

        # Stream execution
        # Note: Temporal will raise asyncio.CancelledError when workflow cancels
        # No need to check explicitly - cancellation happens automatically
        async for chunk in runtime.stream_execute(context, event_callback):
            if chunk.response:
                accumulated_response += chunk.response
                # Streaming output handled by response - removed print

            # Keep final result for metadata
            if chunk.usage or chunk.finish_reason:
                final_result = chunk

        # Empty print removed  # New line after streaming

        # Return final result with accumulated response
        from datetime import datetime, timezone
        response_timestamp = datetime.now(timezone.utc).isoformat()

        if final_result:
            return {
                "success": final_result.success,
                "response": accumulated_response,
                "response_timestamp": response_timestamp,
                "usage": final_result.usage,
                "model": final_result.model or input.model_id,
                "finish_reason": final_result.finish_reason or "stop",
                "tool_messages": final_result.tool_messages or [],
                "runtime_type": "claude_code",
                "error": final_result.error,
                "team_member_count": len(input.agents),
            }
        else:
            return {
                "success": True,
                "response": accumulated_response,
                "response_timestamp": response_timestamp,
                "usage": {},
                "model": input.model_id,
                "finish_reason": "stop",
                "tool_messages": [],
                "runtime_type": "claude_code",
                "team_member_count": len(input.agents),
            }

    async def _execute_claude_code_team_with_native_subagents(
        self, input: Any, session_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Execute Claude Code team using SDK's native subagent support.

        This is the optimal path when:
        - Leader runtime = claude_code
        - All member runtimes = claude_code

        Args:
            input: TeamExecutionInput
            session_history: Previous conversation messages

        Returns:
            Result dict
        """
        execution_id = input.execution_id

        logger.info("using_native_sdk_subagents")

        # STEP 1: Build agents dictionary for SDK
        agents_config = {}
        failed_members = []
        skipped_members = []

        for member in input.agents:
            member_id = member.get('id')
            member_name = member.get('name', 'Unknown')

            if not member_id:
                logger.warning(
                    "member_missing_id_skipped",
                    execution_id=execution_id[:8],
                    member_name=member_name,
                )
                logger.warning("skipping_member_no_id", member_name=member_name)
                skipped_members.append(member_name)
                continue

            # Fetch full member configuration from Control Plane
            try:
                member_full_config = self.control_plane.get_agent(member_id)

                if not member_full_config:
                    logger.warning(
                        "member_config_not_found",
                        execution_id=execution_id[:8],
                        member_id=member_id,
                        member_name=member_name,
                    )
                    logger.warning("member_config_not_found", member_name=member_name, member_id=member_id)
                    failed_members.append(member_name)
                    continue

                # Map skills to tools
                skill_ids = member_full_config.get('skill_ids', [])
                mapped_tools = self._map_skills_to_claude_tools(skill_ids, member_name)

                # Convert to Claude Code agent format
                agents_config[member_id] = {
                    'description': f"{member.get('role', member.get('name'))}. Use for: {member.get('capabilities', '')}",
                    'prompt': member_full_config.get('system_prompt', ''),
                    'tools': mapped_tools,
                    'model': self._map_model_to_sdk_format(member_full_config.get('model_id', 'inherit')),
                }

                logger.info("member_configured", member_name=member_name, model=agents_config[member_id]['model'], tools_count=len(agents_config[member_id]['tools']))

                logger.info(
                    "native_subagent_registered",
                    execution_id=execution_id[:8],
                    member_name=member_name,
                    member_id=member_id,
                    model=agents_config[member_id]['model'],
                    tool_count=len(agents_config[member_id]['tools']),
                    skill_count=len(skill_ids),
                )
            except Exception as e:
                logger.error(
                    "failed_to_load_member_config",
                    execution_id=execution_id[:8],
                    member_id=member_id,
                    member_name=member_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                logger.error("member_load_failed", member_name=member_name, member_id=member_id, error=str(e)[:100])
                failed_members.append(member_name)
                continue

        # Validate that we have at least one configured member
        if not agents_config:
            error_msg = f"No team members could be configured. Failed: {failed_members}, Skipped: {skipped_members}"
            logger.error(
                "no_members_configured_for_native_subagents",
                execution_id=execution_id[:8],
                total_members=len(input.agents),
                failed_count=len(failed_members),
                skipped_count=len(skipped_members),
            )
            logger.error("configuration_error", error=error_msg)
            raise ValueError(error_msg)

        logger.info("native_subagents_configured", count=len(agents_config))
        if failed_members:
            logger.warning('some_members_failed_to_configure', failed_members=failed_members)
            logger.warning(
                "some_members_failed_to_configure",
                execution_id=execution_id[:8],
                failed_members=failed_members,
                configured_count=len(agents_config),
            )
        if skipped_members:
            logger.warning('some_members_skipped_missing_id', skipped_members=skipped_members)
        # Empty print removed

        # STEP 2: Build team leader system prompt
        system_prompt = self._build_team_leader_prompt(input.agents)

        # STEP 3: Get team configuration
        team_config = getattr(input, "team_config", {}) or {}

        # STEP 4: Inject environment variables into MCP servers
        logger.info("fetching_resolved_environment")
        from control_plane_api.worker.activities.runtime_activities import inject_env_vars_into_mcp_servers
        mcp_servers_with_env = inject_env_vars_into_mcp_servers(
            mcp_servers=getattr(input, "mcp_servers", None),
            agent_config=team_config,
            runtime_config=team_config.get("runtime_config"),
            control_plane_client=self.control_plane,
            team_id=input.team_id,
        )

        # AUTO-INCLUDE BUILT-IN MCP SERVERS FOR ALL SUBAGENTS
        # Ensure context-graph-search is available to all team members
        if not mcp_servers_with_env:
            mcp_servers_with_env = {}

        if 'context-graph-search' not in mcp_servers_with_env:
            # Add built-in context-graph-search MCP server
            from control_plane_api.worker.services.skill_factory import SkillFactory
            skill_factory = SkillFactory(runtime_type="claude_code")
            skill_factory.initialize()

            # Create context-graph-search skill config
            builtin_skill_config = {
                'name': 'context_graph_search',
                'type': 'context_graph_search',
                'enabled': True,
                'configuration': {}
            }

            # Create skill and convert to MCP server
            try:
                skills = skill_factory.create_skills_from_list([builtin_skill_config], execution_id=execution_id)
                if skills:
                    # Build MCP servers from skills
                    from control_plane_api.worker.runtimes.claude_code import build_mcp_servers
                    builtin_mcp_servers = build_mcp_servers(skills, execution_id)
                    if builtin_mcp_servers and 'context-graph-search' in builtin_mcp_servers:
                        mcp_servers_with_env['context-graph-search'] = builtin_mcp_servers['context-graph-search']
                        logger.info("builtin_mcp_server_auto_included", server="context-graph-search")
                        logger.info(
                            "context_graph_search_mcp_auto_included",
                            execution_id=execution_id[:8],
                        )
            except Exception as e:
                logger.warning(
                    "failed_to_auto_include_context_graph_search_mcp",
                    execution_id=execution_id[:8],
                    error=str(e),
                )

        # STEP 5: Compile system prompt templates
        logger.info("compiling_system_prompt_templates")
        compiled_system_prompt = system_prompt
        if system_prompt:
            try:
                # Build template context with available variables
                template_context = TemplateContext(
                    variables=getattr(input, "user_metadata", None) or {},
                    secrets=team_config.get("secrets", {}),
                    env_vars=dict(os.environ),  # Make all env vars available
                    # Context graph API configuration for {{.graph.node-id}} templates
                    graph_api_base=os.environ.get("CONTEXT_GRAPH_API_BASE", "https://graph.kubiya.ai"),
                    graph_api_key=os.environ.get("KUBIYA_API_KEY"),
                    graph_org_id=os.environ.get("KUBIYA_ORG_ID") or input.organization_id
                )

                # Resolve templates in system prompt
                compiled_system_prompt = resolve_templates(
                    system_prompt,
                    template_context,
                    strict=False,  # Don't fail on missing variables
                    skip_on_error=True  # Return original if compilation fails
                )

                if compiled_system_prompt != system_prompt:
                    logger.info(
                        "native_team_system_prompt_templates_compiled",
                        original_length=len(system_prompt),
                        compiled_length=len(compiled_system_prompt)
                    )
                    logger.info("system_prompt_templates_compiled")
                else:
                    logger.info("no_templates_in_system_prompt")

            except Exception as e:
                logger.warning(
                    "native_team_system_prompt_template_compilation_failed",
                    error=str(e),
                    exc_info=True
                )
                logger.warning("system_prompt_compilation_failed", error=str(e))
                # Use original system prompt if compilation fails
                compiled_system_prompt = system_prompt

        # STEP 5.5: Enhance system prompt with complete execution environment context
        execution_context_info = self._build_execution_context_info(
            runtime_config=team_config.get("runtime_config", {}),
            skills=[],  # Native subagents path doesn't use leader skills
            mcp_servers=mcp_servers_with_env,
            team_config=team_config
        )
        if execution_context_info:
            if compiled_system_prompt:
                compiled_system_prompt = compiled_system_prompt + "\n\n" + execution_context_info
            else:
                compiled_system_prompt = execution_context_info
            logger.info("system_prompt_enhanced_with_context")

        # STEP 6: Build leader context with agents config
        logger.info("building_execution_context_with_native_subagents")
        context = RuntimeExecutionContext(
            execution_id=execution_id,
            agent_id=input.team_id,
            organization_id=input.organization_id,
            prompt=input.prompt,
            system_prompt=compiled_system_prompt,
            conversation_history=session_history,
            model_id=input.model_id,
            model_config=getattr(input, "model_config", None),
            agent_config={
                **team_config,
                'runtime_config': {
                    'agents': agents_config  # Pass to Claude Code SDK
                }
            },
            skills=[],  # Leader doesn't need extra skills, subagents have their own
            mcp_servers=mcp_servers_with_env,
            user_metadata=getattr(input, "user_metadata", None),
            runtime_config=team_config.get("runtime_config"),
        )
        logger.info("execution_context_ready_with_native_subagents")

        # STEP 6: Create runtime and execute
        runtime = self.runtime_factory.create_runtime(
            runtime_type=RuntimeType.CLAUDE_CODE,
            control_plane_client=self.control_plane,
            cancellation_manager=self.cancellation_manager,
        )

        logger.info("executing_with_native_sdk_subagents")

        # Track turn start time for analytics
        turn_start_time = time.time()
        turn_number = len(session_history) // 2 + 1

        # Create streaming helper for tracking tool messages
        self.streaming_helper = StreamingHelper(
            control_plane_client=self.control_plane, execution_id=input.execution_id
        )

        # Execute - SDK handles subagent routing automatically!
        if runtime.supports_streaming():
            result = await self._execute_streaming(runtime, context, input, self.streaming_helper)
        else:
            exec_result = await runtime.execute(context)
            from datetime import datetime, timezone
            result = {
                "success": exec_result.success,
                "response": exec_result.response,
                "response_timestamp": datetime.now(timezone.utc).isoformat(),
                "usage": exec_result.usage,
                "model": exec_result.model or input.model_id,
                "finish_reason": exec_result.finish_reason or "stop",
                "tool_messages": exec_result.tool_messages or [],
                "runtime_type": "claude_code",
                "error": exec_result.error,
                "team_member_count": len(input.agents),
            }

        # Track turn end time
        turn_end_time = time.time()

        # Submit analytics
        if result.get("success") and result.get("usage"):
            try:
                from runtimes.base import RuntimeExecutionResult
                runtime_result = RuntimeExecutionResult(
                    response=result["response"],
                    usage=result["usage"],
                    success=result["success"],
                    finish_reason=result.get("finish_reason", "stop"),
                    model=result.get("model"),
                    tool_messages=result.get("tool_messages", []),
                    error=result.get("error"),
                )

                await submit_runtime_analytics(
                    result=runtime_result,
                    execution_id=execution_id,
                    turn_number=turn_number,
                    turn_start_time=turn_start_time,
                    turn_end_time=turn_end_time,
                    analytics_service=self.analytics_service,
                )
                logger.info(
                    "native_subagent_team_analytics_submitted",
                    execution_id=execution_id[:8],
                    tokens=result["usage"].get("total_tokens", 0),
                )
            except Exception as analytics_error:
                logger.warning(
                    "native_subagent_team_analytics_failed",
                    execution_id=execution_id[:8],
                    error=str(analytics_error),
                )

        return result

    def _map_skills_to_claude_tools(self, skill_ids: List[str], member_name: str = None) -> List[str]:
        """
        Map skill IDs to Claude Code tool names.

        Args:
            skill_ids: List of skill IDs from agent config
            member_name: Optional member name for logging context

        Returns:
            List of Claude Code tool names
        """
        if not skill_ids:
            logger.info(
                "no_skills_for_member_using_defaults",
                member_name=member_name or "unknown",
                default_tools=['Read', 'Write', 'Bash'],
            )
            return ['Read', 'Write', 'Bash']

        # Fetch skill configurations
        tools = set()
        unmapped_skills = []
        failed_skills = []
        skill_type_counts = {}

        for skill_id in skill_ids:
            try:
                skill_config = self.control_plane.get_skill(skill_id)
                if not skill_config:
                    logger.warning(
                        "skill_config_not_found",
                        skill_id=skill_id,
                        member_name=member_name or "unknown",
                    )
                    failed_skills.append(skill_id)
                    continue

                skill_type = skill_config.get('type', '').lower()
                skill_name = skill_config.get('name', skill_id)

                # Track skill types for analytics
                skill_type_counts[skill_type] = skill_type_counts.get(skill_type, 0) + 1

                # Map skill types to Claude Code tool names
                mapped = True
                if skill_type in ['file_system', 'filesystem', 'file']:
                    tools.update(['Read', 'Write', 'Edit', 'Glob'])
                elif skill_type in ['shell', 'bash', 'command']:
                    tools.add('Bash')
                elif skill_type in ['web', 'http', 'api']:
                    tools.update(['WebFetch', 'WebSearch'])
                elif skill_type in ['data_visualization', 'visualization', 'plotting']:
                    tools.update(['Read', 'Write'])  # Needs read for data access, write for output
                elif skill_type in ['python', 'code', 'scripting']:
                    tools.add('Bash')  # Python via bash
                elif skill_type in ['grep', 'search', 'find']:
                    tools.update(['Grep', 'Glob'])
                elif skill_type in ['task', 'workflow', 'delegation']:
                    tools.add('Task')
                elif skill_type in ['planning', 'todo']:
                    tools.update(['TodoWrite', 'Task'])
                elif skill_type in ['notebook', 'jupyter']:
                    tools.update(['Read', 'Write', 'NotebookEdit'])
                elif skill_type in ['docker', 'container']:
                    tools.add('Bash')  # Docker commands via bash
                elif skill_type in ['git', 'version_control']:
                    tools.add('Bash')  # Git commands via bash
                elif skill_type in ['database', 'sql']:
                    tools.add('Bash')  # SQL commands via bash
                else:
                    # Unknown skill type - log it for future mapping
                    mapped = False
                    unmapped_skills.append((skill_name, skill_type))
                    logger.info(
                        "unmapped_skill_type_encountered",
                        skill_id=skill_id,
                        skill_name=skill_name,
                        skill_type=skill_type,
                        member_name=member_name or "unknown",
                        note="Consider adding mapping for this skill type",
                    )

                if mapped:
                    logger.debug(
                        "skill_mapped_successfully",
                        skill_id=skill_id,
                        skill_name=skill_name,
                        skill_type=skill_type,
                        member_name=member_name or "unknown",
                    )

            except Exception as e:
                logger.warning(
                    "failed_to_map_skill",
                    skill_id=skill_id,
                    member_name=member_name or "unknown",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                failed_skills.append(skill_id)
                continue

        # If no tools mapped, provide basic defaults
        if not tools:
            logger.warning(
                "no_tools_mapped_using_defaults",
                member_name=member_name or "unknown",
                total_skills=len(skill_ids),
                unmapped_count=len(unmapped_skills),
                failed_count=len(failed_skills),
                default_tools=['Read', 'Write', 'Bash'],
            )
            tools = {'Read', 'Write', 'Bash'}

        # Log mapping summary
        logger.info(
            "skill_mapping_completed",
            member_name=member_name or "unknown",
            total_skills=len(skill_ids),
            mapped_tools=list(tools),
            tool_count=len(tools),
            skill_types=skill_type_counts,
            unmapped_count=len(unmapped_skills),
            failed_count=len(failed_skills),
        )

        if unmapped_skills:
            logger.info(
                "unmapped_skills_summary",
                member_name=member_name or "unknown",
                unmapped_skills=[f"{name} ({stype})" for name, stype in unmapped_skills],
            )

        return list(tools)

    def _map_model_to_sdk_format(self, model_id: str) -> str:
        """
        Map model ID to SDK format (sonnet/opus/haiku/inherit).

        Args:
            model_id: Full model ID (e.g., "kubiya/claude-sonnet-4")

        Returns:
            SDK model format string
        """
        if not model_id or model_id == 'inherit':
            return 'inherit'

        model_lower = model_id.lower()

        if 'sonnet' in model_lower:
            return 'sonnet'
        elif 'opus' in model_lower:
            return 'opus'
        elif 'haiku' in model_lower:
            return 'haiku'

        # Default to inherit (use leader's model)
        return 'inherit'

    def _build_team_leader_prompt(self, agents: List[Dict]) -> str:
        """
        Build system prompt for team leader with native subagents.

        Args:
            agents: List of agent configurations

        Returns:
            Formatted system prompt
        """
        member_descriptions = []

        for agent in agents:
            name = agent.get('name', 'Agent')
            role = agent.get('role', 'Team member')
            agent_id = agent.get('id', 'unknown')
            member_descriptions.append(
                f"- **{name}** (ID: {agent_id}): {role}"
            )

        return f"""You are the team leader coordinating a team of specialized AI agents.

Your team members:
{chr(10).join(member_descriptions)}

Claude will automatically invoke the appropriate team member based on the task.
Each member has their own:
- Specialized system prompt and expertise
- Dedicated tools and capabilities
- Separate context (won't see each other's work)
- Own model configuration

Coordinate effectively to solve the user's request. The SDK will handle routing tasks to the right team member.
"""

    def _all_members_are_claude_code(self, agents: List[Dict]) -> bool:
        """
        Check if all team members use Claude Code runtime.

        Optimized to batch-fetch agent configs to avoid N+1 queries.

        Args:
            agents: List of agent configurations

        Returns:
            True if all members are Claude Code runtime
        """
        if not agents:
            logger.warning("no_agents_to_check_runtime")
            return False

        agent_ids = [agent.get('id') for agent in agents if agent.get('id')]

        if len(agent_ids) != len(agents):
            logger.warning(
                "some_agents_missing_ids_in_runtime_check",
                total_agents=len(agents),
                agents_with_ids=len(agent_ids),
            )
            # If some agents don't have IDs, we can't verify them
            return False

        # Batch fetch all agent configs to avoid N+1 queries
        agent_configs = {}
        failed_fetches = []

        logger.info(
            "batch_fetching_agent_configs_for_runtime_check",
            agent_count=len(agent_ids),
            agent_ids=agent_ids,
        )

        # Try to fetch all agent configs
        for agent_id in agent_ids:
            try:
                agent_config = self.control_plane.get_agent(agent_id)
                if agent_config:
                    agent_configs[agent_id] = agent_config
                else:
                    logger.warning(
                        "agent_config_not_found_in_runtime_check",
                        agent_id=agent_id,
                    )
                    failed_fetches.append(agent_id)
            except Exception as e:
                logger.warning(
                    "failed_to_fetch_agent_config_in_runtime_check",
                    agent_id=agent_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                failed_fetches.append(agent_id)

        # If we couldn't fetch all configs, we can't verify runtime consistency
        if failed_fetches:
            logger.warning(
                "cannot_verify_all_agent_runtimes",
                failed_fetches=failed_fetches,
                fetched_count=len(agent_configs),
                total_count=len(agent_ids),
            )
            return False

        # Check if all fetched agents use claude_code runtime
        non_claude_code_agents = []
        runtime_distribution = {}

        for agent_id, config in agent_configs.items():
            runtime = config.get('runtime', 'default')
            runtime_distribution[runtime] = runtime_distribution.get(runtime, 0) + 1

            if runtime != 'claude_code':
                agent_name = next(
                    (a.get('name', agent_id) for a in agents if a.get('id') == agent_id),
                    agent_id
                )
                non_claude_code_agents.append({
                    'id': agent_id,
                    'name': agent_name,
                    'runtime': runtime,
                })

        # Log runtime distribution for observability
        logger.info(
            "team_member_runtime_distribution",
            total_members=len(agent_configs),
            runtime_distribution=runtime_distribution,
            all_claude_code=len(non_claude_code_agents) == 0,
        )

        if non_claude_code_agents:
            logger.info(
                "mixed_runtime_team_detected",
                claude_code_count=runtime_distribution.get('claude_code', 0),
                non_claude_code_count=len(non_claude_code_agents),
                non_claude_code_agents=[
                    f"{a['name']} ({a['runtime']})" for a in non_claude_code_agents
                ],
                decision="will_use_task_tool_delegation",
            )
            return False

        logger.info(
            "all_members_are_claude_code",
            member_count=len(agent_configs),
            decision="will_use_native_subagents",
        )
        return True

    def _build_team_context(self, agents: List[Dict]) -> str:
        """
        Build team context description for system prompt.

        Args:
            agents: List of agent configurations

        Returns:
            Formatted team context string
        """
        context_lines = []
        for i, agent in enumerate(agents, 1):
            name = agent.get("name", f"Agent {i}")
            role = agent.get("role", "No role specified")
            agent_id = agent.get("id", "unknown")

            context_lines.append(
                f"{i}. **{name}** (ID: {agent_id})\n"
                f"   Role: {role}\n"
            )

        return "\n".join(context_lines)

    def _build_execution_context_info(
        self,
        runtime_config: Dict[str, Any],
        skills: List[Any],
        mcp_servers: Optional[Dict[str, Any]],
        team_config: Dict[str, Any]
    ) -> str:
        """
        Build comprehensive execution environment context for system prompt.

        This provides the team with awareness of:
        - Available environment variables (secrets, integrations, config)
        - Available skills/tools
        - MCP servers
        - Runtime configuration

        Args:
            runtime_config: Runtime configuration with env vars
            skills: List of available skills
            mcp_servers: Dictionary of MCP server configurations
            team_config: Team configuration

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
