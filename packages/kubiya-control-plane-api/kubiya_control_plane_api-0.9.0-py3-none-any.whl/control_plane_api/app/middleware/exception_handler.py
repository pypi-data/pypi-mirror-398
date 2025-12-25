"""
Global exception handler middleware for Control Plane API.

Catches all exceptions and returns standardized error responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from control_plane_api.app.exceptions import ControlPlaneException
import structlog
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

logger = structlog.get_logger()


async def control_plane_exception_handler(
    request: Request,
    exc: ControlPlaneException,
) -> JSONResponse:
    """
    Handle ControlPlaneException instances.
    
    These are our custom exceptions with structured error information.
    """
    error_id = str(uuid.uuid4())
    
    # Log the error with context
    logger.error(
        "control_plane_error",
        error_id=error_id,
        error_code=exc.error_code,
        error_message=exc.message,
        error_details=exc.details,
        path=str(request.url),
        method=request.method,
    )
    
    # Build response
    response = {
        "error": {
            "id": error_id,
            "code": exc.error_code,
            "message": exc.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }
    
    # Add details if present
    if exc.details:
        response["error"]["details"] = exc.details
    
    # Add request context in development
    if request.app.debug:
        response["error"]["request"] = {
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) if request.url.query else None,
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Converts Pydantic validation errors to our standard error format.
    """
    error_id = str(uuid.uuid4())
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
        })
    
    # Log validation error
    logger.warning(
        "validation_error",
        error_id=error_id,
        validation_errors=errors,
        path=str(request.url),
        method=request.method,
    )
    
    # Build response
    response = {
        "error": {
            "id": error_id,
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "validation_errors": errors,
            },
        }
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response,
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """
    Handle FastAPI/Starlette HTTP exceptions.
    
    Converts standard HTTP exceptions to our error format.
    """
    error_id = str(uuid.uuid4())
    
    # Log the HTTP exception
    logger.warning(
        "http_exception",
        error_id=error_id,
        status_code=exc.status_code,
        detail=exc.detail,
        path=str(request.url),
        method=request.method,
    )
    
    # Map status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_ERROR",
        403: "AUTHORIZATION_ERROR",
        404: "RESOURCE_NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "RESOURCE_CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    # Build response
    response = {
        "error": {
            "id": error_id,
            "code": error_code,
            "message": exc.detail or f"HTTP {exc.status_code} Error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }
    
    # Add headers if present
    if hasattr(exc, "headers") and exc.headers:
        response["error"]["headers"] = dict(exc.headers)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response,
        headers=getattr(exc, "headers", None),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected exceptions.
    
    This is the catch-all handler for any unhandled exceptions.
    """
    error_id = str(uuid.uuid4())
    
    # Log the full exception with traceback
    logger.error(
        "unhandled_exception",
        error_id=error_id,
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=str(request.url),
        method=request.method,
        traceback=traceback.format_exc(),
        exc_info=exc,
    )
    
    # Build response
    # In production, don't expose internal error details
    if request.app.debug:
        message = f"{type(exc).__name__}: {str(exc)}"
        details = {
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc().split("\n"),
        }
    else:
        message = "An internal server error occurred"
        details = None
    
    response = {
        "error": {
            "id": error_id,
            "code": "INTERNAL_ERROR",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    # Alert on unhandled exceptions (in production, this might trigger PagerDuty)
    if not request.app.debug:
        logger.critical(
            "unhandled_exception_alert",
            error_id=error_id,
            error_type=type(exc).__name__,
            path=str(request.url),
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response,
    )


def setup_exception_handlers(app: Any) -> None:
    """
    Register all exception handlers with the FastAPI app.
    
    Call this in your main.py after creating the app.
    
    Example:
        from control_plane_api.app.middleware.exception_handler import setup_exception_handlers
        
        app = FastAPI()
        setup_exception_handlers(app)
    """
    # Our custom exceptions
    app.add_exception_handler(ControlPlaneException, control_plane_exception_handler)
    
    # FastAPI/Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("exception_handlers_registered")
