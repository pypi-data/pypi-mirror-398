"""
State Transition Service

Provides intelligent state transition decisions for executions using an Agno AI agent.
Analyzes execution context and determines the appropriate next state with reasoning.
"""

import os
import time
import asyncio
from typing import Dict, Any, Literal, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import structlog

from agno.agent import Agent
from agno.models.litellm import LiteLLM
from control_plane_api.app.lib.state_transition_tools.execution_context import ExecutionContextTools
from control_plane_api.app.database import get_db
from control_plane_api.app.models.execution import Execution
from control_plane_api.app.models.execution_transition import ExecutionTransition
from sqlalchemy.orm import Session

logger = structlog.get_logger()


class StateTransitionDecision(BaseModel):
    """
    Structured output from the state transition AI agent
    """

    recommended_state: Literal["running", "waiting_for_input", "completed", "failed"] = Field(
        description="The recommended state to transition to"
    )

    confidence: Literal["low", "medium", "high"] = Field(
        description="Confidence level in this decision"
    )

    reasoning: str = Field(
        description="Detailed explanation of why this state was chosen"
    )

    decision_factors: Dict[str, Any] = Field(
        description="Key factors that influenced this decision",
        default_factory=dict
    )

    should_continue_automatically: bool = Field(
        description="Whether the execution should continue without user input",
        default=False
    )

    estimated_user_action_needed: bool = Field(
        description="Whether user action or input is likely needed",
        default=False
    )


class StateTransitionService:
    """
    Service for intelligent state transition decisions using Agno AI agent
    """

    def __init__(self, organization_id: Optional[str] = None):
        """
        Initialize state transition service

        Args:
            organization_id: Organization context for filtering
        """
        self.organization_id = organization_id

        # Get LiteLLM configuration
        self.litellm_api_url = (
            os.getenv("LITELLM_API_URL")
            or os.getenv("LITELLM_API_BASE")
            or "https://llm-proxy.kubiya.ai"
        ).strip()

        self.litellm_api_key = os.getenv("LITELLM_API_KEY", "").strip()

        if not self.litellm_api_key:
            raise ValueError("LITELLM_API_KEY environment variable not set")

        # Get model from env var or use default
        self.model = os.getenv("STATE_TRANSITION_MODEL", "kubiya/claude-sonnet-4").strip()

        # Get control plane URL for tools
        self.control_plane_url = os.getenv("CONTROL_PLANE_API_URL", "http://localhost:8000")

        logger.info(
            "state_transition_service_initialized",
            model=self.model,
            litellm_api_url=self.litellm_api_url,
            organization_id=organization_id,
        )

    def _create_transition_agent(self) -> Agent:
        """
        Create an Agno agent for state transition decisions

        Returns:
            Configured Agent instance
        """
        # Initialize context tools
        context_tools = ExecutionContextTools(
            base_url=self.control_plane_url,
            organization_id=self.organization_id,
        )

        # Create agent with structured output
        agent = Agent(
            name="State Transition Analyzer",
            role="Expert in analyzing execution states and determining optimal transitions",
            model=LiteLLM(
                id=f"openai/{self.model}",
                api_base=self.litellm_api_url,
                api_key=self.litellm_api_key,
            ),
            output_schema=StateTransitionDecision,
            tools=[context_tools],
            instructions=[
                "You are an expert at analyzing execution states and determining optimal state transitions.",
                "",
                "**Your Task:**",
                "Analyze the execution context and recommend the appropriate next state.",
                "",
                "**Available States:**",
                "1. **completed**: Task is fully done",
                "   - finish_reason = 'stop' or 'end_turn'",
                "   - Response contains completion signals ('done', 'finished', 'completed', 'success')",
                "   - No pending tool calls or error conditions",
                "   - User's intent has been clearly satisfied",
                "   - No follow-up questions or clarifications needed",
                "",
                "2. **waiting_for_input**: Needs user input",
                "   - Asking questions or clarifications",
                "   - Ambiguous requirements need resolution",
                "   - Waiting for approval or feedback",
                "   - finish_reason = 'stop' but task not fully complete",
                "   - Agent explicitly asked user for input",
                "",
                "3. **failed**: Unrecoverable error",
                "   - finish_reason = 'error'",
                "   - Repeated tool failures (>3 consecutive failures)",
                "   - Error message indicates blocker (auth, permissions, not found)",
                "   - Cannot proceed without external intervention",
                "   - Use the check_error_recoverability tool to assess errors",
                "",
                "4. **running**: Continue automatically",
                "   - finish_reason = 'tool_use' (still actively working)",
                "   - Multi-step task in progress",
                "   - No user input needed yet",
                "   - Can make autonomous progress",
                "   - Agent is gathering information or executing tasks",
                "",
                "**Decision Process:**",
                "1. Use get_execution_details() to understand the execution",
                "2. Use get_recent_turns() to see the latest activity",
                "3. Analyze the most recent turn's finish_reason",
                "4. Check if there are errors with check_error_recoverability()",
                "5. Review tool call patterns if needed with get_tool_call_patterns()",
                "6. Make a confident decision based on all context",
                "",
                "**Important Guidelines:**",
                "- Be decisive - don't overthink simple cases",
                "- finish_reason='stop' usually means waiting_for_input or completed",
                "- finish_reason='tool_use' usually means running (continue)",
                "- finish_reason='error' usually means failed (unless recoverable)",
                "- Look for completion signals in the response text",
                "- If the agent asked a question, it's usually waiting_for_input",
                "- If unsure between completed and waiting_for_input, prefer waiting_for_input (safer)",
                "",
                "**Output Requirements:**",
                "- Provide clear, concise reasoning (2-4 sentences)",
                "- Set confidence based on clarity of signals",
                "- Include key decision factors (finish_reason, error status, completion signals, etc.)",
                "- Be specific about why you chose this state",
            ],
            markdown=False,
            add_history_to_context=False,
            retries=2,
        )

        logger.info(
            "state_transition_agent_created",
            model=self.model,
            tools_count=1,
        )

        return agent

    async def analyze_and_transition(
        self,
        execution_id: str,
        turn_number: int,
        turn_data: Any,
    ) -> StateTransitionDecision:
        """
        Analyze execution context and determine state transition

        Args:
            execution_id: The execution ID
            turn_number: The turn number
            turn_data: Turn metrics data

        Returns:
            StateTransitionDecision with recommendation and reasoning
        """
        start_time = time.time()

        try:
            logger.info(
                "analyzing_state_transition",
                execution_id=execution_id,
                turn_number=turn_number,
                finish_reason=turn_data.finish_reason if turn_data else None,
            )

            # Create agent
            agent = self._create_transition_agent()

            # Build analysis prompt
            prompt = self._build_analysis_prompt(execution_id, turn_number, turn_data)

            # Run agent (synchronous run in async wrapper)
            response = await asyncio.to_thread(agent.run, prompt)

            # Extract decision from response
            decision = response.content if isinstance(response.content, StateTransitionDecision) else response.content

            # Calculate decision time
            decision_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "state_transition_decision_made",
                execution_id=execution_id,
                turn_number=turn_number,
                from_state="running",
                to_state=decision.recommended_state,
                confidence=decision.confidence,
                decision_time_ms=decision_time_ms,
            )

            # Record transition in database
            await self._record_transition(
                execution_id=execution_id,
                turn_number=turn_number,
                from_state="running",
                to_state=decision.recommended_state,
                decision=decision,
                decision_time_ms=decision_time_ms,
            )

            # Update execution status
            await self._update_execution_status(
                execution_id=execution_id,
                new_status=decision.recommended_state,
            )

            return decision

        except Exception as e:
            decision_time_ms = int((time.time() - start_time) * 1000)

            logger.error(
                "state_transition_analysis_failed",
                execution_id=execution_id,
                turn_number=turn_number,
                error=str(e),
                decision_time_ms=decision_time_ms,
            )

            raise

    def _build_analysis_prompt(
        self,
        execution_id: str,
        turn_number: int,
        turn_data: Any,
    ) -> str:
        """
        Build the analysis prompt for the AI agent

        Args:
            execution_id: The execution ID
            turn_number: The turn number
            turn_data: Turn metrics data

        Returns:
            Formatted prompt string
        """
        finish_reason = turn_data.finish_reason if turn_data else "unknown"
        error_message = turn_data.error_message if turn_data else None
        response_preview = turn_data.response_preview if turn_data else None
        tools_called = turn_data.tools_called_count if turn_data else 0

        prompt = f"""
# State Transition Analysis Request

## Execution Information
- Execution ID: {execution_id}
- Turn Number: {turn_number}
- Finish Reason: {finish_reason}
- Tools Called This Turn: {tools_called}

## Recent Turn Details
"""

        if response_preview:
            prompt += f"\n**Response Preview:**\n{response_preview[:500]}\n"

        if error_message:
            prompt += f"\n**Error Message:**\n{error_message[:300]}\n"

        prompt += """

## Your Task

Analyze this execution and determine the appropriate next state.

**Steps:**
1. Call get_execution_details() to understand the execution context
2. Call get_recent_turns() to see the recent activity pattern
3. If there's an error, call check_error_recoverability() to assess it
4. Based on all context, recommend the next state with clear reasoning

**Focus on:**
- The finish_reason is a critical signal
- Look for completion indicators in the response
- Check if the agent is asking questions
- Assess error recoverability if present
- Consider if the task can continue autonomously

Be decisive and provide a clear recommendation.
"""

        return prompt

    async def _append_system_message_to_session(
        self,
        execution_id: str,
        to_state: str,
        reasoning: str,
        confidence: str,
        db: Session = None,
    ) -> None:
        """
        Append a system message to the session history about the state transition

        Args:
            execution_id: The execution ID
            to_state: The new state
            reasoning: The AI reasoning for the transition
            confidence: The confidence level
            db: Optional database session (if already open)
        """
        await _append_system_message_to_session_helper(
            db=db,
            execution_id=execution_id,
            to_state=to_state,
            reasoning=reasoning,
            confidence=confidence,
        )

    async def _record_transition(
        self,
        execution_id: str,
        turn_number: int,
        from_state: str,
        to_state: str,
        decision: StateTransitionDecision,
        decision_time_ms: int,
    ) -> None:
        """
        Record state transition in database using SQLAlchemy

        Args:
            execution_id: The execution ID
            turn_number: The turn number
            from_state: The previous state
            to_state: The new state
            decision: The AI decision object
            decision_time_ms: Time taken to make decision
        """
        try:
            # Get database session in async context
            from control_plane_api.app.database import get_session_local
            SessionLocal = get_session_local()
            db = SessionLocal()

            try:
                # Get organization from execution
                execution = db.query(Execution).filter(Execution.id == execution_id).first()

                if not execution:
                    logger.warning("execution_not_found_for_transition", execution_id=execution_id)
                    return

                organization_id = execution.organization_id

                # Create transition record
                transition_record = ExecutionTransition(
                    organization_id=organization_id,
                    execution_id=execution_id,
                    turn_number=turn_number,
                    from_state=from_state,
                    to_state=to_state,
                    reasoning=decision.reasoning,
                    confidence=decision.confidence,
                    decision_factors=decision.decision_factors,
                    ai_model=self.model,
                    decision_time_ms=decision_time_ms,
                    is_manual_override=False,
                )

                db.add(transition_record)
                db.commit()
                db.refresh(transition_record)

                logger.info(
                    "transition_recorded",
                    execution_id=execution_id,
                    turn_number=turn_number,
                    transition_id=str(transition_record.id),
                )

                # Add system message to session history
                await self._append_system_message_to_session(
                    execution_id=execution_id,
                    to_state=to_state,
                    reasoning=decision.reasoning,
                    confidence=decision.confidence,
                    db=db,
                )
            finally:
                db.close()

        except Exception as e:
            logger.error(
                "record_transition_failed",
                execution_id=execution_id,
                error=str(e),
            )
            # Don't raise - recording failure shouldn't block state transition

    async def _update_execution_status(
        self,
        execution_id: str,
        new_status: str,
    ) -> None:
        """
        Update execution status in database using SQLAlchemy

        Args:
            execution_id: The execution ID
            new_status: The new status to set
        """
        try:
            from control_plane_api.app.database import get_session_local
            SessionLocal = get_session_local()
            db = SessionLocal()

            try:
                execution = db.query(Execution).filter(Execution.id == execution_id).first()

                if execution:
                    execution.status = new_status.lower()

                    # Add completed_at if transitioning to completed or failed
                    if new_status in ["completed", "failed"]:
                        execution.completed_at = datetime.now(timezone.utc)

                    db.commit()

                    logger.info(
                        "execution_status_updated",
                        execution_id=execution_id,
                        new_status=new_status,
                    )

                    # Push status event to Redis for live streaming
                    try:
                        from control_plane_api.app.lib.redis_client import get_redis_client
                        import json

                        redis_client = get_redis_client()
                        if redis_client:
                            status_event = {
                                "event_type": "status",
                                "status": new_status.lower(),
                                "execution_id": execution_id,
                                "source": "state_transition_service",
                                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                            }

                            redis_key = f"execution:{execution_id}:events"

                            # Use asyncio.create_task for async Redis push
                            import asyncio
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                asyncio.create_task(redis_client.lpush(redis_key, json.dumps(status_event)))
                            else:
                                loop.run_until_complete(redis_client.lpush(redis_key, json.dumps(status_event)))

                            logger.info(
                                "status_event_pushed_to_redis",
                                execution_id=execution_id,
                                status=new_status,
                            )
                    except Exception as redis_error:
                        logger.warning(
                            "redis_status_push_failed",
                            execution_id=execution_id,
                            status=new_status,
                            error=str(redis_error),
                        )
                        # Don't raise - Redis push failure shouldn't block state transition
                else:
                    logger.warning(
                        "execution_not_found_for_status_update",
                        execution_id=execution_id,
                        new_status=new_status,
                    )
            finally:
                db.close()

        except Exception as e:
            logger.error(
                "update_execution_status_failed",
                execution_id=execution_id,
                new_status=new_status,
                error=str(e),
            )
            # Don't raise - status update failure shouldn't block the transition


async def update_execution_state_safe(
    execution_id: str,
    state: str,
    reasoning: str,
) -> None:
    """
    Safely update execution state with fallback reasoning using SQLAlchemy

    Used when AI decision fails or times out.

    Args:
        execution_id: The execution ID
        state: The state to set
        reasoning: Why this fallback state was chosen
    """
    try:
        from control_plane_api.app.database import get_session_local
        SessionLocal = get_session_local()
        db = SessionLocal()

        try:
            # Get execution
            execution = db.query(Execution).filter(Execution.id == execution_id).first()

            if not execution:
                logger.warning("execution_not_found_for_safe_update", execution_id=execution_id)
                return

            # Update execution status
            execution.status = state.lower()

            if state in ["completed", "failed"]:
                execution.completed_at = datetime.now(timezone.utc)

            db.commit()

            logger.info(
                "fallback_state_update_committed",
                execution_id=execution_id,
                state=state,
            )

            # Push status event to Redis for live streaming
            try:
                from control_plane_api.app.lib.redis_client import get_redis_client
                import json
                import asyncio

                redis_client = get_redis_client()
                if redis_client:
                    status_event = {
                        "event_type": "status",
                        "status": state.lower(),
                        "execution_id": execution_id,
                        "source": "state_transition_fallback",
                        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    }

                    redis_key = f"execution:{execution_id}:events"

                    # Use asyncio for async Redis push
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(redis_client.lpush(redis_key, json.dumps(status_event)))
                    else:
                        loop.run_until_complete(redis_client.lpush(redis_key, json.dumps(status_event)))

                    logger.info(
                        "fallback_status_event_pushed_to_redis",
                        execution_id=execution_id,
                        status=state,
                    )
            except Exception as redis_error:
                logger.warning(
                    "fallback_redis_status_push_failed",
                    execution_id=execution_id,
                    status=state,
                    error=str(redis_error),
                )
                # Don't raise - Redis push failure shouldn't block fallback state transition

            # Record fallback transition
            transition_record = ExecutionTransition(
                organization_id=execution.organization_id,
                execution_id=execution_id,
                turn_number=0,  # Unknown turn number
                from_state="running",
                to_state=state,
                reasoning=f"FALLBACK: {reasoning}",
                confidence="low",
                decision_factors={"fallback": True, "reason": reasoning},
                ai_model="fallback",
                decision_time_ms=0,
                is_manual_override=False,
            )

            db.add(transition_record)
            db.commit()

            # Add system message to session history
            await _append_system_message_to_session_helper(
                db=db,
                execution_id=execution_id,
                to_state=state,
                reasoning=f"FALLBACK: {reasoning}",
                confidence="low",
            )

            logger.info(
                "fallback_state_update",
                execution_id=execution_id,
                state=state,
                reasoning=reasoning,
            )
        finally:
            db.close()

    except Exception as e:
        logger.error(
            "fallback_state_update_failed",
            execution_id=execution_id,
            state=state,
            error=str(e),
        )


async def _append_system_message_to_session_helper(
    db: Session,
    execution_id: str,
    to_state: str,
    reasoning: str,
    confidence: str,
) -> None:
    """
    Helper function to append system message to session using SQLAlchemy (used by fallback too)

    Args:
        db: SQLAlchemy database session
        execution_id: The execution ID
        to_state: The new state
        reasoning: The reasoning for the transition
        confidence: The confidence level
    """
    try:
        # Check if Session model exists, if not skip (sessions may not be migrated yet)
        try:
            from control_plane_api.app.models.session import Session as SessionModel
        except ImportError:
            logger.debug(
                "session_model_not_available",
                execution_id=execution_id,
                note="Skipping session message append - Session model not yet migrated"
            )
            return

        # Get the current session
        session = db.query(SessionModel).filter(SessionModel.execution_id == execution_id).first()

        if not session:
            logger.warning(
                "session_not_found_for_transition_message",
                execution_id=execution_id
            )
            return

        messages = session.messages or []

        # Create system message about the transition
        state_emoji = {
            "completed": "✅",
            "waiting_for_input": "⏸️",
            "failed": "❌",
            "running": "▶️"
        }.get(to_state, "🔄")

        state_display = to_state.replace("_", " ").title()

        system_message = {
            "role": "system",
            "content": f"{state_emoji} **State Transition: {state_display}**\n\n{reasoning}\n\n*Confidence: {confidence}*",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": f"{execution_id}_system_transition_{int(datetime.now(timezone.utc).timestamp() * 1000000)}",
        }

        # Append the system message
        messages.append(system_message)

        # Update the session
        session.messages = messages
        session.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "system_message_appended_to_session",
            execution_id=execution_id,
            to_state=to_state,
        )

    except Exception as e:
        logger.error(
            "append_system_message_failed",
            execution_id=execution_id,
            error=str(e),
        )
        # Don't raise - message failure shouldn't block state transition
