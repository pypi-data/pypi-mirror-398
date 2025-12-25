"""
Temporal Cloud Provisioning Service

This service handles provisioning Temporal Cloud namespaces via the
Vercel serverless function (api/provision-namespace.go).
"""

import os
import httpx
import structlog
from typing import Dict, Any

logger = structlog.get_logger()


class TemporalCloudProvisioningService:
    """Service for provisioning Temporal Cloud namespaces"""

    def __init__(self):
        # Get the Vercel function URL from environment
        self.proxy_url = os.getenv("TEMPORAL_CLOUD_PROXY_URL")
        if not self.proxy_url:
            # If not set, use the Vercel production URL
            self.proxy_url = "https://temporal-cloud-proxy.vercel.app/api/provision-namespace"

        # Get the admin token for authorization (will be checked when actually used)
        self.admin_token = os.getenv("TEMPORAL_CLOUD_ADMIN_TOKEN")

    async def provision_namespace_for_organization(
        self,
        organization_id: str,
        organization_name: str,
        region: str = "aws-us-east-1",
        retention_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Provision a Temporal Cloud namespace for an organization.

        Args:
            organization_id: The organization ID
            organization_name: The organization name
            region: The Temporal Cloud region (default: aws-us-east-1)
            retention_days: Number of days to retain workflow history (default: 7)

        Returns:
            Dictionary with:
            - success: Boolean indicating if provisioning succeeded
            - namespace_name: The provisioned namespace name
            - namespace: Dictionary with namespace details
            - already_exists: Boolean indicating if namespace already existed
            - error: Error message if failed
            - timeout: Boolean indicating if operation timed out
        """
        logger.info(
            "provisioning_temporal_namespace",
            organization_id=organization_id,
            organization_name=organization_name,
            region=region,
        )

        # Check if token is available
        if not self.admin_token:
            error_msg = "TEMPORAL_CLOUD_ADMIN_TOKEN environment variable is required but not set"
            logger.error("temporal_cloud_token_missing", organization_id=organization_id)
            return {
                "success": False,
                "error": error_msg,
                "timeout": False,
            }

        try:
            # Prepare the request
            payload = {
                "organization_id": organization_id,
                "organization_name": organization_name,
                "region": region,
                "retention_days": retention_days,
            }

            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json",
            }

            # Call the Vercel function
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.proxy_url,
                    json=payload,
                    headers=headers,
                )

                # Check response status
                if response.status_code == 200:
                    result = response.json()
                    logger.info(
                        "namespace_provisioned_successfully",
                        organization_id=organization_id,
                        namespace_name=result.get("namespace_name"),
                        already_exists=result.get("already_exists", False),
                    )
                    return result
                else:
                    error_msg = response.text
                    logger.error(
                        "namespace_provisioning_failed",
                        organization_id=organization_id,
                        status_code=response.status_code,
                        error=error_msg,
                    )
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {error_msg}",
                        "timeout": False,
                    }

        except httpx.TimeoutException as e:
            logger.warning(
                "namespace_provisioning_timeout",
                organization_id=organization_id,
                error=str(e),
            )
            return {
                "success": False,
                "error": "Provisioning timed out",
                "timeout": True,
            }
        except Exception as e:
            logger.error(
                "namespace_provisioning_exception",
                organization_id=organization_id,
                error=str(e),
            )
            return {
                "success": False,
                "error": str(e),
                "timeout": False,
            }


# Global instance
_provisioning_service = None


def get_provisioning_service() -> TemporalCloudProvisioningService:
    """Get the provisioning service singleton"""
    global _provisioning_service
    if _provisioning_service is None:
        _provisioning_service = TemporalCloudProvisioningService()
    return _provisioning_service
