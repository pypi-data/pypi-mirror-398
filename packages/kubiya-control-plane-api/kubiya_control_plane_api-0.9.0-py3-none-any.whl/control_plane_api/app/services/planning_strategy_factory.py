"""
Planning Strategy Factory

Factory for creating the appropriate planning strategy based on configuration.
Like a travel agency - chooses the best transportation mode for you!
"""

import os
import structlog
from typing import Literal
from sqlalchemy.orm import Session

from control_plane_api.app.services.planning_strategy import PlanningStrategy
from control_plane_api.app.services.claude_code_planning_service import ClaudeCodePlanningStrategy
from control_plane_api.app.services.agno_planning_strategy import AgnoPlanningStrategy

logger = structlog.get_logger(__name__)

# Supported strategy types
StrategyType = Literal["claude_code_sdk", "agno"]


def get_planning_strategy(
    strategy_type: StrategyType = None,
    db: Session = None,
    organization_id: str = None,
    api_token: str = None
) -> PlanningStrategy:
    """
    Factory function to create the appropriate planning strategy.

    Args:
        strategy_type: Which strategy to use ("claude_code_sdk" or "agno")
                      If None, uses PLANNING_STRATEGY env var (defaults to "agno")
        db: Database session
        organization_id: Organization ID
        api_token: API token

    Returns:
        Concrete PlanningStrategy implementation

    Example:
        # Use Claude Code SDK (default)
        strategy = get_planning_strategy(db=db)

        # Explicitly use Agno
        strategy = get_planning_strategy(strategy_type="agno", db=db)

        # Use both in your code
        plan = await strategy.plan_task(prompt)  # Same interface!
    """
    # Determine strategy from parameter or env var
    if strategy_type is None:
        strategy_type = os.getenv("PLANNING_STRATEGY", "agno").lower()

    logger.info(
        "creating_planning_strategy",
        strategy_type=strategy_type,
        has_db=db is not None,
        has_org_id=organization_id is not None,
    )

    # Validate strategy availability and detect CLI
    if strategy_type == "claude_code_sdk":
        # Check if SDK is available
        try:
            from claude_agent_sdk import ClaudeSDKClient
        except ImportError:
            logger.error(
                "strategy_unavailable",
                strategy_type=strategy_type,
                message="claude-agent-sdk not available, falling back to Agno"
            )
            strategy_type = "agno"  # Fallback
        else:
            # Check if Claude CLI binary is available
            import shutil
            claude_cli = shutil.which("claude")
            if not claude_cli:
                logger.warning(
                    "claude_cli_not_found",
                    message="Claude Code CLI binary not found in PATH. Falling back to Agno.",
                    hint="Install @anthropic-ai/claude-code npm package or use PLANNING_STRATEGY=agno"
                )
                strategy_type = "agno"  # Auto-fallback
            else:
                logger.info(
                    "claude_cli_found",
                    cli_path=claude_cli,
                    message="Claude Code CLI available, using claude_code_sdk strategy"
                )

    # Create the appropriate strategy
    if strategy_type == "claude_code_sdk":
        return ClaudeCodePlanningStrategy(
            db=db,
            organization_id=organization_id,
            api_token=api_token
        )
    elif strategy_type == "agno":
        return AgnoPlanningStrategy(
            db=db,
            organization_id=organization_id,
            api_token=api_token
        )
    else:
        logger.error("unknown_strategy_type", strategy_type=strategy_type)
        # Default to Claude Code SDK
        logger.warning("defaulting_to_claude_code_sdk")
        return ClaudeCodePlanningStrategy(
            db=db,
            organization_id=organization_id,
            api_token=api_token
        )


# Convenience alias for backward compatibility
get_claude_code_planning_service = get_planning_strategy
