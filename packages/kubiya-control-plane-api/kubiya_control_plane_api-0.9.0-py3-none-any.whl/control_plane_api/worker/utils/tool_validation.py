"""
Universal Tool Name Validation for All LLM Providers

This module provides strict tool name validation that works across ALL major LLM providers:
- OpenAI/Azure OpenAI
- Anthropic Claude
- Google Vertex AI/Gemini
- AWS Bedrock

The validation rules are the strictest common denominator to ensure compatibility everywhere.
"""

import re
import structlog
from typing import List, Tuple, Dict, Any

logger = structlog.get_logger(__name__)

# Universal tool name pattern - works for ALL LLM providers
# Rules:
# 1. Must start with letter (a-z, A-Z) or underscore (_)
# 2. Can only contain: letters, numbers, underscores
# 3. Maximum length: 64 characters
# 4. Minimum length: 1 character
UNIVERSAL_TOOL_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]{0,63}$')

# Characters that are safe across all providers
SAFE_CHARS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')


class ToolValidationError(Exception):
    """Raised when tool validation fails and cannot be auto-fixed."""
    pass


def validate_tool_name(name: str, provider_context: str = "universal") -> Tuple[bool, str, List[str]]:
    """
    Validate a tool name against universal LLM provider requirements.

    Args:
        name: The tool name to validate
        provider_context: Context string for logging (e.g., "vertex_ai", "openai")

    Returns:
        Tuple of (is_valid, error_message, list_of_violations)

    Example:
        >>> validate_tool_name("my_tool")
        (True, "", [])
        >>> validate_tool_name("123invalid")
        (False, "Tool name must start with letter or underscore", ["invalid_start"])
    """
    violations = []

    if not name:
        return False, "Tool name cannot be empty", ["empty_name"]

    if not isinstance(name, str):
        return False, f"Tool name must be string, got {type(name)}", ["invalid_type"]

    # Check length
    if len(name) > 64:
        violations.append("exceeds_max_length")

    if len(name) == 0:
        return False, "Tool name cannot be empty", ["empty_name"]

    # Check first character
    if not (name[0].isalpha() or name[0] == '_'):
        violations.append("invalid_start")

    # Check for invalid characters
    invalid_chars = set()
    for char in name:
        if char not in SAFE_CHARS:
            invalid_chars.add(char)

    if invalid_chars:
        violations.append(f"invalid_chars_{','.join(sorted(invalid_chars))}")

    # Check full pattern
    if not UNIVERSAL_TOOL_NAME_PATTERN.match(name):
        if "invalid_start" not in violations and "exceeds_max_length" not in violations:
            violations.append("pattern_mismatch")

    if violations:
        error_msg = f"Tool name '{name}' is invalid for {provider_context}: {', '.join(violations)}"
        return False, error_msg, violations

    return True, "", []


def sanitize_tool_name(name: str, prefix: str = "", max_length: int = 64) -> str:
    """
    Sanitize a tool name to make it valid for all LLM providers.

    This function aggressively cleans tool names to ensure compatibility:
    - Replaces invalid characters with underscores
    - Ensures it starts with letter or underscore
    - Truncates to max_length
    - Collapses multiple underscores

    Args:
        name: The tool name to sanitize
        prefix: Optional prefix to add (useful for namespacing)
        max_length: Maximum allowed length (default 64)

    Returns:
        Sanitized tool name that passes validation

    Example:
        >>> sanitize_tool_name("my-tool!")
        "my_tool"
        >>> sanitize_tool_name("123tool")
        "_123tool"
        >>> sanitize_tool_name("grounding::query_data")
        "grounding_query_data"
    """
    if not name:
        return "unnamed_tool"

    # Add prefix if provided
    if prefix:
        name = f"{prefix}_{name}"

    # Replace all invalid characters with underscores
    sanitized = ""
    for char in name:
        if char in SAFE_CHARS:
            sanitized += char
        else:
            sanitized += "_"

    # Collapse multiple underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")

    # Remove leading/trailing underscores except one if needed for start
    sanitized = sanitized.strip("_")

    # Ensure starts with letter or underscore
    if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
        sanitized = f"_{sanitized}"

    # Handle empty result
    if not sanitized:
        sanitized = "tool" if not prefix else prefix

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        # Ensure we didn't cut in a way that makes it invalid
        sanitized = sanitized.rstrip("_")

    # Final validation - if still invalid, use fallback
    is_valid, _, _ = validate_tool_name(sanitized)
    if not is_valid:
        logger.warning(f"Sanitization failed for '{name}', using fallback name")
        return "sanitized_tool"

    return sanitized


def validate_and_sanitize_tools(
    tools: List[Any],
    tool_name_getter: callable = lambda t: getattr(t, 'name', str(t)),
    auto_fix: bool = True,
    provider_context: str = "universal"
) -> Tuple[List[Any], List[Dict[str, Any]]]:
    """
    Validate and optionally sanitize a list of tools.

    Args:
        tools: List of tool objects to validate
        tool_name_getter: Function to extract tool name from tool object
        auto_fix: If True, sanitize invalid tool names; if False, filter them out
        provider_context: Context for error messages

    Returns:
        Tuple of (validated_tools, validation_report)
        - validated_tools: List of tools with valid names
        - validation_report: List of dicts with validation details

    Example:
        >>> tools = [Tool(name="valid_tool"), Tool(name="invalid-tool!")]
        >>> valid_tools, report = validate_and_sanitize_tools(tools)
        >>> len(valid_tools)
        2
        >>> report[1]['action']
        'sanitized'
    """
    validated_tools = []
    validation_report = []

    for i, tool in enumerate(tools):
        try:
            original_name = tool_name_getter(tool)
            is_valid, error_msg, violations = validate_tool_name(original_name, provider_context)

            if is_valid:
                validated_tools.append(tool)
                validation_report.append({
                    "index": i,
                    "original_name": original_name,
                    "final_name": original_name,
                    "action": "passed",
                    "violations": []
                })
            else:
                if auto_fix:
                    # Try to sanitize
                    sanitized_name = sanitize_tool_name(original_name)

                    # Update tool name if possible
                    if hasattr(tool, 'name'):
                        tool.name = sanitized_name

                    validated_tools.append(tool)
                    validation_report.append({
                        "index": i,
                        "original_name": original_name,
                        "final_name": sanitized_name,
                        "action": "sanitized",
                        "violations": violations,
                        "error": error_msg
                    })

                    logger.warning(
                        f"Tool name sanitized for {provider_context}: "
                        f"'{original_name}' -> '{sanitized_name}' (violations: {violations})"
                    )
                else:
                    # Filter out invalid tool
                    validation_report.append({
                        "index": i,
                        "original_name": original_name,
                        "final_name": None,
                        "action": "filtered",
                        "violations": violations,
                        "error": error_msg
                    })

                    logger.error(
                        f"Tool filtered out for {provider_context}: "
                        f"'{original_name}' - {error_msg}"
                    )
        except Exception as e:
            logger.error(f"Error validating tool at index {i}: {e}")
            validation_report.append({
                "index": i,
                "original_name": "unknown",
                "final_name": None,
                "action": "error",
                "violations": ["exception"],
                "error": str(e)
            })

    return validated_tools, validation_report


def validate_tool_definition(tool_def: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a tool definition dictionary (OpenAI/Anthropic format).

    Args:
        tool_def: Tool definition dict with 'name' and optionally 'function'

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(tool_def, dict):
        return False, "Tool definition must be a dictionary"

    # Check for function.name (OpenAI format)
    if "function" in tool_def:
        if "name" not in tool_def["function"]:
            return False, "Tool function missing 'name' field"
        tool_name = tool_def["function"]["name"]
    # Check for name (Anthropic format)
    elif "name" in tool_def:
        tool_name = tool_def["name"]
    else:
        return False, "Tool definition missing 'name' field"

    is_valid, error_msg, _ = validate_tool_name(tool_name)
    return is_valid, error_msg


def get_provider_specific_requirements() -> Dict[str, Dict[str, Any]]:
    """
    Get provider-specific tool name requirements for reference.

    Returns:
        Dict mapping provider name to their requirements
    """
    return {
        "openai": {
            "pattern": r'^[a-zA-Z0-9_-]{1,64}$',
            "description": "1-64 chars, letters, numbers, hyphens, underscores"
        },
        "anthropic": {
            "pattern": r'^[a-zA-Z0-9_]{1,64}$',
            "description": "1-64 chars, letters, numbers, underscores"
        },
        "vertex_ai": {
            "pattern": r'^[a-zA-Z_][a-zA-Z0-9_\.\:\-]{0,63}$',
            "description": "Start with letter/underscore, letters, numbers, underscore, dot, colon, dash, max 64"
        },
        "bedrock": {
            "pattern": r'^[a-zA-Z][a-zA-Z0-9_]{0,63}$',
            "description": "Start with letter, letters, numbers, underscores, max 64"
        },
        "universal": {
            "pattern": UNIVERSAL_TOOL_NAME_PATTERN.pattern,
            "description": "Start with letter/underscore, letters, numbers, underscores only, max 64 (strictest common)"
        }
    }


# Quick validation functions for common use cases

def is_valid_tool_name(name: str) -> bool:
    """Quick check if a tool name is valid."""
    is_valid, _, _ = validate_tool_name(name)
    return is_valid


def assert_valid_tool_name(name: str, context: str = ""):
    """Assert tool name is valid, raise exception if not."""
    is_valid, error_msg, _ = validate_tool_name(name, context)
    if not is_valid:
        raise ToolValidationError(f"{context}: {error_msg}" if context else error_msg)
