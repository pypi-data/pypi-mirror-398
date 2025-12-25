"""
Policies Router - API endpoints for policy management and enforcement.

This router provides:
- Policy CRUD operations (proxy to enforcer service)
- Policy association management (linking policies to entities)
- Policy inheritance resolution
- Policy evaluation and authorization checks
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import structlog
from sqlalchemy.orm import Session

from control_plane_api.app.database import get_db
from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.lib.policy_enforcer_client import (
    create_policy_enforcer_client,
    PolicyEnforcerClient,
    PolicyCreate,
    PolicyUpdate,
    Policy,
    PolicyValidationError,
    PolicyNotFoundError,
    EnforcerConnectionError,
)
from control_plane_api.app.services.policy_service import (
    PolicyService,
    PolicyAssociationCreate,
    PolicyAssociationUpdate,
    PolicyAssociationResponse,
    ResolvedPolicy,
    EntityType,
)

logger = structlog.get_logger()

router = APIRouter()


# ============================================================================
# Dependency Injection
# ============================================================================

async def get_policy_service(
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> PolicyService:
    """
    Dependency to get PolicyService with enforcer client.

    Note: If ENFORCER_SERVICE_URL is not set, returns service with disabled enforcer.
    The enforcer client uses the same authorization token from the incoming request.
    """
    # Extract the authorization token and auth type from the request state (set by auth middleware)
    auth_token = getattr(request.state, "kubiya_token", None)
    auth_type = getattr(request.state, "kubiya_auth_type", "UserKey")

    async with create_policy_enforcer_client(api_key=auth_token, auth_type=auth_type) as enforcer_client:
        service = PolicyService(
            organization_id=organization["id"],
            enforcer_client=enforcer_client,
            db=db
        )
        yield service


# ============================================================================
# Request/Response Models
# ============================================================================

class PolicyResponse(BaseModel):
    """Extended policy response with association count"""
    id: str
    name: str
    description: Optional[str]
    policy_content: Optional[str] = ""  # May be None or empty in some responses
    organization_id: str
    enabled: bool
    tags: List[str]
    version: int
    created_at: Optional[str]
    updated_at: Optional[str]
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    policy_type: str = "rego"
    association_count: int = 0  # Number of entities using this policy


class EvaluationRequest(BaseModel):
    """Request model for policy evaluation"""
    input_data: Dict[str, Any] = Field(..., description="Input data for evaluation")
    policy_ids: Optional[List[str]] = Field(None, description="Specific policy IDs to evaluate")


class EvaluationResponse(BaseModel):
    """Response model for policy evaluation"""
    allowed: bool
    violations: List[str]
    policy_results: Dict[str, Dict[str, Any]]  # policy_id -> result


class AuthorizationCheckRequest(BaseModel):
    """Request model for authorization check"""
    action: str = Field(..., description="Action to check")
    resource: Optional[str] = Field(None, description="Resource identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class AuthorizationCheckResponse(BaseModel):
    """Response model for authorization check"""
    authorized: bool
    violations: List[str]
    policies_evaluated: int


class PolicyListResponse(BaseModel):
    """Paginated response for list policies"""
    policies: List[PolicyResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class ValidationResultResponse(BaseModel):
    """Response for policy validation"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


# ============================================================================
# Health Check (Must be before parameterized routes)
# ============================================================================

@router.get("/health")
async def check_policy_enforcer_health(
    service: PolicyService = Depends(get_policy_service),
):
    """
    Check health of the policy enforcer service.

    Returns connection status and configuration information.
    """
    if not service.is_enabled:
        return {
            "enabled": False,
            "healthy": False,
            "message": "Policy enforcer is not configured",
        }

    try:
        healthy = await service.enforcer_client.health_check()
        return {
            "enabled": True,
            "healthy": healthy,
            "enforcer_url": service.enforcer_client._base_url,
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e), error_type=type(e).__name__)
        return {
            "enabled": True,
            "healthy": False,
            "error": str(e),
        }


# ============================================================================
# Policy CRUD Endpoints (Proxy to Enforcer Service)
# ============================================================================

@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy: PolicyCreate,
    service: PolicyService = Depends(get_policy_service),
):
    """
    Create a new OPA policy in the enforcer service.

    The policy will be stored in the enforcer service and can then be
    associated with entities (agents, teams, environments).
    """
    if not service.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Policy enforcer is not configured. Set ENFORCER_SERVICE_URL environment variable.",
        )

    try:
        created_policy = await service.create_policy(policy)
        policy_dict = created_policy.model_dump()
        # Convert datetime objects to ISO strings
        if policy_dict.get("created_at"):
            policy_dict["created_at"] = policy_dict["created_at"].isoformat() if hasattr(policy_dict["created_at"], "isoformat") else str(policy_dict["created_at"])
        if policy_dict.get("updated_at"):
            policy_dict["updated_at"] = policy_dict["updated_at"].isoformat() if hasattr(policy_dict["updated_at"], "isoformat") else str(policy_dict["updated_at"])
        return PolicyResponse(
            **policy_dict,
            organization_id=service.organization_id,
            association_count=0,
        )
    except PolicyValidationError as e:
        error_detail = {
            "error": str(e),
            "code": "VALIDATION_ERROR",
            "errors": getattr(e, 'errors', []),
        }
        # Include details if available
        if hasattr(e, 'details') and e.details:
            error_detail["details"] = e.details

        logger.error(
            "policy_creation_validation_error",
            error=str(e),
            errors=error_detail["errors"],
            details=error_detail.get("details")
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )
    except EnforcerConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": str(e), "code": "SERVICE_UNAVAILABLE"}
        )
    except Exception as e:
        logger.error("create_policy_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "code": "INTERNAL_ERROR"}
        )


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    service: PolicyService = Depends(get_policy_service),
):
    """Get a specific policy by ID"""
    if not service.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Policy enforcer is not configured",
        )

    try:
        policy = await service.get_policy(policy_id)

        # Count associations
        associations = service.list_associations(policy_id=policy_id)

        policy_dict = policy.model_dump()
        # Convert datetime objects to ISO strings
        if policy_dict.get("created_at"):
            policy_dict["created_at"] = policy_dict["created_at"].isoformat() if hasattr(policy_dict["created_at"], "isoformat") else str(policy_dict["created_at"])
        if policy_dict.get("updated_at"):
            policy_dict["updated_at"] = policy_dict["updated_at"].isoformat() if hasattr(policy_dict["updated_at"], "isoformat") else str(policy_dict["updated_at"])

        return PolicyResponse(
            **policy_dict,
            organization_id=service.organization_id,
            association_count=len(associations),
        )
    except PolicyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    except Exception as e:
        logger.error("get_policy_failed", policy_id=policy_id, error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "code": "POLICY_FETCH_ERROR"}
        )


@router.get("", response_model=PolicyListResponse)
async def list_policies(
    page: int = 1,
    limit: int = 20,
    enabled: Optional[bool] = None,
    search: Optional[str] = None,
    service: PolicyService = Depends(get_policy_service),
):
    """
    List all policies from the enforcer service.

    Supports pagination, filtering by enabled status, and search.
    """
    if not service.is_enabled:
        return PolicyListResponse(
            policies=[],
            total=0,
            page=page,
            limit=limit,
            has_more=False,
        )

    policies = await service.list_policies(
        page=page,
        limit=limit,
        enabled=enabled,
        search=search,
    )

    # Enhance with association counts
    responses = []
    for policy in policies:
        associations = service.list_associations(policy_id=policy.id)
        policy_dict = policy.model_dump()
        # Ensure policy_content exists (list endpoint may not return it)
        if not policy_dict.get("policy_content"):
            policy_dict["policy_content"] = ""
        # Convert datetime objects to ISO strings
        if policy_dict.get("created_at"):
            policy_dict["created_at"] = policy_dict["created_at"].isoformat() if hasattr(policy_dict["created_at"], "isoformat") else str(policy_dict["created_at"])
        if policy_dict.get("updated_at"):
            policy_dict["updated_at"] = policy_dict["updated_at"].isoformat() if hasattr(policy_dict["updated_at"], "isoformat") else str(policy_dict["updated_at"])
        responses.append(
            PolicyResponse(
                **policy_dict,
                organization_id=service.organization_id,
                association_count=len(associations),
            )
        )

    # Calculate total and has_more
    # Note: The enforcer service list_policies returns all policies for now
    # We'll implement proper pagination when needed
    total = len(responses)
    has_more = False  # Since we're returning all results for now

    return PolicyListResponse(
        policies=responses,
        total=total,
        page=page,
        limit=limit,
        has_more=has_more,
    )


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    update: PolicyUpdate,
    service: PolicyService = Depends(get_policy_service),
):
    """Update an existing policy"""
    if not service.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Policy enforcer is not configured",
        )

    try:
        updated_policy = await service.update_policy(policy_id, update)

        # Count associations
        associations = service.list_associations(policy_id=policy_id)

        policy_dict = updated_policy.model_dump()
        # Convert datetime objects to ISO strings
        if policy_dict.get("created_at"):
            policy_dict["created_at"] = policy_dict["created_at"].isoformat() if hasattr(policy_dict["created_at"], "isoformat") else str(policy_dict["created_at"])
        if policy_dict.get("updated_at"):
            policy_dict["updated_at"] = policy_dict["updated_at"].isoformat() if hasattr(policy_dict["updated_at"], "isoformat") else str(policy_dict["updated_at"])

        return PolicyResponse(
            **policy_dict,
            organization_id=service.organization_id,
            association_count=len(associations),
        )
    except PolicyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    except PolicyValidationError as e:
        error_detail = {
            "error": str(e),
            "code": "VALIDATION_ERROR",
            "errors": getattr(e, 'errors', []),
        }
        # Include details if available
        if hasattr(e, 'details') and e.details:
            error_detail["details"] = e.details

        logger.error(
            "policy_update_validation_error",
            policy_id=policy_id,
            error=str(e),
            errors=error_detail["errors"],
            details=error_detail.get("details")
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )
    except Exception as e:
        logger.error("update_policy_failed", policy_id=policy_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "code": "INTERNAL_ERROR"}
        )


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: str,
    service: PolicyService = Depends(get_policy_service),
):
    """
    Delete a policy from the enforcer service.

    This will also remove all associations with entities.
    """
    if not service.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Policy enforcer is not configured",
        )

    try:
        await service.delete_policy(policy_id)
    except PolicyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")


@router.post("/{policy_id}/validate", response_model=ValidationResultResponse)
async def validate_policy(
    policy_id: str,
    service: PolicyService = Depends(get_policy_service),
):
    """
    Validate a policy's Rego syntax and structure.

    Returns validation results with errors and warnings.
    """
    if not service.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Policy enforcer is not configured",
        )

    try:
        result = await service.validate_policy(policy_id)
        return {
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
        }
    except PolicyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    except Exception as e:
        logger.error("validate_policy_failed", policy_id=policy_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "code": "INTERNAL_ERROR"}
        )


# ============================================================================
# Policy Association Endpoints
# ============================================================================

@router.post("/associations", response_model=PolicyAssociationResponse, status_code=status.HTTP_201_CREATED)
async def create_policy_association(
    association: PolicyAssociationCreate,
    request: Request,
    service: PolicyService = Depends(get_policy_service),
    organization: dict = Depends(get_current_organization),
):
    """
    Create a policy association (link a policy to an entity).

    Entities can be agents, teams, or environments.
    Priority determines which policy wins in case of conflicts (higher wins).
    """
    if not service.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Policy enforcer is not configured",
        )

    # Extract user email from request if available
    created_by = None
    if hasattr(request.state, "user_email"):
        created_by = request.state.user_email

    try:
        return await service.create_association(association, created_by=created_by)
    except PolicyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {association.policy_id} not found",
        )
    except Exception as e:
        logger.error("create_association_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/associations", response_model=List[PolicyAssociationResponse])
def list_policy_associations(
    entity_type: Optional[EntityType] = None,
    entity_id: Optional[str] = None,
    policy_id: Optional[str] = None,
    enabled: Optional[bool] = None,
    service: PolicyService = Depends(get_policy_service),
):
    """
    List policy associations with filtering.

    Can filter by entity type, entity ID, policy ID, and enabled status.
    """
    return service.list_associations(
        entity_type=entity_type,
        entity_id=entity_id,
        policy_id=policy_id,
        enabled=enabled,
    )


@router.get("/associations/{association_id}", response_model=PolicyAssociationResponse)
def get_policy_association(
    association_id: str,
    service: PolicyService = Depends(get_policy_service),
):
    """Get a specific policy association by ID"""
    association = service.get_association(association_id)
    if not association:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Association not found")
    return association


@router.patch("/associations/{association_id}", response_model=PolicyAssociationResponse)
def update_policy_association(
    association_id: str,
    update: PolicyAssociationUpdate,
    service: PolicyService = Depends(get_policy_service),
):
    """Update a policy association (e.g., enable/disable, change priority)"""
    association = service.update_association(association_id, update)
    if not association:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Association not found")
    return association


@router.delete("/associations/{association_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy_association(
    association_id: str,
    service: PolicyService = Depends(get_policy_service),
):
    """Delete a policy association"""
    if not service.delete_association(association_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Association not found")


# ============================================================================
# Policy Resolution and Evaluation Endpoints
# ============================================================================

@router.get("/resolved/{entity_type}/{entity_id}", response_model=List[ResolvedPolicy])
async def resolve_entity_policies(
    entity_type: EntityType,
    entity_id: str,
    include_details: bool = False,
    service: PolicyService = Depends(get_policy_service),
):
    """
    Resolve all policies applicable to an entity considering inheritance.

    Inheritance order: environment > team > agent
    Returns policies with source information showing where each policy comes from.

    Set include_details=true to fetch full policy content from enforcer service.
    """
    if not service.is_enabled:
        return []

    return await service.resolve_entity_policies(
        entity_type=entity_type,
        entity_id=entity_id,
        include_details=include_details,
    )


@router.post("/evaluate/{entity_type}/{entity_id}", response_model=EvaluationResponse)
async def evaluate_entity_policies(
    entity_type: EntityType,
    entity_id: str,
    request: EvaluationRequest,
    service: PolicyService = Depends(get_policy_service),
):
    """
    Evaluate all policies for an entity against input data.

    This evaluates all inherited policies and returns aggregated results.
    """
    if not service.is_enabled:
        return EvaluationResponse(
            allowed=True,
            violations=[],
            policy_results={},
        )

    results = await service.evaluate_policies(
        entity_type=entity_type,
        entity_id=entity_id,
        input_data=request.input_data,
    )

    # Aggregate results
    allowed = all(result.allow for result in results.values())
    all_violations = []
    for result in results.values():
        all_violations.extend(result.violations)

    policy_results = {
        policy_id: result.model_dump()
        for policy_id, result in results.items()
    }

    return EvaluationResponse(
        allowed=allowed,
        violations=all_violations,
        policy_results=policy_results,
    )


@router.post("/check-authorization/{entity_type}/{entity_id}", response_model=AuthorizationCheckResponse)
async def check_entity_authorization(
    entity_type: EntityType,
    entity_id: str,
    request: AuthorizationCheckRequest,
    service: PolicyService = Depends(get_policy_service),
):
    """
    Check if an entity is authorized to perform an action.

    This is a convenience endpoint for common authorization checks.
    It evaluates all policies and returns a simple authorized/denied response.
    """
    if not service.is_enabled:
        return AuthorizationCheckResponse(
            authorized=True,
            violations=[],
            policies_evaluated=0,
        )

    authorized, violations = await service.check_entity_authorization(
        entity_type=entity_type,
        entity_id=entity_id,
        action=request.action,
        resource=request.resource,
        context=request.context,
    )

    # Count policies
    resolved = await service.resolve_entity_policies(entity_type, entity_id)

    return AuthorizationCheckResponse(
        authorized=authorized,
        violations=violations,
        policies_evaluated=len(resolved),
    )
