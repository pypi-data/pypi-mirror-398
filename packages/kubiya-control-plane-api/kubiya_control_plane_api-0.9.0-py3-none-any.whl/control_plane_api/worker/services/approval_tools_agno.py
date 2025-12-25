"""
Agno-compatible approval workflow tools.

Provides wait_for_approval tool as an Agno Tool for seamless integration
with Agno agent runtimes.
"""
import os
from typing import List, Optional, Dict, Any
import structlog
from control_plane_api.worker.services.approval_tools import ApprovalTools

logger = structlog.get_logger()


class ApprovalToolkit:
    """
    Agno toolkit for approval workflow (human-in-the-loop gates).

    Provides tools for workflows to request approval from authorized users
    and wait for approval/rejection before continuing.
    """

    def __init__(
        self,
        control_plane_client: Any,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize approval toolkit.

        Args:
            control_plane_client: Control plane client (provides URL and credentials)
            config: Optional configuration (timeout, etc.)
        """
        self.control_plane_client = control_plane_client
        self.config = config or {}

        # Store environment variable names - will be accessed at tool execution time
        self.control_plane_url = None
        self.api_key = None

        # execution_id and organization_id will be set at runtime
        self.execution_id = None
        self.organization_id = None

        logger.info("approval_toolkit_initialized")

    def set_execution_context(self, execution_id: str, organization_id: str):
        """
        Set execution context (called by runtime before tool execution).

        Args:
            execution_id: Current execution ID
            organization_id: Organization ID
        """
        self.execution_id = execution_id
        self.organization_id = organization_id

    async def wait_for_approval(
        self,
        title: str,
        approver_user_emails: Optional[List[str]] = None,
        approver_group_id: Optional[str] = None,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Wait for approval from authorized users or groups before continuing.

        This tool creates an approval request and pauses the workflow until
        an authorized user approves or rejects the request. Use this for:
        - Deployments to production
        - Destructive operations (deletions, etc.)
        - High-value transactions
        - Policy-gated actions

        APPROVERS: You can specify approvers in three ways:
        1. Pass approver_user_emails parameter (list of emails)
        2. Pass approver_group_id parameter (group UUID)
        3. Use defaults from skill configuration (if configured)

        If you don't specify approvers, the tool will use the default approvers
        configured in the skill settings.

        Args:
            title: Brief title for the approval request (e.g., "Deploy to Production")
            approver_user_emails: List of user email addresses who can approve (optional, uses config default if not provided)
            approver_group_id: Group UUID whose members can approve (optional, uses config default if not provided)
            message: Detailed message explaining why approval is needed (optional)
            context: Additional context data to help approvers decide (optional)

        Returns:
            str: Approval result message

        Examples:
            ```python
            # Approve by specific users
            result = await wait_for_approval(
                title="Deploy to Production",
                message="Deploy version 2.0.0 to production environment",
                approver_user_emails=["ops-lead@company.com", "cto@company.com"],
                context={"version": "2.0.0", "environment": "production"}
            )

            # Approve by group
            result = await wait_for_approval(
                title="Delete Customer Data",
                message="Permanently delete customer data for GDPR request",
                approver_group_id="550e8400-e29b-41d4-a716-446655440000",  # Admin group UUID
            )

            # Approve by group OR specific users
            result = await wait_for_approval(
                title="Emergency Hotfix",
                message="Deploy critical security patch",
                approver_user_emails=["security-lead@company.com"],
                approver_group_id="550e8400-e29b-41d4-a716-446655440000",  # Ops group UUID
            )
            ```
        """
        if not self.execution_id or not self.organization_id:
            return "❌ Error: Approval toolkit not initialized with execution context"

        # Get control plane URL and API key from environment at execution time
        self.control_plane_url = os.getenv("CONTROL_PLANE_URL")
        self.api_key = os.getenv("KUBIYA_API_KEY")

        if not self.control_plane_url or not self.api_key:
            return "❌ Error: CONTROL_PLANE_URL and KUBIYA_API_KEY environment variables must be set"

        # Use config defaults if no approvers specified
        if not approver_user_emails and not approver_group_id:
            # Try to get defaults from config
            approver_user_emails = self.config.get("default_approver_emails")
            approver_group_id = self.config.get("default_approver_group_id")

            # Still no approvers? Error
            if not approver_user_emails and not approver_group_id:
                return (
                    "❌ Error: No approvers specified. Either:\n"
                    "1. Pass approver_user_emails or approver_group_id to this tool call, OR\n"
                    "2. Configure default approvers in the skill configuration"
                )

        logger.info(
            "wait_for_approval_tool_called",
            title=title,
            approver_emails=approver_user_emails,
            approver_group_id=approver_group_id,
            execution_id=self.execution_id,
        )

        try:
            # Create approval tools instance for this execution
            approval_tools = ApprovalTools(
                control_plane_url=self.control_plane_url,
                api_key=self.api_key,
                execution_id=self.execution_id,
                organization_id=self.organization_id,
                config=self.config,
            )

            # Call underlying approval tools
            result = await approval_tools.wait_for_approval(
                title=title,
                message=message,
                approver_user_emails=approver_user_emails or [],
                approver_group_id=approver_group_id,
                context=context,
            )

            if result["approved"]:
                approved_by = result.get("approved_by_email", "unknown")
                return (
                    f"✅ Approval granted by {approved_by}. "
                    f"You may proceed with '{title}'."
                )
            elif result["status"] == "rejected":
                rejected_by = result.get("rejected_by_email", "unknown")
                reason = result.get("rejection_reason", "No reason provided")
                return (
                    f"❌ Request rejected by {rejected_by}. "
                    f"Reason: {reason}. "
                    f"You must not proceed with '{title}'."
                )
            elif result["status"] == "expired":
                return (
                    f"⏱️ Approval request expired without response. "
                    f"You must not proceed with '{title}' without approval."
                )
            else:
                return (
                    f"⚠️ Approval request ended with status: {result['status']}. "
                    f"You must not proceed with '{title}' without explicit approval."
                )

        except Exception as e:
            logger.error(
                "wait_for_approval_tool_error",
                error=str(e),
                title=title,
                execution_id=self.execution_id,
            )
            return (
                f"❌ Failed to request approval: {str(e)}. "
                f"You must not proceed with '{title}' due to approval system error."
            )
