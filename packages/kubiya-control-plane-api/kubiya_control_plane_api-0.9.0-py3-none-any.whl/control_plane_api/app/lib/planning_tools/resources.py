"""
Resources Context Tools - Fetch general resource and capability information
"""

from typing import Optional
from sqlalchemy.orm import Session
from control_plane_api.app.lib.planning_tools.base import BasePlanningTools
from control_plane_api.app.lib.supabase import get_supabase


class ResourcesContextTools(BasePlanningTools):
    """
    Tools for fetching general resource and capability context

    Provides methods to:
    - List available tools and skills
    - Query project information
    - Get integration capabilities
    - Check system-wide resources
    """

    def __init__(self, db: Optional[Session] = None, organization_id: Optional[str] = None):
        super().__init__(db=db, organization_id=organization_id)
        self.name = "resources_context_tools"

    async def list_available_skills(self) -> str:
        """
        List all available skills that agents can use

        Returns:
            Formatted list of skills including:
            - Skill name and category
            - Available tools within each skill
            - Usage descriptions
            - Cost implications
        """
        try:
            response = await self._make_request("GET", "/skills")

            skills = response if isinstance(response, list) else response.get("skills", [])

            output = [f"Available Skills ({len(skills)} total):"]

            for idx, skill in enumerate(skills, 1):
                name = skill.get("name", "Unknown")
                category = skill.get("category", "General")
                tools = skill.get("tools", [])

                output.append(f"\n{idx}. {name} (Category: {category})")
                output.append(f"   Description: {skill.get('description', 'No description')}")

                if tools:
                    output.append(f"   Tools ({len(tools)}):")
                    for tool in tools[:5]:  # Show first 5 tools
                        tool_name = tool.get("name", "unknown")
                        output.append(f"     - {tool_name}")
                    if len(tools) > 5:
                        output.append(f"     ... and {len(tools) - 5} more")

            return "\n".join(output)

        except Exception as e:
            return f"Error listing skills: {str(e)}"

    async def get_skill_details(self, skill_name: str) -> str:
        """
        Get detailed information about a specific skill

        Args:
            skill_name: Name of the skill to fetch

        Returns:
            Detailed skill information including all available tools
        """
        try:
            response = await self._make_request("GET", f"/skills/{skill_name}")

            return self._format_detail_response(
                item=response,
                title=f"Skill Details: {skill_name}",
            )

        except Exception as e:
            return f"Error fetching skill {skill_name}: {str(e)}"

    async def list_projects(self, limit: int = 50) -> str:
        """
        List all available projects

        Args:
            limit: Maximum number of projects to return

        Returns:
            List of projects with basic information
        """
        try:
            params = {"limit": limit}
            if self.organization_id:
                params["organization_id"] = self.organization_id

            response = await self._make_request("GET", "/projects", params=params)

            projects = response if isinstance(response, list) else response.get("projects", [])

            return self._format_list_response(
                items=projects,
                title="Available Projects",
                key_fields=["description", "status", "owner"],
            )

        except Exception as e:
            return f"Error listing projects: {str(e)}"

    async def get_project_details(self, project_id: str) -> str:
        """
        Get detailed information about a specific project

        Args:
            project_id: ID of the project

        Returns:
            Detailed project information
        """
        try:
            response = await self._make_request("GET", f"/projects/{project_id}")

            return self._format_detail_response(
                item=response,
                title=f"Project Details: {response.get('name', 'Unknown')}",
            )

        except Exception as e:
            return f"Error fetching project {project_id}: {str(e)}"

    async def list_integrations(self) -> str:
        """
        List all available integrations

        Returns:
            List of available integrations (Slack, Jira, GitHub, AWS, etc.)
        """
        try:
            response = await self._make_request("GET", "/integrations")

            integrations = response if isinstance(response, list) else response.get("integrations", [])

            return self._format_list_response(
                items=integrations,
                title="Available Integrations",
                key_fields=["type", "status", "capabilities"],
            )

        except Exception as e:
            return f"Error listing integrations: {str(e)}"

    async def get_organization_info(self) -> str:
        """
        Get information about the current organization

        Returns:
            Organization information including:
            - Resource limits
            - Active agents/teams count
            - Usage statistics
        """
        try:
            if not self.organization_id:
                return "Organization ID not provided"

            response = await self._make_request("GET", f"/organizations/{self.organization_id}")

            # Get additional statistics
            agents = await self._make_request("GET", "/agents", params={"organization_id": self.organization_id})
            teams = await self._make_request("GET", "/teams", params={"organization_id": self.organization_id})

            agent_count = len(agents) if isinstance(agents, list) else agents.get("count", 0)
            team_count = len(teams) if isinstance(teams, list) else teams.get("count", 0)

            output = [
                f"Organization: {response.get('name', 'Unknown')}",
                f"  ID: {self.organization_id}",
                f"  Status: {response.get('status', 'unknown')}",
                f"  Active Agents: {agent_count}",
                f"  Active Teams: {team_count}",
            ]

            if "resource_limits" in response:
                output.append("\n  Resource Limits:")
                for key, value in response["resource_limits"].items():
                    output.append(f"    {key}: {value}")

            return "\n".join(output)

        except Exception as e:
            return f"Error fetching organization info: {str(e)}"

    async def search_tools_by_capability(self, capability: str) -> str:
        """
        Search for tools that provide a specific capability

        Args:
            capability: Capability to search for (e.g., "aws", "kubernetes", "database")

        Returns:
            List of tools/skills that provide the capability
        """
        try:
            response = await self._make_request("GET", "/skills")
            skills = response if isinstance(response, list) else response.get("skills", [])

            matching_tools = []
            for skill in skills:
                skill_text = f"{skill.get('name', '')} {skill.get('description', '')}".lower()
                tools = skill.get("tools", [])

                if capability.lower() in skill_text:
                    matching_tools.append({
                        "name": skill.get("name"),
                        "category": skill.get("category"),
                        "description": skill.get("description"),
                        "tool_count": len(tools),
                    })
                else:
                    # Check individual tools
                    for tool in tools:
                        tool_text = f"{tool.get('name', '')} {tool.get('description', '')}".lower()
                        if capability.lower() in tool_text:
                            matching_tools.append({
                                "name": f"{skill.get('name')}/{tool.get('name')}",
                                "category": skill.get("category"),
                                "description": tool.get("description"),
                                "tool_count": 1,
                            })

            return self._format_list_response(
                items=matching_tools,
                title=f"Tools/Skills with '{capability}' capability",
                key_fields=["category", "description"],
            )

        except Exception as e:
            return f"Error searching tools: {str(e)}"
