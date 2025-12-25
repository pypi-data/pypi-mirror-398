"""
Task Planning Helper Functions
"""
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
import structlog
import os

logger = structlog.get_logger()

# Debug configuration - set via environment variable
DEBUG_SAVE_PROMPTS = os.getenv("DEBUG_SAVE_PLANNING_PROMPTS", "false").lower() in ("true", "1", "yes")
DEBUG_PROMPTS_DIR = os.getenv("DEBUG_PROMPTS_DIR", "./debug_prompts")

# Refinement mode instructions template
REFINEMENT_INSTRUCTIONS = """
## REFINEMENT MODE - Critical Instructions

You are refining an existing plan (Iteration #{iteration}). Follow these rules:

1. **PRESERVE Unchanged Portions**:
   - Keep ALL parts of the previous plan that the user didn't ask to change
   - Maintain the same agent/team assignments unless specifically requested to change
   - Preserve task IDs, dependencies, and structure where possible

2. **ONLY Modify What Was Requested**:
   - Read the user feedback carefully
   - Change ONLY the specific aspects mentioned in the feedback
   - Don't over-optimize or change things that work

3. **EXPLAIN Changes**:
   - In the summary, briefly mention what changed from the previous iteration
   - Reference why changes were made based on user feedback
   - Keep the reasoning from the previous plan if still valid

4. **Incremental Updates**:
   - If user says "change task 3 to use a different agent", only update task 3
   - If user says "add a testing step", add it without changing other tasks
   - Think minimal, surgical changes - not full replanning

5. **Context Awareness**:
   - Use the conversation history above to understand the full context
   - Reference previous decisions and build upon them
   - Maintain consistency with earlier iterations
"""


def make_json_serializable(obj):
    """
    Recursively convert datetime objects to ISO format strings for JSON serialization

    Args:
        obj: Object to make JSON serializable (dict, list, or primitive)

    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    else:
        return obj


def save_planning_prompt_debug(prompt: str, iteration: int = 1, task_desc: str = "") -> Optional[str]:
    """
    Save planning prompt to file for debugging if DEBUG_SAVE_PLANNING_PROMPTS is enabled

    Args:
        prompt: The planning prompt to save
        iteration: Planning iteration number
        task_desc: Short task description for filename

    Returns:
        Path to saved file or None if debug is disabled
    """
    if not DEBUG_SAVE_PROMPTS:
        return None

    try:
        # Create debug directory if it doesn't exist
        debug_dir = Path(DEBUG_PROMPTS_DIR)
        debug_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds

        # Sanitize task description for filename
        task_slug = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in task_desc[:50])
        if not task_slug:
            task_slug = "unknown_task"

        filename = f"planning_prompt_{timestamp}_iter{iteration}_{task_slug}.txt"
        filepath = debug_dir / filename

        # Write prompt to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Planning Prompt Debug\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Iteration: {iteration}\n")
            f.write(f"# Task: {task_desc}\n")
            f.write(f"# {'=' * 80}\n\n")
            f.write(prompt)

        logger.info(
            "saved_planning_prompt_debug",
            filepath=str(filepath),
            prompt_length=len(prompt),
            iteration=iteration
        )

        return str(filepath)

    except Exception as e:
        logger.error("failed_to_save_planning_prompt_debug", error=str(e))
        return None


def _extract_organization_id_from_token(api_token: Optional[str]) -> Optional[str]:
    """
    Extract organization ID from JWT token

    Args:
        api_token: JWT token string

    Returns:
        Organization ID if found, None otherwise
    """
    if not api_token:
        return None

    try:
        import jwt
        # Decode without verification to get organization
        decoded = jwt.decode(api_token, options={"verify_signature": False})
        org_id = decoded.get("organization") or decoded.get("org") or decoded.get("org_id")

        if org_id:
            logger.debug("extracted_org_from_token", organization_id=org_id)

        return org_id
    except Exception as e:
        logger.warning("failed_to_decode_token", error=str(e))
        return None


def _get_organization_id_fallback(agents: List, teams: List) -> Optional[str]:
    """
    Get organization ID from agents or teams as fallback

    Args:
        agents: List of agent objects
        teams: List of team objects

    Returns:
        Organization ID if found, None otherwise
    """
    if agents and len(agents) > 0:
        return getattr(agents[0], "organization_id", None)
    elif teams and len(teams) > 0:
        return getattr(teams[0], "organization_id", None)
    return None


async def _discover_agents(db: Session, organization_id: Optional[str], limit: int = 50) -> List[dict]:
    """
    Discover available agents from database

    Args:
        db: Database session
        organization_id: Organization ID for filtering
        limit: Maximum number of agents to discover

    Returns:
        List of discovered agents as dicts
    """
    try:
        from control_plane_api.app.lib.planning_tools import AgentsContextTools
        agents_tools = AgentsContextTools(db=db, organization_id=organization_id)
        discovered_agents = await agents_tools.list_agents(limit=limit)
        logger.info("discovered_agents_before_planning", count=len(discovered_agents))
        return discovered_agents
    except Exception as e:
        logger.error("failed_to_discover_agents", error=str(e))
        return []


async def _discover_teams(db: Session, organization_id: Optional[str], limit: int = 50) -> List[dict]:
    """
    Discover available teams from database

    Args:
        db: Database session
        organization_id: Organization ID for filtering
        limit: Maximum number of teams to discover

    Returns:
        List of discovered teams as dicts
    """
    try:
        from control_plane_api.app.lib.planning_tools import TeamsContextTools
        teams_tools = TeamsContextTools(db=db, organization_id=organization_id)
        discovered_teams = await teams_tools.list_teams(limit=limit)
        logger.info("discovered_teams_before_planning", count=len(discovered_teams))
        return discovered_teams
    except Exception as e:
        logger.error("failed_to_discover_teams", error=str(e))
        return []


def _prepare_resources_for_planning(
    request_agents: Optional[List],
    request_teams: Optional[List],
    discovered_agents: List[dict],
    discovered_teams: List[dict]
) -> tuple[List[dict], List[dict]]:
    """
    Prepare agents and teams for planning by converting to JSON-serializable format

    Args:
        request_agents: Agents provided in request
        request_teams: Teams provided in request
        discovered_agents: Agents discovered from database
        discovered_teams: Teams discovered from database

    Returns:
        Tuple of (agents_to_use, teams_to_use) as JSON-serializable dicts
    """
    # Prepare agents
    agents_to_use = []
    if request_agents:
        agents_to_use = [a.model_dump() for a in request_agents]
    elif discovered_agents:
        agents_to_use = discovered_agents

    # Prepare teams
    teams_to_use = []
    if request_teams:
        teams_to_use = [t.model_dump() for t in request_teams]
    elif discovered_teams:
        teams_to_use = discovered_teams

    # Make JSON serializable
    agents_to_use = make_json_serializable(agents_to_use)
    teams_to_use = make_json_serializable(teams_to_use)

    # Log agent data for debugging
    if agents_to_use:
        logger.info("agent_data_for_planner",
                   agent_count=len(agents_to_use),
                   first_agent_id=agents_to_use[0].get('id') if agents_to_use else None,
                   first_agent_name=agents_to_use[0].get('name') if agents_to_use else None,
                   has_skills=len(agents_to_use[0].get('skills', [])) if agents_to_use else 0,
                   has_exec_env=bool(agents_to_use[0].get('execution_environment')) if agents_to_use else False)

    return agents_to_use, teams_to_use


def _infer_agent_specialty(name: str, description: Optional[str]) -> str:
    """
    Infer agent specialty from name and description for better context.
    """
    name_lower = name.lower()
    desc_lower = (description or "").lower()

    # Check for specific specialties
    if "devops" in name_lower or "devops" in desc_lower:
        return "Infrastructure, deployments, cloud operations, monitoring"
    elif "security" in name_lower or "ciso" in name_lower or "security" in desc_lower:
        return "Security audits, compliance, vulnerability scanning, IAM"
    elif "data" in name_lower or "analytics" in desc_lower:
        return "Data analysis, ETL, reporting, database operations"
    elif "backend" in name_lower or "api" in desc_lower:
        return "API development, backend services, database integration"
    elif "frontend" in name_lower or "ui" in desc_lower:
        return "UI development, React/Vue/Angular, responsive design"
    elif "full" in name_lower or "fullstack" in name_lower:
        return "End-to-end development, frontend + backend + infrastructure"
    elif "test" in name_lower or "qa" in desc_lower:
        return "Testing, quality assurance, test automation"
    else:
        return "General automation, scripting, API integration, cloud operations"


def format_sse_message(event: str, data: dict) -> str:
    """Format data as Server-Sent Event message"""
    import json
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
