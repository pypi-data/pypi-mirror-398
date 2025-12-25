"""
Parser for simple template variables: {{variable}}

Supports basic variable substitution with alphanumeric names and underscores.
"""

import re
from typing import Optional
from control_plane_api.app.lib.templating.parsers.base import BaseParser
from control_plane_api.app.lib.templating.types import TemplateVariable, TemplateVariableType


class SimpleVariableParser(BaseParser):
    """
    Parser for simple template variables.

    Syntax: {{variable_name}}
    Valid names: alphanumeric characters and underscores only
    Examples: {{user}}, {{api_key}}, {{database_name}}
    """

    _pattern = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")

    @property
    def pattern(self) -> re.Pattern:
        """Pattern to match simple variables: {{variable}}"""
        return self._pattern

    @property
    def variable_type(self) -> TemplateVariableType:
        """Returns SIMPLE variable type."""
        return TemplateVariableType.SIMPLE

    def parse_match(self, match: re.Match, template: str) -> Optional[TemplateVariable]:
        """
        Parse a regex match into a TemplateVariable.

        Args:
            match: Regex match object for {{variable}}
            template: Full template string

        Returns:
            TemplateVariable with the parsed information
        """
        name = match.group(1)
        raw = match.group(0)
        start = match.start()
        end = match.end()

        # Additional validation
        if not self.validate_name(name):
            return None

        return TemplateVariable(
            name=name,
            type=self.variable_type,
            raw=raw,
            start=start,
            end=end
        )

    def validate_name(self, name: str) -> bool:
        """
        Validate simple variable name.

        Rules:
        - Must contain only alphanumeric characters and underscores
        - Cannot be empty
        - Cannot start with a number (enforced by pattern)

        Args:
            name: Variable name to validate

        Returns:
            True if valid, False otherwise
        """
        if not name:
            return False

        # Check pattern (redundant but explicit)
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))
