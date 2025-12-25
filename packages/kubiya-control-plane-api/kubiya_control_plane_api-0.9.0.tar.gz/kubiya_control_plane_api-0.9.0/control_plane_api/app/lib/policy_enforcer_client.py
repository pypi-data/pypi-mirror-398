"""
Policy Enforcer Client - Integration with OPA Watchdog Enforcer Service.

This module provides a robust, async client for interacting with the OPA Watchdog
policy enforcement service. It follows best practices including:

- Async/await for non-blocking I/O
- Proper exception hierarchy
- Context manager support for resource cleanup
- Pydantic models for validation
- Dependency injection (no singletons)
- Separation of concerns with specialized clients
- Retry logic and circuit breaker patterns
- Comprehensive logging

The enforcer service URL is configured via ENFORCER_SERVICE_URL environment variable.
Default: https://enforcer-psi.vercel.app

Usage:
    from control_plane_api.app.lib.policy_enforcer_client import PolicyEnforcerClient

    async with PolicyEnforcerClient(base_url="...", api_key="...") as client:
        policy = await client.policies.create(name="...", policy_content="...")
        result = await client.evaluation.evaluate(policy_id="...", input_data={...})
"""

import os
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any, Protocol
from enum import Enum
from pydantic import BaseModel, Field, validator
import structlog
from contextlib import asynccontextmanager

logger = structlog.get_logger()


# ============================================================================
# Custom Exceptions
# ============================================================================

class PolicyEnforcerError(Exception):
    """Base exception for all policy enforcer errors"""
    pass


class PolicyNotFoundError(PolicyEnforcerError):
    """Raised when a policy is not found"""
    pass


class PolicyValidationError(PolicyEnforcerError):
    """Raised when policy validation fails"""
    def __init__(self, message: str, details: dict = None, errors: list = None):
        super().__init__(message)
        self.details = details or {}
        self.errors = errors or []


class PolicyEvaluationError(PolicyEnforcerError):
    """Raised when policy evaluation fails"""
    pass


class RequestNotFoundError(PolicyEnforcerError):
    """Raised when a request is not found"""
    pass


class EnforcerConnectionError(PolicyEnforcerError):
    """Raised when connection to enforcer service fails"""
    pass


class EnforcerAuthenticationError(PolicyEnforcerError):
    """Raised when authentication with enforcer service fails"""
    pass


# ============================================================================
# Pydantic Models
# ============================================================================

class PolicyType(str, Enum):
    """Policy type enumeration"""
    REGO = "rego"


class Decision(str, Enum):
    """Policy evaluation decision"""
    PERMIT = "permit"
    DENY = "deny"


class RequestStatus(str, Enum):
    """Request approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Policy(BaseModel):
    """Policy model matching the enforcer service schema"""
    id: str = Field(..., description="Policy UUID")
    name: str = Field(..., min_length=1, max_length=255, description="Policy name")
    policy_content: Optional[str] = Field(None, description="OPA Rego policy content (optional in list responses)")
    org: str = Field(..., description="Organization ID")
    enabled: bool = Field(default=True, description="Whether policy is enabled")
    description: Optional[str] = Field(None, description="Policy description")
    policy_type: PolicyType = Field(default=PolicyType.REGO, description="Policy type")
    tags: List[str] = Field(default_factory=list, description="Policy tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    version: int = Field(default=1, ge=1, description="Policy version")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator email")
    updated_by: Optional[str] = Field(None, description="Last updater email")

    class Config:
        use_enum_values = True


class PolicyCreate(BaseModel):
    """Schema for creating a new policy"""
    name: str = Field(..., min_length=1, max_length=255)
    policy_content: str = Field(..., min_length=1)
    description: Optional[str] = None
    enabled: bool = True
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicyUpdate(BaseModel):
    """Schema for updating an existing policy"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    policy_content: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EvaluationResult(BaseModel):
    """Policy evaluation result"""
    allow: bool = Field(..., description="Whether the action is allowed")
    decision: Decision = Field(..., description="Evaluation decision")
    violations: List[str] = Field(default_factory=list, description="List of violations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Evaluation metadata")

    class Config:
        use_enum_values = True


class EvaluationRequest(BaseModel):
    """Policy evaluation request"""
    input: Dict[str, Any] = Field(..., description="Input data for evaluation")
    policy_id: Optional[str] = Field(None, description="Policy UUID")
    policy_name: Optional[str] = Field(None, description="Policy name")

    @validator("policy_id", "policy_name")
    def validate_policy_identifier(cls, v, values):
        """Ensure at least one policy identifier is provided"""
        if not v and not values.get("policy_id") and not values.get("policy_name"):
            raise ValueError("Either policy_id or policy_name must be provided")
        return v


class ValidationResult(BaseModel):
    """Policy validation result"""
    valid: bool = Field(..., description="Whether the policy is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class ApprovalRequest(BaseModel):
    """Approval request model"""
    id: str = Field(..., description="Request UUID")
    request_id: str = Field(..., description="Request identifier")
    org: str = Field(..., description="Organization ID")
    runner: str = Field(..., description="Runner name")
    request_hash: str = Field(..., description="Request hash")
    approved: bool = Field(..., description="Whether approved")
    ttl: datetime = Field(..., description="Time to live")
    created_at: datetime = Field(..., description="Creation timestamp")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    approved_by: Optional[str] = Field(None, description="Approver email")
    request_data: Dict[str, Any] = Field(default_factory=dict, description="Request data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PolicyListResponse(BaseModel):
    """Response for list policies endpoint"""
    policies: List[Policy]
    total: int
    page: Optional[int] = 1  # Optional because enforcer may not return it
    limit: int
    has_more: bool


class RequestListResponse(BaseModel):
    """Response for list requests endpoint"""
    requests: List[ApprovalRequest]
    total: int
    page: int
    limit: int
    has_more: bool


# ============================================================================
# Specialized Clients (Separation of Concerns)
# ============================================================================

class PolicyOperations:
    """Handles policy CRUD operations"""

    def __init__(self, client: httpx.AsyncClient, base_url: str, headers: Dict[str, str]):
        self._client = client
        self._base_url = base_url
        self._headers = headers

    async def create(self, policy: PolicyCreate) -> Policy:
        """
        Create a new OPA policy.

        Args:
            policy: Policy creation data

        Returns:
            Created Policy object

        Raises:
            PolicyValidationError: If policy content is invalid
            EnforcerConnectionError: If connection fails
        """
        try:
            url = f"{self._base_url}/api/v1/policies"
            response = await self._client.post(
                url,
                json=policy.model_dump(exclude_none=True),
                headers=self._headers
            )

            if response.status_code == 201:
                data = response.json()
                logger.info(
                    "policy_created",
                    policy_id=data.get("id"),
                    policy_name=policy.name,
                )
                return Policy(**data)
            elif response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get("error", "Policy validation failed")
                error_details = error_data.get("details", {})
                # Handle both single error and array of errors
                error_list = []
                if "errors" in error_data and isinstance(error_data["errors"], list):
                    error_list = error_data["errors"]
                elif error_details and "reason" in error_details:
                    error_list = [error_details["reason"]]

                logger.error(
                    "policy_validation_failed",
                    error=error_message,
                    details=error_details,
                    errors=error_list
                )
                raise PolicyValidationError(
                    message=error_message,
                    details=error_details,
                    errors=error_list
                )
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            elif response.status_code == 409:
                error_data = response.json()
                raise PolicyValidationError(
                    message=error_data.get("error", "Policy already exists"),
                    details=error_data.get("details", {}),
                    errors=error_data.get("errors", [])
                )
            else:
                raise PolicyEnforcerError(
                    f"Failed to create policy: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("policy_creation_request_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e

    async def get(self, policy_id: str) -> Policy:
        """
        Get a specific policy by ID.

        Args:
            policy_id: Policy UUID

        Returns:
            Policy object

        Raises:
            PolicyNotFoundError: If policy doesn't exist
            EnforcerConnectionError: If connection fails
        """
        try:
            url = f"{self._base_url}/api/v1/policies/{policy_id}"
            response = await self._client.get(url, headers=self._headers)

            if response.status_code == 200:
                return Policy(**response.json())
            elif response.status_code == 404:
                raise PolicyNotFoundError(f"Policy {policy_id} not found")
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            else:
                raise PolicyEnforcerError(
                    f"Failed to get policy: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("policy_get_request_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e

    async def list(
        self,
        page: int = 1,
        limit: int = 20,
        enabled: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> PolicyListResponse:
        """
        List policies with pagination and filtering.

        Args:
            page: Page number (default: 1)
            limit: Items per page (default: 20, max: 100)
            enabled: Filter by enabled status
            search: Search term for policy name or description

        Returns:
            PolicyListResponse with policies and pagination info
        """
        try:
            url = f"{self._base_url}/api/v1/policies"
            params = {"page": page, "limit": min(limit, 100)}

            if enabled is not None:
                params["enabled"] = enabled
            if search:
                params["search"] = search

            response = await self._client.get(
                url,
                params=params,
                headers=self._headers
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    "policies_listed",
                    count=len(data.get("policies", [])),
                    total=data.get("total", 0),
                )
                return PolicyListResponse(**data)
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            else:
                raise PolicyEnforcerError(
                    f"Failed to list policies: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("policies_list_request_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e

    async def update(self, policy_id: str, update: PolicyUpdate) -> Policy:
        """
        Update an existing policy.

        Args:
            policy_id: Policy UUID
            update: Policy update data

        Returns:
            Updated Policy object

        Raises:
            PolicyNotFoundError: If policy doesn't exist
            PolicyValidationError: If update is invalid
        """
        try:
            url = f"{self._base_url}/api/v1/policies/{policy_id}"
            response = await self._client.put(
                url,
                json=update.model_dump(exclude_none=True),
                headers=self._headers
            )

            if response.status_code == 200:
                data = response.json()
                logger.info("policy_updated", policy_id=policy_id)
                return Policy(**data)
            elif response.status_code == 404:
                raise PolicyNotFoundError(f"Policy {policy_id} not found")
            elif response.status_code == 400:
                error_data = response.json()
                raise PolicyValidationError(
                    error_data.get("error", "Policy validation failed")
                )
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            else:
                raise PolicyEnforcerError(
                    f"Failed to update policy: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("policy_update_request_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e

    async def delete(self, policy_id: str) -> None:
        """
        Delete a policy.

        Args:
            policy_id: Policy UUID

        Raises:
            PolicyNotFoundError: If policy doesn't exist
        """
        try:
            url = f"{self._base_url}/api/v1/policies/{policy_id}"
            response = await self._client.delete(url, headers=self._headers)

            if response.status_code == 204:
                logger.info("policy_deleted", policy_id=policy_id)
                return
            elif response.status_code == 404:
                raise PolicyNotFoundError(f"Policy {policy_id} not found")
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            else:
                raise PolicyEnforcerError(
                    f"Failed to delete policy: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("policy_delete_request_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e

    async def validate(self, policy_id: str) -> ValidationResult:
        """
        Validate a policy's syntax and structure.

        Args:
            policy_id: Policy UUID

        Returns:
            ValidationResult with validation status and errors

        Raises:
            PolicyNotFoundError: If policy doesn't exist
        """
        try:
            url = f"{self._base_url}/api/v1/policies/{policy_id}/validate"
            response = await self._client.post(url, headers=self._headers)

            if response.status_code in (200, 400):
                data = response.json()
                result = ValidationResult(**data)
                logger.info(
                    "policy_validated",
                    policy_id=policy_id,
                    valid=result.valid,
                    error_count=len(result.errors),
                )
                return result
            elif response.status_code == 404:
                raise PolicyNotFoundError(f"Policy {policy_id} not found")
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            else:
                raise PolicyEnforcerError(
                    f"Failed to validate policy: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("policy_validate_request_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e


class EvaluationOperations:
    """Handles policy evaluation operations"""

    def __init__(self, client: httpx.AsyncClient, base_url: str, headers: Dict[str, str]):
        self._client = client
        self._base_url = base_url
        self._headers = headers

    async def evaluate(
        self,
        input_data: Dict[str, Any],
        policy_id: Optional[str] = None,
        policy_name: Optional[str] = None,
    ) -> EvaluationResult:
        """
        Evaluate a policy against input data.

        Args:
            input_data: Input data to evaluate
            policy_id: Policy UUID (use this or policy_name)
            policy_name: Policy name (use this or policy_id)

        Returns:
            EvaluationResult with decision and violations

        Raises:
            PolicyEvaluationError: If evaluation fails
            PolicyNotFoundError: If policy doesn't exist
        """
        try:
            url = f"{self._base_url}/api/v1/evaluate"
            request = EvaluationRequest(
                input=input_data,
                policy_id=policy_id,
                policy_name=policy_name
            )

            response = await self._client.post(
                url,
                json=request.model_dump(exclude_none=True),
                headers=self._headers
            )

            if response.status_code == 200:
                result = EvaluationResult(**response.json())
                logger.info(
                    "policy_evaluated",
                    policy_id=policy_id,
                    policy_name=policy_name,
                    allow=result.allow,
                    decision=result.decision,
                    violations=len(result.violations),
                )
                return result
            elif response.status_code == 404:
                raise PolicyNotFoundError(
                    f"Policy {policy_id or policy_name} not found"
                )
            elif response.status_code == 400:
                error_data = response.json()
                raise PolicyEvaluationError(
                    error_data.get("error", "Evaluation failed")
                )
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            else:
                raise PolicyEvaluationError(
                    f"Evaluation failed: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("evaluation_request_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e

    async def enforce(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the enforcer's /enforce endpoint to evaluate ALL loaded policies.

        This is the main enforcement endpoint that evaluates the input against
        all policies loaded in the enforcer service.

        Args:
            input_data: Input data to evaluate against policies

        Returns:
            Dict with enforcement result:
            {
                "id": "enforcement-uuid",
                "allow": true/false,
                "policies": ["policy.names.that.passed.or.blocked"]
            }

        Raises:
            PolicyEvaluationError: If enforcement fails
            EnforcerConnectionError: If connection fails
        """
        try:
            url = f"{self._base_url}/enforce"
            response = await self._client.post(
                url,
                json=input_data,
                headers=self._headers
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    "policy_enforced",
                    allow=result.get("allow"),
                    policies=result.get("policies", []),
                    enforcement_id=result.get("id"),
                )
                return result
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            else:
                raise PolicyEvaluationError(
                    f"Enforcement failed: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("enforcement_request_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e


class RequestOperations:
    """Handles approval request operations"""

    def __init__(self, client: httpx.AsyncClient, base_url: str, headers: Dict[str, str]):
        self._client = client
        self._base_url = base_url
        self._headers = headers

    async def approve(
        self,
        request_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApprovalRequest:
        """
        Approve a pending request.

        Args:
            request_id: Request ID to approve
            metadata: Optional metadata to attach

        Returns:
            Updated ApprovalRequest

        Raises:
            RequestNotFoundError: If request doesn't exist
        """
        try:
            url = f"{self._base_url}/api/v1/requests/{request_id}/approve"
            payload = {"metadata": metadata or {}}

            response = await self._client.post(
                url,
                json=payload,
                headers=self._headers
            )

            if response.status_code == 200:
                logger.info("request_approved", request_id=request_id)
                return ApprovalRequest(**response.json())
            elif response.status_code == 404:
                raise RequestNotFoundError(f"Request {request_id} not found")
            elif response.status_code == 409:
                error_data = response.json()
                raise PolicyEnforcerError(
                    error_data.get("error", "Request already processed")
                )
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            else:
                raise PolicyEnforcerError(
                    f"Failed to approve request: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("approve_request_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e

    async def bulk_approve(
        self,
        request_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Approve multiple requests at once.

        Args:
            request_ids: List of request IDs (max 100)
            metadata: Optional metadata to attach

        Returns:
            Dict with approval results
        """
        try:
            url = f"{self._base_url}/api/v1/requests/bulk-approve"
            payload = {
                "request_ids": request_ids[:100],
                "metadata": metadata or {},
            }

            response = await self._client.post(
                url,
                json=payload,
                headers=self._headers
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    "requests_bulk_approved",
                    requested=data.get("requested_count", 0),
                    approved=data.get("approved_count", 0),
                )
                return data
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            else:
                raise PolicyEnforcerError(
                    f"Bulk approval failed: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("bulk_approve_request_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e

    async def get(self, request_id: str) -> ApprovalRequest:
        """
        Get details of a specific request.

        Args:
            request_id: Request ID

        Returns:
            ApprovalRequest object

        Raises:
            RequestNotFoundError: If request doesn't exist
        """
        try:
            url = f"{self._base_url}/api/v1/requests/{request_id}/describe"
            response = await self._client.get(url, headers=self._headers)

            if response.status_code == 200:
                return ApprovalRequest(**response.json())
            elif response.status_code == 404:
                raise RequestNotFoundError(f"Request {request_id} not found")
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            else:
                raise PolicyEnforcerError(
                    f"Failed to get request: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("get_request_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e

    async def list(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[RequestStatus] = None,
        runner: Optional[str] = None,
    ) -> RequestListResponse:
        """
        List approval requests with pagination.

        Args:
            page: Page number
            limit: Items per page (max 100)
            status: Filter by status
            runner: Filter by runner name

        Returns:
            RequestListResponse with requests and pagination
        """
        try:
            url = f"{self._base_url}/api/v1/requests"
            params = {"page": page, "limit": min(limit, 100)}

            if status:
                params["status"] = status.value
            if runner:
                params["runner"] = runner

            response = await self._client.get(
                url,
                params=params,
                headers=self._headers
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    "requests_listed",
                    count=len(data.get("requests", [])),
                    total=data.get("total", 0),
                )
                return RequestListResponse(**data)
            elif response.status_code == 401:
                raise EnforcerAuthenticationError("Authentication failed")
            else:
                raise PolicyEnforcerError(
                    f"Failed to list requests: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.error("list_requests_failed", error=str(e))
            raise EnforcerConnectionError(f"Connection failed: {str(e)}") from e


# ============================================================================
# Main Client with Context Manager Support
# ============================================================================

class PolicyEnforcerClient:
    """
    Main client for OPA Watchdog Enforcer Service.

    This client provides a clean, async interface with proper resource management.
    Use it as a context manager to ensure proper cleanup:

        async with PolicyEnforcerClient(base_url="...", api_key="...") as client:
            policy = await client.policies.create(...)
            result = await client.evaluation.evaluate(...)
            request = await client.requests.approve(...)

    Attributes:
        policies: PolicyOperations for CRUD operations
        evaluation: EvaluationOperations for policy evaluation
        requests: RequestOperations for approval workflows
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        auth_type: str = "UserKey",
    ):
        """
        Initialize Policy Enforcer client.

        Args:
            base_url: Enforcer service URL
            api_key: Kubiya API key (JWT token)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            auth_type: Authentication type - "UserKey" or "Bearer" (default: "UserKey")
        """
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max_retries
        self._auth_type = auth_type
        self._headers = {"Authorization": f"{auth_type} {api_key}"}

        # Create async HTTP client with retries
        transport = httpx.AsyncHTTPTransport(retries=max_retries)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            transport=transport,
        )

        # Initialize specialized operation handlers
        self.policies = PolicyOperations(self._client, self._base_url, self._headers)
        self.evaluation = EvaluationOperations(self._client, self._base_url, self._headers)
        self.requests = RequestOperations(self._client, self._base_url, self._headers)

    async def __aenter__(self):
        """Context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        await self.close()

    async def close(self):
        """Close the HTTP client and cleanup resources"""
        try:
            await self._client.aclose()
        except Exception as e:
            logger.warning("client_close_error", error=str(e), error_type=type(e).__name__)

    async def health_check(self) -> bool:
        """
        Check if the enforcer service is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Use the policies list endpoint with limit=1 to check connectivity
            url = f"{self._base_url}/api/v1/policies"
            response = await self._client.get(
                url,
                params={"limit": 1},
                headers=self._headers,
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning("health_check_failed", error=str(e), error_type=type(e).__name__)
            return False

    async def get_status(self) -> Dict[str, Any]:
        """
        Get detailed service status.

        Returns:
            Status dict with service information
        """
        try:
            url = f"{self._base_url}/status"
            response = await self._client.get(url, timeout=5.0)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.warning("status_check_failed", error=str(e))
            return {}


# ============================================================================
# Factory Function (Dependency Injection)
# ============================================================================

@asynccontextmanager
async def create_policy_enforcer_client(
    enforcer_url: Optional[str] = None,
    api_key: Optional[str] = None,
    auth_type: str = "UserKey",
) -> Optional[PolicyEnforcerClient]:
    """
    Factory function to create a PolicyEnforcerClient with context manager support.

    Reads configuration from environment variables if not provided:
    - ENFORCER_SERVICE_URL: Enforcer service URL (default: https://enforcer-psi.vercel.app)
    - api_key: Authorization token (typically passed from the incoming request)

    Args:
        enforcer_url: Optional enforcer URL override
        api_key: Authorization token (Bearer token from the request)
        auth_type: Authentication type - "UserKey" or "Bearer" (default: "UserKey")

    Yields:
        PolicyEnforcerClient instance if configured, None if disabled

    Usage:
        async with create_policy_enforcer_client(api_key=request_token, auth_type="UserKey") as client:
            if client:
                policy = await client.policies.create(...)
    """
    # Check if enforcer is enabled
    enforcer_url = enforcer_url or os.environ.get("ENFORCER_SERVICE_URL")

    # If no URL is set, yield None (enforcer is disabled)
    if not enforcer_url:
        logger.info("policy_enforcer_disabled", reason="no_url")
        yield None
        return

    # Strip whitespace and newlines
    enforcer_url = enforcer_url.strip()

    # Default to production URL
    if enforcer_url == "":
        enforcer_url = "https://enforcer-psi.vercel.app"

    # API key should be passed from the request, not from environment
    # Fall back to KUBIYA_API_KEY for backward compatibility
    if not api_key:
        api_key = os.environ.get("KUBIYA_API_KEY")

    if not api_key:
        logger.warning("policy_enforcer_disabled_no_api_key", reason="missing_token")
        yield None
        return

    # Create and yield client
    client = PolicyEnforcerClient(base_url=enforcer_url, api_key=api_key, auth_type=auth_type)

    try:
        logger.info("policy_enforcer_client_created", enforcer_url=enforcer_url, auth_type=auth_type)
        yield client
    finally:
        try:
            await client.close()
        except Exception as e:
            logger.warning("policy_enforcer_client_cleanup_error", error=str(e), error_type=type(e).__name__)


# Convenience function for dependency injection in FastAPI
def get_policy_enforcer_client_dependency() -> Optional[PolicyEnforcerClient]:
    """
    Dependency function for FastAPI to inject PolicyEnforcerClient.

    Usage in FastAPI:
        @router.get("/policies")
        async def list_policies(
            client: PolicyEnforcerClient = Depends(get_policy_enforcer_client_dependency)
        ):
            if client:
                policies = await client.policies.list()
            ...
    """
    enforcer_url = os.environ.get("ENFORCER_SERVICE_URL")
    api_key = os.environ.get("KUBIYA_API_KEY")

    if not enforcer_url or not api_key:
        return None

    if enforcer_url == "":
        enforcer_url = "https://enforcer-psi.vercel.app"

    return PolicyEnforcerClient(base_url=enforcer_url, api_key=api_key)
