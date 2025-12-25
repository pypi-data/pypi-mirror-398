"""Authentication validation endpoints for delegated auth from other services."""

from fastapi import APIRouter, Depends
from typing import Dict
import structlog

from control_plane_api.app.middleware.auth import get_current_organization

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.get("/validate")
async def validate_token(
    organization: dict = Depends(get_current_organization)
) -> Dict:
    """
    Validate authentication token and return organization data.

    This endpoint allows other services (like context-graph-api) to validate
    tokens without duplicating auth logic. The control plane handles all
    validation, caching, and Kubiya API integration.

    The token should be passed in the Authorization header:
    - Bearer <token> for user JWT tokens
    - UserKey <token> for worker/API key tokens

    Returns:
        Organization dict with user and org information:
        {
            "id": "org-slug",
            "name": "Organization Name",
            "slug": "org-slug",
            "user_id": "user-uuid",
            "user_email": "user@example.com",
            "user_name": "User Name",
            "user_avatar": "...",
            "user_status": "...",
            "user_groups": [...]
        }

    Raises:
        401: Invalid or expired token
        500: Internal server error

    Example:
        ```bash
        curl -H "Authorization: Bearer <token>" \\
          https://control-plane.kubiya.ai/api/v1/auth/validate
        ```
    """
    logger.info(
        "auth_validation_delegated",
        org_slug=organization["slug"],
        user_id=organization.get("user_id"),
    )

    return organization
