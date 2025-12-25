"""Team executor service - handles team execution business logic"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import structlog
import asyncio
import os
from temporalio import activity

from agno.agent import Agent
from agno.team import Team
from agno.models.litellm import LiteLLM

from control_plane_api.worker.control_plane_client import ControlPlaneClient
from control_plane_api.worker.services.session_service import SessionService
from control_plane_api.worker.services.cancellation_manager import CancellationManager
from control_plane_api.worker.services.skill_factory import SkillFactory
from control_plane_api.worker.utils.streaming_utils import StreamingHelper
from control_plane_api.worker.utils.parameter_validator import (
    validate_tool_parameters,
    ParameterValidationError,
)

logger = structlog.get_logger()


class TeamExecutorService:
    """
    Service for executing teams with full session management and cancellation support.

    This service orchestrates:
    - Session loading and restoration
    - Team and member agent creation with LiteLLM configuration
    - Skill instantiation for team members
    - Streaming execution with real-time updates
    - Session persistence
    - Cancellation support via CancellationManager
    """

    def __init__(
        self,
        control_plane: ControlPlaneClient,
        session_service: SessionService,
        cancellation_manager: CancellationManager
    ):
        self.control_plane = control_plane
        self.session_service = session_service
        self.cancellation_manager = cancellation_manager

    async def execute(self, input: Any) -> Dict[str, Any]:
        """
        Execute a team with full session management and streaming.

        Args:
            input: TeamExecutionInput with execution details

        Returns:
            Dict with response, usage, success flag, etc.
        """
        execution_id = input.execution_id

        logger.info(
            "team_workflow_start",
            execution_id=execution_id[:8],
            team_id=input.team_id,
            session_id=input.session_id,
            agent_count=len(input.agents)
        )

        try:
            # STEP 1: Load session history
            session_history = self.session_service.load_session(
                execution_id=execution_id,
                session_id=input.session_id
            )

            if session_history:
                print(f"✅ Loaded {len(session_history)} messages from previous session\n")
            else:
                print("ℹ️  Starting new conversation\n")

            # STEP 2: Build conversation context for Agno
            conversation_context = self.session_service.build_conversation_context(session_history)

            # STEP 3: Get LiteLLM configuration
            litellm_api_base = os.getenv("LITELLM_API_BASE", "https://llm-proxy.kubiya.ai")
            litellm_api_key = os.getenv("LITELLM_API_KEY")

            if not litellm_api_key:
                raise ValueError("LITELLM_API_KEY environment variable not set")

            model = input.model_id or os.environ.get("LITELLM_DEFAULT_MODEL", "kubiya/claude-sonnet-4")

            # STEP 4: Create member agents with skills
            print(f"👥 Creating {len(input.agents)} member agents...\n")

            team_members = []
            for agent_data in input.agents:
                agent_id = agent_data.get("id")
                agent_name = agent_data.get("name", f"Agent {agent_id}")
                agent_role = agent_data.get("role", "You are a helpful AI assistant")

                print(f"   🤖 Creating Agent: {agent_name}")
                print(f"      ID: {agent_id}")
                print(f"      Role: {agent_role[:80]}...")

                # Fetch skills for this agent
                skills = []
                if agent_id:
                    try:
                        skill_configs = self.control_plane.get_skills(agent_id)

                        # AUTO-INCLUDE BUILT-IN SKILLS
                        if not skill_configs:
                            skill_configs = []

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
                                print(f"      ➕ Auto-included built-in skill: {builtin_type}")

                        if skill_configs:
                            print(f"      Skills: {len(skill_configs)}")
                            # Create SkillFactory instance for agno runtime
                            skill_factory = SkillFactory(runtime_type="agno")
                            skill_factory.initialize()
                            skills = skill_factory.create_skills_from_list(skill_configs, execution_id=execution_id)
                            if skills:
                                print(f"      ✅ Instantiated {len(skills)} skill(s)")
                    except Exception as e:
                        print(f"      ⚠️  Failed to fetch skills: {str(e)}")
                        logger.warning("skill_fetch_error_for_team_member", agent_id=agent_id, error=str(e))

                # Create Agno Agent
                member_agent = Agent(
                    name=agent_name,
                    role=agent_role,
                    model=LiteLLM(
                        id=f"openai/{model}",
                        api_base=litellm_api_base,
                        api_key=litellm_api_key,
                    ),
                    tools=skills if skills else None,
                )

                team_members.append(member_agent)
                print(f"      ✅ Agent created\n")

            if not team_members:
                raise ValueError("No team members available for team execution")

            # STEP 5: Create Agno Team with streaming helper
            print(f"\n🚀 Creating Agno Team:")
            print(f"   Team ID: {input.team_id}")
            print(f"   Members: {len(team_members)}")
            print(f"   Model: {model}")

            # Create streaming helper for this execution
            streaming_helper = StreamingHelper(
                control_plane_client=self.control_plane,
                execution_id=execution_id
            )

            # Create tool hook for real-time updates
            def tool_hook(name: str = None, function_name: str = None, function=None, arguments: dict = None, **kwargs):
                """Hook to capture tool execution for real-time streaming"""
                tool_name = name or function_name or "unknown"
                tool_args = arguments or {}

                # Generate unique tool execution ID
                import time
                tool_execution_id = f"{tool_name}_{int(time.time() * 1000000)}"

                print(f"   🔧 Tool Starting: {tool_name} (ID: {tool_execution_id})")

                # Publish tool start event
                streaming_helper.publish_tool_start(
                    tool_name=tool_name,
                    tool_execution_id=tool_execution_id,
                    tool_args=tool_args,
                    source="team"
                )

                # Execute the tool
                result = None
                error = None
                try:
                    if function and callable(function):
                        # Validate parameters before execution to catch mismatches early
                        try:
                            validate_tool_parameters(
                                function,
                                tool_args,
                                tool_name,
                                execution_id
                            )
                        except ParameterValidationError as ve:
                            # Log detailed error and fail fast
                            logger.error(
                                "tool_parameter_mismatch_detected",
                                tool_name=tool_name,
                                execution_id=execution_id,
                                validation_error=str(ve),
                            )
                            raise

                        result = function(**tool_args) if tool_args else function()
                    else:
                        raise ValueError(f"Function not callable: {function}")

                    status = "success"
                    print(f"   ✅ Tool Success: {tool_name}")

                except Exception as e:
                    error = e
                    status = "failed"
                    print(f"   ❌ Tool Failed: {tool_name} - {str(e)}")

                # Publish tool completion event
                streaming_helper.publish_tool_complete(
                    tool_name=tool_name,
                    tool_execution_id=tool_execution_id,
                    status=status,
                    output=str(result)[:1000] if result else None,
                    error=str(error) if error else None,
                    source="team"
                )

                if error:
                    raise error

                return result

            # Add tool hooks to all team members
            for member in team_members:
                if not hasattr(member, 'tool_hooks') or member.tool_hooks is None:
                    member.tool_hooks = []
                member.tool_hooks.append(tool_hook)

            # Create Agno Team
            team = Team(
                name=f"Team {input.team_id}",
                members=team_members,
                model=LiteLLM(
                    id=f"openai/{model}",
                    api_base=litellm_api_base,
                    api_key=litellm_api_key,
                ),
            )

            # STEP 6: Register for cancellation
            self.cancellation_manager.register(
                execution_id=execution_id,
                instance=team,
                instance_type="team"
            )
            print(f"✅ Team registered for cancellation support\n")

            # Cache execution metadata in Redis
            self.control_plane.cache_metadata(execution_id, "TEAM")

            # STEP 7: Execute with streaming
            print("⚡ Executing Team Run with Streaming...\n")

            # Generate deterministic message IDs for this turn (matches V2 executor pattern)
            # This ensures streaming and persisted messages have the SAME message_id
            turn_number = len(session_history) // 2 + 1
            user_message_id = f"{execution_id}_user_{turn_number}"
            message_id = f"{execution_id}_assistant_{turn_number}"

            # Publish user message to stream immediately so it appears in chronological order
            from datetime import datetime, timezone
            user_message_timestamp = datetime.now(timezone.utc).isoformat()
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
            print(f"   📤 Published user message to stream (ID: {user_message_id})")

            def stream_team_run():
                """Run team with streaming and collect response"""
                # Create event loop for this thread (needed for async streaming)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def _async_stream():
                    """Async wrapper for streaming execution"""
                    import time as time_module
                    last_heartbeat_time = time_module.time()
                    last_persistence_time = time_module.time()
                    heartbeat_interval = 10  # Send heartbeat every 10 seconds
                    persistence_interval = 60  # Persist to database every 60 seconds

                    # Track tool_execution_ids for proper start/complete matching
                    # Key: "{member_name or 'leader'}_{tool_name}", Value: tool_execution_id
                    active_tool_executions: Dict[str, str] = {}

                    try:
                        # Execute with conversation context
                        if conversation_context:
                            run_response = team.run(
                                input.prompt,
                                stream=True,
                                messages=conversation_context,
                            )
                        else:
                            run_response = team.run(input.prompt, stream=True)

                        # Process streaming events (sync iteration in async context)
                        for event in run_response:
                            # Periodic maintenance: heartbeats and persistence
                            current_time = time_module.time()

                            # Send heartbeat every 10s (Temporal liveness)
                            if current_time - last_heartbeat_time >= heartbeat_interval:
                                current_response = streaming_helper.get_full_response()
                                activity.heartbeat({
                                    "status": "Streaming in progress...",
                                    "response_length": len(current_response),
                                    "execution_id": execution_id,
                                })
                                last_heartbeat_time = current_time

                            # Persist snapshot every 60s (resilience against crashes)
                            if current_time - last_persistence_time >= persistence_interval:
                                current_response = streaming_helper.get_full_response()
                                if current_response:
                                    print(f"\n💾 Periodic persistence ({len(current_response)} chars)...")
                                    snapshot_messages = session_history + [{
                                        "role": "assistant",
                                        "content": current_response,
                                        "timestamp": datetime.now(timezone.utc).isoformat(),
                                        "message_id": message_id,  # Include deterministic message_id
                                    }]
                                    try:
                                        # Best effort - don't fail execution if persistence fails
                                        self.session_service.persist_session(
                                            execution_id=execution_id,
                                            session_id=input.session_id or execution_id,
                                            user_id=input.user_id,
                                            messages=snapshot_messages,
                                            metadata={
                                                "team_id": input.team_id,
                                                "organization_id": input.organization_id,
                                                "snapshot": True,
                                            }
                                        )
                                        print(f"   ✅ Session snapshot persisted with message_id: {message_id}")
                                    except Exception as e:
                                        print(f"   ⚠️  Session persistence error: {str(e)} (non-fatal)")
                                last_persistence_time = current_time

                            # Handle run_id capture
                            streaming_helper.handle_run_id(
                                chunk=event,
                                on_run_id=lambda run_id: self.cancellation_manager.set_run_id(execution_id, run_id)
                            )

                            # Get event type
                            event_type = getattr(event, 'event', None)

                            # Handle TEAM LEADER content chunks
                            if event_type == "TeamRunContent":
                                await streaming_helper.handle_content_chunk(
                                    chunk=event,
                                    message_id=message_id,
                                    print_to_console=True
                                )

                            # Handle MEMBER content chunks (from team members)
                            elif event_type == "RunContent":
                                # Member agent content chunk
                                member_name = getattr(event, 'agent_name', getattr(event, 'member_name', 'Team Member'))

                                if hasattr(event, 'content') and event.content:
                                    content = str(event.content)
                                    streaming_helper.handle_member_content_chunk(
                                        member_name=member_name,
                                        content=content,
                                        print_to_console=True
                                    )

                            # Handle TEAM LEADER tool calls
                            elif event_type == "TeamToolCallStarted":
                                # Extract tool name properly
                                tool_obj = getattr(event, 'tool', None)
                                if tool_obj and hasattr(tool_obj, 'tool_name'):
                                    tool_name = tool_obj.tool_name
                                    tool_args = getattr(tool_obj, 'tool_args', {})
                                else:
                                    tool_name = str(tool_obj) if tool_obj else getattr(event, 'tool_name', 'unknown')
                                    tool_args = {}

                                import time
                                tool_execution_id = f"{tool_name}_{int(time.time() * 1000000)}"

                                # Store tool_execution_id for matching with completion event
                                tool_key = f"leader_{tool_name}"
                                active_tool_executions[tool_key] = tool_execution_id

                                print(f"\n   🔧 Tool Starting: {tool_name} (Team Leader) [ID: {tool_execution_id}]")
                                streaming_helper.publish_tool_start(
                                    tool_name=tool_name,
                                    tool_execution_id=tool_execution_id,
                                    tool_args=tool_args,
                                    source="team_leader",
                                    member_name=None
                                )

                            elif event_type == "TeamToolCallCompleted":
                                # Extract tool name and output
                                tool_obj = getattr(event, 'tool', None)
                                if tool_obj and hasattr(tool_obj, 'tool_name'):
                                    tool_name = tool_obj.tool_name
                                    tool_output = getattr(tool_obj, 'result', None) or getattr(event, 'result', None)
                                else:
                                    tool_name = str(tool_obj) if tool_obj else getattr(event, 'tool_name', 'unknown')
                                    tool_output = getattr(event, 'result', None)

                                # Retrieve stored tool_execution_id for matching
                                tool_key = f"leader_{tool_name}"
                                tool_execution_id = active_tool_executions.get(tool_key)

                                if not tool_execution_id:
                                    # Fallback: generate new ID if not found (shouldn't happen)
                                    import time
                                    tool_execution_id = f"{tool_name}_{int(time.time() * 1000000)}"
                                    print(f"\n   ⚠️  Tool completion without matching start event: {tool_name}")
                                else:
                                    # Remove from tracking dict
                                    del active_tool_executions[tool_key]

                                print(f"\n   ✅ Tool Completed: {tool_name} (Team Leader) [ID: {tool_execution_id}]")
                                streaming_helper.publish_tool_complete(
                                    tool_name=tool_name,
                                    tool_execution_id=tool_execution_id,
                                    status="success",
                                    output=str(tool_output) if tool_output else None,
                                    error=None,
                                    source="team_leader",
                                    member_name=None
                                )

                            # Handle MEMBER tool calls
                            elif event_type == "ToolCallStarted":
                                # Extract tool name properly
                                tool_obj = getattr(event, 'tool', None)
                                if tool_obj and hasattr(tool_obj, 'tool_name'):
                                    tool_name = tool_obj.tool_name
                                    tool_args = getattr(tool_obj, 'tool_args', {})
                                else:
                                    tool_name = str(tool_obj) if tool_obj else getattr(event, 'tool_name', 'unknown')
                                    tool_args = {}

                                member_name = getattr(event, 'agent_name', getattr(event, 'member_name', 'Team Member'))

                                import time
                                tool_execution_id = f"{tool_name}_{int(time.time() * 1000000)}"

                                # Store tool_execution_id for matching with completion event
                                tool_key = f"{member_name}_{tool_name}"
                                active_tool_executions[tool_key] = tool_execution_id

                                print(f"\n   🔧 Tool Starting: {tool_name} ({member_name}) [ID: {tool_execution_id}]")
                                streaming_helper.publish_tool_start(
                                    tool_name=tool_name,
                                    tool_execution_id=tool_execution_id,
                                    tool_args=tool_args,
                                    source="team_member",
                                    member_name=member_name
                                )

                            elif event_type == "ToolCallCompleted":
                                # Extract tool name and output
                                tool_obj = getattr(event, 'tool', None)
                                if tool_obj and hasattr(tool_obj, 'tool_name'):
                                    tool_name = tool_obj.tool_name
                                    tool_output = getattr(tool_obj, 'result', None) or getattr(event, 'result', None)
                                else:
                                    tool_name = str(tool_obj) if tool_obj else getattr(event, 'tool_name', 'unknown')
                                    tool_output = getattr(event, 'result', None)

                                member_name = getattr(event, 'agent_name', getattr(event, 'member_name', 'Team Member'))

                                # Retrieve stored tool_execution_id for matching
                                tool_key = f"{member_name}_{tool_name}"
                                tool_execution_id = active_tool_executions.get(tool_key)

                                if not tool_execution_id:
                                    # Fallback: generate new ID if not found (shouldn't happen)
                                    import time
                                    tool_execution_id = f"{tool_name}_{int(time.time() * 1000000)}"
                                    print(f"\n   ⚠️  Tool completion without matching start event: {tool_name} ({member_name})")
                                else:
                                    # Remove from tracking dict
                                    del active_tool_executions[tool_key]

                                print(f"\n   ✅ Tool Completed: {tool_name} ({member_name}) [ID: {tool_execution_id}]")
                                streaming_helper.publish_tool_complete(
                                    tool_name=tool_name,
                                    tool_execution_id=tool_execution_id,
                                    status="success",
                                    output=str(tool_output) if tool_output else None,
                                    error=None,
                                    source="team_member",
                                    member_name=member_name
                                )

                        # Finalize streaming (mark any active member as complete)
                        streaming_helper.finalize_streaming()

                        print()  # New line after streaming
                        return run_response

                    except Exception as e:
                        print(f"\n❌ Streaming error: {str(e)}")
                        # Fall back to non-streaming
                        if conversation_context:
                            return team.run(input.prompt, stream=False, messages=conversation_context)
                        else:
                            return team.run(input.prompt, stream=False)

                # Run the async function in the event loop
                try:
                    return loop.run_until_complete(_async_stream())
                finally:
                    loop.close()

            # Execute in thread pool (no timeout - user controls via STOP button)
            # Wrap in try-except to handle Temporal cancellation
            try:
                result = await asyncio.to_thread(stream_team_run)
            except asyncio.CancelledError:
                # Temporal cancelled the activity - cancel the running team
                print("\n🛑 Cancellation signal received - stopping team execution...")
                cancel_result = self.cancellation_manager.cancel(execution_id)
                if cancel_result["success"]:
                    print(f"✅ Team execution cancelled successfully")
                else:
                    print(f"⚠️  Cancellation completed with warning: {cancel_result.get('error', 'Unknown')}")
                # Re-raise to let Temporal know we're cancelled
                raise

            print("✅ Team Execution Completed!")
            full_response = streaming_helper.get_full_response()
            print(f"   Response Length: {len(full_response)} chars\n")

            logger.info(
                "team_execution_completed",
                execution_id=execution_id[:8],
                response_length=len(full_response)
            )

            # Use the streamed response content
            response_content = full_response if full_response else (result.content if hasattr(result, "content") else str(result))

            # STEP 8: Extract usage metrics
            usage = {}
            if hasattr(result, "metrics") and result.metrics:
                metrics = result.metrics
                usage = {
                    "prompt_tokens": getattr(metrics, "input_tokens", 0),
                    "completion_tokens": getattr(metrics, "output_tokens", 0),
                    "total_tokens": getattr(metrics, "total_tokens", 0),
                }
                print(f"📊 Token Usage:")
                print(f"   Input: {usage.get('prompt_tokens', 0)}")
                print(f"   Output: {usage.get('completion_tokens', 0)}")
                print(f"   Total: {usage.get('total_tokens', 0)}\n")

            # STEP 9: Persist complete session history
            print("\n💾 Persisting session history to Control Plane...")

            # Build message_ids dict to pass to extract_messages_from_result
            # This ensures persisted messages use the SAME IDs as streaming messages
            message_ids_map = {
                len(session_history): user_message_id,      # User message index
                len(session_history) + 1: message_id         # Assistant message index
            }

            # Extract messages from Agno result to get accurate timestamps
            # Agno tracks message timestamps as they're created (msg.created_at)
            extracted_messages = self.session_service.extract_messages_from_result(
                result=result,
                user_id=input.user_id,
                execution_id=execution_id,
                message_ids=message_ids_map  # Pass deterministic IDs
            )
            print(f"   📊 Extracted {len(extracted_messages)} messages with deterministic IDs")

            #  Use extracted messages which have proper timestamps from Agno
            # These include both user and assistant messages with accurate created_at times
            new_messages = extracted_messages

            # Fallback: if no messages extracted (shouldn't happen), create them manually
            if not extracted_messages:
                from datetime import datetime, timezone
                current_timestamp = datetime.now(timezone.utc).isoformat()
                print("   ⚠️  No messages extracted from Agno result, creating manually")
                new_messages = [
                    {
                        "role": "user",
                        "content": input.prompt,
                        "timestamp": current_timestamp,
                        "message_id": f"{execution_id}_user_{turn_number}",
                        "user_id": input.user_id,
                        "user_name": getattr(input, "user_name", None),
                        "user_email": getattr(input, "user_email", None),
                    },
                    {
                        "role": "assistant",
                        "content": response_content,
                        "timestamp": current_timestamp,
                        "message_id": message_id,  # Use the same message_id as streaming
                    },
                ]

            # Extract tool messages from streaming helper
            tool_messages = streaming_helper.get_tool_messages()
            print(f"   📊 Collected {len(tool_messages)} tool messages during streaming")

            # Combine with previous history: session_history + new_messages + tool_messages
            complete_session = session_history + new_messages + tool_messages

            # CRITICAL: Deduplicate messages by message_id AND content to prevent duplicates
            # Use session_service.deduplicate_messages() which has enhanced two-level deduplication
            original_count = len(complete_session)
            complete_session = self.session_service.deduplicate_messages(complete_session)

            # CRITICAL: Sort by timestamp to ensure chronological order
            # Tool messages happen DURING streaming, so they need to be interleaved with user/assistant messages
            complete_session.sort(key=lambda msg: msg.get("timestamp", ""))
            print(f"   ✅ Messages deduplicated ({original_count} -> {len(complete_session)}) and sorted by timestamp")

            if complete_session:
                success = self.session_service.persist_session(
                    execution_id=execution_id,
                    session_id=input.session_id or execution_id,
                    user_id=input.user_id,
                    messages=complete_session,
                    metadata={
                        "team_id": input.team_id,
                        "organization_id": input.organization_id,
                        "turn_count": len(complete_session),
                        "member_count": len(team_members),
                    }
                )

                if success:
                    print(f"   ✅ Session persisted ({len(complete_session)} total messages)")
                else:
                    print(f"   ⚠️  Session persistence failed")
            else:
                print("   ℹ️  No messages to persist")

            print("\n" + "="*80)
            print("🏁 TEAM EXECUTION END")
            print("="*80 + "\n")

            # STEP 10: Cleanup
            self.cancellation_manager.unregister(execution_id)

            from datetime import datetime, timezone
            return {
                "success": True,
                "response": response_content,
                "response_timestamp": datetime.now(timezone.utc).isoformat(),
                "usage": usage,
                "model": model,
                "finish_reason": "stop",
                "team_member_count": len(team_members),
            }

        except Exception as e:
            # Cleanup on error
            self.cancellation_manager.unregister(execution_id)

            print("\n" + "="*80)
            print("❌ TEAM EXECUTION FAILED")
            print("="*80)
            print(f"Error: {str(e)}")
            print("="*80 + "\n")

            logger.error(
                "team_execution_failed",
                execution_id=execution_id[:8],
                error=str(e)
            )

            return {
                "success": False,
                "error": str(e),
                "model": input.model_id,
                "usage": None,
                "finish_reason": "error",
            }
