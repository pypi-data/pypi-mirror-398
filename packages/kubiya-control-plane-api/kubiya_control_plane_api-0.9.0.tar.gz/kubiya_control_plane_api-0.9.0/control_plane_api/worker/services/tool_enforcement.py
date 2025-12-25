"""
Tool enforcement service for policy-based tool governance.

This module provides non-blocking enforcement checks that run in parallel
with tool execution, injecting policy violations into tool results.
"""

import asyncio
import structlog
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone

logger = structlog.get_logger(__name__)


class ToolEnforcementService:
    """
    Service for enforcing policies on tool executions.

    Features:
    - Non-blocking parallel enforcement checks
    - Violation injection into tool outputs
    - Context enrichment with user/org/agent metadata
    - Graceful degradation on enforcer failures
    """

    def __init__(self, policy_enforcer_client: Optional[Any] = None):
        """
        Initialize the tool enforcement service.

        Args:
            policy_enforcer_client: PolicyEnforcerClient instance (optional)
        """
        self.enforcer = policy_enforcer_client
        self.enabled = policy_enforcer_client is not None

    async def enforce_tool_execution(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        enforcement_context: Dict[str, Any],
        timeout: float = 2.0,
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Perform non-blocking enforcement check for tool execution.

        Args:
            tool_name: Name of tool being executed
            tool_args: Tool arguments
            enforcement_context: Full context (user, org, agent, etc.)
            timeout: Maximum time to wait for enforcement (default 2s)

        Returns:
            Tuple of (allow, violation_message, metadata)
            - allow: Whether tool is allowed (True if enforcer unavailable)
            - violation_message: Error message if denied (None if allowed)
            - metadata: Enforcement metadata (policies evaluated, etc.)
        """
        if not self.enabled:
            return True, None, {"enforcer": "disabled"}

        try:
            # Build enforcement request payload
            enforcement_payload = self._build_enforcement_payload(
                tool_name=tool_name,
                tool_args=tool_args,
                context=enforcement_context,
            )

            # Call enforcer with timeout (non-blocking)
            enforcement_result = await asyncio.wait_for(
                self.enforcer.evaluation.enforce(enforcement_payload),
                timeout=timeout,
            )

            allow = enforcement_result.get("allow", True)
            policies = enforcement_result.get("policies", [])

            if not allow:
                violation_msg = self._format_violation_message(
                    tool_name=tool_name,
                    policies=policies,
                    enforcement_result=enforcement_result,
                )
                return False, violation_msg, {
                    "enforcer": "blocked",
                    "policies": policies,
                    "enforcement_id": enforcement_result.get("id"),
                }

            return True, None, {
                "enforcer": "allowed",
                "policies": policies,
                "enforcement_id": enforcement_result.get("id"),
            }

        except asyncio.TimeoutError:
            logger.warning(
                "tool_enforcement_timeout",
                tool_name=tool_name,
                timeout=timeout,
            )
            # Fail open on timeout
            return True, None, {"enforcer": "timeout"}

        except Exception as e:
            logger.error(
                "tool_enforcement_error",
                tool_name=tool_name,
                error=str(e),
                exc_info=True,
            )
            # Fail open on error
            return True, None, {"enforcer": "error", "error": str(e)}

    def _build_enforcement_payload(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build enforcement request payload with all required context.

        Required fields:
        - tool_name, tool_arguments
        - user_email, organization_id, team_id, roles
        - execution_id, agent_id, environment
        - tool_source, tool_category, risk_level
        - timestamp
        """
        return {
            "action": "tool_execution",
            "tool": {
                "name": tool_name,
                "arguments": tool_args,
                "source": self._determine_tool_source(tool_name),
                "category": self._determine_tool_category(tool_name),
                "risk_level": self._determine_risk_level(tool_name, tool_args),
            },
            "user": {
                "email": context.get("user_email"),
                "id": context.get("user_id"),
                "roles": context.get("user_roles", []),
            },
            "organization": {
                "id": context.get("organization_id"),
                "name": context.get("organization_name"),
            },
            "team": {
                "id": context.get("team_id"),
                "name": context.get("team_name"),
            },
            "execution": {
                "execution_id": context.get("execution_id"),
                "agent_id": context.get("agent_id"),
                "environment": context.get("environment", "production"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "metadata": context.get("metadata", {}),
        }

    def _determine_tool_source(self, tool_name: str) -> str:
        """Determine tool source from name."""
        if tool_name.startswith("mcp__"):
            return "mcp"
        elif tool_name in [
            "Bash",
            "Read",
            "Write",
            "Edit",
            "Grep",
            "Glob",
            "WebFetch",
            "WebSearch",
            "TodoWrite",
            "AskUserQuestion",
        ]:
            return "builtin"
        else:
            return "skill"

    def _determine_tool_category(self, tool_name: str) -> str:
        """Categorize tool by function."""
        if tool_name in ["Bash", "Shell"]:
            return "command_execution"
        elif tool_name in ["Read", "Write", "Edit"]:
            return "file_operation"
        elif tool_name in ["Grep", "Glob", "Find"]:
            return "file_search"
        elif "api" in tool_name.lower() or "http" in tool_name.lower() or tool_name in [
            "WebFetch",
            "WebSearch",
        ]:
            return "network"
        else:
            return "general"

    def _determine_risk_level(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> str:
        """Assess risk level of tool execution."""
        # High risk: command execution, destructive file ops
        if tool_name in ["Bash", "Shell"]:
            command = tool_args.get("command", "")
            # Critical: Destructive commands
            if any(
                cmd in command
                for cmd in ["rm -rf", "dd if=", "mkfs", "> /dev/", "format"]
            ):
                return "critical"
            # High: Any command execution
            return "high"

        if tool_name == "Write":
            return "medium"

        if tool_name == "Edit":
            return "medium"

        if tool_name == "Read":
            path = tool_args.get("file_path", "")
            # High: Sensitive file access
            if any(
                sensitive in path
                for sensitive in ["/etc/passwd", ".ssh", ".env", ".key", "credentials"]
            ):
                return "high"
            return "low"

        # Network operations
        if tool_name in ["WebFetch", "WebSearch"]:
            return "medium"

        return "low"

    def _format_violation_message(
        self,
        tool_name: str,
        policies: list,
        enforcement_result: Dict[str, Any],
    ) -> str:
        """Format user-friendly violation message."""
        policy_names = ", ".join(policies) if policies else "unknown policies"
        return (
            f"Tool execution blocked by policy enforcement.\n"
            f"Tool: {tool_name}\n"
            f"Blocked by: {policy_names}\n"
            f"Enforcement ID: {enforcement_result.get('id', 'N/A')}\n"
            f"\n"
            f"Contact your administrator for access approval."
        )
