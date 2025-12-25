"""Kubiya API client for authentication and runner management"""

import httpx
import os
from typing import Optional, Dict, List
import structlog

logger = structlog.get_logger()

KUBIYA_API_BASE = os.environ.get("KUBIYA_API_BASE", "https://api.kubiya.ai")


class KubiyaClient:
    """Client for Kubiya API"""

    def __init__(self, api_base: str = KUBIYA_API_BASE):
        self.api_base = api_base.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def validate_token_and_get_org(self, token: str) -> Optional[Dict]:
        """
        Validate token with Kubiya API and get organization details.
        Automatically tries both Bearer (Auth0 idToken) and UserKey (API key) authentication.

        Args:
            token: Authentication token (Bearer/idToken or UserKey/API key)

        Returns:
            Dict with organization details:
            {
                "id": "org-uuid",
                "name": "Organization Name",
                "slug": "org-slug"
            }
            None if invalid token
        """
        try:
            # Try Bearer authentication first (Auth0 idToken)
            response = await self.client.get(
                f"{self.api_base}/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )

            # If Bearer fails with 401, try UserKey (API key)
            if response.status_code == 401:
                logger.debug("kubiya_bearer_auth_failed_trying_userkey")
                response = await self.client.get(
                    f"{self.api_base}/api/v1/users/me",
                    headers={"Authorization": f"UserKey {token}"},
                )

            if response.status_code == 200:
                data = response.json()

                # Log full response for debugging
                logger.info(
                    "kubiya_api_response",
                    response_keys=list(data.keys()),
                    has_org=bool(data.get("org")),
                    has_org_id=bool(data.get("org_id")),
                )

                # Extract organization from response
                # Kubiya API returns org/org_id at root level, not nested
                org_id = data.get("org") or data.get("org_id") or data.get("organization", {}).get("uuid")
                org_name = data.get("org_name") or data.get("organization_name") or data.get("organization", {}).get("name")
                org_slug = data.get("org_slug") or data.get("organization_slug") or data.get("organization", {}).get("slug")

                org_data = {
                    "id": org_id,
                    "name": org_name,
                    "slug": org_slug,
                    "user_id": data.get("uuid") or data.get("id"),
                    "user_email": data.get("email"),
                    "user_name": data.get("name"),
                }

                logger.info(
                    "kubiya_token_validated",
                    org_id=org_data["id"],
                    org_name=org_data["name"],
                    user_email=org_data.get("user_email"),
                )

                return org_data

            else:
                logger.warning(
                    "kubiya_token_invalid",
                    status_code=response.status_code,
                )
                return None

        except Exception as e:
            logger.error("kubiya_api_error", error=str(e))
            return None

    async def get_runners(self, token: str, org_id: str) -> List[Dict]:
        """
        Get available runners for organization from Kubiya API.
        Automatically tries both Bearer and UserKey authentication methods.

        Args:
            token: Authentication token (Bearer/idToken or UserKey/API key)
            org_id: Organization UUID

        Returns:
            List of runner dicts:
            [
                {
                    "name": "runner-name",
                    "wss_url": "...",
                    "task_id": "...",
                    ...
                }
            ]
        """
        try:
            # Try Bearer authentication first (Auth0 idToken)
            response = await self.client.get(
                f"{self.api_base}/api/v3/runners",
                headers={"Authorization": f"Bearer {token}"},
            )

            # If Bearer fails with 401, try UserKey (API key)
            if response.status_code == 401:
                logger.info(
                    "kubiya_runners_bearer_failed_trying_userkey",
                    org_id=org_id,
                )
                response = await self.client.get(
                    f"{self.api_base}/api/v3/runners",
                    headers={"Authorization": f"UserKey {token}"},
                )

            if response.status_code == 200:
                runners = response.json()

                # Handle both array response and object response
                if isinstance(runners, dict):
                    # If it's a dict, extract the array from common keys
                    runners = runners.get('runners', runners.get('data', []))

                # Ensure it's a list
                if not isinstance(runners, list):
                    logger.warning(
                        "kubiya_runners_unexpected_format",
                        type=type(runners).__name__,
                    )
                    runners = []

                logger.info(
                    "kubiya_runners_fetched",
                    org_id=org_id,
                    runner_count=len(runners),
                )

                return runners

            else:
                logger.warning(
                    "kubiya_runners_fetch_failed",
                    status_code=response.status_code,
                )
                return []

        except Exception as e:
            logger.error("kubiya_runners_error", error=str(e))
            return []

    async def get_temporal_credentials(self, token: str) -> Optional[Dict]:
        """
        Fetch organization-specific Temporal credentials from Kubiya API.
        Automatically tries both Bearer (Auth0 idToken) and UserKey (API key) authentication.

        Args:
            token: Authentication token (Bearer/idToken or UserKey/API key)

        Returns:
            Dict with Temporal credentials:
            {
                "apiKey": "...",
                "apiKeyId": "...",
                "namespace": "kubiya-ai.lpagu",
                "org": "kubiya-ai",
                "ttl": "2026-01-07T14:38:20Z",
                "created_at": "...",
                "updated_at": "..."
            }
            None if request fails
        """
        try:
            # Try Bearer authentication first (Auth0 idToken)
            response = await self.client.get(
                f"{self.api_base}/api/v1/org/temporal",
                headers={"Authorization": f"Bearer {token}"},
            )

            # If Bearer fails with 401, try UserKey (API key)
            if response.status_code == 401:
                logger.debug("kubiya_temporal_bearer_auth_failed_trying_userkey")
                response = await self.client.get(
                    f"{self.api_base}/api/v1/org/temporal",
                    headers={"Authorization": f"UserKey {token}"},
                )

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    "kubiya_temporal_credentials_fetched",
                    namespace=data.get("namespace"),
                    org=data.get("org"),
                    ttl=data.get("ttl"),
                    has_api_key=bool(data.get("apiKey")),
                )
                return data
            else:
                logger.warning(
                    "kubiya_temporal_credentials_fetch_failed",
                    status_code=response.status_code,
                    response_text=response.text[:200] if hasattr(response, 'text') else None,
                )
                return None

        except Exception as e:
            logger.error("kubiya_temporal_credentials_error", error=str(e))
            return None

    async def register_runner_heartbeat(
        self, token: str, org_id: str, runner_name: str, metadata: Dict = None
    ) -> bool:
        """
        Register runner heartbeat with Kubiya API.

        Called by workers to report they're alive and polling.

        Args:
            token: Service token for worker
            org_id: Organization UUID
            runner_name: Runner name
            metadata: Additional metadata (capabilities, version, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.client.post(
                f"{self.api_base}/api/v1/runners/heartbeat",
                headers={"Authorization": f"UserKey {token}"},
                json={
                    "organization_id": org_id,
                    "runner_name": runner_name,
                    "status": "active",
                    "metadata": metadata or {},
                    "task_queue": f"{org_id}.{runner_name}",
                },
            )

            if response.status_code in [200, 201, 204]:
                logger.info(
                    "kubiya_heartbeat_sent",
                    org_id=org_id,
                    runner_name=runner_name,
                )
                return True
            else:
                logger.warning(
                    "kubiya_heartbeat_failed",
                    status_code=response.status_code,
                )
                return False

        except Exception as e:
            logger.error("kubiya_heartbeat_error", error=str(e))
            return False

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Singleton instance
_kubiya_client: Optional[KubiyaClient] = None


def get_kubiya_client() -> KubiyaClient:
    """Get or create Kubiya client singleton"""
    global _kubiya_client

    if _kubiya_client is None:
        _kubiya_client = KubiyaClient()

    return _kubiya_client
