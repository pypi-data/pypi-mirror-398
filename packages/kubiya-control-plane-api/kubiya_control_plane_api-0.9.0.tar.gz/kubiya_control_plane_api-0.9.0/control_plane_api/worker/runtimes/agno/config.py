"""
Configuration builder for Agno runtime.

This module handles:
- LiteLLM API configuration
- Model selection and setup
- Agent configuration
- Environment variable management
"""

import os
import structlog
from typing import Any, Optional, List

from agno.agent import Agent
from agno.models.litellm import LiteLLM
from control_plane_api.worker.services.system_prompt_enhancement import create_default_prompt_builder
from control_plane_api.worker.runtimes.model_utils import get_effective_model, is_model_override_active

# Import LiteLLMLangfuse for proper Langfuse metadata support
try:
    from agno.models.litellm import LiteLLMLangfuse
    LANGFUSE_SUPPORT = True
except ImportError:
    LANGFUSE_SUPPORT = False

logger = structlog.get_logger(__name__)

# Module-level singleton for system prompt enhancement
# NOTE: This is now created per-execution to support dynamic skill context
# _prompt_builder = create_default_prompt_builder()


def build_agno_agent_config(
    agent_id: str,
    system_prompt: Optional[str] = None,
    model_id: Optional[str] = None,
    skills: Optional[List[Any]] = None,
    mcp_tools: Optional[List[Any]] = None,
    tool_hooks: Optional[List[Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    skill_configs: Optional[List[Any]] = None,
) -> Agent:
    """
    Build Agno Agent configuration with LiteLLM.

    Args:
        agent_id: Unique identifier for the agent
        system_prompt: System-level instructions
        model_id: Model identifier (overrides default)
        skills: List of skills/tools available to agent
        mcp_tools: List of MCPTools instances
        tool_hooks: List of tool execution hooks
        user_id: User identifier (email) for Langfuse tracking
        session_id: Session identifier for Langfuse tracking
        organization_id: Organization identifier for Langfuse tracking
        agent_name: Agent name for generation naming
        skill_configs: Original skill configuration dictionaries for prompt enhancement

    Returns:
        Configured Agno Agent instance

    Raises:
        ValueError: If required environment variables are missing
    """
    # Get LiteLLM configuration from environment
    litellm_api_base = os.getenv(
        "LITELLM_API_BASE", "https://llm-proxy.kubiya.ai"
    )
    litellm_api_key = os.getenv("LITELLM_API_KEY")

    if not litellm_api_key:
        raise ValueError("LITELLM_API_KEY environment variable not set")

    # Determine model to use with override support
    # Priority: KUBIYA_MODEL_OVERRIDE > model_id > LITELLM_DEFAULT_MODEL > default
    model = get_effective_model(
        context_model_id=model_id,
        log_context={"agent_id": agent_id},
    )

    logger.info(
        "building_agno_agent_config",
        agent_id=agent_id,
        model=model,
        has_skills=bool(skills),
        has_mcp_tools=bool(mcp_tools),
        mcp_tools_count=len(mcp_tools) if mcp_tools else 0,
        has_tool_hooks=bool(tool_hooks),
    )

    # Build metadata for Langfuse tracking
    # Format: trace_user_id = EMAIL-ORG_NAME, trace_name = "agent-chat" (simple), metadata = {details}
    metadata = {}

    # Always set a simple, consistent trace name
    metadata["trace_name"] = "agent-chat"
    metadata["generation_name"] = "agent-chat"

    if user_id and organization_id:
        # Format: EMAIL-ORG_NAME (EMAIL is the user_id)
        metadata["trace_user_id"] = f"{user_id}-{organization_id}"
        metadata["user_id"] = f"{user_id}-{organization_id}"

    if session_id:
        # Use session_id as trace_id to group all messages in same conversation
        metadata["trace_id"] = session_id
        metadata["session_id"] = session_id

    # Add additional details directly to metadata for Langfuse "Metadata" column
    # Any extra fields not in the standard spec will be saved as metadata
    if agent_id:
        metadata["agent_id"] = agent_id
    if agent_name:
        metadata["agent_name"] = agent_name
    if user_id:
        metadata["user_email"] = user_id
    if organization_id:
        metadata["organization_id"] = organization_id
    if model_id:
        metadata["model"] = model_id

    # DEBUG: Log the complete metadata being sent
    logger.warning(
        "🔍 DEBUG: AGNO RUNTIME - LANGFUSE METADATA",
        metadata=metadata,
        user_id_input=user_id,
        organization_id_input=organization_id,
        agent_name_input=agent_name,
        session_id_input=session_id,
        metadata_json=str(metadata),
    )

    # Create LiteLLM model instance with metadata
    # Use LiteLLMLangfuse for proper Langfuse integration if available
    if LANGFUSE_SUPPORT and metadata:
        logger.warning(
            "🔍 DEBUG: USING LiteLLMLangfuse CLASS FOR LANGFUSE INTEGRATION",
            metadata=metadata,
        )
        litellm_model = LiteLLMLangfuse(
            id=f"openai/{model}",
            api_base=litellm_api_base,
            api_key=litellm_api_key,
            metadata=metadata,
        )
    else:
        logger.warning(
            "🔍 DEBUG: USING STANDARD LiteLLM CLASS (No Langfuse integration)",
            has_metadata=bool(metadata),
            langfuse_available=LANGFUSE_SUPPORT,
            note="Install agno with Langfuse support for proper metadata tracking"
        )
        litellm_model = LiteLLM(
            id=f"openai/{model}",
            api_base=litellm_api_base,
            api_key=litellm_api_key,
            metadata=metadata if metadata else None,
        )

    logger.warning(
        "🔍 DEBUG: LITELLM MODEL CREATED",
        model_class=litellm_model.__class__.__name__,
        model_id=f"openai/{model}",
        api_base=litellm_api_base,
        has_metadata=bool(metadata),
        metadata_keys=list(metadata.keys()) if metadata else [],
    )

    # Combine skills and MCP tools
    all_tools = []
    if skills:
        all_tools.extend(skills)
    if mcp_tools:
        all_tools.extend(mcp_tools)

    # Enhance system prompt with runtime-specific additions
    # Create per-execution prompt builder to support dynamic skill context
    from control_plane_api.worker.services.skill_context_enhancement import (
        SkillContextEnhancement,
    )

    prompt_builder = create_default_prompt_builder()

    # Add skill context enhancement if enabled and skills are configured
    skill_context_enabled = os.getenv("ENABLE_SKILL_CONTEXT_ENHANCEMENT", "true").lower() == "true"
    if skill_context_enabled and skill_configs:
        skill_context_enhancement = SkillContextEnhancement(skill_configs)
        prompt_builder.add_enhancement(skill_context_enhancement)
        logger.info(
            "skill_context_enhancement_enabled",
            skill_count=len(skill_configs),
            agent_id=agent_id,
        )

    enhanced_system_prompt = prompt_builder.build(
        base_prompt=system_prompt,
        runtime_type="agno",
    )

    # Build agent configuration
    agent = Agent(
        name=f"Agent {agent_id}",
        role=enhanced_system_prompt or "You are a helpful AI assistant",
        model=litellm_model,
        tools=all_tools if all_tools else None,
        tool_hooks=tool_hooks if tool_hooks else None,
    )

    return agent


def validate_litellm_config() -> bool:
    """
    Validate LiteLLM configuration is present.

    Returns:
        True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    litellm_api_key = os.getenv("LITELLM_API_KEY")

    if not litellm_api_key:
        raise ValueError(
            "LITELLM_API_KEY environment variable not set. "
            "This is required for Agno runtime to function."
        )

    logger.debug(
        "litellm_config_validated",
        api_base=os.getenv("LITELLM_API_BASE", "https://llm-proxy.kubiya.ai"),
        default_model=os.environ.get("LITELLM_DEFAULT_MODEL", "kubiya/claude-sonnet-4"),
    )

    return True
