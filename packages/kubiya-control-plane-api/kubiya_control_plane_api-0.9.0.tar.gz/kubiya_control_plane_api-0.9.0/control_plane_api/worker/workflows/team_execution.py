"""Team execution workflow for Temporal"""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional, List, Dict, Any
from temporalio import workflow
import asyncio

with workflow.unsafe.imports_passed_through():
    from control_plane_api.worker.activities.team_activities import (
        get_team_agents,
        execute_team_coordination,
        ActivityGetTeamAgentsInput,
        ActivityExecuteTeamInput,
    )
    from control_plane_api.worker.activities.agent_activities import (
        update_execution_status,
        get_execution_details,
        submit_runtime_analytics_activity,
        ActivityUpdateExecutionInput,
        ActivityGetExecutionInput,
        AnalyticsActivityInput,
    )
    from control_plane_api.worker.activities.runtime_activities import (
        publish_user_message,
        PublishUserMessageInput,
    )


@dataclass
class TeamExecutionInput:
    """Input for team execution workflow"""
    execution_id: str
    team_id: str
    organization_id: str
    prompt: str
    system_prompt: Optional[str] = None
    team_config: dict = None
    user_metadata: dict = None
    mcp_servers: dict = None  # MCP servers configuration
    initial_message_timestamp: Optional[str] = None  # Timestamp for initial user message

    def __post_init__(self):
        if self.team_config is None:
            self.team_config = {}
        if self.user_metadata is None:
            self.user_metadata = {}
        if self.mcp_servers is None:
            self.mcp_servers = {}


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
    status: str  # "pending", "running", "waiting_for_input", "paused", "completed", "failed"
    messages: List[ChatMessage] = field(default_factory=list)
    current_response: str = ""
    error_message: Optional[str] = None
    usage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_waiting_for_input: bool = False
    should_complete: bool = False
    is_paused: bool = False


@workflow.defn
class TeamExecutionWorkflow:
    """
    Workflow for executing a team of agents with HITL support.

    This workflow:
    1. Gets team agents
    2. Coordinates execution across agents
    3. Aggregates results
    4. Updates execution status
    5. Supports queries for real-time state access
    6. Supports signals for adding followup messages
    """

    def __init__(self) -> None:
        """Initialize workflow state"""
        self._state = ExecutionState(status="pending")
        self._lock = asyncio.Lock()
        self._new_message_count = 0
        self._processed_message_count = 0

    @workflow.query
    def get_state(self) -> ExecutionState:
        """Query handler: Get current execution state including messages and status"""
        return self._state

    @workflow.signal
    async def add_message(self, message: ChatMessage) -> None:
        """
        Signal handler: Add a message to the conversation.
        This allows clients to send followup messages while the workflow is running.
        """
        async with self._lock:
            self._state.messages.append(message)
            self._new_message_count += 1
            self._state.is_waiting_for_input = False
            workflow.logger.info(
                f"Message added to team conversation",
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
        """
        async with self._lock:
            self._state.should_complete = True
            self._state.is_waiting_for_input = False
            workflow.logger.info("Team workflow marked as done by user")

    @workflow.signal
    async def update_streaming_response(self, current_response: str) -> None:
        """
        Signal handler: Update current streaming response.
        Activity sends this periodically during execution for state tracking.
        """
        async with self._lock:
            self._state.current_response = current_response
            workflow.logger.info(
                f"Streaming response updated",
                extra={"response_length": len(current_response)}
            )

    @workflow.signal
    async def pause_execution(self) -> None:
        """
        Signal handler: Pause the workflow execution.
        This pauses the workflow - it will stop processing but remain active.
        Resume can be called to continue execution.
        """
        async with self._lock:
            if not self._state.is_paused:
                self._state.is_paused = True
                self._state.status = "paused"
                workflow.logger.info("Team workflow paused by user")

    @workflow.signal
    async def resume_execution(self) -> None:
        """
        Signal handler: Resume a paused workflow execution.
        This resumes the workflow from where it was paused.
        """
        async with self._lock:
            if self._state.is_paused:
                self._state.is_paused = False
                # Restore previous status (either running or waiting_for_input)
                self._state.status = "waiting_for_input" if self._state.is_waiting_for_input else "running"
                workflow.logger.info("Team workflow resumed by user")

    @workflow.run
    async def run(self, input: TeamExecutionInput) -> dict:
        """
        Run the team execution workflow with HITL pattern.

        This workflow implements a continuous conversation loop:
        1. Process the initial user message
        2. Execute team coordination and return response
        3. Wait for user input (signals)
        4. Process followup messages in a loop
        5. Only complete when user explicitly marks as done

        Args:
            input: Workflow input with team execution details

        Returns:
            Team execution result dict
        """
        workflow.logger.info(
            f"Starting team execution workflow with HITL pattern",
            extra={
                "execution_id": input.execution_id,
                "team_id": input.team_id,
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
        self._new_message_count = 1
        self._processed_message_count = 0

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
                        "hitl_enabled": True,
                    },
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Step 1.5: Publish initial user message to stream immediately
            # This ensures the user message appears in UI before assistant response
            #
            # IMPORTANT: Use workflow patching to handle existing workflows that don't have this activity
            # Existing workflows will skip this during replay; new workflows will execute it
            if workflow.patched("publish-user-message-v1"):
                workflow.logger.info(
                    f"Publishing initial user message to stream",
                    extra={
                        "execution_id": str(input.execution_id)[:8] if input.execution_id else "unknown",
                        "message_id": initial_user_message.message_id,
                    }
                )
                await workflow.execute_activity(
                    publish_user_message,
                    PublishUserMessageInput(
                        execution_id=input.execution_id,
                        prompt=input.prompt,
                        timestamp=initial_user_message.timestamp,
                        message_id=initial_user_message.message_id,
                        user_id=input.user_metadata.get("user_id") if input.user_metadata else None,
                        user_name=input.user_metadata.get("user_name") if input.user_metadata else None,
                        user_email=input.user_metadata.get("user_email") if input.user_metadata else None,
                        user_avatar=input.user_metadata.get("user_avatar") if input.user_metadata else None,
                    ),
                    start_to_close_timeout=timedelta(seconds=10),
                )

            # Step 2: Get team agents once at the beginning
            workflow.logger.info(
                f"[WORKFLOW] About to call get_team_agents",
                extra={
                    "team_id": input.team_id,
                    "organization_id": input.organization_id,
                }
            )

            team_agents = await workflow.execute_activity(
                get_team_agents,
                ActivityGetTeamAgentsInput(
                    team_id=input.team_id,
                    organization_id=input.organization_id,
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )

            workflow.logger.info(
                f"[WORKFLOW] get_team_agents returned",
                extra={
                    "result": team_agents,
                    "agents_count": len(team_agents.get("agents", [])) if team_agents else 0,
                }
            )

            if not team_agents.get("agents"):
                workflow.logger.error(
                    f"[WORKFLOW] NO AGENTS RETURNED!",
                    extra={
                        "team_agents": team_agents,
                        "team_id": input.team_id,
                        "organization_id": input.organization_id,
                    }
                )
                raise ValueError("No agents found in team")

            # HITL Conversation Loop - Continue until user marks as done
            conversation_turn = 0
            while not self._state.should_complete:
                # Check if workflow is paused - wait until resumed
                if self._state.is_paused:
                    workflow.logger.info(
                        "Team workflow is paused, waiting for resume signal",
                        extra={"execution_id": str(input.execution_id)[:8] if input.execution_id else "unknown"}
                    )
                    await workflow.wait_condition(
                        lambda: not self._state.is_paused or self._state.should_complete,
                        timeout=timedelta(hours=24)
                    )
                    if self._state.should_complete:
                        break
                    workflow.logger.info(
                        "Team workflow resumed, continuing execution",
                        extra={"execution_id": str(input.execution_id)[:8] if input.execution_id else "unknown"}
                    )

                conversation_turn += 1
                workflow.logger.info(
                    f"Starting team conversation turn {conversation_turn}",
                    extra={"turn": conversation_turn, "message_count": len(self._state.messages)}
                )

                # Get the latest user message
                latest_message = self._state.messages[-1] if self._state.messages else None
                latest_prompt = latest_message.content if latest_message and latest_message.role == "user" else input.prompt

                # Capture turn start time for analytics
                # workflow.time() already returns a float timestamp, no need for .timestamp()
                turn_start_time = workflow.time()

                # Step 3: Execute team coordination
                team_result = await workflow.execute_activity(
                    execute_team_coordination,
                    ActivityExecuteTeamInput(
                        execution_id=input.execution_id,
                        team_id=input.team_id,
                        organization_id=input.organization_id,
                        prompt=latest_prompt,
                        system_prompt=input.system_prompt,
                        agents=team_agents["agents"],
                        team_config=input.team_config,
                        mcp_servers=input.mcp_servers,  # Pass MCP servers
                        session_id=input.execution_id,  # Use execution_id as session_id
                        user_id=input.user_metadata.get("user_id") if input.user_metadata else None,
                        model_id=input.team_config.get("llm", {}).get("model") if input.team_config else None,
                        model_config=input.team_config.get("llm", {}) if input.team_config else None,
                        # Activity reads CONTROL_PLANE_URL and KUBIYA_API_KEY from worker environment
                    ),
                    start_to_close_timeout=timedelta(minutes=30),  # Teams can take longer
                )

                # Add tool execution status messages (real-time updates)
                if team_result.get("tool_execution_messages"):
                    async with self._lock:
                        for tool_msg in team_result["tool_execution_messages"]:
                            self._state.messages.append(ChatMessage(
                                role="system",
                                content=tool_msg.get("content", ""),
                                timestamp=tool_msg.get("timestamp", workflow.now().isoformat()),
                                tool_name=tool_msg.get("tool_name"),
                            ))

                # Add tool messages to state (detailed tool info)
                if team_result.get("tool_messages"):
                    async with self._lock:
                        for tool_msg in team_result["tool_messages"]:
                            self._state.messages.append(ChatMessage(
                                role="tool",
                                content=tool_msg.get("content", ""),
                                timestamp=tool_msg.get("timestamp", workflow.now().isoformat()),
                                tool_name=tool_msg.get("tool_name"),
                                tool_input=tool_msg.get("tool_input"),
                            ))

                # Update state with team response
                if team_result.get("response"):
                    async with self._lock:
                        # CRITICAL: Use real-time timestamp from team_result if available
                        # This ensures chronological ordering with streaming events
                        # Fallback to workflow.now() (deterministic) if not provided
                        response_timestamp = team_result.get("response_timestamp") or workflow.now().isoformat()

                        self._state.messages.append(ChatMessage(
                            role="assistant",
                            content=team_result["response"],
                            timestamp=response_timestamp,
                        ))
                        self._state.current_response = team_result["response"]
                        self._processed_message_count += 1

                # Update usage and metadata (accumulate across turns)
                if team_result.get("usage"):
                    current_usage = self._state.usage
                    new_usage = team_result.get("usage", {})
                    self._state.usage = {
                        "input_tokens": current_usage.get("input_tokens", 0) + new_usage.get("input_tokens", 0),
                        "output_tokens": current_usage.get("output_tokens", 0) + new_usage.get("output_tokens", 0),
                        "total_tokens": current_usage.get("total_tokens", 0) + new_usage.get("total_tokens", 0),
                    }

                # Update metadata
                self._state.metadata.update({
                    "agent_count": len(team_agents["agents"]),
                    "coordination_type": team_result.get("coordination_type"),
                    "conversation_turns": conversation_turn,
                })

                # Check if team execution failed
                if not team_result.get("success"):
                    self._state.status = "failed"
                    self._state.error_message = team_result.get("error")
                    break

                # Submit turn analytics (fire-and-forget)
                # This triggers the control plane's intelligent state transition system
                workflow.start_activity(
                    submit_runtime_analytics_activity,
                    AnalyticsActivityInput(
                        execution_id=input.execution_id,
                        turn_number=conversation_turn,
                        result=team_result,
                        turn_start_time=turn_start_time,
                    ),
                    start_to_close_timeout=timedelta(seconds=30),
                )

                # Wait for control plane to make intelligent state decision
                # The control plane AI analyzes the turn and determines the appropriate state
                workflow.logger.info(
                    f"⏳ Waiting for control plane state decision for team turn {conversation_turn}",
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
                    f"Team turn {conversation_turn} complete - state: {control_plane_status}",
                    extra={"turn": conversation_turn, "status": control_plane_status}
                )

                # Wait for either new message, mark as done, or pause signal
                await workflow.wait_condition(
                    lambda: self._new_message_count > self._processed_message_count or self._state.should_complete or self._state.is_paused,
                    timeout=timedelta(hours=24)
                )

                if self._state.should_complete:
                    workflow.logger.info("User marked team workflow as done")
                    break

                # If paused while waiting, loop back to check pause condition at top of while loop
                if self._state.is_paused:
                    workflow.logger.info(
                        "Team workflow paused while waiting for input",
                        extra={"execution_id": str(input.execution_id)[:8] if input.execution_id else "unknown"}
                    )
                    continue

                # Continue loop to process new message
                self._state.status = "running"

            # Conversation complete - finalize workflow
            final_status = "failed" if self._state.status == "failed" else "completed"
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
                    },
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )

            workflow.logger.info(
                f"Team execution workflow completed with HITL",
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

            workflow.logger.error(
                f"Team execution workflow failed",
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
            except Exception as update_error:
                workflow.logger.error(
                    f"Failed to update status after error",
                    extra={"error": str(update_error)}
                )

            raise
