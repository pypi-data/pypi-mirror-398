"""
Approval workflow tools for human-in-the-loop approval gates.

Provides tools for workflows to request approval from authorized users
and wait for approval/rejection before continuing.
"""
import os
import time
import asyncio
import httpx
import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

logger = structlog.get_logger()


class ApprovalTools:
    """
    Approval workflow tools for human-in-the-loop gates.

    Provides a temporal-native way to wait for approval from authorized users.
    The workflow pauses execution and polls the control plane for approval status.
    """

    def __init__(
        self,
        control_plane_url: str,
        api_key: str,
        execution_id: str,
        organization_id: str,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize approval tools.

        Args:
            control_plane_url: Control plane API base URL
            api_key: API key for authentication
            execution_id: Current execution ID
            organization_id: Organization ID
            config: Optional configuration (timeout, require_reason, etc.)
        """
        self.control_plane_url = control_plane_url.rstrip("/")
        self.api_key = api_key
        self.execution_id = execution_id
        self.organization_id = organization_id
        self.config = config or {}

        # Configuration
        self.timeout_minutes = self.config.get("timeout_minutes", 1440)  # 24 hours default
        self.require_approval_reason = self.config.get("require_approval_reason", False)
        self.poll_interval_seconds = self.config.get("poll_interval_seconds", 5)  # Poll every 5 seconds

        self.client = httpx.AsyncClient(
            base_url=self.control_plane_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def wait_for_approval(
        self,
        title: str,
        message: Optional[str] = None,
        approver_user_ids: Optional[List[str]] = None,
        approver_user_emails: Optional[List[str]] = None,
        approver_group_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Wait for approval from authorized users.

        This function creates an approval request and polls the control plane
        until the request is approved, rejected, or times out.

        Args:
            title: Brief title for the approval request
            message: Detailed message or reason for approval
            approver_user_ids: List of user IDs who can approve (optional)
            approver_user_emails: List of user emails who can approve (optional)
            approver_group_id: Group ID that can approve (optional)
            context: Additional context data (optional)

        Returns:
            Dict with approval result:
            {
                "approved": bool,
                "status": "approved" | "rejected" | "expired",
                "approval_id": str,
                "approved_by_email": str (if approved),
                "rejection_reason": str (if rejected),
                "resolved_at": str (ISO timestamp)
            }

        Raises:
            Exception: If approval request creation fails or times out
        """
        logger.info(
            "wait_for_approval_started",
            title=title,
            execution_id=self.execution_id,
            approver_emails=approver_user_emails,
        )

        # Validate at least one approver is specified
        if not approver_user_ids and not approver_user_emails and not approver_group_id:
            raise ValueError("At least one of approver_user_ids, approver_user_emails, or approver_group_id must be provided")

        try:
            # Create approval request via control plane API
            approval_request = {
                "execution_id": self.execution_id,
                "title": title,
                "message": message,
                "approver_user_ids": approver_user_ids or [],
                "approver_user_emails": approver_user_emails or [],
                "approver_group_id": approver_group_id,
                "timeout_minutes": self.timeout_minutes,
                "context": context or {},
            }

            response = await self.client.post(
                "/api/v1/approvals",
                json=approval_request,
            )

            if response.status_code != 201:
                error_detail = response.text
                logger.error(
                    "approval_request_creation_failed",
                    status_code=response.status_code,
                    error=error_detail
                )
                raise Exception(f"Failed to create approval request: {error_detail}")

            approval_data = response.json()
            approval_id = approval_data["id"]

            logger.info(
                "approval_request_created",
                approval_id=approval_id,
                title=title,
                execution_id=self.execution_id,
            )

            # Calculate timeout
            start_time = time.time()
            timeout_seconds = self.timeout_minutes * 60
            expires_at = time.time() + timeout_seconds

            # Poll for approval status
            poll_count = 0
            while time.time() < expires_at:
                poll_count += 1

                # Get approval status
                try:
                    status_response = await self.client.get(
                        f"/api/v1/approvals/{approval_id}"
                    )

                    if status_response.status_code == 200:
                        approval_status = status_response.json()

                        if approval_status["status"] == "approved":
                            elapsed_minutes = (time.time() - start_time) / 60
                            logger.info(
                                "approval_granted",
                                approval_id=approval_id,
                                approved_by=approval_status.get("approved_by_email"),
                                elapsed_minutes=round(elapsed_minutes, 2),
                            )

                            return {
                                "approved": True,
                                "status": "approved",
                                "approval_id": approval_id,
                                "approved_by_email": approval_status.get("approved_by_email"),
                                "approved_by_name": approval_status.get("approved_by_name"),
                                "resolved_at": approval_status.get("resolved_at"),
                            }

                        elif approval_status["status"] == "rejected":
                            elapsed_minutes = (time.time() - start_time) / 60
                            logger.info(
                                "approval_rejected",
                                approval_id=approval_id,
                                rejected_by=approval_status.get("approved_by_email"),
                                reason=approval_status.get("rejection_reason"),
                                elapsed_minutes=round(elapsed_minutes, 2),
                            )

                            return {
                                "approved": False,
                                "status": "rejected",
                                "approval_id": approval_id,
                                "rejected_by_email": approval_status.get("approved_by_email"),
                                "rejected_by_name": approval_status.get("approved_by_name"),
                                "rejection_reason": approval_status.get("rejection_reason"),
                                "resolved_at": approval_status.get("resolved_at"),
                            }

                        elif approval_status["status"] == "expired":
                            logger.warning(
                                "approval_expired",
                                approval_id=approval_id,
                            )

                            return {
                                "approved": False,
                                "status": "expired",
                                "approval_id": approval_id,
                                "resolved_at": approval_status.get("resolved_at"),
                            }

                        # Still pending, continue polling
                        if poll_count % 12 == 0:  # Log every minute (12 * 5 seconds)
                            elapsed_minutes = (time.time() - start_time) / 60
                            remaining_minutes = (expires_at - time.time()) / 60
                            logger.debug(
                                "waiting_for_approval",
                                approval_id=approval_id,
                                status=approval_status["status"],
                                elapsed_minutes=round(elapsed_minutes, 2),
                                remaining_minutes=round(remaining_minutes, 2),
                            )

                    else:
                        logger.warning(
                            "approval_status_check_failed",
                            approval_id=approval_id,
                            status_code=status_response.status_code,
                        )

                except Exception as poll_error:
                    logger.warning(
                        "approval_poll_error",
                        approval_id=approval_id,
                        error=str(poll_error),
                    )

                # Wait before next poll
                await asyncio.sleep(self.poll_interval_seconds)

            # Timeout reached
            logger.warning(
                "approval_timeout",
                approval_id=approval_id,
                timeout_minutes=self.timeout_minutes,
            )

            return {
                "approved": False,
                "status": "expired",
                "approval_id": approval_id,
                "resolved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(
                "wait_for_approval_failed",
                title=title,
                execution_id=self.execution_id,
                error=str(e),
            )
            raise

        finally:
            await self.client.aclose()

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        Get the tool schema for LLM function calling.

        Returns list of tool definitions that can be provided to LLMs.
        """
        return [
            {
                "name": "wait_for_approval",
                "description": "Pause workflow execution and wait for approval from authorized users before continuing. "
                               "Use this when you need human approval for sensitive operations, decisions, or actions. "
                               "The workflow will pause until an authorized user approves or rejects the request.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Brief title for the approval request (e.g., 'Deploy to Production', 'Delete Database')"
                        },
                        "message": {
                            "type": "string",
                            "description": "Detailed message explaining why approval is needed and what will happen if approved"
                        },
                        "approver_user_emails": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of user email addresses who can approve this request"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context data to help approvers make a decision"
                        }
                    },
                    "required": ["title", "approver_user_emails"]
                }
            }
        ]
