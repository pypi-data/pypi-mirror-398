"""
Model selection utilities for runtime execution.

This module provides centralized model selection logic that respects:
1. KUBIYA_MODEL_OVERRIDE (highest priority - from CLI --model flag)
2. RuntimeExecutionContext.model_id (from agent/execution configuration)
3. LITELLM_DEFAULT_MODEL (default fallback)

Usage:
    from control_plane_api.worker.runtimes.model_utils import get_effective_model

    model = get_effective_model(context.model_id)
"""

import os
import structlog

logger = structlog.get_logger(__name__)

# Default model to use if no other configuration is provided
DEFAULT_MODEL = "kubiya/claude-sonnet-4"


def get_effective_model(
    context_model_id: str = None,
    log_context: dict = None,
) -> str:
    """
    Get the effective model ID to use for execution.

    Priority order (highest to lowest):
    1. KUBIYA_MODEL_OVERRIDE environment variable (from CLI --model flag)
    2. context_model_id (from RuntimeExecutionContext.model_id or agent config)
    3. LITELLM_DEFAULT_MODEL environment variable
    4. DEFAULT_MODEL constant ("kubiya/claude-sonnet-4")

    Args:
        context_model_id: Model ID from execution context (optional)
        log_context: Additional context for logging (execution_id, etc.)

    Returns:
        The effective model ID to use
    """
    log_ctx = log_context or {}

    # Priority 1: Environment override (from CLI --model flag)
    model_override = os.environ.get("KUBIYA_MODEL_OVERRIDE")
    if model_override:
        logger.info(
            "model_override_active",
            effective_model=model_override,
            source="KUBIYA_MODEL_OVERRIDE",
            overridden_context_model=context_model_id,
            note="Explicit model override from CLI --model flag or KUBIYA_MODEL env var",
            **log_ctx,
        )
        return model_override

    # Priority 2: Context model_id (from agent/execution configuration)
    if context_model_id:
        logger.debug(
            "using_context_model",
            effective_model=context_model_id,
            source="context.model_id",
            **log_ctx,
        )
        return context_model_id

    # Priority 3: Environment default
    env_default = os.environ.get("LITELLM_DEFAULT_MODEL")
    if env_default:
        logger.debug(
            "using_env_default_model",
            effective_model=env_default,
            source="LITELLM_DEFAULT_MODEL",
            **log_ctx,
        )
        return env_default

    # Priority 4: Hardcoded default
    logger.debug(
        "using_hardcoded_default_model",
        effective_model=DEFAULT_MODEL,
        source="DEFAULT_MODEL",
        **log_ctx,
    )
    return DEFAULT_MODEL


def is_model_override_active() -> bool:
    """
    Check if an explicit model override is active.

    Returns:
        True if KUBIYA_MODEL_OVERRIDE is set
    """
    return bool(os.environ.get("KUBIYA_MODEL_OVERRIDE"))


def get_model_override() -> str:
    """
    Get the model override value if set.

    Returns:
        The override model ID or None if not set
    """
    return os.environ.get("KUBIYA_MODEL_OVERRIDE")
