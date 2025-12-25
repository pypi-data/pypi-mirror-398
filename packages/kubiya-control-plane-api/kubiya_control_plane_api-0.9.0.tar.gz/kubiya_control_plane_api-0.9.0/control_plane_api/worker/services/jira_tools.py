"""JIRA Tools - Project management integration with lazy validation"""

from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()


class JiraTools:
    """
    JIRA tools for project management.

    Validates JIRA authorization on first tool use (lazy validation).
    This allows the LLM to see available tools and only validate when actually needed.
    """

    def __init__(self, control_plane_client=None, config: Dict[str, Any] = None):
        """
        Initialize JIRA tools.

        Args:
            control_plane_client: ControlPlaneClient for validation
            config: JIRA configuration from skill
        """
        self.control_plane_client = control_plane_client
        self.config = config or {}
        self._validated = False
        self._validation_result = None

    def _ensure_validated(self) -> None:
        """
        Validate JIRA integration on first tool use.

        Raises:
            Exception: With OAuth URL if not authorized
        """
        if self._validated:
            # Already validated this execution
            return

        if not self.control_plane_client:
            raise Exception(
                "❌ JIRA tools not available: No control plane client configured"
            )

        # Validate once per execution
        self._validated = True
        result = self.control_plane_client.validate_jira_integration()
        self._validation_result = result

        if not result.get("valid"):
            message = result.get("message", "JIRA integration not configured")
            oauth_url = result.get("oauth_url")

            if oauth_url:
                error_msg = (
                    f"❌ {message}\n\n"
                    f"🔗 Please authorize your JIRA account:\n"
                    f"{oauth_url}\n\n"
                    f"After authorizing, please retry your request."
                )
                logger.error(
                    "jira_not_authorized_on_tool_use",
                    message=message,
                    oauth_url=oauth_url,
                )
                raise Exception(error_msg)
            else:
                logger.error("jira_validation_failed_on_tool_use", message=message)
                raise Exception(f"❌ {message}")

        logger.info(
            "jira_validated_on_first_tool_use",
            jira_url=result.get("jira_url"),
            email=result.get("email"),
        )

    def search_issues(
        self,
        project_key: Optional[str] = None,
        jql: Optional[str] = None,
        max_results: int = 50,
    ) -> str:
        """
        Search JIRA issues.

        Args:
            project_key: Filter by project (e.g., "PROJ")
            jql: JQL query string
            max_results: Maximum number of results

        Returns:
            JSON string with issues or error message
        """
        try:
            self._ensure_validated()

            # TODO: Implement actual JIRA API call
            logger.info(
                "jira_search_issues_called",
                project_key=project_key,
                jql=jql,
                max_results=max_results,
            )

            return "JIRA search not yet implemented. Coming soon!"

        except Exception as e:
            return str(e)

    def get_issue(self, issue_key: str) -> str:
        """
        Get details of a specific JIRA issue.

        Args:
            issue_key: JIRA issue key (e.g., "PROJ-123")

        Returns:
            JSON string with issue details or error message
        """
        try:
            self._ensure_validated()

            # TODO: Implement actual JIRA API call
            logger.info("jira_get_issue_called", issue_key=issue_key)

            return f"JIRA get issue ({issue_key}) not yet implemented. Coming soon!"

        except Exception as e:
            return str(e)

    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: Optional[str] = None,
        issue_type: str = "Task",
    ) -> str:
        """
        Create a new JIRA issue.

        Args:
            project_key: Project key (e.g., "PROJ")
            summary: Issue title
            description: Issue description
            issue_type: Issue type (Task, Bug, Story, etc.)

        Returns:
            JSON string with created issue or error message
        """
        try:
            self._ensure_validated()

            # Check if write is enabled
            if not self.config.get("enable_write", False):
                return "❌ JIRA write operations not enabled for this skill"

            # TODO: Implement actual JIRA API call
            logger.info(
                "jira_create_issue_called",
                project_key=project_key,
                summary=summary,
                issue_type=issue_type,
            )

            return "JIRA create issue not yet implemented. Coming soon!"

        except Exception as e:
            return str(e)

    def update_issue(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        Update an existing JIRA issue.

        Args:
            issue_key: JIRA issue key (e.g., "PROJ-123")
            summary: New summary
            description: New description

        Returns:
            Success message or error
        """
        try:
            self._ensure_validated()

            # Check if write is enabled
            if not self.config.get("enable_write", False):
                return "❌ JIRA write operations not enabled for this skill"

            # TODO: Implement actual JIRA API call
            logger.info(
                "jira_update_issue_called",
                issue_key=issue_key,
                has_summary=bool(summary),
                has_description=bool(description),
            )

            return f"JIRA update issue ({issue_key}) not yet implemented. Coming soon!"

        except Exception as e:
            return str(e)

    def transition_issue(self, issue_key: str, transition_name: str) -> str:
        """
        Transition JIRA issue to a new status.

        Args:
            issue_key: JIRA issue key (e.g., "PROJ-123")
            transition_name: Transition name (e.g., "In Progress", "Done")

        Returns:
            Success message or error
        """
        try:
            self._ensure_validated()

            # Check if transitions are enabled
            if not self.config.get("enable_transitions", False):
                return "❌ JIRA transition operations not enabled for this skill"

            # TODO: Implement actual JIRA API call
            logger.info(
                "jira_transition_issue_called",
                issue_key=issue_key,
                transition_name=transition_name,
            )

            return (
                f"JIRA transition issue ({issue_key} → {transition_name}) "
                f"not yet implemented. Coming soon!"
            )

        except Exception as e:
            return str(e)

    def list_projects(self) -> str:
        """
        List all accessible JIRA projects.

        Returns:
            JSON string with projects or error message
        """
        try:
            self._ensure_validated()

            # TODO: Implement actual JIRA API call
            logger.info("jira_list_projects_called")

            return "JIRA list projects not yet implemented. Coming soon!"

        except Exception as e:
            return str(e)
