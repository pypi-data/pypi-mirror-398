"""Streaming utilities for agent and team execution"""

from typing import Dict, Any, Callable, Optional, List
import structlog

logger = structlog.get_logger()


class StreamingHelper:
    """
    Helper for handling streaming from Agno Agent/Team executions.

    Provides utilities for:
    - Publishing events to Control Plane
    - Tracking run_id from streaming chunks
    - Collecting response content
    - Publishing tool execution events
    - Handling member message streaming
    - Tracking tool IDs for proper start/complete matching
    - Splitting assistant messages into pre-tool and post-tool phases
    """

    def __init__(self, control_plane_client, execution_id: str):
        self.control_plane = control_plane_client
        self.execution_id = execution_id
        self.run_id_published = False
        self.response_content = []
        self.member_message_ids = {}  # Track message_id per member
        self.active_streaming_member = None  # Track which member is streaming
        self.tool_execution_ids = {}  # Track tool IDs for matching start/complete events
        self.tool_messages = []  # Track tool messages for session persistence

        # NEW: Track message phases for proper assistant message splitting
        self.pre_tool_content = []  # Content before first tool use
        self.post_tool_content = []  # Content after tools complete
        self.tool_phase = "pre"  # Current phase: "pre", "during", or "post"
        self.first_tool_timestamp = None  # Timestamp when first tool started
        self.tools_complete_timestamp = None  # Timestamp when all tools completed
        self.has_any_tools = False  # Track if any tools were executed

    def handle_run_id(self, chunk: Any, on_run_id: Optional[Callable[[str], None]] = None) -> None:
        """
        Capture and publish run_id from first streaming chunk.

        Args:
            chunk: Streaming chunk from Agno
            on_run_id: Optional callback when run_id is captured
        """
        if not self.run_id_published and hasattr(chunk, 'run_id') and chunk.run_id:
            run_id = chunk.run_id

            logger.info("run_id_captured", execution_id=self.execution_id[:8], run_id=run_id[:16])

            # Publish to Control Plane for UI
            self.control_plane.publish_event(
                execution_id=self.execution_id,
                event_type="run_started",
                data={
                    "run_id": run_id,
                    "execution_id": self.execution_id,
                    "cancellable": True,
                }
            )

            self.run_id_published = True

            # Call callback if provided (for cancellation manager)
            if on_run_id:
                on_run_id(run_id)

    async def handle_content_chunk(
        self,
        chunk: Any,
        message_id: str,
        print_to_console: bool = True
    ) -> Optional[str]:
        """
        Handle content chunk from streaming response.

        Tracks content in different phases (pre-tool, during-tool, post-tool)
        to enable proper message splitting around tool usage.

        Args:
            chunk: Streaming chunk
            message_id: Unique message ID for this turn
            print_to_console: Whether to print to stdout

        Returns:
            Content string if present, None otherwise
        """
        # Check for both 'response' (RuntimeExecutionResult) and 'content' (legacy/Agno)
        content = None

        if hasattr(chunk, 'response') and chunk.response:
            content = str(chunk.response)
        elif hasattr(chunk, 'content') and chunk.content:
            content = str(chunk.content)

        if content:
            # Track content in appropriate phase
            if self.tool_phase == "pre":
                self.pre_tool_content.append(content)
            elif self.tool_phase == "post":
                self.post_tool_content.append(content)
            # Note: During "during" phase, we don't collect assistant content
            # as tools are executing

            self.response_content.append(content)

            if print_to_console:
                print(content, end='', flush=True)

            # Stream to Control Plane for real-time UI updates
            # Use async version since we're in an async context
            try:
                await self.control_plane.publish_event_async(
                    execution_id=self.execution_id,
                    event_type="message_chunk",
                    data={
                        "role": "assistant",
                        "content": content,
                        "is_chunk": True,
                        "message_id": message_id,
                        "phase": self.tool_phase,  # NEW: Include current phase
                    }
                )
            except Exception as publish_err:
                # Log but don't fail if event publishing fails
                logger.warning(
                    "async_event_publish_failed",
                    execution_id=self.execution_id[:8],
                    error=str(publish_err)[:200],
                )

            return content

        return None

    def publish_content_chunk(self, content: str, message_id: str) -> None:
        """
        Publish content chunk event (sync wrapper for streaming events).

        This method is called from sync event callbacks in the runtime streaming path.
        It tracks content in the appropriate phase and publishes to Control Plane.

        Args:
            content: Content string to publish
            message_id: Unique message ID for this turn
        """
        # Track content
        self.response_content.append(content)

        # Track in appropriate phase for message splitting
        if self.tool_phase == "pre":
            self.pre_tool_content.append(content)
        elif self.tool_phase == "post":
            self.post_tool_content.append(content)
        # Note: During "during" phase, we don't collect assistant content
        # as tools are executing

        # Publish to Control Plane (use sync publish_event, not async)
        # Note: This is called from a sync callback, so we can't use await
        try:
            self.control_plane.publish_event(
                execution_id=self.execution_id,
                event_type="message_chunk",
                data={
                    "role": "assistant",
                    "content": content,
                    "is_chunk": True,
                    "message_id": message_id,
                    "phase": self.tool_phase,  # Include current phase
                }
            )
        except Exception as publish_err:
            # Log but don't fail if event publishing fails
            logger.warning(
                "sync_event_publish_failed",
                execution_id=self.execution_id[:8],
                error=str(publish_err)[:200],
            )

    def get_full_response(self) -> str:
        """Get the complete response accumulated from all chunks."""
        return ''.join(self.response_content)

    def handle_member_content_chunk(
        self,
        member_name: str,
        content: str,
        print_to_console: bool = True
    ) -> str:
        """
        Handle content chunk from a team member.

        Args:
            member_name: Name of the team member
            content: Content string
            print_to_console: Whether to print to stdout

        Returns:
            The member's message_id
        """
        import time

        # Generate unique message ID for this member if not exists
        if member_name not in self.member_message_ids:
            self.member_message_ids[member_name] = f"{self.execution_id}_{member_name}_{int(time.time() * 1000000)}"

            # Print member name header once when they start
            if print_to_console:
                print(f"\n[{member_name}] ", end='', flush=True)

        # If switching to a different member, mark the previous one as complete
        if self.active_streaming_member and self.active_streaming_member != member_name:
            self.publish_member_complete(self.active_streaming_member)

        # Track that this member is now actively streaming
        self.active_streaming_member = member_name

        # Print content without repeated member name prefix
        if print_to_console:
            print(content, end='', flush=True)

        # Stream member chunk to Control Plane
        message_id = self.member_message_ids[member_name]
        self.control_plane.publish_event(
            execution_id=self.execution_id,
            event_type="member_message_chunk",
            data={
                "role": "assistant",
                "content": content,
                "is_chunk": True,
                "message_id": message_id,
                "source": "team_member",
                "member_name": member_name,
            }
        )

        return message_id

    def publish_member_complete(self, member_name: str) -> None:
        """
        Publish member_message_complete event and clear the message_id.

        Args:
            member_name: Name of the member to mark as complete
        """
        if member_name in self.member_message_ids:
            self.control_plane.publish_event(
                execution_id=self.execution_id,
                event_type="member_message_complete",
                data={
                    "message_id": self.member_message_ids[member_name],
                    "member_name": member_name,
                    "source": "team_member",
                }
            )

            # CRITICAL: Clear the message_id for this member after completing
            # This ensures a NEW message_id is generated for their next turn
            # Without this, all turns from the same member would edit the same message!
            del self.member_message_ids[member_name]
            logger.info("member_message_id_cleared", member_name=member_name, execution_id=self.execution_id[:8])

    def finalize_streaming(self) -> None:
        """
        Finalize streaming by marking any active member as complete.
        Call this when streaming ends.
        """
        if self.active_streaming_member:
            self.publish_member_complete(self.active_streaming_member)
            self.active_streaming_member = None

    def get_tool_messages(self) -> List[Dict[str, Any]]:
        """
        Get all tool messages collected during streaming for session persistence.

        Returns:
            List of tool message dicts with role='system', tool metadata, and timestamps
        """
        return self.tool_messages

    def publish_tool_start(
        self,
        tool_name: str,
        tool_execution_id: str,
        tool_args: Optional[Dict[str, Any]] = None,
        source: str = "agent",
        member_name: Optional[str] = None
    ) -> str:
        """
        Publish tool execution start event.

        Also transitions message phase from "pre" to "during" on first tool use.

        Args:
            tool_name: Name of the tool
            tool_execution_id: Unique ID for this tool execution
            tool_args: Tool arguments
            source: "agent" or "team_member" or "team_leader"  or "team"
            member_name: Name of member (if tool is from a member)

        Returns:
            message_id for this tool execution
        """
        import time
        from datetime import datetime, timezone

        # Mark transition to "during" phase on first tool
        if self.tool_phase == "pre":
            self.tool_phase = "during"
            self.first_tool_timestamp = datetime.now(timezone.utc).isoformat()
            self.has_any_tools = True
            logger.info(
                "phase_transition_to_during",
                execution_id=self.execution_id[:8],
                tool_name=tool_name,
                pre_tool_content_length=len(''.join(self.pre_tool_content))
            )

        message_id = f"{self.execution_id}_tool_{tool_execution_id}"
        is_member_tool = member_name is not None
        parent_message_id = self.member_message_ids.get(member_name) if is_member_tool else None

        # Store tool info for matching with completion event
        tool_key = f"{member_name or 'leader'}_{tool_name}_{int(time.time())}"
        self.tool_execution_ids[tool_key] = {
            "tool_execution_id": tool_execution_id,
            "message_id": message_id,
            "tool_name": tool_name,
            "member_name": member_name,
            "parent_message_id": parent_message_id,
            "tool_args": tool_args,  # Store args for persistence
        }

        event_type = "member_tool_started" if is_member_tool else "tool_started"

        self.control_plane.publish_event(
            execution_id=self.execution_id,
            event_type=event_type,
            data={
                "tool_name": tool_name,
                "tool_execution_id": tool_execution_id,
                "message_id": message_id,
                "tool_arguments": tool_args,
                "source": "team_member" if is_member_tool else "team_leader",
                "member_name": member_name,
                "parent_message_id": parent_message_id,
                "message": f"🔧 Executing tool: {tool_name}",
            }
        )

        return message_id

    def publish_tool_complete(
        self,
        tool_name: str,
        tool_execution_id: str,
        status: str = "success",
        output: Optional[str] = None,
        error: Optional[str] = None,
        source: str = "agent",
        member_name: Optional[str] = None
    ) -> None:
        """
        Publish tool execution completion event.

        Args:
            tool_name: Name of the tool
            tool_execution_id: Unique ID for this tool execution
            status: "success" or "failed"
            output: Tool output (if successful)
            error: Error message (if failed)
            source: "agent" or "team_member" or "team_leader" or "team"
            member_name: Name of member (if tool is from a member)
        """
        import time

        # Find the stored tool info from the start event
        tool_key_pattern = f"{member_name or 'leader'}_{tool_name}"
        matching_tool = None
        for key, tool_info in list(self.tool_execution_ids.items()):
            if key.startswith(tool_key_pattern):
                matching_tool = tool_info
                # Remove from tracking dict
                del self.tool_execution_ids[key]
                break

        if matching_tool:
            message_id = matching_tool["message_id"]
            parent_message_id = matching_tool["parent_message_id"]
            # Use the stored tool_execution_id from the start event
            tool_execution_id = matching_tool["tool_execution_id"]
            tool_args = matching_tool.get("tool_args")  # Get stored args
        else:
            # Fallback if start event wasn't captured
            message_id = f"{self.execution_id}_tool_{tool_execution_id}"
            parent_message_id = self.member_message_ids.get(member_name) if member_name else None
            tool_args = None
            logger.warning("tool_completion_without_start", tool_name=tool_name, member_name=member_name)

        is_member_tool = member_name is not None
        event_type = "member_tool_completed" if is_member_tool else "tool_completed"

        tool_data = {
            "tool_name": tool_name,
            "tool_execution_id": tool_execution_id,  # Now uses the stored ID from start event
            "message_id": message_id,
            "status": status,
            "tool_output": output[:50000] if output else None,  # Increased from 1000 to 50000 to preserve Metabase URLs and other important data
            "tool_error": error,
            "source": "team_member" if is_member_tool else "team_leader",
            "member_name": member_name,
            "parent_message_id": parent_message_id,
            "message": f"{'✅' if status == 'success' else '❌'} Tool {status}: {tool_name}",
        }

        self.control_plane.publish_event(
            execution_id=self.execution_id,
            event_type=event_type,
            data=tool_data
        )

        # Store tool message for session persistence
        # NEW: Tool messages are now role="user" with tool_result content blocks
        # This aligns with Claude API best practices where tool results come from user
        from datetime import datetime, timezone

        tool_result_content = output[:50000] if output and status == "success" else (error or "")

        self.tool_messages.append({
            "role": "user",  # CHANGED: Tool results are user role (Claude API format)
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_execution_id,
                    "content": tool_result_content,
                    "is_error": status != "success",
                }
            ],
            "message_type": "tool_result",  # NEW: Mark as tool result message
            "tool_name": tool_name,
            "tool_execution_id": tool_execution_id,
            "tool_input": tool_args,  # Frontend expects "tool_input" not "tool_arguments"
            "tool_output": output[:50000] if output else None,
            "tool_error": error,
            "tool_status": status,  # Frontend expects "tool_status" not "status"
            "member_name": member_name,
            "message_id": message_id,
            "parent_message_id": parent_message_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(
            "tool_result_message_created",
            execution_id=self.execution_id[:8],
            tool_name=tool_name,
            status=status,
            has_output=bool(output),
            has_error=bool(error)
        )

    def transition_to_post_tool_phase(self):
        """
        Transition from "during" phase to "post" phase.

        Call this after all tools have completed to start collecting
        post-tool assistant content.
        """
        if self.tool_phase == "during":
            from datetime import datetime, timezone
            self.tool_phase = "post"
            self.tools_complete_timestamp = datetime.now(timezone.utc).isoformat()
            logger.info(
                "phase_transition_to_post",
                execution_id=self.execution_id[:8],
                tools_completed=len(self.tool_messages)
            )

    def finalize_streaming(self) -> None:
        """
        Finalize streaming by marking any active member as complete
        and transitioning to post-tool phase if needed.

        Call this when streaming ends.
        """
        # Transition to post phase if we had tools
        if self.has_any_tools and self.tool_phase == "during":
            self.transition_to_post_tool_phase()

        # Handle team member completion
        if self.active_streaming_member:
            self.publish_member_complete(self.active_streaming_member)
            self.active_streaming_member = None

    def get_assistant_message_parts(self) -> List[Dict[str, Any]]:
        """
        Get assistant messages split into pre-tool and post-tool parts.

        Returns:
            List of assistant message dicts. May contain:
            - Pre-tool message (if content exists before first tool)
            - Post-tool message (if content exists after tools complete)
            - Single message (if no tools were used)
        """
        from datetime import datetime, timezone

        assistant_parts = []

        # If no tools were used, return single message with all content
        if not self.has_any_tools:
            full_content = ''.join(self.response_content)
            if full_content:
                assistant_parts.append({
                    "content": full_content,
                    "phase": "complete",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            return assistant_parts

        # If tools were used, split into pre and post parts
        pre_content = ''.join(self.pre_tool_content)
        if pre_content:
            assistant_parts.append({
                "content": pre_content,
                "phase": "pre",
                "timestamp": self.first_tool_timestamp or datetime.now(timezone.utc).isoformat(),
            })

        post_content = ''.join(self.post_tool_content)
        if post_content:
            assistant_parts.append({
                "content": post_content,
                "phase": "post",
                "timestamp": self.tools_complete_timestamp or datetime.now(timezone.utc).isoformat(),
            })

        return assistant_parts

    def build_structured_messages(
        self,
        execution_id: str,
        turn_number: int,
        user_message: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Build structured message list with proper interleaving.

        Creates proper message flow:
        1. User message
        2. Assistant message (pre-tool) if tools were used
        3. Tool result messages (role="user")
        4. Assistant message (post-tool) if tools were used
        OR
        1. User message
        2. Assistant message (complete) if no tools

        Args:
            execution_id: Execution ID
            turn_number: Turn number in conversation
            user_message: User message dict (already constructed)

        Returns:
            List of messages in proper order with message_ids assigned
        """
        messages = [user_message]

        assistant_parts = self.get_assistant_message_parts()

        if not self.has_any_tools:
            # Simple case: no tools, single assistant message
            if assistant_parts:
                part = assistant_parts[0]
                messages.append({
                    "role": "assistant",
                    "content": part["content"],
                    "timestamp": part["timestamp"],
                    "message_id": f"{execution_id}_assistant_{turn_number}",
                })
        else:
            # Complex case: tools were used, split assistant messages
            for i, part in enumerate(assistant_parts):
                phase_suffix = f"_{part['phase']}" if part['phase'] in ['pre', 'post'] else ""
                messages.append({
                    "role": "assistant",
                    "content": part["content"],
                    "timestamp": part["timestamp"],
                    "message_id": f"{execution_id}_assistant_{turn_number}{phase_suffix}",
                    "phase": part["phase"],
                })

                # After pre-tool message, insert tool result messages
                if part["phase"] == "pre":
                    messages.extend(self.tool_messages)

            # If we only have pre-tool content (no post), still add tool messages at end
            if assistant_parts and assistant_parts[-1]["phase"] == "pre":
                messages.extend(self.tool_messages)
            # If we have no assistant parts but have tools, add tool messages
            elif not assistant_parts and self.tool_messages:
                messages.extend(self.tool_messages)

        logger.info(
            "structured_messages_built",
            execution_id=execution_id[:8],
            turn_number=turn_number,
            total_messages=len(messages),
            has_tools=self.has_any_tools,
            assistant_parts=len(assistant_parts),
            tool_messages=len(self.tool_messages)
        )

        return messages


def create_tool_hook(control_plane_client, execution_id: str):
    """
    Create a tool hook function for Agno Agent/Team.

    This hook is called before and after each tool execution
    to publish real-time updates to the Control Plane.

    Args:
        control_plane_client: Control Plane client instance
        execution_id: Execution ID

    Returns:
        Hook function compatible with Agno tool_hooks
    """
    import time

    def tool_hook(tool_name: str, tool_args: dict, result: Any = None, error: Exception = None):
        """Tool hook for real-time updates"""
        tool_execution_id = f"{tool_name}_{int(time.time() * 1000000)}"

        if error is None and result is None:
            # Tool starting
            control_plane_client.publish_event(
                execution_id=execution_id,
                event_type="tool_started",
                data={
                    "tool_name": tool_name,
                    "tool_execution_id": tool_execution_id,
                    "tool_arguments": tool_args,
                    "message": f"🔧 Starting: {tool_name}",
                }
            )
        else:
            # Tool completed
            status = "failed" if error else "success"
            control_plane_client.publish_event(
                execution_id=execution_id,
                event_type="tool_completed",
                data={
                    "tool_name": tool_name,
                    "tool_execution_id": tool_execution_id,
                    "status": status,
                    "tool_output": str(result)[:1000] if result else None,
                    "tool_error": str(error) if error else None,
                    "message": f"{'✅' if status == 'success' else '❌'} {status}: {tool_name}",
                }
            )

    return tool_hook
