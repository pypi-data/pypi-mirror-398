"""Runtime-based execution activities for Temporal workflows.

This module provides activities that use the RuntimeFactory/RuntimeRegistry system
for agent execution, supporting multiple runtimes (Agno/Default, Claude Code, etc.)
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from temporalio import activity
from temporalio.exceptions import ApplicationError
import structlog
import os
import asyncio
import time
import httpx
from types import GeneratorType

from control_plane_api.worker.runtimes.base import (
    RuntimeType,
    RuntimeExecutionContext,
    RuntimeExecutionResult,
)
from control_plane_api.worker.runtimes.factory import RuntimeFactory
from control_plane_api.worker.control_plane_client import get_control_plane_client
from control_plane_api.worker.services.cancellation_manager import CancellationManager
from control_plane_api.worker.services.runtime_analytics import submit_runtime_analytics
from control_plane_api.worker.services.analytics_service import AnalyticsService
from control_plane_api.worker.utils.logging_config import sanitize_value

logger = structlog.get_logger(__name__)


def serialize_tool_output(output: Any, max_length: int = 10000) -> Optional[str]:
    """
    Safely serialize tool output for JSON encoding.

    Handles:
    - Generator objects (consumes and converts to string)
    - Large strings (truncates with indication)
    - None values
    - Other types (converts to string)

    Args:
        output: Tool output to serialize
        max_length: Maximum length for output string (default 10000)

    Returns:
        Serialized string or None
    """
    if output is None:
        return None

    try:
        # Check if it's a generator - consume it first
        if isinstance(output, GeneratorType):
            # Consume generator and join results
            output = ''.join(str(item) for item in output)

        # Convert to string
        output_str = str(output)

        # Truncate if too long
        if len(output_str) > max_length:
            return output_str[:max_length] + f"\n... (truncated, {len(output_str) - max_length} chars omitted)"

        return output_str

    except Exception as e:
        logger.warning("failed_to_serialize_tool_output", error=str(e))
        return f"<Failed to serialize output: {str(e)}>"


def inject_env_vars_into_mcp_servers(
    mcp_servers: Dict[str, Any],
    agent_config: Optional[Dict[str, Any]] = None,
    runtime_config: Optional[Dict[str, Any]] = None,
    control_plane_client: Optional[Any] = None,
    agent_id: Optional[str] = None,
    team_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Inject environment variables into MCP server configurations (runtime-agnostic).

    This ensures MCP servers have access to critical environment variables like:
    - KUBIYA_API_KEY: For API authentication
    - KUBIYA_API_BASE: For API base URL
    - Agent/team-specific environment variables from agent_config
    - Resolved environment (inherited vars, decrypted secrets, integration tokens)

    This function is runtime-agnostic and can be used by any runtime (Default, Claude Code, etc.)

    Args:
        mcp_servers: Dictionary of MCP server configurations
        agent_config: Optional agent configuration with env_vars
        runtime_config: Optional runtime configuration with env vars
        control_plane_client: Optional Control Plane API client for fetching resolved environment
        agent_id: Optional agent ID for fetching agent-specific resolved environment
        team_id: Optional team ID for fetching team-specific resolved environment

    Returns:
        Modified MCP server configurations with injected env vars
    """
    if not mcp_servers:
        return mcp_servers

    # Collect environment variables to inject
    env_vars_to_inject = {}

    # Add Kubiya API credentials from OS environment
    kubiya_api_key = os.environ.get("KUBIYA_API_KEY")
    if kubiya_api_key:
        env_vars_to_inject["KUBIYA_API_KEY"] = kubiya_api_key

    kubiya_api_base = os.environ.get("KUBIYA_API_BASE")
    if kubiya_api_base:
        env_vars_to_inject["KUBIYA_API_BASE"] = kubiya_api_base

    # Layer 2: Fetch RESOLVED environment from Control Plane (includes inherited vars, secrets, tokens)
    if control_plane_client and (agent_id or team_id):
        try:
            resolved_env = {}
            if agent_id:
                logger.info("fetching_resolved_agent_environment", agent_id=agent_id[:8])
                resolved_env = control_plane_client.get_agent_execution_environment(agent_id)
            elif team_id:
                logger.info("fetching_resolved_team_environment", team_id=team_id[:8])
                resolved_env = control_plane_client.get_team_execution_environment(team_id)

            if resolved_env:
                logger.info(
                    "resolved_environment_fetched",
                    entity_type="agent" if agent_id else "team",
                    entity_id=(agent_id or team_id)[:8],
                    env_var_count=len(resolved_env),
                    env_var_keys=list(resolved_env.keys()),
                )
                env_vars_to_inject.update(resolved_env)
            else:
                logger.warning("resolved_environment_empty", entity_id=(agent_id or team_id)[:8])
        except Exception as e:
            logger.error(
                "resolved_environment_fetch_failed",
                entity_id=(agent_id or team_id)[:8] if (agent_id or team_id) else "unknown",
                error=str(e),
                error_type=type(e).__name__,
                fallback_behavior="continuing_with_partial_environment",
                exc_info=True,
            )

    # Add any env vars from agent_config
    if agent_config:
        agent_env_vars = agent_config.get("env_vars", {})
        if agent_env_vars and isinstance(agent_env_vars, dict):
            env_vars_to_inject.update(agent_env_vars)
        elif agent_env_vars:
            logger.warning("agent_config.env_vars is not a dict, skipping", type=type(agent_env_vars).__name__)

    # Also check runtime_config for env vars
    if runtime_config:
        runtime_env_vars = runtime_config.get("env", {})
        if runtime_env_vars and isinstance(runtime_env_vars, dict):
            env_vars_to_inject.update(runtime_env_vars)
        elif runtime_env_vars:
            logger.warning("runtime_config.env is not a dict, skipping", type=type(runtime_env_vars).__name__)

    # ALSO inject collected env vars into runtime_config.env for SDK usage
    # This ensures runtime SDK (Claude Code, Agno) has access to resolved environment
    if runtime_config is not None:
        if "env" not in runtime_config:
            runtime_config["env"] = {}
        # Merge all collected env vars into runtime_config.env (in-place mutation)
        # Note: This happens after we've collected from runtime_config, so we're merging
        # OS env + resolved env + agent_config env + runtime_config env back into runtime_config
        runtime_config["env"].update(env_vars_to_inject)
        logger.debug("updated_runtime_config_env", total_env_count=len(runtime_config["env"]))

    if not env_vars_to_inject:
        logger.debug("No environment variables to inject into MCP servers")
        return mcp_servers

    logger.info(
        "Injecting environment variables into MCP servers",
        server_count=len(mcp_servers),
        env_var_keys=list(env_vars_to_inject.keys()),
    )

    def resolve_template_string(value: str, env_vars: Dict[str, str]) -> str:
        """
        Resolve template variables in a string.
        Replaces {{VAR_NAME}} with the value from env_vars.
        """
        import re
        result = value
        for var_name, var_value in env_vars.items():
            # Match {{VAR_NAME}} patterns
            pattern = r'\{\{' + re.escape(var_name) + r'\}\}'
            result = re.sub(pattern, var_value, result)
        return result

    def resolve_templates_in_dict(data: Any, env_vars: Dict[str, str]) -> Any:
        """
        Recursively resolve template variables in dictionaries, lists, and strings.
        """
        if isinstance(data, dict):
            return {k: resolve_templates_in_dict(v, env_vars) for k, v in data.items()}
        elif isinstance(data, list):
            return [resolve_templates_in_dict(item, env_vars) for item in data]
        elif isinstance(data, str):
            return resolve_template_string(data, env_vars)
        else:
            return data

    # Inject env vars into each MCP server
    modified_servers = {}
    for server_name, server_config in mcp_servers.items():
        try:
            # Handle different MCP server configuration formats
            if hasattr(server_config, 'env'):
                # StdioServerParameters or similar object with env attribute
                if server_config.env is None:
                    server_config.env = {}
                # Merge env vars (don't override existing ones from server config)
                server_config.env = {**env_vars_to_inject, **server_config.env}
                logger.debug(
                    f"Injected env vars into MCP server '{server_name}' (object with env attribute)",
                    env_count=len(server_config.env),
                )
            elif isinstance(server_config, dict):
                # Dictionary-based configuration
                # First, resolve template variables in the entire config
                server_config = resolve_templates_in_dict(server_config, env_vars_to_inject)

                # Then add env vars to the env field
                if 'env' not in server_config:
                    server_config['env'] = {}
                # Merge env vars (don't override existing ones from server config)
                server_config['env'] = {**env_vars_to_inject, **server_config['env']}
                logger.debug(
                    f"Injected env vars and resolved templates in MCP server '{server_name}' (dict config)",
                    env_count=len(server_config['env']),
                )
            else:
                # Unknown format - try to set env attribute directly
                try:
                    if not hasattr(server_config, 'env'):
                        setattr(server_config, 'env', {})
                    server_config.env = {**env_vars_to_inject, **getattr(server_config, 'env', {})}
                    logger.debug(
                        f"Injected env vars into MCP server '{server_name}' (setattr)",
                        env_count=len(server_config.env),
                    )
                except Exception as attr_error:
                    logger.warning(
                        f"Could not inject env vars into MCP server '{server_name}' - unsupported format",
                        server_type=type(server_config).__name__,
                        error=str(attr_error),
                    )

            modified_servers[server_name] = server_config

        except Exception as e:
            logger.error(
                f"Error injecting env vars into MCP server '{server_name}'",
                error=str(e),
                exc_info=True,
            )
            # Keep original server config if injection fails
            modified_servers[server_name] = server_config

    logger.info(
        "✅ Environment variables injected into MCP servers",
        server_count=len(modified_servers),
        env_vars_injected=list(env_vars_to_inject.keys()),
    )

    return modified_servers


@dataclass
class ActivityRuntimeExecuteInput:
    """Input for runtime-based execution activity"""
    execution_id: str
    agent_id: str
    organization_id: str
    prompt: str
    runtime_type: str = "default"  # "default", "claude_code", etc.
    system_prompt: Optional[str] = None
    model_id: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    agent_config: Optional[Dict[str, Any]] = None
    skills: Optional[List[Dict[str, Any]]] = None
    mcp_servers: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None
    user_metadata: Optional[Dict[str, Any]] = None
    runtime_config: Optional[Dict[str, Any]] = None
    stream: bool = False
    conversation_turn: int = 1  # Track turn number for analytics
    user_message_id: Optional[str] = None  # Message ID from workflow signal for deduplication
    user_id: Optional[str] = None  # User who sent the message
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None
    # Enforcement context fields
    user_roles: Optional[List[str]] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    environment: str = "production"
    # NEW: Session ID for client pooling (enables client reuse across followups)
    session_id: Optional[str] = None

    def __post_init__(self):
        if self.model_config is None:
            self.model_config = {}
        if self.agent_config is None:
            self.agent_config = {}
        if self.skills is None:
            self.skills = []
        if self.mcp_servers is None:
            self.mcp_servers = {}
        if self.conversation_history is None:
            self.conversation_history = []
        if self.user_metadata is None:
            self.user_metadata = {}
        if self.runtime_config is None:
            self.runtime_config = {}
        if self.user_roles is None:
            self.user_roles = []


@dataclass
class PublishUserMessageInput:
    """Input for publishing user message to stream"""
    execution_id: str
    prompt: str
    timestamp: str
    message_id: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None


@activity.defn
async def publish_user_message(input: PublishUserMessageInput) -> Dict[str, Any]:
    """
    Publish user message to SSE stream immediately.

    This ensures the user message appears in chronological order in the UI,
    before the assistant response starts streaming.

    Args:
        input: User message details to publish

    Returns:
        Dict with success status
    """
    activity.logger.info(
        "Publishing user message to stream",
        extra={
            "execution_id": input.execution_id,
            "message_id": input.message_id,
            "has_user_metadata": bool(input.user_id),
        }
    )

    try:
        # Get Control Plane client
        control_plane = get_control_plane_client()

        # Initialize event bus (Redis) for real-time streaming
        await control_plane.initialize_event_bus()

        # Publish user message event
        control_plane.publish_event(
            execution_id=input.execution_id,
            event_type="message",
            data={
                "role": "user",
                "content": input.prompt,
                "timestamp": input.timestamp,
                "message_id": input.message_id,
                "user_id": input.user_id,
                "user_name": input.user_name,
                "user_email": input.user_email,
                "user_avatar": input.user_avatar,
            }
        )

        activity.logger.info(
            "✅ User message published to stream",
            extra={
                "execution_id": input.execution_id,
                "message_id": input.message_id,
            }
        )

        return {"success": True, "message_id": input.message_id}

    except Exception as e:
        error_msg = str(e) or repr(e) or "Unknown error publishing user message"
        activity.logger.error(
            "Failed to publish user message",
            extra={
                "execution_id": input.execution_id,
                "error": error_msg,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        # Don't fail the workflow if publishing fails - this is non-critical
        return {"success": False, "error": error_msg}


@activity.defn
async def execute_with_runtime(input: ActivityRuntimeExecuteInput) -> Dict[str, Any]:
    """
    Execute agent using the RuntimeFactory/RuntimeRegistry system.

    This activity:
    1. Creates a runtime based on runtime_type (default, claude_code, etc.)
    2. Builds execution context
    3. Executes (streaming or non-streaming)
    4. Returns results

    Args:
        input: Activity input with execution details and runtime_type

    Returns:
        Dict with response, usage, success flag, etc.
    """
    logger.info(
        "runtime_execution_initializing",
        execution_id=input.execution_id,
        agent_id=input.agent_id,
        organization=input.organization_id,
        runtime_type=input.runtime_type,
        model=input.model_id or 'default',
        stream=input.stream,
        skills_count=len(input.skills),
        mcp_servers_count=len(input.mcp_servers),
        prompt_preview=input.prompt[:100] + "..." if len(input.prompt) > 100 else input.prompt
    )

    activity.logger.info(
        "Executing with Runtime system",
        extra={
            "execution_id": input.execution_id,
            "agent_id": input.agent_id,
            "organization_id": input.organization_id,
            "runtime_type": input.runtime_type,
            "model_id": input.model_id,
            "stream": input.stream,
        }
    )

    try:
        # Track execution start time for analytics
        turn_start_time = time.time()

        # Get Control Plane client and cancellation manager
        control_plane = get_control_plane_client()

        # Initialize event bus (Redis) for real-time streaming
        # This must be called in async context to establish connections
        await control_plane.initialize_event_bus()

        cancellation_manager = CancellationManager()

        # STEP 0: Resolve execution environment (secrets, integrations, env vars)
        # Call Control Plane API to get resolved execution environment
        logger.info("resolving_execution_environment", agent_id=input.agent_id)
        resolved_env_vars = {}
        resolved_mcp_servers = {}

        try:
            # Get Kubiya API token from environment
            kubiya_token = os.environ.get("KUBIYA_API_KEY")
            if not kubiya_token:
                raise ValueError("KUBIYA_API_KEY environment variable not set")

            # Get Control Plane URL
            control_plane_url = os.environ.get("CONTROL_PLANE_URL", "https://control-plane.kubiya.ai")

            # Call Control Plane API to resolve execution environment
            api_url = f"{control_plane_url}/api/v1/execution-environment/agents/{input.agent_id}/resolved/full"

            logger.debug("control_plane_api_call", api_url=api_url)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {kubiya_token}",
                        "Accept": "application/json",
                    }
                )

                if response.status_code == 200:
                    resolved_env = response.json()
                    resolved_env_vars = resolved_env.get("env_vars", {})
                    resolved_mcp_servers = resolved_env.get("mcp_servers", {})

                    logger.info(
                        "execution_environment_resolved",
                        env_var_count=len(resolved_env_vars),
                        mcp_server_count=len(resolved_mcp_servers)
                    )

                    logger.debug(
                        "resolved_env_var_keys",
                        env_var_keys=list(resolved_env_vars.keys())
                    )

                    logger.debug(
                        "resolved_mcp_server_names",
                        mcp_server_names=list(resolved_mcp_servers.keys())
                    )

                    # Log detailed env var info at DEBUG level with sanitization
                    for key, value in resolved_env_vars.items():
                        logger.debug(
                            "env_var_detail",
                            key=key,
                            value=sanitize_value(key, value),
                            value_length=len(str(value))
                        )

                    activity.logger.info(
                        "execution_environment_resolved_from_api",
                        extra={
                            "execution_id": input.execution_id,
                            "agent_id": input.agent_id,
                            "env_var_count": len(resolved_env_vars),
                            "mcp_server_count": len(resolved_mcp_servers),
                        }
                    )
                else:
                    logger.warning(
                        "execution_environment_api_error",
                        status_code=response.status_code,
                        error_preview=response.text[:200]
                    )
                    activity.logger.warning(
                        "execution_environment_api_error",
                        extra={
                            "execution_id": input.execution_id,
                            "status_code": response.status_code,
                            "error": response.text[:500],
                        }
                    )

        except Exception as e:
            logger.error("execution_environment_resolution_error", error=str(e))
            activity.logger.error(
                "execution_environment_resolution_error",
                extra={
                    "execution_id": input.execution_id,
                    "agent_id": input.agent_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            # Continue with empty env vars - don't fail execution

        # Initialize analytics service for submission
        analytics_service = AnalyticsService(
            control_plane_url=control_plane.base_url if hasattr(control_plane, 'base_url') else "http://localhost:8000",
            api_key=os.environ.get("KUBIYA_API_KEY", ""),
        )

        # Parse runtime type
        try:
            runtime_type_enum = RuntimeType(input.runtime_type)
        except ValueError:
            logger.error(f"Invalid runtime_type: {input.runtime_type}, falling back to DEFAULT")
            runtime_type_enum = RuntimeType.DEFAULT

        # Create runtime using factory
        factory = RuntimeFactory()
        runtime = factory.create_runtime(
            runtime_type=runtime_type_enum,
            control_plane_client=control_plane,
            cancellation_manager=cancellation_manager,
        )

        logger.info(
            f"Created runtime",
            extra={
                "runtime_type": runtime_type_enum,
                "runtime_class": runtime.__class__.__name__,
                "capabilities": runtime.get_capabilities(),
            }
        )

        # Fetch and instantiate skills if runtime supports tools
        skills = input.skills or []
        if runtime.supports_tools():
            logger.info("fetching_skills_from_control_plane", agent_id=input.agent_id)
            try:
                skill_configs = control_plane.get_skills(input.agent_id)
                if skill_configs:
                    logger.info(
                        "skills_resolved",
                        skill_count=len(skill_configs),
                        types=[t.get('type') for t in skill_configs],
                        names=[t.get('name') for t in skill_configs],
                        enabled=[t.get('enabled', True) for t in skill_configs]
                    )

                    # DEBUG: Show full config for workflow_executor skills
                    for cfg in skill_configs:
                        if cfg.get('type') in ['workflow_executor', 'workflow']:
                            logger.debug(
                                "workflow_executor_skill_config",
                                name=cfg.get('name'),
                                type=cfg.get('type'),
                                enabled=cfg.get('enabled', True),
                                config_keys=list(cfg.get('configuration', {}).keys())
                            )

                    # Import here to avoid circular dependency
                    from control_plane_api.worker.services.skill_factory import SkillFactory

                    logger.debug(
                        "before_skill_factory",
                        execution_id=input.execution_id,
                        execution_id_type=type(input.execution_id).__name__,
                        execution_id_bool=bool(input.execution_id),
                        skill_configs_count=len(skill_configs)
                    )

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
                            logger.info("auto_included_builtin_skill", skill_type=builtin_type)

                    # Determine runtime type from agent config or input
                    runtime_type = (input.agent_config or {}).get("runtime", input.runtime_type or "agno")

                    # Instantiate skills for all runtimes
                    # For Claude Code: custom skills will be converted to MCP servers by build_mcp_servers()
                    # For other runtimes: skills are used directly
                    skill_factory = SkillFactory(runtime_type=runtime_type)
                    skill_factory.initialize()

                    skills = skill_factory.create_skills_from_list(
                        skill_configs,
                        execution_id=input.execution_id  # Pass execution_id for control plane streaming
                    )

                    if skills:
                        skill_types = [type(s).__name__ for s in skills]
                        logger.info(
                            "skills_instantiated",
                            skill_count=len(skills),
                            runtime_type=runtime_type,
                            skill_classes=skill_types
                        )
                    else:
                        logger.warning("no_skills_instantiated", runtime_type=runtime_type)
                else:
                    logger.warning("no_skills_found", message="Using built-in skills only")

                    # Still include built-in skills even when no skills configured
                    from control_plane_api.worker.services.skill_factory import SkillFactory

                    builtin_skill_configs = [
                        {
                            'name': 'context_graph_search',
                            'type': 'context_graph_search',
                            'enabled': True,
                            'configuration': {}
                        }
                    ]

                    runtime_type = (input.agent_config or {}).get("runtime", input.runtime_type or "agno")

                    # Instantiate builtin skills for ALL runtimes (including Claude Code)
                    # For Claude Code, these Toolkit objects will be converted to MCP servers by build_mcp_servers()
                    skill_factory = SkillFactory(runtime_type=runtime_type)
                    skill_factory.initialize()
                    skills = skill_factory.create_skills_from_list(
                        builtin_skill_configs,
                        execution_id=input.execution_id
                    )

                    if skills:
                        skill_types = [type(s).__name__ if hasattr(s, '__name__') else s.get('type', 'unknown') for s in skills]
                        logger.info(
                            "builtin_skills_instantiated",
                            skill_count=len(skills),
                            runtime_type=runtime_type,
                            skill_types=skill_types
                        )
            except Exception as e:
                logger.error("skill_fetch_error", error=str(e), exc_info=True)

        # Merge MCP servers: resolved_mcp_servers (from DB with templates resolved) + input.mcp_servers (from workflow)
        # Input MCP servers override resolved ones (allows runtime overrides)
        merged_mcp_servers = {**resolved_mcp_servers, **(input.mcp_servers or {})}

        logger.info(
            "mcp_servers_merged",
            from_execution_env=len(resolved_mcp_servers),
            from_workflow_input=len(input.mcp_servers) if input.mcp_servers else 0,
            total_merged=len(merged_mcp_servers),
            server_names=list(merged_mcp_servers.keys()) if merged_mcp_servers else []
        )

        # Inject environment variables into MCP servers (runtime-agnostic)
        # This ensures all MCP servers have access to KUBIYA_API_KEY, KUBIYA_API_BASE, etc.
        # Also includes resolved_env_vars from execution environment (secrets, integrations)
        agent_config_with_env = {
            **(input.agent_config or {}),
            "env_vars": {
                **resolved_env_vars,  # Include resolved secrets/integrations
                **(input.agent_config or {}).get("env_vars", {}),  # Override with explicit agent config
            }
        }

        mcp_servers_with_env = inject_env_vars_into_mcp_servers(
            mcp_servers=merged_mcp_servers,
            agent_config=agent_config_with_env,
            runtime_config=input.runtime_config,
        )

        # Enrich user_metadata with additional fields for Langfuse tracking
        enriched_user_metadata = dict(input.user_metadata or {})

        # Add user_email if provided separately
        if input.user_email and "user_email" not in enriched_user_metadata:
            enriched_user_metadata["user_email"] = input.user_email

        # Add user_id if provided separately
        if input.user_id and "user_id" not in enriched_user_metadata:
            enriched_user_metadata["user_id"] = input.user_id

        # Add user_name if provided separately
        if input.user_name and "user_name" not in enriched_user_metadata:
            enriched_user_metadata["user_name"] = input.user_name

        # Add session_id from runtime_config
        if input.runtime_config and "session_id" in input.runtime_config:
            enriched_user_metadata["session_id"] = input.runtime_config["session_id"]
        elif "session_id" not in enriched_user_metadata:
            # Default to execution_id for session tracking
            enriched_user_metadata["session_id"] = input.execution_id

        # Add agent_name if not already present (for generation_name in Langfuse)
        if "agent_name" not in enriched_user_metadata:
            # Try to get from agent_config or use agent_id
            if input.agent_config and "name" in input.agent_config:
                enriched_user_metadata["agent_name"] = input.agent_config["name"]
            else:
                enriched_user_metadata["agent_name"] = input.agent_id

        logger.info(
            "Enriched user_metadata for Langfuse tracking",
            extra={
                "execution_id": input.execution_id,
                "has_user_email": "user_email" in enriched_user_metadata,
                "has_session_id": "session_id" in enriched_user_metadata,
                "has_agent_name": "agent_name" in enriched_user_metadata,
            }
        )

        # Build runtime config with resolved environment variables and session_id
        # This includes secrets, integrations, custom env vars, and session_id for client pooling
        runtime_config_with_env = {
            **(input.runtime_config or {}),
            "env": {
                **resolved_env_vars,  # Secrets, integrations, custom env vars
                **(input.runtime_config or {}).get("env", {}),  # Override with explicit runtime config
            },
            # NEW: Pass session_id for client pooling (enables reuse across followups)
            "session_id": input.session_id or input.execution_id,  # Fallback to execution_id
        }

        logger.info(
            "runtime_config_session_id",
            session_id=(input.session_id or input.execution_id)[:16],
            execution_id=input.execution_id[:16],
            is_reuse_enabled=bool(input.session_id),
            note="Session ID enables client reuse for followup messages"
        )

        env_vars = runtime_config_with_env.get('env', {})
        logger.info(
            "environment_variables_passed_to_runtime",
            total_env_vars=len(env_vars),
            env_var_keys=list(env_vars.keys())
        )

        # Log detailed env var info at DEBUG level with sanitization
        for key, value in env_vars.items():
            logger.debug(
                "runtime_env_var_detail",
                key=key,
                value=sanitize_value(key, str(value)),
                value_length=len(str(value))
            )

        # Create execution workspace
        from control_plane_api.worker.utils.workspace_manager import ensure_workspace

        workspace_path = None
        try:
            workspace_path = ensure_workspace(input.execution_id)

            logger.info(
                "execution_workspace_created",
                execution_id=input.execution_id[:8] if len(input.execution_id) >= 8 else input.execution_id,
                path=str(workspace_path) if workspace_path else None,
            )
        except Exception as e:
            logger.warning(
                "execution_workspace_creation_failed",
                execution_id=input.execution_id[:8] if len(input.execution_id) >= 8 else input.execution_id,
                error=str(e),
                error_type=type(e).__name__,
                fallback="skills_and_runtime_will_use_defaults",
            )

        # Build execution context
        context = RuntimeExecutionContext(
            execution_id=input.execution_id,
            agent_id=input.agent_id,
            organization_id=input.organization_id,
            prompt=input.prompt,
            system_prompt=input.system_prompt,
            conversation_history=input.conversation_history,
            model_id=input.model_id,
            model_config=input.model_config,
            agent_config=input.agent_config,
            skills=skills,  # Use fetched skills
            mcp_servers=mcp_servers_with_env,  # Use MCP servers with injected env vars
            user_metadata=enriched_user_metadata,  # Use enriched metadata
            runtime_config=runtime_config_with_env,  # Include resolved env vars!
            runtime_type=runtime_type_enum,  # Runtime type for validation
            # Enforcement context
            user_email=input.user_email,
            user_id=input.user_id,
            user_roles=input.user_roles or [],
            team_id=input.team_id,
            team_name=input.team_name,
            environment=input.environment,
            workspace_directory=str(workspace_path) if workspace_path else None,
        )

        # Execute based on streaming preference
        if input.stream:
            # Streaming execution
            logger.info(
                "🎬 Starting streaming execution",
                execution_id=input.execution_id,
                agent_id=input.agent_id
            )
            accumulated_response = ""
            final_result = None

            # Generate unique message ID for this turn (execution_id + timestamp)
            message_id = f"{input.execution_id}_{int(time.time() * 1000000)}"

            # Track tool events published
            tool_events_published = {"start": 0, "complete": 0}

            # Define event callback for publishing tool events to Control Plane
            def event_callback(event: Dict):
                """Callback to publish events (tool start/complete, content chunks) to Control Plane SSE"""
                event_type = event.get("type")

                if event_type == "content_chunk":
                    # Content chunks are already handled below via result.response
                    pass
                elif event_type == "tool_start":
                    # Publish tool start event (synchronous - this runs in async context via callback)
                    try:
                        logger.info(
                            "tool_start_event",
                            tool_name=event.get('tool_name'),
                            tool_execution_id=event.get('tool_execution_id')
                        )
                        control_plane.publish_event(
                            execution_id=input.execution_id,
                            event_type="tool_started",  # Match default runtime event type
                            data={
                                "tool_name": event.get("tool_name"),
                                "tool_execution_id": event.get("tool_execution_id"),
                                "tool_arguments": event.get("tool_args", {}),
                                "message": f"🔧 Executing tool: {event.get('tool_name')}",
                                "source": "agent",
                            }
                        )
                        tool_events_published["start"] += 1
                        logger.debug(
                            "tool_started_event_published",
                            event_number=tool_events_published['start'],
                            tool_name=event.get('tool_name')
                        )
                    except Exception as e:
                        logger.error("tool_start_event_publish_failed", error=str(e), exc_info=True)
                elif event_type == "tool_complete":
                    # Publish tool complete event
                    try:
                        status = event.get("status", "success")
                        logger.info(
                            "tool_complete_event",
                            tool_name=event.get('tool_name'),
                            status=status
                        )
                        control_plane.publish_event(
                            execution_id=input.execution_id,
                            event_type="tool_completed",  # Match default runtime event type
                            data={
                                "tool_name": event.get("tool_name"),
                                "tool_execution_id": event.get("tool_execution_id"),
                                "status": status,
                                "tool_output": serialize_tool_output(event.get("output")),  # Safely serialize output (handles generators)
                                "tool_error": event.get("error"),
                                "message": f"Tool {status}: {event.get('tool_name')}",
                                "source": "agent",
                            }
                        )
                        tool_events_published["complete"] += 1
                        logger.debug(
                            "tool_completed_event_published",
                            event_number=tool_events_published['complete'],
                            tool_name=event.get('tool_name')
                        )
                    except Exception as e:
                        logger.error("tool_complete_event_publish_failed", error=str(e), exc_info=True)

            # Stream execution with event callback
            # Note: AgnoRuntime publishes chunks via EventPublisher internally
            # But ClaudeCodeRuntime needs us to publish chunks here
            is_agno_runtime = runtime_type_enum == RuntimeType.DEFAULT

            # Track last heartbeat time for periodic heartbeats during streaming
            last_heartbeat = time.time()
            chunk_count = 0

            async for result in runtime.stream_execute(context, event_callback):
                # Only process non-empty content (filter out empty strings and whitespace)
                if result.response and result.response.strip():
                    accumulated_response += result.response
                    chunk_count += 1

                    # Publish chunks for non-Agno runtimes (e.g., Claude Code)
                    # AgnoRuntime publishes internally via EventPublisher to avoid duplicates
                    if not is_agno_runtime:
                        try:
                            await control_plane.publish_event_async(
                                execution_id=input.execution_id,
                                event_type="message_chunk",
                                data={
                                    "role": "assistant",
                                    "content": result.response,
                                    "is_chunk": True,
                                    "message_id": message_id,
                                }
                            )
                        except Exception as e:
                            logger.warning(f"Failed to publish streaming chunk: {e}")

                # Send heartbeat every 10 seconds or every 50 chunks to detect hung executions
                current_time = time.time()
                if current_time - last_heartbeat > 10 or chunk_count % 50 == 0:
                    activity.heartbeat({
                        "status": "streaming",
                        "chunks_received": chunk_count,
                        "response_length": len(accumulated_response),
                        "elapsed_seconds": int(current_time - last_heartbeat)
                    })
                    last_heartbeat = current_time

                if result.finish_reason:
                    final_result = result
                    break

            if not final_result:
                raise RuntimeError("Streaming execution did not provide final result")

            # Log tool event summary
            logger.info(
                "tool_events_summary",
                tool_started_events=tool_events_published['start'],
                tool_completed_events=tool_events_published['complete'],
                tool_messages_in_result=len(final_result.tool_messages or [])
            )

            # Analytics now handled by separate Temporal activity in workflow
            # See: workflow calls submit_runtime_analytics_activity after this returns

            # Log before return to verify we reach this point
            logger.info(
                "activity_about_to_return_streaming",
                execution_id=input.execution_id,
                turn_number=input.conversation_turn,
                note="About to return streaming activity result to Temporal"
            )

            return {
                "success": final_result.success,
                "response": accumulated_response,
                "usage": final_result.usage or {},
                "model": final_result.model,
                "finish_reason": final_result.finish_reason,
                "tool_messages": final_result.tool_messages or [],
                "metadata": final_result.metadata or {},
                "error": final_result.error,
            }

        else:
            # Non-streaming execution
            logger.info(
                "🎬 Starting non-streaming execution",
                execution_id=input.execution_id,
                agent_id=input.agent_id
            )
            result = await runtime.execute(context)

            # Analytics now handled by separate Temporal activity in workflow
            # See: workflow calls submit_runtime_analytics_activity after this returns

            # Log before return to verify we reach this point
            logger.info(
                "activity_about_to_return_non_streaming",
                execution_id=input.execution_id,
                turn_number=input.conversation_turn,
                note="About to return non-streaming activity result to Temporal"
            )

            return {
                "success": result.success,
                "response": result.response,
                "usage": result.usage or {},
                "model": result.model,
                "finish_reason": result.finish_reason,
                "tool_messages": result.tool_messages or [],
                "metadata": result.metadata or {},
                "error": result.error,
            }

    except asyncio.CancelledError as e:
        # DURABILITY FIX: Handle activity-level cancellation gracefully
        # This catches cancellations from Temporal (workflow cancellation, activity timeout, etc.)
        logger.warning(
            "Activity execution cancelled by Temporal",
            extra={
                "execution_id": input.execution_id,
                "runtime_type": input.runtime_type,
                "conversation_turn": input.conversation_turn,
            },
        )

        # Return a partial result instead of failing
        # This allows the workflow to handle the interruption and potentially resume
        return {
            "success": False,  # Mark as failure since we couldn't complete
            "response": "",
            "usage": {},
            "model": input.model_id,
            "finish_reason": "cancelled",
            "tool_messages": [],
            "metadata": {
                "interrupted": True,
                "can_resume": False,  # Activity-level cancellation can't resume easily
                "cancellation_source": "temporal_activity",
            },
            "error": "Execution was cancelled by Temporal",
        }

    except Exception as e:
        # Ensure error message is never empty
        error_msg = str(e) or repr(e) or f"{type(e).__name__}: No error details available"

        logger.error(
            "Runtime execution failed",
            extra={
                "execution_id": input.execution_id,
                "runtime_type": input.runtime_type,
                "error": error_msg,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )

        # Publish error event to Control Plane for real-time UI updates
        try:
            from control_plane_api.worker.utils.error_publisher import (
                ErrorEventPublisher, ErrorSeverity, ErrorCategory
            )

            error_publisher = ErrorEventPublisher(control_plane)

            # Determine error category based on error message
            error_str = error_msg.lower()
            category = ErrorCategory.UNKNOWN
            if "timeout" in error_str:
                category = ErrorCategory.TIMEOUT
            elif "import" in error_str or "module" in error_str:
                category = ErrorCategory.RUNTIME_INIT
            elif "api" in error_str or "model" in error_str or "anthropic" in error_str:
                category = ErrorCategory.MODEL_ERROR
            elif "network" in error_str or "connection" in error_str:
                category = ErrorCategory.NETWORK
            elif "auth" in error_str or "credential" in error_str:
                category = ErrorCategory.AUTHENTICATION

            await error_publisher.publish_error(
                execution_id=input.execution_id,
                exception=e,
                severity=ErrorSeverity.CRITICAL,
                category=category,
                stage="execution",
                component=f"{input.runtime_type}_runtime",
                operation="agent_execution",
                metadata={
                    "agent_id": input.agent_id,
                    "model_id": input.model_id,
                    "conversation_turn": input.conversation_turn,
                }
            )
        except Exception as publish_error:
            # Never let error publishing break the main flow
            logger.warning(
                "failed_to_publish_error_event",
                error=str(publish_error)
            )

        # Raise ApplicationError so Temporal marks the workflow as FAILED
        raise ApplicationError(
            f"Runtime execution failed: {error_msg}",
            non_retryable=False,  # Allow retries per retry policy
            type=type(e).__name__
        )
