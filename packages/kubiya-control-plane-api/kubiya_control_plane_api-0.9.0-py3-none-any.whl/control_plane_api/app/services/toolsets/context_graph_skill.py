"""
Context Graph Skill - Memory and Knowledge Graph Tools

Provides agents with persistent memory capabilities and knowledge graph search.
All operations are automatically scoped to environment-specific datasets.

This skill extends Agno Toolkit to work with both Agno and Claude Code runtimes.
"""

from typing import Optional, Dict, Any, List
import httpx
import logging
import asyncio
from agno.tools import Toolkit

logger = logging.getLogger(__name__)


# Retry configuration for transient failures
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 10.0  # seconds


async def _retry_with_backoff(func, max_retries: int = MAX_RETRIES, initial_delay: float = INITIAL_RETRY_DELAY):
    """
    Retry a function with exponential backoff for transient failures.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial retry delay in seconds

    Returns:
        Result from func

    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return await func()
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"Transient error on attempt {attempt + 1}/{max_retries}, retrying in {delay}s",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "attempt": attempt + 1,
                        "delay": delay,
                    }
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, MAX_RETRY_DELAY)  # Exponential backoff with cap
            else:
                logger.error(
                    f"All {max_retries} retry attempts failed",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
        except Exception as e:
            # Non-transient errors: fail immediately
            logger.error(
                f"Non-transient error, not retrying",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            raise

    raise last_exception


class ContextGraphSkill(Toolkit):
    """
    Context graph skill providing memory and search capabilities.

    This skill provides three main capabilities:
    1. store_memory - Store information for later recall
    2. recall_memory - Search and retrieve stored memories
    3. semantic_search - Search the knowledge graph

    All operations are automatically scoped to the agent's environment dataset.
    """

    def __init__(
        self,
        graph_api_url: str,
        api_key: str,
        organization_id: str,
        dataset_name: str,
        auto_create_dataset: bool = True,
    ):
        """
        Initialize context graph skill.

        Args:
            graph_api_url: Base URL for context graph API
            api_key: Kubiya API key for authentication
            organization_id: Organization ID for scoping
            dataset_name: Dataset name (typically environment name)
            auto_create_dataset: Auto-create dataset if doesn't exist
        """
        # Initialize Toolkit base class with a name
        super().__init__(name="context-graph-memory")

        self.graph_api_url = graph_api_url.rstrip('/')
        self.api_key = api_key
        self.organization_id = organization_id
        self.dataset_name = dataset_name
        self.auto_create_dataset = auto_create_dataset
        self._dataset_id = None  # Lazy-loaded and cached

        # Register all tool methods with the toolkit
        self.register(self.store_memory)
        self.register(self.recall_memory)
        self.register(self.semantic_search)

        logger.info(
            f"Initialized ContextGraphSkill with 3 tools",
            extra={
                "dataset_name": dataset_name,
                "organization_id": organization_id,
                "graph_api_url": graph_api_url,
            }
        )

    async def _get_or_create_dataset(self) -> str:
        """
        Get or create dataset ID for this environment (cached).

        Returns:
            Dataset ID (UUID string)

        Raises:
            Exception: If dataset not found and auto-create disabled
        """
        # Return cached dataset ID if available
        if self._dataset_id:
            return self._dataset_id

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Organization-ID": self.organization_id,
        }

        try:
            # Increased timeout for reliability with remote graph API
            async with httpx.AsyncClient(timeout=60.0) as client:
                # List datasets to find ours
                response = await client.get(
                    f"{self.graph_api_url}/api/v1/datasets",
                    headers=headers,
                )

                if response.status_code == 200:
                    datasets = response.json()
                    for ds in datasets:
                        if ds.get("name") == self.dataset_name:
                            self._dataset_id = ds["id"]
                            logger.info(
                                f"Found existing dataset",
                                extra={
                                    "dataset_id": self._dataset_id,
                                    "dataset_name": self.dataset_name,
                                }
                            )
                            return self._dataset_id

                # Dataset not found, create if enabled
                if self.auto_create_dataset:
                    create_response = await client.post(
                        f"{self.graph_api_url}/api/v1/datasets",
                        headers=headers,
                        json={
                            "name": self.dataset_name,
                            "description": f"Auto-created dataset for environment: {self.dataset_name}",
                            "scope": "org",  # Org-scoped for team collaboration
                        },
                    )

                    if create_response.status_code in [200, 201]:
                        dataset_data = create_response.json()
                        self._dataset_id = dataset_data["id"]
                        logger.info(
                            f"Created new dataset",
                            extra={
                                "dataset_id": self._dataset_id,
                                "dataset_name": self.dataset_name,
                            }
                        )
                        return self._dataset_id
                    else:
                        error_msg = f"Failed to create dataset: {create_response.status_code} - {create_response.text}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                else:
                    error_msg = f"Dataset '{self.dataset_name}' not found and auto-create disabled"
                    logger.error(error_msg)
                    raise Exception(error_msg)

        except httpx.TimeoutException:
            error_msg = "Request to graph API timed out while getting/creating dataset"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Failed to connect to graph API: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def store_memory(
        self,
        context: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store context in persistent memory.

        Args:
            context: Information to remember (text description or structured data)
            metadata: Optional metadata (tags, category, timestamp, etc.)

        Returns:
            Success message with memory ID
        """
        try:
            dataset_id = await self._get_or_create_dataset()

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "X-Organization-ID": self.organization_id,
            }

            # Prepare context payload
            context_dict = {"content": context}
            if metadata:
                context_dict["metadata"] = metadata

            # Increased timeout for long-running memory operations
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.graph_api_url}/api/v1/memory/store",
                    headers=headers,
                    json={
                        "context": context_dict,
                        "dataset_id": dataset_id,
                        "metadata": metadata,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    memory_id = result.get("memory_id", "unknown")
                    logger.info(
                        f"Memory stored successfully",
                        extra={
                            "memory_id": memory_id,
                            "dataset_id": dataset_id,
                        }
                    )
                    return f"✓ Memory stored successfully. Memory ID: {memory_id}"
                else:
                    error_msg = f"Failed to store memory: HTTP {response.status_code}"
                    logger.error(error_msg, extra={"response": response.text[:500]})
                    return f"Error storing memory: {error_msg}"

        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg, extra={"error_type": type(e).__name__})
            return f"Error: {error_msg}"

    async def recall_memory(
        self,
        query: str,
        limit: int = 5,
    ) -> str:
        """
        Recall memories using semantic search with retry logic.

        Args:
            query: Search query (natural language)
            limit: Maximum number of results (default: 5)

        Returns:
            Formatted list of relevant memories
        """
        try:
            dataset_id = await self._get_or_create_dataset()

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "X-Organization-ID": self.organization_id,
            }

            # Define the recall request as a function for retry
            async def _do_recall():
                # Increased timeout for long-running recall operations
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{self.graph_api_url}/api/v1/memory/recall",
                        headers=headers,
                        json={
                            "query": query,
                            "dataset_id": dataset_id,
                            "limit": limit,
                        },
                    )
                    return response

            # Execute with retry logic
            response = await _retry_with_backoff(_do_recall)

            if response.status_code == 200:
                results = response.json()

                if not results or len(results) == 0:
                    return f"No memories found for query: '{query}'"

                # Format results for LLM
                formatted = f"Found {len(results)} relevant memories:\n\n"
                for i, item in enumerate(results, 1):
                    content = item.get('content', item.get('text', 'N/A'))
                    formatted += f"{i}. {content}\n"

                    if item.get('metadata'):
                        formatted += f"   Metadata: {item['metadata']}\n"

                    if item.get('similarity_score'):
                        formatted += f"   Relevance: {item['similarity_score']:.2f}\n"

                    formatted += "\n"

                logger.info(
                    f"Recalled {len(results)} memories",
                    extra={
                        "query": query,
                        "result_count": len(results),
                        "dataset_id": dataset_id,
                    }
                )

                return formatted
            else:
                error_msg = f"Failed to recall memory: HTTP {response.status_code}"
                logger.error(error_msg, extra={"response": response.text[:500]})
                return f"Error recalling memory: {error_msg}"

        except Exception as e:
            error_msg = f"Failed to recall memory: {str(e)}"
            logger.error(error_msg, extra={"error_type": type(e).__name__})
            return f"Error: {error_msg}"

    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
    ) -> str:
        """
        Perform semantic search across the knowledge graph.

        Args:
            query: Natural language search query
            limit: Maximum number of results (default: 10)

        Returns:
            Formatted search results
        """
        try:
            dataset_id = await self._get_or_create_dataset()

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "X-Organization-ID": self.organization_id,
            }

            # Increased timeout for semantic search operations
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.graph_api_url}/api/v1/search/semantic",
                    headers=headers,
                    json={
                        "query": query,
                        "filters": {"dataset_ids": [dataset_id]},
                        "limit": limit,
                    },
                )

                if response.status_code == 200:
                    results = response.json()

                    if not results or len(results) == 0:
                        return f"No results found for query: '{query}'"

                    # Format results
                    formatted = f"Semantic search results for '{query}':\n\n"
                    for i, item in enumerate(results, 1):
                        content = item.get('content', item.get('text', 'N/A'))
                        formatted += f"{i}. {content}\n"

                        if item.get('similarity_score'):
                            formatted += f"   Relevance: {item['similarity_score']:.2f}\n"

                        if item.get('metadata'):
                            formatted += f"   Metadata: {item['metadata']}\n"

                        if item.get('source'):
                            formatted += f"   Source: {item['source']}\n"

                        formatted += "\n"

                    logger.info(
                        f"Semantic search returned {len(results)} results",
                        extra={
                            "query": query,
                            "result_count": len(results),
                            "dataset_id": dataset_id,
                        }
                    )

                    return formatted
                else:
                    error_msg = f"Failed to search: HTTP {response.status_code}"
                    logger.error(error_msg, extra={"response": response.text[:500]})
                    return f"Error performing search: {error_msg}"

        except Exception as e:
            error_msg = f"Failed to search: {str(e)}"
            logger.error(error_msg, extra={"error_type": type(e).__name__})
            return f"Error: {error_msg}"
