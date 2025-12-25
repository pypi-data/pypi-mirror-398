"""
MCP Resource Discovery

⚠️ WORKAROUND for Claude SDK Bug #3426

The Claude Agent SDK has a known bug where it fails to properly expose MCP tools
from SSE servers to Claude during runtime, even though the documentation says it
should discover them automatically.

This module provides a workaround by:
1. Pre-discovering tools from MCP servers using the MCP Python SDK
2. Returning discovered tools so they can be added to allowedTools explicitly
3. Building MCP context metadata for system prompt injection

For SSE servers: This pre-discovery is REQUIRED until the SDK bug is fixed.
For stdio servers: Pre-discovery ensures consistency across transport types.

See: https://github.com/anthropics/claude-code/issues/3426
"""

from typing import Dict, Any, List, Optional
import structlog
import asyncio
from contextlib import asynccontextmanager

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def connect_to_mcp_server(server_name: str, config: Dict[str, Any]):
    """
    Connect to an MCP server (stdio or SSE) and yield a session.

    IMPORTANT: For STDIO servers, the server MUST output only JSONRPC messages to stdout.
    Any other output (logs, debug prints, etc.) MUST go to stderr to avoid breaking
    the MCP protocol. The MCP SDK will log parsing errors for non-JSONRPC output but
    will continue operating. However, excessive parsing errors may cause the SDK to
    report execution errors.

    Args:
        server_name: Name of the MCP server
        config: Server configuration (stdio or SSE format)

    Yields:
        ClientSession connected to the server
    """
    import logging
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client
    from mcp.client.sse import sse_client

    # Suppress verbose parsing error logs from MCP SDK's stdio client
    # These errors are non-fatal and happen when servers incorrectly log to stdout
    # instead of stderr. The connection continues to work despite these errors.
    mcp_stdio_logger = logging.getLogger("mcp.client.stdio")
    original_level = mcp_stdio_logger.level
    mcp_stdio_logger.setLevel(logging.ERROR)  # Only show critical errors

    try:
        # Determine transport type
        is_stdio = "command" in config
        is_sse = "type" in config and config["type"] == "sse"

        if is_stdio:
            # Stdio transport
            from mcp import StdioServerParameters

            server_params = StdioServerParameters(
                command=config["command"],
                args=config.get("args", []),
                env=config.get("env", {})
            )

            logger.info(
                "connecting_to_stdio_mcp_server",
                server_name=server_name,
                command=config["command"],
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    logger.info("stdio_mcp_server_connected", server_name=server_name)
                    yield session

        elif is_sse:
            # SSE transport
            url = config["url"]
            headers = config.get("headers", {})

            logger.info(
                "connecting_to_sse_mcp_server",
                server_name=server_name,
                url=url,
            )

            # SSE connections might not support bidirectional messaging required for discovery
            # Use longer timeouts to prevent background task exceptions
            try:
                async with sse_client(url, headers=headers, timeout=30, sse_read_timeout=60) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        logger.info("sse_mcp_server_connected", server_name=server_name)
                        yield session
            except Exception as eg:
                # Handle both regular exceptions and ExceptionGroups (Python 3.10 compatible)
                # Check if it's an ExceptionGroup by type name (for Python 3.10 compatibility)
                if type(eg).__name__ == "ExceptionGroup" and hasattr(eg, 'exceptions'):
                    logger.error(
                        "sse_connection_exception_group",
                        server_name=server_name,
                        error=str(eg),
                        sub_exception_count=len(eg.exceptions),
                    )
                else:
                    logger.error(
                        "sse_connection_error",
                        server_name=server_name,
                        error=str(eg),
                        error_type=type(eg).__name__,
                    )
                raise
        else:
            raise ValueError(f"Invalid MCP server config for {server_name}: {config}")
    finally:
        # Restore original log level
        mcp_stdio_logger.setLevel(original_level)


async def discover_mcp_resources(server_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Connect to an MCP server and discover all available tools, resources, and prompts.

    ⚠️ IMPORTANT: Pre-discovery is ONLY needed for SSE servers (bug #3426 workaround)

    For HTTP servers: Claude SDK handles discovery natively - skip pre-discovery!
    For SSE servers: SDK bug requires manual pre-discovery as workaround
    For stdio servers: SDK handles discovery but we pre-discover for verification
    For SDK MCP servers: These are Python objects, not configs - skip pre-discovery!

    Args:
        server_name: Name of the MCP server
        config: Server configuration (or SDK MCP server object for skill-based servers)

    Returns:
        Dictionary with discovered capabilities:
        {
            "server_name": str,
            "tools": [...],
            "resources": [...],
            "prompts": [...],
            "connected": bool,
            "error": str | None
        }
    """
    transport_type = config.get("type") if isinstance(config, dict) else None

    # SDK MCP servers: Skip pre-discovery - these are created from Python Toolkits via create_sdk_mcp_server()
    # They're wrapped in a dict with type='sdk' and instance=<Server object>
    if transport_type == "sdk" or not isinstance(config, dict):
        logger.info(
            "skipping_sdk_mcp_server_prediscovery",
            server_name=server_name,
            config_type=str(type(config)),
            has_type_sdk=(transport_type == "sdk"),
            note="SDK MCP servers (from Python Toolkits) use native SDK discovery (no pre-discovery needed)"
        )
        return {
            "server_name": server_name,
            "tools": [],
            "resources": [],
            "prompts": [],
            "connected": True,  # Assume connection will work
            "error": None,
            "skipped": True,  # Mark as skipped for logging
        }

    # HTTP servers: Skip pre-discovery - SDK handles it natively
    if transport_type == "http":
        logger.info(
            "skipping_http_server_prediscovery",
            server_name=server_name,
            url=config.get("url"),
            note="HTTP servers use native SDK discovery (no workaround needed)"
        )
        return {
            "server_name": server_name,
            "tools": [],
            "resources": [],
            "prompts": [],
            "connected": True,  # Assume connection will work
            "error": None,
            "skipped": True,  # Mark as skipped for logging
        }

    # SSE servers: Check for explicit tool configuration first
    is_sse = transport_type == "sse"
    explicit_tools = config.get("tools", [])
    if is_sse and explicit_tools:
        logger.info(
            "using_explicit_sse_tool_config",
            server_name=server_name,
            url=config.get("url"),
            tool_count=len(explicit_tools),
            tools=explicit_tools,
            note="Using explicit tool configuration (skipping discovery for SSE server)",
        )
        # Return mock discovery result with explicit tools
        return {
            "server_name": server_name,
            "tools": [{"name": tool, "description": f"{tool} from {server_name}", "inputSchema": {}} for tool in explicit_tools],
            "resources": [],
            "prompts": [],
            "connected": True,
            "error": None,
        }
    elif is_sse:
        # WORKAROUND: SSE servers require pre-discovery due to Claude SDK bug #3426
        # The MCP Python SDK will attempt to connect and discover tools
        # If discovery fails, we'll catch the exception and log it properly
        logger.info(
            "attempting_sse_mcp_discovery",
            server_name=server_name,
            url=config.get("url"),
            note="⚠️  SSE WORKAROUND: Pre-discovering tools (SDK bug #3426)",
            recommendation="If discovery fails repeatedly, add explicit tools to config: "
                          f"mcp_servers.{server_name}.tools = ['list_tables', 'query_data', ...]"
        )

    try:
        async with connect_to_mcp_server(server_name, config) as session:
            # List all capabilities - handle each separately for resilience
            tools = []
            resources = []
            prompts = []

            # Try to list tools (most critical)
            try:
                tools_result = await session.list_tools()
                tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": (
                            # Handle both Pydantic models and plain dicts
                            tool.inputSchema.model_dump() if hasattr(tool.inputSchema, "model_dump")
                            else tool.inputSchema if hasattr(tool, "inputSchema")
                            else None
                        ),
                    }
                    for tool in tools_result.tools
                ]
                logger.info(
                    "tools_listed_successfully",
                    server_name=server_name,
                    tool_count=len(tools),
                    tool_names=[t["name"] for t in tools],
                )
            except Exception as tool_error:
                logger.warning(
                    "failed_to_list_tools",
                    server_name=server_name,
                    error=str(tool_error)[:200],
                    error_type=type(tool_error).__name__,
                    exc_info=True,
                )

            # Try to list resources (optional)
            try:
                resources_result = await session.list_resources()
                resources = [
                    {
                        "uri": resource.uri,
                        "name": resource.name,
                        "description": resource.description,
                        "mimeType": getattr(resource, "mimeType", None),
                    }
                    for resource in resources_result.resources
                ]
            except Exception as resource_error:
                logger.debug(
                    "failed_to_list_resources",
                    server_name=server_name,
                    error=str(resource_error)[:100]
                )

            # Try to list prompts (optional)
            try:
                prompts_result = await session.list_prompts()
                prompts = [
                    {
                        "name": prompt.name,
                        "description": prompt.description,
                        "arguments": [
                            {
                                "name": arg.name,
                                "description": arg.description,
                                "required": arg.required,
                            }
                            for arg in (prompt.arguments or [])
                        ]
                    }
                    for prompt in prompts_result.prompts
                ]
            except Exception as prompt_error:
                logger.debug(
                    "failed_to_list_prompts",
                    server_name=server_name,
                    error=str(prompt_error)[:100]
                )

            # Special logging for SSE servers since this is a workaround for SDK bug
            if is_sse:
                logger.info(
                    "sse_mcp_resources_discovered",
                    server_name=server_name,
                    tools_count=len(tools),
                    resources_count=len(resources),
                    prompts_count=len(prompts),
                    tool_names=[t["name"] for t in tools],
                    resource_uris=[r["uri"] for r in resources],
                    prompt_names=[p["name"] for p in prompts],
                    note="Pre-discovery successful! Tools will be added to allowedTools (SDK bug #3426 workaround)",
                )
            else:
                logger.info(
                    "mcp_resources_discovered",
                    server_name=server_name,
                    tools_count=len(tools),
                    resources_count=len(resources),
                    prompts_count=len(prompts),
                    tool_names=[t["name"] for t in tools],
                    resource_uris=[r["uri"] for r in resources],
                    prompt_names=[p["name"] for p in prompts],
                )

            return {
                "server_name": server_name,
                "tools": tools,
                "resources": resources,
                "prompts": prompts,
                "connected": True,
                "error": None,
            }

    except Exception as e:
        error_str = str(e)
        is_sse = config.get("type") == "sse"
        is_timeout = "timeout" in error_str.lower() or "timed out" in error_str.lower()
        is_404 = "404" in error_str or "/messages" in error_str

        # For ExceptionGroup, try to extract sub-exceptions
        sub_errors = []
        if type(e).__name__ == "ExceptionGroup":
            try:
                # ExceptionGroup has an 'exceptions' attribute
                if hasattr(e, 'exceptions'):
                    sub_errors = [
                        f"{type(ex).__name__}: {str(ex)[:100]}"
                        for ex in e.exceptions[:3]  # First 3 errors
                    ]
            except:
                pass

        # Special handling for SSE-only servers (404 on /messages endpoint)
        if is_sse and is_404:
            logger.error(
                "sse_server_incompatible_with_mcp_discovery",
                server_name=server_name,
                url=config.get("url"),
                error="Server doesn't support bidirectional MCP protocol (404 on /messages endpoint)",
                solution=f"Add explicit tools to agent config:\n"
                        f"  mcp_servers:\n"
                        f"    {server_name}:\n"
                        f"      type: sse\n"
                        f"      url: {config.get('url')}\n"
                        f"      tools:\n"
                        f"        - list_tables\n"
                        f"        - query_data\n"
                        f"        - get_schema\n"
                        f"        - create_visualization\n"
                        f"        # ... add all tool names here",
                note="SSE-only servers require explicit tool configuration for Claude to see them",
            )
        else:
            # Log appropriately based on error type
            logger.error(
                "mcp_resource_discovery_failed",
                server_name=server_name,
                error=error_str[:200],
                error_type=type(e).__name__,
                sub_errors=sub_errors if sub_errors else None,
                is_sse_server=is_sse,
                is_timeout=is_timeout,
                note="Check SSE server connectivity and authentication.",
                exc_info=True,  # Include full traceback for debugging
            )

        return {
            "server_name": server_name,
            "tools": [],
            "resources": [],
            "prompts": [],
            "connected": False,
            "error": error_str[:200],
        }


async def discover_all_mcp_resources(mcp_servers: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Discover resources from configured MCP servers (verification and workaround).

    ⚠️ IMPORTANT: Different behavior per transport type:

    - HTTP servers: SKIPPED - SDK handles discovery natively (no workaround needed)
    - SSE servers: PRE-DISCOVERED - SDK bug #3426 requires manual discovery workaround
    - stdio servers: PRE-DISCOVERED - For verification/consistency

    ⚠️ WORKAROUND for Claude SDK Bug #3426:
    The Claude Agent SDK has a known bug where it fails to properly expose MCP tools
    from SSE servers to Claude during runtime. This function pre-discovers tools from
    SSE servers as a workaround.

    Args:
        mcp_servers: Dictionary of MCP server configurations {server_name: config}

    Returns:
        Dictionary mapping server names to their discovered resources

    See: https://github.com/anthropics/claude-code/issues/3426
    """
    if not mcp_servers:
        return {}

    # Count servers by type
    http_servers = [name for name, cfg in mcp_servers.items() if cfg.get("type") == "http"]
    sse_servers = [name for name, cfg in mcp_servers.items() if cfg.get("type") == "sse"]
    stdio_servers = [name for name, cfg in mcp_servers.items() if "command" in cfg]

    logger.info(
        "starting_mcp_resource_discovery",
        server_count=len(mcp_servers),
        server_names=list(mcp_servers.keys()),
        http_count=len(http_servers),
        sse_count=len(sse_servers),
        stdio_count=len(stdio_servers),
        note="HTTP: skipped (SDK native) | SSE: workaround | stdio: verification"
    )

    # Discover resources from all servers in parallel
    tasks = [
        discover_mcp_resources(server_name, config)
        for server_name, config in mcp_servers.items()
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build results dictionary
    discovered = {}
    for result in results:
        if isinstance(result, Exception):
            logger.error(
                "mcp_discovery_task_failed",
                error=str(result),
                error_type=type(result).__name__,
            )
            continue

        server_name = result["server_name"]
        discovered[server_name] = result

    # Log summary with proper categorization
    skipped_servers = [name for name, r in discovered.items() if r.get("skipped")]
    discovered_servers = [name for name, r in discovered.items() if not r.get("skipped")]

    total_tools = sum(len(r["tools"]) for r in discovered.values() if not r.get("skipped"))
    total_resources = sum(len(r["resources"]) for r in discovered.values() if not r.get("skipped"))
    total_prompts = sum(len(r["prompts"]) for r in discovered.values() if not r.get("skipped"))

    logger.info(
        "mcp_resource_discovery_complete",
        servers_total=len(discovered),
        servers_skipped=len(skipped_servers),
        servers_discovered=len(discovered_servers),
        skipped_server_names=skipped_servers,
        discovered_server_names=discovered_servers,
        total_tools=total_tools,
        total_resources=total_resources,
        total_prompts=total_prompts,
        note="HTTP servers skipped (SDK native) | SSE/stdio pre-discovered"
    )

    return discovered


def build_mcp_context_metadata(discovered_resources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build structured metadata about MCP capabilities to inject into execution context.

    ⚠️ WORKAROUND for Claude SDK Bug #3426:
    This function builds metadata from pre-discovered MCP resources so we can
    explicitly tell Claude about available MCP tools, resources, and prompts.

    Args:
        discovered_resources: Results from discover_all_mcp_resources()

    Returns:
        Structured metadata dict with all MCP capabilities
    """
    metadata = {
        "mcp_servers": {},
        "all_tools": [],
        "all_resources": [],
        "all_prompts": [],
    }

    for server_name, data in discovered_resources.items():
        if not data["connected"]:
            continue

        metadata["mcp_servers"][server_name] = {
            "tools_count": len(data["tools"]),
            "resources_count": len(data["resources"]),
            "prompts_count": len(data["prompts"]),
            "tools": data["tools"],
            "resources": data["resources"],
            "prompts": data["prompts"],
        }

        # Add prefixed tool names for reference
        for tool in data["tools"]:
            metadata["all_tools"].append({
                "server": server_name,
                "name": tool["name"],
                "full_name": f"mcp__{server_name}__{tool['name']}",
                "description": tool["description"],
                "inputSchema": tool["inputSchema"],
            })

        # Add resource URIs
        for resource in data["resources"]:
            metadata["all_resources"].append({
                "server": server_name,
                "uri": resource["uri"],
                "name": resource["name"],
                "description": resource["description"],
            })

        # Add prompts
        for prompt in data["prompts"]:
            metadata["all_prompts"].append({
                "server": server_name,
                "name": prompt["name"],
                "description": prompt["description"],
                "arguments": prompt["arguments"],
            })

    return metadata
