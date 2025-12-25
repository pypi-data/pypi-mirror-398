"""
Parser for context graph node template variables: {{.graph.node-id}}

Supports referencing nodes from the context graph by their ID.
"""

import re
from typing import Optional
from control_plane_api.app.lib.templating.parsers.base import BaseParser
from control_plane_api.app.lib.templating.types import TemplateVariable, TemplateVariableType


class GraphNodeParser(BaseParser):
    """
    Parser for context graph node template variables.

    Syntax: {{.graph.node-id}}
    Valid node IDs: alphanumeric characters, underscores, hyphens, and dots
    Examples: {{.graph.user-123}}, {{.graph.repo_456}}, {{.graph.service.prod}}

    When compiled, these variables will be replaced with formatted node data including:
    - Node properties (metadata)
    - Relationships (incoming/outgoing)
    - Labels and types
    """

    _pattern = re.compile(r"\{\{\.graph\.([a-zA-Z0-9._-]+)\}\}")

    @property
    def pattern(self) -> re.Pattern:
        """Pattern to match graph node variables: {{.graph.node-id}}"""
        return self._pattern

    @property
    def variable_type(self) -> TemplateVariableType:
        """Returns GRAPH variable type."""
        return TemplateVariableType.GRAPH

    def parse_match(self, match: re.Match, template: str) -> Optional[TemplateVariable]:
        """
        Parse a regex match into a TemplateVariable.

        Args:
            match: Regex match object for {{.graph.node-id}}
            template: Full template string

        Returns:
            TemplateVariable with the parsed information
        """
        node_id = match.group(1)
        raw = match.group(0)
        start = match.start()
        end = match.end()

        # Additional validation
        if not self.validate_node_id(node_id):
            return None

        # Store with "graph." prefix for consistency
        name = f"graph.{node_id}"

        return TemplateVariable(
            name=name,
            type=self.variable_type,
            raw=raw,
            start=start,
            end=end
        )

    def validate_name(self, name: str) -> bool:
        """
        Validate variable name (implements BaseParser abstract method).

        For graph variables, the name format is "graph.node-id".

        Args:
            name: Variable name to validate

        Returns:
            True if valid, False otherwise
        """
        if not name or not name.startswith("graph."):
            return False

        # Extract node ID after "graph." prefix
        node_id = name[6:]  # len("graph.") == 6
        return self.validate_node_id(node_id)

    def validate_node_id(self, node_id: str) -> bool:
        """
        Validate node ID.

        Rules:
        - Must contain only alphanumeric characters, underscores, hyphens, and dots
        - Cannot be empty
        - Cannot start or end with special characters (best practice)

        Args:
            node_id: Node ID to validate

        Returns:
            True if valid, False otherwise
        """
        if not node_id:
            return False

        # Basic pattern check - allow alphanumeric, underscore, hyphen, and dot
        # Allow single character IDs or multi-character with proper start/end
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$", node_id):
            return False

        return True
