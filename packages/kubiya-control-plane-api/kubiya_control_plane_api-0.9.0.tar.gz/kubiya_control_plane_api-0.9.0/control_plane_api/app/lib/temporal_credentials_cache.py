"""Temporal credentials caching service.

This module provides caching functionality for organization-specific Temporal
credentials fetched from the Kubiya API. Credentials are cached in Redis with
TTL calculated from the credentials expiry time.
"""

import json
from datetime import datetime
from typing import Optional, Dict
import structlog

from control_plane_api.app.lib.redis_client import get_redis_client

logger = structlog.get_logger()


def get_credentials_cache_key(org_id: str) -> str:
    """
    Generate cache key for organization's Temporal credentials.

    Args:
        org_id: Organization ID (slug or UUID)

    Returns:
        Cache key in format: temporal:credentials:{org_id}
    """
    return f"temporal:credentials:{org_id}"


async def get_cached_temporal_credentials(org_id: str) -> Optional[Dict]:
    """
    Get cached Temporal credentials for organization.

    Args:
        org_id: Organization ID

    Returns:
        Cached credentials dict or None if not found

    Example:
        {
            "apiKey": "...",
            "namespace": "org-slug.lpagu",
            "org": "org-slug",
            "ttl": "2026-01-07T14:38:20Z"
        }
    """
    redis = get_redis_client()
    if not redis:
        return None

    try:
        cache_key = get_credentials_cache_key(org_id)
        cached_data = await redis.get(cache_key)

        if cached_data:
            logger.debug("temporal_credentials_cache_hit", org_id=org_id)
            if isinstance(cached_data, bytes):
                cached_data = cached_data.decode('utf-8')
            return json.loads(cached_data)

        logger.debug("temporal_credentials_cache_miss", org_id=org_id)
        return None

    except Exception as e:
        logger.warning(
            "temporal_credentials_cache_read_failed",
            error=str(e),
            org_id=org_id
        )
        return None


async def cache_temporal_credentials(org_id: str, credentials: Dict) -> None:
    """
    Cache Temporal credentials for organization with TTL.

    The TTL is calculated from the credentials.ttl field if present,
    otherwise defaults to 1 hour. TTL is clamped between 60 seconds
    and 7 days.

    Args:
        org_id: Organization ID
        credentials: Credentials dict with optional 'ttl' field

    Example:
        await cache_temporal_credentials(
            "kubiya-ai",
            {
                "apiKey": "...",
                "namespace": "kubiya-ai.lpagu",
                "org": "kubiya-ai",
                "ttl": "2026-01-07T14:38:20Z"
            }
        )
    """
    redis = get_redis_client()
    if not redis:
        return

    try:
        cache_key = get_credentials_cache_key(org_id)

        # Calculate TTL from credentials.ttl field
        ttl_str = credentials.get("ttl")
        if ttl_str:
            try:
                # Parse ISO 8601 timestamp
                ttl_datetime = datetime.fromisoformat(ttl_str.replace('Z', '+00:00'))
                now = datetime.now(ttl_datetime.tzinfo)
                ttl_seconds = int((ttl_datetime - now).total_seconds())

                # Ensure reasonable TTL (min 60s, max 7 days)
                ttl_seconds = max(60, min(ttl_seconds, 7 * 24 * 3600))

                logger.debug(
                    "ttl_calculated_from_expiry",
                    org_id=org_id,
                    ttl_seconds=ttl_seconds,
                    expires_at=ttl_str
                )
            except Exception as e:
                logger.warning(
                    "ttl_parse_failed_using_default",
                    error=str(e),
                    ttl_str=ttl_str
                )
                ttl_seconds = 3600  # Default 1 hour
        else:
            ttl_seconds = 3600  # Default 1 hour

        # Store credentials as JSON
        await redis.set(
            cache_key,
            json.dumps(credentials),
            ex=ttl_seconds
        )

        logger.info(
            "temporal_credentials_cached",
            org_id=org_id,
            ttl_seconds=ttl_seconds,
            namespace=credentials.get("namespace")
        )

    except Exception as e:
        logger.warning(
            "temporal_credentials_cache_write_failed",
            error=str(e),
            org_id=org_id
        )


async def invalidate_temporal_credentials_cache(org_id: str) -> None:
    """
    Invalidate cached Temporal credentials for organization.

    This is useful for forcing a credential refresh, for example
    when credentials are rotated or revoked.

    Args:
        org_id: Organization ID
    """
    redis = get_redis_client()
    if not redis:
        return

    try:
        cache_key = get_credentials_cache_key(org_id)
        await redis.delete(cache_key)
        logger.info("temporal_credentials_cache_invalidated", org_id=org_id)
    except Exception as e:
        logger.warning(
            "temporal_credentials_cache_invalidation_failed",
            error=str(e),
            org_id=org_id
        )
