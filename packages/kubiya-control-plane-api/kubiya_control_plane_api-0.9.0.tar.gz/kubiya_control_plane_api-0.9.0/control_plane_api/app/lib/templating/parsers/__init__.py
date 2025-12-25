"""
Template parsers package.

Exports all available template variable parsers.
"""

from control_plane_api.app.lib.templating.parsers.base import BaseParser
from control_plane_api.app.lib.templating.parsers.simple import SimpleVariableParser
from control_plane_api.app.lib.templating.parsers.secret import SecretVariableParser
from control_plane_api.app.lib.templating.parsers.env import EnvVariableParser
from control_plane_api.app.lib.templating.parsers.graph import GraphNodeParser

# Default list of parsers to use in the template engine
# Order matters: more specific patterns should come first to avoid conflicts
DEFAULT_PARSERS = [
    SecretVariableParser(),    # {{.secret.name}} - most specific
    EnvVariableParser(),       # {{.env.VAR}} - specific
    GraphNodeParser(),         # {{.graph.node-id}} - specific
    SimpleVariableParser(),    # {{variable}} - most general (must be last)
]

__all__ = [
    "BaseParser",
    "SimpleVariableParser",
    "SecretVariableParser",
    "EnvVariableParser",
    "GraphNodeParser",
    "DEFAULT_PARSERS",
]
