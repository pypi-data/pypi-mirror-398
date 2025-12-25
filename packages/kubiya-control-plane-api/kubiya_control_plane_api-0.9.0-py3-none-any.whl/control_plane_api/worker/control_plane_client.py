"""
Control Plane Client - Clean API for worker to communicate with Control Plane.

This centralizes all HTTP and WebSocket communication between worker and Control Plane,
providing a clean interface for:
- Event streaming (real-time UI updates via WebSocket or HTTP fallback)
- Session persistence (history storage)
- Metadata caching (execution types)
- Skill resolution
- Bi-directional control messages

Usage:
    from control_plane_client import get_control_plane_client

    client = get_control_plane_client()
    await client.start_websocket()  # If WebSocket enabled
    await client.publish_event_async(execution_id, "message_chunk", {...})
    client.persist_session(execution_id, session_id, user_id, messages)
"""

import os
import httpx
import asyncio
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import structlog

logger = structlog.get_logger()


class ControlPlaneClient:
    """Client for communicating with the Control Plane API from workers."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        websocket_enabled: bool = False,
        websocket_url: Optional[str] = None,
        worker_id: Optional[str] = None,
        event_bus_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Control Plane client.

        Args:
            base_url: Control Plane URL (e.g., http://localhost:8000)
            api_key: Kubiya API key for authentication
            websocket_enabled: Whether WebSocket is enabled
            websocket_url: WebSocket URL if enabled
            worker_id: Worker ID for WebSocket connection
            event_bus_config: Optional event bus configuration dict
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Authorization": f"UserKey {api_key}"}
        self.worker_id = worker_id

        # Event bus manager for multi-provider support
        self.event_bus_manager = None
        if event_bus_config:
            try:
                from control_plane_api.app.lib.event_bus.manager import (
                    EventBusManager,
                    EventBusManagerConfig,
                )
                from control_plane_api.app.lib.event_bus.providers.http_provider import HTTPConfig
                from control_plane_api.app.lib.event_bus.providers.redis_provider import RedisConfig
                from control_plane_api.app.lib.event_bus.providers.websocket_provider import WebSocketConfig

                # Parse config dicts into config objects
                parsed_config = {}

                if "http" in event_bus_config and event_bus_config["http"]:
                    parsed_config["http"] = HTTPConfig(**event_bus_config["http"])

                if "redis" in event_bus_config and event_bus_config["redis"]:
                    parsed_config["redis"] = RedisConfig(**event_bus_config["redis"])

                if "websocket" in event_bus_config and event_bus_config["websocket"]:
                    parsed_config["websocket"] = WebSocketConfig(**event_bus_config["websocket"])

                if "nats" in event_bus_config and event_bus_config["nats"]:
                    try:
                        from control_plane_api.app.lib.event_bus.providers.nats_provider import NATSConfig
                        parsed_config["nats"] = NATSConfig(**event_bus_config["nats"])
                    except ImportError:
                        logger.warning("nats_provider_not_installed", message="Install with: pip install kubiya-control-plane-api[nats]")

                manager_config = EventBusManagerConfig(**parsed_config)
                self.event_bus_manager = EventBusManager(manager_config)
                logger.info(
                    "worker_event_bus_initialized",
                    worker_id=worker_id[:8] if worker_id else "unknown",
                    providers=list(parsed_config.keys())
                )
            except ImportError as e:
                logger.warning(
                    "event_bus_dependencies_missing",
                    error=str(e),
                    message="Install event bus dependencies with: pip install kubiya-control-plane-api[event-bus]"
                )
            except Exception as e:
                logger.error(
                    "worker_event_bus_init_failed",
                    error=str(e),
                    worker_id=worker_id[:8] if worker_id else "unknown"
                )

        # Thread-local storage for event loop reuse in sync context
        # This prevents creating a new event loop per publish_event() call
        self._thread_local = threading.local()

        # Use BOTH sync and async clients for different use cases
        # Sync client for backwards compatibility with non-async code
        self._client = httpx.Client(
            timeout=httpx.Timeout(30.0, connect=5.0, read=30.0, write=10.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

        # Async client for streaming/real-time operations
        # Longer read timeout to handle streaming scenarios
        self._async_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=5.0, read=60.0, write=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

        # WebSocket client for persistent connection
        self.websocket_client: Optional[Any] = None

        # Initialize WebSocket client if enabled and environment supports it
        if websocket_enabled and websocket_url and worker_id:
            from control_plane_api.worker.utils.environment import should_use_websocket

            if should_use_websocket():
                from control_plane_api.worker.websocket_client import WorkerWebSocketClient

                self.websocket_client = WorkerWebSocketClient(
                    worker_id=worker_id,
                    websocket_url=websocket_url,
                    api_key=api_key,
                    on_control_message=self._handle_control_message
                )
                logger.info("websocket_client_initialized", worker_id=worker_id[:8])
            else:
                logger.info("websocket_skipped_serverless_environment")

    def __del__(self):
        """Close the HTTP clients on cleanup."""
        try:
            self._client.close()
        except:
            pass
        # Async client cleanup happens via context manager or explicit close

    def _get_thread_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        Get or create a persistent event loop for the current thread.

        This reuses the same event loop for all publish_event() calls within
        a thread, preventing resource leaks and "await wasn't used with future"
        errors that occur when creating a new loop per call.

        Returns:
            The thread-local event loop
        """
        if not hasattr(self._thread_local, 'loop') or self._thread_local.loop is None or self._thread_local.loop.is_closed():
            self._thread_local.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._thread_local.loop)
            logger.debug(
                "created_thread_local_event_loop",
                thread_id=threading.current_thread().ident,
                thread_name=threading.current_thread().name,
            )
        return self._thread_local.loop

    def close_thread_event_loop(self):
        """
        Close the thread-local event loop if it exists.

        Call this when the thread is done publishing events (e.g., at end of
        Agno streaming execution) to properly clean up resources.
        """
        if hasattr(self._thread_local, 'loop') and self._thread_local.loop is not None:
            loop = self._thread_local.loop
            if not loop.is_closed():
                try:
                    # Cancel any pending tasks
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()

                    # Run loop until all tasks are cancelled
                    if pending:
                        loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )

                    loop.close()
                    logger.debug(
                        "closed_thread_local_event_loop",
                        thread_id=threading.current_thread().ident,
                        pending_tasks_cancelled=len(pending) if pending else 0,
                    )
                except Exception as e:
                    logger.warning(
                        "thread_event_loop_close_error",
                        error=str(e),
                        thread_id=threading.current_thread().ident,
                    )
            self._thread_local.loop = None

    async def initialize_event_bus(self):
        """Initialize event bus manager asynchronously with connection testing."""
        if self.event_bus_manager and not self.event_bus_manager.is_initialized():
            try:
                await self.event_bus_manager.initialize()

                # Test provider connectivity (especially Redis)
                provider_health = {}
                for provider_name, provider in self.event_bus_manager.providers.items():
                    try:
                        health = await provider.health_check()
                        provider_health[provider_name] = health.get("healthy", False)
                    except Exception as e:
                        logger.warning(
                            "provider_health_check_failed",
                            provider=provider_name,
                            error=str(e),
                            worker_id=self.worker_id[:8] if self.worker_id else "unknown"
                        )
                        provider_health[provider_name] = False

                # Log provider status
                healthy_providers = [name for name, healthy in provider_health.items() if healthy]
                unhealthy_providers = [name for name, healthy in provider_health.items() if not healthy]

                if healthy_providers:
                    logger.info(
                        "worker_event_bus_ready",
                        worker_id=self.worker_id[:8] if self.worker_id else "unknown",
                        providers=self.event_bus_manager.get_provider_names(),
                        healthy_providers=healthy_providers,
                        unhealthy_providers=unhealthy_providers if unhealthy_providers else None
                    )

                    # If Redis failed but was configured, log warning about falling back to HTTP
                    if "redis" in unhealthy_providers:
                        logger.warning(
                            "redis_connection_failed_will_fallback",
                            worker_id=self.worker_id[:8] if self.worker_id else "unknown",
                            message="Redis unavailable, will fallback to HTTP endpoint for event streaming"
                        )
                else:
                    logger.warning(
                        "all_event_bus_providers_unhealthy",
                        worker_id=self.worker_id[:8] if self.worker_id else "unknown",
                        providers=list(provider_health.keys()),
                        message="Will fallback to HTTP endpoint for event streaming"
                    )

            except Exception as e:
                logger.error(
                    "worker_event_bus_init_failed",
                    error=str(e),
                    worker_id=self.worker_id[:8] if self.worker_id else "unknown"
                )
                # Don't fail initialization - just won't use event bus
                self.event_bus_manager = None

    async def aclose(self):
        """Async cleanup for async client and event bus."""
        try:
            # Shutdown event bus first
            if self.event_bus_manager:
                await self.event_bus_manager.shutdown()
                logger.info("worker_event_bus_shutdown", worker_id=self.worker_id[:8] if self.worker_id else "unknown")

            # Then close async client
            await self._async_client.aclose()
        except:
            pass

    async def start_websocket(self):
        """Start WebSocket client if enabled."""
        if self.websocket_client:
            await self.websocket_client.start()
            logger.info("websocket_started")

    async def stop_websocket(self):
        """Stop WebSocket client if running."""
        if self.websocket_client:
            await self.websocket_client.stop()
            logger.info("websocket_stopped")

    def _get_running_loop_safe(self) -> Optional[asyncio.AbstractEventLoop]:
        """
        Safely get the running event loop if one exists.

        Returns:
            The running event loop, or None if not in an async context
        """
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            # No running loop in this thread
            return None

    def publish_event(
        self,
        execution_id: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Publish a streaming event for real-time UI updates (SYNC version).

        NOTE: This is the BLOCKING version. For real-time streaming,
        use publish_event_async() instead to avoid blocking the event loop.

        IMPORTANT: This method now auto-detects if it's being called from within
        an async context (like Claude Code SDK hooks) and schedules tasks
        appropriately to avoid "Cannot run the event loop while another loop
        is running" errors.

        Strategy (in order):
        1. Try Event Bus (multi-provider) if configured [DEFAULT: includes Redis for fast path]
        2. Try WebSocket if connected
        3. Fallback to HTTP endpoint

        Args:
            execution_id: Execution ID
            event_type: Event type (message_chunk, tool_started, etc.)
            data: Event payload

        Returns:
            True if successful, False otherwise
        """
        # Check if we're in an async context
        running_loop = self._get_running_loop_safe()
        in_async_context = running_loop is not None

        # Strategy 1: Try Event Bus first (Redis is auto-configured by default)
        if self.event_bus_manager and self.event_bus_manager.is_initialized():
            metadata = {}
            if self.worker_id:
                metadata["worker_id"] = self.worker_id

            if in_async_context:
                # We're in an async context - schedule task directly without creating coroutine first
                try:
                    # Create and schedule the task in one go
                    coro = self.event_bus_manager.publish_event(
                        execution_id=execution_id,
                        event_type=event_type,
                        data=data,
                        metadata=metadata
                    )
                    task = running_loop.create_task(coro)

                    # Add error callback
                    def handle_task_error(t):
                        try:
                            exc = t.exception()
                            if exc:
                                logger.warning(
                                    "background_event_bus_task_error",
                                    error=str(exc),
                                    execution_id=execution_id[:8],
                                    event_type=event_type,
                                )
                        except asyncio.CancelledError:
                            pass
                        except Exception:
                            pass

                    task.add_done_callback(handle_task_error)
                    logger.debug(
                        "worker_event_scheduled_via_event_bus_async",
                        execution_id=execution_id[:8],
                        event_type=event_type,
                        note="Task scheduled in running event loop"
                    )
                    return True
                except Exception as e:
                    logger.warning(
                        "failed_to_schedule_event_bus_task",
                        error=str(e),
                        execution_id=execution_id[:8],
                        event_type=event_type,
                    )
                    # Fall through to fallback strategies
            else:
                # Not in async context - use blocking execution
                try:
                    loop = self._get_thread_event_loop()
                    coro = self.event_bus_manager.publish_event(
                        execution_id=execution_id,
                        event_type=event_type,
                        data=data,
                        metadata=metadata
                    )

                    try:
                        results = loop.run_until_complete(coro)
                    except RuntimeError as re:
                        # Handle nested event loop case
                        if "Cannot run the event loop while another loop is running" in str(re):
                            logger.warning(
                                "nested_event_loop_detected",
                                execution_id=execution_id[:8],
                                event_type=event_type,
                                note="Skipping event bus publish due to nested loop"
                            )
                            coro.close()
                            # Fall through to fallback strategies
                            results = None
                        else:
                            coro.close()
                            raise

                    if results is not None:
                        # Success if any provider succeeded
                        success_count = sum(1 for success in results.values() if success)
                        if success_count > 0:
                            logger.debug(
                                "worker_event_published_via_event_bus_sync",
                                execution_id=execution_id[:8],
                                event_type=event_type,
                                success_count=success_count,
                                total_providers=len(results)
                            )
                            return True
                        else:
                            logger.warning(
                                "worker_event_bus_all_providers_failed_fallback_sync",
                                execution_id=execution_id[:8],
                                event_type=event_type,
                                results=results
                            )
                            # Fall through to WebSocket/HTTP fallback
                except Exception as e:
                    logger.error(
                        "worker_event_bus_publish_error_sync",
                        error=str(e),
                        execution_id=execution_id[:8],
                        event_type=event_type
                    )
                    # Fall through to WebSocket/HTTP fallback

        # Strategy 2: Try WebSocket if available and connected
        if self.websocket_client and self.websocket_client.is_connected():
            if in_async_context:
                # Schedule WebSocket send as a task
                try:
                    coro = self.websocket_client.send_event(execution_id, event_type, data)
                    task = running_loop.create_task(coro)
                    logger.debug(
                        "worker_event_scheduled_via_websocket_async",
                        execution_id=execution_id[:8],
                        event_type=event_type
                    )
                    return True
                except Exception as e:
                    logger.warning(
                        "failed_to_schedule_websocket_task",
                        error=str(e),
                        execution_id=execution_id[:8],
                    )
                    # Fall through to HTTP fallback
            else:
                # WebSocket send_event is async, need to run it in event loop
                try:
                    loop = self._get_thread_event_loop()
                    coro = self.websocket_client.send_event(execution_id, event_type, data)

                    try:
                        success = loop.run_until_complete(coro)
                    except RuntimeError as re:
                        if "Cannot run the event loop while another loop is running" in str(re):
                            coro.close()
                            success = None
                        else:
                            coro.close()
                            raise

                    if success:
                        logger.debug(
                            "worker_event_published_via_websocket_sync",
                            execution_id=execution_id[:8],
                            event_type=event_type
                        )
                        return True

                    # Queue full - fallback to HTTP immediately
                    if success is not None:
                        logger.warning("websocket_queue_full_fallback_http_sync", execution_id=execution_id[:8])
                except Exception as e:
                    logger.error(
                        "websocket_publish_error_sync",
                        error=str(e),
                        execution_id=execution_id[:8]
                    )
                    # Fall through to HTTP fallback

        # Strategy 3: Fallback to HTTP
        logger.debug(
            "worker_event_publishing_via_http_fallback_sync",
            execution_id=execution_id[:8],
            event_type=event_type
        )

        try:
            # Sanitize data to remove non-JSON-serializable objects
            import json
            import asyncio

            def sanitize_value(val):
                """Remove non-JSON-serializable objects"""
                try:
                    # Fast path for JSON primitives
                    if val is None or isinstance(val, (bool, int, float, str)):
                        return val

                    # Check type name to avoid event loop issues
                    type_name = type(val).__name__
                    type_module = str(type(val).__module__)

                    # Remove asyncio objects by checking module and type name
                    if 'asyncio' in type_module or any(x in type_name for x in ['Event', 'Lock', 'Queue', 'Semaphore', 'Condition']):
                        return f"<{type_name}>"
                    elif isinstance(val, dict):
                        return {k: sanitize_value(v) for k, v in val.items()}
                    elif isinstance(val, (list, tuple)):
                        return [sanitize_value(v) for v in val]
                    else:
                        try:
                            json.dumps(val)
                            return val
                        except (TypeError, ValueError, RuntimeError):
                            # RuntimeError catches "bound to different event loop" errors
                            return f"<non-serializable: {type_name}>"
                except Exception as e:
                    # Catch-all for ANY errors during sanitization itself
                    # Do NOT attempt to inspect the value here - it may cause event loop errors
                    return "<sanitization-error>"

            sanitized_data = sanitize_value(data)

            url = f"{self.base_url}/api/v1/executions/{execution_id}/events"
            payload = {
                "event_type": event_type,
                "data": sanitized_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Double-check: Try to serialize the payload before sending
            try:
                json.dumps(payload)
            except Exception as serialize_err:
                logger.error(
                    "payload_serialization_test_failed",
                    execution_id=execution_id[:8],
                    event_type=event_type,
                    error=str(serialize_err)[:200],
                )
                # If we can't serialize it, don't even try to send
                return False

            response = self._client.post(url, json=payload, headers=self.headers)

            if response.status_code not in (200, 202):
                logger.warning(
                    "event_publish_failed",
                    status=response.status_code,
                    execution_id=execution_id[:8],
                    event_type=event_type,
                )
                return False

            return True

        except Exception as e:
            # Sanitize error message to avoid serialization issues
            import re
            error_str = str(e) or "(empty)"
            error_type = type(e).__name__
            # Remove asyncio object references that cause serialization errors
            error_str = re.sub(r'<asyncio\.\w+\.\w+ object at 0x[0-9a-f]+ \[[\w\s]+\]>', '[asyncio-object]', error_str)

            logger.warning(
                "event_publish_error",
                error=error_str[:500],  # Truncate to prevent huge error messages
                error_type=error_type,
                execution_id=execution_id[:8],
                event_type=event_type,
            )
            return False

    async def publish_event_async(
        self,
        execution_id: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Publish a streaming event for real-time UI updates (ASYNC version).

        Strategy (in order):
        1. Try Event Bus (multi-provider) if configured [DEFAULT: includes Redis for fast path]
        2. Try WebSocket if connected
        3. Fallback to HTTP endpoint (control plane handles Redis internally)

        By default, workers receive Redis credentials during registration and
        publish directly to Redis (fast path). If Redis is unavailable, falls
        back to HTTP endpoint.

        Args:
            execution_id: Execution ID
            event_type: Event type (message_chunk, tool_started, etc.)
            data: Event payload

        Returns:
            True if at least one provider succeeded, False otherwise
        """
        # Strategy 1: Try Event Bus first (Redis is auto-configured by default)
        if self.event_bus_manager and self.event_bus_manager.is_initialized():
            try:
                metadata = {}
                if self.worker_id:
                    metadata["worker_id"] = self.worker_id

                results = await self.event_bus_manager.publish_event(
                    execution_id=execution_id,
                    event_type=event_type,
                    data=data,
                    metadata=metadata
                )

                # Success if any provider succeeded
                success_count = sum(1 for success in results.values() if success)
                if success_count > 0:
                    logger.debug(
                        "worker_event_published_via_event_bus",
                        execution_id=execution_id[:8],
                        event_type=event_type,
                        success_count=success_count,
                        total_providers=len(results)
                    )
                    return True
                else:
                    logger.warning(
                        "worker_event_bus_all_providers_failed_fallback",
                        execution_id=execution_id[:8],
                        event_type=event_type,
                        results=results
                    )
                    # Fall through to WebSocket/HTTP fallback
            except Exception as e:
                logger.error(
                    "worker_event_bus_publish_error",
                    error=str(e),
                    execution_id=execution_id[:8],
                    event_type=event_type
                )
                # Fall through to WebSocket/HTTP fallback

        # Strategy 2: Try WebSocket if available and connected
        if self.websocket_client and self.websocket_client.is_connected():
            success = await self.websocket_client.send_event(execution_id, event_type, data)
            if success:
                logger.debug(
                    "worker_event_published_via_websocket",
                    execution_id=execution_id[:8],
                    event_type=event_type
                )
                return True

            # Queue full - fallback to HTTP immediately
            logger.warning("websocket_queue_full_fallback_http", execution_id=execution_id[:8])

        # Strategy 3: Fallback to HTTP
        logger.debug(
            "worker_event_publishing_via_http_fallback",
            execution_id=execution_id[:8],
            event_type=event_type
        )
        return await self._publish_event_http(execution_id, event_type, data)

    async def _publish_event_http(
        self,
        execution_id: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Publish event via HTTP (internal method for fallback).

        Args:
            execution_id: Execution ID
            event_type: Event type
            data: Event payload

        Returns:
            True if successful, False otherwise
        """
        try:
            # Sanitize data to remove non-JSON-serializable objects
            import json
            import asyncio

            def sanitize_value(val):
                """Remove non-JSON-serializable objects"""
                try:
                    # Fast path for JSON primitives
                    if val is None or isinstance(val, (bool, int, float, str)):
                        return val

                    # Check type name to avoid event loop issues
                    type_name = type(val).__name__
                    type_module = str(type(val).__module__)

                    # Remove asyncio objects by checking module and type name
                    if 'asyncio' in type_module or any(x in type_name for x in ['Event', 'Lock', 'Queue', 'Semaphore', 'Condition']):
                        return f"<{type_name}>"
                    elif isinstance(val, dict):
                        return {k: sanitize_value(v) for k, v in val.items()}
                    elif isinstance(val, (list, tuple)):
                        return [sanitize_value(v) for v in val]
                    else:
                        try:
                            json.dumps(val)
                            return val
                        except (TypeError, ValueError, RuntimeError):
                            # RuntimeError catches "bound to different event loop" errors
                            return f"<non-serializable: {type_name}>"
                except Exception as e:
                    # Catch-all for ANY errors during sanitization itself
                    # Do NOT attempt to inspect the value here - it may cause event loop errors
                    return "<sanitization-error>"

            sanitized_data = sanitize_value(data)

            url = f"{self.base_url}/api/v1/executions/{execution_id}/events"
            payload = {
                "event_type": event_type,
                "data": sanitized_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Double-check: Try to serialize the payload before sending
            try:
                json.dumps(payload)
            except Exception as serialize_err:
                logger.error(
                    "payload_serialization_test_failed",
                    execution_id=execution_id[:8],
                    event_type=event_type,
                    error=str(serialize_err)[:200],
                )
                # If we can't serialize it, don't even try to send
                return False

            response = await self._async_client.post(url, json=payload, headers=self.headers)

            if response.status_code not in (200, 202):
                logger.warning(
                    "event_publish_failed",
                    status=response.status_code,
                    execution_id=execution_id[:8],
                    event_type=event_type,
                )
                return False

            return True

        except Exception as e:
            # Sanitize error message to avoid serialization issues
            import re
            error_str = str(e) or "(empty)"
            error_type = type(e).__name__
            # Remove asyncio object references that cause serialization errors
            error_str = re.sub(r'<asyncio\.\w+\.\w+ object at 0x[0-9a-f]+ \[[\w\s]+\]>', '[asyncio-object]', error_str)

            logger.warning(
                "event_publish_error",
                error=error_str[:500],  # Truncate to prevent huge error messages
                error_type=error_type,
                execution_id=execution_id[:8],
                event_type=event_type,
            )
            return False

    def cache_metadata(
        self,
        execution_id: str,
        execution_type: str,
    ) -> bool:
        """
        Cache execution metadata in Redis for fast SSE lookups.

        This eliminates the need for database queries on every SSE connection.

        Args:
            execution_id: Execution ID
            execution_type: "AGENT" or "TEAM"

        Returns:
            True if successful, False otherwise
        """
        return self.publish_event(
            execution_id=execution_id,
            event_type="metadata",
            data={"execution_type": execution_type},
        )

    def get_session(
        self,
        execution_id: str,
        session_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve session history from Control Plane database.

        This loads conversation history so workers can restore context
        across multiple execution turns.

        Args:
            execution_id: Execution ID
            session_id: Session ID (defaults to execution_id if not provided)

        Returns:
            Dict with session data including messages, or None if not found
        """
        try:
            session_id = session_id or execution_id
            url = f"{self.base_url}/api/v1/executions/{execution_id}/session"

            response = self._client.get(url, headers=self.headers)

            if response.status_code == 200:
                session_data = response.json()
                logger.info(
                    "session_loaded",
                    execution_id=execution_id[:8],
                    message_count=len(session_data.get("messages", [])),
                )
                return session_data
            elif response.status_code == 404:
                logger.info(
                    "session_not_found",
                    execution_id=execution_id[:8],
                )
                return None
            else:
                logger.warning(
                    "session_load_failed",
                    status=response.status_code,
                    execution_id=execution_id[:8],
                )
                return None

        except Exception as e:
            logger.warning(
                "session_load_error",
                error=str(e),
                execution_id=execution_id[:8],
            )
            return None

    def persist_session(
        self,
        execution_id: str,
        session_id: str,
        user_id: Optional[str],
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Persist session history to Control Plane database.

        This ensures history is available even when worker is offline.

        Args:
            execution_id: Execution ID
            session_id: Session ID
            user_id: User ID
            messages: List of session messages
            metadata: Optional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/executions/{execution_id}/session"
            payload = {
                "session_id": session_id,
                "user_id": user_id,
                "messages": messages,
                "metadata": metadata or {},
            }

            response = self._client.post(url, json=payload, headers=self.headers)

            if response.status_code in (200, 201):
                logger.info(
                    "session_persisted",
                    execution_id=execution_id[:8],
                    message_count=len(messages),
                )
                return True
            else:
                logger.warning(
                    "session_persistence_failed",
                    status=response.status_code,
                    execution_id=execution_id[:8],
                )
                return False

        except Exception as e:
            logger.warning(
                "session_persistence_error",
                error=str(e),
                execution_id=execution_id[:8],
            )
            return False

    def get_skills(
        self,
        agent_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch resolved skills for an agent from Control Plane.

        This endpoint returns skills merged from all layers:
        - All agent environments (many-to-many)
        - Team skills (if agent has team)
        - All team environments (many-to-many)
        - Agent's own skills

        Args:
            agent_id: Agent ID

        Returns:
            List of skill configurations with source and inheritance info
        """
        try:
            url = f"{self.base_url}/api/v1/skills/associations/agents/{agent_id}/skills/resolved"
            response = self._client.get(url, headers=self.headers)

            if response.status_code == 200:
                skills = response.json()
                logger.info(
                    "skills_fetched",
                    agent_id=agent_id[:8],
                    skill_count=len(skills),
                )
                return skills
            else:
                logger.warning(
                    "skills_fetch_failed",
                    status=response.status_code,
                    agent_id=agent_id[:8],
                )
                return []

        except Exception as e:
            logger.warning(
                "skills_fetch_error",
                error=str(e),
                agent_id=agent_id[:8],
            )
            return []

    def get_team_skills(
        self,
        team_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch resolved skills for a team from Control Plane.

        This endpoint returns skills merged from all layers:
        - All team environments (many-to-many)
        - Team's own skills

        Args:
            team_id: Team ID

        Returns:
            List of skill configurations with source and inheritance info
        """
        try:
            url = f"{self.base_url}/api/v1/skills/associations/teams/{team_id}/skills/resolved"
            response = self._client.get(url, headers=self.headers)

            if response.status_code == 200:
                skills = response.json()
                logger.info(
                    "team_skills_fetched",
                    team_id=team_id[:8],
                    skill_count=len(skills),
                )
                return skills
            else:
                logger.warning(
                    "team_skills_fetch_failed",
                    status=response.status_code,
                    team_id=team_id[:8],
                )
                return []

        except Exception as e:
            logger.warning(
                "team_skills_fetch_error",
                error=str(e),
                team_id=team_id[:8],
            )
            return []

    def get_agent_execution_environment(
        self,
        agent_id: str,
    ) -> Dict[str, str]:
        """
        Fetch resolved execution environment for an agent from Control Plane.

        This endpoint returns a fully resolved environment variable dict with:
        - Custom env vars from agent configuration
        - Secret values (resolved from Kubiya vault)
        - Integration tokens (resolved and mapped to env var names like GH_TOKEN, JIRA_TOKEN)

        Args:
            agent_id: Agent ID

        Returns:
            Dict of environment variables ready to inject into agent execution
        """
        try:
            url = f"{self.base_url}/api/v1/execution-environment/agents/{agent_id}/resolved"
            response = self._client.get(url, headers=self.headers)

            if response.status_code == 200:
                env_vars = response.json()
                logger.info(
                    "agent_execution_environment_fetched",
                    agent_id=agent_id[:8],
                    env_var_count=len(env_vars),
                    env_var_keys=list(env_vars.keys()),
                )
                return env_vars
            else:
                logger.warning(
                    "agent_execution_environment_fetch_failed",
                    status=response.status_code,
                    agent_id=agent_id[:8],
                )
                return {}

        except Exception as e:
            logger.warning(
                "agent_execution_environment_fetch_error",
                error=str(e),
                agent_id=agent_id[:8],
            )
            return {}

    def get_team_execution_environment(
        self,
        team_id: str,
    ) -> Dict[str, str]:
        """
        Fetch resolved execution environment for a team from Control Plane.

        This endpoint returns a fully resolved environment variable dict with:
        - Custom env vars from team configuration
        - Secret values (resolved from Kubiya vault)
        - Integration tokens (resolved and mapped to env var names like GH_TOKEN, JIRA_TOKEN)

        Args:
            team_id: Team ID

        Returns:
            Dict of environment variables ready to inject into team execution
        """
        try:
            url = f"{self.base_url}/api/v1/execution-environment/teams/{team_id}/resolved"
            response = self._client.get(url, headers=self.headers)

            if response.status_code == 200:
                env_vars = response.json()
                logger.info(
                    "team_execution_environment_fetched",
                    team_id=team_id[:8],
                    env_var_count=len(env_vars),
                    env_var_keys=list(env_vars.keys()),
                )
                return env_vars
            else:
                logger.warning(
                    "team_execution_environment_fetch_failed",
                    status=response.status_code,
                    team_id=team_id[:8],
                )
                return {}

        except Exception as e:
            logger.warning(
                "team_execution_environment_fetch_error",
                error=str(e),
                team_id=team_id[:8],
            )
            return {}

    async def create_job_execution_record(
        self,
        execution_id: str,
        job_id: Optional[str],
        organization_id: str,
        entity_type: str,
        entity_id: Optional[str],
        prompt: str,
        trigger_type: str,
        trigger_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create execution and job_executions records for a scheduled job.

        This calls the Control Plane API to create execution records
        instead of directly accessing Supabase.

        Args:
            execution_id: Execution ID
            job_id: Job ID (optional)
            organization_id: Organization ID
            entity_type: "agent" or "team"
            entity_id: Agent or team ID
            prompt: Prompt text
            trigger_type: "cron", "webhook", or "manual"
            trigger_metadata: Additional trigger metadata

        Returns:
            Dict with execution_id, status, and created_at
        """
        try:
            url = f"{self.base_url}/api/v1/executions/create"
            payload = {
                "execution_id": execution_id,
                "job_id": job_id,
                "organization_id": organization_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "prompt": prompt,
                "trigger_type": trigger_type,
                "trigger_metadata": trigger_metadata,
            }

            response = await self._async_client.post(url, json=payload, headers=self.headers)

            if response.status_code == 201:
                result = response.json()
                logger.info(
                    "job_execution_record_created",
                    execution_id=execution_id[:8],
                    job_id=job_id[:8] if job_id else None,
                )
                return result
            else:
                logger.error(
                    "job_execution_record_creation_failed",
                    status=response.status_code,
                    execution_id=execution_id[:8],
                    response=response.text,
                )
                raise Exception(f"Failed to create execution record: HTTP {response.status_code}")

        except Exception as e:
            logger.error(
                "job_execution_record_creation_error",
                error=str(e),
                execution_id=execution_id[:8],
            )
            raise

    async def update_job_execution_status(
        self,
        execution_id: str,
        job_id: str,
        status: str,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update job_executions record with execution results.

        This calls the Control Plane API to update job execution status
        instead of directly accessing Supabase.

        Args:
            execution_id: Execution ID
            job_id: Job ID
            status: Final status ("completed" or "failed")
            duration_ms: Execution duration in milliseconds
            error_message: Error message if failed

        Returns:
            Dict with job_id, execution_id, and status
        """
        try:
            url = f"{self.base_url}/api/v1/executions/{execution_id}/job/{job_id}/status"
            payload = {
                "status": status,
                "duration_ms": duration_ms,
                "error_message": error_message,
            }

            response = await self._async_client.post(url, json=payload, headers=self.headers)

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    "job_execution_status_updated",
                    execution_id=execution_id[:8],
                    job_id=job_id[:8],
                    status=status,
                )
                return result
            else:
                logger.error(
                    "job_execution_status_update_failed",
                    status_code=response.status_code,
                    execution_id=execution_id[:8],
                    job_id=job_id[:8],
                    response=response.text,
                )
                raise Exception(f"Failed to update job execution status: HTTP {response.status_code}")

        except Exception as e:
            logger.error(
                "job_execution_status_update_error",
                error=str(e),
                execution_id=execution_id[:8],
                job_id=job_id[:8],
            )
            raise

    async def _handle_control_message(self, message: Dict[str, Any]):
        """
        Handle control messages from control plane via WebSocket.

        This method is called when the worker receives a control message
        from the control plane (pause, resume, cancel, reload_config).

        Args:
            message: Control message with command, execution_id, and data
        """
        command = message.get("command")
        execution_id = message.get("execution_id")

        try:
            # Import Temporal client here to avoid circular import
            from control_plane_api.app.lib.temporal_client import get_temporal_client

            temporal_client = get_temporal_client()
            workflow_handle = temporal_client.get_workflow_handle(execution_id)

            if command == "pause":
                await workflow_handle.signal("pause_execution")
                logger.info("control_command_executed", command="pause", execution_id=execution_id[:8])

            elif command == "resume":
                await workflow_handle.signal("resume_execution")
                logger.info("control_command_executed", command="resume", execution_id=execution_id[:8])

            elif command == "cancel":
                await workflow_handle.cancel()
                logger.info("control_command_executed", command="cancel", execution_id=execution_id[:8])

            elif command == "reload_config":
                # Future: Reload config without restart
                logger.info("control_command_not_implemented", command="reload_config", execution_id=execution_id[:8])

            else:
                logger.warning("unknown_control_command", command=command, execution_id=execution_id[:8])

        except Exception as e:
            logger.error(
                "control_command_error",
                error=str(e),
                command=command,
                execution_id=execution_id[:8] if execution_id else None
            )


# Singleton instance
_control_plane_client: Optional[ControlPlaneClient] = None


def get_control_plane_client() -> ControlPlaneClient:
    """
    Get or create the Control Plane client singleton.

    Reads configuration from environment variables:
    - CONTROL_PLANE_URL: Control Plane URL
    - KUBIYA_API_KEY: API key for authentication
    - REDIS_URL: Redis URL for direct event streaming (from registration)
    - REDIS_PASSWORD: Redis password if needed (from registration)
    - REDIS_ENABLED: Whether Redis is enabled (from registration)
    - WEBSOCKET_ENABLED: Whether WebSocket is enabled (from registration)
    - WEBSOCKET_URL: WebSocket URL (from registration)
    - WORKER_ID: Worker ID (from registration)
    - EVENT_BUS_CONFIG: JSON string with event bus configuration (from registration, optional)

    Returns:
        ControlPlaneClient instance

    Raises:
        ValueError: If required environment variables are not set
    """
    global _control_plane_client

    if _control_plane_client is None:
        base_url = os.environ.get("CONTROL_PLANE_URL")
        api_key = os.environ.get("KUBIYA_API_KEY")

        # WebSocket config from environment (set by worker.py after registration)
        websocket_enabled = os.environ.get("WEBSOCKET_ENABLED", "false").lower() == "true"
        websocket_url = os.environ.get("WEBSOCKET_URL")
        worker_id = os.environ.get("WORKER_ID")

        # Redis config from environment (set by worker.py after registration)
        # This is the DEFAULT fast path for event streaming
        redis_url = os.environ.get("REDIS_URL")
        redis_password = os.environ.get("REDIS_PASSWORD")
        redis_enabled = os.environ.get("REDIS_ENABLED", "false").lower() == "true"

        # Event bus config from environment (set by worker.py after registration)
        event_bus_config = None
        event_bus_config_str = os.environ.get("EVENT_BUS_CONFIG")
        if event_bus_config_str:
            try:
                import json
                event_bus_config = json.loads(event_bus_config_str)
                logger.info("event_bus_config_loaded_from_env", providers=list(event_bus_config.keys()))
            except Exception as e:
                logger.warning("event_bus_config_parse_failed", error=str(e))

        # AUTO-CONFIGURE: If Redis credentials provided, auto-enable Redis provider
        # This makes Redis the default fast path without explicit event_bus_config
        if redis_enabled and redis_url and not event_bus_config:
            event_bus_config = {
                "redis": {
                    "enabled": True,
                    "redis_url": redis_url,
                }
            }
            logger.info(
                "redis_auto_configured_as_default",
                worker_id=worker_id[:8] if worker_id else "unknown",
                redis_url=redis_url.split("@")[-1] if "@" in redis_url else redis_url,  # Log without password
            )

        if not base_url:
            raise ValueError("CONTROL_PLANE_URL environment variable not set")
        if not api_key:
            raise ValueError("KUBIYA_API_KEY environment variable not set")

        _control_plane_client = ControlPlaneClient(
            base_url=base_url,
            api_key=api_key,
            websocket_enabled=websocket_enabled,
            websocket_url=websocket_url,
            worker_id=worker_id,
            event_bus_config=event_bus_config
        )

        logger.info(
            "control_plane_client_initialized",
            base_url=base_url,
            websocket_enabled=websocket_enabled,
            event_bus_configured=event_bus_config is not None
        )

    return _control_plane_client
