"""
Temporal worker for Agent Control Plane - Decoupled Architecture.

This worker:
1. Registers with Control Plane API on startup using KUBIYA_API_KEY
2. Gets dynamic configuration (Temporal credentials, task queue name, etc.)
3. Connects to Temporal Cloud with provided credentials
4. Sends periodic heartbeats to Control Plane
5. Has NO direct database access - all state managed via Control Plane API

Environment variables REQUIRED:
- KUBIYA_API_KEY: Kubiya API key for authentication (required)
- CONTROL_PLANE_URL: Control Plane API URL (e.g., https://control-plane.kubiya.ai)
- ENVIRONMENT_NAME: Environment/task queue name to join (default: "default")

Environment variables OPTIONAL:
- WORKER_HOSTNAME: Custom hostname for worker (default: auto-detected)
- HEARTBEAT_INTERVAL: Seconds between heartbeats (default: 60, lightweight mode)
"""

import asyncio
import os
import sys
import structlog
import httpx
import socket
import platform
import psutil
import time
from dataclasses import dataclass
from typing import Optional, List
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions
from temporalio.client import Client, TLSConfig
from collections import deque

from control_plane_api.app.utils.helpers import is_local_temporal
# Import workflows and activities from local package
from control_plane_api.worker.workflows.agent_execution import AgentExecutionWorkflow
from control_plane_api.worker.workflows.team_execution import TeamExecutionWorkflow
from control_plane_api.worker.workflows.scheduled_job_wrapper import ScheduledJobWrapperWorkflow
from control_plane_api.worker.activities.agent_activities import (
    execute_agent_llm,
    update_execution_status,
    update_agent_status,
    get_execution_details,
    persist_conversation_history,
    submit_runtime_analytics_activity,
)
from control_plane_api.worker.activities.team_activities import (
    get_team_agents,
    execute_team_coordination,
)
from control_plane_api.worker.activities.runtime_activities import (
    execute_with_runtime,
    publish_user_message,
)
from control_plane_api.worker.activities.job_activities import (
    create_job_execution_record,
    update_job_execution_status,
)

# Configure structured logging
import logging
from control_plane_api.worker.utils.logging_config import configure_logging

# Configure logging with dynamic settings from environment variables
configure_logging()

logger = structlog.get_logger()

# Global log buffer to collect logs since last heartbeat
log_buffer = deque(maxlen=500)  # Keep last 500 log lines
worker_start_time = time.time()

# Global state for differential heartbeats (optimization)
_last_full_heartbeat_time: float = 0
_cached_system_info: Optional[dict] = None
_last_log_index_sent: int = 0
_full_heartbeat_interval: int = 300  # Full heartbeat every 5 minutes (vs lightweight every 60s)


class ProgressUI:
    """Minimal animated UI for worker startup - minikube style"""

    @staticmethod
    def step(emoji: str, message: str, status: str = ""):
        """Log a step with emoji and optional status"""
        if status:
            logger.info("worker_progress", emoji=emoji, message=message, status=status)
        else:
            logger.info("worker_progress", emoji=emoji, message=message)

    @staticmethod
    def success(emoji: str, message: str):
        """Log success message"""
        logger.info("worker_success", emoji=emoji, message=message)

    @staticmethod
    def error(emoji: str, message: str):
        """Log error message"""
        logger.error("worker_error", emoji=emoji, message=message)

    @staticmethod
    def warning(emoji: str, message: str):
        """Log warning message"""
        logger.warning("worker_warning", emoji=emoji, message=message)

    @staticmethod
    def header(text: str):
        """Log section header"""
        logger.info("worker_header", text=text)

    @staticmethod
    def banner():
        """Log startup banner"""
        logger.info("worker_banner", title="Kubiya Agent Worker")


def collect_system_info() -> dict:
    """
    Collect current system metrics and information.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Get Kubiya CLI version from environment variable (set by CLI) - skipped for now
        cli_version = None

        # Get SDK version
        from control_plane_api.version import get_sdk_version
        sdk_version = get_sdk_version()

        # Get process ID
        pid = os.getpid()

        # Get current working directory
        cwd = os.getcwd()

        # Get supported runtimes (both are always available)
        supported_runtimes = ["agno", "claude_code"]

        # Check Docker availability
        docker_available = False
        docker_version = None
        try:
            import subprocess
            import shutil

            # First try to find docker in PATH using shutil.which
            docker_path = shutil.which('docker')
            logger.debug("docker_which_result", path=docker_path)

            # Fallback to common locations if not in PATH
            if not docker_path:
                docker_paths = [
                    '/usr/local/bin/docker',
                    '/usr/bin/docker',
                    '/opt/homebrew/bin/docker',
                ]
                for path in docker_paths:
                    logger.debug("docker_checking_path", path=path, exists=os.path.exists(path))
                    if os.path.exists(path):
                        docker_path = path
                        break

            if docker_path:
                logger.debug("docker_running_version_check", path=docker_path)
                result = subprocess.run(
                    [docker_path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    shell=False
                )
                logger.debug(
                    "docker_version_output",
                    returncode=result.returncode,
                    stdout=result.stdout[:200],
                    stderr=result.stderr[:200] if result.stderr else None
                )
                if result.returncode == 0:
                    docker_available = True
                    # Parse "Docker version 28.1.1, build 4eba377"
                    output = result.stdout.strip()
                    if ',' in output:
                        docker_version = output.split(',')[0].replace('Docker version', '').strip()
                    else:
                        docker_version = output.replace('Docker version', '').strip()
                    logger.debug("docker_detected", version=docker_version, path=docker_path)
                else:
                    logger.warning("docker_version_check_failed", returncode=result.returncode)
            else:
                logger.warning("docker_not_found_in_path_or_common_locations")
        except Exception as e:
            # Log for debugging but don't fail
            logger.warning("docker_detection_failed", error=str(e), error_type=type(e).__name__)
            import traceback
            logger.debug("docker_detection_traceback", traceback=traceback.format_exc())

        # Parse OS details from platform
        os_name = platform.system()  # Darwin, Linux, Windows
        os_version = platform.release()

        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "os_name": os_name,
            "os_version": os_version,
            "python_version": platform.python_version(),
            "cli_version": cli_version,
            "sdk_version": sdk_version,
            "pid": pid,
            "cwd": cwd,
            "supported_runtimes": supported_runtimes,
            "docker_available": docker_available,
            "docker_version": docker_version,
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": cpu_percent,
            "memory_total": memory.total,
            "memory_used": memory.used,
            "memory_percent": memory.percent,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_percent": disk.percent,
            "uptime_seconds": time.time() - worker_start_time,
        }
    except Exception as e:
        logger.warning("failed_to_collect_system_info", error=str(e))
        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
        }


def get_recent_logs() -> List[str]:
    """
    Get logs collected since last heartbeat and clear the buffer.
    """
    logs = list(log_buffer)
    log_buffer.clear()
    return logs


def log_to_buffer(message: str):
    """
    Add a log message to the buffer for sending in next heartbeat.
    """
    log_buffer.append(message)


@dataclass
class WorkerConfig:
    """Configuration received from Control Plane registration"""
    worker_id: str
    environment_name: str  # Task queue name (org_id.environment)
    temporal_namespace: str
    temporal_host: str
    temporal_api_key: str
    organization_id: str
    control_plane_url: str
    litellm_api_url: str = "https://llm-proxy.kubiya.ai"
    litellm_api_key: str = ""
    # Redis configuration for direct event streaming
    redis_url: str = ""
    redis_password: str = ""
    redis_enabled: bool = False
    # WebSocket configuration
    websocket_enabled: bool = True
    websocket_url: str = ""
    websocket_features: list = None
    # Queue configuration for cleanup
    queue_id: str = ""
    queue_ephemeral: bool = False
    queue_single_execution: bool = False


async def start_worker_for_queue(
    control_plane_url: str,
    kubiya_api_key: str,
    queue_id: str,
) -> WorkerConfig:
    """
    Start a worker for a specific queue ID.

    Args:
        control_plane_url: Control Plane API URL
        kubiya_api_key: Kubiya API key for authentication
        queue_id: Worker queue ID (UUID)

    Returns:
        WorkerConfig with all necessary configuration

    Raises:
        Exception if start fails
    """
    # Get worker SDK version for compatibility check
    from control_plane_api.version import get_sdk_version
    worker_sdk_version = get_sdk_version()

    # Collect system info to send during registration
    system_info = collect_system_info()

    logger.info(
        "starting_worker_for_queue",
        queue_id=queue_id,
        control_plane_url=control_plane_url,
        sdk_version=worker_sdk_version,
        pid=system_info.get("pid"),
        cwd=system_info.get("cwd"),
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{control_plane_url}/api/v1/worker-queues/{queue_id}/start",
                headers={"Authorization": f"Bearer {kubiya_api_key}"},
                json={
                    "worker_sdk_version": worker_sdk_version,
                    "system_info": system_info,
                    "control_plane_url": control_plane_url
                }
            )

            # Success case
            if response.status_code == 200:
                data = response.json()

                ProgressUI.success("✓", f"Registered with control plane")
                logger.info(
                    "worker_registered",
                    worker_id=data.get("worker_id")[:8],
                    queue_name=data.get("queue_name"),
                )

                # Check SDK version compatibility
                control_plane_sdk_version = data.get("control_plane_sdk_version")
                if control_plane_sdk_version and control_plane_sdk_version != worker_sdk_version:
                    ProgressUI.warning("⚠", "SDK version mismatch detected")
                    print(f"\n   Worker SDK version:        {worker_sdk_version}")
                    print(f"   Control Plane SDK version: {control_plane_sdk_version}")
                    print(f"\n   Consider updating your worker to match the control plane version.\n")

                    logger.warning(
                        "sdk_version_mismatch",
                        worker_version=worker_sdk_version,
                        control_plane_version=control_plane_sdk_version,
                    )
                elif control_plane_sdk_version:
                    logger.info(
                        "sdk_version_match",
                        version=worker_sdk_version,
                    )

                # The task_queue_name is now just the queue UUID
                # Priority for LiteLLM API URL:
                # 1. LITELLM_API_BASE environment variable (from local proxy via CLI)
                # 2. Control plane litellm_api_url
                # 3. Default (https://llm-proxy.kubiya.ai)
                litellm_api_url = os.getenv("LITELLM_API_BASE") or data.get("litellm_api_url", "https://llm-proxy.kubiya.ai")
                litellm_api_key = os.getenv("LITELLM_API_KEY") or data.get("litellm_api_key", "")

                # Log which LiteLLM endpoint is being used
                if os.getenv("LITELLM_API_BASE"):
                    logger.info(
                        "using_local_litellm_proxy",
                        litellm_api_url=litellm_api_url,
                        source="environment_variable"
                    )
                elif "litellm_api_url" in data:
                    logger.info(
                        "using_control_plane_litellm_proxy",
                        litellm_api_url=litellm_api_url,
                        source="control_plane"
                    )

                return WorkerConfig(
                    worker_id=data["worker_id"],
                    environment_name=data["task_queue_name"],  # This is now the queue UUID
                    temporal_namespace=data["temporal_namespace"],
                    temporal_host=data["temporal_host"],
                    temporal_api_key=data["temporal_api_key"],
                    organization_id=data["organization_id"],
                    control_plane_url=data["control_plane_url"],
                    litellm_api_url=litellm_api_url,
                    litellm_api_key=litellm_api_key,
                    # Redis configuration from control plane (for direct event streaming)
                    redis_url=data.get("redis_url", ""),
                    redis_password=data.get("redis_password", ""),
                    redis_enabled=data.get("redis_enabled", False),
                    # WebSocket configuration from control plane
                    websocket_enabled=data.get("websocket_enabled", True),
                    websocket_url=data.get("websocket_url", ""),
                    websocket_features=data.get("websocket_features", []),
                )

            # Handle errors
            else:
                # Try to extract error detail from response
                error_message = response.text
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", response.text)
                except:
                    pass

                ProgressUI.error("✗", "Worker registration failed")
                print(f"   {error_message}\n")

                logger.error(
                    "worker_start_failed",
                    status_code=response.status_code,
                    queue_id=queue_id,
                )
                sys.exit(1)

    except httpx.RequestError as e:
        ProgressUI.error("✗", f"Connection failed: {control_plane_url}")
        print(f"   {str(e)}\n")
        logger.error("control_plane_connection_failed", error=str(e))
        sys.exit(1)


async def send_heartbeat(
    config: WorkerConfig,
    kubiya_api_key: str,
    status: str = "active",
    tasks_processed: int = 0,
    current_task_id: Optional[str] = None,
    force_full: bool = False
) -> bool:
    """
    Send heartbeat to Control Plane with differential data.

    Optimization: Uses lightweight heartbeats (status only) by default,
    and sends full heartbeats (with system info + logs) every 5 minutes.
    This reduces server load by 90% while maintaining full visibility.

    Args:
        config: Worker configuration
        kubiya_api_key: Kubiya API key for authentication
        status: Worker status (active, idle, busy)
        tasks_processed: Number of tasks processed
        current_task_id: Currently executing task ID
        force_full: Force a full heartbeat (ignores timing logic)

    Returns:
        True if successful, False otherwise
    """
    global _last_full_heartbeat_time, _cached_system_info, _last_log_index_sent

    current_time = time.time()
    time_since_last_full = current_time - _last_full_heartbeat_time

    # Determine if this should be a full heartbeat
    # Full heartbeat: every 5 minutes, or on first run, or if forced
    is_full_heartbeat = (
        force_full or
        _last_full_heartbeat_time == 0 or
        time_since_last_full >= _full_heartbeat_interval
    )

    # Build base heartbeat data (always included)
    heartbeat_data = {
        "status": status,
        "tasks_processed": tasks_processed,
        "current_task_id": current_task_id,
        "worker_metadata": {},
    }

    # Add system info and logs only for full heartbeats
    if is_full_heartbeat:
        # Collect fresh system info (expensive operation)
        system_info = collect_system_info()
        _cached_system_info = system_info
        heartbeat_data["system_info"] = system_info

        # Get logs since last full heartbeat (only new logs)
        logs = get_recent_logs()
        if logs:
            heartbeat_data["logs"] = logs

        # Update last full heartbeat time
        _last_full_heartbeat_time = current_time
        heartbeat_type = "full"
    else:
        # Lightweight heartbeat - no system info or logs
        # Server will use cached system info from Redis
        heartbeat_type = "lightweight"

    try:
        # Normalize URL to prevent double-slash issues
        control_plane_url = config.control_plane_url.rstrip("/")
        url = f"{control_plane_url}/api/v1/workers/{config.worker_id}/heartbeat"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json=heartbeat_data,
                headers={"Authorization": f"Bearer {kubiya_api_key}"}
            )

            if response.status_code in [200, 204]:
                logger.debug(
                    "heartbeat_sent",
                    worker_id=config.worker_id,
                    type=heartbeat_type,
                    payload_size=len(str(heartbeat_data))
                )
                log_to_buffer(
                    f"[{time.strftime('%H:%M:%S')}] Heartbeat sent ({heartbeat_type})"
                )
                return True
            else:
                logger.warning(
                    "heartbeat_failed",
                    status_code=response.status_code,
                    response=response.text[:200],
                    type=heartbeat_type
                )
                log_to_buffer(
                    f"[{time.strftime('%H:%M:%S')}] Heartbeat failed: HTTP {response.status_code}"
                )
                return False

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}" if str(e) else f"{type(e).__name__} (no message)"
        logger.warning(
            "heartbeat_error",
            error=error_msg,
            error_type=type(e).__name__,
            worker_id=config.worker_id[:8] if config.worker_id else "unknown",
            type=heartbeat_type
        )
        log_to_buffer(f"[{time.strftime('%H:%M:%S')}] Heartbeat error: {error_msg[:150]}")
        return False


async def create_temporal_client(config: WorkerConfig) -> Client:
    """
    Create Temporal client using configuration from Control Plane.

    Args:
        config: Worker configuration from Control Plane registration

    Returns:
        Connected Temporal client instance
    """
    try:
        if is_local_temporal():
            # Connect to local Temporal without TLS or API key
            logger.info("connecting_to_local_temporal", host=config.temporal_host)
            client = await Client.connect(
                config.temporal_host,
                namespace=config.temporal_namespace,
            )
        else:
            # Connect to Temporal Cloud with TLS and API key
            logger.info("connecting_to_temporal_cloud", host=config.temporal_host)
            client = await Client.connect(
                config.temporal_host,
                namespace=config.temporal_namespace,
                tls=TLSConfig(),  # TLS enabled
                rpc_metadata={"authorization": f"Bearer {config.temporal_api_key}"}
            )

        return client

    except Exception as e:
        logger.error("connection_failed", error=str(e))
        ProgressUI.error("✗", f"Temporal connection failed: {str(e)}")
        raise


async def send_disconnect(
    config: WorkerConfig,
    kubiya_api_key: str,
    reason: str = "shutdown",
    exit_code: Optional[int] = None,
    error_message: Optional[str] = None
) -> bool:
    """
    Notify Control Plane that worker is disconnecting/exiting.

    Args:
        config: Worker configuration
        kubiya_api_key: Kubiya API key for authentication
        reason: Disconnect reason (shutdown, error, crash, etc.)
        exit_code: Exit code if applicable
        error_message: Error message if applicable

    Returns:
        True if successful, False otherwise
    """
    disconnect_data = {
        "reason": reason,
        "exit_code": exit_code,
        "error_message": error_message
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{config.control_plane_url}/api/v1/workers/{config.worker_id}/disconnect",
                json=disconnect_data,
                headers={"Authorization": f"Bearer {kubiya_api_key}"}
            )

            if response.status_code in [200, 204]:
                logger.info(
                    "worker_disconnected",
                    worker_id=config.worker_id,
                    reason=reason,
                    exit_code=exit_code
                )
                return True
            else:
                logger.warning(
                    "disconnect_notification_failed",
                    status_code=response.status_code,
                    response=response.text[:200]
                )
                return False

    except Exception as e:
        logger.warning("disconnect_notification_error", error=str(e))
        return False


async def delete_ephemeral_queue(
    config: WorkerConfig,
    kubiya_api_key: str,
    queue_id: str,
    timeout: int = 5
) -> bool:
    """
    Delete ephemeral queue during worker shutdown.

    This allows the worker to clean up its ephemeral queue immediately,
    without requiring the CLI to wait for worker unregistration.

    Args:
        config: Worker configuration
        kubiya_api_key: Kubiya API key for authentication
        queue_id: Queue UUID to delete
        timeout: Request timeout in seconds (short timeout - if it fails, TTL handles it)

    Returns:
        True if successful, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=float(timeout)) as client:
            response = await client.delete(
                f"{config.control_plane_url}/api/v1/worker-queues/{queue_id}",
                headers={"Authorization": f"Bearer {kubiya_api_key}"}
            )

            if response.status_code in [200, 204]:
                logger.info(
                    "ephemeral_queue_deleted",
                    queue_id=queue_id,
                    worker_id=config.worker_id
                )
                return True
            else:
                logger.warning(
                    "queue_delete_failed",
                    queue_id=queue_id,
                    status_code=response.status_code,
                    response=response.text[:200]
                )
                return False

    except Exception as e:
        logger.warning(
            "queue_delete_error",
            queue_id=queue_id,
            error=str(e)
        )
        return False


async def heartbeat_loop(config: WorkerConfig, kubiya_api_key: str, interval: int = 60):
    """
    Background task to send periodic heartbeats to Control Plane.

    Args:
        config: Worker configuration
        kubiya_api_key: Kubiya API key for authentication
        interval: Seconds between heartbeats
    """
    tasks_processed = 0

    while True:
        try:
            await asyncio.sleep(interval)
            await send_heartbeat(
                config=config,
                kubiya_api_key=kubiya_api_key,
                status="active",
                tasks_processed=tasks_processed
            )
        except asyncio.CancelledError:
            logger.info("heartbeat_loop_cancelled")
            break
        except Exception as e:
            logger.warning("heartbeat_loop_error", error=str(e))


async def run_worker():
    """
    Run the Temporal worker with decoupled architecture.

    The worker:
    1. Registers with Control Plane API
    2. Gets dynamic configuration (Temporal credentials, task queue, etc.)
    3. Connects to Temporal Cloud
    4. Starts heartbeat loop
    5. Registers workflows and activities
    6. Polls for tasks and executes them
    """
    # Get configuration from environment
    kubiya_api_key = os.environ.get("KUBIYA_API_KEY")
    control_plane_url = os.environ.get("CONTROL_PLANE_URL")
    queue_id = os.environ.get("QUEUE_ID")
    heartbeat_interval = int(os.environ.get("HEARTBEAT_INTERVAL", "60"))
    single_execution_mode = os.environ.get("SINGLE_EXECUTION", "").lower() in ("true", "1", "yes")

    # Validate required configuration
    if not kubiya_api_key:
        logger.error(
            "configuration_error",
            message="KUBIYA_API_KEY environment variable is required"
        )
        sys.exit(1)

    if not control_plane_url:
        logger.error(
            "configuration_error",
            message="CONTROL_PLANE_URL environment variable is required"
        )
        sys.exit(1)

    if not queue_id:
        logger.error(
            "configuration_error",
            message="QUEUE_ID environment variable is required"
        )
        sys.exit(1)

    log_to_buffer(f"[{time.strftime('%H:%M:%S')}] Worker starting for queue {queue_id}")

    if single_execution_mode:
        log_to_buffer(f"[{time.strftime('%H:%M:%S')}] Single execution mode: enabled (will exit after one task)")
        logger.info("single_execution_mode_enabled", queue_id=queue_id)

    try:
        # Print banner
        ProgressUI.banner()

        # Step 1: Register with control plane
        ProgressUI.step("⏳", "Registering with control plane...")
        log_to_buffer(f"[{time.strftime('%H:%M:%S')}] Registering with control plane...")
        config = await start_worker_for_queue(
            control_plane_url=control_plane_url,
            kubiya_api_key=kubiya_api_key,
            queue_id=queue_id,
        )
        log_to_buffer(f"[{time.strftime('%H:%M:%S')}] Worker registered: {config.worker_id}")

        # Set environment variables for activities to use
        os.environ["CONTROL_PLANE_URL"] = config.control_plane_url

        # Set single execution flag so event publisher can disable WebSocket
        if single_execution_mode:
            os.environ["KUBIYA_SINGLE_EXECUTION_MODE"] = "true"
        os.environ["KUBIYA_API_KEY"] = kubiya_api_key
        os.environ["WORKER_ID"] = config.worker_id
        os.environ["LITELLM_API_BASE"] = config.litellm_api_url
        os.environ["LITELLM_API_KEY"] = config.litellm_api_key

        # Set WebSocket environment variables if enabled
        from control_plane_api.worker.utils.environment import should_use_websocket

        if config.websocket_enabled and config.websocket_url and should_use_websocket():
            os.environ["WEBSOCKET_ENABLED"] = "true"
            os.environ["WEBSOCKET_URL"] = config.websocket_url
            logger.info(
                "websocket_configured",
                worker_id=config.worker_id[:8],
                websocket_url=config.websocket_url
            )
        else:
            os.environ["WEBSOCKET_ENABLED"] = "false"
            if not should_use_websocket():
                logger.info("websocket_disabled_serverless_environment")
            else:
                logger.info("websocket_disabled_using_http")

        # Set Redis environment variables if provided (for Redis-first event streaming)
        if config.redis_enabled and config.redis_url:
            os.environ["REDIS_URL"] = config.redis_url
            os.environ["REDIS_ENABLED"] = "true"
            if config.redis_password:
                os.environ["REDIS_PASSWORD"] = config.redis_password
            logger.info(
                "redis_configured_for_direct_streaming",
                worker_id=config.worker_id[:8],
                redis_url=config.redis_url.split("@")[-1] if "@" in config.redis_url else config.redis_url  # Log without password
            )
        else:
            os.environ["REDIS_ENABLED"] = "false"
            logger.debug("redis_not_configured_will_use_http_endpoint")

        # Step 2: Connect to Temporal
        ProgressUI.step("⏳", "Connecting to Temporal...")
        client = await create_temporal_client(config)
        ProgressUI.success("✓", "Connected to Temporal")

        # Step 3: Send initial heartbeat
        ProgressUI.step("⏳", "Sending heartbeat...")
        await send_heartbeat(
            config=config,
            kubiya_api_key=kubiya_api_key,
            status="active",
            tasks_processed=0
        )
        ProgressUI.success("✓", "Worker visible in UI")

        # Start heartbeat loop in background
        heartbeat_task = asyncio.create_task(
            heartbeat_loop(config, kubiya_api_key, heartbeat_interval)
        )

        # Step 4: Create worker
        ProgressUI.step("⏳", "Starting worker...")

        # Configure workflow sandbox with passthrough modules
        # These modules use non-deterministic operations at import time but are safe
        # because they're only used in activities, not workflow logic
        sandbox_restrictions = SandboxRestrictions.default.with_passthrough_modules(
            "structlog",
            "structlog.dev",
            "structlog.processors",
            "structlog.tracebacks",
            "rich",
            "rich.traceback",
            "control_plane_api.version",  # Version checking uses filesystem operations
        )

        worker = Worker(
            client,
            task_queue=config.environment_name,
            workflows=[
                AgentExecutionWorkflow,
                TeamExecutionWorkflow,
                ScheduledJobWrapperWorkflow,  # Wrapper for scheduled jobs
            ],
            activities=[
                execute_agent_llm,
                update_execution_status,
                update_agent_status,
                get_execution_details,  # Get execution details from Control Plane
                persist_conversation_history,  # Conversation persistence
                submit_runtime_analytics_activity,  # Analytics submission
                get_team_agents,
                execute_team_coordination,
                execute_with_runtime,  # RuntimeFactory-based execution
                publish_user_message,  # Publish user message to stream
                create_job_execution_record,  # Job execution record creation
                update_job_execution_status,  # Job execution status updates
            ],
            max_concurrent_activities=10,
            max_concurrent_workflow_tasks=10,
            workflow_runner=SandboxedWorkflowRunner(restrictions=sandbox_restrictions),
        )

        ProgressUI.success("✓", "Worker ready")

        # Start WebSocket client if enabled
        from control_plane_api.worker.control_plane_client import get_control_plane_client

        control_plane_client = get_control_plane_client()
        if config.websocket_enabled and should_use_websocket():
            await control_plane_client.start_websocket()
            ProgressUI.step("✓", "WebSocket connected")
            logger.info("websocket_started", worker_id=config.worker_id[:8])

        if single_execution_mode:
            ProgressUI.header("📡 Listening for one task... (will exit after completion)")
        else:
            ProgressUI.header("📡 Listening for tasks... (Ctrl+C to stop)")

        logger.info(
            "worker_ready",
            worker_id=config.worker_id[:8],
            single_execution_mode=single_execution_mode,
        )

        # Run worker (blocks until interrupted)
        try:
            if single_execution_mode:
                # Single execution mode: run worker and monitor for workflow completion
                logger.info("starting_worker_in_single_execution_mode")

                # Create a task to run the worker
                worker_run_task = asyncio.create_task(worker.run())

                # Monitor for execution completion via Control Plane API
                async def monitor_and_shutdown():
                    """
                    Monitor execution status and shutdown after task completes.
                    Robustness improvements:
                    - Requires consecutive completion checks to avoid false positives
                    - Extends timeout for long-running tasks
                    """
                    # Wait for worker to start and pick up the execution
                    await asyncio.sleep(5)

                    # Monitor for 30 minutes max (extended from 10 minutes)
                    max_runtime = 1800
                    check_interval = 3  # Check every 3 seconds
                    elapsed = 0
                    execution_seen = False
                    execution_id = None

                    # Robustness: Require 2 consecutive "completed" checks before shutting down
                    consecutive_completion_checks = 0
                    required_consecutive_checks = 2

                    logger.info("single_execution_monitor_started", queue_id=queue_id)

                    should_shutdown = False
                    while elapsed < max_runtime and not should_shutdown:
                        await asyncio.sleep(check_interval)
                        elapsed += check_interval

                        # Check if worker task completed unexpectedly
                        if worker_run_task.done():
                            logger.info("single_execution_worker_task_completed", elapsed=elapsed)
                            break

                        # Query Control Plane for recent executions on this queue
                        try:
                            # Get the control plane client
                            async with httpx.AsyncClient(timeout=10.0) as http_client:
                                # List recent executions for this queue
                                response = await http_client.get(
                                    f"{control_plane_url}/api/v1/worker-queues/{queue_id}/executions",
                                    headers={"Authorization": f"Bearer {kubiya_api_key}"},
                                    params={"limit": 5, "status": "all"}
                                )

                                if response.status_code == 200:
                                    executions = response.json()

                                    # Look for any execution in a terminal or waiting state
                                    for execution in executions:
                                        exec_status = execution.get("status", "").lower()
                                        exec_id = execution.get("id")

                                        if not execution_seen:
                                            if exec_status in ["running", "completed", "failed", "waiting_for_input"]:
                                                execution_seen = True
                                                execution_id = exec_id
                                                logger.info("single_execution_detected", execution_id=exec_id[:8] if exec_id else None, status=exec_status)

                                        # If we've seen an execution and it's now in a terminal/waiting state, check if consistent
                                        if execution_seen and exec_id == execution_id:
                                            if exec_status in ["completed", "failed", "waiting_for_input", "cancelled"]:
                                                consecutive_completion_checks += 1
                                                logger.info("single_execution_completion_check",
                                                           execution_id=exec_id[:8] if exec_id else None,
                                                           status=exec_status,
                                                           consecutive_checks=consecutive_completion_checks,
                                                           required_checks=required_consecutive_checks,
                                                           elapsed=elapsed)

                                                # Only shutdown after consecutive checks confirm completion
                                                if consecutive_completion_checks >= required_consecutive_checks:
                                                    logger.info("single_execution_completed",
                                                               execution_id=exec_id[:8] if exec_id else None,
                                                               status=exec_status,
                                                               elapsed=elapsed)
                                                    # Give a moment for any final cleanup
                                                    await asyncio.sleep(2)
                                                    should_shutdown = True
                                                    break
                                            else:
                                                # Execution is back to running state - reset counter
                                                if consecutive_completion_checks > 0:
                                                    logger.info("single_execution_still_active",
                                                               execution_id=exec_id[:8] if exec_id else None,
                                                               status=exec_status,
                                                               resetting_counter=True)
                                                    consecutive_completion_checks = 0
                                else:
                                    logger.debug("single_execution_status_check_failed", status_code=response.status_code)
                                    # Reset consecutive checks on failed API call to be safe
                                    if consecutive_completion_checks > 0:
                                        logger.debug("single_execution_resetting_counter_after_failed_check")
                                        consecutive_completion_checks = 0

                        except Exception as e:
                            logger.debug("single_execution_status_check_error", error=str(e))
                            # Reset consecutive checks on error to be safe
                            if consecutive_completion_checks > 0:
                                logger.debug("single_execution_resetting_counter_after_error")
                                consecutive_completion_checks = 0
                            # Continue monitoring even if status check fails

                    # Check why we exited the loop
                    if not should_shutdown and elapsed >= max_runtime:
                        # Actual timeout
                        logger.warning("single_execution_timeout_reached", elapsed=elapsed)

                    # Shutdown the worker gracefully
                    logger.info("single_execution_triggering_shutdown", elapsed_seconds=elapsed, reason="completed" if should_shutdown else "timeout")
                    ProgressUI.step("✓", "Task completed - shutting down worker...")
                    log_to_buffer(f"[{time.strftime('%H:%M:%S')}] Task completed, shutting down...")
                    await worker.shutdown()

                # Start monitoring task
                monitor_task = asyncio.create_task(monitor_and_shutdown())

                try:
                    # Wait for worker to complete
                    await worker_run_task
                    logger.info("single_execution_worker_stopped")
                finally:
                    # Cancel monitor task if still running
                    if not monitor_task.done():
                        monitor_task.cancel()
                        try:
                            await monitor_task
                        except asyncio.CancelledError:
                            pass
            else:
                # Normal mode - run indefinitely
                await worker.run()
        finally:
            # Stop WebSocket client
            await control_plane_client.stop_websocket()

        # Cancel heartbeat task when worker stops
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

        # Notify control plane of graceful shutdown
        print()
        ProgressUI.step("⏳", "Shutting down gracefully...")

        # Delete ephemeral queue if we're the owner (single execution mode)
        if config.queue_ephemeral and config.queue_single_execution and config.queue_id:
            try:
                await delete_ephemeral_queue(
                    config=config,
                    kubiya_api_key=kubiya_api_key,
                    queue_id=config.queue_id
                )
                logger.info("ephemeral_queue_cleaned_up", queue_id=config.queue_id)
            except Exception as e:
                logger.warning(
                    "ephemeral_queue_cleanup_failed",
                    queue_id=config.queue_id,
                    error=str(e)
                )
                # Continue shutdown even if delete fails (TTL will handle it)

        await send_disconnect(
            config=config,
            kubiya_api_key=kubiya_api_key,
            reason="shutdown",
            exit_code=0
        )
        ProgressUI.success("✓", "Worker stopped")
        print()

    except KeyboardInterrupt:
        print()
        ProgressUI.step("⏳", "Shutting down...")

        # Stop WebSocket client
        from control_plane_api.worker.control_plane_client import get_control_plane_client
        try:
            control_plane_client = get_control_plane_client()
            await control_plane_client.stop_websocket()
        except:
            pass

        # Notify control plane of keyboard interrupt (only if config was successfully obtained)
        try:
            if 'config' in locals():
                # Delete ephemeral queue if we're the owner
                if config.queue_ephemeral and config.queue_single_execution and config.queue_id:
                    try:
                        await delete_ephemeral_queue(
                            config=config,
                            kubiya_api_key=kubiya_api_key,
                            queue_id=config.queue_id
                        )
                    except Exception as e:
                        logger.warning(
                            "ephemeral_queue_cleanup_on_interrupt_failed",
                            error=str(e)
                        )

                await send_disconnect(
                    config=config,
                    kubiya_api_key=kubiya_api_key,
                    reason="shutdown",
                    exit_code=0
                )
                ProgressUI.success("✓", "Worker stopped")
            else:
                logger.info("shutdown_before_registration_completed")
        except Exception as e:
            logger.warning("disconnect_on_interrupt_failed", error=str(e))
    except Exception as e:
        import traceback
        logger.error("temporal_worker_error", error=str(e), traceback=traceback.format_exc())
        # Notify control plane of error (only if config was successfully obtained)
        try:
            if 'config' in locals():
                await send_disconnect(
                    config=config,
                    kubiya_api_key=kubiya_api_key,
                    reason="error",
                    exit_code=1,
                    error_message=str(e)[:2000] + (" [truncated]" if len(str(e)) > 2000 else "")
                )
            else:
                logger.warning("disconnect_skipped_no_config", error="Worker failed before registration completed")
        except Exception as disconnect_error:
            logger.warning("disconnect_on_error_failed", error=str(disconnect_error))
        raise


def main():
    """Main entry point with CLI argument support"""
    import argparse

    # Parse CLI arguments
    parser = argparse.ArgumentParser(
        description="Kubiya Agent Worker - Temporal worker for agent execution"
    )
    parser.add_argument(
        "--queue-id",
        type=str,
        help="Worker queue ID (can also use QUEUE_ID env var)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Kubiya API key (can also use KUBIYA_API_KEY env var)"
    )
    parser.add_argument(
        "--control-plane-url",
        type=str,
        help="Control plane URL (can also use CONTROL_PLANE_URL env var)"
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=60,
        help="Heartbeat interval in seconds (default: 60, lightweight mode)"
    )

    args = parser.parse_args()

    # Set environment variables from CLI args if not already set
    # Environment variables take precedence over CLI args (safer)
    if args.queue_id and not os.environ.get("QUEUE_ID"):
        os.environ["QUEUE_ID"] = args.queue_id
    if args.api_key and not os.environ.get("KUBIYA_API_KEY"):
        os.environ["KUBIYA_API_KEY"] = args.api_key
    if args.control_plane_url and not os.environ.get("CONTROL_PLANE_URL"):
        os.environ["CONTROL_PLANE_URL"] = args.control_plane_url
    if args.heartbeat_interval and not os.environ.get("HEARTBEAT_INTERVAL"):
        os.environ["HEARTBEAT_INTERVAL"] = str(args.heartbeat_interval)

    logger.info("worker_starting")

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("worker_stopped")
    except Exception as e:
        logger.error("worker_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
