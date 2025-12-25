"""
Centralized exception hierarchy for Control Plane API.

Provides standardized exceptions with consistent error codes and status codes.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""
    
    # Validation errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Authentication/Authorization (401/403)
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Resource errors (404/409)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    
    # Rate limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # External service errors (502/503)
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    
    # Internal errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    WORKFLOW_ERROR = "WORKFLOW_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


class ControlPlaneException(Exception):
    """
    Base exception for all Control Plane errors.
    
    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        status_code: HTTP status code
        details: Additional error details
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[ErrorCode] = None,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or ErrorCode.INTERNAL_ERROR
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# 400 - Bad Request Errors

class ValidationError(ControlPlaneException):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if field:
            details = details or {}
            details["field"] = field
            if value is not None:
                details["value"] = str(value)
        
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details,
        )


class InvalidInputError(ControlPlaneException):
    """Raised when input is invalid but passes basic validation."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            details=details,
        )


# 401 - Authentication Errors

class AuthenticationError(ControlPlaneException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTHENTICATION_ERROR,
            status_code=401,
        )


class InvalidCredentialsError(ControlPlaneException):
    """Raised when credentials are invalid."""
    
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_CREDENTIALS,
            status_code=401,
        )


class TokenExpiredError(ControlPlaneException):
    """Raised when authentication token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            message=message,
            error_code=ErrorCode.TOKEN_EXPIRED,
            status_code=401,
        )


# 403 - Authorization Errors

class AuthorizationError(ControlPlaneException):
    """Raised when user lacks required permissions."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
    ):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTHORIZATION_ERROR,
            status_code=403,
            details=details,
        )


# 404 - Not Found Errors

class ResourceNotFoundError(ControlPlaneException):
    """Raised when a requested resource doesn't exist."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
    ):
        if not message:
            message = f"{resource_type} with ID '{resource_id}' not found"
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )


# 409 - Conflict Errors

class ResourceAlreadyExistsError(ControlPlaneException):
    """Raised when attempting to create a resource that already exists."""
    
    def __init__(
        self,
        resource_type: str,
        identifier: str,
        message: Optional[str] = None,
    ):
        if not message:
            message = f"{resource_type} already exists: {identifier}"
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            status_code=409,
            details={
                "resource_type": resource_type,
                "identifier": identifier,
            },
        )


class ResourceConflictError(ControlPlaneException):
    """Raised when a resource operation conflicts with current state."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_CONFLICT,
            status_code=409,
            details=details,
        )


# 429 - Rate Limit Errors

class RateLimitError(ControlPlaneException):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        limit: int,
        window: str,
        retry_after: Optional[int] = None,
    ):
        details = {
            "limit": limit,
            "window": window,
        }
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details,
        )


# 502/503 - Service Errors

class ExternalServiceError(ControlPlaneException):
    """Raised when an external service call fails."""
    
    def __init__(
        self,
        service: str,
        message: str,
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ):
        full_details = {"service": service}
        if details:
            full_details.update(details)
        
        super().__init__(
            message=f"{service}: {message}",
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=status_code,
            details=full_details,
        )


class ServiceUnavailableError(ControlPlaneException):
    """Raised when a service is temporarily unavailable."""
    
    def __init__(
        self,
        service: str,
        message: Optional[str] = None,
        retry_after: Optional[int] = None,
    ):
        if not message:
            message = f"{service} is temporarily unavailable"
        
        details = {"service": service}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=503,
            details=details,
        )


class TimeoutError(ControlPlaneException):
    """Raised when an operation times out."""
    
    def __init__(
        self,
        operation: str,
        timeout_seconds: Optional[float] = None,
    ):
        details = {"operation": operation}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        
        super().__init__(
            message=f"Operation '{operation}' timed out",
            error_code=ErrorCode.TIMEOUT_ERROR,
            status_code=504,
            details=details,
        )


# 500 - Internal Errors

class DatabaseError(ControlPlaneException):
    """Raised when a database operation fails."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        full_details = details or {}
        if operation:
            full_details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=500,
            details=full_details,
        )


class WorkflowExecutionError(ControlPlaneException):
    """Raised when a Temporal workflow execution fails."""
    
    def __init__(
        self,
        workflow_id: str,
        message: str,
        workflow_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        full_details = {
            "workflow_id": workflow_id,
        }
        if workflow_type:
            full_details["workflow_type"] = workflow_type
        if details:
            full_details.update(details)
        
        super().__init__(
            message=f"Workflow {workflow_id}: {message}",
            error_code=ErrorCode.WORKFLOW_ERROR,
            status_code=500,
            details=full_details,
        )


class ConfigurationError(ControlPlaneException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            status_code=500,
            details=details,
        )
