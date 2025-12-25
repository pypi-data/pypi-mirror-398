"""
Parser for environment variable template variables: {{.env.VAR}}

Supports referencing environment variables.
"""

import re
from typing import Optional
from control_plane_api.app.lib.templating.parsers.base import BaseParser
from control_plane_api.app.lib.templating.types import TemplateVariable, TemplateVariableType


class EnvVariableParser(BaseParser):
    """
    Parser for environment variable template variables.

    Syntax: {{.env.VARIABLE_NAME}}
    Valid names: alphanumeric characters and underscores (following Unix conventions)
    Examples: {{.env.API_KEY}}, {{.env.DATABASE_URL}}, {{.env.PORT}}
    """

    _pattern = re.compile(r"\{\{\.env\.([a-zA-Z_][a-zA-Z0-9_]*)\}\}")

    @property
    def pattern(self) -> re.Pattern:
        """Pattern to match environment variables: {{.env.VAR}}"""
        return self._pattern

    @property
    def variable_type(self) -> TemplateVariableType:
        """Returns ENV variable type."""
        return TemplateVariableType.ENV

    def parse_match(self, match: re.Match, template: str) -> Optional[TemplateVariable]:
        """
        Parse a regex match into a TemplateVariable.

        Args:
            match: Regex match object for {{.env.VAR}}
            template: Full template string

        Returns:
            TemplateVariable with the parsed information
        """
        env_var_name = match.group(1)
        raw = match.group(0)
        start = match.start()
        end = match.end()

        # Additional validation
        if not self.validate_name(env_var_name):
            return None

        # Store with "env." prefix for consistency
        name = f"env.{env_var_name}"

        return TemplateVariable(
            name=name,
            type=self.variable_type,
            raw=raw,
            start=start,
            end=end
        )

    def validate_name(self, name: str) -> bool:
        """
        Validate environment variable name.

        Rules (following Unix conventions):
        - Must start with a letter or underscore
        - Can contain letters, digits, and underscores
        - Cannot be empty
        - By convention, usually uppercase but not required

        Args:
            name: Environment variable name to validate

        Returns:
            True if valid, False otherwise
        """
        if not name:
            return False

        # Must start with letter or underscore, contain only alphanumeric and underscores
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))
