"""Contextual Awareness Tools - Runtime implementation for accessing Context Graph API."""
import json
import httpx
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


class ContextualAwarenessTools:
    """
    Tools for accessing organizational context from the Context Graph API.

    Provides methods to query nodes, relationships, and perform graph traversals
    to understand organizational context in real-time.
    """

    def __init__(
        self,
        predefined_nodes: List[Dict[str, Any]] = None,
        predefined_relationships: List[Dict[str, Any]] = None,
        allow_dynamic_search: bool = False,
        allow_text_search: bool = True,
        allow_subgraph_queries: bool = False,
        allowed_integrations: Optional[List[str]] = None,
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
        self.predefined_nodes = predefined_nodes or []
        self.predefined_relationships = predefined_relationships or []
        self.allow_dynamic_search = allow_dynamic_search
        self.allow_text_search = allow_text_search
        self.allow_subgraph_queries = allow_subgraph_queries
        self.allowed_integrations = allowed_integrations
        self.max_results = max_results
        self.default_subgraph_depth = default_subgraph_depth
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl

        # Get control plane URL from environment or parameter
        import os
        self.control_plane_base_url = (
            control_plane_base_url or
            os.environ.get("CONTROL_PLANE_BASE_URL", "http://localhost:8000")
        ).rstrip("/")

        self.kubiya_api_key = kubiya_api_key or os.environ.get("KUBIYA_API_KEY")
        if not self.kubiya_api_key:
            raise ValueError("KUBIYA_API_KEY is required for Contextual Awareness tools")

        # Simple in-memory cache if enabled
        self._cache: Dict[str, Any] = {} if enable_caching else None

        logger.info(
            "contextual_awareness_tools_initialized",
            allow_dynamic_search=allow_dynamic_search,
            allow_text_search=allow_text_search,
            allow_subgraph_queries=allow_subgraph_queries,
            max_results=max_results,
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"UserKey {self.kubiya_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _check_integration_allowed(self, integration: Optional[str]) -> bool:
        """Check if an integration is allowed."""
        if not self.allowed_integrations:
            return True
        if not integration:
            return True
        return integration in self.allowed_integrations

    async def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the Context Graph API via Control Plane proxy."""
        url = f"{self.control_plane_base_url}/api/v1/context-graph{path}"

        # Check cache if enabled
        if self._cache is not None and method == "GET":
            cache_key = f"{method}:{url}:{json.dumps(params or {})}"
            if cache_key in self._cache:
                logger.debug("contextual_awareness_cache_hit", cache_key=cache_key[:50])
                return self._cache[cache_key]

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=self._get_headers(), params=params)
                elif method == "POST":
                    response = await client.post(
                        url, headers=self._get_headers(), params=params, json=json_data
                    )
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response.raise_for_status()
                result = response.json()

                # Cache result if enabled
                if self._cache is not None and method == "GET":
                    cache_key = f"{method}:{url}:{json.dumps(params or {})}"
                    self._cache[cache_key] = result

                return result

            except httpx.HTTPStatusError as e:
                logger.error(
                    "contextual_awareness_http_error",
                    status=e.response.status_code,
                    error=str(e),
                )
                raise RuntimeError(f"Context Graph API error ({e.response.status_code}): {e.response.text}")
            except Exception as e:
                logger.error("contextual_awareness_error", error=str(e))
                raise RuntimeError(f"Failed to query Context Graph: {str(e)}")

    async def search_nodes(
        self,
        label: Optional[str] = None,
        property_name: Optional[str] = None,
        property_value: Optional[Any] = None,
        integration: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for nodes in the context graph.

        Args:
            label: Node label to filter by (e.g., 'User', 'Team', 'Project')
            property_name: Property name to filter by
            property_value: Property value to match
            integration: Filter by integration name (e.g., 'Azure', 'Slack')
            limit: Maximum number of results (uses max_results if not specified)

        Returns:
            List of matching nodes
        """
        if not self._check_integration_allowed(integration):
            raise ValueError(f"Integration '{integration}' is not allowed")

        body = {}
        if label:
            body["label"] = label
        if property_name:
            body["property_name"] = property_name
        if property_value is not None:
            body["property_value"] = property_value

        params = {
            "skip": 0,
            "limit": min(limit or self.max_results, self.max_results),
        }
        if integration:
            params["integration"] = integration

        logger.info("searching_nodes", label=label, property_name=property_name)
        result = await self._make_request("POST", "/api/v1/graph/nodes/search", params=params, json_data=body)
        return result

    async def get_node(
        self,
        node_id: str,
        integration: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a specific node by its ID.

        Args:
            node_id: Node ID to retrieve
            integration: Filter by integration name

        Returns:
            Node details
        """
        if not self._check_integration_allowed(integration):
            raise ValueError(f"Integration '{integration}' is not allowed")

        params = {}
        if integration:
            params["integration"] = integration

        logger.info("getting_node", node_id=node_id)
        result = await self._make_request("GET", f"/api/v1/graph/nodes/{node_id}", params=params)
        return result

    async def get_relationships(
        self,
        node_id: str,
        direction: str = "both",
        relationship_type: Optional[str] = None,
        integration: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a specific node.

        Args:
            node_id: Node ID
            direction: Relationship direction: 'incoming', 'outgoing', or 'both'
            relationship_type: Filter by relationship type (e.g., 'BELONGS_TO', 'OWNS')
            integration: Filter by integration name
            limit: Maximum number of results

        Returns:
            List of relationships
        """
        if not self._check_integration_allowed(integration):
            raise ValueError(f"Integration '{integration}' is not allowed")

        params = {
            "direction": direction,
            "skip": 0,
            "limit": min(limit or self.max_results, self.max_results),
        }
        if relationship_type:
            params["relationship_type"] = relationship_type
        if integration:
            params["integration"] = integration

        logger.info("getting_relationships", node_id=node_id, direction=direction)
        result = await self._make_request("GET", f"/api/v1/graph/nodes/{node_id}/relationships", params=params)
        return result

    async def get_subgraph(
        self,
        node_id: str,
        depth: Optional[int] = None,
        relationship_types: Optional[List[str]] = None,
        integration: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a subgraph starting from a node.

        Args:
            node_id: Starting node ID
            depth: Traversal depth (1-5, uses default_subgraph_depth if not specified)
            relationship_types: List of relationship types to follow
            integration: Filter by integration name

        Returns:
            Subgraph with nodes and relationships
        """
        if not self.allow_subgraph_queries:
            raise RuntimeError("Subgraph queries are not enabled for this tool")

        if not self._check_integration_allowed(integration):
            raise ValueError(f"Integration '{integration}' is not allowed")

        body = {
            "node_id": node_id,
            "depth": min(depth or self.default_subgraph_depth, 5),
        }
        if relationship_types:
            body["relationship_types"] = relationship_types

        params = {}
        if integration:
            params["integration"] = integration

        logger.info("getting_subgraph", node_id=node_id, depth=body["depth"])
        result = await self._make_request("POST", "/api/v1/graph/subgraph", params=params, json_data=body)
        return result

    async def search_by_text(
        self,
        property_name: str,
        search_text: str,
        label: Optional[str] = None,
        integration: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search nodes by text pattern in a property.

        Args:
            property_name: Property name to search in
            search_text: Text to search for
            label: Optional node label to filter by
            integration: Filter by integration name
            limit: Maximum number of results

        Returns:
            List of matching nodes
        """
        if not self.allow_text_search:
            raise RuntimeError("Text search is not enabled for this tool")

        if not self._check_integration_allowed(integration):
            raise ValueError(f"Integration '{integration}' is not allowed")

        body = {
            "property_name": property_name,
            "search_text": search_text,
        }
        if label:
            body["label"] = label

        params = {
            "skip": 0,
            "limit": min(limit or self.max_results, self.max_results),
        }
        if integration:
            params["integration"] = integration

        logger.info("searching_by_text", property_name=property_name, search_text=search_text[:50])
        result = await self._make_request("POST", "/api/v1/graph/nodes/search/text", params=params, json_data=body)
        return result

    async def execute_cypher_query(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """
        Execute a custom Cypher query (read-only).

        IMPORTANT: Only available if allow_dynamic_search is enabled.
        The query will be automatically scoped to your organization's data.

        Args:
            query: Cypher query to execute (read-only)

        Returns:
            Query results
        """
        if not self.allow_dynamic_search:
            raise RuntimeError("Dynamic search and custom Cypher queries are not enabled for this tool")

        body = {"query": query}

        logger.info("executing_cypher_query", query=query[:100])
        result = await self._make_request("POST", "/api/v1/graph/query", json_data=body)
        return result

    async def get_graph_stats(
        self,
        integration: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics about the context graph.

        Args:
            integration: Filter by integration name

        Returns:
            Graph statistics (node counts, label counts, relationship type counts)
        """
        params = {}
        if integration:
            if not self._check_integration_allowed(integration):
                raise ValueError(f"Integration '{integration}' is not allowed")
            params["integration"] = integration

        logger.info("getting_graph_stats", integration=integration)
        result = await self._make_request("GET", "/api/v1/graph/stats", params=params)
        return result

    async def list_integrations(self) -> List[Dict[str, Any]]:
        """
        Get all available integrations for the organization.

        Returns:
            List of available integrations
        """
        logger.info("listing_integrations")
        result = await self._make_request("GET", "/api/v1/graph/integrations")

        # Filter by allowed integrations if specified
        if self.allowed_integrations:
            result = [i for i in result if i.get("name") in self.allowed_integrations]

        return result
