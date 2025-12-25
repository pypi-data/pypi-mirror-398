"""Team-related Temporal activities"""

import os
from dataclasses import dataclass
from typing import Optional, List
from temporalio import activity
import structlog

from agno.agent import Agent
from agno.team import Team
from agno.models.litellm import LiteLLM

from control_plane_api.app.database import get_session_local
from control_plane_api.app.models.team import Team as TeamDB
from control_plane_api.app.models.agent import Agent as AgentDB
from control_plane_api.app.activities.agent_activities import update_execution_status, ActivityUpdateExecutionInput

logger = structlog.get_logger()


@dataclass
class ActivityGetTeamAgentsInput:
    """Input for get_team_agents activity"""
    team_id: str
    organization_id: str


@dataclass
class ActivityExecuteTeamInput:
    """Input for execute_team_coordination activity"""
    execution_id: str
    team_id: str
    organization_id: str
    prompt: str
    system_prompt: Optional[str] = None
    agents: List[dict] = None
    team_config: dict = None

    def __post_init__(self):
        if self.agents is None:
            self.agents = []
        if self.team_config is None:
            self.team_config = {}


@activity.defn
async def get_team_agents(input: ActivityGetTeamAgentsInput) -> dict:
    """
    Get all agents in a team.

    This activity fetches agents belonging to the team from the database.

    Args:
        input: Activity input with team details

    Returns:
        Dict with agents list
    """
    print(f"\n\n=== GET_TEAM_AGENTS START ===")
    print(f"team_id: {input.team_id} (type: {type(input.team_id).__name__})")
    print(f"organization_id: {input.organization_id} (type: {type(input.organization_id).__name__})")
    print(f"================================\n")

    activity.logger.info(
        f"[DEBUG] Getting team agents START",
        extra={
            "team_id": input.team_id,
            "team_id_type": type(input.team_id).__name__,
            "organization_id": input.organization_id,
            "organization_id_type": type(input.organization_id).__name__,
        }
    )

    try:
        SessionLocal = get_session_local()
        db = SessionLocal()
        print(f"Database session created successfully")

        activity.logger.info(
            f"[DEBUG] Database session created, fetching team configuration",
            extra={
                "team_id": input.team_id,
                "organization_id": input.organization_id,
            }
        )

        try:
            # First, get the team configuration to get member_ids (source of truth)
            print(f"Fetching team configuration for team_id={input.team_id}")
            team = db.query(TeamDB).filter(
                TeamDB.id == input.team_id,
                TeamDB.organization_id == input.organization_id
            ).first()

            if not team:
                print(f"Team not found!")
                activity.logger.error(
                    f"[DEBUG] Team not found",
                    extra={
                        "team_id": input.team_id,
                        "organization_id": input.organization_id,
                    }
                )
                return {"agents": [], "count": 0}

            team_config = team.configuration or {}
            member_ids = team_config.get("member_ids", [])
            print(f"Team configuration member_ids: {member_ids}")

            activity.logger.info(
                f"[DEBUG] Team configuration loaded",
                extra={
                    "team_id": input.team_id,
                    "member_ids": member_ids,
                    "member_count": len(member_ids),
                }
            )

            # Get agents by member_ids (not by FK relationship)
            agents_data = []
            if member_ids:
                print(f"Fetching agents with IDs: {member_ids}")
                agents_objs = db.query(AgentDB).filter(
                    AgentDB.id.in_(member_ids),
                    AgentDB.organization_id == input.organization_id
                ).all()

                # Convert SQLAlchemy objects to dicts for compatibility
                agents_data = [
                    {
                        "id": str(agent.id),
                        "name": agent.name,
                        "description": agent.description,
                        "status": agent.status,
                        "capabilities": agent.capabilities,
                        "configuration": agent.configuration,
                        "model_id": agent.model_id,
                        "model_config": agent.model_config,
                        "team_id": str(agent.team_id) if agent.team_id else None,
                        "organization_id": agent.organization_id,
                        "created_at": agent.created_at.isoformat() if agent.created_at else None,
                        "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
                    }
                    for agent in agents_objs
                ]
            print(f"Query executed. Result data length: {len(agents_data)}")

            activity.logger.info(
                f"[DEBUG] Query executed, processing results",
                extra={
                    "agents_found": len(agents_data),
                    "agent_ids": [a.get("id") for a in agents_data],
                }
            )

            print(f"Agents found: {len(agents_data)}")
            if agents_data:
                for agent in agents_data:
                    print(f"  - {agent.get('name')} (ID: {agent.get('id')})")

            activity.logger.info(
                f"[DEBUG] Retrieved team agents",
                extra={
                    "team_id": input.team_id,
                    "agent_count": len(agents_data),
                    "agent_names": [a.get("name") for a in agents_data],
                    "agent_ids": [a.get("id") for a in agents_data],
                }
            )

            if not agents_data:
                print(f"\n!!! NO AGENTS FOUND - Running verification query !!!")
                activity.logger.warning(
                    f"[DEBUG] WARNING: No agents found for team - running verification query",
                    extra={
                        "team_id": input.team_id,
                        "organization_id": input.organization_id,
                    }
                )

                # Try query without org filter to debug
                agents_no_org = db.query(AgentDB).filter(
                    AgentDB.team_id == input.team_id
                ).all()
                print(f"Query without org filter returned {len(agents_no_org)} agents")
                if agents_no_org:
                    for agent in agents_no_org:
                        print(f"  - {agent.name} (team_id: {agent.team_id}, org_id: {agent.organization_id})")

                activity.logger.warning(
                    f"[DEBUG] Query without org filter returned {len(agents_no_org)} agents",
                    extra={
                        "agents_found": [{"id": str(a.id), "name": a.name, "organization_id": a.organization_id} for a in agents_no_org],
                    }
                )

            print(f"\n=== GET_TEAM_AGENTS END: Returning {len(agents_data)} agents ===\n\n")
            return {
                "agents": agents_data,
                "count": len(agents_data),
            }
        finally:
            db.close()

    except Exception as e:
        print(f"\n!!! EXCEPTION in get_team_agents: {type(e).__name__}: {str(e)} !!!\n")
        activity.logger.error(
            f"[DEBUG] EXCEPTION in get_team_agents",
            extra={
                "team_id": input.team_id,
                "organization_id": input.organization_id,
                "error": str(e),
                "error_type": type(e).__name__,
            }
        )
        raise


@activity.defn
async def execute_team_coordination(input: ActivityExecuteTeamInput) -> dict:
    """
    Execute team coordination using Agno Teams.

    This activity creates an Agno Team with member Agents and executes
    the team run, allowing Agno to handle coordination.

    Args:
        input: Activity input with team execution details

    Returns:
        Dict with aggregated response, usage, success flag
    """
    activity.logger.info(
        f"Executing team coordination with Agno Teams",
        extra={
            "execution_id": input.execution_id,
            "team_id": input.team_id,
            "agent_count": len(input.agents),
        }
    )

    try:
        # Create Agno Agent objects for each team member
        member_agents = []
        for agent_data in input.agents:
            # Get model ID (default to kubiya/claude-sonnet-4 if not specified)
            model_id = agent_data.get("model_id") or "kubiya/claude-sonnet-4"

            # Get LiteLLM configuration from environment
            litellm_api_base = os.getenv("LITELLM_API_BASE", "https://llm-proxy.kubiya.ai")
            litellm_api_key = os.getenv("LITELLM_API_KEY")

            # Create Agno Agent with explicit LiteLLM proxy configuration
            # IMPORTANT: Use openai/ prefix for custom proxy compatibility (same as agno_service)
            member_agent = Agent(
                name=agent_data["name"],
                role=agent_data.get("description", agent_data["name"]),
                model=LiteLLM(
                    id=f"openai/{model_id}",  # e.g., "openai/kubiya/claude-sonnet-4"
                    api_base=litellm_api_base,
                    api_key=litellm_api_key,
                ),
            )
            member_agents.append(member_agent)

            activity.logger.info(
                f"Created Agno Agent",
                extra={
                    "agent_name": agent_data["name"],
                    "model": model_id,
                }
            )

        # Create Agno Team with member agents and LiteLLM model for coordination
        litellm_api_base = os.getenv("LITELLM_API_BASE", "https://llm-proxy.kubiya.ai")
        litellm_api_key = os.getenv("LITELLM_API_KEY")

        # Get coordinator model from team configuration (if specified by user in UI)
        # Falls back to default if not configured
        team_model = (
            input.team_config.get("llm", {}).get("model")
            or "kubiya/claude-sonnet-4"  # Default coordinator model
        )

        # Create Team with openai/ prefix for custom proxy compatibility (same as agno_service)
        team = Team(
            members=member_agents,
            name=f"Team {input.team_id}",
            model=LiteLLM(
                id=f"openai/{team_model}",  # e.g., "openai/kubiya/claude-sonnet-4"
                api_base=litellm_api_base,
                api_key=litellm_api_key,
            ),
        )

        activity.logger.info(
            f"Created Agno Team with {len(member_agents)} members",
            extra={
                "coordinator_model": team_model,
                "member_count": len(member_agents),
            }
        )

        # Execute team run in a thread pool since team.run() is synchronous
        # This prevents blocking the async event loop in Temporal
        import asyncio
        result = await asyncio.to_thread(team.run, input.prompt)

        activity.logger.info(
            f"Agno Team execution completed",
            extra={
                "execution_id": input.execution_id,
                "has_content": bool(result.content),
            }
        )

        # Extract response content
        response_content = result.content if hasattr(result, "content") else str(result)

        # Extract usage metrics if available
        usage = {}
        if hasattr(result, "metrics") and result.metrics:
            metrics = result.metrics
            usage = {
                "input_tokens": getattr(metrics, "input_tokens", 0),
                "output_tokens": getattr(metrics, "output_tokens", 0),
                "total_tokens": getattr(metrics, "total_tokens", 0),
            }

        return {
            "success": True,
            "response": response_content,
            "usage": usage,
            "coordination_type": "agno_team",
        }

    except Exception as e:
        activity.logger.error(
            f"Team coordination failed",
            extra={
                "execution_id": input.execution_id,
                "error": str(e),
            }
        )
        return {
            "success": False,
            "error": str(e),
            "coordination_type": "agno_team",
            "usage": {},
        }


async def _execute_sequential(input: ActivityExecuteTeamInput) -> dict:
    """Execute agents sequentially"""
    activity.logger.info("Executing team sequentially")

    responses = []
    total_usage = {}

    for agent in input.agents:
        try:
            # Import here to avoid circular dependency
            from control_plane_api.app.services.litellm_service import litellm_service

            model = agent.get("model_id") or "kubiya/claude-sonnet-4"
            model_config = agent.get("model_config", {})

            # Execute agent
            result = litellm_service.execute_agent(
                prompt=f"{input.prompt}\n\nAgent role: {agent.get('description', agent['name'])}",
                model=model,
                system_prompt=input.system_prompt,
                **model_config
            )

            if result.get("success"):
                responses.append({
                    "agent": agent["name"],
                    "response": result.get("response"),
                })

            # Aggregate usage
            usage = result.get("usage", {})
            for key, value in usage.items():
                total_usage[key] = total_usage.get(key, 0) + value

        except Exception as e:
            activity.logger.error(
                f"Agent execution failed",
                extra={"agent_id": agent["id"], "error": str(e)}
            )
            responses.append({
                "agent": agent["name"],
                "error": str(e),
            })

    # Combine responses
    combined_response = "\n\n".join([
        f"**{r['agent']}**: {r.get('response', r.get('error'))}"
        for r in responses
    ])

    return {
        "success": True,
        "response": combined_response,
        "usage": total_usage,
        "coordination_type": "sequential",
    }


async def _execute_parallel(input: ActivityExecuteTeamInput) -> dict:
    """Execute agents in parallel (placeholder - would use asyncio.gather in real impl)"""
    activity.logger.info("Executing team in parallel")
    # For now, fall back to sequential
    # In a real implementation, this would use asyncio.gather or child workflows
    return await _execute_sequential(input)


async def _execute_hierarchical(input: ActivityExecuteTeamInput) -> dict:
    """Execute agents hierarchically with a coordinator (placeholder)"""
    activity.logger.info("Executing team hierarchically")
    # For now, fall back to sequential
    # In a real implementation, this would have a coordinator agent that delegates
    return await _execute_sequential(input)
