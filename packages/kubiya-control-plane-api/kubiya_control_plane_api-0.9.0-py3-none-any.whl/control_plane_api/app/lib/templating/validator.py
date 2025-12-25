"""
Template validation logic.

Validates templates against a context to ensure all variables can be resolved.
"""

import structlog
from typing import List
from control_plane_api.app.lib.templating.types import (
    TemplateContext,
    TemplateVariable,
    TemplateVariableType,
    ValidationResult,
    ValidationError,
    ParseResult,
)
from control_plane_api.app.lib.templating.engine import TemplateEngine, get_default_engine

logger = structlog.get_logger()


class TemplateValidator:
    """
    Validates templates against a context.

    Checks that all variables referenced in a template have values available
    in the provided context.
    """

    def __init__(self, engine: TemplateEngine = None):
        """
        Initialize the validator with a template engine.

        Args:
            engine: Template engine to use. If None, uses default engine.
        """
        self.engine = engine if engine is not None else get_default_engine()

    def validate(self, template: str, context: TemplateContext) -> ValidationResult:
        """
        Validate a template against a context.

        Performs the following checks:
        1. Template syntax is valid
        2. All referenced secrets exist in context
        3. All referenced env vars exist in context
        4. All simple variables exist in context

        Args:
            template: Template string to validate
            context: Template context with available values

        Returns:
            ValidationResult with errors and warnings
        """
        # First parse the template
        parse_result: ParseResult = self.engine.parse(template)

        # If parsing failed, return those errors
        if not parse_result.is_valid:
            return ValidationResult(
                valid=False,
                errors=parse_result.errors,
                warnings=[],
                variables=parse_result.variables
            )

        # Now validate each variable against the context
        errors: List[ValidationError] = []
        warnings: List[str] = []

        # Validate secret variables
        for var in parse_result.secret_variables:
            secret_name = var.display_name
            if secret_name not in context.secrets:
                errors.append(ValidationError(
                    message=f"Secret '{secret_name}' not found in context",
                    variable=var,
                    position=var.start,
                    code="MISSING_SECRET"
                ))
                logger.debug(
                    "missing_secret",
                    secret_name=secret_name,
                    position=var.start
                )

        # Validate environment variables
        for var in parse_result.env_variables:
            env_var_name = var.display_name
            if env_var_name not in context.env_vars:
                errors.append(ValidationError(
                    message=f"Environment variable '{env_var_name}' not found in context",
                    variable=var,
                    position=var.start,
                    code="MISSING_ENV_VAR"
                ))
                logger.debug(
                    "missing_env_var",
                    env_var_name=env_var_name,
                    position=var.start
                )

        # Validate simple variables
        for var in parse_result.simple_variables:
            if var.name not in context.variables:
                errors.append(ValidationError(
                    message=f"Variable '{var.name}' not found in context",
                    variable=var,
                    position=var.start,
                    code="MISSING_VARIABLE"
                ))
                logger.debug(
                    "missing_variable",
                    variable_name=var.name,
                    position=var.start
                )

        # Validate graph node variables
        for var in parse_result.graph_variables:
            node_id = var.display_name

            # Check if node is in pre-populated context
            if context.graph_nodes and node_id in context.graph_nodes:
                continue  # Node is available

            # Node not in context - check if we can fetch it
            if not context.graph_api_base or not context.graph_api_key:
                errors.append(ValidationError(
                    message=(
                        f"Graph node '{node_id}' not in context and "
                        f"context graph API not configured"
                    ),
                    variable=var,
                    position=var.start,
                    code="MISSING_GRAPH_NODE"
                ))
                logger.debug(
                    "missing_graph_node_config",
                    node_id=node_id,
                    position=var.start,
                    has_api_base=bool(context.graph_api_base),
                    has_api_key=bool(context.graph_api_key)
                )
            # If API is configured, node will be fetched on-demand during compilation
            # We don't validate existence here to avoid unnecessary API calls

        # Generate warnings for unused context values
        # (This helps catch typos or configuration issues)
        if not errors:  # Only show warnings if validation passed
            # Check for unused secrets
            used_secrets = {v.display_name for v in parse_result.secret_variables}
            unused_secrets = set(context.secrets.keys()) - used_secrets
            if unused_secrets:
                warnings.append(
                    f"Unused secrets in context: {', '.join(sorted(unused_secrets))}"
                )

            # Check for unused env vars
            used_env_vars = {v.display_name for v in parse_result.env_variables}
            unused_env_vars = set(context.env_vars.keys()) - used_env_vars
            if unused_env_vars:
                warnings.append(
                    f"Unused environment variables in context: {', '.join(sorted(unused_env_vars))}"
                )

            # Check for unused simple variables
            used_variables = {v.name for v in parse_result.simple_variables}
            unused_variables = set(context.variables.keys()) - used_variables
            if unused_variables:
                warnings.append(
                    f"Unused variables in context: {', '.join(sorted(unused_variables))}"
                )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            variables=parse_result.variables
        )

    def validate_syntax_only(self, template: str) -> ValidationResult:
        """
        Validate only the syntax of a template without checking context.

        Useful for validating templates before a context is available.

        Args:
            template: Template string to validate

        Returns:
            ValidationResult with syntax errors only
        """
        parse_result: ParseResult = self.engine.parse(template)

        return ValidationResult(
            valid=parse_result.is_valid,
            errors=parse_result.errors,
            warnings=[],
            variables=parse_result.variables
        )
