"""
Template engine package for variable substitution in MCP configurations.

This package provides a flexible, extensible template engine that supports
multiple template syntaxes through a plugin-based parser system.

Supported template syntaxes:
- {{variable}} - Simple variable substitution
- {{.secret.name}} - Secret from vault
- {{.env.VAR}} - Environment variable

Example usage:
    from control_plane_api.app.lib.templating import TemplateEngine, TemplateContext, TemplateCompiler

    # Parse and compile a template
    engine = TemplateEngine()
    context = TemplateContext(
        secrets={"api_key": "secret-value"},
        env_vars={"PORT": "8080"}
    )

    compiler = TemplateCompiler(engine)
    result = compiler.compile("http://api.example.com:{{.env.PORT}}/{{.secret.api_key}}", context)
    print(result.compiled)  # "http://api.example.com:8080/secret-value"
"""

# Core types
from control_plane_api.app.lib.templating.types import (
    TemplateVariableType,
    TemplateVariable,
    ValidationError,
    ParseResult,
    TemplateContext,
    ValidationResult,
    CompileResult,
)

# Main engine components
from control_plane_api.app.lib.templating.engine import TemplateEngine, get_default_engine
from control_plane_api.app.lib.templating.validator import TemplateValidator
from control_plane_api.app.lib.templating.compiler import TemplateCompiler
from control_plane_api.app.lib.templating.resolver import (
    TemplateResolver,
    TemplateResolutionError,
    resolve_templates,
    has_templates,
    extract_all_variables,
)

# Parser infrastructure (for advanced usage)
from control_plane_api.app.lib.templating.parsers import (
    BaseParser,
    SimpleVariableParser,
    SecretVariableParser,
    EnvVariableParser,
    DEFAULT_PARSERS,
)

__all__ = [
    # Types
    "TemplateVariableType",
    "TemplateVariable",
    "ValidationError",
    "ParseResult",
    "TemplateContext",
    "ValidationResult",
    "CompileResult",
    # Main components
    "TemplateEngine",
    "get_default_engine",
    "TemplateValidator",
    "TemplateCompiler",
    "TemplateResolver",
    "TemplateResolutionError",
    # Convenience functions
    "resolve_templates",
    "has_templates",
    "extract_all_variables",
    # Parsers (advanced)
    "BaseParser",
    "SimpleVariableParser",
    "SecretVariableParser",
    "EnvVariableParser",
    "DEFAULT_PARSERS",
]

# Version
__version__ = "1.0.0"
