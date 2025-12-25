"""
Rate limiting middleware using token bucket algorithm.

Provides configurable rate limiting per client IP or user.
"""

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import time
import asyncio
import structlog
import hashlib
from control_plane_api.app.exceptions import RateLimitError

logger = structlog.get_logger()


class TokenBucket:
    """
    Token bucket implementation for rate limiting.
    
    Each bucket starts with a capacity of tokens.
    Tokens are consumed when requests are made.
    Tokens are refilled at a constant rate.
    """
    
    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        refill_period: float = 60.0,
    ):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens in bucket
            refill_rate: Number of tokens to add per period
            refill_period: Period in seconds for refilling tokens
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            Tuple of (success, info_dict)
        """
        async with self.lock:
            now = time.time()
            
            # Refill tokens based on time elapsed
            time_elapsed = now - self.last_refill
            tokens_to_add = (time_elapsed / self.refill_period) * self.refill_rate
            
            if tokens_to_add > 0:
                self.tokens = min(self.capacity, self.tokens + tokens_to_add)
                self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                success = True
                retry_after = None
            else:
                success = False
                # Calculate when enough tokens will be available
                tokens_needed = tokens - self.tokens
                time_to_wait = (tokens_needed / self.refill_rate) * self.refill_period
                retry_after = int(time_to_wait) + 1
            
            info = {
                "limit": self.capacity,
                "remaining": int(self.tokens),
                "reset": int(now + self.refill_period),
                "retry_after": retry_after,
            }
            
            return success, info


class RateLimiter:
    """
    Rate limiter managing multiple token buckets for different clients.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,
        cleanup_interval: int = 300,
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Number of requests allowed per minute
            burst_size: Maximum burst size (defaults to requests_per_minute // 4)
            cleanup_interval: Interval in seconds to clean up old buckets
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or max(10, requests_per_minute // 4)
        self.buckets: Dict[str, TokenBucket] = {}
        self.last_cleanup = time.time()
        self.cleanup_interval = cleanup_interval
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(self, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: Client identifier (IP, user ID, etc.)
            
        Returns:
            Tuple of (allowed, headers_dict)
        """
        # Clean up old buckets periodically
        await self._cleanup_buckets()
        
        # Get or create bucket for this identifier
        bucket = await self._get_or_create_bucket(identifier)
        
        # Try to consume a token
        allowed, info = await bucket.consume()
        
        # Build rate limit headers
        headers = {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(info["reset"]),
        }
        
        if not allowed and info.get("retry_after"):
            headers["Retry-After"] = str(info["retry_after"])
        
        return allowed, headers
    
    async def _get_or_create_bucket(self, identifier: str) -> TokenBucket:
        """Get existing bucket or create new one."""
        async with self.lock:
            if identifier not in self.buckets:
                self.buckets[identifier] = TokenBucket(
                    capacity=self.burst_size,
                    refill_rate=self.requests_per_minute,
                    refill_period=60.0,
                )
            return self.buckets[identifier]
    
    async def _cleanup_buckets(self):
        """Remove old unused buckets to prevent memory leak."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        async with self.lock:
            # Remove buckets that haven't been used recently
            cutoff_time = now - self.cleanup_interval
            to_remove = []
            
            for identifier, bucket in self.buckets.items():
                if bucket.last_refill < cutoff_time:
                    to_remove.append(identifier)
            
            for identifier in to_remove:
                del self.buckets[identifier]
            
            if to_remove:
                logger.info(
                    "rate_limiter_cleanup",
                    removed_count=len(to_remove),
                    remaining_count=len(self.buckets),
                )
            
            self.last_cleanup = now


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI.
    
    Limits requests per client based on IP address or authenticated user.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,
        exclude_paths: Optional[list] = None,
        identifier_callback: Optional[callable] = None,
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Default rate limit
            burst_size: Maximum burst size
            exclude_paths: Paths to exclude from rate limiting
            identifier_callback: Custom function to get client identifier
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute, burst_size)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.identifier_callback = identifier_callback
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        
        # Check if path is excluded
        if self._is_excluded(request.url.path):
            return await call_next(request)
        
        # Get client identifier
        identifier = await self._get_identifier(request)
        
        # Check rate limit
        allowed, headers = await self.rate_limiter.check_rate_limit(identifier)
        
        if not allowed:
            # Log rate limit exceeded
            logger.warning(
                "rate_limit_exceeded",
                identifier=self._hash_identifier(identifier),
                path=request.url.path,
                method=request.method,
            )
            
            # Raise rate limit error
            raise RateLimitError(
                limit=self.rate_limiter.requests_per_minute,
                window="minute",
                retry_after=int(headers.get("Retry-After", 60)),
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for header, value in headers.items():
            response.headers[header] = value
        
        return response
    
    def _is_excluded(self, path: str) -> bool:
        """Check if path is excluded from rate limiting."""
        for excluded in self.exclude_paths:
            if path.startswith(excluded):
                return True
        return False
    
    async def _get_identifier(self, request: Request) -> str:
        """
        Get client identifier for rate limiting.
        
        Priority:
        1. Custom identifier callback
        2. Authenticated user ID
        3. Client IP address
        """
        # Use custom identifier callback if provided
        if self.identifier_callback:
            identifier = await self.identifier_callback(request)
            if identifier:
                return f"custom:{identifier}"
        
        # Check for authenticated user
        if hasattr(request.state, "user") and request.state.user:
            user_id = getattr(request.state.user, "id", None)
            if user_id:
                return f"user:{user_id}"
        
        # Fall back to IP address
        client_host = request.client.host if request.client else "unknown"
        
        # Check for proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_host = forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            client_host = real_ip
        
        return f"ip:{client_host}"
    
    def _hash_identifier(self, identifier: str) -> str:
        """Hash identifier for logging (privacy)."""
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]


# Per-endpoint rate limiting decorator
class EndpointRateLimiter:
    """
    Decorator for per-endpoint rate limiting.
    
    Usage:
        rate_limiter = EndpointRateLimiter()
        
        @app.get("/expensive-operation")
        @rate_limiter.limit(requests_per_minute=10)
        async def expensive_operation():
            ...
    """
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
    
    def limit(
        self,
        requests_per_minute: int,
        burst_size: Optional[int] = None,
        identifier_callback: Optional[callable] = None,
    ):
        """
        Create rate limit decorator for endpoint.
        
        Args:
            requests_per_minute: Rate limit for this endpoint
            burst_size: Burst size for this endpoint
            identifier_callback: Custom identifier function
        """
        def decorator(func):
            # Create rate limiter for this endpoint
            endpoint_id = f"{func.__module__}.{func.__name__}"
            self.limiters[endpoint_id] = RateLimiter(
                requests_per_minute=requests_per_minute,
                burst_size=burst_size,
            )
            
            async def wrapper(request: Request, *args, **kwargs):
                # Get client identifier
                if identifier_callback:
                    identifier = await identifier_callback(request)
                else:
                    identifier = self._default_identifier(request)
                
                # Check rate limit
                limiter = self.limiters[endpoint_id]
                allowed, headers = await limiter.check_rate_limit(identifier)
                
                if not allowed:
                    raise RateLimitError(
                        limit=requests_per_minute,
                        window="minute",
                        retry_after=int(headers.get("Retry-After", 60)),
                    )
                
                # Add headers to response (if we have access to it)
                response = await func(request, *args, **kwargs)
                if isinstance(response, Response):
                    for header, value in headers.items():
                        response.headers[header] = value
                
                return response
            
            return wrapper
        return decorator
    
    def _default_identifier(self, request: Request) -> str:
        """Default identifier extraction."""
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"
        
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"


# Global rate limiter instance for decorator usage
endpoint_rate_limiter = EndpointRateLimiter()
