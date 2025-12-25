"""
Local FastAPI proxy for Claude Code SDK to inject Langfuse metadata.

This proxy runs in the same process as the worker and intercepts requests
from Claude Code SDK to add missing metadata before forwarding to the real
LiteLLM proxy.

Architecture:
    Claude Code SDK → Local Proxy (adds metadata) → Real LiteLLM Proxy → Langfuse

The proxy:
1. Receives requests from Claude Code SDK
2. Extracts execution context from thread-local cache
3. Injects Langfuse metadata (trace_name, trace_user_id, session_id, etc.)
4. Forwards request to real LiteLLM proxy
5. Returns response back to Claude Code SDK
"""

import asyncio
import os
import threading
import time
from typing import Dict, Any, Optional
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import uvicorn

logger = structlog.get_logger(__name__)


# Thread-local storage for execution context
# This allows us to access execution metadata from the proxy
class ExecutionContextStore:
    """
    Thread-safe storage for execution context metadata with TTL and proactive cleanup.

    Features:
    - TTL-based expiration (default 3600s)
    - Proactive cleanup timer (runs every 60s)
    - Circuit breaker to prevent runaway memory growth
    - Thread-safe operations
    """

    def __init__(self, ttl_seconds: int = 3600, max_contexts: int = 1000):
        self._contexts: Dict[str, Dict[str, Any]] = {}
        self._context_timestamps: Dict[str, float] = {}
        self._ttl_seconds = ttl_seconds
        self._max_contexts = max_contexts  # Circuit breaker threshold
        self._current_execution: Optional[str] = None
        self._lock = threading.Lock()

        # Proactive cleanup timer
        self._cleanup_timer: Optional[threading.Timer] = None
        self._cleanup_interval = 60  # Run cleanup every 60 seconds
        self._start_proactive_cleanup()

    def _start_proactive_cleanup(self):
        """Start periodic cleanup timer."""
        self._cleanup_timer = threading.Timer(
            self._cleanup_interval,
            self._proactive_cleanup_worker
        )
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()
        logger.debug("proactive_cleanup_timer_started", interval=self._cleanup_interval)

    def _proactive_cleanup_worker(self):
        """Worker that runs periodic cleanup."""
        try:
            self._cleanup_expired()

            # Check circuit breaker
            with self._lock:
                context_count = len(self._contexts)

            if context_count > self._max_contexts:
                logger.error(
                    "context_store_circuit_breaker_triggered",
                    context_count=context_count,
                    max_contexts=self._max_contexts,
                    action="forcing_aggressive_cleanup"
                )
                # Aggressive cleanup: remove oldest 50%
                self._force_cleanup(keep_ratio=0.5)

        except Exception as e:
            logger.error(
                "proactive_cleanup_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
        finally:
            # Reschedule timer
            self._start_proactive_cleanup()

    def _force_cleanup(self, keep_ratio: float = 0.5):
        """
        Force cleanup of oldest contexts when circuit breaker triggers.

        Args:
            keep_ratio: Ratio of newest contexts to keep (0.5 = keep newest 50%)
        """
        with self._lock:
            if not self._contexts:
                return

            # Sort by timestamp (oldest first)
            sorted_ids = sorted(
                self._context_timestamps.items(),
                key=lambda x: x[1]
            )

            # Calculate how many to remove
            keep_count = int(len(sorted_ids) * keep_ratio)
            to_remove = sorted_ids[:len(sorted_ids) - keep_count]

            # Remove oldest contexts
            removed_count = 0
            for exec_id, _ in to_remove:
                self._contexts.pop(exec_id, None)
                self._context_timestamps.pop(exec_id, None)
                if self._current_execution == exec_id:
                    self._current_execution = None
                removed_count += 1

            logger.warning(
                "forced_cleanup_completed",
                removed=removed_count,
                remaining=len(self._contexts),
                keep_ratio=keep_ratio
            )

    def set_context(self, execution_id: str, context: Dict[str, Any]):
        """Store execution context for an execution ID with timestamp."""
        with self._lock:
            # Check circuit breaker before adding
            if len(self._contexts) >= self._max_contexts:
                logger.error(
                    "context_store_at_capacity",
                    current_count=len(self._contexts),
                    max_contexts=self._max_contexts,
                    action="rejecting_new_context"
                )
                raise RuntimeError(
                    f"Context store at capacity ({self._max_contexts}). "
                    "System may be leaking contexts or under high load."
                )

            self._contexts[execution_id] = context
            self._context_timestamps[execution_id] = time.time()
            self._current_execution = execution_id
            logger.debug(
                "execution_context_stored",
                execution_id=execution_id[:8] if len(execution_id) >= 8 else execution_id,
                total_contexts=len(self._contexts),
                has_user_id=bool(context.get("user_id")),
                has_session_id=bool(context.get("session_id")),
            )

    def get_context(self, execution_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve execution context for an execution ID if not expired.

        If execution_id is None, returns the current active execution context.
        """
        with self._lock:
            target_id = execution_id if execution_id else self._current_execution
            if not target_id:
                return None

            # Check if expired
            timestamp = self._context_timestamps.get(target_id)
            if timestamp and (time.time() - timestamp) > self._ttl_seconds:
                # Expired - remove and return None
                self._contexts.pop(target_id, None)
                self._context_timestamps.pop(target_id, None)
                logger.debug("execution_context_expired", execution_id=target_id[:8] if len(target_id) >= 8 else target_id)
                return None

            return self._contexts.get(target_id)

    def get_current_execution_id(self) -> Optional[str]:
        """Get the current active execution ID."""
        with self._lock:
            return self._current_execution

    def get_any_valid_execution_id(self) -> Optional[str]:
        """
        Get any valid (non-expired) execution ID.

        This is a fallback when _current_execution is None but there are still
        valid contexts available. Useful for sub-agent requests that arrive
        after _current_execution has been overwritten by concurrent executions.

        Returns the most recently set context's execution ID.
        """
        with self._lock:
            if not self._contexts:
                return None

            now = time.time()
            # Find the most recent non-expired context
            valid_contexts = [
                (exec_id, ts) for exec_id, ts in self._context_timestamps.items()
                if (now - ts) <= self._ttl_seconds and exec_id in self._contexts
            ]

            if not valid_contexts:
                return None

            # Return the most recently set context
            most_recent = max(valid_contexts, key=lambda x: x[1])
            logger.debug(
                "using_fallback_execution_context",
                execution_id=most_recent[0][:8] if len(most_recent[0]) >= 8 else most_recent[0],
                total_valid_contexts=len(valid_contexts),
            )
            return most_recent[0]

    def clear_context(self, execution_id: str):
        """Clear execution context after execution completes."""
        with self._lock:
            if execution_id in self._contexts:
                del self._contexts[execution_id]
                self._context_timestamps.pop(execution_id, None)
                if self._current_execution == execution_id:
                    self._current_execution = None
                logger.debug(
                    "execution_context_cleared",
                    execution_id=execution_id[:8] if len(execution_id) >= 8 else execution_id,
                    remaining_contexts=len(self._contexts)
                )

    def _cleanup_expired(self) -> None:
        """Remove contexts older than TTL."""
        now = time.time()
        with self._lock:
            expired_ids = [
                exec_id for exec_id, timestamp in self._context_timestamps.items()
                if (now - timestamp) > self._ttl_seconds
            ]

            if expired_ids:
                for exec_id in expired_ids:
                    self._contexts.pop(exec_id, None)
                    self._context_timestamps.pop(exec_id, None)
                    if self._current_execution == exec_id:
                        self._current_execution = None

                logger.info(
                    "expired_contexts_cleaned",
                    removed=len(expired_ids),
                    remaining=len(self._contexts)
                )

    def get_stats(self) -> Dict[str, Any]:
        """Get context store statistics."""
        with self._lock:
            now = time.time()
            ages = [now - ts for ts in self._context_timestamps.values()]
            return {
                'total_contexts': len(self._contexts),
                'max_contexts': self._max_contexts,
                'ttl_seconds': self._ttl_seconds,
                'oldest_age_seconds': int(max(ages)) if ages else 0,
                'newest_age_seconds': int(min(ages)) if ages else 0,
            }

    def shutdown(self):
        """Stop proactive cleanup timer."""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
            logger.info("context_store_cleanup_timer_stopped")


# Global context store
_context_store = ExecutionContextStore()


class ContextCleanupScheduler:
    """Schedules delayed context cleanup without blocking."""

    def __init__(self):
        self._pending_cleanups: Dict[str, asyncio.Task] = {}
        self._lock = threading.Lock()

    def schedule_cleanup(
        self,
        execution_id: str,
        delay_seconds: float,
        store: 'ExecutionContextStore'
    ):
        """Schedule cleanup after delay (non-blocking)."""
        with self._lock:
            # Cancel existing cleanup if rescheduling
            if execution_id in self._pending_cleanups:
                self._pending_cleanups[execution_id].cancel()

            # Create background task for delayed cleanup
            try:
                loop = asyncio.get_event_loop()
                task = loop.create_task(
                    self._delayed_cleanup(execution_id, delay_seconds, store)
                )
                self._pending_cleanups[execution_id] = task
            except RuntimeError:
                # No event loop - fallback to immediate cleanup
                store.clear_context(execution_id)

    async def _delayed_cleanup(
        self,
        execution_id: str,
        delay_seconds: float,
        store: 'ExecutionContextStore'
    ):
        """Internal: Wait then clear context."""
        try:
            await asyncio.sleep(delay_seconds)
            store.clear_context(execution_id)
        except asyncio.CancelledError:
            pass  # Cleanup was cancelled
        except Exception as e:
            # Log but don't crash - TTL will handle it
            logger.warning(
                "context_cleanup_error",
                execution_id=execution_id[:8] if len(execution_id) >= 8 else execution_id,
                error=str(e)
            )
        finally:
            with self._lock:
                self._pending_cleanups.pop(execution_id, None)


# Global cleanup scheduler
_cleanup_scheduler = ContextCleanupScheduler()


def _hash_user_id(user_id: str, organization_id: str) -> str:
    """
    Hash user_id to avoid sending email addresses to Anthropic API.

    Anthropic API rejects email addresses in metadata.user_id.
    We hash the email with org to create a unique, non-PII identifier.

    Args:
        user_id: User ID (may be email address)
        organization_id: Organization ID

    Returns:
        Hashed user identifier (SHA256, first 16 chars)
    """
    import hashlib
    combined = f"{user_id}-{organization_id}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def build_langfuse_metadata(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build Langfuse metadata from execution context.

    Matches the format used by agno runtime for consistency.

    Args:
        context: Execution context with user_id, session_id, agent_id, etc.

    Returns:
        Metadata dict for Langfuse tracking
    """
    metadata = {}

    user_id = context.get("user_id")
    organization_id = context.get("organization_id")
    session_id = context.get("session_id")
    agent_id = context.get("agent_id")
    agent_name = context.get("agent_name")
    model_id = context.get("model_id")

    # Langfuse naming fields - try all possible field names
    metadata["name"] = "agent-chat"  # Primary field for trace/generation name
    metadata["trace_name"] = "agent-chat"
    metadata["generation_name"] = "agent-chat"

    # Hash user_id to avoid sending email addresses to Anthropic API
    # Anthropic rejects: "user_id appears to contain an email address"
    if user_id and organization_id:
        hashed_user_id = _hash_user_id(user_id, organization_id)
        metadata["trace_user_id"] = hashed_user_id
        metadata["user_id"] = hashed_user_id

    # Use session_id as trace_id to group conversation turns
    if session_id:
        metadata["trace_id"] = session_id
        metadata["session_id"] = session_id

    # Additional metadata (these are safe - not sent to Anthropic)
    if agent_id:
        metadata["agent_id"] = agent_id
    if agent_name:
        metadata["agent_name"] = agent_name
    if user_id:
        metadata["user_email"] = user_id  # Keep original for Langfuse internal tracking
    if organization_id:
        metadata["organization_id"] = organization_id
    if model_id:
        metadata["model"] = model_id

    return metadata


class LiteLLMProxyApp:
    """FastAPI application for LiteLLM proxy with metadata injection."""

    def __init__(self, litellm_base_url: str, litellm_api_key: str):
        """
        Initialize the proxy application.

        Args:
            litellm_base_url: Base URL of the real LiteLLM proxy
            litellm_api_key: API key for LiteLLM proxy
        """
        self.litellm_base_url = litellm_base_url.rstrip('/')
        self.litellm_api_key = litellm_api_key
        self.client = None  # Will be lazily initialized per request
        self._client_lock = None  # Asyncio lock for thread-safe client creation

        # Create FastAPI app WITHOUT lifespan
        # Reason: httpx clients must be created in the same event loop where they're used
        # When uvicorn runs in a background thread, it has its own event loop
        # Creating the client in a different loop causes ConnectError
        self.app = FastAPI(
            title="Claude Code LiteLLM Proxy",
            description="Local proxy to inject Langfuse metadata for Claude Code SDK",
        )

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all proxy routes."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "claude-code-litellm-proxy"}

        @self.app.post("/v1/messages")
        async def proxy_messages(request: Request):
            """
            Proxy endpoint for Anthropic Messages API format.

            This is the main endpoint used by Claude Code SDK.
            We keep the Anthropic format by forwarding to /v1/messages.
            """
            # Keep Anthropic format - forward to /v1/messages
            return await self._proxy_request(request, "/v1/messages")

        @self.app.post("/v1/chat/completions")
        async def proxy_chat_completions(request: Request):
            """
            Proxy endpoint for OpenAI Chat Completions API format.

            Fallback for OpenAI-format requests.
            """
            return await self._proxy_request(request, "/v1/chat/completions")

    async def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create the httpx client in the current event loop.

        This ensures the client is created in the same event loop where it will be used,
        avoiding ConnectError when uvicorn runs in a background thread.

        Returns:
            httpx.AsyncClient instance
        """
        if self.client is None:
            # Initialize lock if needed (must be done in async context)
            if self._client_lock is None:
                self._client_lock = asyncio.Lock()

            async with self._client_lock:
                # Double-check after acquiring lock
                if self.client is None:
                    logger.info(
                        "initializing_httpx_client_in_current_event_loop",
                        litellm_base_url=self.litellm_base_url,
                    )
                    # Create client with explicit settings for reliability
                    # Increased timeouts to handle long-running LLM operations
                    self.client = httpx.AsyncClient(
                        timeout=httpx.Timeout(
                            connect=30.0,      # Connection timeout (increased for slow networks)
                            read=600.0,        # Read timeout (10 minutes for long operations)
                            write=60.0,        # Write timeout
                            pool=60.0,         # Pool timeout (increased to avoid pool exhaustion)
                        ),
                        limits=httpx.Limits(
                            max_keepalive_connections=50,  # Increased for better reuse
                            max_connections=200,           # Increased for high concurrency
                        ),
                        follow_redirects=True,
                    )
        return self.client

    async def cleanup(self):
        """Clean up HTTP client resources."""
        if self.client is not None:
            try:
                await self.client.aclose()
                logger.info("httpx_client_closed")
                self.client = None
            except Exception as e:
                logger.error(
                    "httpx_client_close_failed",
                    error=str(e),
                    error_type=type(e).__name__
                )

    async def _proxy_request(self, request: Request, path: str) -> Response:
        """
        Proxy a request to the real LiteLLM proxy with metadata injection.

        Args:
            request: Incoming FastAPI request
            path: API path to forward to

        Returns:
            Response from LiteLLM proxy
        """
        # Get or create client in current event loop
        client = await self._get_client()

        try:
            # Parse request body
            body = await request.json()

            # CRITICAL: Override model if KUBIYA_MODEL_OVERRIDE is set
            # This ensures the explicit model from CLI --model flag takes precedence
            model_override = os.environ.get("KUBIYA_MODEL_OVERRIDE")
            if model_override:
                original_model = body.get("model")
                body["model"] = model_override
                logger.info(
                    "model_override_applied_in_proxy",
                    original_model=original_model,
                    overridden_model=model_override,
                    path=path,
                    note="CLI --model flag or KUBIYA_MODEL env var is active"
                )

            # Extract execution_id from custom header, or use current execution
            execution_id = request.headers.get("X-Execution-ID")

            if not execution_id:
                # Try to get current execution ID
                execution_id = _context_store.get_current_execution_id()

            if not execution_id:
                # Fallback: try to get any valid execution context
                # This handles sub-agent requests when _current_execution was overwritten
                execution_id = _context_store.get_any_valid_execution_id()
                if execution_id:
                    logger.debug(
                        "using_fallback_execution_id",
                        execution_id=execution_id[:8] if execution_id else None,
                        path=path,
                    )

            if not execution_id:
                # Still no execution_id - this is unexpected but not fatal
                # Log at debug level since this may happen during proxy startup/shutdown
                logger.debug(
                    "no_execution_id_available",
                    path=path,
                    note="Cannot inject Langfuse metadata - no execution context found"
                )

            if execution_id:
                # Get execution context and build metadata
                context = _context_store.get_context(execution_id)

                if context:
                    metadata = build_langfuse_metadata(context)

                    # For Anthropic format, we need to be more explicit with Langfuse fields
                    # LiteLLM looks for specific fields in specific places

                    # 1. Set 'user' at top level (works with both formats)
                    body["user"] = metadata.get("trace_user_id")

                    # 2. Initialize metadata dict
                    if "metadata" not in body:
                        body["metadata"] = {}

                    # 3. Put Langfuse fields with explicit naming that LiteLLM recognizes
                    # Based on LiteLLM source, these specific keys are extracted for Langfuse
                    body["metadata"]["generation_name"] = metadata.get("trace_name", "agent-chat")
                    body["metadata"]["trace_name"] = metadata.get("trace_name", "agent-chat")
                    body["metadata"]["trace_id"] = metadata.get("trace_id")
                    body["metadata"]["session_id"] = metadata.get("session_id")
                    body["metadata"]["trace_user_id"] = metadata.get("trace_user_id")
                    body["metadata"]["user_id"] = metadata.get("trace_user_id")

                    # Additional context metadata
                    body["metadata"]["agent_id"] = metadata.get("agent_id")
                    body["metadata"]["agent_name"] = metadata.get("agent_name")
                    body["metadata"]["organization_id"] = metadata.get("organization_id")
                    body["metadata"]["user_email"] = metadata.get("user_email")
                    body["metadata"]["model"] = metadata.get("model")

                    logger.debug(
                        "metadata_injected_into_request",
                        execution_id=execution_id[:8],
                        path=path,
                        user_field=body.get("user"),
                        metadata_keys=list(metadata.keys()),
                        trace_user_id=metadata.get("trace_user_id"),
                        trace_id=metadata.get("trace_id"),
                        session_id=metadata.get("session_id"),
                        trace_name=metadata.get("trace_name"),
                    )
                else:
                    logger.warning(
                        "no_context_found_for_execution",
                        execution_id=execution_id[:8] if execution_id else "unknown",
                        path=path,
                    )

            # Build forwarding URL (keep same endpoint - don't convert formats)
            forward_url = f"{self.litellm_base_url}{path}"

            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.litellm_api_key}",
                "Content-Type": "application/json",
            }

            # Add Langfuse metadata as custom headers (LiteLLM recognizes these)
            if execution_id:
                context = _context_store.get_context(execution_id)
                if context:
                    metadata = build_langfuse_metadata(context)

                    # LiteLLM extracts Langfuse fields from these custom headers
                    headers["X-Langfuse-Trace-Id"] = metadata.get("trace_id", "")
                    headers["X-Langfuse-Session-Id"] = metadata.get("session_id", "")
                    headers["X-Langfuse-User-Id"] = metadata.get("trace_user_id", "")
                    headers["X-Langfuse-Trace-Name"] = metadata.get("trace_name", "agent-chat")

                    # Additional metadata as JSON in custom header
                    import json
                    extra_metadata = {
                        "agent_id": metadata.get("agent_id"),
                        "agent_name": metadata.get("agent_name"),
                        "organization_id": metadata.get("organization_id"),
                        "user_email": metadata.get("user_email"),
                    }
                    headers["X-Langfuse-Metadata"] = json.dumps(extra_metadata)

                    logger.debug(
                        "langfuse_headers_added",
                        execution_id=execution_id[:8],
                        trace_id=metadata.get("trace_id", ""),
                        session_id=metadata.get("session_id", ""),
                    )

            # Copy relevant headers from original request
            for header in ["X-Request-ID", "User-Agent"]:
                if header.lower() in request.headers:
                    headers[header] = request.headers[header.lower()]

            # Check if streaming is requested
            is_streaming = body.get("stream", False)

            if is_streaming:
                # Handle streaming response
                logger.info(
                    "starting_streaming_request",
                    url=forward_url,
                    model=body.get("model", "unknown"),
                    execution_id=execution_id[:8] if execution_id else "unknown",
                )
                return await self._proxy_streaming_request(client, forward_url, body, headers)
            else:
                # Handle non-streaming response
                response = await client.post(
                    forward_url,
                    json=body,
                    headers=headers,
                )

                logger.debug(
                    "litellm_request_completed",
                    status_code=response.status_code,
                    path=path,
                    execution_id=execution_id[:8] if execution_id else None,
                )

                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )

        except httpx.ConnectError as e:
            logger.error(
                "litellm_proxy_connection_error",
                error=str(e),
                error_type=type(e).__name__,
                path=path,
                forward_url=forward_url,
                litellm_base_url=self.litellm_base_url,
                message="Failed to connect to LiteLLM proxy - check network connectivity and URL",
            )
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to LiteLLM proxy at {self.litellm_base_url}: {str(e)}"
            )

        except httpx.HTTPError as e:
            logger.error(
                "litellm_proxy_http_error",
                error=str(e),
                error_type=type(e).__name__,
                path=path,
                forward_url=forward_url,
            )
            raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")

        except Exception as e:
            logger.error(
                "litellm_proxy_error",
                error=str(e),
                error_type=type(e).__name__,
                path=path,
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=f"Internal proxy error: {str(e)}")

    async def _proxy_streaming_request(
        self, client: httpx.AsyncClient, url: str, body: Dict[str, Any], headers: Dict[str, str]
    ) -> StreamingResponse:
        """
        Proxy a streaming request to LiteLLM with robust error handling.

        Args:
            client: httpx AsyncClient instance
            url: Forward URL
            body: Request body
            headers: Request headers

        Returns:
            StreamingResponse that forwards chunks from LiteLLM

        Raises:
            HTTPException: On connection or streaming errors
        """
        async def stream_generator():
            """Generator that yields chunks from LiteLLM with error handling."""
            try:
                # Use explicit timeout for streaming to ensure long operations work
                stream_timeout = httpx.Timeout(
                    connect=30.0,     # Connection timeout (increased for reliability)
                    read=600.0,       # Read timeout (10 minutes for long operations)
                    write=60.0,       # Write timeout
                    pool=30.0,        # Pool timeout (increased to avoid pool exhaustion)
                )
                async with client.stream(
                    "POST",
                    url,
                    json=body,
                    headers=headers,
                    timeout=stream_timeout,
                ) as response:
                    # Check for HTTP errors before streaming
                    if response.status_code >= 400:
                        error_text = await response.aread()
                        logger.error(
                            "litellm_streaming_http_error",
                            status_code=response.status_code,
                            error=error_text.decode('utf-8', errors='ignore')[:500],
                            url=url,
                        )
                        # Yield error message as SSE event
                        error_msg = f"data: {{\"error\": \"HTTP {response.status_code}: {error_text.decode('utf-8', errors='ignore')[:200]}\"}}\n\n"
                        yield error_msg.encode('utf-8')
                        return

                    # Stream chunks
                    async for chunk in response.aiter_bytes():
                        yield chunk

            except httpx.ConnectError as e:
                logger.error(
                    "litellm_streaming_connection_error",
                    error=str(e),
                    url=url,
                    message="Failed to connect to LiteLLM proxy during streaming",
                )
                # Yield error as SSE event instead of crashing
                error_msg = f"data: {{\"error\": \"Connection failed: {str(e)}\"}}\n\n"
                yield error_msg.encode('utf-8')

            except httpx.TimeoutException as e:
                # Capture detailed timeout info
                error_detail = str(e) or repr(e) or "No error details available"
                logger.error(
                    "litellm_streaming_timeout",
                    error=error_detail,
                    error_type=type(e).__name__,
                    error_args=getattr(e, 'args', []),
                    url=url,
                    model=body.get("model", "unknown"),
                    message="Request timed out during streaming",
                    note="Check network connectivity to LLM proxy or increase timeouts"
                )
                error_msg = f"data: {{\"error\": \"Request timed out ({type(e).__name__}): {error_detail}\"}}\n\n"
                yield error_msg.encode('utf-8')

            except httpx.HTTPError as e:
                logger.error(
                    "litellm_streaming_http_error_general",
                    error=str(e),
                    error_type=type(e).__name__,
                    url=url,
                )
                error_msg = f"data: {{\"error\": \"HTTP error: {str(e)}\"}}\n\n"
                yield error_msg.encode('utf-8')

            except Exception as e:
                logger.error(
                    "litellm_streaming_unexpected_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    url=url,
                    exc_info=True,
                )
                error_msg = f"data: {{\"error\": \"Unexpected error: {str(e)}\"}}\n\n"
                yield error_msg.encode('utf-8')

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
        )


class LiteLLMProxyServer:
    """Manager for running the LiteLLM proxy server in the same process."""

    def __init__(self, port: int = 0):
        """
        Initialize the proxy server.

        Args:
            port: Port to listen on (0 = auto-assign random port)
        """
        self.port = port
        self.actual_port: Optional[int] = None
        self.server_thread: Optional[threading.Thread] = None
        self.app: Optional[LiteLLMProxyApp] = None
        self._started = threading.Event()
        self._shutdown = threading.Event()

    def start(self) -> int:
        """
        Start the proxy server in a background thread.

        Returns:
            The actual port the server is listening on

        Raises:
            RuntimeError: If server fails to start
        """
        # Get LiteLLM configuration
        litellm_base_url = os.getenv("LITELLM_API_BASE", "https://llm-proxy.kubiya.ai")
        litellm_api_key = os.getenv("LITELLM_API_KEY")

        # Check for model override
        model_override = os.getenv("KUBIYA_MODEL_OVERRIDE")

        logger.info(
            "litellm_proxy_server_initializing",
            litellm_base_url=litellm_base_url,
            model_override=model_override,
            has_model_override=bool(model_override),
            note="Model override will be applied to ALL requests" if model_override else "No model override active"
        )

        if not litellm_api_key:
            raise RuntimeError("LITELLM_API_KEY not set")

        # Create proxy app
        self.app = LiteLLMProxyApp(litellm_base_url, litellm_api_key)

        # Auto-assign port if needed
        if self.port == 0:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', 0))
                s.listen(1)
                self.actual_port = s.getsockname()[1]
        else:
            self.actual_port = self.port

        # Start server in background thread
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="LiteLLMProxyServer"
        )
        self.server_thread.start()

        # Wait for server to become ready by checking health endpoint
        import time
        import httpx
        max_wait = 10  # seconds
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                # Try to connect to health endpoint
                with httpx.Client(timeout=1.0) as client:
                    response = client.get(f"http://127.0.0.1:{self.actual_port}/health")
                    if response.status_code == 200:
                        self._started.set()
                        logger.info(
                            "litellm_proxy_server_started",
                            port=self.actual_port,
                            url=f"http://127.0.0.1:{self.actual_port}",
                        )
                        return self.actual_port
            except Exception:
                # Server not ready yet, wait and retry
                time.sleep(0.1)
                continue

        # Timeout waiting for server
        raise RuntimeError("LiteLLM proxy server failed to start within 10 seconds")

    def _run_server(self):
        """Run the uvicorn server (called in background thread)."""
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Create uvicorn config
            config = uvicorn.Config(
                self.app.app,
                host="127.0.0.1",
                port=self.actual_port,
                log_level="error",
                access_log=False,
                loop=loop,
            )
            server = uvicorn.Server(config)

            # Run server
            loop.run_until_complete(server.serve())

        except Exception as e:
            logger.error(
                "litellm_proxy_server_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
        finally:
            # Cleanup HTTP client
            if self.app and self.app.client:
                try:
                    loop.run_until_complete(self.app.cleanup())
                except Exception as cleanup_error:
                    logger.error(
                        "proxy_app_cleanup_failed",
                        error=str(cleanup_error)
                    )

            # Close event loop
            try:
                loop.close()
            except Exception as loop_error:
                logger.error("event_loop_close_failed", error=str(loop_error))

            self._shutdown.set()

    def stop(self):
        """Stop the proxy server and cleanup resources."""
        logger.info("stopping_litellm_proxy_server")
        self._shutdown.set()

        # Give server time to shutdown gracefully
        if self.server_thread:
            self.server_thread.join(timeout=10)

            if self.server_thread.is_alive():
                logger.warning(
                    "proxy_server_thread_still_alive",
                    note="Daemon thread will be terminated by Python at exit"
                )
            else:
                logger.info("proxy_server_thread_stopped")

        logger.info("litellm_proxy_server_stopped")

    def get_base_url(self) -> str:
        """Get the base URL of the proxy server."""
        if not self.actual_port:
            raise RuntimeError("Server not started")
        return f"http://127.0.0.1:{self.actual_port}"


# Singleton instance
_proxy_server: Optional[LiteLLMProxyServer] = None
_proxy_lock = threading.Lock()


def get_proxy_server() -> LiteLLMProxyServer:
    """
    Get or create the singleton proxy server instance.

    Returns:
        LiteLLMProxyServer instance
    """
    global _proxy_server

    with _proxy_lock:
        if _proxy_server is None:
            _proxy_server = LiteLLMProxyServer(port=0)  # Auto-assign port
            _proxy_server.start()

        return _proxy_server


def set_execution_context(execution_id: str, context: Dict[str, Any]):
    """
    Store execution context for metadata injection.

    Call this before starting a Claude Code execution.

    Args:
        execution_id: Execution ID
        context: Context dict with user_id, session_id, agent_id, etc.
    """
    _context_store.set_context(execution_id, context)


def clear_execution_context(
    execution_id: str,
    immediate: bool = False,
    delay_seconds: float = 5.0
):
    """
    Clear execution context after execution completes.

    Args:
        execution_id: Execution ID
        immediate: If True, clear immediately. If False, schedule delayed cleanup.
        delay_seconds: Delay before cleanup (only if immediate=False)
    """
    if immediate:
        _context_store.clear_context(execution_id)
    else:
        _cleanup_scheduler.schedule_cleanup(
            execution_id,
            delay_seconds,
            _context_store
        )


def get_proxy_base_url() -> str:
    """
    Get the base URL of the local proxy server.

    Starts the server if not already running.

    Returns:
        Base URL (e.g., "http://127.0.0.1:8080")
    """
    server = get_proxy_server()
    return server.get_base_url()
