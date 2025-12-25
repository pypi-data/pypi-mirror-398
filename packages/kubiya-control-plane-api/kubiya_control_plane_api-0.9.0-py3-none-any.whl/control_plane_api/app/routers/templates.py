"""
API endpoints for template compilation and validation.

Provides endpoints for:
- Compiling templates with variable substitution
- Validating template syntax
- Extracting variables from templates
"""

import structlog
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from control_plane_api.app.schemas.template_schemas import (
    TemplateCompileRequest,
    TemplateCompileResponse,
    TemplateExtractVariablesRequest,
    TemplateExtractVariablesResponse,
    TemplateVariableSchema,
    ValidationErrorSchema,
)
from control_plane_api.app.lib.templating import (
    TemplateEngine,
    TemplateCompiler,
    TemplateValidator,
    TemplateContext,
    get_default_engine,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/templates", tags=["templates"])


def _template_variable_to_schema(var) -> TemplateVariableSchema:
    """Convert TemplateVariable to schema."""
    return TemplateVariableSchema(
        name=var.name,
        type=var.type.value,
        raw=var.raw,
        start=var.start,
        end=var.end,
        display_name=var.display_name
    )


def _validation_error_to_schema(error) -> ValidationErrorSchema:
    """Convert ValidationError to schema."""
    return ValidationErrorSchema(
        message=error.message,
        variable=_template_variable_to_schema(error.variable) if error.variable else None,
        position=error.position,
        code=error.code
    )


@router.post("/compile", response_model=TemplateCompileResponse)
async def compile_template(request: TemplateCompileRequest) -> TemplateCompileResponse:
    """
    Compile a template by substituting variables with values from context.

    This endpoint:
    1. Parses the template to extract variables
    2. Validates syntax
    3. If context provided: validates against context and compiles
    4. If validate_only=True: only validates without compiling

    Returns detailed information about variables, errors, and warnings.
    """
    try:
        logger.info(
            "template_compile_request",
            template_length=len(request.template),
            has_context=bool(request.context),
            validate_only=request.validate_only,
            environment_id=request.environment_id
        )

        engine = get_default_engine()
        validator = TemplateValidator(engine)

        # Parse the template
        parse_result = engine.parse(request.template)

        # Convert variables to schema
        variables = [_template_variable_to_schema(var) for var in parse_result.variables]

        # Check for syntax errors
        if not parse_result.is_valid:
            errors = [_validation_error_to_schema(err) for err in parse_result.errors]
            logger.warning(
                "template_syntax_errors",
                error_count=len(errors)
            )
            return TemplateCompileResponse(
                valid=False,
                compiled=None,
                variables=variables,
                errors=errors,
                warnings=[]
            )

        # If validate_only, just return syntax validation
        if request.validate_only and not request.context:
            logger.info("template_syntax_validated")
            return TemplateCompileResponse(
                valid=True,
                compiled=None,
                variables=variables,
                errors=[],
                warnings=[]
            )

        # If context provided, validate and/or compile
        if request.context:
            # Build context from request
            context = TemplateContext(
                variables=request.context.get("variables", {}),
                secrets=request.context.get("secrets", {}),
                env_vars=request.context.get("env_vars", {})
            )

            # Validate against context
            validation_result = validator.validate(request.template, context)

            # Convert errors and warnings to schema
            errors = [_validation_error_to_schema(err) for err in validation_result.errors]
            warnings = validation_result.warnings

            if not validation_result.valid:
                logger.warning(
                    "template_validation_errors",
                    error_count=len(errors),
                    missing_secrets=validation_result.missing_secrets,
                    missing_env_vars=validation_result.missing_env_vars
                )
                return TemplateCompileResponse(
                    valid=False,
                    compiled=None,
                    variables=variables,
                    errors=errors,
                    warnings=warnings
                )

            # If not validate_only, compile the template
            compiled = None
            if not request.validate_only:
                compiler = TemplateCompiler(engine)
                compile_result = compiler.compile(request.template, context)

                if not compile_result.success:
                    logger.error(
                        "template_compilation_failed",
                        error=compile_result.error
                    )
                    return TemplateCompileResponse(
                        valid=False,
                        compiled=None,
                        variables=variables,
                        errors=[ValidationErrorSchema(
                            message=compile_result.error,
                            code="COMPILATION_ERROR"
                        )],
                        warnings=warnings
                    )

                compiled = compile_result.compiled
                logger.info(
                    "template_compiled_successfully",
                    original_length=len(request.template),
                    compiled_length=len(compiled)
                )

            return TemplateCompileResponse(
                valid=True,
                compiled=compiled,
                variables=variables,
                errors=[],
                warnings=warnings
            )

        # No context and not validate_only - just return parsed variables
        logger.info("template_parsed_successfully", variable_count=len(variables))
        return TemplateCompileResponse(
            valid=True,
            compiled=None,
            variables=variables,
            errors=[],
            warnings=[]
        )

    except Exception as e:
        logger.error("template_compile_endpoint_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template compilation failed: {str(e)}"
        )


@router.post("/extract-variables", response_model=TemplateExtractVariablesResponse)
async def extract_variables(request: TemplateExtractVariablesRequest) -> TemplateExtractVariablesResponse:
    """
    Extract all variables from a template without validation or compilation.

    Useful for:
    - Analyzing templates before providing context
    - Building UI autocomplete suggestions
    - Determining required secrets/env vars
    """
    try:
        logger.info(
            "extract_variables_request",
            template_length=len(request.template)
        )

        engine = get_default_engine()

        # Parse the template
        parse_result = engine.parse(request.template)

        # Convert variables to schema
        variables = [_template_variable_to_schema(var) for var in parse_result.variables]

        # Extract categorized variable names
        secrets = [var.display_name for var in parse_result.secret_variables]
        env_vars = [var.display_name for var in parse_result.env_variables]
        simple_vars = [var.name for var in parse_result.simple_variables]

        logger.info(
            "variables_extracted",
            total_count=len(variables),
            secrets_count=len(secrets),
            env_vars_count=len(env_vars),
            simple_vars_count=len(simple_vars)
        )

        return TemplateExtractVariablesResponse(
            variables=variables,
            secrets=secrets,
            env_vars=env_vars,
            simple_vars=simple_vars
        )

    except Exception as e:
        logger.error("extract_variables_endpoint_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Variable extraction failed: {str(e)}"
        )
