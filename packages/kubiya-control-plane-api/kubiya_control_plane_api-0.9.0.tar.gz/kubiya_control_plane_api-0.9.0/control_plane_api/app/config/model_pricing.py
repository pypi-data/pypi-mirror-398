"""
Model Pricing and AEM Weight Configuration

This module defines pricing tiers and Agentic Engineering Minutes (AEM) weights
for different model families.

AEM Formula: Runtime (minutes) × Model Weight × Tool Calls Weight

Model Weights:
- Opus-class (most capable): 2.0x weight
- Sonnet-class (balanced): 1.0x weight
- Haiku-class (fast): 0.5x weight
"""

from typing import Dict, Any
from enum import Enum


class ModelTier(str, Enum):
    """Universal model capability tiers (provider-agnostic)"""
    PREMIUM = "premium"  # Most capable: Opus, GPT-4, o1, Gemini Pro (weight >= 1.5)
    MID = "mid"         # Balanced: Sonnet, GPT-4o, Gemini Flash (weight 0.8-1.4)
    BASIC = "basic"     # Fast/efficient: Haiku, GPT-3.5, mini models (weight < 0.8)
    CUSTOM = "custom"   # Custom/unknown models


# Model Weight Configuration for AEM Calculation
MODEL_WEIGHTS: Dict[str, float] = {
    # Anthropic Claude Models
    "claude-opus-4": 2.0,
    "claude-4-opus": 2.0,
    "claude-3-opus": 2.0,
    "claude-3-opus-20240229": 2.0,

    "claude-sonnet-4": 1.0,
    "claude-4-sonnet": 1.0,
    "claude-3.5-sonnet": 1.0,
    "claude-3-5-sonnet-20241022": 1.0,
    "claude-3-sonnet": 1.0,
    "claude-3-sonnet-20240229": 1.0,

    "claude-haiku-4": 0.5,
    "claude-4-haiku": 0.5,
    "claude-3.5-haiku": 0.5,
    "claude-3-5-haiku-20241022": 0.5,
    "claude-3-haiku": 0.5,
    "claude-3-haiku-20240307": 0.5,

    # OpenAI Models
    "gpt-4": 2.0,
    "gpt-4-turbo": 2.0,
    "gpt-4-turbo-preview": 2.0,
    "gpt-4-0125-preview": 2.0,
    "gpt-4-1106-preview": 2.0,
    "gpt-4o": 1.3,  # As shown in the image
    "gpt-4o-mini": 0.7,

    "gpt-3.5-turbo": 0.5,
    "gpt-3.5-turbo-16k": 0.5,

    # Google Models
    "gemini-1.5-pro": 1.5,
    "gemini-1.5-flash": 0.7,
    "gemini-pro": 1.0,

    # Meta Models
    "llama-3-70b": 1.2,
    "llama-3-8b": 0.5,

    # Mistral Models
    "mistral-large": 1.5,
    "mistral-medium": 1.0,
    "mistral-small": 0.5,
}


# Token Pricing per 1M tokens (in USD)
TOKEN_PRICING: Dict[str, Dict[str, float]] = {
    # Anthropic Claude
    "claude-opus-4": {
        "input": 15.00,
        "output": 75.00,
        "cache_read": 1.50,
        "cache_creation": 18.75,
    },
    "claude-sonnet-4": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_creation": 3.75,
    },
    "claude-haiku-4": {
        "input": 0.80,
        "output": 4.00,
        "cache_read": 0.08,
        "cache_creation": 1.00,
    },

    # OpenAI
    "gpt-4": {
        "input": 30.00,
        "output": 60.00,
        "cache_read": 0.0,
        "cache_creation": 0.0,
    },
    "gpt-4o": {
        "input": 5.00,
        "output": 15.00,
        "cache_read": 0.0,
        "cache_creation": 0.0,
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50,
        "cache_read": 0.0,
        "cache_creation": 0.0,
    },

    # Google Gemini
    "gemini-1.5-pro": {
        "input": 3.50,
        "output": 10.50,
        "cache_read": 0.0,
        "cache_creation": 0.0,
    },
    "gemini-1.5-flash": {
        "input": 0.35,
        "output": 1.05,
        "cache_read": 0.0,
        "cache_creation": 0.0,
    },
}


# AEM Pricing Configuration
AEM_PRICING: Dict[str, float] = {
    "saas_prepaid_per_minute": 0.15,  # $0.15/min for SaaS/Hybrid
    "on_prem_unlimited": 0.0,          # Unlimited for on-prem
}


def get_model_weight(model: str) -> float:
    """
    Get the AEM weight for a model.

    Args:
        model: Model identifier

    Returns:
        Weight multiplier for AEM calculation (default 1.0)
    """
    # Normalize model name
    model_lower = model.lower().strip()

    # Try exact match first
    if model_lower in MODEL_WEIGHTS:
        return MODEL_WEIGHTS[model_lower]

    # Try fuzzy matching by keywords
    if "opus" in model_lower:
        return 2.0
    elif "sonnet" in model_lower:
        return 1.0
    elif "haiku" in model_lower:
        return 0.5
    elif "gpt-4" in model_lower and "turbo" in model_lower:
        return 2.0
    elif "gpt-4o" in model_lower:
        return 1.3
    elif "gpt-3.5" in model_lower:
        return 0.5
    elif "gemini" in model_lower and "pro" in model_lower:
        return 1.5
    elif "gemini" in model_lower and "flash" in model_lower:
        return 0.7

    # Default weight
    return 1.0


def get_model_tier(model: str) -> ModelTier:
    """
    Determine the tier/class of a model using provider-agnostic naming.

    Tier Classification:
    - Premium (weight >= 1.5): Most capable models (Claude Opus, GPT-4, o1, Gemini Pro)
    - Mid (weight 0.8-1.4): Balanced models (Claude Sonnet, GPT-4o, Gemini Flash)
    - Basic (weight < 0.8): Fast/efficient models (Claude Haiku, GPT-3.5, mini models)

    Args:
        model: Model identifier

    Returns:
        ModelTier enum value
    """
    weight = get_model_weight(model)

    if weight >= 1.5:
        return ModelTier.PREMIUM
    elif weight >= 0.8:
        return ModelTier.MID
    elif weight >= 0.3:
        return ModelTier.BASIC
    else:
        return ModelTier.CUSTOM


def calculate_token_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
) -> Dict[str, float]:
    """
    Calculate token costs based on model pricing.

    Args:
        model: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cache_read_tokens: Number of cached tokens read
        cache_creation_tokens: Number of tokens used for cache creation

    Returns:
        Dict with cost breakdown
    """
    # Normalize model name
    model_lower = model.lower().strip()

    # Get pricing (use closest match or default to sonnet pricing)
    pricing = None

    # Try exact match
    for price_key in TOKEN_PRICING:
        if price_key in model_lower or model_lower in price_key:
            pricing = TOKEN_PRICING[price_key]
            break

    # Default to sonnet pricing if no match
    if pricing is None:
        pricing = TOKEN_PRICING["claude-sonnet-4"]

    # Calculate costs (pricing is per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    cache_read_cost = (cache_read_tokens / 1_000_000) * pricing["cache_read"]
    cache_creation_cost = (cache_creation_tokens / 1_000_000) * pricing["cache_creation"]

    return {
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "cache_read_cost": round(cache_read_cost, 6),
        "cache_creation_cost": round(cache_creation_cost, 6),
        "total_cost": round(input_cost + output_cost + cache_read_cost + cache_creation_cost, 6),
    }


def calculate_aem(
    duration_ms: int,
    model: str,
    tool_calls_count: int,
    tool_calls_weight: float = 1.0,
) -> Dict[str, float]:
    """
    Calculate Agentic Engineering Minutes (AEM).

    Formula: Runtime (minutes) × Model Weight × Tool Calls Weight

    Args:
        duration_ms: Turn duration in milliseconds
        model: Model identifier
        tool_calls_count: Number of tool calls in this turn
        tool_calls_weight: Weight multiplier for tool complexity (default 1.0)

    Returns:
        Dict with AEM metrics
    """
    # Convert duration to minutes
    runtime_minutes = duration_ms / 60_000.0

    # Get model weight
    model_weight = get_model_weight(model)

    # Calculate tool calls weight (simple linear for now, can be made more complex)
    # Example: Each tool call adds to complexity
    # From the image example: 200 tool calls = 3.9 weight
    # This suggests approximately: tool_calls_weight = (tool_calls_count / 50) if tool_calls_count > 0 else 1.0
    if tool_calls_count > 0:
        calculated_tool_weight = max(1.0, tool_calls_count / 50.0)  # Roughly matches 200 calls = 4.0
    else:
        calculated_tool_weight = 1.0

    # Override with provided weight if specified
    final_tool_weight = tool_calls_weight if tool_calls_weight != 1.0 else calculated_tool_weight

    # Calculate AEM value
    aem_value = runtime_minutes * model_weight * final_tool_weight

    # Calculate AEM cost (using SaaS pricing)
    aem_cost = aem_value * AEM_PRICING["saas_prepaid_per_minute"]

    return {
        "runtime_minutes": round(runtime_minutes, 4),
        "model_weight": round(model_weight, 2),
        "tool_calls_weight": round(final_tool_weight, 2),
        "aem_value": round(aem_value, 4),
        "aem_cost": round(aem_cost, 4),
        "model_tier": get_model_tier(model).value,
    }


# Export configuration for external use
__all__ = [
    "ModelTier",
    "MODEL_WEIGHTS",
    "TOKEN_PRICING",
    "AEM_PRICING",
    "get_model_weight",
    "get_model_tier",
    "calculate_token_cost",
    "calculate_aem",
]
