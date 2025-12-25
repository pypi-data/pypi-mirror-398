"""Supabase client for Agent Control Plane"""

import os
from typing import Optional
from supabase import create_client, Client
import structlog

logger = structlog.get_logger()

_supabase_client: Optional[Client] = None


def get_supabase() -> Client:
    """
    Get or create Supabase client singleton.

    Uses service role key for admin operations with RLS bypass.
    The API will set organization context via middleware.

    Returns:
        Supabase client instance
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    supabase_url = os.environ.get("SUPABASE_URL") or os.environ.get("SUPABASE_SUPABASE_URL")
    # Try multiple env var names for service key (Vercel Supabase integration uses different names)
    supabase_key = (
        os.environ.get("SUPABASE_SERVICE_KEY") or
        os.environ.get("SUPABASE_SUPABASE_SERVICE_ROLE_KEY") or
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    )

    if not supabase_url or not supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables are required. "
            f"Found URL: {bool(supabase_url)}, Key: {bool(supabase_key)}"
        )

    _supabase_client = create_client(supabase_url, supabase_key)

    logger.info("supabase_client_initialized", url=supabase_url)

    return _supabase_client


def execute_with_org_context(org_id: str, query_func):
    """
    Execute a Supabase query with organization context for RLS.

    Sets the app.current_org_id config parameter that RLS policies use.

    Args:
        org_id: Organization UUID
        query_func: Function that performs the database operation

    Returns:
        Query result
    """
    client = get_supabase()

    # Set organization context for RLS
    # This uses the PostgreSQL set_config function via RPC
    client.rpc("set_organization_context", {"org_id": org_id}).execute()

    # Execute the query
    result = query_func()

    return result
