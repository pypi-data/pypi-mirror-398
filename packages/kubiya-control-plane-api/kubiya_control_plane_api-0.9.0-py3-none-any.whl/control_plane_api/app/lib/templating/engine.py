"""
Main template engine orchestrator.

Coordinates multiple parsers to extract, validate, and compile templates.
"""

import structlog
from typing import List, Set
from control_plane_api.app.lib.templating.types import (
    TemplateVariable,
    ParseResult,
    ValidationError,
)
from control_plane_api.app.lib.templating.parsers import BaseParser, DEFAULT_PARSERS

logger = structlog.get_logger()


class TemplateEngine:
    """
    Main template engine that coordinates multiple parsers.

    This engine uses a plugin-based architecture where different parsers
    can be registered to handle different template syntaxes.
    """

    def __init__(self, parsers: List[BaseParser] = None):
        """
        Initialize the template engine with a list of parsers.

        Args:
            parsers: List of parsers to use. If None, uses DEFAULT_PARSERS.
        """
        self.parsers = parsers if parsers is not None else DEFAULT_PARSERS.copy()
        logger.debug("template_engine_initialized", parser_count=len(self.parsers))

    def parse(self, template: str) -> ParseResult:
        """
        Parse a template string using all registered parsers.

        Args:
            template: Template string to parse

        Returns:
            ParseResult with all variables found and any syntax errors
        """
        if not template:
            return ParseResult(template="", variables=[], errors=[])

        variables: List[TemplateVariable] = []
        errors: List[ValidationError] = []
        processed_positions: Set[int] = set()

        # Run each parser
        for parser in self.parsers:
            try:
                parser_variables = parser.parse(template)

                # Filter out variables at already-processed positions
                # This prevents conflicts between parsers (e.g., {{var}} matching as both simple and secret)
                for var in parser_variables:
                    if var.start not in processed_positions:
                        variables.append(var)
                        processed_positions.add(var.start)
                        logger.debug(
                            "variable_parsed",
                            variable_name=var.name,
                            variable_type=var.type.value,
                            position=var.start
                        )

            except Exception as e:
                logger.error(
                    "parser_error",
                    parser=parser.__class__.__name__,
                    error=str(e)
                )
                errors.append(ValidationError(
                    message=f"Parser error ({parser.__class__.__name__}): {str(e)}",
                    code="PARSER_ERROR"
                ))

        # Check for unrecognized template patterns
        # Find all {{ }} that weren't matched by any parser
        import re
        all_braces = re.finditer(r"\{\{([^}]+)\}\}", template)
        for match in all_braces:
            start = match.start()
            if start not in processed_positions:
                raw = match.group(0)
                errors.append(ValidationError(
                    message=f"Unrecognized template syntax: '{raw}'. Expected {{{{variable}}}}, {{{{.secret.name}}}}, or {{{{.env.VAR}}}}",
                    position=start,
                    code="INVALID_SYNTAX"
                ))
                logger.warning(
                    "unrecognized_template_syntax",
                    raw=raw,
                    position=start
                )

        # Sort variables by position for consistent ordering
        variables.sort(key=lambda v: v.start)

        return ParseResult(
            template=template,
            variables=variables,
            errors=errors
        )

    def extract_variables(self, template: str) -> List[TemplateVariable]:
        """
        Extract all variables from a template without full parsing.

        Args:
            template: Template string

        Returns:
            List of TemplateVariable objects
        """
        parse_result = self.parse(template)
        return parse_result.variables

    def get_required_secrets(self, template: str) -> List[str]:
        """
        Get list of required secret names from a template.

        Args:
            template: Template string

        Returns:
            List of secret names (without .secret prefix)
        """
        parse_result = self.parse(template)
        return [var.display_name for var in parse_result.secret_variables]

    def get_required_env_vars(self, template: str) -> List[str]:
        """
        Get list of required environment variable names from a template.

        Args:
            template: Template string

        Returns:
            List of environment variable names (without .env prefix)
        """
        parse_result = self.parse(template)
        return [var.display_name for var in parse_result.env_variables]

    def get_required_simple_vars(self, template: str) -> List[str]:
        """
        Get list of required simple variable names from a template.

        Args:
            template: Template string

        Returns:
            List of simple variable names
        """
        parse_result = self.parse(template)
        return [var.name for var in parse_result.simple_variables]


# Global default engine instance
_default_engine = None


def get_default_engine() -> TemplateEngine:
    """
    Get the default global template engine instance.

    Returns:
        TemplateEngine instance
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = TemplateEngine()
    return _default_engine
