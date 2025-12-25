"""
Agno Service

This service provides integration with Agno for agent execution with MCP server support.
Agno enables dynamic MCP configuration at runtime, allowing agents to use different
MCP servers based on their configuration.
"""

import os
import json
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator
import logging
from agno.agent import Agent
from agno.team import Team
from agno.models.litellm import LiteLLM
from agno.tools.mcp import MCPTools
from agno.run.team import TeamRunOutputEvent
from agno.db.postgres import PostgresDb

logger = logging.getLogger(__name__)


class AgnoService:
    """Service for executing agents with Agno and MCP support"""

    def __init__(self):
        """Initialize Agno service with persistent session storage using Supabase PostgreSQL"""
        self.model_mapping = self._load_model_mapping()

        # Get PostgreSQL connection string from environment
        # This should be the direct database connection string from Supabase
        db_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")

        if db_url:
            self.db = PostgresDb(
                db_url=db_url,
                db_schema="agno",  # Use "agno" schema for Agno session data
            )

            logger.info(
                "Agno Service initialized with PostgreSQL session storage",
                extra={
                    "model_mappings": len(self.model_mapping),
                    "db_schema": "agno",
                }
            )
        else:
            logger.warning(
                "DATABASE_URL or SUPABASE_DB_URL not set, Agno sessions will not persist",
                extra={"model_mappings": len(self.model_mapping)}
            )
            self.db = None

    def _load_model_mapping(self) -> Dict[str, str]:
        """
        Load model mapping from models.json.
        Maps kubiya/ prefix models to actual LiteLLM provider models.
        """
        try:
            models_file = Path(__file__).parent.parent.parent / "models.json"
            if models_file.exists():
                with open(models_file, "r") as f:
                    mapping = json.load(f)
                    logger.info(f"Loaded model mapping from {models_file}", extra={"mappings": mapping})
                    return mapping
            else:
                logger.warning(f"Model mapping file not found at {models_file}, using empty mapping")
                return {}
        except Exception as e:
            logger.error(f"Failed to load model mapping: {str(e)}")
            return {}

    def _resolve_model(self, model: str) -> str:
        """
        Resolve kubiya/ prefixed models to actual LiteLLM provider models.

        Args:
            model: Model identifier (e.g., "kubiya/claude-sonnet-4")

        Returns:
            Resolved model identifier (e.g., "anthropic/claude-sonnet-4-20250514")
        """
        if model in self.model_mapping:
            resolved = self.model_mapping[model]
            logger.info(f"Resolved model: {model} -> {resolved}")
            return resolved

        # If no mapping found, return as-is (for backward compatibility)
        logger.info(f"No mapping found for model: {model}, using as-is")
        return model

    async def _build_mcp_tools_async(self, mcp_config: Dict[str, Any]) -> List[Any]:
        """
        Build and connect to MCP tools from agent configuration (async).

        Args:
            mcp_config: MCP servers configuration from agent.configuration.mcpServers

        Returns:
            List of connected MCP tool instances
        """
        mcp_tools = []

        if not mcp_config:
            logger.info("No MCP servers configured, agent will run without MCP tools")
            return mcp_tools

        logger.info(
            f"Building MCP tools from {len(mcp_config)} MCP server configurations",
            extra={
                "mcp_server_count": len(mcp_config),
                "mcp_server_ids": list(mcp_config.keys()),
            }
        )

        for server_id, server_config in mcp_config.items():
            try:
                # Determine transport type
                if "url" in server_config:
                    # SSE/HTTP transport
                    mcp_tool = MCPTools(
                        url=server_config["url"],
                        headers=server_config.get("headers", {}),
                    )
                    logger.info(
                        f"Configured MCP server '{server_id}' with SSE transport",
                        extra={"url": server_config["url"]}
                    )
                else:
                    # stdio transport - build full command with args using proper shell escaping
                    command = server_config.get("command")
                    args = server_config.get("args", [])
                    env = server_config.get("env", {})

                    # Build full command string with proper shell escaping
                    # Using shlex.quote() to safely handle args with spaces and special characters
                    full_command = shlex.quote(command)

                    # Args can be a list or already a string
                    if isinstance(args, list) and args:
                        # Properly escape each argument
                        escaped_args = ' '.join(shlex.quote(str(arg)) for arg in args)
                        full_command = f"{shlex.quote(command)} {escaped_args}"
                    elif isinstance(args, str) and args:
                        # If args is a string, assume it's already properly formatted or escape it
                        full_command = f"{shlex.quote(command)} {shlex.quote(args)}"

                    mcp_tool = MCPTools(
                        command=full_command,
                        env=env,
                    )
                    logger.info(
                        f"Configured MCP server '{server_id}' with stdio transport",
                        extra={
                            "command": command,
                            "args": args,
                            "full_command": full_command
                        }
                    )

                # Connect to the MCP server
                await mcp_tool.connect()
                mcp_tools.append(mcp_tool)
                logger.info(f"Successfully connected to MCP server '{server_id}'")

            except Exception as e:
                import traceback
                error_details = {
                    "server_id": server_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                    "config": {
                        "command": server_config.get("command") if "command" in server_config else None,
                        "url": server_config.get("url") if "url" in server_config else None,
                    }
                }
                logger.error(
                    f"Failed to configure MCP server '{server_id}': {str(e)}",
                    extra=error_details
                )
                # Continue with other servers even if one fails

        logger.info(
            f"Built {len(mcp_tools)} MCP tools from {len(mcp_config)} server configurations",
            extra={
                "mcp_tool_count": len(mcp_tools),
                "total_servers_configured": len(mcp_config),
                "connection_success_rate": f"{len(mcp_tools)}/{len(mcp_config)}"
            }
        )

        return mcp_tools

    async def _build_skill_tools(self, skill_defs: List[Dict[str, Any]]) -> List[Any]:
        """
        Build OS-level skill tools from skill definitions.

        Args:
            skill_defs: List of resolved skill definitions with configurations

        Returns:
            List of instantiated skill tool instances
        """
        # Import agno OS-level tools
        try:
            from agno.tools.file import FileTools
            from agno.tools.shell import ShellTools
            from agno.tools.docker import DockerTools
            from agno.tools.sleep import SleepTools
            from agno.tools.file_generation import FileGenerationTools
        except ImportError as e:
            logger.error(f"Failed to import agno tools: {str(e)}")
            return []

        # Tool registry mapping skill types to agno tool classes
        SKILL_REGISTRY = {
            "file_system": FileTools,
            "shell": ShellTools,
            "docker": DockerTools,
            "sleep": SleepTools,
            "file_generation": FileGenerationTools,
        }

        tools = []

        if not skill_defs:
            logger.info("No skill definitions provided, agent will run without OS-level tools")
            return tools

        logger.info(
            f"Building skill tools from {len(skill_defs)} skill definitions",
            extra={
                "skill_count": len(skill_defs),
                "skill_names": [t.get("name") for t in skill_defs],
                "skill_types": [t.get("type") for t in skill_defs],
                "skill_sources": [t.get("source") for t in skill_defs],
            }
        )

        for skill_def in skill_defs:
            if not skill_def.get("enabled", True):
                logger.debug(
                    f"Skipping disabled skill",
                    extra={"skill_name": skill_def.get("name")}
                )
                continue

            skill_type = skill_def.get("type")
            tool_class = SKILL_REGISTRY.get(skill_type)

            if not tool_class:
                logger.warning(
                    f"Unknown skill type: {skill_type}",
                    extra={
                        "skill_type": skill_type,
                        "skill_name": skill_def.get("name")
                    }
                )
                continue

            # Get configuration from skill definition
            config = skill_def.get("configuration", {})

            # Instantiate tool with configuration
            try:
                tool_instance = tool_class(**config)
                tools.append(tool_instance)

                logger.info(
                    f"Skill instantiated: {skill_def.get('name')}",
                    extra={
                        "skill_name": skill_def.get("name"),
                        "skill_type": skill_type,
                        "source": skill_def.get("source"),
                        "configuration": config
                    }
                )
            except Exception as e:
                import traceback
                logger.error(
                    f"Failed to instantiate skill '{skill_def.get('name')}': {str(e)}",
                    extra={
                        "skill_name": skill_def.get("name"),
                        "skill_type": skill_type,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "traceback": traceback.format_exc(),
                    }
                )
                # Continue with other tools even if one fails

        logger.info(
            f"Built {len(tools)} skill tools",
            extra={
                "tool_count": len(tools),
                "tool_types": [type(t).__name__ for t in tools]
            }
        )

        return tools

    async def _build_context_graph_skill(
        self,
        graph_api_url: str,
        api_key: str,
        organization_id: str,
        dataset_name: str,
    ) -> List[Any]:
        """
        Build context graph skill (memory + search tools).

        Args:
            graph_api_url: Context graph API base URL
            api_key: Kubiya API key
            organization_id: Organization ID
            dataset_name: Dataset name (from environment)

        Returns:
            List containing ContextGraphSkill instance
        """
        from control_plane_api.app.services.toolsets.context_graph_skill import ContextGraphSkill

        tools = []

        if not graph_api_url or not api_key:
            logger.warning(
                "context_graph_skill_not_configured",
                extra={
                    "message": "Missing graph API URL or API key",
                    "has_url": bool(graph_api_url),
                    "has_key": bool(api_key)
                }
            )
            return tools

        try:
            context_skill = ContextGraphSkill(
                graph_api_url=graph_api_url,
                api_key=api_key,
                organization_id=organization_id,
                dataset_name=dataset_name,
                auto_create_dataset=True,
            )

            tools.append(context_skill)

            logger.info(
                "context_graph_skill_initialized",
                extra={
                    "dataset_name": dataset_name,
                    "organization_id": organization_id,
                    "graph_api_url": graph_api_url,
                }
            )
        except Exception as e:
            import traceback
            logger.error(
                "context_graph_skill_failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                }
            )

        return tools

    async def _recall_relevant_memories(
        self,
        prompt: str,
        graph_api_url: str,
        api_key: str,
        organization_id: str,
        dataset_name: str,
        limit: int = 3,
    ) -> Optional[str]:
        """
        Recall relevant memories based on the user prompt.

        Args:
            prompt: User's prompt to search for relevant memories
            graph_api_url: Context graph API URL
            api_key: API key for authentication
            organization_id: Organization ID
            dataset_name: Dataset name for scoping
            limit: Maximum number of memories to recall

        Returns:
            Formatted string of recalled memories or None if no memories found
        """
        try:
            import httpx

            # First, check if dataset exists
            headers = {
                "Authorization": f"Bearer {api_key}",
                "X-Organization-ID": organization_id,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                # List datasets to find ours
                response = await client.get(
                    f"{graph_api_url}/api/v1/datasets",
                    headers=headers,
                )

                if response.status_code != 200:
                    logger.debug("Failed to list datasets for memory recall", status_code=response.status_code)
                    return None

                datasets = response.json()
                dataset_id = None
                for ds in datasets:
                    if ds.get("name") == dataset_name:
                        dataset_id = ds["id"]
                        break

                if not dataset_id:
                    logger.debug("Dataset not found for memory recall", dataset_name=dataset_name)
                    return None

                # Recall memories using the user prompt as query
                recall_response = await client.post(
                    f"{graph_api_url}/api/v1/memory/recall",
                    headers=headers,
                    json={
                        "query": prompt,
                        "dataset_id": dataset_id,
                        "limit": limit,
                    },
                    timeout=5.0,
                )

                if recall_response.status_code != 200:
                    logger.debug("Memory recall request failed", status_code=recall_response.status_code)
                    return None

                memories = recall_response.json()

                if not memories or len(memories) == 0:
                    logger.debug("No relevant memories found", query=prompt[:50])
                    return None

                # Format memories for injection
                formatted = "\n\n---\n**📚 Related memories found:**\n"
                for i, memory in enumerate(memories, 1):
                    content = memory.get('content', memory.get('text', 'N/A'))
                    formatted += f"\n{i}. {content}"
                    if memory.get('metadata'):
                        formatted += f"\n   _Metadata: {memory['metadata']}_"
                formatted += "\n---\n"

                logger.info(
                    "recalled_memories_for_context",
                    count=len(memories),
                    query=prompt[:50],
                    dataset_name=dataset_name,
                )

                return formatted

        except Exception as e:
            logger.warning(
                "memory_recall_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    async def execute_agent_async(
        self,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        mcp_servers: Optional[Dict[str, Any]] = None,
        skills: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        graph_api_url: Optional[str] = None,
        dataset_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute an agent using Agno Teams with MCP and OS-level skill support and session management.

        Args:
            prompt: The user prompt (for single-turn conversations)
            model: Model identifier
            system_prompt: System prompt for the agent
            mcp_servers: MCP servers configuration dict
            skills: List of resolved skill definitions (OS-level tools)
            temperature: Temperature for response generation
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            conversation_history: Full conversation history (for multi-turn conversations) - DEPRECATED, use session_id instead
            session_id: Session ID for multi-turn conversations (enables Agno session management)
            user_id: User ID for multi-user support
            graph_api_url: Context graph API base URL for memory tools
            dataset_name: Dataset name for memory scoping (typically environment name)
            organization_id: Organization ID for API authentication
            api_key: API key for graph API authentication
            **kwargs: Additional parameters

        Returns:
            Dict containing the response and metadata including session messages
        """
        mcp_tools = []
        skill_tools = []
        try:
            # Use default model if not specified
            if not model:
                model = os.environ.get("LITELLM_DEFAULT_MODEL", "claude-sonnet-4")

            # Build and connect to MCP tools from configuration
            mcp_tools = await self._build_mcp_tools_async(mcp_servers or {})

            # Build OS-level skill tools
            skill_tools = await self._build_skill_tools(skills or [])

            # Build context graph skill (memory + search)
            context_graph_tools = []
            if graph_api_url and dataset_name and organization_id and api_key:
                context_graph_tools = await self._build_context_graph_skill(
                    graph_api_url=graph_api_url,
                    api_key=api_key,
                    organization_id=organization_id,
                    dataset_name=dataset_name,
                )

                # Automatically recall relevant memories and inject into prompt
                if prompt:
                    recalled_memories = await self._recall_relevant_memories(
                        prompt=prompt,
                        graph_api_url=graph_api_url,
                        api_key=api_key,
                        organization_id=organization_id,
                        dataset_name=dataset_name,
                        limit=3,
                    )

                    if recalled_memories:
                        # Inject recalled memories into the prompt
                        prompt = f"{prompt}{recalled_memories}"
                        logger.info(
                            "injected_recalled_memories_into_prompt",
                            extra={
                                "original_prompt_length": len(prompt) - len(recalled_memories),
                                "recalled_memories_length": len(recalled_memories),
                                "dataset_name": dataset_name,
                            }
                        )

            # Create LiteLLM model instance
            # IMPORTANT: Use openai/ prefix for custom proxy compatibility
            litellm_model = LiteLLM(
                id=f"openai/{model}",
                api_base=os.environ.get("LITELLM_API_BASE", "https://llm-proxy.kubiya.ai"),
                api_key=os.environ.get("LITELLM_API_KEY"),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Create specialized agent members for MCP tools
            members = []
            if mcp_tools:
                # Create a specialized agent for each MCP tool
                for idx, tool in enumerate(mcp_tools):
                    member = Agent(
                        name=f"MCP Agent {idx+1}",
                        role="Execute MCP tool operations",
                        tools=[tool],
                        model=litellm_model,
                    )
                    members.append(member)
                logger.info(
                    f"Created {len(members)} specialized MCP agents",
                    extra={
                        "mcp_agent_count": len(members),
                        "mcp_tools_per_agent": [1] * len(members)
                    }
                )

            # Combine all tools: MCP tools + OS-level skill tools + context graph tools
            all_tools = mcp_tools + skill_tools + context_graph_tools
            logger.info(
                f"Total tools available: {len(all_tools)} (MCP: {len(mcp_tools)}, Skills: {len(skill_tools)}, Context Graph: {len(context_graph_tools)})",
                extra={
                    "mcp_tool_count": len(mcp_tools),
                    "skill_tool_count": len(skill_tools),
                    "context_graph_tool_count": len(context_graph_tools),
                    "total_tools": len(all_tools)
                }
            )

            # Create the team with database for session management
            # The team itself gets all tools (both MCP and OS-level skills)
            logger.info(
                f"Creating Agent Execution Team with {len(members)} MCP agents and {len(all_tools)} total tools",
                extra={
                    "team_members": len(members),
                    "total_tools": len(all_tools),
                    "mcp_tools": len(mcp_tools),
                    "skill_tools": len(skill_tools),
                    "session_enabled": bool(session_id),
                    "session_id": session_id,
                    "user_id": user_id,
                    "model": model,
                }
            )

            team = Team(
                name="Agent Execution Team",
                members=members,
                tools=all_tools,  # Add all tools to the team
                model=litellm_model,
                instructions=system_prompt or ["You are a helpful AI assistant."],
                markdown=True,
                db=self.db,  # Enable session storage
                add_history_to_context=True,  # Automatically add history to context
                num_history_runs=5,  # Include last 5 runs in context
                read_team_history=True,  # Enable reading team history
            )

            logger.info(
                f"Team created successfully with session management enabled",
                extra={
                    "team_name": team.name,
                    "team_id": id(team),
                }
            )

            # For session-based conversations, just use the current prompt
            # Agno will automatically handle the conversation history through sessions
            if not prompt:
                raise ValueError("'prompt' is required for session-based conversations")

            input_text = prompt
            logger.info(
                f"Executing team with Agno. Model: {model}, Members: {len(members)}, MCP tools: {len(mcp_tools)}, Session: {session_id}, User: {user_id}"
            )

            # Execute team with session support (use arun for async)
            run_kwargs = {}
            if session_id:
                run_kwargs["session_id"] = session_id
            if user_id:
                run_kwargs["user_id"] = user_id

            if stream:
                # For streaming, collect all chunks AND publish to Redis for real-time UI
                response_stream: Iterator[TeamRunOutputEvent] = team.arun(
                    input_text,
                    stream=True,
                    stream_intermediate_steps=True,
                    **run_kwargs
                )

                # Generate unique message ID for this streaming turn
                import time
                message_id = f"{session_id}_{int(time.time() * 1000000)}" if session_id else f"msg_{int(time.time() * 1000000)}"

                # Publish chunks to Redis for real-time UI updates
                from control_plane_api.app.lib.redis_client import get_redis_client
                from datetime import datetime, timezone
                import json as json_lib

                redis_client = get_redis_client()

                content_chunks = []
                async for chunk in response_stream:
                    if chunk.event == "TeamRunContent" and chunk.content:
                        content_chunks.append(chunk.content)

                        # Publish chunk to Redis immediately for real-time UI
                        if redis_client and session_id:  # session_id acts as execution_id
                            try:
                                redis_key = f"execution:{session_id}:events"
                                event_data = {
                                    "event_type": "message_chunk",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "data": {
                                        "role": "assistant",
                                        "content": chunk.content,  # Delta chunk, not accumulated
                                        "is_chunk": True,
                                        "message_id": message_id,
                                    }
                                }
                                await redis_client.lpush(redis_key, json_lib.dumps(event_data))
                                await redis_client.ltrim(redis_key, 0, 999)  # Keep last 1000 events
                                await redis_client.expire(redis_key, 3600)  # 1 hour TTL
                            except Exception as redis_error:
                                # Don't fail execution if Redis publish fails
                                logger.debug("redis_chunk_publish_failed", error=str(redis_error), session_id=session_id)

                content = "".join(content_chunks)

                # Get the final response object
                response = await team.arun(input_text, stream=False, **run_kwargs)
            else:
                # Non-streaming execution with session
                response = await team.arun(input_text, **run_kwargs)
                content = response.content

            # Extract usage from metrics if available
            usage = {}
            if hasattr(response, 'metrics') and response.metrics:
                usage = {
                    "prompt_tokens": getattr(response.metrics, 'input_tokens', 0),
                    "completion_tokens": getattr(response.metrics, 'output_tokens', 0),
                    "total_tokens": getattr(response.metrics, 'total_tokens', 0),
                }

            # Get session messages if session_id was provided
            messages = []
            if session_id and self.db:
                try:
                    # Fetch all messages for this session from Agno's database
                    session_messages = team.get_messages_for_session(session_id=session_id)
                    messages = [
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "timestamp": msg.created_at if hasattr(msg, 'created_at') else None,
                        }
                        for msg in session_messages
                    ]
                    logger.info(f"Retrieved {len(messages)} messages from session {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to retrieve session messages: {str(e)}")

            result = {
                "success": True,
                "response": content,
                "model": model,
                "usage": usage,
                "finish_reason": "stop",
                "mcp_tools_used": len(mcp_tools),
                "run_id": getattr(response, 'run_id', None),
                "session_id": session_id,
                "messages": messages,  # Include full session history
            }

            logger.info(
                f"Team execution successful",
                extra={
                    "mcp_tools": len(mcp_tools),
                    "members": len(members),
                    "session_messages": len(messages)
                }
            )
            return result

        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            error_type = type(e).__name__

            logger.error(f"Error executing team with Agno: {str(e)}")
            logger.error(f"Error type: {error_type}")
            logger.error(f"Traceback: {error_traceback}")

            return {
                "success": False,
                "error": str(e),
                "error_type": error_type,
                "error_traceback": error_traceback,
                "model": model or os.environ.get("LITELLM_DEFAULT_MODEL", "kubiya/claude-sonnet-4"),
                "mcp_tools_used": 0,
            }
        finally:
            # Close all MCP connections
            for mcp_tool in mcp_tools:
                try:
                    await mcp_tool.close()
                except Exception as e:
                    logger.warning(f"Failed to close MCP tool: {str(e)}")

    def execute_agent(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        mcp_servers: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Sync wrapper for execute_agent_async.

        Args:
            prompt: The user prompt
            model: Model identifier
            system_prompt: System prompt for the agent
            mcp_servers: MCP servers configuration dict
            temperature: Temperature for response generation
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            Dict containing the response and metadata
        """
        import asyncio

        # Always create a new event loop for isolation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(
                self.execute_agent_async(
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt,
                    mcp_servers=mcp_servers,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    **kwargs,
                )
            )
        finally:
            loop.close()


# Singleton instance
agno_service = AgnoService()
