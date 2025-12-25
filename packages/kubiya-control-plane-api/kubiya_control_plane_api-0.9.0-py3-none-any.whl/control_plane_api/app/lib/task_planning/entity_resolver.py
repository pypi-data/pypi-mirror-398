"""
Entity name-to-UUID resolution helpers for task planning.

This module provides functions to resolve entity names (agents, teams, worker queues,
environments) to their actual UUIDs. This is needed because the LLM planning workflow
often returns entity names in the entity_id field instead of UUIDs, which causes
PostgreSQL errors when trying to execute plans.
"""
from typing import Optional
from sqlalchemy.orm import Session
from uuid import UUID
import structlog

from control_plane_api.app.models.agent import Agent
from control_plane_api.app.models.team import Team
from control_plane_api.app.models.worker import WorkerQueue
from control_plane_api.app.models.environment import Environment

logger = structlog.get_logger(__name__)


async def resolve_agent_name_to_uuid(
    name_or_id: str,
    organization_id: str,
    db: Session
) -> Optional[str]:
    """
    Resolve agent name or ID to UUID.

    Args:
        name_or_id: Agent name or UUID string
        organization_id: Organization ID
        db: Database session

    Returns:
        UUID string if found, None otherwise
    """
    # First check if it's already a valid UUID
    try:
        uuid_obj = UUID(name_or_id)
        # It's a valid UUID, verify it exists
        agent = db.query(Agent).filter(
            Agent.id == str(uuid_obj),
            Agent.organization_id == organization_id
        ).first()

        if agent:
            logger.info("agent_uuid_valid", agent_id=str(uuid_obj))
            return str(uuid_obj)
    except (ValueError, AttributeError):
        # Not a UUID, treat as name
        pass

    # Look up by name
    agent = db.query(Agent).filter(
        Agent.name == name_or_id,
        Agent.organization_id == organization_id
    ).first()

    if agent:
        logger.info("agent_resolved", name=name_or_id, uuid=str(agent.id))
        return str(agent.id)

    logger.warning("agent_not_found", name_or_id=name_or_id)
    return None


async def resolve_team_name_to_uuid(
    name_or_id: str,
    organization_id: str,
    db: Session
) -> Optional[str]:
    """
    Resolve team name or ID to UUID.

    Args:
        name_or_id: Team name or UUID string
        organization_id: Organization ID
        db: Database session

    Returns:
        UUID string if found, None otherwise
    """
    # First check if it's already a valid UUID
    try:
        uuid_obj = UUID(name_or_id)
        # It's a valid UUID, verify it exists
        team = db.query(Team).filter(
            Team.id == str(uuid_obj),
            Team.organization_id == organization_id
        ).first()

        if team:
            logger.info("team_uuid_valid", team_id=str(uuid_obj))
            return str(uuid_obj)
    except (ValueError, AttributeError):
        # Not a UUID, treat as name
        pass

    # Look up by name
    team = db.query(Team).filter(
        Team.name == name_or_id,
        Team.organization_id == organization_id
    ).first()

    if team:
        logger.info("team_resolved", name=name_or_id, uuid=str(team.id))
        return str(team.id)

    logger.warning("team_not_found", name_or_id=name_or_id)
    return None


async def resolve_worker_queue_name_to_uuid(
    name_or_id: str,
    organization_id: str,
    db: Session
) -> Optional[str]:
    """
    Resolve worker queue name or ID to UUID.

    Args:
        name_or_id: Worker queue name or UUID string
        organization_id: Organization ID
        db: Database session

    Returns:
        UUID string if found, None otherwise
    """
    # First check if it's already a valid UUID
    try:
        uuid_obj = UUID(name_or_id)
        wq = db.query(WorkerQueue).filter(
            WorkerQueue.id == str(uuid_obj),
            WorkerQueue.organization_id == organization_id,
            WorkerQueue.ephemeral == False,  # Exclude ephemeral queues
            ~WorkerQueue.name.startswith('local-exec')  # Exclude local-exec queues
        ).first()

        if wq:
            logger.info("worker_queue_uuid_valid", wq_id=str(uuid_obj))
            return str(uuid_obj)
    except (ValueError, AttributeError):
        pass

    # Look up by name
    wq = db.query(WorkerQueue).filter(
        WorkerQueue.name == name_or_id,
        WorkerQueue.organization_id == organization_id,
        WorkerQueue.ephemeral == False,  # Exclude ephemeral queues
        ~WorkerQueue.name.startswith('local-exec')  # Exclude local-exec queues
    ).first()

    if wq:
        logger.info("worker_queue_resolved", name=name_or_id, uuid=str(wq.id))
        return str(wq.id)

    logger.warning("worker_queue_not_found", name_or_id=name_or_id)
    return None


async def resolve_environment_name_to_uuid(
    name_or_id: str,
    organization_id: str,
    db: Session
) -> Optional[str]:
    """
    Resolve environment name or ID to UUID.

    Args:
        name_or_id: Environment name or UUID string
        organization_id: Organization ID
        db: Database session

    Returns:
        UUID string if found, None otherwise
    """
    # First check if it's already a valid UUID
    try:
        uuid_obj = UUID(name_or_id)
        env = db.query(Environment).filter(
            Environment.id == str(uuid_obj),
            Environment.organization_id == organization_id
        ).first()

        if env:
            logger.info("environment_uuid_valid", env_id=str(uuid_obj))
            return str(uuid_obj)
    except (ValueError, AttributeError):
        pass

    # Look up by name
    env = db.query(Environment).filter(
        Environment.name == name_or_id,
        Environment.organization_id == organization_id
    ).first()

    if env:
        logger.info("environment_resolved", name=name_or_id, uuid=str(env.id))
        return str(env.id)

    logger.warning("environment_not_found", name_or_id=name_or_id)
    return None


async def resolve_plan_entities(
    plan_response,
    organization_id: str,
    db: Session
) -> None:
    """
    Resolve all entity names in a plan response to UUIDs (in-place).

    This modifies the plan_response object to replace entity names with UUIDs
    in the recommended_execution section.

    Args:
        plan_response: TaskPlanResponse object
        organization_id: Organization ID
        db: Database session
    """
    if not plan_response.recommended_execution:
        logger.info("no_recommended_execution_to_resolve")
        return

    rec_exec = plan_response.recommended_execution

    # Resolve main entity (agent or team)
    if rec_exec.entity_id:
        entity_type = rec_exec.entity_type
        name_or_id = rec_exec.entity_id

        if entity_type == "agent":
            uuid = await resolve_agent_name_to_uuid(name_or_id, organization_id, db)
        else:  # team
            uuid = await resolve_team_name_to_uuid(name_or_id, organization_id, db)

        if uuid:
            rec_exec.entity_id = uuid
            logger.info("entity_resolved",
                       entity_type=entity_type,
                       original=name_or_id,
                       resolved=uuid)
        else:
            error_msg = f"{entity_type.capitalize()} '{name_or_id}' not found in organization"
            logger.error("entity_resolution_failed",
                        entity_type=entity_type,
                        name_or_id=name_or_id,
                        error=error_msg)
            # Raise error instead of failing silently
            raise ValueError(f"Entity resolution failed: {error_msg}. Please ensure the {entity_type} exists in your organization.")

    # Resolve worker queue
    if rec_exec.recommended_worker_queue_id:
        wq_uuid = await resolve_worker_queue_name_to_uuid(
            rec_exec.recommended_worker_queue_id,
            organization_id,
            db
        )
        if wq_uuid:
            rec_exec.recommended_worker_queue_id = wq_uuid
            logger.info("worker_queue_resolved", resolved=wq_uuid)

    # Resolve environment
    if rec_exec.recommended_environment_id:
        env_uuid = await resolve_environment_name_to_uuid(
            rec_exec.recommended_environment_id,
            organization_id,
            db
        )
        if env_uuid:
            rec_exec.recommended_environment_id = env_uuid
            logger.info("environment_resolved", resolved=env_uuid)
