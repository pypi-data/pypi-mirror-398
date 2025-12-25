"""Temporal credentials service with caching and fallback.

This service orchestrates fetching organization-specific Temporal credentials
from the Kubiya API, with Redis caching and fallback to environment variables.
"""

import os
from typing import Optional, Dict
import structlog

from control_plane_api.app.lib.kubiya_client import get_kubiya_client
from control_plane_api.app.lib.temporal_credentials_cache import (
    get_cached_temporal_credentials,
    cache_temporal_credentials,
)

logger = structlog.get_logger()


def is_local_temporal() -> bool:
    """
    Check if running against local Temporal server.

    Detects local Temporal by checking if TEMPORAL_HOST contains
    localhost, 127.0.0.1, or temporal: (Docker Compose service name).

    Returns:
        True if local Temporal, False if Temporal Cloud
    """
    temporal_host = os.getenv("TEMPORAL_HOST", "us-east-1.aws.api.temporal.io:7233")
    return (
        "localhost" in temporal_host or
        "127.0.0.1" in temporal_host or
        temporal_host.startswith("temporal:")
    )


async def get_temporal_credentials_for_org(
    org_id: str,
    token: str,
    use_fallback: bool = True
) -> Dict:
    """
    Get Temporal credentials for organization with caching and fallback.

    This is the main entry point for fetching Temporal credentials.

    Flow:
    1. Check if local Temporal (auto-detect from TEMPORAL_HOST)
       - If local: Return env var credentials immediately
    2. Check Redis cache
    3. If not cached, call Kubiya API
    4. Cache the result
    5. On failure, optionally fallback to env vars (backwards compatibility)

    Args:
        org_id: Organization ID (slug or UUID)
        token: Authentication token
        use_fallback: If True, fallback to env vars on API failure (default: True)

    Returns:
        Dict with keys:
        {
            "namespace": "org-slug.lpagu",
            "api_key": "...",
            "host": "us-east-1.aws.api.temporal.io:7233",
            "org": "org-slug",
            "ttl": "2026-01-07T14:38:20Z"
        }

    Raises:
        ValueError: If credentials cannot be obtained and fallback is disabled

    Example:
        credentials = await get_temporal_credentials_for_org(
            org_id="kubiya-ai",
            token=request.state.kubiya_token,
            use_fallback=True
        )
    """
    # Check if running against local Temporal
    if is_local_temporal():
        logger.debug("using_local_temporal_credentials", org_id=org_id)
        return _get_local_temporal_credentials()

    # PRIORITY: Check if explicit Temporal credentials are set in environment variables
    # This allows overriding Kubiya API with admin credentials
    if os.getenv("TEMPORAL_API_KEY") or os.getenv("TEMPORAL_NAMESPACE"):
        logger.info(
            "using_explicit_env_temporal_credentials",
            org_id=org_id,
            namespace=os.getenv("TEMPORAL_NAMESPACE", "not_set"),
            has_api_key=bool(os.getenv("TEMPORAL_API_KEY"))
        )
        return _get_fallback_credentials()

    # Check cache first
    cached_creds = await get_cached_temporal_credentials(org_id)
    if cached_creds:
        logger.debug("using_cached_temporal_credentials", org_id=org_id)
        return _normalize_credentials(cached_creds)

    # Fetch from Kubiya API
    kubiya_client = get_kubiya_client()
    api_creds = await kubiya_client.get_temporal_credentials(token)

    if api_creds:
        # Cache the credentials
        await cache_temporal_credentials(org_id, api_creds)

        logger.info(
            "temporal_credentials_fetched_from_api",
            org_id=org_id,
            namespace=api_creds.get("namespace"),
            source="kubiya_api"
        )

        return _normalize_credentials(api_creds)

    # API fetch failed
    if use_fallback:
        logger.warning(
            "temporal_credentials_api_failed_using_fallback",
            org_id=org_id,
            fallback_enabled=use_fallback
        )
        return _get_fallback_credentials()
    else:
        raise ValueError(
            f"Failed to fetch Temporal credentials for org {org_id} "
            "and fallback is disabled"
        )


def _normalize_credentials(api_response: Dict) -> Dict:
    """
    Normalize API response to standard format.

    Converts the Kubiya API response format to the internal format
    used by the control plane.

    Args:
        api_response: Response from Kubiya API with keys like 'apiKey', 'namespace'

    Returns:
        Normalized credentials dict with keys like 'api_key', 'namespace'
    """
    # Get host from env or use default
    host = os.getenv("TEMPORAL_HOST", "us-east-1.aws.api.temporal.io:7233")

    return {
        "namespace": api_response.get("namespace"),
        "api_key": api_response.get("apiKey"),
        "host": host,
        "org": api_response.get("org"),
        "ttl": api_response.get("ttl"),
    }


def _get_local_temporal_credentials() -> Dict:
    """
    Get local Temporal credentials from environment variables.

    Used when running against a local Temporal server (development).

    Returns:
        Credentials dict with env var values
    """
    logger.info("using_local_temporal_credentials", source="env_vars")

    return {
        "namespace": os.getenv("TEMPORAL_NAMESPACE", "default").strip(),
        "api_key": "",  # No API key for local Temporal
        "host": os.getenv("TEMPORAL_HOST", "localhost:7233").strip(),
        "org": "local",
        "ttl": None,
    }


def _get_fallback_credentials() -> Dict:
    """
    Get fallback credentials from environment variables.

    Used for backwards compatibility during migration when the
    Kubiya API is unavailable.

    Returns:
        Credentials dict with env var values
    """
    logger.warning("using_fallback_temporal_credentials", source="env_vars")

    # Strip whitespace/newlines from env vars to handle malformed .env files
    namespace = os.getenv("TEMPORAL_NAMESPACE", "agent-control-plane.lpagu").strip()
    api_key = (os.getenv("TEMPORAL_API_KEY") or os.getenv("TEMPORAL_CLOUD_ADMIN_TOKEN", "")).strip()
    host = os.getenv("TEMPORAL_HOST", "us-east-1.aws.api.temporal.io:7233").strip()

    return {
        "namespace": namespace,
        "api_key": api_key,
        "host": host,
        "org": "fallback",
        "ttl": None,
    }
