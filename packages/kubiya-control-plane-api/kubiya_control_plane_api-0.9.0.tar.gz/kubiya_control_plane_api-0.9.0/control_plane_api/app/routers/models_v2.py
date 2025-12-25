"""
LLM Models CRUD API with LiteLLM Integration

This router provides model management with native LiteLLM integration.
Models are fetched dynamically from the LiteLLM server with caching for performance.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from control_plane_api.app.models.llm_model import LLMModel as LLMModelDB
from control_plane_api.app.services.litellm_service import litellm_service
from control_plane_api.app.config import settings

logger = structlog.get_logger()

router = APIRouter()

# Cache for LiteLLM models (in-memory cache with TTL)
_models_cache: Optional[Dict[str, Any]] = None
_cache_timestamp: Optional[datetime] = None


# ==================== Pydantic Schemas ====================

class LLMModelCreate(BaseModel):
    """Schema for creating a new LLM model"""
    value: str = Field(..., description="Model identifier (e.g., 'kubiya/claude-sonnet-4')")
    label: str = Field(..., description="Display name (e.g., 'Claude Sonnet 4')")
    provider: str = Field(..., description="Provider name (e.g., 'Anthropic', 'OpenAI')")
    model_type: str = Field("text-generation", description="Model type: 'text-generation', 'embedding', 'multimodal'")
    logo: Optional[str] = Field(None, description="Logo path or URL")
    description: Optional[str] = Field(None, description="Model description")
    enabled: bool = Field(True, description="Whether model is enabled")
    recommended: bool = Field(False, description="Whether model is recommended by default")
    compatible_runtimes: List[str] = Field(
        default_factory=list,
        description="List of compatible runtime IDs (e.g., ['default', 'claude_code'])"
    )
    capabilities: dict = Field(
        default_factory=dict,
        description="Model capabilities (e.g., {'vision': true, 'max_tokens': 4096})"
    )
    pricing: Optional[dict] = Field(None, description="Pricing information")
    display_order: int = Field(1000, description="Display order (lower = shown first)")


class LLMModelUpdate(BaseModel):
    """Schema for updating an existing LLM model"""
    value: Optional[str] = None
    label: Optional[str] = None
    provider: Optional[str] = None
    model_type: Optional[str] = None
    logo: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    recommended: Optional[bool] = None
    compatible_runtimes: Optional[List[str]] = None
    capabilities: Optional[dict] = None
    pricing: Optional[dict] = None
    display_order: Optional[int] = None


class LLMModelResponse(BaseModel):
    """Schema for LLM model responses"""
    id: str
    value: str
    label: str
    provider: str
    model_type: str
    logo: Optional[str]
    description: Optional[str]
    enabled: bool
    recommended: bool
    compatible_runtimes: List[str]
    capabilities: dict
    pricing: Optional[dict]
    display_order: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ==================== Helper Functions ====================

async def fetch_models_from_litellm_cached(db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Fetch models from LiteLLM with caching and database fallback.

    Uses in-memory cache with configurable TTL to avoid hitting LiteLLM on every request.
    Falls back to:
    1. Stale cache if LiteLLM is temporarily unavailable
    2. Database models if no cache available
    3. Empty list if all sources fail

    This makes the system work seamlessly in all scenarios:
    - With LiteLLM gateway: Returns live models
    - Without LiteLLM: Returns database models (manually configured)
    - Production: Works with or without LiteLLM endpoint
    """
    global _models_cache, _cache_timestamp

    # Check if cache is valid
    if _models_cache is not None and _cache_timestamp is not None:
        cache_age = datetime.utcnow() - _cache_timestamp
        if cache_age.total_seconds() < settings.litellm_models_cache_ttl:
            logger.debug("returning_cached_models", count=len(_models_cache.get("models", [])), source=_models_cache.get("source", "unknown"))
            return _models_cache.get("models", [])

    # Cache miss or expired - try to fetch from LiteLLM
    try:
        logger.info("fetching_models_from_litellm", base_url=settings.litellm_api_base)
        models = await litellm_service.fetch_available_models()

        if models:
            # Update cache with LiteLLM models
            _models_cache = {"models": models, "source": "litellm"}
            _cache_timestamp = datetime.utcnow()

            logger.info("models_fetched_from_litellm", count=len(models), ttl=settings.litellm_models_cache_ttl)
            return models

    except Exception as e:
        logger.warning("litellm_fetch_failed", error=str(e), msg="Trying fallbacks...")

    # Fallback 1: Return stale cache if available
    if _models_cache is not None and _models_cache.get("models"):
        cache_age = (datetime.utcnow() - _cache_timestamp).total_seconds() if _cache_timestamp else float('inf')
        logger.warning("returning_stale_cache", age_seconds=cache_age, source=_models_cache.get("source", "unknown"))
        return _models_cache.get("models", [])

    # Fallback 2: Fetch from database if available
    if db is not None:
        try:
            logger.info("fetching_models_from_database")
            db_models = db.query(LLMModelDB).filter(LLMModelDB.enabled == True).all()

            if db_models:
                # Convert database models to OpenAI format for consistency
                models = [
                    {
                        "id": model.value,
                        "object": "model",
                        "created": int(model.created_at.timestamp()) if model.created_at else 0,
                        "owned_by": model.provider
                    }
                    for model in db_models
                ]

                # Cache database models
                _models_cache = {"models": models, "source": "database"}
                _cache_timestamp = datetime.utcnow()

                logger.info("models_fetched_from_database", count=len(models))
                return models

        except Exception as e:
            logger.error("database_fetch_failed", error=str(e))

    # No models available from any source
    logger.error("no_models_available_from_any_source")
    return []


def convert_litellm_model_to_response(litellm_model: Dict[str, Any]) -> LLMModelResponse:
    """Convert a LiteLLM model dict to our response format"""
    model_id = litellm_model.get("id", "")

    # Provider mapping for logo resolution
    provider_logo_map = {
        "anthropic": "/thirdparty/logos/anthropic.svg",
        "openai": "/thirdparty/logos/openai.svg",
        "google": "/thirdparty/logos/google.svg",
        "mistral": "/thirdparty/logos/mistral.svg",
        "groq": "/thirdparty/logos/groq.svg",
        "deepseek": "/thirdparty/logos/deepseek.svg",
        "xai": "/thirdparty/logos/xai.svg",
        "meta": "/logos/meta-logo.svg",
    }

    # Extract provider - handle both "provider/model" and model names
    if "/" in model_id:
        # Format: kubiya/claude-sonnet-4 or openai/gpt-4
        prefix = model_id.split("/")[0].lower()
        # Check if it's a known provider prefix
        if prefix in provider_logo_map:
            provider = prefix.capitalize()
        else:
            # It's a custom prefix (like "kubiya"), detect actual provider from model name
            model_name = model_id.split("/", 1)[1].lower()
            if "claude" in model_name:
                provider = "Anthropic"
            elif "gpt" in model_name or "o1" in model_name or "o3" in model_name:
                provider = "OpenAI"
            elif "gemini" in model_name:
                provider = "Google"
            elif "llama" in model_name:
                provider = "Meta"
            elif "mistral" in model_name:
                provider = "Mistral"
            elif "deepseek" in model_name:
                provider = "DeepSeek"
            elif "grok" in model_name:
                provider = "xAI"
            else:
                provider = prefix.capitalize()
    else:
        # No slash - try to detect from model name
        model_lower = model_id.lower()
        if "claude" in model_lower:
            provider = "Anthropic"
        elif "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
            provider = "OpenAI"
        elif "gemini" in model_lower:
            provider = "Google"
        elif "llama" in model_lower:
            provider = "Meta"
        elif "mistral" in model_lower:
            provider = "Mistral"
        elif "deepseek" in model_lower:
            provider = "DeepSeek"
        elif "grok" in model_lower:
            provider = "xAI"
        else:
            provider = litellm_model.get("owned_by", "Unknown")

    # Get logo based on provider
    provider_key = provider.lower()
    logo = provider_logo_map.get(provider_key)

    # Generate label - remove provider prefix and clean up
    if "/" in model_id:
        label_base = model_id.split("/", 1)[1]
    else:
        label_base = model_id

    # Better label formatting
    label = label_base.replace("-", " ").replace("_", " ").title()
    # Fix common capitalization issues
    label = label.replace("Gpt", "GPT").replace("Llm", "LLM").replace("Api", "API")

    # Get mode from LiteLLM and map to our model_type
    litellm_mode = litellm_model.get("mode", "completion")

    # Map LiteLLM mode to our model_type
    model_type_map = {
        "embedding": "embedding",
        "chat": "text-generation",
        "completion": "text-generation",
        "image_generation": "multimodal",
        "audio_transcription": "audio",
        "moderation": "moderation"
    }
    model_type = model_type_map.get(litellm_mode, "text-generation")

    # Determine compatible runtimes based on model ID
    compatible_runtimes = ["default"]
    if "claude" in model_id.lower():
        compatible_runtimes.append("claude_code")

    # Determine if model should be recommended
    # Prioritize Claude Sonnet 4 variants
    model_lower = model_id.lower()
    is_recommended = (
        "claude-sonnet-4" in model_lower or
        "claude-4-sonnet" in model_lower or
        (model_lower.endswith("claude-sonnet-4") or "claude-sonnet-4-" in model_lower)
    )

    # Set display order (lower = shown first)
    # Recommended models get priority
    if is_recommended:
        display_order = 1
    elif "claude" in model_lower and "sonnet" in model_lower:
        display_order = 10
    elif "claude" in model_lower:
        display_order = 50
    elif "gpt-4" in model_lower:
        display_order = 100
    else:
        display_order = 1000

    return LLMModelResponse(
        id=model_id,  # Use model ID as the ID for LiteLLM models
        value=model_id,
        label=label,
        provider=provider,
        model_type=model_type,
        logo=logo,
        description=f"{provider} model: {label}",
        enabled=True,
        recommended=is_recommended,
        compatible_runtimes=compatible_runtimes,
        capabilities={},
        pricing=None,
        display_order=display_order,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )


def check_runtime_compatibility(model: LLMModelDB, runtime_id: Optional[str]) -> bool:
    """Check if a model is compatible with a specific runtime"""
    if not runtime_id:
        return True  # No filter specified
    if not model.compatible_runtimes:
        return True  # Model doesn't specify compatibility, allow all
    return runtime_id in model.compatible_runtimes


def check_runtime_compatibility_dict(compatible_runtimes: List[str], runtime_id: Optional[str]) -> bool:
    """Check if a model is compatible with a specific runtime (dict version)"""
    if not runtime_id:
        return True  # No filter specified
    if not compatible_runtimes:
        return True  # Model doesn't specify compatibility, allow all
    return runtime_id in compatible_runtimes


# ==================== CRUD Endpoints ====================

@router.post("", response_model=LLMModelResponse, status_code=status.HTTP_201_CREATED)
def create_model(
    model_data: LLMModelCreate,
    request: Request,
    db: Session = Depends(get_db),
    organization: dict = Depends(get_current_organization),
):
    """
    Create a new LLM model.

    Only accessible by authenticated users (org admins recommended).
    """
    # Check if model with this value already exists
    existing = db.query(LLMModelDB).filter(LLMModelDB.value == model_data.value).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Model with value '{model_data.value}' already exists"
        )

    # Create new model
    new_model = LLMModelDB(
        value=model_data.value,
        label=model_data.label,
        provider=model_data.provider,
        model_type=model_data.model_type,
        logo=model_data.logo,
        description=model_data.description,
        enabled=model_data.enabled,
        recommended=model_data.recommended,
        compatible_runtimes=model_data.compatible_runtimes,
        capabilities=model_data.capabilities,
        pricing=model_data.pricing,
        display_order=model_data.display_order,
        created_by=organization.get("user_id"),
    )

    db.add(new_model)
    db.commit()
    db.refresh(new_model)

    logger.info(
        "llm_model_created",
        model_id=new_model.id,
        model_value=new_model.value,
        provider=new_model.provider,
        org_id=organization["id"]
    )

    return model_to_response(new_model)


def get_db_optional():
    """Get database session, returns None if database not configured"""
    try:
        db = next(get_db())
        try:
            yield db
        finally:
            db.close()
    except RuntimeError:
        # Database not configured
        yield None


@router.get("", response_model=List[LLMModelResponse])
async def list_models(
    db: Optional[Session] = Depends(get_db_optional),
    provider: Optional[str] = Query(None, description="Filter by provider (e.g., 'xai', 'anthropic')"),
    runtime: Optional[str] = Query(None, description="Filter by compatible runtime (e.g., 'claude_code')"),
    type: Optional[str] = Query(None, description="Filter by model type (e.g., 'embedding', 'text-generation')"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    List all LLM models from LiteLLM server with database fallback.

    Models are fetched dynamically from the configured LiteLLM server with caching for performance.
    Falls back to database models if LiteLLM is unavailable.

    Query Parameters:
    - provider: Filter by provider name (e.g., 'xai', 'anthropic', 'openai')
    - runtime: Filter by compatible runtime (e.g., 'claude_code', 'default')
    - type: Filter by model type (e.g., 'embedding', 'text-generation', 'multimodal')
    - skip/limit: Pagination

    **Example:**
    ```
    GET /api/v1/models
    GET /api/v1/models?provider=xai
    GET /api/v1/models?runtime=claude_code
    GET /api/v1/models?type=embedding
    GET /api/v1/models?type=text-generation&provider=anthropic
    ```
    """
    # Fetch models from LiteLLM (with caching and database fallback)
    litellm_models = await fetch_models_from_litellm_cached(db=db)

    # Convert to response format
    models = [convert_litellm_model_to_response(m) for m in litellm_models]

    # Apply filters
    if provider:
        models = [m for m in models if m.provider.lower() == provider.lower()]

    if runtime:
        models = [m for m in models if check_runtime_compatibility_dict(m.compatible_runtimes, runtime)]

    if type:
        models = [m for m in models if m.model_type.lower() == type.lower()]

    # Apply pagination
    total = len(models)
    models = models[skip : skip + limit]

    logger.info("listed_models", total=total, returned=len(models), provider=provider, runtime=runtime, type=type)

    return models


@router.get("/default", response_model=LLMModelResponse)
async def get_default_model(db: Optional[Session] = Depends(get_db_optional)):
    """
    Get the default recommended LLM model.

    Returns a recommended model from LiteLLM or falls back to database/first available model.
    Uses LITELLM_DEFAULT_MODEL from environment if set.
    """
    # Fetch models from LiteLLM (with database fallback)
    litellm_models = await fetch_models_from_litellm_cached(db=db)

    if not litellm_models:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No models available"
        )

    # Try to find the default model from config
    if settings.litellm_default_model:
        for model in litellm_models:
            if model.get("id") == settings.litellm_default_model:
                return convert_litellm_model_to_response(model)

    # Fallback to first available model
    return convert_litellm_model_to_response(litellm_models[0])


@router.get("/providers", response_model=List[str])
async def list_providers(db: Optional[Session] = Depends(get_db_optional)):
    """
    Get list of unique model providers.

    Returns a list of all unique provider names from available models.
    """
    # Fetch models (with database fallback)
    litellm_models = await fetch_models_from_litellm_cached(db=db)

    # Extract unique providers
    providers = set()
    for model in litellm_models:
        model_id = model.get("id", "")
        if "/" in model_id:
            provider = model_id.split("/")[0]
            providers.add(provider)

    return sorted(list(providers))


@router.get("/{model_id:path}", response_model=LLMModelResponse)
async def get_model(model_id: str, db: Optional[Session] = Depends(get_db_optional)):
    """
    Get a specific LLM model by ID.

    Accepts model ID in the format: provider/model (e.g., 'xai/grok-2-1212')

    **Example:**
    ```
    GET /api/v1/models/xai/grok-2-1212
    GET /api/v1/models/kubiya/claude-sonnet-4
    ```
    """
    # Fetch models (with database fallback)
    litellm_models = await fetch_models_from_litellm_cached(db=db)

    # Find the model
    for model in litellm_models:
        if model.get("id") == model_id:
            return convert_litellm_model_to_response(model)

    # Model not found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Model '{model_id}' not found"
    )


@router.patch("/{model_id}", response_model=LLMModelResponse)
def update_model(
    model_id: str,
    model_data: LLMModelUpdate,
    request: Request,
    db: Session = Depends(get_db),
    organization: dict = Depends(get_current_organization),
):
    """
    Update an existing LLM model.

    Only accessible by authenticated users (org admins recommended).
    """
    # Find model
    model = db.query(LLMModelDB).filter(LLMModelDB.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found"
        )

    # Check if value is being updated and conflicts with existing
    if model_data.value and model_data.value != model.value:
        existing = db.query(LLMModelDB).filter(LLMModelDB.value == model_data.value).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Model with value '{model_data.value}' already exists"
            )

    # Update fields
    update_dict = model_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(model, field, value)

    model.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(model)

    logger.info(
        "llm_model_updated",
        model_id=model.id,
        model_value=model.value,
        updated_fields=list(update_dict.keys()),
        org_id=organization["id"]
    )

    return model_to_response(model)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: str,
    request: Request,
    db: Session = Depends(get_db),
    organization: dict = Depends(get_current_organization),
):
    """
    Delete an LLM model.

    Only accessible by authenticated users (org admins recommended).
    """
    model = db.query(LLMModelDB).filter(LLMModelDB.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found"
        )

    db.delete(model)
    db.commit()

    logger.info(
        "llm_model_deleted",
        model_id=model.id,
        model_value=model.value,
        org_id=organization["id"]
    )

    return None


# ==================== Helper Functions ====================

def model_to_response(model: LLMModelDB) -> LLMModelResponse:
    """Convert database model to response schema"""
    return LLMModelResponse(
        id=model.id,
        value=model.value,
        label=model.label,
        provider=model.provider,
        model_type=model.model_type,
        logo=model.logo,
        description=model.description,
        enabled=model.enabled,
        recommended=model.recommended,
        compatible_runtimes=model.compatible_runtimes or [],
        capabilities=model.capabilities or {},
        pricing=model.pricing,
        display_order=model.display_order,
        created_at=model.created_at.isoformat() if model.created_at else "",
        updated_at=model.updated_at.isoformat() if model.updated_at else "",
    )
