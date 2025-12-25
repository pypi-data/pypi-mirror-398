"""
Core type definitions for the template engine.

This module defines all data classes, enums, and type definitions used
throughout the templating system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional


class TemplateVariableType(str, Enum):
    """Types of template variables supported by the engine."""
    SIMPLE = "simple"  # {{variable}}
    SECRET = "secret"  # {{.secret.name}}
    ENV = "env"        # {{.env.VAR}}
    GRAPH = "graph"    # {{.graph.node-id}}


@dataclass
class TemplateVariable:
    """
    Represents a template variable found in a template string.

    Attributes:
        name: Full variable name (e.g., "api_key" or "secret.github_token")
        type: Type of template variable
        raw: Raw template string as it appears in the template
        start: Start position in the template string
        end: End position in the template string
    """
    name: str
    type: TemplateVariableType
    raw: str
    start: int
    end: int

    @property
    def display_name(self) -> str:
        """
        Get display name for UI/error messages.

        Removes type prefixes to show just the variable name:
        - "secret.api_key" -> "api_key"
        - "env.API_KEY" -> "API_KEY"
        - "graph.node-123" -> "node-123"
        - "variable" -> "variable"
        """
        if self.type == TemplateVariableType.SECRET:
            return self.name.replace("secret.", "", 1)
        elif self.type == TemplateVariableType.ENV:
            return self.name.replace("env.", "", 1)
        elif self.type == TemplateVariableType.GRAPH:
            return self.name.replace("graph.", "", 1)
        return self.name


@dataclass
class ValidationError:
    """
    Represents a validation error in a template.

    Attributes:
        message: Human-readable error message
        variable: Variable that caused the error (if applicable)
        position: Character position in template where error occurred
        code: Machine-readable error code for programmatic handling
    """
    message: str
    variable: Optional[TemplateVariable] = None
    position: Optional[int] = None
    code: Optional[str] = None


@dataclass
class ParseResult:
    """
    Result of parsing a template string.

    Attributes:
        template: Original template string
        variables: List of variables found in the template
        errors: List of parsing/syntax errors
    """
    template: str
    variables: List[TemplateVariable] = field(default_factory=list)
    errors: List[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if template is syntactically valid."""
        return len(self.errors) == 0

    @property
    def simple_variables(self) -> List[TemplateVariable]:
        """Get all simple variables ({{variable}})."""
        return [v for v in self.variables if v.type == TemplateVariableType.SIMPLE]

    @property
    def secret_variables(self) -> List[TemplateVariable]:
        """Get all secret variables ({{.secret.name}})."""
        return [v for v in self.variables if v.type == TemplateVariableType.SECRET]

    @property
    def env_variables(self) -> List[TemplateVariable]:
        """Get all environment variables ({{.env.VAR}})."""
        return [v for v in self.variables if v.type == TemplateVariableType.ENV]

    @property
    def graph_variables(self) -> List[TemplateVariable]:
        """Get all graph node variables ({{.graph.node-id}})."""
        return [v for v in self.variables if v.type == TemplateVariableType.GRAPH]


@dataclass
class TemplateContext:
    """
    Context for template resolution.

    Provides all available values for template variable substitution.

    Attributes:
        variables: Simple variable name -> value mapping
        secrets: Secret name -> secret value mapping
        env_vars: Environment variable name -> value mapping
        graph_nodes: Context graph node ID -> node data mapping (optional, fetched on demand)
        graph_api_base: Base URL for context graph API
        graph_api_key: API key for context graph API
        graph_org_id: Organization ID for context graph queries
    """
    variables: Dict[str, Any] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    env_vars: Dict[str, str] = field(default_factory=dict)
    graph_nodes: Optional[Dict[str, Dict[str, Any]]] = None
    graph_api_base: Optional[str] = None
    graph_api_key: Optional[str] = None
    graph_org_id: Optional[str] = None


@dataclass
class ValidationResult:
    """
    Result of template validation.

    Attributes:
        valid: Whether the template is valid
        errors: List of validation errors
        warnings: List of non-fatal warnings
        variables: List of variables found in the template
    """
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    variables: List[TemplateVariable] = field(default_factory=list)

    @property
    def missing_secrets(self) -> List[str]:
        """Get list of missing secret names."""
        return [
            err.variable.display_name
            for err in self.errors
            if err.variable
            and err.variable.type == TemplateVariableType.SECRET
            and err.code == "MISSING_SECRET"
        ]

    @property
    def missing_env_vars(self) -> List[str]:
        """Get list of missing environment variable names."""
        return [
            err.variable.display_name
            for err in self.errors
            if err.variable
            and err.variable.type == TemplateVariableType.ENV
            and err.code == "MISSING_ENV_VAR"
        ]

    @property
    def missing_variables(self) -> List[str]:
        """Get list of missing simple variable names."""
        return [
            err.variable.name
            for err in self.errors
            if err.variable
            and err.variable.type == TemplateVariableType.SIMPLE
            and err.code == "MISSING_VARIABLE"
        ]

    @property
    def missing_graph_nodes(self) -> List[str]:
        """Get list of missing graph node IDs."""
        return [
            err.variable.display_name
            for err in self.errors
            if err.variable
            and err.variable.type == TemplateVariableType.GRAPH
            and err.code == "MISSING_GRAPH_NODE"
        ]


@dataclass
class CompileResult:
    """
    Result of template compilation.

    Attributes:
        compiled: Compiled template string with variables substituted
        success: Whether compilation succeeded
        error: Error message if compilation failed
    """
    compiled: str
    success: bool = True
    error: Optional[str] = None
