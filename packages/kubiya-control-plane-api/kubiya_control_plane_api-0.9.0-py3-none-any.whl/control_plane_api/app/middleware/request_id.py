"""
Request ID middleware for request tracking and correlation.

Adds a unique request ID to each request for tracking through logs and services.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog
import logging
import uuid
import contextvars
from typing import Optional

logger = structlog.get_logger()

# Context variable to store request ID
request_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID to all requests.
    
    - Checks for existing X-Request-ID header
    - Generates new ID if not present
    - Adds ID to response headers
    - Makes ID available in context for logging
    """
    
    REQUEST_ID_HEADER = "X-Request-ID"
    
    def __init__(self, app: ASGIApp, header_name: str = None):
        super().__init__(app)
        if header_name:
            self.REQUEST_ID_HEADER = header_name
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and add request ID."""
        
        # Get or generate request ID
        request_id = (
            request.headers.get(self.REQUEST_ID_HEADER) or
            request.headers.get(self.REQUEST_ID_HEADER.lower()) or
            self._generate_request_id()
        )
        
        # Validate request ID format (basic security check)
        if not self._is_valid_request_id(request_id):
            request_id = self._generate_request_id()
        
        # Store in request state for easy access
        request.state.request_id = request_id
        
        # Set context variable for logging
        token = request_id_context.set(request_id)
        
        try:
            # Log request start
            logger.info(
                "request_started",
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                query=str(request.url.query) if request.url.query else None,
                client=request.client.host if request.client else None,
            )
            
            # Process request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers[self.REQUEST_ID_HEADER] = request_id
            
            # Log request completion
            logger.info(
                "request_completed",
                request_id=request_id,
                status_code=response.status_code,
            )
            
            return response
            
        except Exception as e:
            # Log request failure
            logger.error(
                "request_failed",
                request_id=request_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
            
        finally:
            # Reset context variable
            request_id_context.reset(token)
    
    def _generate_request_id(self) -> str:
        """Generate a new request ID."""
        return str(uuid.uuid4())
    
    def _is_valid_request_id(self, request_id: str) -> bool:
        """
        Validate request ID format.
        
        Accepts UUIDs and alphanumeric strings up to 128 characters.
        """
        if not request_id or len(request_id) > 128:
            return False
        
        # Allow UUIDs, alphanumeric, hyphens, and underscores
        import re
        return bool(re.match(r'^[a-zA-Z0-9\-_]+$', request_id))


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.
    
    This can be used anywhere in the application to get the current request ID.
    
    Returns:
        Request ID if in request context, None otherwise
    """
    return request_id_context.get()


def set_request_id(request_id: str) -> None:
    """
    Set the request ID in context.
    
    This is useful for background tasks or other contexts where you want
    to maintain the request ID.
    
    Args:
        request_id: Request ID to set
    """
    request_id_context.set(request_id)


class RequestIDLogProcessor:
    """
    Structlog processor to add request ID to all log entries.
    
    Use this in your structlog configuration:
    
    structlog.configure(
        processors=[
            RequestIDLogProcessor(),
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        ...
    )
    """
    
    def __call__(self, logger, name, event_dict):
        """Add request ID to log entry if available."""
        request_id = get_request_id()
        if request_id:
            event_dict["request_id"] = request_id
        return event_dict


def setup_request_id_logging():
    """
    Configure structlog to include request ID in all logs.
    
    Call this in your app initialization.
    """
    import structlog
    
    structlog.configure(
        processors=[
            RequestIDLogProcessor(),  # Add request ID
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.INFO
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )


# For FastAPI dependency injection
async def get_request_id_from_request(request: Request) -> str:
    """
    FastAPI dependency to get request ID.
    
    Usage:
        @app.get("/example")
        async def example(request_id: str = Depends(get_request_id_from_request)):
            return {"request_id": request_id}
    """
    return getattr(request.state, "request_id", None) or str(uuid.uuid4())
