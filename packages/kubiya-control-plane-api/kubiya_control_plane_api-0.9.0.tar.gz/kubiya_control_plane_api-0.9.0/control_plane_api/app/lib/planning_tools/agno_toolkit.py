"""
Agno Planning Toolkit - Synchronous tools for task planning with internal service integration

This module follows the Agno Toolkit pattern with internal service access:
- Tools are synchronous (not async) for proper Agno workflow compatibility
- Uses PlanningService with direct DB access (no HTTP self-calls)
- Returns structured JSON for reliable parsing
- Proper tool registration via Toolkit base class

Architecture:
- Agents/Teams: Direct DB queries via PlanningService (fast, no HTTP)
- Context Graph: HTTP to external graph.kubiya.ai (correct for external service)
"""

import json
import structlog
import asyncio
import hashlib
import redis
from typing import Optional
from functools import wraps
from sqlalchemy.orm import Session
from agno.tools.toolkit import Toolkit

from control_plane_api.app.lib.planning_tools.planning_service import PlanningService
from control_plane_api.app.config import settings

logger = structlog.get_logger(__name__)

# Initialize Redis client for caching (lazy connection)
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    CACHE_ENABLED = True
except Exception as e:
    logger.warning("redis_connection_failed", error=str(e), message="Tool caching disabled")
    redis_client = None
    CACHE_ENABLED = False


def cache_tool_result(ttl: int = 60):
    """
    Cache tool results in Redis for specified TTL.

    Args:
        ttl: Time-to-live in seconds (default: 60)

    Returns:
        Decorator function that wraps tool methods with caching
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # If caching disabled, call function directly
            if not CACHE_ENABLED or redis_client is None:
                return func(self, *args, **kwargs)

            # Generate cache key from function name, organization, and args
            cache_parts = [
                func.__name__,
                self.organization_id,
                str(args),
                str(sorted(kwargs.items()))
            ]
            cache_string = "|".join(cache_parts)
            cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
            cache_key = f"tool_cache:{func.__name__}:{cache_hash}"

            try:
                # Try to get from cache
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info("tool_cache_hit", tool=func.__name__, organization=self.organization_id[:8])
                    return cached
            except Exception as e:
                logger.warning("redis_get_error", error=str(e), key=cache_key)

            # Execute function
            result = func(self, *args, **kwargs)

            # Cache result
            try:
                redis_client.setex(cache_key, ttl, result)
                logger.debug("tool_cache_set", tool=func.__name__, ttl=ttl)
            except Exception as e:
                logger.warning("redis_set_error", error=str(e), key=cache_key)

            return result

        return wrapper
    return decorator


class PlanningToolkit(Toolkit):
    """
    Custom toolkit for task planning with auto-registered tools.

    CRITICAL: Service must be initialized BEFORE calling super().__init__()
    so it's available when tools are registered.

    This uses internal services directly (no HTTP self-calls).
    """

    def __init__(
        self,
        db: Session,
        organization_id: str,
        api_token: str,
        name: str = "planning_tools"
    ):
        """
        Initialize planning toolkit with internal services.

        Args:
            db: SQLAlchemy database session
            organization_id: Organization ID for filtering
            api_token: Org-scoped API token
            name: Toolkit name for Agno
        """
        # CRITICAL: Initialize service BEFORE calling super().__init__()
        self.planning_service = PlanningService(
            db=db,
            organization_id=organization_id,
            api_token=api_token
        )
        self.organization_id = organization_id

        # Create tools list for auto-registration
        tools = [
            self.list_agents,
            self.list_teams,
            self.search_agents_by_capability,
            self.search_teams_by_capability,
            self.get_agent_details,
            self.get_team_details,
            self.list_environments,
            self.list_worker_queues,
            self.search_context_graph,
            self.get_fallback_agent,  # NEW: Fallback for when no perfect match found
        ]

        # Pass to parent for auto-registration
        # This registers each method in self.functions dict
        super().__init__(name=name, tools=tools)

        logger.info(
            "planning_toolkit_initialized",
            tool_count=len(tools),
            organization_id=organization_id[:8]
        )

    @cache_tool_result(ttl=60)  # Cache for 60 seconds
    def list_agents(self, limit: int = 20) -> str:
        """List available agents in the organization.

        Use this to discover what agents are available for executing tasks.

        Args:
            limit: Maximum number of agents to return (default: 20)

        Returns:
            JSON string with structured agent data and human-readable format
        """
        try:
            # Call service method (direct DB query)
            agents = self.planning_service.list_agents(limit=limit)

            # Format human-readable output
            if not agents:
                human_readable = "No active agents found in the organization."
            else:
                human_readable = f"Found {len(agents)} active agents:\n\n"
                for i, agent in enumerate(agents, 1):
                    human_readable += f"Agent {i}:\n"
                    human_readable += f"  ID: {agent.get('id')}\n"
                    human_readable += f"  Name: {agent.get('name')}\n"
                    human_readable += f"  Model: {agent.get('model_id', 'default')}\n"
                    human_readable += f"  Description: {agent.get('description', 'N/A')}\n"

                    capabilities = agent.get('capabilities', [])
                    if capabilities:
                        human_readable += f"  Capabilities: {', '.join(capabilities)}\n"
                    human_readable += "\n"

            # Return structured JSON
            result = {
                "type": "tool_result",
                "tool": "list_agents",
                "success": True,
                "data": {
                    "agents": agents,
                    "count": len(agents)
                },
                "human_readable": human_readable
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error("list_agents_tool_error", error=str(e), exc_info=True)
            return json.dumps({
                "type": "tool_result",
                "tool": "list_agents",
                "success": False,
                "error": str(e)
            })

    @cache_tool_result(ttl=60)  # Cache for 60 seconds
    def list_teams(self, limit: int = 20) -> str:
        """List available teams in the organization.

        Use this to discover what teams are available for executing multi-agent tasks.

        Args:
            limit: Maximum number of teams to return (default: 20)

        Returns:
            JSON string with structured team data and human-readable format
        """
        try:
            # Call service method (direct DB query)
            teams = self.planning_service.list_teams(limit=limit)

            # Format human-readable output
            if not teams:
                human_readable = "No active teams found in the organization."
            else:
                human_readable = f"Found {len(teams)} active teams:\n\n"
                for i, team in enumerate(teams, 1):
                    human_readable += f"Team {i}:\n"
                    human_readable += f"  ID: {team.get('id')}\n"
                    human_readable += f"  Name: {team.get('name')}\n"
                    human_readable += f"  Description: {team.get('description', 'N/A')}\n"
                    human_readable += f"  Agent Count: {team.get('agent_count', 0)}\n"

                    agents = team.get('agents', [])
                    if agents:
                        agent_names = [a.get('name', 'Unknown') for a in agents[:5]]
                        human_readable += f"  Members: {', '.join(agent_names)}\n"
                    human_readable += "\n"

            # Return structured JSON
            result = {
                "type": "tool_result",
                "tool": "list_teams",
                "success": True,
                "data": {
                    "teams": teams,
                    "count": len(teams)
                },
                "human_readable": human_readable
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error("list_teams_tool_error", error=str(e), exc_info=True)
            return json.dumps({
                "type": "tool_result",
                "tool": "list_teams",
                "success": False,
                "error": str(e)
            })

    def search_agents_by_capability(
        self,
        capability: str,
        limit: int = 10
    ) -> str:
        """Search for agents that have a specific capability or skill.

        Use this to find agents with required skills like 'kubernetes', 'aws', 'python', etc.

        Args:
            capability: Skill or capability name to search for (required)
            limit: Maximum number of agents to return (default: 10)

        Returns:
            JSON string with structured agent data and human-readable format
        """
        try:
            # Call service method (direct DB query)
            agents = self.planning_service.search_agents_by_capability(
                capability=capability,
                limit=limit
            )

            # Format human-readable output
            if not agents:
                human_readable = f"No agents found with capability '{capability}'."
            else:
                human_readable = f"Found {len(agents)} agents with '{capability}' capability:\n\n"
                for i, agent in enumerate(agents, 1):
                    human_readable += f"Agent {i}:\n"
                    human_readable += f"  ID: {agent.get('id')}\n"
                    human_readable += f"  Name: {agent.get('name')}\n"
                    human_readable += f"  Model: {agent.get('model_id', 'default')}\n"
                    human_readable += f"  Description: {agent.get('description', 'N/A')}\n"

                    capabilities = agent.get('capabilities', [])
                    if capabilities:
                        human_readable += f"  All Capabilities: {', '.join(capabilities)}\n"
                    human_readable += "\n"

            # Return structured JSON
            result = {
                "type": "tool_result",
                "tool": "search_agents_by_capability",
                "success": True,
                "data": {
                    "agents": agents,
                    "count": len(agents),
                    "query": {
                        "capability": capability
                    }
                },
                "human_readable": human_readable
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error("search_agents_by_capability_tool_error", error=str(e), exc_info=True)
            return json.dumps({
                "type": "tool_result",
                "tool": "search_agents_by_capability",
                "success": False,
                "error": str(e)
            })

    def search_teams_by_capability(
        self,
        capability: str,
        limit: int = 5
    ) -> str:
        """Search for teams that have agents with a specific capability.

        Use this to find teams for multi-agent tasks requiring specific skills.

        Args:
            capability: Skill or capability name to search for (required)
            limit: Maximum number of teams to return (default: 5)

        Returns:
            JSON string with structured team data and human-readable format
        """
        try:
            # Call service method (direct DB query)
            teams = self.planning_service.search_teams_by_capability(
                capability=capability,
                limit=limit
            )

            # Format human-readable output
            if not teams:
                human_readable = f"No teams found with capability '{capability}'."
            else:
                human_readable = f"Found {len(teams)} teams with '{capability}' capability:\n\n"
                for i, team in enumerate(teams, 1):
                    human_readable += f"Team {i}:\n"
                    human_readable += f"  ID: {team.get('id')}\n"
                    human_readable += f"  Name: {team.get('name')}\n"
                    human_readable += f"  Description: {team.get('description', 'N/A')}\n"
                    human_readable += f"  Agent Count: {team.get('agent_count', 0)}\n"

                    agents = team.get('agents', [])
                    if agents:
                        agent_names = [a.get('name', 'Unknown') for a in agents[:5]]
                        human_readable += f"  Members: {', '.join(agent_names)}\n"
                    human_readable += "\n"

            # Return structured JSON
            result = {
                "type": "tool_result",
                "tool": "search_teams_by_capability",
                "success": True,
                "data": {
                    "teams": teams,
                    "count": len(teams),
                    "query": {
                        "capability": capability
                    }
                },
                "human_readable": human_readable
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error("search_teams_by_capability_tool_error", error=str(e), exc_info=True)
            return json.dumps({
                "type": "tool_result",
                "tool": "search_teams_by_capability",
                "success": False,
                "error": str(e)
            })

    def get_agent_details(self, agent_id: str) -> str:
        """Get complete details for a specific agent.

        Use this after finding relevant agents to get full execution environment details.

        Args:
            agent_id: Agent ID to fetch (required)

        Returns:
            JSON string with full agent details and human-readable format
        """
        try:
            if not agent_id:
                return json.dumps({
                    "type": "tool_result",
                    "tool": "get_agent_details",
                    "success": False,
                    "error": "agent_id is required"
                })

            # Call service method (direct DB query)
            agent = self.planning_service.get_agent_details(agent_id=agent_id)

            if not agent:
                return json.dumps({
                    "type": "tool_result",
                    "tool": "get_agent_details",
                    "success": False,
                    "error": f"Agent {agent_id} not found"
                })

            # Format human-readable output
            human_readable = f"Agent Details:\n"
            human_readable += f"  ID: {agent.get('id')}\n"
            human_readable += f"  Name: {agent.get('name')}\n"
            human_readable += f"  Model: {agent.get('model_id', 'default')}\n"
            human_readable += f"  Status: {agent.get('status')}\n"
            human_readable += f"  Description: {agent.get('description', 'N/A')}\n"

            capabilities = agent.get('capabilities', [])
            if capabilities:
                human_readable += f"  Capabilities: {', '.join(capabilities)}\n"

            skills = agent.get('skills', [])
            if skills:
                human_readable += f"  Skills: {len(skills)} configured\n"

            exec_env = agent.get('execution_environment', {})
            if exec_env:
                if exec_env.get('secrets'):
                    human_readable += f"  Secrets: {', '.join(exec_env['secrets'].keys())}\n"
                if exec_env.get('env_vars'):
                    human_readable += f"  Env Vars: {', '.join(exec_env['env_vars'].keys())}\n"

            # Return structured JSON
            result = {
                "type": "tool_result",
                "tool": "get_agent_details",
                "success": True,
                "data": {
                    "agent": agent
                },
                "human_readable": human_readable
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error("get_agent_details_tool_error", error=str(e), exc_info=True)
            return json.dumps({
                "type": "tool_result",
                "tool": "get_agent_details",
                "success": False,
                "error": str(e)
            })

    def get_team_details(self, team_id: str) -> str:
        """Get complete details for a specific team.

        Use this after finding relevant teams to get full team composition and capabilities.

        Args:
            team_id: Team ID to fetch (required)

        Returns:
            JSON string with full team details and human-readable format
        """
        try:
            if not team_id:
                return json.dumps({
                    "type": "tool_result",
                    "tool": "get_team_details",
                    "success": False,
                    "error": "team_id is required"
                })

            # Call service method (direct DB query)
            team = self.planning_service.get_team_details(team_id=team_id)

            if not team:
                return json.dumps({
                    "type": "tool_result",
                    "tool": "get_team_details",
                    "success": False,
                    "error": f"Team {team_id} not found"
                })

            # Format human-readable output
            human_readable = f"Team Details:\n"
            human_readable += f"  ID: {team.get('id')}\n"
            human_readable += f"  Name: {team.get('name')}\n"
            human_readable += f"  Status: {team.get('status')}\n"
            human_readable += f"  Description: {team.get('description', 'N/A')}\n"
            human_readable += f"  Agent Count: {team.get('agent_count', 0)}\n"

            agents = team.get('agents', [])
            if agents:
                human_readable += f"\n  Team Members:\n"
                for agent in agents[:10]:  # Show first 10
                    human_readable += f"    - {agent.get('name')} ({agent.get('model_id', 'default')})\n"

            # Return structured JSON
            result = {
                "type": "tool_result",
                "tool": "get_team_details",
                "success": True,
                "data": {
                    "team": team
                },
                "human_readable": human_readable
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error("get_team_details_tool_error", error=str(e), exc_info=True)
            return json.dumps({
                "type": "tool_result",
                "tool": "get_team_details",
                "success": False,
                "error": str(e)
            })

    def search_context_graph(
        self,
        query: str,
        label: Optional[str] = None,
        limit: int = 20
    ) -> str:
        """Search the context graph for relevant resources.

        Use this to discover services, repositories, or other resources that might be relevant.

        Args:
            query: Search query text (required)
            label: Optional label to filter by (e.g., 'Service', 'Repository')
            limit: Maximum results to return (default: 20)

        Returns:
            JSON string with search results and human-readable format
        """
        try:
            if not query:
                return json.dumps({
                    "type": "tool_result",
                    "tool": "search_context_graph",
                    "success": False,
                    "error": "query is required"
                })

            # This method is async, need to wrap it
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run async method synchronously
            results = loop.run_until_complete(
                self.planning_service.search_context_graph(
                    query=query,
                    label=label,
                    limit=limit
                )
            )

            nodes = results.get('nodes', []) if isinstance(results, dict) else []

            # Format human-readable output
            if not nodes:
                human_readable = f"No resources found matching '{query}'."
            else:
                human_readable = f"Found {len(nodes)} resources matching '{query}':\n\n"
                for i, node in enumerate(nodes, 1):
                    labels = node.get('labels', [])
                    props = node.get('properties', {})

                    human_readable += f"Resource {i}:\n"
                    human_readable += f"  ID: {node.get('id')}\n"
                    human_readable += f"  Type: {', '.join(labels) if labels else 'Unknown'}\n"

                    # Show key properties
                    if props:
                        human_readable += f"  Properties:\n"
                        for key, value in list(props.items())[:5]:  # Show first 5 props
                            human_readable += f"    {key}: {value}\n"
                    human_readable += "\n"

            # Return structured JSON
            result = {
                "type": "tool_result",
                "tool": "search_context_graph",
                "success": True,
                "data": {
                    "nodes": nodes,
                    "count": len(nodes),
                    "query": {
                        "text": query,
                        "label": label
                    }
                },
                "human_readable": human_readable
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error("search_context_graph_tool_error", error=str(e), exc_info=True)
            return json.dumps({
                "type": "tool_result",
                "tool": "search_context_graph",
                "success": False,
                "error": str(e)
            })

    @cache_tool_result(ttl=60)  # Cache for 60 seconds
    def list_environments(self, status: str = "active", limit: int = 20) -> str:
        """List available execution environments in the organization.

        Use this to discover where agents and teams can be executed.
        Environments provide execution context like secrets, env vars, and worker queues.

        Args:
            status: Filter by status (default: "active")
            limit: Maximum number of environments to return (default: 20)

        Returns:
            JSON string with structured environment data and human-readable format
        """
        try:
            # Call service method (direct DB query)
            environments = self.planning_service.list_environments(
                status=status,
                limit=limit
            )

            # Format human-readable output
            if not environments:
                human_readable = "No active environments found in the organization."
            else:
                human_readable = f"Found {len(environments)} active environments:\n\n"
                for i, env in enumerate(environments, 1):
                    human_readable += f"Environment {i}:\n"
                    human_readable += f"  ID: {env.get('id')}\n"
                    human_readable += f"  Name: {env.get('name')}\n"
                    human_readable += f"  Display Name: {env.get('display_name')}\n"
                    human_readable += f"  Status: {env.get('status')}\n"
                    if env.get('description'):
                        human_readable += f"  Description: {env.get('description')}\n"
                    tags = env.get('tags', [])
                    if tags:
                        human_readable += f"  Tags: {', '.join(tags)}\n"
                    human_readable += "\n"

            # Return structured JSON
            result = {
                "type": "tool_result",
                "tool": "list_environments",
                "success": True,
                "data": {
                    "environments": environments,
                    "count": len(environments)
                },
                "human_readable": human_readable
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error("list_environments_tool_error", error=str(e), exc_info=True)
            return json.dumps({
                "type": "tool_result",
                "tool": "list_environments",
                "success": False,
                "error": str(e)
            })

    @cache_tool_result(ttl=60)  # Cache for 60 seconds
    def list_worker_queues(
        self,
        environment_id: str = None,
        status: str = "active",
        limit: int = 20
    ) -> str:
        """List available worker queues where tasks can be executed.

        Worker queues are execution targets within environments. Each queue can have
        multiple active workers ready to process tasks. Use this to find the best
        queue for executing a task.

        Args:
            environment_id: Optional - filter by environment ID (default: None, returns all)
            status: Filter by status (default: "active")
            limit: Maximum number of queues to return (default: 20)

        Returns:
            JSON string with structured worker queue data including active worker counts
        """
        try:
            # Call service method (direct DB query)
            worker_queues = self.planning_service.list_worker_queues(
                environment_id=environment_id,
                status=status,
                limit=limit
            )

            # Format human-readable output
            if not worker_queues:
                human_readable = "No active worker queues found"
                if environment_id:
                    human_readable += f" in environment {environment_id}"
                human_readable += "."
            else:
                human_readable = f"Found {len(worker_queues)} active worker queues:\n\n"
                for i, queue in enumerate(worker_queues, 1):
                    human_readable += f"Queue {i}:\n"
                    human_readable += f"  ID: {queue.get('id')}\n"
                    human_readable += f"  Name: {queue.get('name')}\n"
                    human_readable += f"  Display Name: {queue.get('display_name')}\n"
                    human_readable += f"  Environment ID: {queue.get('environment_id')}\n"
                    human_readable += f"  Status: {queue.get('status')}\n"
                    human_readable += f"  Active Workers: {queue.get('active_workers', 0)}\n"
                    if queue.get('description'):
                        human_readable += f"  Description: {queue.get('description')}\n"
                    human_readable += "\n"

            # Return structured JSON
            result = {
                "type": "tool_result",
                "tool": "list_worker_queues",
                "success": True,
                "data": {
                    "worker_queues": worker_queues,
                    "count": len(worker_queues)
                },
                "human_readable": human_readable
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error("list_worker_queues_tool_error", error=str(e), exc_info=True)
            return json.dumps({
                "type": "tool_result",
                "tool": "list_worker_queues",
                "success": False,
                "error": str(e)
            })

    @cache_tool_result(ttl=300)  # Cache for 5 minutes (fallback rarely changes)
    def get_fallback_agent(self) -> str:
        """Get a general-purpose fallback agent when no specific match is found.

        **Use this tool when**:
        - search_agents_by_capability returns empty results
        - No agents match the task requirements
        - You need to select SOMETHING (never return None)

        This returns the most recently used general-purpose agent, ensuring
        Step 1 ALWAYS has an agent to select.

        Returns:
            JSON string with fallback agent details
        """
        try:
            # Try to get a versatile, recently-used agent
            agents = self.planning_service.list_agents(limit=50)

            if not agents:
                # Absolutely no agents - return error
                return json.dumps({
                    "type": "tool_result",
                    "tool": "get_fallback_agent",
                    "success": False,
                    "error": "No agents available in organization. Cannot select fallback."
                })

            # Find best fallback: prefer general-purpose, recently used
            fallback_agent = None

            # Priority 1: Agent with "general" in name or description
            for agent in agents:
                name_lower = agent.get("name", "").lower()
                desc_lower = agent.get("description", "").lower()
                if "general" in name_lower or "general" in desc_lower:
                    fallback_agent = agent
                    break

            # Priority 2: First agent in list (most recently used/created)
            if not fallback_agent:
                fallback_agent = agents[0]

            # Format human-readable output
            human_readable = f"Fallback Agent (no perfect match found):\n\n"
            human_readable += f"ID: {fallback_agent.get('id')}\n"
            human_readable += f"Name: {fallback_agent.get('name')}\n"
            human_readable += f"Model: {fallback_agent.get('model_id', 'default')}\n"
            human_readable += f"Description: {fallback_agent.get('description', 'General purpose agent')}\n"

            capabilities = fallback_agent.get('capabilities', [])
            if capabilities:
                human_readable += f"Capabilities: {', '.join(capabilities)}\n"

            human_readable += "\n⚠️  This is a fallback selection. "
            human_readable += "Consider explaining in your reasoning why no perfect match was found."

            # Return structured JSON
            result = {
                "type": "tool_result",
                "tool": "get_fallback_agent",
                "success": True,
                "data": {
                    "agent": fallback_agent,
                    "is_fallback": True,
                    "note": "No perfect match - this is the best available general-purpose agent"
                },
                "human_readable": human_readable
            }
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error("get_fallback_agent_tool_error", error=str(e), exc_info=True)
            return json.dumps({
                "type": "tool_result",
                "tool": "get_fallback_agent",
                "success": False,
                "error": str(e)
            })
