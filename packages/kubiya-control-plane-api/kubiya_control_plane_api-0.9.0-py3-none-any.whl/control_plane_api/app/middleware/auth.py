"""Authentication middleware for multi-tenant API with Kubiya integration"""

import os
import json
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
import httpx
import structlog

from control_plane_api.app.lib.redis_client import get_redis_client
from control_plane_api.app.database import get_session_local
from sqlalchemy.orm import Session
from control_plane_api.app.models.worker import WorkerHeartbeat

logger = structlog.get_logger()

security = HTTPBearer(auto_error=False)

# Cache TTL settings
DEFAULT_CACHE_TTL = 3600  # 1 hour default
MAX_CACHE_TTL = 86400  # 24 hours max

# Shared httpx client for auth validation (reuse connections)
_auth_http_client: Optional[httpx.AsyncClient] = None

def get_auth_http_client() -> httpx.AsyncClient:
    """Get or create shared httpx client for auth validation"""
    global _auth_http_client
    if _auth_http_client is None:
        _auth_http_client = httpx.AsyncClient(
            timeout=3.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
    return _auth_http_client


def get_token_cache_key(token: str) -> str:
    """
    Generate a unique cache key for a token using SHA256 hash.

    This ensures each unique token gets its own cache entry, preventing
    collisions and ensuring proper isolation between different tokens/orgs.

    Args:
        token: Authentication token

    Returns:
        Cache key in format: auth:token:sha256:{hash}
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return f"auth:token:sha256:{token_hash}"


async def extract_token_from_headers(request: Request) -> Optional[str]:
    """
    Extract authentication token from request headers.

    Supports multiple header formats for compatibility:
    - Authorization: Bearer <token>
    - Authorization: UserKey <token>
    - Authorization: Baerer <token> (typo compatibility)
    - Authorization: <token> (raw token)
    - UserKey: <token>

    Args:
        request: FastAPI request object

    Returns:
        Extracted token or None
    """
    # Check Authorization header
    auth_header = request.headers.get("authorization")
    if auth_header:
        # Handle "Bearer <token>"
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        # Handle "UserKey <token>"
        elif auth_header.startswith("UserKey "):
            return auth_header[8:]
        # Handle "Baerer <token>" (common typo)
        elif auth_header.startswith("Baerer "):
            logger.warning("api_key_typo_detected", message="'Baerer' should be 'Bearer'")
            return auth_header[7:]
        # Handle raw token without prefix
        elif " " not in auth_header:
            return auth_header

    # Check UserKey header (alternative)
    userkey_header = request.headers.get("userkey")
    if userkey_header:
        return userkey_header

    return None


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token without verification to extract expiry and metadata.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None
    """
    try:
        # Decode without verification (we just need exp and other metadata)
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        logger.warning("jwt_decode_failed", error=str(e))
        return None


def get_cache_ttl_from_token(token: str) -> int:
    """
    Extract expiry from JWT token and calculate appropriate cache TTL.

    Args:
        token: JWT token string

    Returns:
        TTL in seconds (minimum 60s, maximum MAX_CACHE_TTL)
    """
    decoded = decode_jwt_token(token)
    if not decoded or "exp" not in decoded:
        return DEFAULT_CACHE_TTL

    try:
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.now()

        # Calculate time until expiry
        ttl = int((exp_datetime - now).total_seconds())

        # Ensure TTL is reasonable (at least 60s, max MAX_CACHE_TTL)
        ttl = max(60, min(ttl, MAX_CACHE_TTL))

        logger.debug("calculated_cache_ttl", ttl=ttl, exp=exp_timestamp)
        return ttl
    except Exception as e:
        logger.warning("ttl_calculation_failed", error=str(e))
        return DEFAULT_CACHE_TTL


async def validate_kubiya_api_key(auth_header: str, use_userkey: bool = False) -> Optional[Dict[str, Any]]:
    """
    Validate API key with Kubiya API by calling /api/v1/users/self or /api/v1/users/current.

    Args:
        auth_header: Full Authorization header value (e.g., "Bearer xyz123" or "UserKey xyz123")
        use_userkey: If True, use "UserKey" prefix instead of "Bearer" for worker authentication

    Returns:
        User object from Kubiya API or None if invalid
    """
    base_url = os.getenv("KUBIYA_API_BASE") or os.getenv("KUBIYA_API_URL") or "https://api.kubiya.ai"
    endpoints = ["/api/v1/users/self", "/api/v1/users/current"]

    # If use_userkey is True, ensure the header uses "UserKey" prefix
    if use_userkey and not auth_header.startswith("UserKey "):
        # Extract token and reformat with UserKey prefix
        token = auth_header.replace("Bearer ", "").replace("UserKey ", "").strip()
        auth_header = f"UserKey {token}"
        logger.debug("reformatted_auth_header_for_worker", prefix="UserKey")

    client = get_auth_http_client()
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            logger.debug("validating_token_with_kubiya", url=url, use_userkey=use_userkey)

            response = await client.get(
                url,
                headers={"Authorization": auth_header}
            )

            if response.status_code == 200:
                user_data = response.json()
                logger.info(
                    "token_validated_with_kubiya",
                    endpoint=endpoint,
                    user_id=user_data.get("id"),
                    org_id=user_data.get("organization_id"),
                    use_userkey=use_userkey
                )
                return user_data

            logger.debug(
                "kubiya_validation_attempt_failed",
                endpoint=endpoint,
                status=response.status_code,
                use_userkey=use_userkey
            )

        except Exception as e:
            logger.warning("kubiya_validation_error", endpoint=endpoint, error=str(e))
            continue

    logger.warning("token_validation_failed_all_endpoints", use_userkey=use_userkey)
    return None


async def get_cached_user_data(token: str) -> Optional[Dict[str, Any]]:
    """
    Get cached user data from Redis using SHA256 hash of token.

    Args:
        token: Authentication token (full token will be hashed)

    Returns:
        Cached user data or None
    """
    redis = get_redis_client()
    if not redis:
        return None

    try:
        cache_key = get_token_cache_key(token)
        cached_data = await redis.get(cache_key)

        if cached_data:
            logger.debug("cache_hit", cache_key=cache_key[:40] + "...")
            if isinstance(cached_data, bytes):
                cached_data = cached_data.decode('utf-8')
            return json.loads(cached_data)

        logger.debug("cache_miss", cache_key=cache_key[:40] + "...")
        return None

    except Exception as e:
        logger.warning("cache_read_failed", error=str(e))
        return None


async def cache_user_data(token: str, user_data: Dict[str, Any]) -> None:
    """
    Cache user data in Redis with TTL based on token expiry.
    Uses SHA256 hash of the full token as cache key for uniqueness.

    Args:
        token: Authentication token (full token will be hashed)
        user_data: User data to cache
    """
    redis = get_redis_client()
    if not redis:
        return

    try:
        cache_key = get_token_cache_key(token)
        ttl = get_cache_ttl_from_token(token)

        await redis.set(
            cache_key,
            json.dumps(user_data),
            ex=ttl  # Set expiry in seconds
        )

        logger.info("cache_write_success", cache_key=cache_key[:40] + "...", ttl=ttl)

    except Exception as e:
        logger.warning("cache_write_failed", error=str(e))


async def get_organization_from_worker_token(token: str) -> Optional[dict]:
    """
    Validate worker token and return organization data.

    Worker tokens are in format: worker_{uuid} and stored in worker_heartbeats.worker_metadata

    Args:
        token: Worker authentication token

    Returns:
        Organization dict or None if invalid
    """
    if not token.startswith("worker_"):
        return None

    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # Query worker_heartbeats for active workers
        workers = db.query(WorkerHeartbeat).filter(
            WorkerHeartbeat.status == "active"
        ).all()

        # Find worker with matching token in metadata
        for worker in workers:
            worker_metadata = worker.worker_metadata or {}
            if worker_metadata.get("worker_token") == token:
                # Return minimal org data for worker
                return {
                    "id": worker.organization_id,
                    "name": "Worker",  # Workers don't need full org details
                    "slug": "worker",
                    "user_id": "worker",
                    "user_email": "worker@system",
                    "user_name": "Worker Process"
                }

        logger.warning("worker_token_not_found", token_prefix=token[:15])
        return None

    except Exception as e:
        logger.error("worker_token_validation_failed", error=str(e))
        return None
    finally:
        db.close()


async def get_organization_allow_worker(request: Request) -> dict:
    """
    Dependency that accepts both user tokens and worker tokens.

    This is used by endpoints that workers need to call (like execution updates).

    Flow:
    1. Extract token from Authorization header
    2. If token starts with "worker_", validate as worker token
    3. Otherwise, validate as user token (with caching)
    4. Return organization data

    Args:
        request: FastAPI request object

    Returns:
        Organization dict with id, name, slug, user_id, etc.

    Raises:
        HTTPException: 401 if authentication fails
    """
    # Extract token from headers
    token = await extract_token_from_headers(request)

    if not token:
        logger.warning("auth_token_missing", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "Authorization header is required",
                "hint": "Include 'Authorization: Bearer <token>' header"
            }
        )

    # Check if this is a worker token (fast path)
    if token.startswith("worker_"):
        logger.debug("validating_worker_token", path=request.url.path)
        org = await get_organization_from_worker_token(token)
        if org:
            # Store in request state for later use
            request.state.organization = org
            request.state.worker_token = token
            logger.info(
                "worker_authenticated",
                org_id=org["id"],
                path=request.url.path,
                method=request.method,
            )
            return org

        # Worker token invalid
        logger.warning("worker_token_invalid", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "Invalid or expired worker token",
                "hint": "Worker token not found in active workers"
            }
        )

    # Fall back to regular user authentication
    return await get_current_organization(request)


async def get_current_organization(request: Request) -> dict:
    """
    Dependency to get current organization and validate authentication.

    Flow:
    1. Extract token from Authorization header
    2. Check Redis cache for user data
    3. If not cached, validate with Kubiya API
    4. Cache the user data with TTL based on JWT expiry
    5. Return organization data

    Args:
        request: FastAPI request object

    Returns:
        Organization dict:
        {
            "id": "org-uuid",
            "name": "Organization Name",
            "slug": "org-slug",
            "user_id": "user-uuid",
            "user_email": "user@example.com",
            "user_name": "User Name"
        }

    Raises:
        HTTPException: 401 if authentication fails
    """
    # Extract token from headers
    token = await extract_token_from_headers(request)

    if not token:
        logger.warning("auth_token_missing", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "Authorization header is required",
                "hint": "Include 'Authorization: Bearer <token>' header"
            }
        )

    # Try to get cached user data
    user_data = await get_cached_user_data(token)

    # Track which auth type succeeded
    auth_type = None

    # If not cached, validate with Kubiya API
    if not user_data:
        logger.debug("validating_with_kubiya_api", path=request.url.path)
        auth_header = f"Bearer {token}" if not token.startswith("Bearer ") else token

        # Try Bearer first (for regular user tokens)
        user_data = await validate_kubiya_api_key(auth_header, use_userkey=False)
        if user_data:
            auth_type = "Bearer"

        # If Bearer fails, try UserKey (for API keys/worker tokens)
        if not user_data:
            logger.debug("bearer_auth_failed_trying_userkey", path=request.url.path)
            user_data = await validate_kubiya_api_key(auth_header, use_userkey=True)
            if user_data:
                auth_type = "UserKey"

        if not user_data:
            logger.warning("authentication_failed", path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Unauthorized",
                    "message": "Invalid or expired authentication token",
                    "hint": "Ensure you're using a valid Kubiya API token"
                }
            )

        # Cache the validated user data with auth type
        await cache_user_data(token, {**user_data, "_auth_type": auth_type})
    else:
        # Retrieve auth type from cache
        auth_type = user_data.get("_auth_type", "Bearer")

    # Extract organization slug from Kubiya API response
    # Kubiya API returns the org slug in the "org" field (e.g., "kubiya-ai")
    # We use this slug as the primary organization identifier throughout the system
    org_slug = user_data.get("org")

    if not org_slug:
        logger.error("org_slug_missing_in_user_data", user_data=user_data)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "No organization slug found in user data",
                "hint": "User data must contain 'org' field from Kubiya API"
            }
        )

    # Build organization object
    # We use the org slug as the primary identifier (id field)
    # This slug is used for all database operations (agents, teams, executions, etc.)
    user_email = user_data.get("email")
    user_name = user_data.get("name") or (user_email.split("@")[0] if user_email else None)  # Fallback to email username

    organization = {
        "id": org_slug,  # Use slug as ID (e.g., "kubiya-ai")
        "name": user_data.get("org"),  # Also use slug as display name
        "slug": org_slug,  # The slug itself
        "user_id": user_data.get("uuid"),  # User UUID from Kubiya
        "user_email": user_email,
        "user_name": user_name,
        "user_avatar": user_data.get("picture") or user_data.get("avatar") or user_data.get("image"),  # Avatar from Auth0/Kubiya
        "user_status": user_data.get("user_status") or user_data.get("status"),
        "user_groups": user_data.get("groups") or user_data.get("user_groups"),
    }

    # Store in request state for later use
    request.state.organization = organization
    request.state.kubiya_token = token
    request.state.kubiya_auth_type = auth_type  # Store whether to use Bearer or UserKey
    request.state.user_data = user_data

    logger.info(
        "request_authenticated",
        org_id=organization["id"],
        user_id=organization.get("user_id"),
        path=request.url.path,
        method=request.method,
        cached=user_data is not None
    )

    return organization
