"""
Knowledge Context Tools - Fetch organizational knowledge for task planning
"""

import os
from typing import Optional, List
import structlog
import httpx
from control_plane_api.app.lib.planning_tools.base import BasePlanningTools

logger = structlog.get_logger()

KNOWLEDGE_API_BASE_URL = os.environ.get("KUBIYA_API_BASE", "https://api.kubiya.ai")
ORCHESTRATOR_API_BASE_URL = os.environ.get("ORCHESTRATOR_API_BASE", "https://orchestrator.kubiya.ai")

class KnowledgeContextTools(BasePlanningTools):
    """
    Tools for fetching organizational knowledge and documentation

    Provides methods to:
    - Search manual knowledge base (user-entered private docs)
    - Query organizational knowledge (Slack, Confluence, GitHub, etc.)
    - Get relevant documentation
    - Query best practices and guidelines
    """

    def __init__(
        self,
        db=None,
        organization_id: Optional[str] = None,
        api_token: Optional[str] = None,
        api_base_url: str = f"{KNOWLEDGE_API_BASE_URL}/api/v1",
        orchestrator_base_url: str = ORCHESTRATOR_API_BASE_URL
    ):
        super().__init__(db=db, organization_id=organization_id)
        self.name = "knowledge_context_tools"
        self.api_token = api_token
        self.api_base_url = api_base_url.rstrip("/")
        self.orchestrator_base_url = orchestrator_base_url.rstrip("/")

    async def get_all_knowledge(self) -> List[dict]:
        """
        Get all organizational knowledge and documentation

        Endpoint: GET /api/v1/knowledge
        Returns all knowledge items for the organization

        Returns:
            List of all knowledge items with complete data
        """
        if not self.api_token:
            logger.warning("knowledge_api_token_not_provided")
            return []

        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_base_url}/knowledge",
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    knowledge_items = data if isinstance(data, list) else data.get("data", [])

                    logger.info(
                        "knowledge_fetch_success",
                        count=len(knowledge_items)
                    )
                    return knowledge_items
                else:
                    logger.error(
                        "knowledge_fetch_failed",
                        status_code=response.status_code,
                        error=response.text
                    )
                    return []

        except Exception as e:
            logger.error("knowledge_fetch_error", error=str(e))
            return []

    async def query_knowledge(self, query: str) -> List[str]:
        """
        Query the knowledge base with a specific question or search term

        Endpoint: POST /api/v1/knowledge/query
        Searches through organizational knowledge and returns relevant results

        Args:
            query: Search query or question (e.g., "how to deploy to AWS?", "raz==superman ? omer==?")

        Returns:
            List of relevant knowledge items/answers as strings
        """
        if not self.api_token:
            logger.warning("knowledge_api_token_not_provided")
            return []

        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            payload = {"query": query}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/knowledge/query",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    # API returns a list of strings
                    results = data if isinstance(data, list) else []

                    logger.info(
                        "knowledge_query_success",
                        query=query,
                        results_count=len(results)
                    )
                    return results
                else:
                    logger.error(
                        "knowledge_query_failed",
                        query=query,
                        status_code=response.status_code,
                        error=response.text
                    )
                    return []

        except Exception as e:
            logger.error("knowledge_query_error", query=query, error=str(e))
            return []

    async def query_organizational_knowledge(self, query: str, limit: int = 5) -> List[dict]:
        """
        Query organizational knowledge from integrated sources (Slack, Confluence, GitHub, etc.)

        Endpoint: POST https://orchestrator.kubiya.ai/api/query
        Searches through Slack messages, Confluence pages, GitHub discussions, and other integrated sources

        Args:
            query: Search query or question (e.g., "I seems that version 0.3.37 is broken")
            limit: Maximum number of results to return (default: 5)

        Returns:
            List of relevant knowledge items from organizational sources
        """
        if not self.api_token:
            logger.warning("orchestrator_api_token_not_provided")
            return []

        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            payload = {
                "query": query,
                "limit": limit
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.orchestrator_base_url}/api/query",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    # API returns results as a list or dict with results key
                    results = data if isinstance(data, list) else data.get("results", data.get("data", []))

                    logger.info(
                        "organizational_knowledge_query_success",
                        query=query,
                        results_count=len(results) if isinstance(results, list) else 0
                    )
                    return results if isinstance(results, list) else []
                else:
                    logger.error(
                        "organizational_knowledge_query_failed",
                        query=query,
                        status_code=response.status_code,
                        error=response.text
                    )
                    return []

        except Exception as e:
            logger.error("organizational_knowledge_query_error", query=query, error=str(e))
            return []

