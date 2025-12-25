"""
Parser for secret template variables: {{.secret.name}}

Supports referencing secrets from the vault.
"""

import re
from typing import Optional
from control_plane_api.app.lib.templating.parsers.base import BaseParser
from control_plane_api.app.lib.templating.types import TemplateVariable, TemplateVariableType


class SecretVariableParser(BaseParser):
    """
    Parser for secret template variables.

    Syntax: {{.secret.secret_name}}
    Valid names: alphanumeric characters, underscores, and hyphens
    Examples: {{.secret.api_key}}, {{.secret.github-token}}, {{.secret.db_password}}
    """

    _pattern = re.compile(r"\{\{\.secret\.([a-zA-Z0-9_-]+)\}\}")

    @property
    def pattern(self) -> re.Pattern:
        """Pattern to match secret variables: {{.secret.name}}"""
        return self._pattern

    @property
    def variable_type(self) -> TemplateVariableType:
        """Returns SECRET variable type."""
        return TemplateVariableType.SECRET

    def parse_match(self, match: re.Match, template: str) -> Optional[TemplateVariable]:
        """
        Parse a regex match into a TemplateVariable.

        Args:
            match: Regex match object for {{.secret.name}}
            template: Full template string

        Returns:
            TemplateVariable with the parsed information
        """
        secret_name = match.group(1)
        raw = match.group(0)
        start = match.start()
        end = match.end()

        # Additional validation
        if not self.validate_name(secret_name):
            return None

        # Store with "secret." prefix for consistency
        name = f"secret.{secret_name}"

        return TemplateVariable(
            name=name,
            type=self.variable_type,
            raw=raw,
            start=start,
            end=end
        )

    def validate_name(self, name: str) -> bool:
        """
        Validate secret name.

        Rules:
        - Must contain only alphanumeric characters, underscores, and hyphens
        - Cannot be empty
        - Cannot start or end with hyphen or underscore (best practice)

        Args:
            name: Secret name to validate

        Returns:
            True if valid, False otherwise
        """
        if not name:
            return False

        # Basic pattern check
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$", name):
            return False

        return True
