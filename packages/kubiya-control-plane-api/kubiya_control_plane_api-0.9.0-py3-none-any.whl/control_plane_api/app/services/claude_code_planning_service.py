"""
Claude Code Planning Strategy - Uses claude-agent-sdk with LiteLLM proxy via ANTHROPIC_BASE_URL
"""

from typing import Dict, Any, AsyncIterator
import structlog
import os
import json

from control_plane_api.app.services.planning_strategy import PlanningStrategy
from control_plane_api.app.models.task_planning import TaskPlanResponse

logger = structlog.get_logger(__name__)

try:
    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    _SDK_AVAILABLE = True
except ImportError as e:
    _SDK_AVAILABLE = False
    _SDK_ERROR = str(e)


class ClaudeCodePlanningStrategy(PlanningStrategy):
    """
    Claude Agent SDK with LiteLLM proxy support.
    
    Uses ANTHROPIC_BASE_URL to route requests through LiteLLM proxy.
    Dynamic JSON schema from Pydantic model (auto-updates when model changes).
    """

    @property  
    def name(self) -> str:
        return "claude_code_sdk"

    def __init__(self, db=None, organization_id=None, api_token=None):
        super().__init__(db, organization_id, api_token)
        
        self.litellm_api_base = (os.getenv("LITELLM_API_URL") or os.getenv("LITELLM_API_BASE") or "https://llm-proxy.kubiya.ai").strip()
        self.litellm_api_key = os.getenv("LITELLM_API_KEY", "").strip()
        self.model = os.getenv("LITELLM_DEFAULT_MODEL", "kubiya/claude-sonnet-4").strip()
        
        if not self.litellm_api_key:
            raise ValueError("LITELLM_API_KEY not set")
        
        # Get JSON schema from Pydantic model (DYNAMIC!)
        json_schema = TaskPlanResponse.model_json_schema()
        
        # Build system prompt with embedded schema
        self.system_prompt = f"""You are a fast, efficient task planning agent.

You MUST return ONLY a valid JSON object matching this EXACT schema:

{json.dumps(json_schema, indent=2)}

CRITICAL RULES:
- Return ONLY the JSON object
- NO markdown, NO explanations, NO code blocks
- Follow schema field names and types EXACTLY
- All required fields must be present
"""
        
        logger.info("claude_code_strategy_init", model=self.model, litellm_base=self.litellm_api_base)

    async def plan_task(self, planning_prompt: str) -> TaskPlanResponse:
        """Generate plan using claude-agent-sdk through LiteLLM proxy"""
        if not _SDK_AVAILABLE:
            raise ImportError(
                "claude-agent-sdk not available. "
                "This strategy requires the Claude Code CLI binary which is not available in serverless environments. "
                "Set PLANNING_STRATEGY=agno to use the serverless-compatible Agno strategy. "
                f"Original error: {_SDK_ERROR}"
            )

        # Configure to use LiteLLM proxy via ANTHROPIC_BASE_URL
        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=self.system_prompt,
            permission_mode="plan",  # Use plan mode for better control
            env={
                "ANTHROPIC_API_KEY": self.litellm_api_key,  # LiteLLM key
                "ANTHROPIC_BASE_URL": self.litellm_api_base  # Point to LiteLLM proxy!
            }
        )
        
        client = ClaudeSDKClient(options=options)
        
        try:
            await client.connect()
            await client.query(planning_prompt)
            
            response_text = ""
            async for message in client.receive_response():
                if hasattr(message, "content"):
                    for block in message.content:
                        if hasattr(block, "text"):
                            response_text += block.text
                
                if message.__class__.__name__ == "ResultMessage":
                    break
            
            response_text = response_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            plan_dict = json.loads(response_text)
            return TaskPlanResponse(**plan_dict)
            
        finally:
            try:
                await client.disconnect()
            except:
                pass

    async def plan_task_stream(self, planning_prompt: str) -> AsyncIterator[Dict[str, Any]]:
        """Generate plan with streaming through LiteLLM proxy"""
        if not _SDK_AVAILABLE:
            yield {
                "event": "error",
                "data": {
                    "message": f"claude-agent-sdk not available. This strategy requires the Claude Code CLI binary "
                               f"which is not available in serverless environments. Set PLANNING_STRATEGY=agno to use "
                               f"the serverless-compatible Agno strategy. Original error: {_SDK_ERROR}"
                }
            }
            return

        try:
            # Configure claude-agent-sdk to use LiteLLM proxy
            options = ClaudeAgentOptions(
                model=self.model,
                system_prompt=self.system_prompt,
                permission_mode="plan",  # Use plan mode for better control
                env={
                    "ANTHROPIC_API_KEY": self.litellm_api_key,
                    "ANTHROPIC_BASE_URL": self.litellm_api_base  # LiteLLM proxy!
                }
            )
            
            client = ClaudeSDKClient(options=options)
            await client.connect()
            await client.query(planning_prompt)
            
            response_text = ""
            async for message in client.receive_messages():
                if hasattr(message, "content"):
                    for block in message.content:
                        # Handle text blocks
                        if hasattr(block, "text"):
                            text = block.text
                            response_text += text

                            if len(text.strip()) > 20:
                                yield {"event": "thinking", "data": {"content": text[:300], "message": "💭 Analyzing..."}}

                        # Handle tool use blocks (TodoWrite, ExitPlanMode, etc.)
                        elif hasattr(block, "name") and hasattr(block, "input"):
                            tool_name = block.name
                            tool_input = block.input if isinstance(block.input, dict) else {}

                            # Capture TodoWrite tool for todo list updates
                            if tool_name == "TodoWrite":
                                todos = tool_input.get("todos", [])
                                if todos:
                                    yield {
                                        "event": "todo_update",
                                        "data": {
                                            "todos": todos,
                                            "total": len(todos),
                                            "pending": sum(1 for t in todos if t.get("status") == "pending"),
                                            "in_progress": sum(1 for t in todos if t.get("status") == "in_progress"),
                                            "completed": sum(1 for t in todos if t.get("status") == "completed"),
                                            "message": "📝 Planning tasks..."
                                        }
                                    }

                            # Capture ExitPlanMode for plan approval
                            elif tool_name == "ExitPlanMode":
                                plan_text = tool_input.get("plan", "")
                                if plan_text:
                                    yield {
                                        "event": "plan_mode_exit",
                                        "data": {
                                            "plan": plan_text,
                                            "message": "📋 Plan ready for approval"
                                        }
                                    }

                if message.__class__.__name__ == "ResultMessage":
                    break
            
            yield {"event": "progress", "data": {"stage": "finalizing", "message": "💰 Finalizing...", "progress": 90}}
            
            response_text = response_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            plan_dict = json.loads(response_text)
            plan = TaskPlanResponse(**plan_dict)
            
            yield {"event": "complete", "data": {"plan": plan.model_dump(), "progress": 100, "message": "✅ Plan ready!"}}
            
        except Exception as e:
            logger.error("claude_stream_error", error=str(e), exc_info=True)
            yield {"event": "error", "data": {"message": f"Planning failed: {str(e)}"}}
        finally:
            try:
                await client.disconnect()
            except:
                pass