"""
Pydantic schemas for template API endpoints.

Defines request and response models for template compilation and validation.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class TemplateVariableSchema(BaseModel):
    """Schema for a template variable."""
    name: str = Field(..., description="Variable name (e.g., 'api_key' or 'secret.github_token')")
    type: str = Field(..., description="Variable type: 'simple', 'secret', or 'env'")
    raw: str = Field(..., description="Raw template string (e.g., '{{.secret.api_key}}')")
    start: int = Field(..., description="Start position in template")
    end: int = Field(..., description="End position in template")
    display_name: str = Field(..., description="Display name without type prefix")


class ValidationErrorSchema(BaseModel):
    """Schema for a validation error."""
    message: str = Field(..., description="Human-readable error message")
    variable: Optional[TemplateVariableSchema] = Field(None, description="Variable that caused the error")
    position: Optional[int] = Field(None, description="Character position in template")
    code: Optional[str] = Field(None, description="Machine-readable error code")


class TemplateCompileRequest(BaseModel):
    """Request schema for template compilation endpoint."""
    template: str = Field(..., description="Template string with {{variable}} syntax", min_length=1)
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Context for compilation (variables, secrets, env_vars)"
    )
    validate_only: bool = Field(
        False,
        description="Only validate syntax without compiling"
    )
    environment_id: Optional[str] = Field(
        None,
        description="Environment ID for secret validation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "template": "http://api.example.com:{{.env.PORT}}/auth?key={{.secret.api_key}}",
                "context": {
                    "variables": {},
                    "secrets": {"api_key": "secret-value"},
                    "env_vars": {"PORT": "8080"}
                },
                "validate_only": False,
                "environment_id": "env-123"
            }
        }


class TemplateCompileResponse(BaseModel):
    """Response schema for template compilation endpoint."""
    valid: bool = Field(..., description="Whether the template is valid")
    compiled: Optional[str] = Field(None, description="Compiled template (if valid and context provided)")
    variables: List[TemplateVariableSchema] = Field(default_factory=list, description="Variables found in template")
    errors: List[ValidationErrorSchema] = Field(default_factory=list, description="Validation/compilation errors")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "compiled": "http://api.example.com:8080/auth?key=secret-value",
                "variables": [
                    {
                        "name": "env.PORT",
                        "type": "env",
                        "raw": "{{.env.PORT}}",
                        "start": 25,
                        "end": 38,
                        "display_name": "PORT"
                    },
                    {
                        "name": "secret.api_key",
                        "type": "secret",
                        "raw": "{{.secret.api_key}}",
                        "start": 48,
                        "end": 68,
                        "display_name": "api_key"
                    }
                ],
                "errors": [],
                "warnings": []
            }
        }


class TemplateExtractVariablesRequest(BaseModel):
    """Request schema for extracting variables from a template."""
    template: str = Field(..., description="Template string to analyze", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "template": "User {{user}} accessing {{.secret.database}} on {{.env.HOST}}"
            }
        }


class TemplateExtractVariablesResponse(BaseModel):
    """Response schema for variable extraction endpoint."""
    variables: List[TemplateVariableSchema] = Field(..., description="All variables found in template")
    secrets: List[str] = Field(default_factory=list, description="Secret names required")
    env_vars: List[str] = Field(default_factory=list, description="Environment variable names required")
    simple_vars: List[str] = Field(default_factory=list, description="Simple variable names required")

    class Config:
        json_schema_extra = {
            "example": {
                "variables": [
                    {
                        "name": "user",
                        "type": "simple",
                        "raw": "{{user}}",
                        "start": 5,
                        "end": 13,
                        "display_name": "user"
                    }
                ],
                "secrets": ["database"],
                "env_vars": ["HOST"],
                "simple_vars": ["user"]
            }
        }
