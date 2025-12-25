"""
Cleanup utilities for Claude Code SDK clients.

This module provides cleanup functionality for SDK clients and their associated
processes. The cleanup strategy avoids calling client.disconnect() due to
internal cancel scope issues in the SDK.
"""

import psutil
import structlog
from typing import Any

logger = structlog.get_logger(__name__)


def terminate_client_processes(client: Any, execution_id: str) -> int:
    """
    Terminate MCP server subprocesses associated with a Claude SDK client.

    This function forcefully terminates child processes that match MCP patterns.
    It tries graceful termination first (SIGTERM), then forceful kill (SIGKILL)
    if the process doesn't terminate within 1 second.

    Args:
        client: Claude SDK client (may have references to subprocesses)
        execution_id: Execution ID for logging

    Returns:
        Number of processes successfully terminated

    Note:
        This is the primary cleanup method. We avoid calling client.disconnect()
        because it has internal cancel scope issues that cause RuntimeError even
        when called from the correct event loop.
    """
    terminated_count = 0

    try:
        current_process = psutil.Process()
        for child in current_process.children(recursive=True):
            try:
                cmdline = ' '.join(child.cmdline())

                # Look for MCP-related processes
                # These patterns match: MCP servers, Claude SDK processes, stdio-client processes
                mcp_patterns = ['mcp', 'claude', 'stdio-client']
                if any(pattern in cmdline.lower() for pattern in mcp_patterns):
                    logger.info(
                        "terminating_mcp_process",
                        execution_id=execution_id,
                        pid=child.pid,
                        cmdline=cmdline[:100]  # Truncate to first 100 chars
                    )

                    # Try graceful termination first (SIGTERM)
                    child.terminate()
                    try:
                        # Wait up to 1 second for process to terminate gracefully
                        child.wait(timeout=1)
                        terminated_count += 1
                        logger.debug(
                            "mcp_process_terminated_gracefully",
                            execution_id=execution_id,
                            pid=child.pid
                        )
                    except psutil.TimeoutExpired:
                        # Force kill if it doesn't terminate (SIGKILL)
                        child.kill()
                        terminated_count += 1
                        logger.warning(
                            "force_killed_mcp_process",
                            execution_id=execution_id,
                            pid=child.pid,
                            note="Process did not terminate gracefully within timeout"
                        )

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                # Process already gone or we don't have permission
                # This is not an error - log at debug level
                logger.debug(
                    "could_not_terminate_process",
                    execution_id=execution_id,
                    error=str(e),
                    error_type=type(e).__name__
                )

    except Exception as e:
        # Unexpected error during process termination
        # Log but don't propagate - cleanup should never break execution
        logger.warning(
            "process_termination_failed",
            execution_id=execution_id,
            error=str(e),
            error_type=type(e).__name__
        )

    if terminated_count > 0:
        logger.info(
            "terminated_client_processes",
            execution_id=execution_id,
            process_count=terminated_count
        )

    return terminated_count


def cleanup_sdk_client(client: Any, execution_id: str, logger_instance: Any) -> dict:
    """
    Cleanup SDK client and associated resources.

    This is a wrapper that provides structured cleanup with comprehensive
    error handling. It skips client.disconnect() due to cancel scope issues
    and goes directly to process termination.

    Args:
        client: Claude SDK client to clean up
        execution_id: Execution ID for logging
        logger_instance: Logger instance to use for logging

    Returns:
        Dictionary with cleanup results:
        {
            'success': bool,
            'processes_terminated': int,
            'method': str,
            'error': str | None
        }

    Note:
        This function will NEVER raise exceptions. All errors are caught,
        logged, and returned in the result dictionary.
    """
    try:
        # Skip problematic disconnect() - go straight to process termination
        logger_instance.info(
            "skipping_sdk_disconnect_cleaning_processes",
            execution_id=execution_id,
            note="Skipping SDK disconnect due to cancel scope issues - terminating processes directly"
        )

        # Terminate MCP child processes
        terminated = terminate_client_processes(client, execution_id)

        if terminated > 0:
            logger_instance.info(
                "sdk_client_cleanup_completed",
                execution_id=execution_id,
                processes_terminated=terminated,
                method="process_termination"
            )
            return {
                'success': True,
                'processes_terminated': terminated,
                'method': 'process_termination',
                'error': None
            }
        else:
            logger_instance.debug(
                "no_processes_to_terminate",
                execution_id=execution_id
            )
            return {
                'success': True,
                'processes_terminated': 0,
                'method': 'no_action_needed',
                'error': None
            }

    except Exception as cleanup_error:
        # LAST RESORT: Log but NEVER propagate
        logger_instance.error(
            "cleanup_catastrophic_failure",
            execution_id=execution_id,
            error=str(cleanup_error),
            error_type=type(cleanup_error).__name__,
            exc_info=True,
            note="Cleanup completely failed - returning error but not propagating exception"
        )
        return {
            'success': False,
            'processes_terminated': 0,
            'method': 'failed',
            'error': str(cleanup_error)
        }
