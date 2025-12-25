"""
Context Graph Client

Provides typed interface to context graph API.
Handles communication with Neo4j-based knowledge graph at https://graph.kubiya.ai
"""

import httpx
import structlog
from typing import Optional, Dict, Any, List

logger = structlog.get_logger(__name__)


class ContextGraphClient:
    """Client for querying context graph API"""

    def __init__(
        self,
        api_base: str,
        api_token: str,
        organization_id: str,
        timeout: int = 30
    ):
        """
        Initialize context graph client

        Args:
            api_base: Base URL for context graph API (e.g., https://graph.kubiya.ai)
            api_token: API token for authentication
            organization_id: Organization ID for scoping queries
            timeout: Request timeout in seconds
        """
        self.api_base = api_base.rstrip("/")
        self.api_token = api_token
        self.organization_id = organization_id
        self.timeout = timeout

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute Cypher query on context graph.

        Args:
            query: Cypher query string
            parameters: Query parameters for parameterized queries

        Returns:
            {"data": [...], "summary": {...}}

        Raises:
            httpx.HTTPStatusError: If API returns error status
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/api/v1/graph/query",
                    json={"query": query, "parameters": parameters or {}},
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "X-Organization-ID": self.organization_id
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "context_graph_query_error",
                status_code=e.response.status_code,
                error=str(e),
                query=query[:200]  # Log first 200 chars of query
            )
            raise
        except Exception as e:
            logger.error("context_graph_connection_error", error=str(e))
            raise

    async def search_nodes(
        self,
        label: Optional[str] = None,
        property_name: Optional[str] = None,
        property_value: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Search nodes by label and properties

        Args:
            label: Node label to filter (e.g., "Agent", "Team", "Service")
            property_name: Property name to filter on
            property_value: Property value to match
            limit: Maximum number of results

        Returns:
            {"nodes": [...], "count": N}
        """
        try:
            async with httpx.AsyncClient() as client:
                params = {"limit": limit}
                if label:
                    params["label"] = label
                if property_name:
                    params["property_name"] = property_name
                if property_value:
                    params["property_value"] = property_value

                response = await client.get(
                    f"{self.api_base}/api/v1/graph/nodes/search",
                    params=params,
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "X-Organization-ID": self.organization_id
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "context_graph_search_error",
                status_code=e.response.status_code,
                label=label,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error("context_graph_search_connection_error", error=str(e))
            raise

    async def search_by_text(
        self,
        search_text: str,
        label: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Free-text search across node properties

        Args:
            search_text: Text to search for across node properties
            label: Optional node label to filter results
            limit: Maximum number of results

        Returns:
            {"nodes": [...], "count": N}
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/api/v1/graph/nodes/search/text",
                    json={
                        "search_text": search_text,
                        "label": label,
                        "limit": limit
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "X-Organization-ID": self.organization_id
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "context_graph_text_search_error",
                status_code=e.response.status_code,
                search_text=search_text[:100],
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error("context_graph_text_search_connection_error", error=str(e))
            raise

    async def get_node_relationships(
        self,
        node_id: str,
        relationship_type: Optional[str] = None,
        direction: str = "both"
    ) -> Dict[str, Any]:
        """
        Get relationships for a specific node

        Args:
            node_id: ID of the node
            relationship_type: Optional filter for relationship type
            direction: "outgoing", "incoming", or "both"

        Returns:
            {"relationships": [...]}
        """
        try:
            async with httpx.AsyncClient() as client:
                params = {"direction": direction}
                if relationship_type:
                    params["relationship_type"] = relationship_type

                response = await client.get(
                    f"{self.api_base}/api/v1/graph/nodes/{node_id}/relationships",
                    params=params,
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "X-Organization-ID": self.organization_id
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "context_graph_relationships_error",
                status_code=e.response.status_code,
                node_id=node_id,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error("context_graph_relationships_connection_error", error=str(e))
            raise
