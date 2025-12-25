"""
LiteLLM Pricing Integration - Fetch and cache model pricing data
"""

import httpx
import structlog
from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio

logger = structlog.get_logger()

# Cache for pricing data
_pricing_cache: Optional[Dict] = None
_cache_timestamp: Optional[datetime] = None
_cache_lock = asyncio.Lock()

PRICING_URL = "https://raw.githubusercontent.com/BerriAI/litellm/refs/heads/main/model_prices_and_context_window.json"
CACHE_TTL_HOURS = 24  # Refresh pricing data daily


async def get_litellm_pricing() -> Dict:
    """
    Fetch LiteLLM pricing data with caching

    Returns:
        Dict containing model pricing information
    """
    global _pricing_cache, _cache_timestamp

    async with _cache_lock:
        # Check if cache is valid
        if _pricing_cache and _cache_timestamp:
            age = datetime.utcnow() - _cache_timestamp
            if age < timedelta(hours=CACHE_TTL_HOURS):
                logger.debug("litellm_pricing_cache_hit", age_hours=age.total_seconds() / 3600)
                return _pricing_cache

        # Fetch fresh pricing data
        logger.info("fetching_litellm_pricing", url=PRICING_URL)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(PRICING_URL)
                response.raise_for_status()
                pricing_data = response.json()

                # Update cache
                _pricing_cache = pricing_data
                _cache_timestamp = datetime.utcnow()

                logger.info(
                    "litellm_pricing_fetched_successfully",
                    models_count=len(pricing_data),
                    cached_until=(_cache_timestamp + timedelta(hours=CACHE_TTL_HOURS)).isoformat()
                )

                return pricing_data
        except Exception as e:
            logger.error("litellm_pricing_fetch_failed", error=str(e), error_type=type(e).__name__)
            # Return empty dict on failure
            return {}


def get_model_pricing(model_id: str, pricing_data: Dict) -> Optional[Dict]:
    """
    Get pricing information for a specific model

    Args:
        model_id: Model identifier (e.g., "claude-sonnet-4", "gpt-4o")
        pricing_data: Full pricing data from LiteLLM

    Returns:
        Dict with pricing info or None if not found
    """
    # Try exact match first
    if model_id in pricing_data:
        return pricing_data[model_id]

    # Try common variations
    variations = [
        model_id,
        f"openai/{model_id}",
        f"anthropic/{model_id}",
        f"anthropic.{model_id}",
        f"bedrock/{model_id}",
    ]

    for variation in variations:
        if variation in pricing_data:
            return pricing_data[variation]

    logger.warning("model_pricing_not_found", model_id=model_id, tried_variations=variations)
    return None


def calculate_llm_cost(
    model_id: str,
    estimated_input_tokens: int,
    estimated_output_tokens: int,
    pricing_data: Dict
) -> tuple[float, float, float]:
    """
    Calculate LLM cost for a model

    Args:
        model_id: Model identifier
        estimated_input_tokens: Expected input tokens
        estimated_output_tokens: Expected output tokens
        pricing_data: Full pricing data from LiteLLM

    Returns:
        Tuple of (cost_per_1k_input, cost_per_1k_output, total_cost)
    """
    model_pricing = get_model_pricing(model_id, pricing_data)

    if not model_pricing:
        # Fallback defaults
        logger.warning("using_default_pricing", model_id=model_id)
        return (0.003, 0.015, 0.0)

    input_cost_per_token = model_pricing.get("input_cost_per_token", 0.000003)
    output_cost_per_token = model_pricing.get("output_cost_per_token", 0.000015)

    # Convert to per-1k pricing for display
    input_cost_per_1k = input_cost_per_token * 1000
    output_cost_per_1k = output_cost_per_token * 1000

    # Calculate total cost
    total_cost = (
        (estimated_input_tokens * input_cost_per_token) +
        (estimated_output_tokens * output_cost_per_token)
    )

    return (input_cost_per_1k, output_cost_per_1k, total_cost)


def get_model_display_name(model_id: str) -> str:
    """
    Get human-readable model name

    Args:
        model_id: Model identifier

    Returns:
        Display name
    """
    # Map of common model IDs to display names
    display_names = {
        "claude-sonnet-4": "Claude Sonnet 4",
        "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet",
        "claude-3-5-sonnet-20240620": "Claude 3.5 Sonnet (Legacy)",
        "claude-3-opus-20240229": "Claude 3 Opus",
        "claude-3-haiku-20240307": "Claude 3 Haiku",
        "gpt-4o": "GPT-4o",
        "gpt-4o-mini": "GPT-4o Mini",
        "gpt-4-turbo": "GPT-4 Turbo",
        "gpt-4": "GPT-4",
        "gpt-3.5-turbo": "GPT-3.5 Turbo",
        "o1": "OpenAI o1",
        "o1-mini": "OpenAI o1-mini",
        "gemini-2.0-flash-exp": "Gemini 2.0 Flash",
        "gemini-1.5-pro": "Gemini 1.5 Pro",
        "gemini-1.5-flash": "Gemini 1.5 Flash",
    }

    return display_names.get(model_id, model_id.replace("-", " ").title())
