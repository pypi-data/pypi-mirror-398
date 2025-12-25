"""
Centralized logging configuration for the worker process.

This module provides:
- Dynamic log level configuration via KUBIYA_CLI_LOG_LEVEL environment variable
- Multiple log format support (pretty, json, text) via KUBIYA_LOG_FORMAT
- Backward compatibility with CLAUDE_CODE_DEBUG
- Sensitive data sanitization helpers
- Unified structlog configuration
"""

import os
import logging
import time
import structlog
from typing import Any, Dict


def get_log_level() -> int:
    """
    Get log level from environment variables with fallback hierarchy.

    Priority:
    1. KUBIYA_CLI_LOG_LEVEL (new, preferred)
    2. LOG_LEVEL (generic fallback)
    3. CLAUDE_CODE_DEBUG=true → DEBUG (deprecated, with warning)
    4. Default: INFO

    Returns:
        int: Python logging level constant (logging.DEBUG, logging.INFO, etc.)
    """
    logger = structlog.get_logger(__name__)

    # Check KUBIYA_CLI_LOG_LEVEL first (preferred)
    kubiya_log_level = os.getenv("KUBIYA_CLI_LOG_LEVEL", "").upper()
    if kubiya_log_level:
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        if kubiya_log_level in level_map:
            return level_map[kubiya_log_level]

    # Check generic LOG_LEVEL
    log_level = os.getenv("LOG_LEVEL", "").upper()
    if log_level:
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        if log_level in level_map:
            return level_map[log_level]

    # Check deprecated CLAUDE_CODE_DEBUG
    if os.getenv("CLAUDE_CODE_DEBUG", "false").lower() == "true":
        # Show deprecation warning (but only once, using a module-level flag)
        if not hasattr(get_log_level, "_warned"):
            logger.warning(
                "deprecated_env_var",
                old_var="CLAUDE_CODE_DEBUG",
                new_var="KUBIYA_CLI_LOG_LEVEL",
                message="CLAUDE_CODE_DEBUG is deprecated. Please use KUBIYA_CLI_LOG_LEVEL=DEBUG instead."
            )
            get_log_level._warned = True
        return logging.DEBUG

    # Default to INFO
    return logging.INFO


def get_log_format() -> str:
    """
    Get log format from environment variable.

    Priority:
    1. KUBIYA_LOG_FORMAT
    2. Default: "pretty"

    Supported formats:
    - pretty: Human-readable colored output with emojis (default)
    - json: JSON-formatted for log aggregation
    - text: Simple text without colors

    Returns:
        str: Log format ("pretty", "json", or "text")
    """
    log_format = os.getenv("KUBIYA_LOG_FORMAT", "pretty").lower()
    if log_format not in ["pretty", "json", "text"]:
        # Invalid format, default to pretty
        return "pretty"
    return log_format


def sanitize_value(key: str, value: Any) -> str:
    """
    Sanitize sensitive values based on key name.

    Keys containing TOKEN, SECRET, PASSWORD, KEY, or CREDENTIAL will be masked.
    Shows first 10 and last 5 characters for values longer than 15 chars,
    otherwise shows "***".

    Args:
        key: The key/variable name
        value: The value to potentially sanitize

    Returns:
        str: Sanitized value if key is sensitive, otherwise original value as string
    """
    sensitive_keywords = ["TOKEN", "SECRET", "PASSWORD", "KEY", "CREDENTIAL"]

    # Check if key contains any sensitive keyword
    is_sensitive = any(keyword in key.upper() for keyword in sensitive_keywords)

    if not is_sensitive:
        return str(value)

    # Sanitize sensitive value
    value_str = str(value)
    if len(value_str) > 15:
        return f"{value_str[:10]}...{value_str[-5:]}"
    else:
        return "***"


def pretty_console_renderer(logger, name, event_dict):
    """
    Render logs in a pretty, human-readable format instead of JSON.
    Uses colors and emojis for better readability.

    Args:
        logger: The logger instance
        name: The logger name
        event_dict: Dictionary containing log event data

    Returns:
        str: Formatted log message
    """
    level = event_dict.get("level", "info").upper()
    event = event_dict.get("event", "")
    timestamp = event_dict.get("timestamp", "")

    # Extract timestamp (just time part)
    if timestamp:
        try:
            time_part = timestamp.split("T")[1].split(".")[0]  # HH:MM:SS
        except:
            time_part = timestamp
    else:
        time_part = time.strftime("%H:%M:%S")

    # Color codes
    RESET = "\033[0m"
    GRAY = "\033[90m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"

    # Level icons and colors
    level_config = {
        "INFO": ("ℹ️", CYAN),
        "WARNING": ("⚠️", YELLOW),
        "ERROR": ("❌", RED),
        "DEBUG": ("🔍", GRAY),
    }

    icon, color = level_config.get(level, ("•", RESET))

    # Format the main message
    message = f"{GRAY}[{time_part}]{RESET} {icon}  {event}"

    # Add relevant context (skip internal keys)
    skip_keys = {"level", "event", "timestamp", "logger"}
    context_parts = []

    for key, value in event_dict.items():
        if key in skip_keys:
            continue
        # Format value nicely
        if isinstance(value, bool):
            value_str = "✓" if value else "✗"
        elif isinstance(value, str) and len(value) > 60:
            value_str = value[:57] + "..."
        else:
            value_str = str(value)

        context_parts.append(f"{GRAY}{key}={RESET}{value_str}")

    if context_parts:
        message += f" {GRAY}({', '.join(context_parts)}){RESET}"

    return message


def json_renderer(logger, name, event_dict):
    """
    Render logs in JSON format for log aggregation systems.

    Args:
        logger: The logger instance
        name: The logger name
        event_dict: Dictionary containing log event data

    Returns:
        str: JSON-formatted log message
    """
    import json
    return json.dumps(event_dict)


def text_renderer(logger, name, event_dict):
    """
    Render logs in simple text format without colors.

    Args:
        logger: The logger instance
        name: The logger name
        event_dict: Dictionary containing log event data

    Returns:
        str: Simple text log message
    """
    level = event_dict.get("level", "info").upper()
    event = event_dict.get("event", "")
    timestamp = event_dict.get("timestamp", "")

    # Extract timestamp (just time part)
    if timestamp:
        try:
            time_part = timestamp.split("T")[1].split(".")[0]  # HH:MM:SS
        except:
            time_part = timestamp
    else:
        time_part = time.strftime("%H:%M:%S")

    # Format the main message
    message = f"[{time_part}] {level:8} {event}"

    # Add relevant context (skip internal keys)
    skip_keys = {"level", "event", "timestamp", "logger"}
    context_parts = []

    for key, value in event_dict.items():
        if key in skip_keys:
            continue
        context_parts.append(f"{key}={value}")

    if context_parts:
        message += f" ({', '.join(context_parts)})"

    return message


def configure_logging() -> None:
    """
    Configure structlog with dynamic settings from environment variables.

    This function sets up structlog with:
    - Dynamic log level from KUBIYA_CLI_LOG_LEVEL (or fallback)
    - Dynamic log format from KUBIYA_LOG_FORMAT
    - Appropriate renderer based on format
    - Standard processors for context and timestamps

    Should be called once at application startup before any logging occurs.
    """
    log_level = get_log_level()
    log_format = get_log_format()

    # Select renderer based on format
    if log_format == "json":
        renderer = json_renderer
    elif log_format == "text":
        renderer = text_renderer
    else:  # "pretty" (default)
        renderer = pretty_console_renderer

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
    )
