"""Agent execution workflow for Temporal"""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional, List, Dict, Any
from temporalio import workflow
from temporalio.common import RetryPolicy
import asyncio
import os

with workflow.unsafe.imports_passed_through():
    from control_plane_api.worker.activities.agent_activities import (
        execute_agent_llm,
        update_execution_status,
        get_execution_details,
        update_agent_status,
        persist_conversation_history,
        submit_runtime_analytics_activity,
        ActivityExecuteAgentInput,
        ActivityUpdateExecutionInput,
        ActivityGetExecutionInput,
        ActivityUpdateAgentInput,
        ActivityPersistConversationInput,
        AnalyticsActivityInput,
    )
    from control_plane_api.worker.activities.runtime_activities import (
        execute_with_runtime,
        publish_user_message,
        ActivityRuntimeExecuteInput,
        PublishUserMessageInput,
    )
    from control_plane_api.worker.utils.logging_helper import execution_logger


# Default 10 minutes for long-running tasks (Claude Code and Agno can take very long time)
HEARTBEAT_TIMEOUT_SECONDS = int(os.environ.get("ACTIVITY_HEARTBEAT_TIMEOUT_SECONDS", "600"))


@dataclass
class AgentExecutionInput:
    """Input for agent execution workflow"""
    # Required fields (no defaults)
    agent_id: str
    organization_id: str
    prompt: str
    # Optional fields (with defaults)
    execution_id: Optional[str] = None  # Optional for backward compatibility with old schedules
    system_prompt: Optional[str] = None
    model_id: Optional[str] = None
    model_config: dict = None
    agent_config: dict = None
    mcp_servers: dict = None  # MCP servers configuration
    user_metadata: dict = None
    runtime_type: str = "default"  # "default" (Agno) or "claude_code"
    initial_message_timestamp: Optional[str] = None  # Real-time timestamp for initial message

    def __post_init__(self):
        if self.model_config is None:
            self.model_config = {}
        if self.agent_config is None:
            self.agent_config = {}
        if self.mcp_servers is None:
            self.mcp_servers = {}
        if self.user_metadata is None:
            self.user_metadata = {}


@dataclass
class TeamExecutionInput:
    """Input for team execution workflow (uses same workflow as agent)"""
    # Required fields (no defaults)
    team_id: str
    organization_id: str
    prompt: str
    # Optional fields (with defaults)
    execution_id: Optional[str] = None  # Optional for backward compatibility with old schedules
    system_prompt: Optional[str] = None
    model_id: Optional[str] = None
    model_config: dict = None
    team_config: dict = None
    mcp_servers: dict = None  # MCP servers configuration
    user_metadata: dict = None
    runtime_type: str = "default"  # "default" (Agno) or "claude_code"
    initial_message_timestamp: Optional[str] = None  # Real-time timestamp for initial message

    def __post_init__(self):
        if self.model_config is None:
            self.model_config = {}
        if self.team_config is None:
            self.team_config = {}
        if self.mcp_servers is None:
            self.mcp_servers = {}
        if self.user_metadata is None:
            self.user_metadata = {}

    def to_agent_input(self) -> AgentExecutionInput:
        """Convert TeamExecutionInput to AgentExecutionInput for workflow reuse"""
        return AgentExecutionInput(
            execution_id=self.execution_id,
            agent_id=self.team_id,  # Use team_id as agent_id
            organization_id=self.organization_id,
            prompt=self.prompt,
            system_prompt=self.system_prompt,
            model_id=self.model_id,
            model_config=self.model_config,
            agent_config=self.team_config,
            mcp_servers=self.mcp_servers,
            user_metadata=self.user_metadata,
            runtime_type=self.runtime_type,
            initial_message_timestamp=self.initial_message_timestamp,
        )


@dataclass
class ChatMessage:
    """Represents a message in the conversation"""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    message_id: Optional[str] = None  # Unique identifier for deduplication
    user_id: Optional[str] = None  # User who sent the message
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None


@dataclass
class ExecutionState:
    """Current state of the execution for queries"""
    status: str  # "pending", "running", "waiting_for_input", "completed", "failed"
    messages: List[ChatMessage] = field(default_factory=list)
    current_response: str = ""
    error_message: Optional[str] = None
    usage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_waiting_for_input: bool = False
    should_complete: bool = False


@workflow.defn
class AgentExecutionWorkflow:
    """
    Workflow for executing an agent with LLM with Temporal message passing support.

    This workflow:
    1. Updates execution status to running
    2. Executes the agent's LLM call
    3. Updates execution with results
    4. Updates agent status
    5. Supports queries for real-time state access
    6. Supports signals for adding followup messages
    """

    def __init__(self) -> None:
        """Initialize workflow state"""
        self._state = ExecutionState(status="pending")
        self._lock = asyncio.Lock()
        self._new_message_count = 0
        self._processed_message_count = 0

    def _messages_to_dict(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """
        Convert ChatMessage objects to dict format for persistence.

        This ensures the conversation history is in a clean, serializable format
        that can be stored in the database and retrieved later.

        Args:
            messages: List of ChatMessage objects from workflow state

        Returns:
            List of message dicts ready for persistence
        """
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "tool_name": msg.tool_name,
                "tool_input": msg.tool_input,
                "tool_output": msg.tool_output,
                "tool_execution_id": getattr(msg, "tool_execution_id", None),  # CRITICAL: For tool message deduplication
                "message_id": getattr(msg, "message_id", None),  # CRITICAL: For message deduplication
                "user_id": getattr(msg, "user_id", None),
                "user_name": getattr(msg, "user_name", None),
                "user_email": getattr(msg, "user_email", None),
                "user_avatar": getattr(msg, "user_avatar", None),
            }
            for msg in messages
        ]

    @workflow.query
    def get_state(self) -> ExecutionState:
        """Query handler: Get current execution state including messages and status"""
        return self._state

    @workflow.signal
    async def add_message(self, message: ChatMessage) -> None:
        """
        Signal handler: Add a message to the conversation.
        This allows clients to send followup messages while the workflow is running.
        The workflow will wake up and process this message.
        """
        async with self._lock:
            self._state.messages.append(message)
            self._new_message_count += 1
            self._state.is_waiting_for_input = False
            workflow.logger.info(
                f"Message added to conversation",
                extra={
                    "role": message.role,
                    "content_preview": message.content[:100] if message.content else "",
                    "total_messages": len(self._state.messages)
                }
            )

    @workflow.signal
    async def mark_as_done(self) -> None:
        """
        Signal handler: Mark the workflow as complete.
        This signals that the user is done with the conversation and the workflow should complete.
        """
        async with self._lock:
            self._state.should_complete = True
            self._state.is_waiting_for_input = False
            workflow.logger.info("Workflow marked as done by user")

    @workflow.run
    async def run(self, input: AgentExecutionInput) -> dict:
        """
        Run the agent execution workflow with Human-in-the-Loop (HITL) pattern.

        This workflow implements a continuous conversation loop:
        1. Process the initial user message
        2. Execute LLM and return response
        3. Wait for user input (signals)
        4. Process followup messages in a loop
        5. Only complete when user explicitly marks as done

        Args:
            input: Workflow input with execution details

        Returns:
            Execution result dict with response, usage, etc.
        """
        # Generate execution_id if not provided (for backward compatibility with old schedules)
        execution_id = input.execution_id
        if not execution_id:
            execution_id = workflow.uuid4()
            workflow.logger.info(
                "Generated execution_id for backward compatibility",
                extra={"execution_id": execution_id}
            )
            # Update input object to use generated ID
            input.execution_id = execution_id

        # Removed: execution start logging (was appearing for all workers, possibly due to Temporal replays)
        # execution_logger.execution_started(
        #     input.execution_id,
        #     agent_id=input.agent_id,
        #     model=input.model_id,
        #     runtime=input.runtime_type
        # )

        workflow.logger.info(
            f"Starting agent execution workflow with HITL pattern",
            extra={
                "execution_id": input.execution_id,
                "agent_id": input.agent_id,
                "organization_id": input.organization_id,
            }
        )

        # Initialize state with user's initial message
        # CRITICAL: Use real-time timestamp (not workflow.now()) to ensure chronological ordering
        # This prevents timestamp mismatches between initial and follow-up messages
        message_timestamp = input.initial_message_timestamp or workflow.now().isoformat()

        initial_user_message = ChatMessage(
            role="user",
            content=input.prompt,
            timestamp=message_timestamp,
            message_id=f"{input.execution_id}_user_1",  # Generate deterministic ID
        )
        self._state.messages.append(initial_user_message)
        self._state.status = "running"
        self._new_message_count = 1  # Initial message counts as a new message
        self._processed_message_count = 0  # No messages processed yet (no response)

        try:
            # Step 1: Update execution status to running
            await workflow.execute_activity(
                update_execution_status,
                ActivityUpdateExecutionInput(
                    execution_id=input.execution_id,
                    status="running",
                    started_at=workflow.now().isoformat(),
                    execution_metadata={
                        "workflow_started": True,
                        "has_mcp_servers": bool(input.mcp_servers),
                        "mcp_server_count": len(input.mcp_servers) if input.mcp_servers else 0,
                        "hitl_enabled": True,
                    },
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Step 2: Update agent status to running
            await workflow.execute_activity(
                update_agent_status,
                ActivityUpdateAgentInput(
                    agent_id=input.agent_id,
                    organization_id=input.organization_id,
                    status="running",
                    last_active_at=workflow.now().isoformat(),
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Deprecate old patch: We moved status update BEFORE persistence (was after)
            # This ensures deterministic replay when continuing multi-turn conversations
            workflow.deprecate_patch("status-update-before-persistence")

            # HITL Conversation Loop - Continue until user marks as done
            conversation_turn = 0
            while not self._state.should_complete:
                conversation_turn += 1
                workflow.logger.info(
                    f"Starting conversation turn {conversation_turn}",
                    extra={"turn": conversation_turn, "message_count": len(self._state.messages)}
                )

                # Get the latest user message (last message added)
                latest_message = self._state.messages[-1] if self._state.messages else None
                latest_prompt = latest_message.content if latest_message and latest_message.role == "user" else input.prompt

                # Extract user message metadata for session persistence deduplication
                user_message_id = latest_message.message_id if latest_message and latest_message.role == "user" else None
                user_id = latest_message.user_id if latest_message and latest_message.role == "user" else None
                user_name = latest_message.user_name if latest_message and latest_message.role == "user" else None
                user_email = latest_message.user_email if latest_message and latest_message.role == "user" else None
                user_avatar = latest_message.user_avatar if latest_message and latest_message.role == "user" else None

                # Step 3: Publish user message to stream IMMEDIATELY (for turn 1)
                # For follow-up turns, the message is published when received via signal
                # This ensures the initial user message appears in UI before assistant response
                #
                # IMPORTANT: Use workflow patching to handle existing workflows that don't have this activity
                # Existing workflows will skip this during replay; new workflows will execute it
                if conversation_turn == 1 and workflow.patched("publish-user-message-v1"):
                    workflow.logger.info(
                        f"Publishing initial user message to stream",
                        extra={
                            "turn": conversation_turn,
                            "message_id": user_message_id,
                            "execution_id": str(input.execution_id)[:8] if input.execution_id else "unknown"
                        }
                    )
                    await workflow.execute_activity(
                        publish_user_message,
                        PublishUserMessageInput(
                            execution_id=input.execution_id,
                            prompt=input.prompt,
                            timestamp=initial_user_message.timestamp,
                            message_id=user_message_id,
                            user_id=input.user_metadata.get("user_id") if input.user_metadata else None,
                            user_name=input.user_metadata.get("user_name") if input.user_metadata else None,
                            user_email=input.user_metadata.get("user_email") if input.user_metadata else None,
                            user_avatar=input.user_metadata.get("user_avatar") if input.user_metadata else None,
                        ),
                        start_to_close_timeout=timedelta(seconds=10),
                    )

                # Execute using RuntimeFactory (supports both "default" Agno and "claude_code")
                workflow.logger.info(
                    f"Executing with runtime: {input.runtime_type}",
                    extra={
                        "runtime_type": input.runtime_type,
                        "turn": conversation_turn,
                        "user_message_id": user_message_id  # Log for debugging
                    }
                )

                # DEBUG: Log MCP servers in workflow input
                workflow.logger.info(
                    f"🔍 DEBUG: Workflow MCP servers",
                    extra={
                        "mcp_servers_type": str(type(input.mcp_servers)),
                        "mcp_servers_count": len(input.mcp_servers) if input.mcp_servers else 0,
                        "mcp_server_names": list(input.mcp_servers.keys()) if input.mcp_servers else []
                    }
                )

                # Track turn start time for analytics
                # workflow.time() already returns a float timestamp, not a datetime
                turn_start_time = workflow.time()

                llm_result = await workflow.execute_activity(
                    execute_with_runtime,
                    ActivityRuntimeExecuteInput(
                        execution_id=input.execution_id,
                        agent_id=input.agent_id,
                        organization_id=input.organization_id,
                        prompt=latest_prompt,  # Current turn's prompt
                        runtime_type=input.runtime_type,
                        system_prompt=input.system_prompt,
                        model_id=input.model_id,
                        model_config=input.model_config,
                        agent_config=input.agent_config,
                        mcp_servers=input.mcp_servers,
                        conversation_history=[],  # Agno manages history via session_id
                        user_metadata=input.user_metadata,
                        runtime_config={
                            "session_id": input.execution_id,  # For Agno runtime
                        },
                        stream=True,  # Enable streaming for real-time updates
                        conversation_turn=conversation_turn,  # Pass turn number for analytics
                        # CRITICAL: Pass user message metadata for consistent deduplication
                        user_message_id=user_message_id,
                        user_id=user_id,
                        user_name=user_name,
                        user_email=user_email,
                        user_avatar=user_avatar,
                    ),
                    start_to_close_timeout=timedelta(minutes=10),
                    heartbeat_timeout=timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS),  # Configurable, default 10 min for long-running tasks
                    retry_policy=RetryPolicy(
                        maximum_attempts=3,  # Retry automatically 1-3 times
                        initial_interval=timedelta(seconds=1),
                        maximum_interval=timedelta(seconds=10),
                        backoff_coefficient=2.0,
                        non_retryable_error_types=["ExecutionNotFound"],  # Don't retry if execution deleted
                    ),
                )

                # Submit analytics as separate activity (fire-and-forget)
                # This runs independently and doesn't block workflow progression
                workflow.start_activity(
                    submit_runtime_analytics_activity,
                    AnalyticsActivityInput(
                        execution_id=input.execution_id,
                        turn_number=conversation_turn,
                        result=llm_result,
                        turn_start_time=turn_start_time,
                    ),
                    start_to_close_timeout=timedelta(seconds=30),
                )

                # Add tool execution status messages (real-time updates)
                if llm_result.get("tool_execution_messages"):
                    async with self._lock:
                        for tool_msg in llm_result["tool_execution_messages"]:
                            self._state.messages.append(ChatMessage(
                                role="system",
                                content=tool_msg.get("content", ""),
                                timestamp=tool_msg.get("timestamp", workflow.now().isoformat()),
                                tool_name=tool_msg.get("tool_name"),
                            ))

                # Add tool messages to state (detailed tool info)
                if llm_result.get("tool_messages"):
                    async with self._lock:
                        for tool_msg in llm_result["tool_messages"]:
                            self._state.messages.append(ChatMessage(
                                role="tool",
                                content=tool_msg.get("content", ""),
                                timestamp=tool_msg.get("timestamp", workflow.now().isoformat()),
                                tool_name=tool_msg.get("tool_name"),
                                tool_input=tool_msg.get("tool_input"),
                            ))

                # Update state with assistant response
                if llm_result.get("response"):
                    async with self._lock:
                        self._state.messages.append(ChatMessage(
                            role="assistant",
                            content=llm_result["response"],
                            timestamp=workflow.now().isoformat(),
                        ))
                        self._state.current_response = llm_result["response"]
                        self._processed_message_count += 1

                # Update usage and metadata (accumulate across turns)
                if llm_result.get("usage"):
                    # Accumulate token usage across conversation turns
                    current_usage = self._state.usage
                    new_usage = llm_result.get("usage", {})
                    self._state.usage = {
                        "prompt_tokens": current_usage.get("prompt_tokens", 0) + new_usage.get("prompt_tokens", 0),
                        "completion_tokens": current_usage.get("completion_tokens", 0) + new_usage.get("completion_tokens", 0),
                        "total_tokens": current_usage.get("total_tokens", 0) + new_usage.get("total_tokens", 0),
                    }

                # Update metadata with latest turn info
                self._state.metadata.update({
                    "model": llm_result.get("model"),
                    "latest_finish_reason": llm_result.get("finish_reason"),
                    "mcp_tools_used": self._state.metadata.get("mcp_tools_used", 0) + llm_result.get("mcp_tools_used", 0),
                    "latest_run_id": llm_result.get("run_id"),
                    "conversation_turns": conversation_turn,
                })

                # Extract session_id from runtime result for conversation continuity
                # This enables multi-turn conversations in Claude Code runtime
                llm_metadata = llm_result.get("metadata", {})
                if "claude_code_session_id" in llm_metadata:
                    # Update input.user_metadata so next turn can resume the session
                    if not input.user_metadata:
                        input.user_metadata = {}
                    session_id_value = llm_metadata["claude_code_session_id"]
                    input.user_metadata["claude_code_session_id"] = session_id_value
                    workflow.logger.info(
                        f"Updated user_metadata with session_id for turn continuity",
                        extra={
                            "turn": conversation_turn,
                            "session_id": session_id_value[:16] if session_id_value else None
                        }
                    )

                # Check if LLM call was cancelled (DURABILITY FIX)
                finish_reason = llm_result.get("finish_reason")
                if finish_reason == "cancelled":
                    # Execution was cancelled/interrupted - handle gracefully
                    workflow.logger.warning(
                        f"⚠️ Execution cancelled during turn {conversation_turn}",
                        extra={
                            "turn": conversation_turn,
                            "execution_id": input.execution_id,
                            "metadata": llm_result.get("metadata", {}),
                        }
                    )

                    # Mark as interrupted (not failed) to indicate this is recoverable
                    self._state.status = "interrupted"
                    self._state.error_message = "Execution was interrupted and can be resumed"

                    # Save any accumulated response before breaking
                    if llm_result.get("response"):
                        async with self._lock:
                            self._state.messages.append(ChatMessage(
                                role="assistant",
                                content=llm_result["response"],
                                timestamp=workflow.now().isoformat(),
                            ))
                            self._state.current_response = llm_result["response"]

                    # Break but allow workflow to complete gracefully
                    break

                # Check if LLM call failed
                if not llm_result.get("success"):
                    self._state.status = "failed"
                    # Validate error message is never empty
                    error_msg = llm_result.get("error") or "Execution failed with unknown error"
                    if not error_msg.strip():
                        error_msg = "Execution failed (error details not available)"
                    self._state.error_message = error_msg
                    break

                # Wait for control plane to make intelligent state decision
                # The control plane AI analyzes the turn and determines the appropriate state
                workflow.logger.info(
                    f"⏳ Waiting for control plane state decision for turn {conversation_turn}",
                    extra={"turn": conversation_turn, "execution_id": str(input.execution_id)[:8] if input.execution_id else "unknown"}
                )

                # Give control plane time to make AI decision (up to 6 seconds with retries)
                max_retries = 3
                retry_delay = 2  # seconds

                for retry in range(max_retries):
                    await asyncio.sleep(retry_delay)

                    # Query execution state from control plane
                    try:
                        current_execution = await workflow.execute_activity(
                            get_execution_details,
                            ActivityGetExecutionInput(execution_id=input.execution_id),
                            start_to_close_timeout=timedelta(seconds=10),
                        )

                        control_plane_status = current_execution.get("status", "unknown")

                        # Check if status has been updated from "running" (indicates AI made a decision)
                        if control_plane_status != "running":
                            workflow.logger.info(
                                f"✅ Control plane decided state: {control_plane_status}",
                                extra={
                                    "execution_id": input.execution_id,
                                    "turn": conversation_turn,
                                    "decided_status": control_plane_status,
                                    "retry": retry + 1
                                }
                            )
                            break
                        else:
                            if retry < max_retries - 1:
                                workflow.logger.info(
                                    f"⏳ Control plane still processing, retry {retry + 1}/{max_retries}",
                                    extra={"turn": conversation_turn}
                                )
                    except Exception as e:
                        workflow.logger.warning(
                            f"⚠️ Failed to query execution state: {str(e)}",
                            extra={"turn": conversation_turn, "retry": retry + 1}
                        )
                        if retry == max_retries - 1:
                            # Final retry failed - default to waiting_for_input (safe fallback)
                            control_plane_status = "waiting_for_input"
                            workflow.logger.warning(
                                "Using safe fallback state: waiting_for_input",
                                extra={"turn": conversation_turn}
                            )

                # Update internal state based on control plane decision
                self._state.status = control_plane_status
                self._state.is_waiting_for_input = (control_plane_status == "waiting_for_input")

                workflow.logger.info(
                    f"🎯 State transition complete: {control_plane_status}",
                    extra={
                        "execution_id": input.execution_id,
                        "turn": conversation_turn,
                        "status": control_plane_status
                    }
                )

                # Then persist conversation
                workflow.logger.info(
                    f"Persisting conversation after turn {conversation_turn}",
                    extra={"turn": conversation_turn, "message_count": len(self._state.messages)}
                )

                try:
                    persist_result = await workflow.execute_activity(
                        persist_conversation_history,
                        ActivityPersistConversationInput(
                            execution_id=input.execution_id,
                            session_id=input.execution_id,
                            messages=self._messages_to_dict(self._state.messages),
                            user_id=input.user_metadata.get("user_id") if input.user_metadata else None,
                            metadata={
                                "agent_id": input.agent_id,
                                "organization_id": input.organization_id,
                                "conversation_turn": conversation_turn,
                                "total_messages": len(self._state.messages),
                            },
                        ),
                        start_to_close_timeout=timedelta(seconds=30),
                    )

                    if persist_result.get("success"):
                        workflow.logger.info(
                            f"✅ Conversation persisted for turn {conversation_turn}",
                            extra={
                                "turn": conversation_turn,
                                "message_count": persist_result.get("message_count", len(self._state.messages))
                            }
                        )
                    else:
                        workflow.logger.warning(
                            f"⚠️ Persistence returned failure for turn {conversation_turn}",
                            extra={
                                "turn": conversation_turn,
                                "error": persist_result.get("error", "Unknown error")
                            }
                        )

                except Exception as persist_error:
                    # Log but don't fail the workflow if persistence fails
                    error_type = type(persist_error).__name__
                    error_msg = str(persist_error) if str(persist_error) else "No error message"

                    workflow.logger.error(
                        f"❌ Failed to persist conversation for turn {conversation_turn}",
                        extra={
                            "turn": conversation_turn,
                            "error_type": error_type,
                            "error": error_msg[:200],  # Truncate long errors
                            "message_count": len(self._state.messages),
                        }
                    )

                # Handle different states based on control plane decision
                if control_plane_status == "completed":
                    workflow.logger.info(
                        f"✅ Task completed (AI decision) after turn {conversation_turn}",
                        extra={"turn": conversation_turn}
                    )
                    # Task is complete - exit loop
                    break

                elif control_plane_status == "failed":
                    workflow.logger.info(
                        f"❌ Task failed (AI decision) after turn {conversation_turn}",
                        extra={"turn": conversation_turn}
                    )
                    # Unrecoverable error - exit loop
                    break

                elif control_plane_status == "waiting_for_input":
                    workflow.logger.info(
                        f"⏸️ Waiting for user input after turn {conversation_turn}",
                        extra={"turn": conversation_turn}
                    )

                    # Wait for either:
                    # 1. New message from user (add_message signal)
                    # 2. User marks as done (mark_as_done signal)
                    # 3. Timeout (24 hours for long-running conversations)
                    await workflow.wait_condition(
                        lambda: self._new_message_count > self._processed_message_count or self._state.should_complete,
                        timeout=timedelta(hours=24)
                    )

                    # Don't update processed count here - it will be updated after we add the assistant's response

                    if self._state.should_complete:
                        workflow.logger.info("User marked workflow as done")
                        break

                    # Continue loop to process new message
                    self._state.status = "running"

                elif control_plane_status == "running":
                    workflow.logger.info(
                        f"▶️ Continuing automatically to next turn {conversation_turn + 1}",
                        extra={"turn": conversation_turn}
                    )
                    # Continue automatically to next turn (no user input needed)
                    # Just loop back to execute_agent_llm
                    continue

                else:
                    # Unknown status - default to waiting_for_input (safe fallback)
                    workflow.logger.warning(
                        f"⚠️ Unknown status '{control_plane_status}', defaulting to waiting_for_input",
                        extra={"turn": conversation_turn, "status": control_plane_status}
                    )
                    self._state.status = "waiting_for_input"
                    self._state.is_waiting_for_input = True

                    await workflow.wait_condition(
                        lambda: self._new_message_count > self._processed_message_count or self._state.should_complete,
                        timeout=timedelta(hours=24)
                    )

                    if self._state.should_complete:
                        workflow.logger.info("User marked workflow as done")
                        break

                    self._state.status = "running"

            # Conversation complete - finalize workflow
            # DURABILITY FIX: Handle interrupted status separately from failed/completed
            if self._state.status == "interrupted":
                final_status = "interrupted"
                workflow.logger.warning(
                    f"⚠️ Workflow interrupted (not failed)",
                    extra={
                        "execution_id": input.execution_id,
                        "conversation_turns": conversation_turn,
                    }
                )
            elif self._state.status == "failed":
                final_status = "failed"
            else:
                final_status = "completed"

            self._state.status = final_status

            await workflow.execute_activity(
                update_execution_status,
                ActivityUpdateExecutionInput(
                    execution_id=input.execution_id,
                    status=final_status,
                    completed_at=workflow.now().isoformat(),
                    response=self._state.current_response,
                    error_message=self._state.error_message,
                    usage=self._state.usage,
                    execution_metadata={
                        **self._state.metadata,
                        "workflow_completed": True,
                        "total_conversation_turns": conversation_turn,
                        "was_interrupted": final_status == "interrupted",
                    },
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Update agent final status
            # DURABILITY FIX: Treat interrupted as a partial success, not a failure
            agent_final_status = "failed" if final_status == "failed" else "completed"
            await workflow.execute_activity(
                update_agent_status,
                ActivityUpdateAgentInput(
                    agent_id=input.agent_id,
                    organization_id=input.organization_id,
                    status=agent_final_status,
                    last_active_at=workflow.now().isoformat(),
                    error_message=self._state.error_message if final_status == "failed" else None,
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )

            workflow.logger.info(
                f"Agent execution workflow completed with HITL",
                extra={
                    "execution_id": input.execution_id,
                    "status": final_status,
                    "conversation_turns": conversation_turn,
                }
            )

            return {
                "success": final_status == "completed",
                "execution_id": input.execution_id,
                "status": final_status,
                "response": self._state.current_response,
                "usage": self._state.usage,
                "conversation_turns": conversation_turn,
            }

        except Exception as e:
            # Update state with error
            self._state.status = "failed"
            self._state.error_message = str(e)
            self._state.metadata["error_type"] = type(e).__name__

            # Log failure with clear context
            execution_logger.execution_failed(
                input.execution_id,
                error=str(e),
                error_type=type(e).__name__,
                recoverable=False
            )

            workflow.logger.error(
                f"Agent execution workflow failed",
                extra={
                    "execution_id": input.execution_id,
                    "error": str(e),
                }
            )

            # Update execution as failed
            try:
                await workflow.execute_activity(
                    update_execution_status,
                    ActivityUpdateExecutionInput(
                        execution_id=input.execution_id,
                        status="failed",
                        completed_at=workflow.now().isoformat(),
                        error_message=f"Workflow error: {str(e)}",
                        execution_metadata={
                            "workflow_error": True,
                            "error_type": type(e).__name__,
                        },
                    ),
                    start_to_close_timeout=timedelta(seconds=30),
                )

                await workflow.execute_activity(
                    update_agent_status,
                    ActivityUpdateAgentInput(
                        agent_id=input.agent_id,
                        organization_id=input.organization_id,
                        status="failed",
                        last_active_at=workflow.now().isoformat(),
                        error_message=str(e),
                    ),
                    start_to_close_timeout=timedelta(seconds=30),
                )
            except Exception as update_error:
                execution_logger.warning(
                    input.execution_id,
                    f"Could not update execution status after workflow error: {str(update_error)}"
                )
                workflow.logger.error(
                    f"Failed to update status after error",
                    extra={"error": str(update_error)}
                )

            raise
