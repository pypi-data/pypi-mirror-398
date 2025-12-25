"""
Temporal Cloud Namespace Provisioning Workflow

This workflow handles the provisioning of Temporal Cloud namespaces using tcld CLI.
Since Temporal doesn't provide SDK/API for namespace creation, we use the CLI tool.

Flow:
1. Check if namespace already exists
2. Create namespace if needed
3. Poll until namespace is ready
4. Generate API key
5. Store credentials
6. Update task queue status to 'ready'
"""

from dataclasses import dataclass
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
import structlog

# Import activities
with workflow.unsafe.imports_passed_through():
    from control_plane_api.app.activities.temporal_cloud_activities import (
        check_namespace_exists,
        create_namespace,
        poll_namespace_status,
        generate_namespace_api_key,
        store_namespace_credentials,
        update_task_queue_status,
        CheckNamespaceInput,
        CreateNamespaceInput,
        PollNamespaceStatusInput,
        GenerateApiKeyInput,
        StoreNamespaceCredentialsInput,
    )

logger = structlog.get_logger()


@dataclass
class ProvisionNamespaceInput:
    """Input for namespace provisioning workflow"""
    organization_id: str
    organization_name: str
    task_queue_id: str
    account_id: str
    region: str = "aws-us-east-1"
    retention_days: int = 30


@dataclass
class ProvisionNamespaceOutput:
    """Output from namespace provisioning workflow"""
    success: bool
    namespace_name: str
    namespace_id: str | None = None
    status: str = "pending"
    error_message: str | None = None


@workflow.defn
class ProvisionTemporalNamespaceWorkflow:
    """
    Workflow to provision a Temporal Cloud namespace for an organization.

    This workflow is triggered when the first task queue is created for an org.
    It handles the entire provisioning process including retries and error handling.
    """

    @workflow.run
    async def run(self, input: ProvisionNamespaceInput) -> ProvisionNamespaceOutput:
        """
        Main workflow execution.

        Args:
            input: Provisioning input with org details

        Returns:
            ProvisionNamespaceOutput with result
        """
        workflow.logger.info(
            f"Starting namespace provisioning workflow",
            extra={
                "organization_id": input.organization_id,
                "task_queue_id": input.task_queue_id,
            }
        )

        # Generate namespace name: kubiya-{org_slug}-{short_id}
        # Format: kubiya-acme-corp-a1b2c3
        org_slug = input.organization_name.lower().replace(" ", "-")[:20]
        org_short_id = input.organization_id[:6]
        namespace_name = f"kubiya-{org_slug}-{org_short_id}"

        try:
            # Step 1: Check if namespace already exists
            workflow.logger.info("Step 1: Checking if namespace exists")

            check_result = await workflow.execute_activity(
                check_namespace_exists,
                CheckNamespaceInput(
                    organization_id=input.organization_id,
                    namespace_name=namespace_name,
                ),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                ),
            )

            if check_result.get("exists"):
                workflow.logger.info(
                    f"Namespace already exists",
                    extra={"namespace_name": namespace_name}
                )

                # If it exists and is ready, update task queue and we're done
                if check_result.get("status") == "ready":
                    namespace_id = check_result.get("details", {}).get("id")

                    await workflow.execute_activity(
                        update_task_queue_status,
                        args=[input.task_queue_id, "ready", None, namespace_id],
                        start_to_close_timeout=timedelta(seconds=15),
                    )

                    return ProvisionNamespaceOutput(
                        success=True,
                        namespace_name=namespace_name,
                        namespace_id=namespace_id,
                        status="ready",
                    )

            # Step 2: Create namespace
            workflow.logger.info("Step 2: Creating namespace")

            create_result = await workflow.execute_activity(
                create_namespace,
                CreateNamespaceInput(
                    organization_id=input.organization_id,
                    namespace_name=namespace_name,
                    account_id=input.account_id,
                    region=input.region,
                    retention_days=input.retention_days,
                ),
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=10),
                ),
            )

            if not create_result.get("success"):
                error_msg = create_result.get("error", "Failed to create namespace")
                workflow.logger.error(
                    f"Namespace creation failed",
                    extra={"error": error_msg}
                )

                # Update task queue with error
                await workflow.execute_activity(
                    update_task_queue_status,
                    args=[input.task_queue_id, "error", error_msg, None],
                    start_to_close_timeout=timedelta(seconds=15),
                )

                return ProvisionNamespaceOutput(
                    success=False,
                    namespace_name=namespace_name,
                    status="error",
                    error_message=error_msg,
                )

            namespace_id = create_result.get("namespace_id")

            # Step 3: Poll namespace status until ready
            workflow.logger.info("Step 3: Polling namespace status")

            poll_result = await workflow.execute_activity(
                poll_namespace_status,
                PollNamespaceStatusInput(
                    namespace_name=namespace_name,
                    max_attempts=60,  # 5 minutes max
                    poll_interval_seconds=5,
                ),
                start_to_close_timeout=timedelta(minutes=6),
                retry_policy=RetryPolicy(
                    maximum_attempts=2,
                    initial_interval=timedelta(seconds=5),
                ),
            )

            if not poll_result.get("ready"):
                error_msg = poll_result.get("error", "Namespace not ready")
                workflow.logger.error(
                    f"Namespace provisioning timed out",
                    extra={"attempts": poll_result.get("attempts")}
                )

                # Update task queue with error
                await workflow.execute_activity(
                    update_task_queue_status,
                    args=[input.task_queue_id, "error", error_msg, namespace_id],
                    start_to_close_timeout=timedelta(seconds=15),
                )

                return ProvisionNamespaceOutput(
                    success=False,
                    namespace_name=namespace_name,
                    namespace_id=namespace_id,
                    status="error",
                    error_message=error_msg,
                )

            # Step 4: Generate API key
            workflow.logger.info("Step 4: Generating API key")

            api_key_result = await workflow.execute_activity(
                generate_namespace_api_key,
                GenerateApiKeyInput(
                    namespace_name=namespace_name,
                    key_description=f"Control Plane API Key for {input.organization_name}",
                ),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=10),
                ),
            )

            if not api_key_result.get("success"):
                error_msg = api_key_result.get("error", "Failed to generate API key")
                workflow.logger.error(
                    f"API key generation failed",
                    extra={"error": error_msg}
                )

                # Update task queue with error
                await workflow.execute_activity(
                    update_task_queue_status,
                    args=[input.task_queue_id, "error", error_msg, namespace_id],
                    start_to_close_timeout=timedelta(seconds=15),
                )

                return ProvisionNamespaceOutput(
                    success=False,
                    namespace_name=namespace_name,
                    namespace_id=namespace_id,
                    status="error",
                    error_message=error_msg,
                )

            api_key = api_key_result.get("api_key")

            # Step 5: Store credentials
            workflow.logger.info("Step 5: Storing credentials")

            store_result = await workflow.execute_activity(
                store_namespace_credentials,
                StoreNamespaceCredentialsInput(
                    organization_id=input.organization_id,
                    namespace_name=namespace_name,
                    api_key=api_key,
                    status="ready",
                ),
                start_to_close_timeout=timedelta(seconds=15),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                ),
            )

            stored_namespace_id = store_result.get("namespace_id")

            # Step 6: Update task queue status to ready
            workflow.logger.info("Step 6: Updating task queue status")

            await workflow.execute_activity(
                update_task_queue_status,
                args=[input.task_queue_id, "ready", None, stored_namespace_id],
                start_to_close_timeout=timedelta(seconds=15),
            )

            workflow.logger.info(
                f"Namespace provisioning complete",
                extra={
                    "namespace_name": namespace_name,
                    "namespace_id": stored_namespace_id,
                }
            )

            return ProvisionNamespaceOutput(
                success=True,
                namespace_name=namespace_name,
                namespace_id=stored_namespace_id,
                status="ready",
            )

        except Exception as e:
            error_msg = f"Workflow failed: {str(e)}"
            workflow.logger.error(
                f"Namespace provisioning workflow failed",
                extra={"error": str(e)}
            )

            # Update task queue with error
            try:
                await workflow.execute_activity(
                    update_task_queue_status,
                    args=[input.task_queue_id, "error", error_msg, None],
                    start_to_close_timeout=timedelta(seconds=15),
                )
            except Exception:
                pass  # Best effort

            return ProvisionNamespaceOutput(
                success=False,
                namespace_name=namespace_name,
                status="error",
                error_message=error_msg,
            )
