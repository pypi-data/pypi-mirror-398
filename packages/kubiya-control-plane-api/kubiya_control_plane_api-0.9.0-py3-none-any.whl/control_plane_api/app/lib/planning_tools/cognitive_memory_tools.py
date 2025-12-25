"""
Cognitive Memory Planning Tools

Provides intelligent memory and context graph operations for planning agents.

This tool enables the planning agent to:
1. Memorize important context and insights
2. Recall relevant memories based on semantic queries
3. Search context graphs for knowledge
4. Extract insights from accumulated knowledge
5. Query organizational memory

Following the same pattern used by workers and skills for tool-based discovery.
"""

import structlog
from typing import Optional, List, Dict, Any
import httpx

from control_plane_api.app.lib.planning_tools.base import BasePlanningTools

logger = structlog.get_logger(__name__)


class CognitiveMemoryPlanningTools(BasePlanningTools):
    """
    Cognitive memory tools for intelligent context and knowledge operations during planning.

    Usage pattern:
    1. AI analyzes task and context
    2. AI memorizes important information for future reference
    3. AI recalls relevant memories when needed
    4. AI searches semantic memory for related knowledge
    5. AI extracts insights from accumulated context
    """

    def __init__(
        self,
        db=None,
        organization_id: Optional[str] = None,
        api_token: Optional[str] = None,
        context_graph_api_base: Optional[str] = None,
    ):
        """
        Initialize cognitive memory planning tools

        Args:
            db: Database session for direct data access
            organization_id: Organization context for filtering
            api_token: API token for context graph authentication
            context_graph_api_base: Context graph API base URL
        """
        super().__init__(db=db, organization_id=organization_id)
        self.name = "cognitive_memory_planning_tools"
        self.api_token = api_token
        self.context_graph_api_base = (
            context_graph_api_base or "https://graph.kubiya.ai"
        ).rstrip("/")

        # HTTP client for API calls
        self._client = httpx.AsyncClient(
            base_url=self.context_graph_api_base,
            timeout=httpx.Timeout(timeout=60.0),
            headers={
                "Authorization": f"Bearer {api_token}" if api_token else "",
                "Content-Type": "application/json",
            },
        )

    async def memorize_context(
        self,
        context: str,
        metadata: Optional[Dict[str, Any]] = None,
        dataset_id: Optional[str] = None,
    ) -> str:
        """
        Memorize important context for future recall.

        Use this to store significant insights, decisions, or information that
        may be relevant for future tasks or conversations.

        Args:
            context: The context or information to memorize
            metadata: Optional metadata (tags, categories, etc.)
            dataset_id: Optional dataset ID for scoped storage

        Returns:
            JSON string with memorization result:
            {
                "status": "success",
                "memory_id": "mem_...",
                "message": "Context memorized successfully"
            }
        """
        try:
            logger.info(
                "memorize_context",
                organization_id=self.organization_id,
                has_metadata=bool(metadata),
                has_dataset=bool(dataset_id),
            )

            payload = {
                "context": {"text": context},
                "metadata": metadata or {},
            }

            if dataset_id:
                payload["dataset_id"] = dataset_id

            response = await self._client.post(
                f"/api/v1/organizations/{self.organization_id}/memory/memorize",
                json=payload,
            )
            response.raise_for_status()

            result = response.json()
            return self._format_detail_response(
                result,
                "Memory Stored",
            )

        except Exception as e:
            logger.error(
                "memorize_context_failed",
                error=str(e),
                organization_id=self.organization_id,
            )
            return self._format_error("Failed to memorize context", str(e))

    async def recall_memories(
        self,
        query: str,
        limit: int = 5,
        dataset_ids: Optional[List[str]] = None,
    ) -> str:
        """
        Recall memories relevant to a query.

        Use this to retrieve previously memorized context, insights, or information
        that may be relevant to the current task.

        Args:
            query: Natural language query describing what to recall
            limit: Maximum number of memories to return (default: 5)
            dataset_ids: Optional list of dataset IDs to filter by

        Returns:
            JSON string with relevant memories:
            [
                {
                    "id": "mem_...",
                    "content": "Previously memorized context...",
                    "metadata": {...},
                    "created_at": "2025-01-15T10:30:00Z",
                    "relevance_score": 0.95
                },
                ...
            ]
        """
        try:
            logger.info(
                "recall_memories",
                query_length=len(query),
                limit=limit,
                organization_id=self.organization_id,
                has_dataset_filter=bool(dataset_ids),
            )

            params = {
                "query": query,
                "limit": limit,
            }

            if dataset_ids:
                params["dataset_ids"] = ",".join(dataset_ids)

            response = await self._client.get(
                f"/api/v1/organizations/{self.organization_id}/memory/recall",
                params=params,
            )
            response.raise_for_status()

            memories = response.json()

            if not memories:
                return self._format_list_response(
                    [],
                    f"No relevant memories found for: {query}",
                    [],
                )

            return self._format_list_response(
                memories,
                f"Relevant Memories ({len(memories)} found)",
                ["id", "content", "created_at"],
            )

        except Exception as e:
            logger.error(
                "recall_memories_failed",
                error=str(e),
                organization_id=self.organization_id,
            )
            return self._format_error("Failed to recall memories", str(e))

    async def search_semantic_memory(
        self,
        query: str,
        search_type: str = "GRAPH_COMPLETION",
        limit: int = 10,
        dataset_ids: Optional[List[str]] = None,
    ) -> str:
        """
        Search semantic memory using advanced graph-based search.

        Use this for intelligent search that understands relationships and context,
        not just keyword matching.

        Args:
            query: Natural language search query
            search_type: Type of search (GRAPH_COMPLETION, RAG_COMPLETION, CHUNKS)
            limit: Maximum results to return (default: 10)
            dataset_ids: Optional list of dataset IDs to filter by

        Returns:
            JSON string with search results:
            [
                {
                    "text": "Result text...",
                    "metadata": {...},
                    "relevance_score": 0.92
                },
                ...
            ]
        """
        try:
            logger.info(
                "search_semantic_memory",
                query_length=len(query),
                search_type=search_type,
                limit=limit,
                organization_id=self.organization_id,
            )

            payload = {
                "query": query,
                "search_type": search_type,
                "limit": limit,
            }

            if dataset_ids:
                payload["dataset_ids"] = dataset_ids

            response = await self._client.post(
                f"/api/v1/organizations/{self.organization_id}/memory/search",
                json=payload,
            )
            response.raise_for_status()

            results = response.json()

            if not results:
                return self._format_list_response(
                    [],
                    f"No results found for: {query}",
                    [],
                )

            return self._format_list_response(
                results.get("results", results),
                f"Search Results ({len(results.get('results', results))} found)",
                ["text"],
            )

        except Exception as e:
            logger.error(
                "search_semantic_memory_failed",
                error=str(e),
                organization_id=self.organization_id,
            )
            return self._format_error("Failed to search semantic memory", str(e))

    async def get_memory_insights(
        self,
        dataset_ids: Optional[List[str]] = None,
        insight_type: str = "patterns",
    ) -> str:
        """
        Get cognitive insights from accumulated memories.

        Use this to extract patterns, summaries, or insights from the knowledge base.

        Args:
            dataset_ids: Optional list of dataset IDs to analyze
            insight_type: Type of insights (patterns, summaries, trends)

        Returns:
            JSON string with insights:
            {
                "insights": [...],
                "patterns": [...],
                "summary": "..."
            }
        """
        try:
            logger.info(
                "get_memory_insights",
                insight_type=insight_type,
                organization_id=self.organization_id,
            )

            params = {
                "insight_type": insight_type,
            }

            if dataset_ids:
                params["dataset_ids"] = ",".join(dataset_ids)

            response = await self._client.get(
                f"/api/v1/organizations/{self.organization_id}/memory/insights",
                params=params,
            )
            response.raise_for_status()

            insights = response.json()
            return self._format_detail_response(
                insights,
                f"Memory Insights ({insight_type})",
            )

        except Exception as e:
            logger.error(
                "get_memory_insights_failed",
                error=str(e),
                organization_id=self.organization_id,
            )
            return self._format_error("Failed to get memory insights", str(e))

    async def list_memory_datasets(self) -> str:
        """
        List all memory datasets available to the organization.

        Use this to discover what memory contexts are available.

        Returns:
            JSON string with datasets:
            [
                {
                    "id": "dataset_...",
                    "name": "project_alpha",
                    "description": "...",
                    "created_at": "2025-01-15T10:30:00Z",
                    "memory_count": 42
                },
                ...
            ]
        """
        try:
            logger.info(
                "list_memory_datasets",
                organization_id=self.organization_id,
            )

            response = await self._client.get(
                f"/api/v1/organizations/{self.organization_id}/memory/datasets",
            )
            response.raise_for_status()

            datasets = response.json()

            if not datasets:
                return self._format_list_response(
                    [],
                    "No memory datasets found",
                    [],
                )

            return self._format_list_response(
                datasets,
                f"Memory Datasets ({len(datasets)} found)",
                ["id", "name", "memory_count", "created_at"],
            )

        except Exception as e:
            logger.error(
                "list_memory_datasets_failed",
                error=str(e),
                organization_id=self.organization_id,
            )
            return self._format_error("Failed to list memory datasets", str(e))

    def _format_error(self, message: str, error: str) -> str:
        """Format error response"""
        import json
        return json.dumps({
            "error": message,
            "details": error,
        }, indent=2)

    async def close(self):
        """Close HTTP client"""
        await self._client.aclose()
