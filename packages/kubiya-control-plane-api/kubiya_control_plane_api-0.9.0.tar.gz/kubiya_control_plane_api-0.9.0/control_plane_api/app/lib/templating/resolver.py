"""
Generic template resolution service.

Recursively resolves templates in any data structure (strings, dicts, lists).
This service is used on the worker side to compile templates in runtime configurations,
system prompts, descriptions, and any other text-based fields.
"""

import structlog
from typing import Any, Dict, List, Optional, Union
from control_plane_api.app.lib.templating.types import TemplateContext
from control_plane_api.app.lib.templating.compiler import TemplateCompiler
from control_plane_api.app.lib.templating.engine import TemplateEngine, get_default_engine

logger = structlog.get_logger()


class TemplateResolutionError(Exception):
    """Raised when template resolution fails."""
    pass


class TemplateResolver:
    """
    Generic template resolver that recursively processes data structures.

    This resolver can process:
    - Strings: Compile templates
    - Dicts: Recursively process all values
    - Lists: Recursively process all items
    - Other types: Return as-is

    Usage:
        resolver = TemplateResolver(context)
        resolved_config = resolver.resolve(config)
    """

    def __init__(
        self,
        context: TemplateContext,
        engine: TemplateEngine = None,
        strict: bool = False,
        skip_on_error: bool = False
    ):
        """
        Initialize the template resolver.

        Args:
            context: Template context with available values
            engine: Template engine to use. If None, uses default engine.
            strict: If True, raise error on missing variables. If False, log warning.
            skip_on_error: If True, return original value on error instead of raising.
        """
        self.context = context
        self.engine = engine if engine is not None else get_default_engine()
        self.compiler = TemplateCompiler(self.engine)
        self.strict = strict
        self.skip_on_error = skip_on_error
        self._resolution_count = 0
        self._error_count = 0

    def resolve(self, value: Any) -> Any:
        """
        Recursively resolve templates in any data structure.

        Args:
            value: Value to resolve (string, dict, list, or other)

        Returns:
            Resolved value with all templates compiled

        Raises:
            TemplateResolutionError: If strict=True and resolution fails
        """
        try:
            resolved = self._resolve_recursive(value)
            logger.info(
                "template_resolution_completed",
                resolution_count=self._resolution_count,
                error_count=self._error_count
            )
            return resolved
        except Exception as e:
            if not self.skip_on_error:
                raise TemplateResolutionError(f"Template resolution failed: {str(e)}") from e
            logger.error("template_resolution_failed", error=str(e), exc_info=True)
            return value

    def _resolve_recursive(self, value: Any, path: str = "$") -> Any:
        """
        Recursively resolve templates in a value.

        Args:
            value: Value to resolve
            path: JSON path for logging (e.g., "$.config.system_prompt")

        Returns:
            Resolved value
        """
        # Handle None
        if value is None:
            return None

        # Handle strings (compile templates)
        if isinstance(value, str):
            return self._resolve_string(value, path)

        # Handle dictionaries (recurse into values)
        if isinstance(value, dict):
            return self._resolve_dict(value, path)

        # Handle lists (recurse into items)
        if isinstance(value, list):
            return self._resolve_list(value, path)

        # Handle other types (return as-is)
        return value

    def _resolve_string(self, value: str, path: str) -> str:
        """
        Resolve templates in a string.

        Args:
            value: String value to resolve
            path: JSON path for logging

        Returns:
            Resolved string
        """
        # Check if string contains templates
        parse_result = self.engine.parse(value)

        # If no variables, return as-is (optimization)
        if not parse_result.variables:
            return value

        # Compile the template
        try:
            compile_result = self.compiler.compile(value, self.context)

            if not compile_result.success:
                self._error_count += 1
                error_msg = f"Template compilation failed at {path}: {compile_result.error}"

                if self.strict:
                    raise TemplateResolutionError(error_msg)

                logger.warning(
                    "template_compilation_failed",
                    path=path,
                    error=compile_result.error,
                    original_value=value
                )

                if self.skip_on_error:
                    return value

                raise TemplateResolutionError(error_msg)

            self._resolution_count += 1
            logger.debug(
                "template_resolved",
                path=path,
                variable_count=len(parse_result.variables),
                original_length=len(value),
                resolved_length=len(compile_result.compiled)
            )

            return compile_result.compiled

        except Exception as e:
            self._error_count += 1
            error_msg = f"Template resolution error at {path}: {str(e)}"

            if self.strict:
                raise TemplateResolutionError(error_msg) from e

            logger.warning(
                "template_resolution_error",
                path=path,
                error=str(e),
                original_value=value
            )

            if self.skip_on_error:
                return value

            raise TemplateResolutionError(error_msg) from e

    def _resolve_dict(self, value: Dict[str, Any], path: str) -> Dict[str, Any]:
        """
        Recursively resolve templates in a dictionary.

        Args:
            value: Dictionary to resolve
            path: JSON path for logging

        Returns:
            Resolved dictionary
        """
        resolved = {}
        for key, val in value.items():
            key_path = f"{path}.{key}" if path else key
            resolved[key] = self._resolve_recursive(val, key_path)
        return resolved

    def _resolve_list(self, value: List[Any], path: str) -> List[Any]:
        """
        Recursively resolve templates in a list.

        Args:
            value: List to resolve
            path: JSON path for logging

        Returns:
            Resolved list
        """
        resolved = []
        for idx, item in enumerate(value):
            item_path = f"{path}[{idx}]"
            resolved.append(self._resolve_recursive(item, item_path))
        return resolved

    @property
    def stats(self) -> Dict[str, int]:
        """
        Get resolution statistics.

        Returns:
            Dictionary with resolution_count and error_count
        """
        return {
            "resolution_count": self._resolution_count,
            "error_count": self._error_count
        }


def resolve_templates(
    data: Any,
    context: TemplateContext,
    strict: bool = False,
    skip_on_error: bool = False
) -> Any:
    """
    Convenience function to resolve templates in any data structure.

    Args:
        data: Data to resolve (string, dict, list, or other)
        context: Template context with available values
        strict: If True, raise error on missing variables
        skip_on_error: If True, return original value on error

    Returns:
        Resolved data with all templates compiled

    Example:
        config = {
            "system_prompt": "You are {{agent_name}} running on {{.env.HOST}}",
            "mcp_servers": {
                "github": {
                    "url": "https://{{.env.GITHUB_HOST}}/api",
                    "headers": {
                        "Authorization": "Bearer {{.secret.github_token}}"
                    }
                }
            }
        }

        context = TemplateContext(
            variables={"agent_name": "MyAgent"},
            secrets={"github_token": "ghp_xxx"},
            env_vars={"HOST": "api.example.com", "GITHUB_HOST": "github.com"}
        )

        resolved = resolve_templates(config, context)
        # All templates in the config will be resolved
    """
    resolver = TemplateResolver(context, strict=strict, skip_on_error=skip_on_error)
    return resolver.resolve(data)


def has_templates(value: Any) -> bool:
    """
    Check if a value contains any templates.

    Args:
        value: Value to check (string, dict, list, or other)

    Returns:
        True if value contains templates, False otherwise
    """
    engine = get_default_engine()

    def _check_recursive(val: Any) -> bool:
        if val is None:
            return False

        if isinstance(val, str):
            parse_result = engine.parse(val)
            return len(parse_result.variables) > 0

        if isinstance(val, dict):
            return any(_check_recursive(v) for v in val.values())

        if isinstance(val, list):
            return any(_check_recursive(item) for item in val)

        return False

    return _check_recursive(value)


def extract_all_variables(data: Any) -> Dict[str, List[str]]:
    """
    Extract all template variables from any data structure.

    Args:
        data: Data to analyze (string, dict, list, or other)

    Returns:
        Dictionary with 'secrets', 'env_vars', and 'variables' lists

    Example:
        config = {
            "prompt": "Hello {{user}}",
            "api_key": "{{.secret.github_token}}",
            "host": "{{.env.API_HOST}}"
        }

        variables = extract_all_variables(config)
        # Returns: {
        #     'secrets': ['github_token'],
        #     'env_vars': ['API_HOST'],
        #     'variables': ['user']
        # }
    """
    engine = get_default_engine()
    secrets = set()
    env_vars = set()
    variables = set()

    def _extract_recursive(val: Any):
        if val is None:
            return

        if isinstance(val, str):
            parse_result = engine.parse(val)
            secrets.update(v.display_name for v in parse_result.secret_variables)
            env_vars.update(v.display_name for v in parse_result.env_variables)
            variables.update(v.name for v in parse_result.simple_variables)

        elif isinstance(val, dict):
            for v in val.values():
                _extract_recursive(v)

        elif isinstance(val, list):
            for item in val:
                _extract_recursive(item)

    _extract_recursive(data)

    return {
        "secrets": sorted(list(secrets)),
        "env_vars": sorted(list(env_vars)),
        "variables": sorted(list(variables))
    }
