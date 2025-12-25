"""
API router for LLM models configuration
"""
from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/models", tags=["models"])


class LLMModel(BaseModel):
    """LLM Model configuration"""
    value: str
    label: str
    provider: str
    logo: str
    recommended: bool = False
    description: Optional[str] = None


# Kubiya's supported LLM models
# NOTE: All models must include "kubiya/" prefix for LiteLLM routing
KUBIYA_LLM_MODELS = [
    LLMModel(
        value="kubiya/claude-sonnet-4",
        label="Claude Sonnet 4",
        provider="Anthropic",
        logo="/logos/claude-color.svg",
        recommended=True,
        description="Most intelligent model with best reasoning capabilities"
    ),
    LLMModel(
        value="kubiya/claude-opus-4",
        label="Claude Opus 4",
        provider="Anthropic",
        logo="/logos/claude-color.svg",
        description="Powerful model for complex tasks requiring deep analysis"
    ),
    LLMModel(
        value="kubiya/gpt-4o",
        label="GPT-4o",
        provider="OpenAI",
        logo="/thirdparty/logos/openai.svg",
        description="Fast and capable model with vision support"
    ),
    LLMModel(
        value="kubiya/gpt-4-turbo",
        label="GPT-4 Turbo",
        provider="OpenAI",
        logo="/thirdparty/logos/openai.svg",
        description="Enhanced GPT-4 with improved speed and capabilities"
    ),
    LLMModel(
        value="kubiya/claude-3-5-sonnet-20241022",
        label="Claude 3.5 Sonnet",
        provider="Anthropic",
        logo="/logos/claude-color.svg",
        description="Previous generation Sonnet with excellent performance"
    ),
]


@router.get("", response_model=List[LLMModel])
async def list_models():
    """
    Get list of available LLM models.

    Returns:
        List of LLM model configurations with logos and metadata
    """
    return KUBIYA_LLM_MODELS


@router.get("/default", response_model=LLMModel)
async def get_default_model():
    """
    Get the default recommended LLM model.

    Returns:
        The recommended default model configuration
    """
    return next((model for model in KUBIYA_LLM_MODELS if model.recommended), KUBIYA_LLM_MODELS[0])
