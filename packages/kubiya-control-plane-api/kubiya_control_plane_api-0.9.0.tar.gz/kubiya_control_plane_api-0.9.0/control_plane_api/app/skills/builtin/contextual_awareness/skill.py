"""Contextual Awareness Skill - Access Context Graph API for real-time organizational context."""
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from control_plane_api.app.skills.base import SkillDefinition, SkillType, SkillCategory, SkillVariant, SkillRequirements


class NodeFilter(BaseModel):
    """Configuration for filtering specific nodes in the context graph."""
    label: Optional[str] = Field(None, description="Node label to filter by (e.g., 'User', 'Team', 'Project')")
    property_name: Optional[str] = Field(None, description="Property name to filter by")
    property_value: Optional[Any] = Field(None, description="Property value to match")
    integration: Optional[str] = Field(None, description="Filter by integration name (e.g., 'Azure', 'Slack')")


class RelationshipFilter(BaseModel):
    """Configuration for filtering specific relationships in the context graph."""
    relationship_type: str = Field(..., description="Relationship type to filter (e.g., 'BELONGS_TO', 'OWNS')")
    direction: str = Field("both", description="Relationship direction: 'incoming', 'outgoing', or 'both'")
    integration: Optional[str] = Field(None, description="Filter by integration name")


class ContextualAwarenessConfiguration(BaseModel):
    """Configuration for the Contextual Awareness skill."""

    # Specific node/relationship configuration
    predefined_nodes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of predefined node filters that the agent can query"
    )

    predefined_relationships: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of predefined relationship filters that the agent can query"
    )

    # Dynamic search configuration
    allow_dynamic_search: bool = Field(
        False,
        description="Allow agent to perform dynamic searches and custom Cypher queries on the graph"
    )

    allow_text_search: bool = Field(
        True,
        description="Allow agent to search nodes by text patterns"
    )

    allow_subgraph_queries: bool = Field(
        True,
        description="Allow agent to retrieve subgraphs (nodes and their relationships)"
    )

    # Integration filters
    allowed_integrations: Optional[List[str]] = Field(
        None,
        description="List of integrations the agent can query. If None, all integrations are allowed."
    )

    # Query limits
    max_results: int = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum number of results to return per query"
    )

    default_subgraph_depth: int = Field(
        1,
        ge=1,
        le=5,
        description="Default depth for subgraph traversal (1-5)"
    )

    # Cache configuration
    enable_caching: bool = Field(
        True,
        description="Enable caching of graph query results for performance"
    )

    cache_ttl: int = Field(
        300,
        ge=0,
        le=3600,
        description="Cache time-to-live in seconds (0 to disable, max 1 hour)"
    )

    @validator('predefined_nodes')
    def validate_nodes(cls, nodes):
        """Validate that predefined nodes have proper structure."""
        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError("Each predefined node must be a dictionary")
            # Optional validation of fields
            valid_keys = {'label', 'property_name', 'property_value', 'integration', 'description'}
            invalid_keys = set(node.keys()) - valid_keys
            if invalid_keys:
                raise ValueError(f"Invalid keys in node filter: {invalid_keys}")
        return nodes

    @validator('predefined_relationships')
    def validate_relationships(cls, relationships):
        """Validate that predefined relationships have proper structure."""
        for rel in relationships:
            if not isinstance(rel, dict):
                raise ValueError("Each predefined relationship must be a dictionary")
            if 'relationship_type' not in rel:
                raise ValueError("Each predefined relationship must have a 'relationship_type' field")
            # Validate direction if present
            if 'direction' in rel and rel['direction'] not in ['incoming', 'outgoing', 'both']:
                raise ValueError(f"Invalid direction: {rel['direction']}")
        return relationships


class ContextualAwarenessSkill(SkillDefinition):
    """
    Contextual Awareness Skill Definition.

    Provides agents with access to organizational context through the Context Graph API.
    Agents can query nodes, relationships, and perform graph traversals to understand
    the organizational context in real-time.
    """

    @property
    def type(self) -> SkillType:
        return SkillType.CONTEXTUAL_AWARENESS

    @property
    def name(self) -> str:
        return "Contextual Awareness"

    @property
    def description(self) -> str:
        return "Access organizational context from the Context Graph (Neo4j) including nodes, relationships, and graph traversals"

    @property
    def icon(self) -> str:
        return "Network"

    @property
    def icon_type(self) -> str:
        return "lucide"

    def get_requirements(self) -> SkillRequirements:
        """Get runtime requirements."""
        return SkillRequirements(
            python_packages=["httpx>=0.27.0", "pydantic>=2.0.0"],
            external_dependencies=["Context Graph API"],
            required_env_vars=[],
            notes="Requires access to Context Graph API endpoint (default: https://graph.kubiya.ai)",
        )

    def get_variants(self) -> List[SkillVariant]:
        """Get predefined variants for this skill."""
        return [
            SkillVariant(
                id="read_only_basic",
                name="Basic Context Access",
                description="Read-only access to predefined nodes and relationships",
                category=SkillCategory.COMMON,
                configuration={
                    "predefined_nodes": [],
                    "predefined_relationships": [],
                    "allow_dynamic_search": False,
                    "allow_text_search": True,
                    "allow_subgraph_queries": False,
                    "max_results": 50,
                    "default_subgraph_depth": 1,
                    "enable_caching": True,
                    "cache_ttl": 300,
                },
                badge="Safe",
                is_default=True,
            ),
            SkillVariant(
                id="dynamic_search",
                name="Dynamic Context Search",
                description="Full search capabilities including dynamic queries and graph traversals",
                category=SkillCategory.ADVANCED,
                configuration={
                    "predefined_nodes": [],
                    "predefined_relationships": [],
                    "allow_dynamic_search": True,
                    "allow_text_search": True,
                    "allow_subgraph_queries": True,
                    "max_results": 100,
                    "default_subgraph_depth": 2,
                    "enable_caching": True,
                    "cache_ttl": 300,
                },
                badge="Advanced",
            ),
            SkillVariant(
                id="integration_specific",
                name="Integration-Specific Context",
                description="Access context from specific integrations only",
                category=SkillCategory.COMMON,
                configuration={
                    "predefined_nodes": [],
                    "predefined_relationships": [],
                    "allow_dynamic_search": False,
                    "allow_text_search": True,
                    "allow_subgraph_queries": True,
                    "allowed_integrations": [],  # To be filled by user
                    "max_results": 100,
                    "default_subgraph_depth": 2,
                    "enable_caching": True,
                    "cache_ttl": 300,
                },
                badge="Filtered",
            ),
        ]

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize configuration.

        Args:
            config: Raw configuration dict

        Returns:
            Validated and normalized configuration

        Raises:
            ValueError: If configuration is invalid
        """
        try:
            # Parse and validate using Pydantic model
            validated = ContextualAwarenessConfiguration(**config)
            return validated.model_dump()
        except Exception as e:
            raise ValueError(f"Invalid Contextual Awareness configuration: {str(e)}")

    def get_default_configuration(self) -> Dict[str, Any]:
        """Get the default configuration for this skill."""
        return {
            "predefined_nodes": [],
            "predefined_relationships": [],
            "allow_dynamic_search": False,
            "allow_text_search": True,
            "allow_subgraph_queries": False,
            "max_results": 50,
            "default_subgraph_depth": 1,
            "enable_caching": True,
            "cache_ttl": 300,
        }

    def get_framework_class_name(self) -> str:
        """
        Get the underlying framework tool class name.

        Returns:
            Class name for the runtime tools implementation
        """
        return "ContextualAwarenessTools"

    def get_configuration_schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema for configuration validation.

        Returns:
            JSON schema for the configuration
        """
        return {
            "type": "object",
            "properties": {
                "predefined_nodes": {
                    "type": "array",
                    "title": "Predefined Nodes",
                    "description": "List of predefined node filters that the agent can query",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {
                                "type": "string",
                                "description": "Node label to filter by (e.g., 'User', 'Team', 'Project')"
                            },
                            "property_name": {
                                "type": "string",
                                "description": "Property name to filter by"
                            },
                            "property_value": {
                                "description": "Property value to match"
                            },
                            "integration": {
                                "type": "string",
                                "description": "Filter by integration name (e.g., 'Azure', 'Slack')"
                            },
                            "description": {
                                "type": "string",
                                "description": "Human-readable description of this node filter"
                            }
                        }
                    },
                    "default": []
                },
                "predefined_relationships": {
                    "type": "array",
                    "title": "Predefined Relationships",
                    "description": "List of predefined relationship filters that the agent can query",
                    "items": {
                        "type": "object",
                        "properties": {
                            "relationship_type": {
                                "type": "string",
                                "description": "Relationship type to filter (e.g., 'BELONGS_TO', 'OWNS')",
                                "required": True
                            },
                            "direction": {
                                "type": "string",
                                "enum": ["incoming", "outgoing", "both"],
                                "default": "both",
                                "description": "Relationship direction"
                            },
                            "integration": {
                                "type": "string",
                                "description": "Filter by integration name"
                            },
                            "description": {
                                "type": "string",
                                "description": "Human-readable description of this relationship filter"
                            }
                        },
                        "required": ["relationship_type"]
                    },
                    "default": []
                },
                "allow_dynamic_search": {
                    "type": "boolean",
                    "title": "Allow Dynamic Search",
                    "description": "Allow agent to perform dynamic searches and custom Cypher queries",
                    "default": False
                },
                "allow_text_search": {
                    "type": "boolean",
                    "title": "Allow Text Search",
                    "description": "Allow agent to search nodes by text patterns",
                    "default": True
                },
                "allow_subgraph_queries": {
                    "type": "boolean",
                    "title": "Allow Subgraph Queries",
                    "description": "Allow agent to retrieve subgraphs (nodes and their relationships)",
                    "default": False
                },
                "allowed_integrations": {
                    "type": "array",
                    "title": "Allowed Integrations",
                    "description": "List of integrations the agent can query. If empty, all integrations are allowed.",
                    "items": {
                        "type": "string"
                    },
                    "default": []
                },
                "max_results": {
                    "type": "integer",
                    "title": "Maximum Results",
                    "description": "Maximum number of results to return per query",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 50
                },
                "default_subgraph_depth": {
                    "type": "integer",
                    "title": "Default Subgraph Depth",
                    "description": "Default depth for subgraph traversal (1-5)",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 1
                },
                "enable_caching": {
                    "type": "boolean",
                    "title": "Enable Caching",
                    "description": "Enable caching of graph query results for performance",
                    "default": True
                },
                "cache_ttl": {
                    "type": "integer",
                    "title": "Cache TTL (seconds)",
                    "description": "Cache time-to-live in seconds (0 to disable, max 1 hour)",
                    "minimum": 0,
                    "maximum": 3600,
                    "default": 300
                }
            }
        }
