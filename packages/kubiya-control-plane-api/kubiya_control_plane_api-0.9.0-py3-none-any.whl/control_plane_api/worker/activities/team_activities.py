"""Team-related Temporal activities"""

import os
import httpx
from dataclasses import dataclass
from typing import Optional, List, Any, Dict
from datetime import datetime, timezone
from temporalio import activity
import structlog
from pathlib import Path
from types import GeneratorType

from agno.agent import Agent
from agno.team import Team
from agno.models.litellm import LiteLLM
from agno.tools.shell import ShellTools
from agno.tools.python import PythonTools
from agno.tools.file import FileTools

from control_plane_api.worker.activities.agent_activities import update_execution_status, ActivityUpdateExecutionInput
from control_plane_api.worker.control_plane_client import get_control_plane_client
from control_plane_api.worker.services.skill_factory import SkillFactory
from control_plane_api.worker.services.team_executor_v2 import TeamExecutorServiceV2
from control_plane_api.worker.services.session_service import SessionService
from control_plane_api.worker.services.cancellation_manager import CancellationManager

logger = structlog.get_logger()


def serialize_tool_output(output: Any, max_length: int = 10000) -> Optional[str]:
    """
    Safely serialize tool output for JSON encoding.

    Handles:
    - Generator objects (consumes and converts to string)
    - Large strings (truncates with indication)
    - None values
    - Other types (converts to string)

    Args:
        output: Tool output to serialize
        max_length: Maximum length for output string (default 10000)

    Returns:
        Serialized string or None
    """
    if output is None:
        return None

    try:
        # Check if it's a generator - consume it first
        if isinstance(output, GeneratorType):
            # Consume generator and join results
            output = ''.join(str(item) for item in output)

        # Convert to string
        output_str = str(output)

        # Truncate if too long
        if len(output_str) > max_length:
            return output_str[:max_length] + f"\n... (truncated, {len(output_str) - max_length} chars omitted)"

        return output_str

    except Exception as e:
        logger.warning("failed_to_serialize_tool_output", error=str(e))
        return f"<Failed to serialize output: {str(e)}>"

# Global registry for active Team instances to support cancellation
# Key: execution_id, Value: {team: Team, run_id: str}
_active_teams: Dict[str, Dict[str, Any]] = {}


def instantiate_skill(skill_data: dict) -> Optional[Any]:
    """
    Instantiate an Agno toolkit based on skill configuration from Control Plane.

    Args:
        skill_data: Skill data from Control Plane API containing:
            - type: Skill type (file_system, shell, python, docker, etc.)
            - name: Skill name
            - configuration: Dict with skill-specific config
            - enabled: Whether skill is enabled

    Returns:
        Instantiated Agno toolkit or None if type not supported/enabled
    """
    if not skill_data.get("enabled", True):
        print(f"   ⊗ Skipping disabled skill: {skill_data.get('name')}")
        return None

    skill_type = skill_data.get("type", "").lower()
    config = skill_data.get("configuration", {})
    name = skill_data.get("name", "Unknown")

    try:
        # Map Control Plane skill types to Agno toolkit classes
        if skill_type in ["file_system", "file", "file_generation"]:
            # FileTools: file operations (read, write, list, search)
            # Note: file_generation is mapped to FileTools (save_file functionality)
            base_dir = config.get("base_dir")
            toolkit = FileTools(
                base_dir=Path(base_dir) if base_dir else None,
                enable_save_file=config.get("enable_save_file", True),
                enable_read_file=config.get("enable_read_file", True),
                enable_list_files=config.get("enable_list_files", True),
                enable_search_files=config.get("enable_search_files", True),
            )
            print(f"   ✓ Instantiated FileTools: {name}")
            if skill_type == "file_generation":
                print(f"     - Type: File Generation (using FileTools.save_file)")
            print(f"     - Base Dir: {base_dir or 'Current directory'}")
            print(f"     - Read: {config.get('enable_read_file', True)}, Write: {config.get('enable_save_file', True)}")
            return toolkit

        elif skill_type in ["shell", "bash"]:
            # ShellTools: shell command execution
            base_dir = config.get("base_dir")
            toolkit = ShellTools(
                base_dir=Path(base_dir) if base_dir else None,
                enable_run_shell_command=config.get("enable_run_shell_command", True),
            )
            print(f"   ✓ Instantiated ShellTools: {name}")
            print(f"     - Base Dir: {base_dir or 'Current directory'}")
            print(f"     - Run Commands: {config.get('enable_run_shell_command', True)}")
            return toolkit

        elif skill_type == "python":
            # PythonTools: Python code execution
            base_dir = config.get("base_dir")
            toolkit = PythonTools(
                base_dir=Path(base_dir) if base_dir else None,
                safe_globals=config.get("safe_globals"),
                safe_locals=config.get("safe_locals"),
            )
            print(f"   ✓ Instantiated PythonTools: {name}")
            print(f"     - Base Dir: {base_dir or 'Current directory'}")
            return toolkit

        elif skill_type == "docker":
            # DockerTools requires docker package and running Docker daemon
            try:
                from agno.tools.docker import DockerTools
                import docker

                # Check if Docker daemon is accessible
                try:
                    docker_client = docker.from_env()
                    docker_client.ping()

                    # Docker is available, instantiate toolkit
                    toolkit = DockerTools()
                    print(f"   ✓ Instantiated DockerTools: {name}")
                    print(f"     - Docker daemon: Connected")
                    docker_client.close()
                    return toolkit

                except Exception as docker_error:
                    print(f"   ⚠ Docker daemon not available - skipping: {name}")
                    print(f"     Error: {str(docker_error)}")
                    return None

            except ImportError:
                print(f"   ⚠ Docker skill requires 'docker' package - skipping: {name}")
                print(f"     Install with: pip install docker")
                return None

        else:
            print(f"   ⚠ Unsupported skill type '{skill_type}': {name}")
            return None

    except Exception as e:
        print(f"   ❌ Error instantiating skill '{name}' (type: {skill_type}): {str(e)}")
        logger.error(
            f"Error instantiating skill",
            extra={
                "skill_name": name,
                "skill_type": skill_type,
                "error": str(e)
            }
        )
        return None


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
    mcp_servers: dict = None  # MCP servers configuration
    session_id: Optional[str] = None  # Session ID for session management
    user_id: Optional[str] = None  # User ID for multi-user support
    model_id: Optional[str] = None  # Model ID for the team coordinator
    model_config: Optional[dict] = None  # Model configuration
    # Note: control_plane_url and api_key are read from worker environment variables (CONTROL_PLANE_URL, KUBIYA_API_KEY)

    def __post_init__(self):
        if self.agents is None:
            self.agents = []
        if self.team_config is None:
            self.team_config = {}
        if self.mcp_servers is None:
            self.mcp_servers = {}
        if self.model_config is None:
            self.model_config = {}
        # Default model_id if not provided
        if self.model_id is None:
            self.model_id = self.team_config.get("llm", {}).get("model", "kubiya/claude-sonnet-4")


@activity.defn
async def get_team_agents(input: ActivityGetTeamAgentsInput) -> dict:
    """
    Get all agents in a team via Control Plane API.

    This activity fetches team details including member agents from the Control Plane.

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
        # Get Control Plane URL and Kubiya API key from environment
        control_plane_url = os.getenv("CONTROL_PLANE_URL")
        kubiya_api_key = os.getenv("KUBIYA_API_KEY")

        if not control_plane_url:
            raise ValueError("CONTROL_PLANE_URL environment variable not set")
        if not kubiya_api_key:
            raise ValueError("KUBIYA_API_KEY environment variable not set")

        print(f"Fetching team from Control Plane API: {control_plane_url}")

        # Call Control Plane API to get team with agents
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{control_plane_url}/api/v1/teams/{input.team_id}",
                headers={
                    "Authorization": f"Bearer {kubiya_api_key}",
                    "Content-Type": "application/json",
                }
            )

            if response.status_code == 404:
                print(f"Team not found!")
                activity.logger.error(
                    f"[DEBUG] Team not found",
                    extra={
                        "team_id": input.team_id,
                        "organization_id": input.organization_id,
                    }
                )
                return {"agents": [], "count": 0}
            elif response.status_code != 200:
                raise Exception(f"Failed to get team: {response.status_code} - {response.text}")

            team_data = response.json()

        # Extract agents from the API response
        # The API returns a TeamWithAgentsResponse which includes the agents array
        agents = team_data.get("agents", [])

        print(f"Query executed. Agents found: {len(agents)}")

        activity.logger.info(
            f"[DEBUG] Query executed, processing results",
            extra={
                "agents_found": len(agents),
                "agent_ids": [a.get("id") for a in agents],
            }
        )

        print(f"Agents found: {len(agents)}")
        if agents:
            for agent in agents:
                print(f"  - {agent.get('name')} (ID: {agent.get('id')})")

        activity.logger.info(
            f"[DEBUG] Retrieved team agents via API",
            extra={
                "team_id": input.team_id,
                "agent_count": len(agents),
                "agent_names": [a.get("name") for a in agents],
                "agent_ids": [a.get("id") for a in agents],
            }
        )

        if not agents:
            print(f"\n!!! NO AGENTS FOUND - Team may have no members !!!")
            activity.logger.warning(
                f"[DEBUG] WARNING: No agents found for team",
                extra={
                    "team_id": input.team_id,
                    "organization_id": input.organization_id,
                }
            )

        print(f"\n=== GET_TEAM_AGENTS END: Returning {len(agents)} agents ===\n\n")
        return {
            "agents": agents,
            "count": len(agents),
        }

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
    Execute team coordination using runtime-abstracted execution (V2).

    This activity uses TeamExecutorServiceV2 which:
    - Detects the team's runtime configuration (claude_code or agno)
    - Routes to appropriate executor
    - Handles session management
    - Provides streaming support

    Args:
        input: Activity input with team execution details

    Returns:
        Dict with aggregated response, usage, success flag
    """
    print("\n" + "="*80)
    print("🚀 TEAM EXECUTION START (V2)")
    print("="*80)
    print(f"Execution ID: {input.execution_id}")
    print(f"Team ID: {input.team_id}")
    print(f"Organization: {input.organization_id}")
    print(f"Agent Count: {len(input.agents)}")
    print(f"MCP Servers: {len(input.mcp_servers)} configured" if input.mcp_servers else "MCP Servers: None")
    print(f"Session ID: {input.session_id}")
    print(f"Prompt: {input.prompt[:100]}..." if len(input.prompt) > 100 else f"Prompt: {input.prompt}")
    print("="*80 + "\n")

    activity.logger.info(
        f"Executing team coordination with V2 (runtime-abstracted)",
        extra={
            "execution_id": input.execution_id,
            "team_id": input.team_id,
            "organization_id": input.organization_id,
            "agent_count": len(input.agents),
            "has_mcp_servers": bool(input.mcp_servers),
            "mcp_server_count": len(input.mcp_servers) if input.mcp_servers else 0,
            "mcp_server_ids": list(input.mcp_servers.keys()) if input.mcp_servers else [],
            "session_id": input.session_id,
            "team_config_runtime": input.team_config.get("runtime", "default") if input.team_config else "default",
        }
    )

    try:
        # Initialize services
        control_plane = get_control_plane_client()
        session_service = SessionService(control_plane)
        cancellation_manager = CancellationManager()

        # Create V2 executor
        executor = TeamExecutorServiceV2(
            control_plane=control_plane,
            session_service=session_service,
            cancellation_manager=cancellation_manager,
        )

        # Execute using V2 - it will handle runtime detection and routing
        result = await executor.execute(input)

        print("\n" + "="*80)
        print("🏁 TEAM EXECUTION END (V2)")
        print("="*80 + "\n")

        return result

    except Exception as e:
        print("\n" + "="*80)
        print("❌ TEAM EXECUTION FAILED (V2)")
        print("="*80)
        print(f"Error: {str(e)}")
        print("="*80 + "\n")

        activity.logger.error(
            f"Team coordination failed (V2)",
            extra={
                "execution_id": input.execution_id,
                "error": str(e),
            }
        )
        return {
            "success": False,
            "error": str(e),
            "coordination_type": "unknown",
            "usage": {},
        }





@dataclass
class ActivityCancelTeamInput:
    execution_id: str


@activity.defn(name="cancel_team_run")
async def cancel_team_run(input: ActivityCancelTeamInput) -> dict:
    """Cancel an active team run using Agno's cancel_run API."""
    print("\n" + "="*80)
    print("🛑 CANCEL TEAM RUN")
    print("="*80)
    print(f"Execution ID: {input.execution_id}\n")

    try:
        if input.execution_id not in _active_teams:
            print(f"⚠️  Team not found in registry - may have already completed")
            return {"success": False, "error": "Team not found or already completed", "execution_id": input.execution_id}

        team_info = _active_teams[input.execution_id]
        team = team_info["team"]
        run_id = team_info.get("run_id")

        if not run_id:
            print(f"⚠️  No run_id found - execution may not have started yet")
            return {"success": False, "error": "Execution not started yet", "execution_id": input.execution_id}

        print(f"🆔 Found run_id: {run_id}")
        print(f"🛑 Calling team.cancel_run()...")

        success = team.cancel_run(run_id)

        if success:
            print(f"✅ Team run cancelled successfully!\n")
            del _active_teams[input.execution_id]
            return {"success": True, "execution_id": input.execution_id, "run_id": run_id, "cancelled_at": datetime.now(timezone.utc).isoformat()}
        else:
            print(f"⚠️  Cancel failed - run may have already completed\n")
            return {"success": False, "error": "Cancel failed - run may be completed", "execution_id": input.execution_id, "run_id": run_id}

    except Exception as e:
        print(f"❌ Error cancelling run: {str(e)}\n")
        return {"success": False, "error": str(e), "execution_id": input.execution_id}
