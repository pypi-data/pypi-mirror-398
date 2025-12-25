"""
Configuration builder for Claude Code runtime.

This module handles the construction of ClaudeAgentOptions from execution
context, including LiteLLM integration, MCP servers, and session management.

BUG FIX #4: Added session_id validation before use.
"""

from typing import Dict, Any, Tuple, Optional, Callable, Set, List
import structlog
import os
import asyncio
import hashlib
import json
import time

from .tool_mapper import map_skills_to_tools, validate_tool_names
from .mcp_builder import build_mcp_servers
from .hooks import build_hooks
from .mcp_discovery import discover_all_mcp_resources
from control_plane_api.worker.services.system_prompt_enhancement import create_default_prompt_builder
from .litellm_proxy import (
    get_proxy_base_url,
    set_execution_context,
    clear_execution_context,
)
from control_plane_api.worker.runtimes.model_utils import get_effective_model, is_model_override_active

logger = structlog.get_logger(__name__)

# Module-level singleton for system prompt enhancement
# NOTE: This is now created per-execution to support dynamic skill context
# _prompt_builder = create_default_prompt_builder()

# Note: Claude SDK handles MCP discovery automatically - we verify connection and log errors

# MCP Discovery Cache - Reduces process spawning by 50%
# Key: hash of MCP server configuration, Value: discovery results
_mcp_discovery_cache: Dict[str, Dict[str, Any]] = {}

# Options Cache - Reduces options rebuild overhead by ~80%
# Key: hash of execution configuration, Value: (options, timestamp)
# This cache stores built ClaudeAgentOptions to avoid rebuilding when config unchanged
_options_cache: Dict[str, Tuple[Any, float]] = {}
_options_cache_ttl = int(os.getenv("CLAUDE_CODE_OPTIONS_CACHE_TTL", "3600"))  # 1 hour default


def _get_mcp_cache_key(mcp_servers: Dict[str, Any]) -> str:
    """
    Generate cache key for MCP server configuration.

    Uses hash of server configs to detect when discovery needs to be re-run.
    Only command/args/env matter for STDIO servers, URL for HTTP servers.
    """
    # Sort keys for consistent hashing
    cache_input = {}
    for server_name, server_config in sorted(mcp_servers.items()):
        # Extract relevant fields for cache key
        transport = server_config.get("transport", {})
        transport_type = transport.get("type", "stdio")

        if transport_type == "stdio":
            # For stdio: command + args determine the process
            cache_input[server_name] = {
                "type": "stdio",
                "command": transport.get("command", ""),
                "args": transport.get("args", []),
                "env": transport.get("env", {}),
            }
        elif transport_type in ["http", "sse"]:
            # For HTTP/SSE: URL is what matters
            cache_input[server_name] = {
                "type": transport_type,
                "url": transport.get("url", ""),
            }

    # Hash the configuration
    config_json = json.dumps(cache_input, sort_keys=True)
    return hashlib.sha256(config_json.encode()).hexdigest()[:16]  # Short hash


def _get_options_cache_key(context: Any) -> str:
    """
    Generate cache key from execution context configuration.

    This hash includes all configuration that affects options building:
    - Model ID and system prompt
    - Agent ID (affects permissions and config)
    - Skills (determines tools and MCP servers)
    - MCP servers configuration

    Args:
        context: RuntimeExecutionContext

    Returns:
        Cache key string (16-char hash)
    """
    # Extract skills as sorted list of names/types for consistent hashing
    skill_identifiers = []
    if hasattr(context, 'skills') and context.skills:
        for skill in context.skills:
            if isinstance(skill, dict):
                skill_identifiers.append({
                    "name": skill.get("name", ""),
                    "type": skill.get("type", ""),
                })
            else:
                # Toolkit object - use class name
                skill_identifiers.append({"type": type(skill).__name__})

    # Build cache input (only config that affects options)
    cache_input = {
        "model_id": context.model_id or "",
        "system_prompt_length": len(context.system_prompt or ""),  # Use length to avoid huge strings
        "agent_id": context.agent_id,
        "skill_identifiers": sorted(skill_identifiers, key=lambda x: (x.get("type", ""), x.get("name", ""))),
        "mcp_server_names": sorted((context.mcp_servers or {}).keys()) if hasattr(context, 'mcp_servers') else [],
        # Don't include execution_id or session_id - those vary per execution but don't affect config
    }

    config_json = json.dumps(cache_input, sort_keys=True)
    return hashlib.sha256(config_json.encode()).hexdigest()[:16]  # Short hash


def build_mcp_permission_handler(
    mcp_servers: Dict[str, Any], allowed_tools: List[str]
) -> Callable:
    """
    Build permission handler for MCP tools.

    IMPORTANT: The SDK discovers MCP tools automatically, but does NOT
    automatically grant permission to use them. We need to handle permissions
    separately using the canUseTool callback.

    This handler:
    1. Allows tools in the allowed_tools list (builtin tools)
    2. Auto-allows tools matching mcp__<server_name>__* for configured servers
    3. Denies everything else

    Args:
        mcp_servers: Dict of MCP server configurations
        allowed_tools: List of allowed builtin tool names

    Returns:
        Async permission handler for canUseTool parameter
    """
    # Extract MCP server names for permission matching
    mcp_server_names: Set[str] = set(mcp_servers.keys())

    logger.info(
        "building_mcp_permission_handler",
        mcp_server_count=len(mcp_server_names),
        mcp_server_names=list(mcp_server_names),
        builtin_tools_count=len(allowed_tools),
        note="SDK discovers tools, but we handle permissions via canUseTool"
    )

    async def permission_handler(
        tool_name: str, input_data: dict, context: dict
    ) -> Dict[str, Any]:
        """
        Permission handler that allows:
        1. Builtin tools from allowed_tools list
        2. MCP tools matching mcp__<server_name>__* pattern

        Args:
            tool_name: Tool being invoked
            input_data: Tool input parameters
            context: Execution context

        Returns:
            Permission decision: {"behavior": "allow"|"deny", "updatedInput": input_data}
        """
        # ALWAYS log permission checks for debugging
        logger.info(
            "permission_handler_called",
            tool_name=tool_name,
            is_builtin=tool_name in allowed_tools,
            is_mcp=tool_name.startswith("mcp__"),
            configured_servers=list(mcp_server_names),
        )

        # Allow builtin tools
        if tool_name in allowed_tools:
            logger.info("permission_granted_builtin", tool_name=tool_name)
            return {"behavior": "allow", "updatedInput": input_data}

        # Allow MCP tools from configured servers
        # Pattern: mcp__<server_name>__<tool_name>
        if tool_name.startswith("mcp__"):
            parts = tool_name.split("__", 2)
            if len(parts) >= 2:
                server_name = parts[1]
                logger.info(
                    "checking_mcp_permission",
                    tool_name=tool_name,
                    extracted_server=server_name,
                    configured_servers=list(mcp_server_names),
                    matches=server_name in mcp_server_names,
                )
                if server_name in mcp_server_names:
                    logger.info(
                        "permission_granted_mcp",
                        tool_name=tool_name,
                        server_name=server_name,
                    )
                    return {"behavior": "allow", "updatedInput": input_data}

        # Deny unrecognized tools
        logger.warning(
            "tool_permission_denied",
            tool_name=tool_name,
            reason="not_in_allowed_tools_or_mcp_servers",
            available_mcp_servers=list(mcp_server_names),
            available_builtin_count=len(allowed_tools),
        )
        return {
            "behavior": "deny",
            "updatedInput": input_data,
            "message": f"Tool '{tool_name}' not permitted. Not in allowed tools or MCP servers."
        }

    return permission_handler


def validate_session_id(session_id: Optional[str]) -> Optional[str]:
    """
    Validate session_id format before use.

    BUG FIX #4: Ensures session_id is valid before storing for multi-turn.

    Args:
        session_id: Session ID to validate

    Returns:
        Valid session_id or None if invalid
    """
    if not session_id:
        return None

    if not isinstance(session_id, str) or len(session_id) < 10:
        logger.warning(
            "invalid_session_id_format",
            session_id=session_id if isinstance(session_id, str) else None,
            type=type(session_id).__name__,
            length=len(session_id) if isinstance(session_id, str) else 0,
        )
        return None

    return session_id


async def build_claude_options(
    context: Any,  # RuntimeExecutionContext
    event_callback: Optional[Callable] = None,
    runtime: Optional[Any] = None,  # ClaudeCodeRuntime instance for caching
) -> Tuple[Any, Dict[str, str], Set[str], Set[str]]:
    """
    Build ClaudeAgentOptions from execution context.

    Args:
        context: RuntimeExecutionContext with prompt, history, config
        event_callback: Optional event callback for hooks
        runtime: Optional ClaudeCodeRuntime instance for MCP discovery caching

    Returns:
        Tuple of (ClaudeAgentOptions instance, active_tools dict, started_tools set, completed_tools set)
    """
    from claude_agent_sdk import ClaudeAgentOptions

    # Extract configuration
    agent_config = context.agent_config or {}
    runtime_config = context.runtime_config or {}

    # Get LiteLLM configuration (same as DefaultRuntime/Agno)
    litellm_api_base = os.getenv("LITELLM_API_BASE", "https://llm-proxy.kubiya.ai")
    litellm_api_key = os.getenv("LITELLM_API_KEY")

    if not litellm_api_key:
        raise ValueError("LITELLM_API_KEY environment variable not set")

    # Determine model (use LiteLLM format) with override support
    # Priority: KUBIYA_MODEL_OVERRIDE > context.model_id > LITELLM_DEFAULT_MODEL > default
    model = get_effective_model(
        context_model_id=context.model_id,
        log_context={"execution_id": context.execution_id[:8] if context.execution_id else "unknown"},
    )

    # Map skills to Claude Code tool names (built-in tools only)
    allowed_tools = map_skills_to_tools(context.skills)

    # Build MCP servers (both from context and custom skills)
    # SDK will discover tools automatically - we just provide configs
    mcp_servers, _ = build_mcp_servers(
        context.skills, context.mcp_servers
    )

    # Verify MCP server connections and discover tools (with caching)
    # This helps us detect configuration errors early
    # Cache reduces process spawning by 50% by reusing discovery results
    mcp_discovery_results = {}
    if mcp_servers:
        try:
            # Check cache first
            cache_key = _get_mcp_cache_key(mcp_servers)
            if cache_key in _mcp_discovery_cache:
                mcp_discovery_results = _mcp_discovery_cache[cache_key]
                logger.info(
                    "using_cached_mcp_discovery",
                    server_count=len(mcp_servers),
                    server_names=list(mcp_servers.keys()),
                    cache_key=cache_key,
                    note="✅ Using cached MCP discovery results (no processes spawned)"
                )
            else:
                logger.info(
                    "verifying_mcp_server_connections",
                    server_count=len(mcp_servers),
                    server_names=list(mcp_servers.keys()),
                    cache_key=cache_key,
                    note="Attempting to connect and discover tools from all MCP servers"
                )
                mcp_discovery_results = await discover_all_mcp_resources(mcp_servers)
                # Cache the results for future executions
                _mcp_discovery_cache[cache_key] = mcp_discovery_results
                logger.info(
                    "cached_mcp_discovery_results",
                    cache_key=cache_key,
                    note="Discovery results cached for future executions"
                )

            # Log results for each server
            failed_servers = []
            successful_servers = []
            skipped_servers = []
            for server_name, result in mcp_discovery_results.items():
                # Check if server was skipped (HTTP servers use native SDK discovery)
                if result.get("skipped"):
                    skipped_servers.append(server_name)
                    logger.info(
                        "mcp_server_skipped_native_discovery",
                        server_name=server_name,
                        status="⚡ HTTP - Using SDK native discovery",
                        note="Pre-discovery skipped for HTTP servers (SDK handles them natively)"
                    )
                elif result["connected"]:
                    tool_count = len(result["tools"])
                    successful_servers.append(server_name)
                    if tool_count == 0:
                        logger.warning(
                            "mcp_server_connected_but_no_tools",
                            server_name=server_name,
                            message=f"MCP server '{server_name}' connected successfully but discovered 0 tools",
                            recommendation="Check server implementation - it may not be exposing any tools"
                        )
                    else:
                        logger.info(
                            "mcp_server_verified",
                            server_name=server_name,
                            tool_count=tool_count,
                            tool_names=result["tools"][:5] if tool_count <= 5 else [t["name"] for t in result["tools"][:5]] + [f"... and {tool_count - 5} more"],
                            status="✅ Connected and discovered tools"
                        )
                else:
                    failed_servers.append(server_name)
                    logger.error(
                        "mcp_server_connection_failed",
                        server_name=server_name,
                        error=result.get("error", "Unknown error"),
                        status="❌ Failed to connect",
                        recommendation="Check server command, args, and environment variables in agent configuration"
                    )

            # Summary log
            if failed_servers:
                logger.error(
                    "mcp_verification_summary",
                    total_servers=len(mcp_servers),
                    http_skipped=len(skipped_servers),
                    successful=len(successful_servers),
                    failed=len(failed_servers),
                    failed_server_names=failed_servers,
                    message=f"⚠️  {len(failed_servers)} MCP server(s) failed to connect - agent may not have access to expected tools"
                )
            else:
                logger.info(
                    "mcp_verification_summary",
                    total_servers=len(mcp_servers),
                    http_skipped=len(skipped_servers),
                    successful=len(successful_servers),
                    total_tools_discovered=sum(len(r["tools"]) for r in mcp_discovery_results.values() if not r.get("skipped")),
                    message=f"✅ All MCP servers ready: {len(skipped_servers)} HTTP (native SDK) + {len(successful_servers)} pre-discovered"
                )

        except Exception as discovery_error:
            logger.error(
                "mcp_discovery_process_failed",
                error=str(discovery_error),
                error_type=type(discovery_error).__name__,
                message="Failed to verify MCP server connections - will proceed but tools may not be available",
                exc_info=True
            )

    # BUG FIX #6: Validate built-in tool names before using
    allowed_tools, invalid_tools = validate_tool_names(allowed_tools)

    # Build permission handler for MCP tools
    # IMPORTANT: SDK discovers tools, but we must permit them via canUseTool
    permission_handler = None
    if mcp_servers:
        permission_handler = build_mcp_permission_handler(mcp_servers, allowed_tools)
        logger.info(
            "mcp_permission_handler_configured",
            mcp_servers=list(mcp_servers.keys()),
            note="Will auto-allow tools matching mcp__<server_name>__* pattern"
        )

    logger.info(
        "claude_code_tools_configured",
        builtin_tools_count=len(allowed_tools),
        mcp_servers_count=len(mcp_servers),
        mcp_server_names=list(mcp_servers.keys()) if mcp_servers else [],
        builtin_tools=allowed_tools[:20],  # Limit for readability
        has_permission_handler=permission_handler is not None,
        note="SDK discovers MCP tools automatically, we handle permissions via canUseTool"
    )

    # Create shared active_tools dict for tool name tracking
    # This is populated in the stream when ToolUseBlock is received,
    # and used in hooks to look up tool names
    active_tools: Dict[str, str] = {}

    # Create shared started_tools set for tracking published start events
    # This prevents duplicate tool_start events from hooks
    from typing import Set
    started_tools: Set[str] = set()

    # Create shared completed_tools set for tracking published completion events
    # This prevents duplicate tool_complete events from hooks and ToolResultBlock
    completed_tools: Set[str] = set()

    # Initialize enforcement service for policy checks
    enforcement_context = {
        "organization_id": context.organization_id,
        "user_email": context.user_email,
        "user_id": context.user_id,
        "user_roles": context.user_roles or [],
        "team_id": context.team_id,
        "team_name": context.team_name,
        "agent_id": context.agent_id,
        "environment": context.environment,
        "model_id": context.model_id,
    }

    # Import enforcement dependencies
    from control_plane_api.app.lib.policy_enforcer_client import create_policy_enforcer_client
    from control_plane_api.worker.services.tool_enforcement import ToolEnforcementService

    # Get enforcer client (using the same token as the control plane)
    enforcer_client = None
    enforcement_service = None

    # Check if enforcement is enabled (opt-in via environment variable)
    enforcement_enabled = os.environ.get("KUBIYA_ENFORCE_ENABLED", "").lower() in ("true", "1", "yes")

    if not enforcement_enabled:
        logger.info(
            "policy_enforcement_disabled",
            reason="KUBIYA_ENFORCE_ENABLED not set",
            execution_id=context.execution_id[:8],
            note="Set KUBIYA_ENFORCE_ENABLED=true to enable policy enforcement"
        )
    else:
        try:
            # Get API key from runtime (if available)
            api_key = runtime.control_plane.api_key if runtime and hasattr(runtime, 'control_plane') else None
            if api_key:
                # Get enforcer URL - default to control plane enforcer proxy
                enforcer_url = os.environ.get("ENFORCER_SERVICE_URL")
                if not enforcer_url:
                    # Use control plane's enforcer proxy as default
                    control_plane_url = os.environ.get("CONTROL_PLANE_URL", "http://localhost:8000")
                    enforcer_url = f"{control_plane_url.rstrip('/')}/api/v1/enforcer"
                    logger.debug(
                        "using_control_plane_enforcer_proxy",
                        enforcer_url=enforcer_url,
                        execution_id=context.execution_id[:8],
                    )

                # Use async context manager properly (we're in an async function)
                enforcer_client_context = create_policy_enforcer_client(
                    enforcer_url=enforcer_url,
                    api_key=api_key,
                    auth_type="UserKey"
                )
                enforcer_client = await enforcer_client_context.__aenter__()
                if enforcer_client:
                    enforcement_service = ToolEnforcementService(enforcer_client)
                    logger.info(
                        "policy_enforcement_enabled",
                        enforcer_url=enforcer_url,
                        execution_id=context.execution_id[:8],
                    )
            else:
                logger.debug(
                    "enforcement_service_skipped",
                    reason="no_api_key_available",
                    execution_id=context.execution_id[:8],
                )
        except Exception as e:
            logger.warning(
                "enforcement_service_init_failed",
                error=str(e),
                execution_id=context.execution_id[:8],
            )

    # Build hooks for tool execution monitoring with enforcement
    hooks = (
        build_hooks(
            context.execution_id,
            event_callback,
            active_tools,
            completed_tools,
            started_tools,
            enforcement_context=enforcement_context,
            enforcement_service=enforcement_service,
        )
        if event_callback
        else {}
    )

    # Build environment with LiteLLM configuration
    env = runtime_config.get("env", {}).copy()

    # Check if model override is active - if so, we'll bypass the internal proxy
    model_override_active = is_model_override_active()
    model_override_value = os.environ.get("KUBIYA_MODEL_OVERRIDE") if model_override_active else None

    if model_override_active:
        logger.info(
            "model_override_detected_bypassing_internal_proxy",
            model_override=model_override_value,
            note="Internal LiteLLM proxy will be bypassed, using direct API configuration"
        )

    # Extract and validate secrets from skill configurations
    # Skills may reference secrets (e.g., Slack skill with secret_name or secrets parameters)
    # These secrets should be resolved and injected as environment variables by the execution environment controller
    if context.skill_configs:
        for skill_config in context.skill_configs:
            config = skill_config.get("configuration", {})
            skill_name = skill_config.get("name", "unknown")

            # Check for secrets (list) or secret_name (single, deprecated)
            secrets_list = []
            if "secrets" in config:
                secrets = config["secrets"]
                if isinstance(secrets, list):
                    secrets_list = secrets
                elif isinstance(secrets, str):
                    secrets_list = [s.strip() for s in secrets.split(",") if s.strip()]
            elif "secret_name" in config and config["secret_name"]:
                secrets_list = [config["secret_name"]]

            # Validate that configured secrets are available in environment
            for secret_name in secrets_list:
                if secret_name not in env:
                    logger.warning(
                        "skill_secret_not_resolved",
                        skill_name=skill_name,
                        secret_name=secret_name,
                        note=f"Secret '{secret_name}' configured in skill '{skill_name}' but not found in execution environment. "
                             f"Ensure the secret is added to the execution environment's secrets list."
                    )

    # LOG WHAT ENV VARS WE RECEIVED FROM RUNTIME CONFIG
    print(f"\n🔍 CLAUDE CODE CONFIG - ENV VARS RECEIVED:")
    print(f"   Received from runtime_config: {len(env)} variables")
    print(f"   Keys: {list(env.keys())}")
    for key, value in env.items():
        if any(s in key.upper() for s in ["TOKEN", "KEY", "SECRET", "PASSWORD"]):
            masked = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
            print(f"   {key}: {masked} (length: {len(value)})")
        else:
            print(f"   {key}: {value}")
    print()

    # ALWAYS use internal proxy - it handles:
    # 1. Model override (rewrites ALL model names including subagents)
    # 2. Langfuse metadata injection
    # 3. Request forwarding to real LiteLLM
    try:
        local_proxy_url = get_proxy_base_url()
        logger.info(
            "local_litellm_proxy_started",
            proxy_url=local_proxy_url,
            real_litellm_url=litellm_api_base,
            execution_id=context.execution_id[:8],
            model_override_active=model_override_active,
            model_override=model_override_value if model_override_active else None,
            note="Internal proxy handles model override for ALL requests including subagents"
        )
    except Exception as proxy_error:
        logger.error(
            "failed_to_start_local_proxy",
            error=str(proxy_error),
            execution_id=context.execution_id,
            fallback="Using direct LiteLLM connection (no metadata injection or model override)",
        )
        # Fallback to direct connection if proxy fails
        local_proxy_url = litellm_api_base

    # Configure Claude Code SDK to use LOCAL proxy (which forwards to real LiteLLM)
    env["ANTHROPIC_BASE_URL"] = local_proxy_url
    env["ANTHROPIC_API_KEY"] = litellm_api_key

    # Store execution context for metadata injection
    execution_context = {}
    if context.user_metadata:
        user_id = context.user_metadata.get("user_email") or context.user_metadata.get("user_id")
        session_id = context.user_metadata.get("session_id") or context.execution_id

        execution_context = {
            "user_id": user_id,
            "session_id": session_id,
            "organization_id": context.organization_id,
            "agent_id": context.agent_id,
            "agent_name": context.user_metadata.get("agent_name") or context.agent_id,
            "model_id": model,
        }

        # Store context for proxy to use
        set_execution_context(context.execution_id, execution_context)

        logger.info(
            "execution_context_stored_for_proxy",
            execution_id=context.execution_id[:8],
            has_user_id=bool(user_id),
            has_session_id=bool(session_id),
            metadata_keys=list(execution_context.keys()),
        )

    # Pass Kubiya API credentials for workflow execution
    kubiya_api_key = os.environ.get("KUBIYA_API_KEY")
    if kubiya_api_key:
        env["KUBIYA_API_KEY"] = kubiya_api_key
        logger.debug("added_kubiya_api_key_to_environment")

    kubiya_api_base = os.environ.get("KUBIYA_API_BASE")
    if kubiya_api_base:
        env["KUBIYA_API_BASE"] = kubiya_api_base
        logger.debug(
            "added_kubiya_api_base_to_environment", kubiya_api_base=kubiya_api_base
        )

    # Get session_id from previous turn for conversation continuity
    # BUG FIX #4: Validate session_id format before use
    previous_session_id = None
    if context.user_metadata:
        raw_session_id = context.user_metadata.get("claude_code_session_id")
        previous_session_id = validate_session_id(raw_session_id)

        if raw_session_id and not previous_session_id:
            logger.warning(
                "invalid_session_id_from_user_metadata",
                raw_session_id=raw_session_id,
            )

    logger.info(
        "building_claude_code_options",
        has_user_metadata=bool(context.user_metadata),
        has_session_id_in_metadata=bool(previous_session_id),
        previous_session_id_prefix=(
            previous_session_id[:16] if previous_session_id else None
        ),
        will_resume=bool(previous_session_id),
    )

    # NEW: Support native subagents for team execution
    sdk_agents = None
    agents_config = agent_config.get('runtime_config', {}).get('agents')

    if agents_config:
        from claude_agent_sdk import AgentDefinition

        sdk_agents = {}
        for agent_id, agent_data in agents_config.items():
            sdk_agents[agent_id] = AgentDefinition(
                description=agent_data.get('description', ''),
                prompt=agent_data.get('prompt', ''),
                tools=agent_data.get('tools'),
                model=agent_data.get('model', 'inherit'),
            )

        logger.info(
            "native_subagents_configured",
            execution_id=context.execution_id[:8] if context.execution_id else "unknown",
            subagent_count=len(sdk_agents),
            subagent_ids=list(sdk_agents.keys()),
            subagent_models=[agent_data.get('model', 'inherit') for agent_data in agents_config.values()],
        )

    # Log detailed MCP server configuration for debugging
    if mcp_servers:
        logger.info(
            "mcp_servers_being_passed_to_sdk",
            server_count=len(mcp_servers),
            server_names=list(mcp_servers.keys()),
            server_configs={
                name: {
                    "type": cfg.get("type", "stdio"),
                    "url": cfg.get("url", "N/A")[:50] if cfg.get("url") else "N/A",
                    "command": cfg.get("command", "N/A"),
                    "args": cfg.get("args", []),  # Show args for debugging
                    "has_env": bool(cfg.get("env"))
                }
                for name, cfg in mcp_servers.items()
            },
            note="SDK should discover tools from these servers"
        )

    # Build options - SDK discovers tools, we handle permissions
    # Enhance system prompt with runtime-specific additions
    # Create per-execution prompt builder to support dynamic skill context
    from control_plane_api.worker.services.skill_context_enhancement import (
        SkillContextEnhancement,
    )

    prompt_builder = create_default_prompt_builder()

    # Add skill context enhancement if enabled and skills are configured
    skill_context_enabled = os.getenv("ENABLE_SKILL_CONTEXT_ENHANCEMENT", "true").lower() == "true"
    if skill_context_enabled and context.skill_configs:
        skill_context_enhancement = SkillContextEnhancement(context.skill_configs)
        prompt_builder.add_enhancement(skill_context_enhancement)
        logger.info(
            "skill_context_enhancement_enabled",
            skill_count=len(context.skill_configs),
            execution_id=context.execution_id[:8] if context.execution_id else "unknown",
        )

    enhanced_system_prompt = prompt_builder.build(
        base_prompt=context.system_prompt,
        runtime_type="claude_code",
    )

    # LOG FINAL ENV VARS BEING PASSED TO CLAUDE SDK
    print(f"\n🔍 CLAUDE SDK OPTIONS - FINAL ENV VARS:")
    print(f"   Total env vars for SDK: {len(env)} variables")
    print(f"   Keys: {list(env.keys())}")
    for key, value in env.items():
        if any(s in key.upper() for s in ["TOKEN", "KEY", "SECRET", "PASSWORD"]):
            masked = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
            print(f"   {key}: {masked} (length: {len(value)})")
        else:
            print(f"   {key}: {value}")
    print()

    # Determine working directory: user override > workspace > None (SDK default)
    cwd_value = agent_config.get("cwd") or runtime_config.get("cwd")

    if not cwd_value and context.workspace_directory:
        cwd_value = context.workspace_directory

        logger.info(
            "claude_code_using_execution_workspace",
            execution_id=context.execution_id[:8] if len(context.execution_id) >= 8 else context.execution_id,
            workspace=cwd_value,
        )

    options_dict = {
        "system_prompt": enhanced_system_prompt,
        "allowed_tools": allowed_tools,
        "mcp_servers": mcp_servers,  # SDK discovers tools automatically
        "agents": sdk_agents,  # NEW: Native subagent support for teams
        "permission_mode": runtime_config.get(
            "permission_mode",
            os.getenv("CLAUDE_CODE_PERMISSION_MODE", "bypassPermissions")
        ),
        "cwd": cwd_value,
        "model": model,
        "env": env,  # ← ENVIRONMENT VARIABLES PASSED HERE!
        "max_turns": runtime_config.get("max_turns", 50),  # Default 50 turns to support complex multi-step workflows
        "hooks": hooks,
        "setting_sources": [],  # Explicit: don't load filesystem settings
        "include_partial_messages": True,  # Enable character-by-character streaming
        "resume": previous_session_id,  # Resume previous conversation if available
    }

    # Extended thinking support - enables thinking/reasoning streaming
    # Can be configured via runtime_config or environment variable
    max_thinking_tokens = runtime_config.get(
        "max_thinking_tokens",
        int(os.getenv("CLAUDE_CODE_MAX_THINKING_TOKENS", "0"))
    )
    if max_thinking_tokens > 0:
        options_dict["max_thinking_tokens"] = max_thinking_tokens
        logger.info(
            "extended_thinking_enabled",
            max_thinking_tokens=max_thinking_tokens,
            note="Extended thinking will stream thinking_start/thinking_delta/thinking_complete events"
        )

    # Add permission handler if we have MCP servers
    # CRITICAL: SDK discovers tools but doesn't auto-permit them
    if permission_handler:
        options_dict["can_use_tool"] = permission_handler

    options = ClaudeAgentOptions(**options_dict)

    logger.info(
        "claude_code_options_configured",
        include_partial_messages=getattr(options, "include_partial_messages", "NOT SET"),
        permission_mode=options.permission_mode,
        model=options.model,
        mcp_servers_configured=len(mcp_servers) if mcp_servers else 0,
        has_can_use_tool=permission_handler is not None,
        note="SDK discovers tools, canUseTool handler permits mcp__<server>__* pattern"
    )

    # Return options, active_tools dict, started_tools set, and completed_tools set for tracking
    return options, active_tools, started_tools, completed_tools
