"""Runtime types endpoint for agent execution frameworks"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from control_plane_api.app.lib.validation import (
    validate_agent_for_runtime,
    get_runtime_requirements_info,
)

router = APIRouter()


class ModelRequirementInfo(BaseModel):
    """Model requirements for a runtime"""
    description: str = Field(..., description="Human-readable description")
    supported_providers: List[str] = Field(..., description="Supported model providers")
    supported_families: List[str] = Field(..., description="Supported model families")
    examples: List[str] = Field(..., description="Example valid model IDs")


class RuntimeRequirementsInfo(BaseModel):
    """Requirements specification for a runtime"""
    model_requirement: ModelRequirementInfo
    required_config_fields: List[str] = Field(default_factory=list)
    recommended_config_fields: List[str] = Field(default_factory=list)
    max_history_length: Optional[int] = None
    requires_system_prompt: bool = False
    requires_tools: bool = False


class RuntimeInfo(BaseModel):
    """Information about an agent runtime"""
    id: str = Field(..., description="Runtime identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Description of the runtime")
    icon: str = Field(..., description="Icon identifier for UI")
    features: List[str] = Field(..., description="Key features of this runtime")
    status: str = Field(..., description="Status: available, beta, coming_soon")
    requirements: Optional[RuntimeRequirementsInfo] = Field(None, description="Runtime requirements and validation rules")


class ValidationRequest(BaseModel):
    """Request to validate agent configuration for a runtime"""
    runtime_type: str = Field(..., description="Runtime type to validate for")
    model_id: Optional[str] = Field(None, description="Model ID to validate")
    agent_config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")
    system_prompt: Optional[str] = Field(None, description="System prompt")


class ValidationResponse(BaseModel):
    """Response from validation"""
    valid: bool = Field(..., description="Whether configuration is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors if any")


def _get_runtime_requirements(runtime_id: str) -> Optional[RuntimeRequirementsInfo]:
    """Helper to get requirements for a runtime from shared validation module."""
    try:
        req_info = get_runtime_requirements_info(runtime_id)
        if "error" in req_info:
            return None

        model_req = req_info.get("model_requirement", {})
        return RuntimeRequirementsInfo(
            model_requirement=ModelRequirementInfo(
                description=model_req.get("description", ""),
                supported_providers=model_req.get("supported_providers", []),
                supported_families=model_req.get("supported_families", []),
                examples=model_req.get("examples", []),
            ),
            required_config_fields=req_info.get("required_config_fields", []),
            recommended_config_fields=req_info.get("recommended_config_fields", []),
            max_history_length=req_info.get("max_history_length"),
            requires_system_prompt=req_info.get("requires_system_prompt", False),
            requires_tools=req_info.get("requires_tools", False),
        )
    except Exception as e:
        print(f"Error loading requirements for {runtime_id}: {e}")
        return None


@router.get("/runtimes", response_model=List[RuntimeInfo], tags=["Runtimes"])
def list_runtimes():
    """
    List available agent runtime types with requirements.

    Returns information about different agent execution frameworks
    that can be used when creating or configuring agents, including
    model compatibility requirements and validation rules.
    """
    return [
        RuntimeInfo(
            id="default",
            name="Agno Runtime",
            description="Production-ready agent framework with advanced reasoning and tool execution capabilities. Best for complex workflows and multi-step tasks. Supports most LiteLLM-compatible models.",
            icon="agno",
            features=[
                "Advanced reasoning capabilities",
                "Multi-step task execution",
                "Built-in tool integration",
                "Session management",
                "Production-tested reliability",
                "Supports GPT, Claude, Gemini, Mistral, and more"
            ],
            status="available",
            requirements=_get_runtime_requirements("default")
        ),
        RuntimeInfo(
            id="claude_code",
            name="Claude Code SDK",
            description="Specialized runtime for code generation and software development tasks. Requires Anthropic Claude models for optimal performance with extended context and advanced code understanding.",
            icon="code",
            features=[
                "Code-first design",
                "Advanced code generation",
                "Built-in code review",
                "Repository awareness",
                "Development workflow optimization",
                "Requires Claude models (claude-3-opus, claude-3-sonnet, etc.)"
            ],
            status="beta",
            requirements=_get_runtime_requirements("claude_code")
        )
    ]


@router.post("/runtimes/validate", response_model=ValidationResponse, tags=["Runtimes"])
def validate_runtime_config(request: ValidationRequest):
    """
    Validate agent/team configuration for a specific runtime.

    This endpoint checks if the provided configuration is compatible with
    the selected runtime, including model validation and required fields.

    Use this before creating or updating agents to ensure compatibility.
    """
    try:
        is_valid, errors = validate_agent_for_runtime(
            runtime_type=request.runtime_type,
            model_id=request.model_id,
            agent_config=request.agent_config,
            system_prompt=request.system_prompt,
        )

        return ValidationResponse(
            valid=is_valid,
            errors=errors
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        )


@router.get("/runtimes/{runtime_id}/requirements", response_model=RuntimeRequirementsInfo, tags=["Runtimes"])
def get_runtime_requirements(runtime_id: str):
    """
    Get detailed requirements for a specific runtime.

    Returns model compatibility requirements, required configuration fields,
    and other validation rules for the specified runtime.
    """
    requirements = _get_runtime_requirements(runtime_id)
    if not requirements:
        raise HTTPException(
            status_code=404,
            detail=f"Runtime '{runtime_id}' not found or has no requirements"
        )
    return requirements
