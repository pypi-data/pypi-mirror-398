"""
MCP server builder for Agno runtime.

This module converts MCP server configurations from the execution environment
into Agno MCPTools instances.
"""

import shlex
import structlog
from typing import Dict, Any, List, Optional

logger = structlog.get_logger(__name__)


def build_agno_mcp_tools(
    mcp_servers: Optional[Dict[str, Any]] = None,
) -> List[Any]:
    """
    Build Agno MCPTools instances from MCP server configurations.

    Converts MCP server configs from our format to Agno's MCPTools format:
    - stdio: command, args, env -> MCPTools(command="...", env={...})
    - http/sse: url, headers -> MCPTools(transport="...", url="...", env={...})

    Args:
        mcp_servers: Dict of MCP server configurations from execution environment

    Returns:
        List of MCPTools instances (not connected yet)
    """
    if not mcp_servers:
        logger.debug("No MCP servers to build for Agno runtime")
        return []

    try:
        from agno.tools.mcp import MCPTools
    except ImportError:
        logger.warning(
            "agno.tools.mcp not available - MCP support disabled",
            mcp_server_count=len(mcp_servers),
        )
        return []

    mcp_tools_instances = []

    for server_name, server_config in mcp_servers.items():
        try:
            # Determine transport type
            transport_type = server_config.get("transport_type", "stdio")

            if transport_type == "stdio":
                # Build stdio MCPTools instance
                command = server_config.get("command")
                args = server_config.get("args", [])
                env = server_config.get("env", {})

                if not command:
                    logger.warning(
                        "stdio_mcp_server_missing_command",
                        server_name=server_name,
                    )
                    continue

                # Build full command string with proper shell escaping
                # Using shlex.quote() to safely handle args with spaces and special characters
                full_command = shlex.quote(command)
                if args:
                    # Properly escape each argument
                    escaped_args = ' '.join(shlex.quote(str(arg)) for arg in args)
                    full_command = f"{shlex.quote(command)} {escaped_args}"

                logger.info(
                    "building_stdio_mcp_tools",
                    server_name=server_name,
                    command=command,
                    args=args,
                    full_command=full_command,
                    has_env=bool(env),
                )

                mcp_tool = MCPTools(
                    command=full_command,
                    env=env if env else None,
                )
                # Store server name for logging
                mcp_tool._server_name = server_name
                mcp_tools_instances.append(mcp_tool)

            elif transport_type in ("http", "sse"):
                # Build HTTP/SSE MCPTools instance
                url = server_config.get("url")
                headers = server_config.get("headers", {})

                if not url:
                    logger.warning(
                        "http_sse_mcp_server_missing_url",
                        server_name=server_name,
                        transport_type=transport_type,
                    )
                    continue

                # Use streamable-http for both http and sse (SSE standalone is deprecated)
                agno_transport = "streamable-http"

                # Normalize URL: remove /sse suffix if present (old SSE endpoint)
                # Streamable HTTP uses the base /mcp endpoint
                original_url = url
                if url.endswith("/sse"):
                    url = url[:-4]  # Remove /sse suffix
                    logger.info(
                        "mcp_url_normalized",
                        server_name=server_name,
                        original_url=original_url,
                        normalized_url=url,
                        reason="Streamable HTTP uses base /mcp endpoint",
                    )

                if transport_type == "sse":
                    logger.info(
                        "sse_transport_mapped_to_streamable_http",
                        server_name=server_name,
                        reason="SSE standalone transport is deprecated in Agno",
                    )

                logger.info(
                    "building_http_sse_mcp_tools",
                    server_name=server_name,
                    transport=agno_transport,
                    url=url,
                    has_headers=bool(headers),
                )

                # Use StreamableHTTPClientParams to properly pass headers
                if headers:
                    try:
                        from agno.tools.mcp import StreamableHTTPClientParams

                        server_params = StreamableHTTPClientParams(
                            url=url,
                            headers=headers,
                        )
                        mcp_tool = MCPTools(
                            server_params=server_params,
                            transport=agno_transport,
                        )

                        logger.debug(
                            "mcp_tools_created_with_headers",
                            server_name=server_name,
                            header_count=len(headers),
                        )
                    except ImportError:
                        logger.warning(
                            "streamable_http_params_not_available",
                            server_name=server_name,
                            fallback="creating without headers",
                        )
                        mcp_tool = MCPTools(
                            transport=agno_transport,
                            url=url,
                        )
                else:
                    # No headers, simple initialization
                    mcp_tool = MCPTools(
                        transport=agno_transport,
                        url=url,
                    )

                # Store server name for logging
                mcp_tool._server_name = server_name
                mcp_tools_instances.append(mcp_tool)

            else:
                logger.warning(
                    "unknown_mcp_transport_type",
                    server_name=server_name,
                    transport_type=transport_type,
                )
                continue

        except Exception as e:
            logger.error(
                "failed_to_build_mcp_tool",
                server_name=server_name,
                error=str(e),
            )
            continue

    logger.info(
        "agno_mcp_tools_built",
        mcp_tools_count=len(mcp_tools_instances),
        server_names=[getattr(t, '_server_name', t.name) for t in mcp_tools_instances] if mcp_tools_instances else [],
    )

    return mcp_tools_instances
