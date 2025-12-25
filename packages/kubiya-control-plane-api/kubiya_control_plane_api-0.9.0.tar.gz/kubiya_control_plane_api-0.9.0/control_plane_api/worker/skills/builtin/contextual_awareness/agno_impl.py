"""Contextual Awareness skill implementation for agno runtime."""
from control_plane_api.worker.services.contextual_awareness_tools import (
    ContextualAwarenessTools as BaseContextualAwarenessTools
)


class ContextualAwarenessTools(BaseContextualAwarenessTools):
    """
    Contextual Awareness tools using existing ContextualAwarenessTools.

    Wraps the base contextual awareness implementation.
    """

    def __init__(
        self,
        predefined_nodes: list = None,
        predefined_relationships: list = None,
        allow_dynamic_search: bool = False,
        allow_text_search: bool = True,
        allow_subgraph_queries: bool = False,
        allowed_integrations: list = None,
        max_results: int = 100,
        default_subgraph_depth: int = 1,
        enable_caching: bool = True,
        cache_ttl: int = 300,
        control_plane_base_url: str = None,
        kubiya_api_key: str = None,
        **kwargs
    ):
        """
        Initialize contextual awareness tools.

        Args:
            predefined_nodes: List of predefined node filters
            predefined_relationships: List of predefined relationship filters
            allow_dynamic_search: Allow dynamic searches and custom Cypher queries
            allow_text_search: Allow text-based searches
            allow_subgraph_queries: Allow subgraph queries
            allowed_integrations: List of allowed integrations (None = all)
            max_results: Maximum results per query
            default_subgraph_depth: Default subgraph traversal depth
            enable_caching: Enable result caching
            cache_ttl: Cache TTL in seconds
            control_plane_base_url: Control Plane API base URL
            kubiya_api_key: Kubiya API key for authentication
            **kwargs: Additional configuration
        """
        super().__init__(
            predefined_nodes=predefined_nodes,
            predefined_relationships=predefined_relationships,
            allow_dynamic_search=allow_dynamic_search,
            allow_text_search=allow_text_search,
            allow_subgraph_queries=allow_subgraph_queries,
            allowed_integrations=allowed_integrations,
            max_results=max_results,
            default_subgraph_depth=default_subgraph_depth,
            enable_caching=enable_caching,
            cache_ttl=cache_ttl,
            control_plane_base_url=control_plane_base_url,
            kubiya_api_key=kubiya_api_key,
            **kwargs
        )
