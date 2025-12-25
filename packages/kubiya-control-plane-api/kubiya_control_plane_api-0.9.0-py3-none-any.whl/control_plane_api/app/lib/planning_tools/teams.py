"""
Team Context Tools - Fetch team information for task planning
"""

from typing import Optional, List
from sqlalchemy.orm import Session
import structlog
from control_plane_api.app.lib.planning_tools.base import BasePlanningTools
from control_plane_api.app.lib.planning_tools.models import TeamModel, TeamMemberModel
from control_plane_api.app.models.team import Team
from control_plane_api.app.models.agent import Agent
from control_plane_api.app.lib.supabase import get_supabase

logger = structlog.get_logger()


class TeamsContextTools(BasePlanningTools):
    """
    Tools for fetching team context and composition

    Provides methods to:
    - List all available teams
    - Get detailed team information
    - Query team member capabilities
    - Check team availability
    """

    def __init__(self, db: Optional[Session] = None, organization_id: Optional[str] = None):
        super().__init__(db=db, organization_id=organization_id)
        self.name = "team_context_tools"

    async def list_teams(self, limit: int = 50, status_filter: Optional[str] = None) -> List[dict]:
        """
        List all available teams with their full information

        Args:
            limit: Maximum number of teams to return
            status_filter: Optional status filter (e.g., 'active', 'inactive')

        Returns:
            List of team dictionaries with complete data including:
            - Team name, ID, description, status
            - Full agent details for each team member
            - Agent execution environments, skills, capabilities
            - Team configuration
        """
        try:
            # CRITICAL SECURITY: organization_id MUST be set to prevent cross-org data leakage
            if not self.organization_id:
                logger.error("list_teams_called_without_organization_id",
                           message="SECURITY: Refusing to list teams without organization_id filter")
                return []

            db = self._get_db()

            # Build query - ALWAYS filter by organization
            query = db.query(Team).filter(Team.organization_id == self.organization_id)
            if status_filter:
                query = query.filter(Team.status == status_filter)

            teams = query.limit(limit).all()

            # Convert to Pydantic models
            team_models = []
            for team in teams:
                # Get agent count from configuration
                member_ids = team.configuration.get("member_ids", []) if team.configuration else []
                team_models.append(
                    TeamModel(
                        id=str(team.id),
                        name=team.name,
                        description=team.description,
                        status=team.status,
                        agent_count=len(member_ids),
                    )
                )

            # Convert to dict for formatting - but we need more data!
            # Fetch full agent details for each team to include in context
            team_dicts = []
            for team in teams:
                member_ids = team.configuration.get("member_ids", []) if team.configuration else []

                # Fetch full agent data for team members - SECURITY: Filter by organization!
                agents_data = []
                if member_ids:
                    agent_objs = db.query(Agent).filter(
                        Agent.id.in_(member_ids),
                        Agent.organization_id == self.organization_id  # SECURITY: Always filter
                    ).all()
                    for agent in agent_objs:
                        agents_data.append({
                            "id": str(agent.id),
                            "name": agent.name,
                            "model_id": getattr(agent, 'model_id', None) or "default",
                            "description": getattr(agent, 'description', None),
                            "status": getattr(agent, 'status', 'unknown'),
                            "capabilities": getattr(agent, 'capabilities', None) or [],
                            "execution_environment": getattr(agent, 'execution_environment', None),
                        })

                team_dicts.append({
                    "id": str(team.id),
                    "name": team.name,
                    "description": team.description,
                    "status": team.status,
                    "agent_count": len(member_ids),
                    "agents": agents_data,  # Include full agent data
                    "configuration": team.configuration,
                })

            # Return structured data directly instead of formatted string
            return team_dicts

        except Exception as e:
            logger.error("error_listing_teams", error=str(e))
            return []

    async def get_team_details(self, team_id: str) -> str:
        """
        Get detailed information about a specific team

        Args:
            team_id: ID of the team to fetch

        Returns:
            Detailed team information including:
            - Full team configuration
            - List of all team members with their roles
            - Team capabilities (aggregate of member capabilities)
            - Coordination strategy
        """
        try:
            db = self._get_db()

            team = db.query(Team).filter(Team.id == team_id)
            if self.organization_id:
                team = team.filter(Team.organization_id == self.organization_id)
            team = team.first()

            if not team:
                return f"Team {team_id} not found"

            # Get member IDs from configuration
            member_ids = team.configuration.get("member_ids", []) if team.configuration else []

            # Fetch agents and convert to Pydantic models
            agent_models = []
            if member_ids:
                agent_objs = db.query(Agent).filter(Agent.id.in_(member_ids)).all()
                agent_models = [
                    TeamMemberModel(
                        id=str(agent.id),
                        name=agent.name,
                        model_id=agent.model_id or "default",
                        description=agent.description,
                    )
                    for agent in agent_objs
                ]

            # Convert to dict for output formatting
            agents = [model.model_dump() for model in agent_models]

            output = [
                f"Team Details: {team.name}",
                f"  ID: {str(team.id)}",
                f"  Description: {team.description or 'No description'}",
                f"  Agent Count: {len(agents)}",
                "",
                "Team Members:",
            ]

            for idx, agent in enumerate(agents, 1):
                output.append(f"  {idx}. {agent.get('name', 'Unnamed')} (ID: {agent.get('id')})")
                if "model_id" in agent:
                    output.append(f"     Model: {agent['model_id']}")
                if "description" in agent:
                    output.append(f"     Capabilities: {agent['description'][:100]}")

            return "\n".join(output)

        except Exception as e:
            return f"Error fetching team {team_id}: {str(e)}"

    async def get_team_members(self, team_id: str) -> str:
        """
        Get list of agents in a specific team

        Args:
            team_id: ID of the team

        Returns:
            List of team members with their capabilities
        """
        try:
            db = self._get_db()

            team = db.query(Team).filter(Team.id == team_id)
            if self.organization_id:
                team = team.filter(Team.organization_id == self.organization_id)
            team = team.first()

            if not team:
                return f"Team {team_id} not found"

            # Get member IDs from configuration
            member_ids = team.configuration.get("member_ids", []) if team.configuration else []

            if not member_ids:
                return f"Team {team_id} has no members"

            # Fetch agents and convert to Pydantic models
            agent_objs = db.query(Agent).filter(Agent.id.in_(member_ids)).all()
            agent_models = [
                TeamMemberModel(
                    id=str(agent.id),
                    name=agent.name,
                    model_id=agent.model_id or "default",
                    description=agent.description,
                )
                for agent in agent_objs
            ]

            # Convert to dict for formatting
            agent_dicts = [model.model_dump() for model in agent_models]

            return self._format_list_response(
                items=agent_dicts,
                title=f"Team Members ({len(agent_dicts)} total)",
                key_fields=["model_id", "description"],
            )

        except Exception as e:
            return f"Error fetching team members: {str(e)}"

    async def search_teams_by_capability(self, capability: str) -> str:
        """
        Search for teams that have agents with a specific capability

        Args:
            capability: Capability to search for (e.g., "devops", "security", "data")

        Returns:
            List of teams with members having the capability
        """
        try:
            db = self._get_db()

            query = db.query(Team)
            if self.organization_id:
                query = query.filter(Team.organization_id == self.organization_id)

            teams = query.all()

            matching_teams = []
            for team in teams:
                # Search in team name and description
                team_text = f"{team.name} {team.description or ''}".lower()

                # Also search in team members' descriptions
                member_ids = team.configuration.get("member_ids", []) if team.configuration else []
                if member_ids:
                    agents = db.query(Agent).filter(Agent.id.in_(member_ids)).all()
                    agent_text = " ".join([agent.description or "" for agent in agents]).lower()
                else:
                    agent_text = ""

                if capability.lower() in team_text or capability.lower() in agent_text:
                    matching_teams.append(
                        TeamModel(
                            id=str(team.id),
                            name=team.name,
                            description=team.description,
                            status=team.status,
                            agent_count=len(member_ids),
                        )
                    )

            # Convert to dict for formatting
            matching_dicts = [model.model_dump() for model in matching_teams]

            return self._format_list_response(
                items=matching_dicts,
                title=f"Teams with '{capability}' capability",
                key_fields=["description", "agent_count"],
            )

        except Exception as e:
            return f"Error searching teams: {str(e)}"

    async def get_team_execution_history(self, team_id: str, limit: int = 10) -> str:
        """
        Get recent execution history for a team

        Args:
            team_id: ID of the team
            limit: Number of recent executions to fetch

        Returns:
            Recent execution history with success rates
        """
        try:
            # Use Supabase for execution history
            client = get_supabase()

            query = client.table("executions").select("*").eq("entity_id", team_id).eq("execution_type", "TEAM")
            if self.organization_id:
                query = query.eq("organization_id", self.organization_id)

            result = query.order("created_at", desc=True).limit(limit).execute()
            executions = result.data or []

            if not executions:
                return f"No execution history found for team {team_id}"

            completed = sum(1 for e in executions if e.get("status") == "completed")
            total = len(executions)
            success_rate = (completed / total * 100) if total > 0 else 0

            output = [
                f"Execution History for Team (Last {total} runs):",
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
