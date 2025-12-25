"""
MCP (Model Context Protocol) server builder for Claude Code runtime.

This module handles the creation and configuration of MCP servers from
both external sources and custom skills.

The Claude Code SDK automatically:
- Connects to MCP servers
- Discovers available tools
- Names them as mcp__<server_name>__<tool_name>
- Makes them available to Claude

We only need to:
1. Validate and format MCP server configs
2. Convert custom skills to SDK MCP servers (for custom tools)
"""

from typing import Dict, Any, List, Tuple, Optional
import structlog
import asyncio

logger = structlog.get_logger(__name__)


def _validate_and_normalize_mcp_config(server_name: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Validate and normalize MCP server configuration dict.

    The Claude SDK expects TypedDict configs (McpStdioServerConfig or McpSSEServerConfig).
    These are just dictionaries with specific required/optional fields.

    Stdio format:
        {
            "command": str,          # Required
            "args": list[str],       # Optional
            "env": dict[str, str]    # Optional
        }

    SSE format:
        {
            "type": "sse",           # Required, must be "sse"
            "url": str,              # Required
            "headers": dict[str, str] # Optional
        }

    Args:
        server_name: Name of the MCP server
        config: Configuration dict from execution environment

    Returns:
        Validated config dict, or None if invalid
    """
    try:
        # Check if it's stdio transport (has 'command' field)
        if "command" in config:
            command = config.get("command")
            if not command:
                logger.error(
                    "stdio_mcp_server_missing_command",
                    server_name=server_name,
                    config=config
                )
                return None

            # Build normalized stdio config
            normalized = {
                "command": command,
            }
            if "args" in config:
                normalized["args"] = config["args"]
            if "env" in config:
                normalized["env"] = config["env"]

            logger.info(
                "validated_stdio_mcp_server",
                server_name=server_name,
                command=command,
                has_args="args" in normalized,
                has_env="env" in normalized
            )

            # Print detailed config for debugging
            print(f"\n{'='*80}")
            print(f"🔍 STDIO MCP SERVER FULL CONFIG (after template resolution)")
            print(f"{'='*80}")
            print(f"Server Name: {server_name}")
            print(f"Command: {command}")
            if "args" in normalized:
                print(f"Args: {normalized['args']}")
            if "env" in normalized:
                print(f"\nEnvironment Variables:")
                for env_name, env_value in normalized["env"].items():
                    # Mask sensitive values
                    if any(sensitive in env_name.lower() for sensitive in ["key", "token", "auth", "secret", "password"]):
                        masked_value = env_value[:20] + "..." if len(env_value) > 20 else "***"
                        print(f"  {env_name}: {masked_value} (length: {len(env_value)})")
                    else:
                        print(f"  {env_name}: {env_value}")
            print(f"{'='*80}\n")

            return normalized

        # Check if it's HTTP/SSE transport (has 'type'/'transport_type' and 'url' fields)
        # Support both 'type' and 'transport_type' for backward compatibility
        elif ("type" in config or "transport_type" in config) and "url" in config:
            transport_type = config.get("type") or config.get("transport_type")
            url = config.get("url")

            if not url:
                logger.error(
                    "http_sse_mcp_server_missing_url",
                    server_name=server_name,
                    transport_type=transport_type,
                    config=config
                )
                return None

            # Validate transport type
            if transport_type not in ("sse", "http"):
                logger.error(
                    "unsupported_mcp_transport_type",
                    server_name=server_name,
                    transport_type=transport_type,
                    supported=["sse", "http"]
                )
                return None

            # Build normalized config - preserve transport type!
            # HTTP = recommended (native Claude SDK support, bidirectional)
            # SSE = deprecated (requires workaround, unidirectional)
            normalized = {
                "type": transport_type,  # Keep original: "http" or "sse"
                "url": url,
            }
            if "headers" in config:
                normalized["headers"] = config["headers"]

            # Log full configuration including headers for debugging
            logger.info(
                "validated_http_mcp_server",
                server_name=server_name,
                transport=transport_type,
                url=url,
                has_headers="headers" in normalized,
            )

            # Print detailed config for debugging
            transport_label = "HTTP" if transport_type == "http" else "SSE (DEPRECATED)"
            print(f"\n{'='*80}")
            print(f"🔍 {transport_label} MCP SERVER FULL CONFIG (after template resolution)")
            print(f"{'='*80}")
            print(f"Server Name: {server_name}")
            print(f"Transport: {transport_type}")
            print(f"URL: {url}")
            if "headers" in normalized:
                print(f"\nHeaders:")
                for header_name, header_value in normalized["headers"].items():
                    # Mask sensitive values but show structure
                    if any(sensitive in header_name.lower() for sensitive in ["key", "token", "auth", "secret"]):
                        masked_value = header_value[:20] + "..." if len(header_value) > 20 else "***"
                        print(f"  {header_name}: {masked_value} (length: {len(header_value)})")
                    else:
                        print(f"  {header_name}: {header_value}")
            else:
                print(f"\nHeaders: (none)")
            print(f"{'='*80}\n")

            return normalized

        else:
            logger.error(
                "invalid_mcp_server_config_format",
                server_name=server_name,
                config=config,
                error="Must have either 'command' (stdio) or 'type'+'url' (SSE/HTTP)"
            )
            return None

    except Exception as e:
        logger.error(
            "mcp_config_validation_error",
            server_name=server_name,
            error=str(e),
            exc_info=True
        )
        return None


def extract_mcp_tool_names(
    server_name: str,
    server_obj: Any,
    explicit_tools: Optional[List[str]] = None
) -> List[str]:
    """
    Extract MCP tool names from server object.

    ⚠️ Note: This function is kept for backward compatibility but isn't used
    in the main flow. Tool discovery is handled by discover_all_mcp_resources()
    in mcp_discovery.py as a workaround for Claude SDK bug #3426.

    Args:
        server_name: Name of the MCP server
        server_obj: MCP server object
        explicit_tools: Optional list of tool names

    Returns:
        Empty list (discovery handled in mcp_discovery.py)
    """
    logger.debug(
        "extract_mcp_tool_names_skipped",
        server_name=server_name,
        message="Tool extraction handled by mcp_discovery.py pre-discovery"
    )

    # Return empty list - discovery handled elsewhere
    return []


def build_mcp_servers(
    skills: List[Any],
    context_mcp_servers: Dict[str, Any] = None,
    mcp_tools_config: Optional[Dict[str, List[str]]] = None
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Build MCP server configurations from context and custom skills.

    This function:
    1. Validates and formats external MCP server configs (stdio/SSE)
    2. Converts custom skills to SDK MCP servers (for custom tools)

    ⚠️ Note about tool discovery:
    The Claude SDK has a bug (#3426) where it doesn't properly expose SSE MCP tools.
    Tool discovery is handled separately in config.py via discover_all_mcp_resources()
    which pre-discovers tools and adds them to allowedTools as a workaround.

    Args:
        skills: List of skill objects to convert to MCP servers
        context_mcp_servers: Optional MCP servers from execution context (as config dicts)
        mcp_tools_config: Optional dict mapping server_name -> list of tool names (not used)

    Returns:
        Tuple of (MCP server configurations dict, empty list)
        Note: Second return value is always empty - tool discovery handled in config.py
    """
    if mcp_tools_config is None:
        mcp_tools_config = {}
    from claude_agent_sdk import create_sdk_mcp_server, tool as mcp_tool

    # DEBUG: Log what we received
    print(f"\n🔍 DEBUG: build_mcp_servers() INPUTS:")
    print(f"   context_mcp_servers type: {type(context_mcp_servers)}")
    print(f"   context_mcp_servers value: {context_mcp_servers}")
    print(f"   context_mcp_servers count: {len(context_mcp_servers) if context_mcp_servers else 0}")
    if context_mcp_servers:
        print(f"   Server names from context: {list(context_mcp_servers.keys())}")
    print()

    mcp_servers = {}

    # Include MCP servers from context (if any)
    if context_mcp_servers:
        logger.info(
            "processing_mcp_servers_from_context",
            server_count=len(context_mcp_servers),
            server_names=list(context_mcp_servers.keys()),
            note="SDK will discover tools automatically from these servers"
        )

        for server_name, server_config in context_mcp_servers.items():
            logger.debug(
                "processing_mcp_server_from_context",
                server_name=server_name,
                config_keys=list(server_config.keys()) if isinstance(server_config, dict) else "not_dict",
                has_command="command" in server_config if isinstance(server_config, dict) else False,
                has_type="type" in server_config if isinstance(server_config, dict) else False,
                has_url="url" in server_config if isinstance(server_config, dict) else False,
            )
            # Validate and normalize config dict (already in Claude SDK TypedDict format)
            normalized_config = _validate_and_normalize_mcp_config(server_name, server_config)
            if normalized_config:
                mcp_servers[server_name] = normalized_config
                transport = normalized_config.get("type", "stdio") if "type" in normalized_config else "stdio"
                logger.info(
                    "mcp_server_configured",
                    server_name=server_name,
                    transport=transport,
                    note="SDK will connect and discover tools automatically" if transport == "http"
                         else "SDK will connect (pre-discovery may be needed for SSE)" if transport == "sse"
                         else "SDK will connect and discover tools automatically"
                )
            else:
                logger.warning(
                    "skipping_mcp_server_invalid_config",
                    server_name=server_name,
                    config=server_config
                )
                continue

    # Convert custom skills to MCP servers
    for skill in skills:
        tools_list = []
        registered_tool_names = []  # Track tool names for logging
        skill_name = getattr(skill, "name", "custom_skill")

        # Check for Toolkit pattern (has .functions attribute)
        if hasattr(skill, "functions") and hasattr(skill.functions, "items"):
            logger.info(
                "found_skill_with_registered_functions",
                skill_name=skill_name,
                function_count=len(skill.functions),
                function_names=list(skill.functions.keys()),
            )

            # Extract tools from functions registry
            for func_name, func_obj in skill.functions.items():
                # Skip helper tools for workflow_executor skills to avoid confusion
                if func_name in ["list_all_workflows", "get_workflow_info"]:
                    logger.debug(
                        "skipping_helper_tool_for_workflow_executor",
                        skill_name=skill_name,
                        tool_name=func_name,
                    )
                    continue

                # Get entrypoint (the actual callable)
                entrypoint = getattr(func_obj, "entrypoint", None)
                if not entrypoint:
                    logger.warning(
                        "function_missing_entrypoint",
                        skill_name=skill_name,
                        function_name=func_name,
                    )
                    continue

                # Get function metadata - use function name as-is
                tool_name = func_name
                tool_description = (
                    getattr(func_obj, "description", None)
                    or entrypoint.__doc__
                    or f"{tool_name} tool"
                )
                tool_parameters = getattr(func_obj, "parameters", {})

                # Create a closure that captures the entrypoint with proper variable scope
                def make_tool_wrapper(
                    tool_entrypoint,
                    tool_func_name,
                    tool_func_description,
                    tool_func_parameters,
                ):
                    """Factory to create tool wrappers with proper closure"""

                    @mcp_tool(tool_func_name, tool_func_description, tool_func_parameters)
                    async def wrapped_tool(args: dict) -> dict:
                        try:
                            logger.debug(
                                "executing_builtin_skill_tool",
                                tool_name=tool_func_name,
                                args=args,
                            )
                            # Call the entrypoint with unpacked args
                            if asyncio.iscoroutinefunction(tool_entrypoint):
                                result = (
                                    await tool_entrypoint(**args)
                                    if args
                                    else await tool_entrypoint()
                                )
                            else:
                                # Run synchronous tools in thread pool to avoid blocking
                                result = await asyncio.to_thread(
                                    lambda: tool_entrypoint(**args)
                                    if args
                                    else tool_entrypoint()
                                )

                            logger.info(
                                "builtin_skill_tool_completed",
                                tool_name=tool_func_name,
                                result_length=len(str(result)),
                            )

                            return {
                                "content": [{"type": "text", "text": str(result)}]
                            }
                        except Exception as e:
                            logger.error(
                                "builtin_skill_tool_execution_failed",
                                tool_name=tool_func_name,
                                error=str(e),
                                exc_info=True,
                            )
                            return {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Error executing {tool_func_name}: {str(e)}",
                                    }
                                ],
                                "isError": True,
                            }

                    return wrapped_tool

                wrapped_tool = make_tool_wrapper(
                    entrypoint, tool_name, tool_description, tool_parameters
                )
                tools_list.append(wrapped_tool)
                registered_tool_names.append(tool_name)

                logger.info(
                    "registered_mcp_tool_from_skill_function",
                    skill_name=skill_name,
                    tool_name=tool_name,
                    full_mcp_tool_name=f"mcp__{skill_name}__{tool_name}",
                    note="SDK will make this available automatically"
                )

        # Legacy: Check if skill has get_tools() method
        elif hasattr(skill, "get_tools"):
            for tool_func in skill.get_tools():
                # Wrap each tool function with MCP tool decorator
                tool_name = getattr(tool_func, "__name__", "custom_tool")
                tool_description = getattr(tool_func, "__doc__", f"{tool_name} tool")

                # Create MCP tool wrapper
                @mcp_tool(tool_name, tool_description, {})
                async def wrapped_tool(args: dict) -> dict:
                    # Run synchronous tools in thread pool to avoid blocking
                    if asyncio.iscoroutinefunction(tool_func):
                        result = (
                            await tool_func(**args) if args else await tool_func()
                        )
                    else:
                        result = await asyncio.to_thread(
                            lambda: tool_func(**args) if args else tool_func()
                        )
                    return {"content": [{"type": "text", "text": str(result)}]}

                tools_list.append(wrapped_tool)
                registered_tool_names.append(tool_name)

        # Create MCP server for this skill if it has tools
        if tools_list:
            server_name = skill_name

            mcp_servers[server_name] = create_sdk_mcp_server(
                name=server_name, version="1.0.0", tools=tools_list
            )

            logger.info(
                "created_mcp_server_for_skill",
                skill_name=skill_name,
                server_name=server_name,
                tool_count=len(tools_list),
                tool_names=registered_tool_names,
                note="SDK will make these tools available as mcp__<server>__<tool>"
            )

    logger.info(
        "built_mcp_servers",
        server_count=len(mcp_servers),
        servers=list(mcp_servers.keys()),
        note="SDK will discover and provide all tools automatically - no manual intervention needed"
    )

    # Return empty list for tool names - SDK discovers them automatically
    return mcp_servers, []
