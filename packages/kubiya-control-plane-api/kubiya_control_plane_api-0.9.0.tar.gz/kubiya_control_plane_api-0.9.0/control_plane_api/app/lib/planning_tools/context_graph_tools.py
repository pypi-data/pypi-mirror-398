"""
Context Graph Planning Tools

Provides intelligent resource discovery via context graph queries.
Replaces the anti-pattern of dumping all agents/teams into prompt.

This tool enables the planning agent to:
1. Discover agents by capability/skill
2. Search teams with specific capabilities
3. Get full agent details on-demand
4. Query context graph for relevant resources
5. List available capabilities

Following the same pattern used by workers and skills for tool-based discovery.
"""

import structlog
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from control_plane_api.app.lib.planning_tools.base import BasePlanningTools
from control_plane_api.app.services.context_graph_client import ContextGraphClient
from control_plane_api.app.models.agent import Agent

logger = structlog.get_logger(__name__)


class ContextGraphPlanningTools(BasePlanningTools):
    """
    Context graph tools for intelligent resource discovery during planning.

    Usage pattern:
    1. AI analyzes task description
    2. AI identifies required capabilities (e.g., "kubernetes", "aws")
    3. AI calls search_agents_with_capability("kubernetes")
    4. AI gets relevant agent summaries
    5. AI optionally calls get_agent_full_details(agent_id) for specific agents
    """

    def __init__(
        self,
        db=None,
        organization_id: Optional[str] = None,
        api_token: Optional[str] = None,
        graph_api_base: Optional[str] = None,
    ):
        """
        Initialize context graph planning tools

        Args:
            db: Database session for direct data access
            organization_id: Organization context for filtering
            api_token: API token for context graph authentication
            graph_api_base: Context graph API base URL (default: https://graph.kubiya.ai)
        """
        super().__init__(db=db, organization_id=organization_id)
        self.name = "context_graph_planning_tools"
        self.api_token = api_token
        self.graph_client = ContextGraphClient(
            api_base=graph_api_base or "https://graph.kubiya.ai",
            api_token=api_token,
            organization_id=organization_id
        )

    async def search_agents_with_capability(
        self,
        capability: str,
        limit: int = 10
    ) -> str:
        """
        Search for agents that have a specific capability (skill).

        Args:
            capability: Skill name (e.g., "kubectl", "aws_cli", "python")
            limit: Maximum agents to return (default: 10)

        Returns:
            JSON string with matching agents:
            [
                {
                    "id": "agent-123",
                    "name": "DevOps Agent",
                    "description": "Handles K8s deployments",
                    "model_id": "claude-sonnet-4",
                    "skills": ["kubectl", "helm", "aws_cli"],
                    "has_secrets": ["KUBECONFIG", "AWS_ACCESS_KEY_ID"],
                    "has_env_vars": ["AWS_REGION"],
                    "status": "active"
                },
                ...
            ]

        Example:
            AI: "I need to deploy to Kubernetes"
            AI calls: search_agents_with_capability("kubectl")
            Returns: Agents with kubectl skill
        """
        try:
            logger.info(
                "searching_agents_by_capability",
                capability=capability,
                limit=limit,
                organization_id=self.organization_id
            )

            # Query context graph for agents with this skill
            query = """
            MATCH (a:Agent)-[:HAS_SKILL]->(s:Skill {name: $capability})
            WHERE a.organization_id = $org_id
            AND a.status = 'active'
            OPTIONAL MATCH (a)-[:HAS_SKILL]->(other_skill:Skill)
            OPTIONAL MATCH (a)-[:HAS_SECRET]->(secret:Secret)
            OPTIONAL MATCH (a)-[:HAS_ENV_VAR]->(env:EnvVar)
            RETURN
                a.id as agent_id,
                a.name as agent_name,
                a.description as description,
                a.model_id as model_id,
                a.status as status,
                collect(DISTINCT other_skill.name) as skills,
                collect(DISTINCT secret.name) as secrets,
                collect(DISTINCT env.name) as env_vars
            LIMIT $limit
            """

            result = await self.graph_client.execute_query(
                query=query,
                parameters={
                    "capability": capability,
                    "org_id": self.organization_id,
                    "limit": limit
                }
            )

            agents = []
            for record in result.get("data", []):
                agents.append({
                    "id": record["agent_id"],
                    "name": record["agent_name"],
                    "description": record["description"] or "",
                    "model_id": record["model_id"],
                    "skills": [s for s in record["skills"] if s],
                    "has_secrets": [s for s in record["secrets"] if s],
                    "has_env_vars": [e for e in record["env_vars"] if e],
                    "status": record["status"]
                })

            logger.info(
                "agents_found_by_capability",
                capability=capability,
                count=len(agents)
            )

            return self._format_list_response(
                agents,
                f"Agents with '{capability}' capability",
                ["name", "skills", "model_id", "description"]
            )

        except Exception as e:
            logger.error(
                "search_agents_error",
                capability=capability,
                error=str(e)
            )
            return f"Error searching agents: {str(e)}"

    async def search_teams_with_capability(
        self,
        capability: str,
        limit: int = 5
    ) -> str:
        """
        Search for teams that have agents with a specific capability.

        Args:
            capability: Skill name needed
            limit: Maximum teams to return

        Returns:
            JSON string with matching teams and their agent summaries

        Example:
            AI: "I need a team for multi-step deployment"
            AI calls: search_teams_with_capability("kubernetes")
            Returns: Teams with kubernetes-capable agents
        """
        try:
            logger.info(
                "searching_teams_by_capability",
                capability=capability,
                limit=limit,
                organization_id=self.organization_id
            )

            query = """
            MATCH (t:Team)-[:HAS_MEMBER]->(a:Agent)-[:HAS_SKILL]->(s:Skill {name: $capability})
            WHERE t.organization_id = $org_id
            AND t.status = 'active'
            WITH t, collect(DISTINCT a.name) as agent_names, count(DISTINCT a) as agent_count
            RETURN
                t.id as team_id,
                t.name as team_name,
                t.description as description,
                agent_names,
                agent_count
            LIMIT $limit
            """

            result = await self.graph_client.execute_query(
                query=query,
                parameters={
                    "capability": capability,
                    "org_id": self.organization_id,
                    "limit": limit
                }
            )

            teams = []
            for record in result.get("data", []):
                teams.append({
                    "id": record["team_id"],
                    "name": record["team_name"],
                    "description": record["description"] or "",
                    "agent_count": record["agent_count"],
                    "agents": record["agent_names"][:5]  # Show first 5
                })

            logger.info(
                "teams_found_by_capability",
                capability=capability,
                count=len(teams)
            )

            return self._format_list_response(
                teams,
                f"Teams with '{capability}' capability",
                ["name", "agent_count", "agents", "description"]
            )

        except Exception as e:
            logger.error("search_teams_error", capability=capability, error=str(e))
            return f"Error searching teams: {str(e)}"

    async def get_agent_full_details(
        self,
        agent_id: str
    ) -> str:
        """
        Get complete details for a specific agent.

        Use this AFTER finding relevant agents to get full execution environment details.

        Args:
            agent_id: Agent ID to fetch

        Returns:
            JSON string with full agent details including:
            - All skills with configurations
            - All secrets (names only)
            - All environment variables
            - Execution environment settings
            - Projects and environments

        Example:
            AI: "I found agent-123 with kubectl, let me get full details"
            AI calls: get_agent_full_details("agent-123")
            Returns: Complete agent config including secrets, env vars, etc.
        """
        try:
            logger.info(
                "getting_agent_full_details",
                agent_id=agent_id,
                organization_id=self.organization_id
            )

            # Fetch from database with full relationships
            db = self._get_db()
            agent = db.execute(
                select(Agent)
                .options(
                    selectinload(Agent.team),
                    selectinload(Agent.project),
                    selectinload(Agent.environment)
                )
                .where(
                    Agent.id == agent_id,
                    Agent.organization_id == self.organization_id
                )
            ).scalar_one_or_none()

            if not agent:
                return f"Agent {agent_id} not found"

            # Build complete details
            details = {
                "id": str(agent.id),
                "name": agent.name,
                "description": agent.description,
                "model_id": agent.model_id,
                "status": agent.status,
                "capabilities": agent.capabilities or [],
                "runtime": agent.runtime,
                "execution_environment": {
                    "secrets": {},
                    "env_vars": {},
                    "integration_ids": []
                }
            }

            # Add execution environment
            if agent.execution_environment:
                exec_env = agent.execution_environment

                # Show secret names only, not values (security)
                if isinstance(exec_env, dict):
                    if exec_env.get("secrets"):
                        details["execution_environment"]["secrets"] = {
                            k: "***" for k in exec_env["secrets"].keys()
                        }
                    if exec_env.get("env_vars"):
                        details["execution_environment"]["env_vars"] = exec_env["env_vars"]
                    if exec_env.get("integration_ids"):
                        details["execution_environment"]["integration_ids"] = exec_env["integration_ids"]

            # Add team info
            if agent.team:
                details["team"] = {
                    "id": str(agent.team.id),
                    "name": agent.team.name
                }

            # Add project info
            if agent.project:
                details["project"] = {
                    "id": str(agent.project.id),
                    "name": agent.project.name
                }

            # Add environment info
            if agent.environment:
                details["environment"] = {
                    "id": str(agent.environment.id),
                    "name": agent.environment.name
                }

            logger.info(
                "agent_full_details_fetched",
                agent_id=agent_id,
                agent_name=agent.name
            )

            return self._format_detail_response(details, f"Agent: {agent.name}")

        except Exception as e:
            logger.error("get_agent_details_error", agent_id=agent_id, error=str(e))
            return f"Error fetching agent details: {str(e)}"

    async def search_context_graph(
        self,
        label: Optional[str] = None,
        property_name: Optional[str] = None,
        property_value: Optional[str] = None,
        text_search: Optional[str] = None,
        limit: int = 20
    ) -> str:
        """
        Generic context graph search for discovering relevant resources.

        Args:
            label: Node label (e.g., "Service", "Repository", "User")
            property_name: Property to filter on
            property_value: Value to match
            text_search: Free-text search across properties
            limit: Maximum results

        Returns:
            JSON string with matching nodes

        Examples:
            - Find services: search_context_graph(label="Service")
            - Find prod services: search_context_graph(label="Service", property_name="environment", property_value="production")
            - Text search: search_context_graph(text_search="kubernetes deployment")
        """
        try:
            logger.info(
                "searching_context_graph",
                label=label,
                property_name=property_name,
                text_search=text_search,
                organization_id=self.organization_id
            )

            if text_search:
                result = await self.graph_client.search_by_text(
                    search_text=text_search,
                    label=label,
                    limit=limit
                )
            else:
                result = await self.graph_client.search_nodes(
                    label=label,
                    property_name=property_name,
                    property_value=property_value,
                    limit=limit
                )

            nodes = result.get("nodes", [])

            logger.info(
                "context_graph_search_complete",
                label=label,
                count=len(nodes)
            )

            return self._format_list_response(
                nodes,
                f"Context graph search results",
                ["label", "properties"]
            )

        except Exception as e:
            logger.error("context_graph_search_error", error=str(e))
            return f"Error searching context graph: {str(e)}"

    async def get_available_capabilities(self) -> str:
        """
        List all available capabilities (skills) in the organization.

        Returns:
            JSON string with skill names and usage counts

        Example:
            AI: "What capabilities are available?"
            AI calls: get_available_capabilities()
            Returns: ["kubectl", "aws_cli", "python", "terraform", ...]
            AI can then search for agents with specific capabilities
        """
        try:
            logger.info(
                "getting_available_capabilities",
                organization_id=self.organization_id
            )

            query = """
            MATCH (s:Skill)<-[:HAS_SKILL]-(a:Agent)
            WHERE a.organization_id = $org_id
            AND a.status = 'active'
            RETURN s.name as skill_name, count(a) as agent_count
            ORDER BY agent_count DESC
            LIMIT 50
            """

            result = await self.graph_client.execute_query(
                query=query,
                parameters={"org_id": self.organization_id}
            )

            capabilities = [
                {
                    "skill": record["skill_name"],
                    "agent_count": record["agent_count"]
                }
                for record in result.get("data", [])
            ]

            logger.info(
                "capabilities_fetched",
                count=len(capabilities)
            )

            return self._format_list_response(
                capabilities,
                "Available capabilities",
                ["skill", "agent_count"]
            )

        except Exception as e:
            logger.error("get_capabilities_error", error=str(e))
            return f"Error fetching capabilities: {str(e)}"

    async def discover_agents_by_task(
        self,
        task_description: str,
        limit: int = 5
    ) -> str:
        """
        Intelligent agent discovery based on task description.

        Uses text search across agent names, descriptions, and capabilities
        to find relevant agents for a given task.

        Args:
            task_description: Description of the task (e.g., "deploy to kubernetes")
            limit: Maximum agents to return

        Returns:
            JSON string with matching agents

        Example:
            AI: "Task: Deploy app to production Kubernetes cluster"
            AI calls: discover_agents_by_task("deploy to kubernetes")
            Returns: Agents with kubernetes-related skills and descriptions
        """
        try:
            logger.info(
                "discovering_agents_by_task",
                task_description=task_description[:100],
                organization_id=self.organization_id
            )

            # Search context graph using text search
            result = await self.graph_client.search_by_text(
                search_text=task_description,
                label="Agent",
                limit=limit
            )

            agents = []
            for node in result.get("nodes", []):
                props = node.get("properties", {})
                if props.get("status") == "active":
                    agents.append({
                        "id": props.get("id"),
                        "name": props.get("name"),
                        "description": props.get("description", ""),
                        "model_id": props.get("model_id"),
                        "status": props.get("status")
                    })

            logger.info(
                "agents_discovered_by_task",
                count=len(agents)
            )

            return self._format_list_response(
                agents,
                f"Agents matching task: {task_description[:50]}...",
                ["name", "description", "model_id"]
            )

        except Exception as e:
            logger.error("discover_agents_by_task_error", error=str(e))
            return f"Error discovering agents: {str(e)}"
