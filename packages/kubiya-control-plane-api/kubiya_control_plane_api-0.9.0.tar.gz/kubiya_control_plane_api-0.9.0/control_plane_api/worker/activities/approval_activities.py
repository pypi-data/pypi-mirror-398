"""
Approval workflow activities for Temporal.

Activities for creating approval requests and waiting for approval/rejection.

Two approaches:
1. Signal-based (recommended): create_approval_request + workflow waits for signal
2. Polling-based (legacy): wait_for_approval_activity polls for status
"""
import os
import httpx
import structlog
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from temporalio import activity

from control_plane_api.worker.services.approval_tools import ApprovalTools

logger = structlog.get_logger()


@dataclass
class ActivityCreateApprovalInput:
    """Input for create_approval_request activity"""
    execution_id: str
    organization_id: str
    title: str
    message: Optional[str] = None
    approver_user_emails: Optional[List[str]] = None
    approver_group_id: Optional[str] = None
    timeout_minutes: int = 1440  # 24 hours default
    context: Optional[Dict[str, Any]] = None


@dataclass
class ActivityCreateApprovalOutput:
    """Output from create_approval_request activity"""
    approval_id: str
    status: str  # "pending"
    expires_at: Optional[str]


@activity.defn
async def create_approval_request(
    input: ActivityCreateApprovalInput,
) -> ActivityCreateApprovalOutput:
    """
    Create an approval request via Control Plane API and return immediately.

    This is the signal-based approach where:
    1. Activity creates the approval request
    2. Activity returns approval_id to workflow
    3. Workflow waits for approval_response signal
    4. Control Plane sends signal when user approves/rejects

    This is more durable than polling because workflow state is preserved
    across worker restarts.

    Args:
        input: Approval request parameters

    Returns:
        ActivityCreateApprovalOutput with approval_id

    Raises:
        Exception: If approval request creation fails
    """
    activity.logger.info(
        "creating_approval_request",
        title=input.title,
        execution_id=input.execution_id,
        approver_emails=input.approver_user_emails,
        approver_group_id=input.approver_group_id,
    )

    control_plane_url = os.getenv("CONTROL_PLANE_URL")
    api_key = os.getenv("KUBIYA_API_KEY")

    if not control_plane_url or not api_key:
        raise ValueError("CONTROL_PLANE_URL and KUBIYA_API_KEY must be set")

    # Validate at least one approver is specified
    if not input.approver_user_emails and not input.approver_group_id:
        raise ValueError("At least one of approver_user_emails or approver_group_id must be provided")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create approval request
            approval_request = {
                "execution_id": input.execution_id,
                "title": input.title,
                "message": input.message,
                "approver_user_ids": [],
                "approver_user_emails": input.approver_user_emails or [],
                "approver_group_id": input.approver_group_id,
                "timeout_minutes": input.timeout_minutes,
                "context": input.context or {},
            }

            response = await client.post(
                f"{control_plane_url.rstrip('/')}/api/v1/approvals",
                json=approval_request,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 201:
                error_detail = response.text
                activity.logger.error(
                    "approval_request_creation_failed",
                    status_code=response.status_code,
                    error=error_detail,
                )
                raise Exception(f"Failed to create approval request: {error_detail}")

            approval_data = response.json()
            approval_id = approval_data["id"]

            activity.logger.info(
                "approval_request_created_signal_mode",
                approval_id=approval_id,
                title=input.title,
                execution_id=input.execution_id,
            )

            return ActivityCreateApprovalOutput(
                approval_id=approval_id,
                status=approval_data.get("status", "pending"),
                expires_at=approval_data.get("expires_at"),
            )

    except Exception as e:
        activity.logger.error(
            "create_approval_request_failed",
            error=str(e),
            title=input.title,
            execution_id=input.execution_id,
        )
        raise


@dataclass
class ActivityWaitForApprovalInput:
    """Input for wait_for_approval activity"""
    execution_id: str
    organization_id: str
    title: str
    message: Optional[str] = None
    approver_user_ids: Optional[List[str]] = None
    approver_user_emails: Optional[List[str]] = None
    approver_group_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


@activity.defn
async def wait_for_approval_activity(input: ActivityWaitForApprovalInput) -> Dict[str, Any]:
    """
    Activity to create approval request and wait for approval/rejection.

    This activity:
    1. Creates an approval request via control plane API
    2. Publishes approval_request event for UI streaming
    3. Polls control plane for approval status changes
    4. Returns result when approved/rejected/expired

    Args:
        input: Approval request configuration

    Returns:
        Dict with approval result:
        {
            "approved": bool,
            "status": "approved" | "rejected" | "expired",
            "approval_id": str,
            "approved_by_email": str (if approved),
            "rejection_reason": str (if rejected)
        }

    Raises:
        Exception: If approval request creation fails
    """
    activity.logger.info(
        "wait_for_approval_activity_started",
        execution_id=input.execution_id,
        title=input.title,
    )

    try:
        # Get control plane configuration from environment
        control_plane_url = os.getenv("CONTROL_PLANE_URL")
        api_key = os.getenv("KUBIYA_API_KEY")

        if not control_plane_url or not api_key:
            raise ValueError("CONTROL_PLANE_URL and KUBIYA_API_KEY must be set")

        # Initialize approval tools
        approval_tools = ApprovalTools(
            control_plane_url=control_plane_url,
            api_key=api_key,
            execution_id=input.execution_id,
            organization_id=input.organization_id,
            config=input.config or {},
        )

        # Wait for approval (this polls until approved/rejected/expired)
        result = await approval_tools.wait_for_approval(
            title=input.title,
            message=input.message,
            approver_user_ids=input.approver_user_ids,
            approver_user_emails=input.approver_user_emails,
            approver_group_id=input.approver_group_id,
            context=input.context,
        )

        activity.logger.info(
            "wait_for_approval_activity_completed",
            execution_id=input.execution_id,
            approval_id=result.get("approval_id"),
            status=result.get("status"),
            approved=result.get("approved"),
        )

        return result

    except Exception as e:
        activity.logger.error(
            "wait_for_approval_activity_failed",
            execution_id=input.execution_id,
            error=str(e),
        )
        raise
