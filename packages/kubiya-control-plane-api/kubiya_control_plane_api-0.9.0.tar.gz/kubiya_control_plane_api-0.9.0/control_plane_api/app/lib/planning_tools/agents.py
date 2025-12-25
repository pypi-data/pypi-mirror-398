"""
Agent Context Tools - Fetch agent information for task planning
"""

from typing import Optional, List
import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from control_plane_api.app.lib.planning_tools.base import BasePlanningTools
from control_plane_api.app.lib.planning_tools.models import AgentModel
from control_plane_api.app.models.agent import Agent
from control_plane_api.app.models.associations import AgentEnvironment

logger = structlog.get_logger()
class AgentsContextTools(BasePlanningTools):
    """
    Tools for fetching agent context and capabilities

    Provides methods to:
    - List all available agents
    - Get detailed agent information
    - Query agent capabilities
    - Check agent availability
    """

    def __init__(self, db = None, organization_id: Optional[str] = None):
        super().__init__(db=db, organization_id=organization_id)
        self.name = "agent_context_tools"

    async def list_agents(self, limit: int = 50, status_filter: Optional[str] = None) -> List[dict]:
        """
        List all available agents with their full information

        Args:
            limit: Maximum number of agents to return
            status_filter: Optional status filter (e.g., 'active', 'inactive')

        Returns:
            List of agent dictionaries with complete data including:
            - Agent name, ID, model_id, description, status
            - Skills (with full configuration)
            - Execution environment (secrets, env_vars, integration_ids)
            - Projects and environments
            - Capabilities and runtime info
        """
        try:
            # CRITICAL SECURITY: organization_id MUST be set to prevent cross-org data leakage
            if not self.organization_id:
                logger.error("list_agents_called_without_organization_id",
                           message="SECURITY: Refusing to list agents without organization_id filter")
                return []

            # DEBUG: Log the ACTUAL organization_id value being used in the query
            logger.info(
                "list_agents_DEBUG_org_id",
                org_id_value=self.organization_id,
                org_id_length=len(self.organization_id),
                org_id_repr=repr(self.organization_id)
            )

            db = self._get_db()

            # Query agents using SQLAlchemy - ALWAYS filter by organization
            query = select(Agent).options(
                selectinload(Agent.team),
                selectinload(Agent.project),
                selectinload(Agent.environment),
                selectinload(Agent.environment_associations)
            ).where(Agent.organization_id == self.organization_id)  # SECURITY: Always filter

            if status_filter:
                query = query.where(Agent.status == status_filter)

            query = query.order_by(Agent.created_at.desc()).limit(limit)

            result = db.execute(query)
            agents = result.scalars().all()

            if not agents:
                return []

            # Convert SQLAlchemy objects to dictionaries
            agent_list = []
            for agent in agents:
                agent_dict = {
                    "id": str(agent.id),
                    "organization_id": agent.organization_id,
                    "name": agent.name,
                    "description": agent.description,
                    # status field excluded - not relevant for agent selection
                    "capabilities": agent.capabilities or [],
                    "configuration": agent.configuration or {},
                    "model_id": agent.model_id,
                    "model_config": agent.model_config or {},
                    "team_id": str(agent.team_id) if agent.team_id else None,
                    "runtime": agent.runtime,
                    "execution_environment": agent.execution_environment or {},
                    "runner_name": agent.runner_name,
                    "visibility": agent.visibility,
                    "created_at": agent.created_at.isoformat() if agent.created_at else None,
                    "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
                }

                # Add project if available
                if agent.project:
                    agent_dict["project"] = {
                        "id": str(agent.project.id),
                        "name": agent.project.name,
                    }

                # Add environment if available
                if agent.environment:
                    agent_dict["environment"] = {
                        "id": str(agent.environment.id),
                        "name": agent.environment.name,
                    }

                # Note: Skills will need to be fetched via SQL if needed
                # For now, returning basic agent data is sufficient for planning
                agent_dict["skills"] = []

                agent_list.append(agent_dict)

            logger.info(
                "list_agents_sqlalchemy",
                count=len(agent_list),
                org_id=self.organization_id,
            )

            return agent_list

        except Exception as e:
            logger.error("error_listing_agents", error=str(e))
            return []

    async def get_agent_details(self, agent_id: str) -> str:
        """
        Get detailed information about a specific agent

        Args:
            agent_id: ID of the agent to fetch

        Returns:
            Detailed agent information including:
            - Full configuration
            - Available tools/capabilities
            - Model details
            - Resource requirements
        """
        try:
            client = get_supabase()

            # Query agent from Supabase
            query = client.table("agents").select("*").eq("id", agent_id)

            if self.organization_id:
                query = query.eq("organization_id", self.organization_id)

            result = query.single().execute()

            if not result.data:
                return f"Agent {agent_id} not found"

            agent = result.data

            # Fetch projects
            projects = []
            try:
                projects_result = (
                    client.table("project_agents")
                    .select("agent_id, projects(id, name, key, description)")
                    .eq("agent_id", agent_id)
                    .execute()
                )
                for item in projects_result.data or []:
                    project_data = item.get("projects")
                    if project_data:
                        projects.append({
                            "id": project_data["id"],
                            "name": project_data["name"],
                            "key": project_data["key"],
                            "description": project_data.get("description"),
                        })
            except Exception as e:
                logger.warning("failed_to_fetch_agent_projects", agent_id=agent_id, error=str(e))

            # Fetch environments
            environments_list = []
            try:
                environments_result = (
                    client.table("agent_environments")
                    .select("agent_id, environments(id, name, display_name, status)")
                    .eq("agent_id", agent_id)
                    .execute()
                )
                for item in environments_result.data or []:
                    env_data = item.get("environments")
                    if env_data:
                        environments_list.append({
                            "id": env_data["id"],
                            "name": env_data["name"],
                            "display_name": env_data.get("display_name"),
                            "status": env_data.get("status"),
                        })
            except Exception as e:
                logger.warning("failed_to_fetch_agent_environments", agent_id=agent_id, error=str(e))

            # Fetch skills with team inheritance
            skills = []
            team_id = agent.get("team_id")

            # Fetch team skills first (if agent is part of a team)
            seen_ids = set()
            if team_id and self.organization_id:
                try:
                    team_skills_result = (
                        client.table("skill_associations")
                        .select("entity_id, skill_id, configuration_override, skills(*)")
                        .eq("organization_id", self.organization_id)
                        .eq("entity_type", "team")
                        .eq("entity_id", team_id)
                        .execute()
                    )
                    for item in team_skills_result.data or []:
                        skill_data = item.get("skills")
                        if skill_data and skill_data.get("enabled", True):
                            config = skill_data.get("configuration", {})
                            override = item.get("configuration_override")
                            if override:
                                config = {**config, **override}
                            skill_obj = {
                                "id": skill_data["id"],
                                "name": skill_data["name"],
                                "type": skill_data["skill_type"],
                                "description": skill_data.get("description"),
                                "enabled": skill_data.get("enabled", True),
                                "configuration": config,
                            }
                            skills.append(skill_obj)
                            seen_ids.add(skill_data["id"])
                except Exception as e:
                    logger.warning("failed_to_fetch_team_skills_for_agent", agent_id=agent_id, team_id=team_id, error=str(e))

            # Fetch agent-specific skills (these override team skills)
            if self.organization_id:
                try:
                    agent_skills_result = (
                        client.table("skill_associations")
                        .select("entity_id, skill_id, configuration_override, skills(*)")
                        .eq("organization_id", self.organization_id)
                        .eq("entity_type", "agent")
                        .eq("entity_id", agent_id)
                        .execute()
                    )
                    for item in agent_skills_result.data or []:
                        skill_data = item.get("skills")
                        if skill_data and skill_data.get("enabled", True):
                            if skill_data["id"] not in seen_ids:
                                config = skill_data.get("configuration", {})
                                override = item.get("configuration_override")
                                if override:
                                    config = {**config, **override}
                                skills.append({
                                    "id": skill_data["id"],
                                    "name": skill_data["name"],
                                    "type": skill_data["skill_type"],
                                    "description": skill_data.get("description"),
                                    "enabled": skill_data.get("enabled", True),
                                    "configuration": config,
                                })
                except Exception as e:
                    logger.warning("failed_to_fetch_agent_skills", agent_id=agent_id, error=str(e))

            # Extract configuration
            configuration = agent.get("configuration") or {}

            agent_model = AgentModel(
                id=agent["id"],
                name=agent["name"],
                model_id=agent.get("model_id") or "default",
                description=agent.get("description"),
                status=agent["status"],
                capabilities=agent.get("capabilities") or [],
                configuration=configuration,
                llm_config=agent.get("model_config") or {},
                runtime=agent.get("runtime"),
                team_id=team_id,
                skills=skills,
                skill_ids=[s["id"] for s in skills],
                projects=projects,
                environments=environments_list,
                execution_environment=agent.get("execution_environment"),
                created_at=agent.get("created_at"),
                updated_at=agent.get("updated_at"),
                last_active_at=agent.get("last_active_at"),
                error_message=agent.get("error_message"),
            )

            agent_dict = agent_model.model_dump()

            return self._format_detail_response(
                item=agent_dict,
                title=f"Agent Details: {agent['name']}",
            )

        except Exception as e:
            return f"Error fetching agent {agent_id}: {str(e)}"

    async def search_agents_by_capability(self, capability: str) -> str:
        """
        Search for agents that have a specific capability

        Args:
            capability: Capability to search for (e.g., "kubernetes", "aws", "python")

        Returns:
            List of agents matching the capability
        """
        try:
            client = get_supabase()

            # Query agents from Supabase
            query = client.table("agents").select("*")

            if self.organization_id:
                query = query.eq("organization_id", self.organization_id)

            result = query.execute()

            if not result.data:
                return self._format_list_response(
                    items=[],
                    title=f"Agents with '{capability}' capability",
                    key_fields=["model_id", "description"],
                )

            # Filter by capability (search in description and name)
            matching_agent_models = []
            for agent in result.data:
                agent_text = f"{agent['name']} {agent.get('description') or ''}".lower()
                if capability.lower() in agent_text:
                    matching_agent_models.append(
                        AgentModel(
                            id=agent["id"],
                            name=agent["name"],
                            model_id=agent.get("model_id") or "default",
                            description=agent.get("description"),
                            status=agent["status"],
                            capabilities=agent.get("capabilities") or [],
                        )
                    )

            # Convert to dict for formatting
            matching_dicts = [model.model_dump() for model in matching_agent_models]

            return self._format_list_response(
                items=matching_dicts,
                title=f"Agents with '{capability}' capability",
                key_fields=["model_id", "description"],
            )

        except Exception as e:
            return f"Error searching agents: {str(e)}"

    async def get_agent_execution_history(self, agent_id: str, limit: int = 10) -> str:
        """
        Get recent execution history for an agent

        Args:
            agent_id: ID of the agent
            limit: Number of recent executions to fetch

        Returns:
            Recent execution history with success rates
        """
        try:
            # Use Supabase for execution history
            client = get_supabase()

            query = client.table("executions").select("*").eq("entity_id", agent_id)
            if self.organization_id:
                query = query.eq("organization_id", self.organization_id)

            result = query.order("created_at", desc=True).limit(limit).execute()
            executions = result.data or []

            if not executions:
                return f"No execution history found for agent {agent_id}"

            # Calculate success rate
            completed = sum(1 for e in executions if e.get("status") == "completed")
            total = len(executions)
            success_rate = (completed / total * 100) if total > 0 else 0

            output = [
                f"Execution History for Agent (Last {total} runs):",
                f"Success Rate: {success_rate:.1f}% ({completed}/{total})",
                "\nRecent Executions:",
            ]

            for idx, execution in enumerate(executions[:5], 1):
                status = execution.get("status", "unknown")
                prompt = execution.get("prompt", "No description")[:50]
                output.append(f"{idx}. Status: {status} | Task: {prompt}...")

            return "\n".join(output)

        except Exception as e:
            return f"Error fetching execution history: {str(e)}"
