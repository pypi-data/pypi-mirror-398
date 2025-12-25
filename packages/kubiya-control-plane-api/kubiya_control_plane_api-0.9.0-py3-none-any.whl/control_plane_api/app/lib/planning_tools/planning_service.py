"""
Planning Service - Internal service for task planning with direct DB access

This service provides access to agents, teams, and context graph data using:
- Direct SQLAlchemy queries for agents/teams (no HTTP overhead)
- ContextGraphClient for external context graph API (graph.kubiya.ai)

All queries are org-scoped to ensure proper authorization.
"""

import structlog
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from control_plane_api.app.models.agent import Agent
from control_plane_api.app.models.team import Team, TeamStatus
from control_plane_api.app.services.context_graph_client import ContextGraphClient

logger = structlog.get_logger(__name__)


class PlanningService:
    """
    Internal service for accessing planning resources.

    Uses direct DB queries for agents/teams (fast, no HTTP overhead)
    Uses ContextGraphClient for context graph (external service, HTTP correct)
    """

    def __init__(
        self,
        db: Session,
        organization_id: str,
        api_token: str,
        context_graph_base: str = "https://graph.kubiya.ai"
    ):
        """
        Initialize planning service.

        Args:
            db: SQLAlchemy database session
            organization_id: Organization ID for filtering
            api_token: API token for context graph auth
            context_graph_base: Context graph API base URL
        """
        self.db = db
        self.organization_id = organization_id
        self.api_token = api_token

        # Initialize context graph client for external queries
        self.context_graph_client = ContextGraphClient(
            api_base=context_graph_base,
            api_token=api_token,
            organization_id=organization_id
        )

        logger.info(
            "planning_service_initialized",
            organization_id=organization_id[:8]
        )

    def _agent_to_dict(self, agent: Agent) -> Dict[str, Any]:
        """Convert Agent model to dictionary for planning (status field excluded)."""
        return {
            "id": str(agent.id),
            "name": agent.name,
            "description": agent.description,
            "model_id": agent.model_id or "default",
            "capabilities": agent.capabilities or [],
            "runtime": agent.runtime,
            "team_id": str(agent.team_id) if agent.team_id else None,
            "execution_environment": agent.execution_environment or {},
        }

    def _team_to_dict(self, team: Team) -> Dict[str, Any]:
        """Convert Team model to dictionary."""
        # Get agent count from configuration
        config = team.configuration or {}
        member_ids = config.get("member_ids", [])

        # Get agents if they exist
        agents = []
        if member_ids:
            db_agents = self.db.query(Agent).filter(
                Agent.id.in_([UUID(mid) if isinstance(mid, str) else mid for mid in member_ids]),
                Agent.organization_id == self.organization_id
            ).all()
            agents = [
                {
                    "id": str(a.id),
                    "name": a.name,
                    "model_id": a.model_id or "default",
                    "status": a.status,
                }
                for a in db_agents
            ]

        return {
            "id": str(team.id),
            "name": team.name,
            "description": team.description,
            "status": team.status.value if hasattr(team.status, 'value') else str(team.status),
            "agent_count": len(agents),
            "agents": agents,
            "runtime": team.runtime,
            "execution_environment": team.execution_environment or {},
        }

    def list_agents(
        self,
        limit: int = 20,
        status: str = None  # Changed from "active" to None - don't filter by default
    ) -> List[Dict[str, Any]]:
        """
        List agents in the organization.

        Args:
            limit: Maximum agents to return
            status: Optional status filter (None = return all agents regardless of status)

        Returns:
            List of agent dictionaries
        """
        try:
            logger.info(
                "list_agents_called",
                organization_id=self.organization_id[:8],
                limit=limit,
                status=status or "all"
            )

            # DEBUG: Log actual query parameters
            logger.info(
                "list_agents_DEBUG_QUERY",
                full_org_id=self.organization_id,
                org_id_len=len(self.organization_id),
                status_filter=status or "no_filter",
                query_info=f"WHERE organization_id='{self.organization_id}'" + (f" AND status='{status}'" if status else " (no status filter)")
            )

            # Direct SQLAlchemy query with org filtering
            query = self.db.query(Agent).filter(
                Agent.organization_id == self.organization_id
            )

            # Only filter by status if explicitly provided
            if status:
                query = query.filter(Agent.status == status)

            agents = query.limit(limit).all()

            # DEBUG: Log what we got back
            logger.info(
                "list_agents_DEBUG_RESULTS",
                agents_found=len(agents),
                agent_names=[a.name for a in agents[:5]] if agents else []
            )

            result = [self._agent_to_dict(a) for a in agents]

            logger.info(
                "list_agents_completed",
                count=len(result),
                organization_id=self.organization_id[:8]
            )

            return result

        except Exception as e:
            logger.error("list_agents_error", error=str(e), exc_info=True)
            return []

    def search_agents_by_capability(
        self,
        capability: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for agents with a specific capability.

        Args:
            capability: Capability to search for
            limit: Maximum agents to return

        Returns:
            List of matching agent dictionaries
        """
        try:
            logger.info(
                "search_agents_by_capability_called",
                capability=capability,
                organization_id=self.organization_id[:8],
                limit=limit
            )

            # Get all agents in org (no status filter - let LLM decide based on capabilities)
            agents = self.db.query(Agent).filter(
                Agent.organization_id == self.organization_id
            ).all()

            # Filter by capability (search in capabilities, description, name)
            capability_lower = capability.lower()
            matching = [
                a for a in agents
                if capability_lower in str(a.capabilities).lower()
                or capability_lower in (a.description or "").lower()
                or capability_lower in a.name.lower()
            ]

            result = [self._agent_to_dict(a) for a in matching[:limit]]

            logger.info(
                "search_agents_by_capability_completed",
                capability=capability,
                count=len(result),
                organization_id=self.organization_id[:8]
            )

            return result

        except Exception as e:
            logger.error("search_agents_by_capability_error", error=str(e), exc_info=True)
            return []

    def list_teams(
        self,
        limit: int = 20,
        status: str = None  # Don't filter by status by default
    ) -> List[Dict[str, Any]]:
        """
        List teams in the organization.

        Args:
            limit: Maximum teams to return
            status: Optional status filter (None = return all teams regardless of status)

        Returns:
            List of team dictionaries with agent details
        """
        try:
            logger.info(
                "list_teams_called",
                organization_id=self.organization_id[:8],
                limit=limit,
                status=status or "all"
            )

            # Direct SQLAlchemy query with org filtering
            query = self.db.query(Team).filter(
                Team.organization_id == self.organization_id
            )

            # Only filter by status if explicitly provided
            if status:
                query = query.filter(Team.status == status)

            teams = query.limit(limit).all()

            result = [self._team_to_dict(t) for t in teams]

            logger.info(
                "list_teams_completed",
                count=len(result),
                organization_id=self.organization_id[:8]
            )

            return result

        except Exception as e:
            logger.error("list_teams_error", error=str(e), exc_info=True)
            return []

    def search_teams_by_capability(
        self,
        capability: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for teams with agents that have a specific capability.

        Args:
            capability: Capability to search for
            limit: Maximum teams to return

        Returns:
            List of matching team dictionaries
        """
        try:
            logger.info(
                "search_teams_by_capability_called",
                capability=capability,
                organization_id=self.organization_id[:8],
                limit=limit
            )

            # Get all teams (no status filter - let LLM decide based on capabilities)
            teams = self.db.query(Team).filter(
                Team.organization_id == self.organization_id
            ).all()

            # Filter teams that have the capability in description or members
            capability_lower = capability.lower()
            matching = []

            for team in teams:
                # Check team description
                if capability_lower in (team.description or "").lower() or capability_lower in team.name.lower():
                    matching.append(team)
                    continue

                # Check team member capabilities
                config = team.configuration or {}
                member_ids = config.get("member_ids", [])
                if member_ids:
                    agents = self.db.query(Agent).filter(
                        Agent.id.in_([UUID(mid) if isinstance(mid, str) else mid for mid in member_ids]),
                        Agent.organization_id == self.organization_id
                    ).all()

                    for agent in agents:
                        if capability_lower in str(agent.capabilities).lower():
                            matching.append(team)
                            break

            result = [self._team_to_dict(t) for t in matching[:limit]]

            logger.info(
                "search_teams_by_capability_completed",
                capability=capability,
                count=len(result),
                organization_id=self.organization_id[:8]
            )

            return result

        except Exception as e:
            logger.error("search_teams_by_capability_error", error=str(e), exc_info=True)
            return []

    def get_agent_details(
        self,
        agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get complete details for a specific agent.

        Args:
            agent_id: Agent ID

        Returns:
            Agent dictionary with full details or None
        """
        try:
            logger.info(
                "get_agent_details_called",
                agent_id=agent_id,
                organization_id=self.organization_id[:8]
            )

            # Get agent with org filtering
            agent = self.db.query(Agent).filter(
                Agent.id == UUID(agent_id) if isinstance(agent_id, str) else agent_id,
                Agent.organization_id == self.organization_id
            ).first()

            if not agent:
                logger.warning(
                    "agent_not_found",
                    agent_id=agent_id,
                    organization_id=self.organization_id[:8]
                )
                return None

            # Import router helpers
            from control_plane_api.app.routers.agents_v2 import (
                get_agent_projects,
                get_agent_environments,
                get_agent_skills_with_inheritance
            )

            # Get related data
            result = {
                **self._agent_to_dict(agent),
                "projects": get_agent_projects(self.db, str(agent.id)),
                "environments": get_agent_environments(self.db, str(agent.id)),
                "skills": get_agent_skills_with_inheritance(
                    self.db,
                    self.organization_id,
                    str(agent.id),
                    str(agent.team_id) if agent.team_id else None
                )
            }

            logger.info(
                "get_agent_details_completed",
                agent_id=agent_id,
                agent_name=agent.name
            )

            return result

        except Exception as e:
            logger.error("get_agent_details_error", error=str(e), exc_info=True)
            return None

    def get_team_details(
        self,
        team_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get complete details for a specific team.

        Args:
            team_id: Team ID

        Returns:
            Team dictionary with full details or None
        """
        try:
            logger.info(
                "get_team_details_called",
                team_id=team_id,
                organization_id=self.organization_id[:8]
            )

            # Get team with org filtering
            team = self.db.query(Team).filter(
                Team.id == UUID(team_id) if isinstance(team_id, str) else team_id,
                Team.organization_id == self.organization_id
            ).first()

            if not team:
                logger.warning(
                    "team_not_found",
                    team_id=team_id,
                    organization_id=self.organization_id[:8]
                )
                return None

            result = self._team_to_dict(team)

            logger.info(
                "get_team_details_completed",
                team_id=team_id,
                team_name=team.name
            )

            return result

        except Exception as e:
            logger.error("get_team_details_error", error=str(e), exc_info=True)
            return None

    def list_environments(
        self,
        status: str = "active",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List available environments in the organization.

        Args:
            status: Filter by status (default: "active")
            limit: Maximum number of environments to return

        Returns:
            List of environment dictionaries
        """
        try:
            from control_plane_api.app.models.environment import Environment

            logger.info(
                "list_environments_called",
                organization_id=self.organization_id[:8],
                status=status,
                limit=limit
            )

            query = self.db.query(Environment).filter(
                Environment.organization_id == self.organization_id
            )

            if status:
                query = query.filter(Environment.status == status)

            environments = query.order_by(Environment.created_at.desc()).limit(limit).all()

            result = [
                {
                    "id": str(env.id),
                    "name": env.name,
                    "display_name": env.display_name or env.name,
                    "description": env.description,
                    "status": env.status,
                    "tags": env.tags or [],
                    "created_at": env.created_at.isoformat() if env.created_at else None,
                }
                for env in environments
            ]

            logger.info(
                "list_environments_completed",
                count=len(result),
                organization_id=self.organization_id[:8]
            )

            return result

        except Exception as e:
            logger.error("list_environments_error", error=str(e), exc_info=True)
            return []

    def list_worker_queues(
        self,
        environment_id: Optional[str] = None,
        status: str = "active",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List available worker queues in the organization.

        Args:
            environment_id: Optional filter by environment
            status: Filter by status (default: "active")
            limit: Maximum number of queues to return

        Returns:
            List of worker queue dictionaries with active worker counts
        """
        try:
            from control_plane_api.app.models.worker import WorkerQueue, WorkerHeartbeat
            from sqlalchemy import func
            from datetime import datetime, timedelta

            logger.info(
                "list_worker_queues_called",
                organization_id=self.organization_id[:8],
                environment_id=environment_id,
                status=status,
                limit=limit
            )

            # Build base query with active worker count
            # Count workers that heartbeated in last 5 minutes
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)

            query = self.db.query(
                WorkerQueue,
                func.count(WorkerHeartbeat.id).label('active_workers')
            ).outerjoin(
                WorkerHeartbeat,
                (WorkerHeartbeat.worker_queue_id == WorkerQueue.id) &
                (WorkerHeartbeat.status == 'active') &
                (WorkerHeartbeat.last_heartbeat >= cutoff_time)
            ).filter(
                WorkerQueue.organization_id == self.organization_id,
                WorkerQueue.ephemeral == False  # Exclude ephemeral queues from planning
            )

            if environment_id:
                query = query.filter(WorkerQueue.environment_id == environment_id)

            if status:
                query = query.filter(WorkerQueue.status == status)

            query = query.group_by(WorkerQueue.id).order_by(WorkerQueue.created_at.desc()).limit(limit)

            results = query.all()

            worker_queues = [
                {
                    "id": str(wq.id),
                    "name": wq.name,
                    "display_name": wq.display_name or wq.name,
                    "description": wq.description,
                    "environment_id": str(wq.environment_id),
                    "status": wq.status,
                    "active_workers": active_count,
                    "created_at": wq.created_at.isoformat() if wq.created_at else None,
                }
                for wq, active_count in results
            ]

            logger.info(
                "list_worker_queues_completed",
                count=len(worker_queues),
                organization_id=self.organization_id[:8]
            )

            return worker_queues

        except Exception as e:
            logger.error("list_worker_queues_error", error=str(e), exc_info=True)
            return []

    async def search_context_graph(
        self,
        query: str,
        label: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search the context graph for resources.

        This uses ContextGraphClient which makes HTTP calls to external
        graph.kubiya.ai service - this is correct since it's external.

        Args:
            query: Search query text
            label: Optional node label filter
            limit: Maximum results

        Returns:
            Search results dictionary with nodes
        """
        try:
            logger.info(
                "search_context_graph_called",
                query=query[:100],
                label=label,
                organization_id=self.organization_id[:8],
                limit=limit
            )

            # Use ContextGraphClient (external service - HTTP is correct)
            result = await self.context_graph_client.search_by_text(
                search_text=query,
                label=label,
                limit=limit
            )

            node_count = len(result.get("nodes", [])) if isinstance(result, dict) else 0

            logger.info(
                "search_context_graph_completed",
                query=query[:100],
                node_count=node_count,
                organization_id=self.organization_id[:8]
            )

            return result if isinstance(result, dict) else {"nodes": [], "count": 0}

        except Exception as e:
            logger.error("search_context_graph_error", error=str(e), exc_info=True)
            return {"nodes": [], "count": 0}
