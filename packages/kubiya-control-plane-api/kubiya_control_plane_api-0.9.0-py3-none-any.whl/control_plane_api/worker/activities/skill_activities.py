"""
Skill Activities for Agent Control Plane Worker.

These activities handle skill resolution and instantiation for agent execution.
"""

import structlog
from dataclasses import dataclass
from typing import Any, Optional
from temporalio import activity
import httpx

logger = structlog.get_logger()


@dataclass
class SkillDefinition:
    """Resolved skill definition with merged configuration"""
    id: str
    name: str
    type: str
    description: str
    enabled: bool
    configuration: dict
    source: str  # 'environment', 'team', 'agent'


@activity.defn
async def resolve_agent_skills(
    agent_id: str,
    control_plane_url: str,
    api_key: str
) -> list[dict]:
    """
    Resolve skills for an agent by calling Control Plane API.

    The Control Plane handles all inheritance logic (Environment → Team → Agent)
    and returns the merged, resolved skill list.

    Args:
        agent_id: Agent ID
        control_plane_url: Control Plane API URL (e.g., https://control-plane.kubiya.ai)
        api_key: API key for authentication

    Returns:
        List of resolved skill definitions with merged configurations
    """
    logger.info(
        "resolving_agent_skills_from_control_plane",
        agent_id=agent_id,
        control_plane_url=control_plane_url
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Call Control Plane API to resolve skills with inheritance
            response = await client.get(
                f"{control_plane_url}/api/v1/skills/associations/agents/{agent_id}/skills/resolved",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code != 200:
                logger.error(
                    "skill_resolution_failed",
                    status_code=response.status_code,
                    response=response.text[:500],
                    agent_id=agent_id
                )
                # Return empty list on failure - agent can still run without tools
                return []

            # Response is list of resolved skills
            skills = response.json()

            logger.info(
                "skills_resolved_from_control_plane",
                agent_id=agent_id,
                skill_count=len(skills),
                skill_types=[t.get("type") for t in skills],
                skill_sources=[t.get("source") for t in skills]
            )

            return skills

    except Exception as e:
        logger.error(
            "skill_resolution_error",
            error=str(e),
            agent_id=agent_id
        )
        return []


@activity.defn
async def instantiate_agent_skills(
    skill_definitions: list[dict]
) -> list[Any]:
    """
    Instantiate agno tool instances from skill definitions.

    Args:
        skill_definitions: List of resolved skill definitions

    Returns:
        List of instantiated agno tool objects
    """
    # Import agno tools
    try:
        from agno.tools.file import FileTools
        from agno.tools.shell import ShellTools
        from agno.tools.docker import DockerTools
        from agno.tools.sleep import SleepTools
        from agno.tools.file_generation import FileGenerationTools
    except ImportError as e:
        logger.error("agno_tools_import_failed", error=str(e))
        return []

    # Import custom worker tools
    try:
        from control_plane_api.worker.services.agent_communication_tools import AgentCommunicationTools
    except ImportError as e:
        logger.error("custom_tools_import_failed", error=str(e))
        AgentCommunicationTools = None

    try:
        from control_plane_api.worker.services.remote_filesystem_tools import RemoteFilesystemTools
    except ImportError as e:
        logger.error("remote_filesystem_tools_import_failed", error=str(e))
        RemoteFilesystemTools = None

    # Tool registry
    SKILL_REGISTRY = {
        "file_system": FileTools,
        "shell": ShellTools,
        "docker": DockerTools,
        "sleep": SleepTools,
        "file_generation": FileGenerationTools,
        "agent_communication": AgentCommunicationTools,
        "remote_filesystem": RemoteFilesystemTools,
    }

    tools = []

    for skill_def in skill_definitions:
        if not skill_def.get("enabled", True):
            logger.debug(
                "skipping_disabled_skill",
                skill_name=skill_def.get("name")
            )
            continue

        skill_type = skill_def.get("type")
        tool_class = SKILL_REGISTRY.get(skill_type)

        if not tool_class:
            logger.warning(
                "unknown_skill_type",
                skill_type=skill_type,
                skill_name=skill_def.get("name")
            )
            continue

        # Get configuration
        config = skill_def.get("configuration", {})

        # Instantiate tool with configuration
        try:
            tool_instance = tool_class(**config)
            tools.append(tool_instance)

            logger.info(
                "skill_instantiated",
                skill_name=skill_def.get("name"),
                skill_type=skill_type,
                configuration=config
            )
        except Exception as e:
            logger.error(
                "skill_instantiation_failed",
                skill_name=skill_def.get("name"),
                skill_type=skill_type,
                error=str(e)
            )
            # Continue with other tools even if one fails

    logger.info(
        "agent_tools_instantiated",
        tool_count=len(tools),
        tool_types=[type(t).__name__ for t in tools]
    )

    return tools


@activity.defn
async def instantiate_custom_skill(
    skill_definition: dict,
    organization_id: str,
    control_plane_url: str,
    api_key: str
) -> Optional[Any]:
    """
    Instantiate a custom skill by loading user-provided Python code.

    Args:
        skill_definition: Skill definition with custom_class path
        organization_id: Organization ID
        control_plane_url: Control Plane API URL
        api_key: API key for authentication

    Returns:
        Instantiated tool instance or None if failed
    """
    logger.info(
        "instantiating_custom_skill",
        skill_name=skill_definition.get("name"),
        organization_id=organization_id
    )

    try:
        # Get custom class path from configuration
        custom_class = skill_definition.get("configuration", {}).get("custom_class")
        if not custom_class:
            logger.error("custom_skill_missing_class", skill_definition=skill_definition)
            return None

        # Fetch custom skill code from Control Plane
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{control_plane_url}/api/v1/skills/{skill_definition['id']}/code",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"organization_id": organization_id}
            )

            if response.status_code != 200:
                logger.error(
                    "custom_skill_code_fetch_failed",
                    status_code=response.status_code
                )
                return None

            code_data = response.json()
            python_code = code_data.get("code")

            if not python_code:
                logger.error("custom_skill_no_code")
                return None

        # Execute code in isolated namespace
        namespace = {}
        exec(python_code, namespace)

        # Extract class from namespace
        class_parts = custom_class.split(".")
        tool_class = namespace.get(class_parts[-1])

        if not tool_class:
            logger.error(
                "custom_skill_class_not_found",
                custom_class=custom_class
            )
            return None

        # Instantiate with configuration
        config = skill_definition.get("configuration", {}).get("custom_config", {})
        tool_instance = tool_class(**config)

        logger.info(
            "custom_skill_instantiated",
            skill_name=skill_definition.get("name"),
            custom_class=custom_class
        )

        return tool_instance

    except Exception as e:
        logger.error(
            "custom_skill_instantiation_error",
            skill_name=skill_definition.get("name"),
            error=str(e)
        )
        return None
