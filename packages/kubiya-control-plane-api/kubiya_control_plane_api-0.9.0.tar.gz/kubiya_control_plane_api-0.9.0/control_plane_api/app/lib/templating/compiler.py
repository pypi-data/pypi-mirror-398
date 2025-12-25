"""
Template compilation logic.

Compiles templates by substituting variables with their values from a context.
"""

import json
import os
import structlog
import httpx
from typing import Any, Dict, Optional
from control_plane_api.app.lib.templating.types import (
    TemplateContext,
    TemplateVariableType,
    CompileResult,
)
from control_plane_api.app.lib.templating.engine import TemplateEngine, get_default_engine
from control_plane_api.app.lib.templating.validator import TemplateValidator

logger = structlog.get_logger()


class TemplateCompiler:
    """
    Compiles templates by substituting variables with values from a context.

    The compiler:
    1. Validates the template
    2. Substitutes variables with their values
    3. Returns the compiled string
    """

    def __init__(self, engine: TemplateEngine = None):
        """
        Initialize the compiler with a template engine.

        Args:
            engine: Template engine to use. If None, uses default engine.
        """
        self.engine = engine if engine is not None else get_default_engine()
        self.validator = TemplateValidator(self.engine)

    def compile(self, template: str, context: TemplateContext) -> CompileResult:
        """
        Compile a template by substituting all variables with their values.

        Process:
        1. Parse the template to extract variables
        2. Validate that all variables exist in context
        3. Substitute variables with their values (in reverse order to preserve positions)

        Args:
            template: Template string to compile
            context: Template context with variable values

        Returns:
            CompileResult with compiled string or error
        """
        try:
            # Parse the template
            parse_result = self.engine.parse(template)

            # Check for syntax errors
            if not parse_result.is_valid:
                error_messages = [err.message for err in parse_result.errors]
                error_str = "; ".join(error_messages)
                logger.warning("template_syntax_errors", errors=error_messages)
                return CompileResult(
                    compiled="",
                    success=False,
                    error=f"Template syntax errors: {error_str}"
                )

            # Validate against context
            validation_result = self.validator.validate(template, context)
            if not validation_result.valid:
                error_messages = [err.message for err in validation_result.errors]
                error_str = "; ".join(error_messages)
                logger.warning("template_validation_errors", errors=error_messages)
                return CompileResult(
                    compiled="",
                    success=False,
                    error=f"Template validation errors: {error_str}"
                )

            # Substitute variables (process in reverse order to preserve positions)
            result = template
            for var in sorted(parse_result.variables, key=lambda v: v.start, reverse=True):
                try:
                    # Get the value based on variable type
                    value = self._get_variable_value(var.type, var, context)

                    # Convert to string
                    value_str = str(value) if value is not None else ""

                    # Substitute
                    result = result[:var.start] + value_str + result[var.end:]

                    logger.debug(
                        "variable_substituted",
                        variable_name=var.name,
                        variable_type=var.type.value,
                        has_value=bool(value),
                        value_length=len(value_str)
                    )

                except KeyError as e:
                    # This shouldn't happen if validation passed, but handle it gracefully
                    logger.error(
                        "variable_not_found_during_compilation",
                        variable_name=var.name,
                        error=str(e)
                    )
                    # Preserve the original error message (especially for graph node API errors)
                    error_msg = str(e) if str(e) else f"Variable '{var.name}' not found in context"
                    return CompileResult(
                        compiled="",
                        success=False,
                        error=error_msg
                    )

            logger.info(
                "template_compiled_successfully",
                original_length=len(template),
                compiled_length=len(result),
                variable_count=len(parse_result.variables)
            )

            return CompileResult(
                compiled=result,
                success=True
            )

        except Exception as e:
            logger.error("template_compilation_failed", error=str(e), exc_info=True)
            return CompileResult(
                compiled="",
                success=False,
                error=f"Compilation failed: {str(e)}"
            )

    def _get_variable_value(
        self,
        var_type: TemplateVariableType,
        var,
        context: TemplateContext
    ) -> Any:
        """
        Get the value for a variable from the context.

        Args:
            var_type: Type of variable
            var: TemplateVariable object
            context: Template context

        Returns:
            Variable value

        Raises:
            KeyError: If variable not found in context
        """
        if var_type == TemplateVariableType.SECRET:
            return context.secrets[var.display_name]
        elif var_type == TemplateVariableType.ENV:
            return context.env_vars[var.display_name]
        elif var_type == TemplateVariableType.GRAPH:
            return self._get_graph_node_value(var.display_name, context)
        else:  # SIMPLE
            return context.variables[var.name]

    def _get_graph_node_value(
        self,
        node_id: str,
        context: TemplateContext
    ) -> str:
        """
        Get graph node data from context or fetch from API.

        Args:
            node_id: The node ID to fetch
            context: Template context with graph configuration

        Returns:
            Formatted node data as JSON string

        Raises:
            KeyError: If node not found or API configuration missing
        """
        # Check if node is already in context
        if context.graph_nodes and node_id in context.graph_nodes:
            node_data = context.graph_nodes[node_id]
            return json.dumps(node_data, indent=2)

        # Need to fetch from API - validate configuration
        if not context.graph_api_base:
            raise KeyError(
                f"Context graph API base URL not configured for node '{node_id}'"
            )
        if not context.graph_api_key:
            raise KeyError(
                f"Context graph API key not configured for node '{node_id}'"
            )

        # Fetch node from API
        try:
            node_data = self._fetch_graph_node(
                node_id=node_id,
                api_base=context.graph_api_base,
                api_key=context.graph_api_key,
                org_id=context.graph_org_id
            )

            # Cache in context for subsequent requests
            if context.graph_nodes is None:
                context.graph_nodes = {}
            context.graph_nodes[node_id] = node_data

            return json.dumps(node_data, indent=2)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise KeyError(f"Graph node '{node_id}' not found")
            else:
                raise KeyError(
                    f"Failed to fetch graph node '{node_id}': "
                    f"HTTP {e.response.status_code}"
                )
        except Exception as e:
            raise KeyError(f"Failed to fetch graph node '{node_id}': {str(e)}")

    def _fetch_graph_node(
        self,
        node_id: str,
        api_base: str,
        api_key: str,
        org_id: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch a node from the context graph API.

        Args:
            node_id: The node ID to fetch
            api_base: Context graph API base URL
            api_key: API key for authentication
            org_id: Optional organization ID
            timeout: Request timeout in seconds

        Returns:
            Node data dictionary

        Raises:
            httpx.HTTPStatusError: If request fails (including 404)
            Exception: If request fails for other reasons
        """
        url = f"{api_base.rstrip('/')}/api/v1/graph/nodes/{node_id}"

        headers = {
            "Authorization": f"UserKey {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Kubiya-Client": "agent-runtime-template-compiler",
        }

        if org_id:
            headers["X-Organization-ID"] = org_id

        logger.debug(
            "fetching_graph_node",
            node_id=node_id,
            api_base=api_base,
            has_org_id=bool(org_id)
        )

        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
