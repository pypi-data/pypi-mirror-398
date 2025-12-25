"""
Base parser interface for template variable parsers.

This module defines the abstract base class that all template parsers must implement.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Optional
from control_plane_api.app.lib.templating.types import TemplateVariable, TemplateVariableType


class BaseParser(ABC):
    """
    Abstract base class for template variable parsers.

    Each parser is responsible for:
    - Defining a regex pattern to match its template syntax
    - Parsing matches into TemplateVariable objects
    - Validating variable names according to its rules
    """

    @property
    @abstractmethod
    def pattern(self) -> re.Pattern:
        """
        Regular expression pattern to match this parser's template syntax.

        Returns:
            Compiled regex pattern
        """
        pass

    @property
    @abstractmethod
    def variable_type(self) -> TemplateVariableType:
        """
        Type of variables this parser handles.

        Returns:
            TemplateVariableType enum value
        """
        pass

    @abstractmethod
    def parse_match(self, match: re.Match, template: str) -> Optional[TemplateVariable]:
        """
        Parse a regex match into a TemplateVariable.

        Args:
            match: Regex match object
            template: Full template string (for context)

        Returns:
            TemplateVariable if valid, None if invalid
        """
        pass

    @abstractmethod
    def validate_name(self, name: str) -> bool:
        """
        Validate that a variable name follows this parser's rules.

        Args:
            name: Variable name to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def parse(self, template: str) -> List[TemplateVariable]:
        """
        Parse a template string and extract all variables of this parser's type.

        Args:
            template: Template string to parse

        Returns:
            List of TemplateVariable objects found
        """
        if not template:
            return []

        variables: List[TemplateVariable] = []

        for match in self.pattern.finditer(template):
            variable = self.parse_match(match, template)
            if variable:
                variables.append(variable)

        return variables

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(type={self.variable_type.value})"
