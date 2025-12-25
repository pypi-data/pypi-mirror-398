"""Context Graph Search skill implementation for all runtimes."""
import os
import json
import structlog
from typing import Optional, Dict, Any, List
import httpx
from agno.tools import Toolkit
from control_plane_api.worker.skills.builtin.schema_fix_mixin import SchemaFixMixin

logger = structlog.get_logger(__name__)


class ContextGraphSearchTools(SchemaFixMixin, Toolkit):
    """
    Context Graph Search toolkit for querying Neo4j-based context graphs and managing memory.

    Provides tools for:
    - **Memory**: Store and recall information persistently
    - **Graph Search**: Search nodes by properties and relationships
    - **Text Search**: Find nodes by text patterns
    - **Custom Queries**: Execute Cypher queries
    - **Metadata**: Get available labels and relationship types
    """

    def __init__(
        self,
        api_base: Optional[str] = None,
        timeout: int = 60,  # 60s timeout - fail fast, no retries
        default_limit: int = 100,
        **kwargs
    ):
        """
        Initialize Context Graph Search tools.

        Args:
            api_base: Context Graph API base URL (defaults to CONTEXT_GRAPH_API_BASE env var)
            timeout: Request timeout in seconds (default: 60s - no retries)
            default_limit: Default result limit for queries
            **kwargs: Additional configuration
        """
        super().__init__(name="context-graph-search")

        # Get authentication
        self.api_key = os.environ.get("KUBIYA_API_KEY")
        self.org_id = os.environ.get("KUBIYA_ORG_ID")

        # Get dataset name for memory scoping (defaults to "default")
        self.dataset_name = os.environ.get("MEMORY_DATASET_NAME", "default")
        self._dataset_id = None  # Lazy-loaded and cached

        if not self.api_key:
            logger.warning("No KUBIYA_API_KEY provided - context graph queries will fail")

        # Resolve API base URL
        # Priority: 1) explicit param, 2) env var, 3) fetch from control plane, 4) fallback
        if api_base:
            self.api_base = api_base.rstrip("/")
        elif os.environ.get("CONTEXT_GRAPH_API_BASE"):
            self.api_base = os.environ.get("CONTEXT_GRAPH_API_BASE").rstrip("/")
        else:
            # Fetch context-graph-api URL from control plane's client config
            self.api_base = self._fetch_graph_url_from_control_plane() or "https://context-graph-api.dev.kubiya.ai"
            self.api_base = self.api_base.rstrip("/")

        self.timeout = timeout
        self.default_limit = default_limit

        # Prepare headers
        self.headers = {
            "Authorization": f"UserKey {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Kubiya-Client": "agent-runtime-builtin-tool",
        }

        if self.org_id:
            self.headers["X-Organization-ID"] = self.org_id

        # Register all tool methods
        # Memory tools (most important - register first)
        self.register(self.store_memory)
        self.register(self.recall_memory)
        # Knowledge ingestion tools
        self.register(self.ingest_knowledge)
        self.register(self.process_dataset)
        # Graph search tools
        self.register(self.search_nodes)
        self.register(self.get_node)
        self.register(self.search_by_text)
        # Advanced tools
        self.register(self.get_relationships)
        self.register(self.get_subgraph)
        self.register(self.execute_query)
        self.register(self.get_labels)
        self.register(self.get_relationship_types)

        logger.info(f"Initialized Context Graph Search tools with memory and ingestion support (api_base: {self.api_base}, dataset: {self.dataset_name})")

        # Fix: Rebuild function schemas with proper parameters
        self._rebuild_function_schemas()
    def _fetch_graph_url_from_control_plane(self) -> Optional[str]:
        """
        Fetch the context graph API URL from control plane's client config endpoint.

        Returns:
            Context graph API URL or None if fetch fails
        """
        control_plane_url = os.environ.get("CONTROL_PLANE_URL", "http://localhost:7777")

        try:
            with httpx.Client(timeout=5.0) as client:
                headers = {
                    "Authorization": f"UserKey {self.api_key}",
                    "Accept": "application/json",
                }

                response = client.get(
                    f"{control_plane_url}/api/v1/client/config",
                    headers=headers
                )

                if response.status_code == 200:
                    config = response.json()
                    graph_url = config.get("context_graph_api_base")
                    logger.info(f"Fetched graph URL from control plane: {graph_url}")
                    return graph_url
                else:
                    logger.warning(f"Failed to fetch client config: HTTP {response.status_code}")
                    return None

        except Exception as e:
            logger.warning(f"Could not fetch client config from control plane: {e}")
            return None

    def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Context Graph API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., "/api/v1/graph/nodes")
            params: Query parameters
            body: Request body for POST requests

        Returns:
            Response JSON

        Raises:
            Exception: If request fails
        """
        url = f"{self.api_base}{path}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                if method == "GET":
                    response = client.get(url, headers=self.headers, params=params)
                elif method == "POST":
                    response = client.post(url, headers=self.headers, params=params, json=body)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            raise Exception(f"Request timed out after {self.timeout}s: {method} {path}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    def search_nodes(
        self,
        label: Optional[str] = None,
        property_name: Optional[str] = None,
        property_value: Optional[str] = None,
        integration: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> str:
        """
        Search for nodes in the context graph by label and/or properties.

        Args:
            label: Node label to filter by (e.g., "User", "Repository", "Service")
            property_name: Property name to filter by
            property_value: Property value to match
            integration: Integration name to filter by
            skip: Number of results to skip
            limit: Maximum number of results to return

        Returns:
            JSON string with search results

        Example:
            search_nodes(label="User", property_name="email", property_value="user@example.com")
            search_nodes(label="Repository", integration="github")
        """
        body = {}
        if label:
            body["label"] = label
        if property_name:
            body["property_name"] = property_name
        if property_value:
            body["property_value"] = property_value

        params = {
            "skip": skip,
            "limit": limit or self.default_limit,
        }
        if integration:
            params["integration"] = integration

        result = self._make_request("POST", "/api/v1/graph/nodes/search", params=params, body=body)
        return json.dumps(result, indent=2)

    def get_node(
        self,
        node_id: str,
        integration: Optional[str] = None,
    ) -> str:
        """
        Get a specific node by its ID.

        Args:
            node_id: The node ID to retrieve
            integration: Optional integration name to filter by

        Returns:
            JSON string with node details

        Example:
            get_node(node_id="abc123")
        """
        params = {}
        if integration:
            params["integration"] = integration

        result = self._make_request("GET", f"/api/v1/graph/nodes/{node_id}", params=params)
        return json.dumps(result, indent=2)

    def get_relationships(
        self,
        node_id: str,
        direction: str = "both",
        relationship_type: Optional[str] = None,
        integration: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> str:
        """
        Get relationships for a specific node.

        Args:
            node_id: The node ID to get relationships for
            direction: Relationship direction ("incoming", "outgoing", or "both")
            relationship_type: Optional relationship type to filter by
            integration: Optional integration name to filter by
            skip: Number of results to skip
            limit: Maximum number of results to return

        Returns:
            JSON string with relationships

        Example:
            get_relationships(node_id="abc123", direction="outgoing", relationship_type="OWNS")
        """
        params = {
            "direction": direction,
            "skip": skip,
            "limit": limit or self.default_limit,
        }
        if relationship_type:
            params["relationship_type"] = relationship_type
        if integration:
            params["integration"] = integration

        result = self._make_request("GET", f"/api/v1/graph/nodes/{node_id}/relationships", params=params)
        return json.dumps(result, indent=2)

    def get_subgraph(
        self,
        node_id: str,
        depth: int = 1,
        relationship_types: Optional[List[str]] = None,
        integration: Optional[str] = None,
    ) -> str:
        """
        Get a subgraph starting from a node.

        Args:
            node_id: Starting node ID
            depth: Traversal depth (1-5)
            relationship_types: Optional list of relationship types to follow
            integration: Optional integration name to filter by

        Returns:
            JSON string with subgraph (nodes and relationships)

        Example:
            get_subgraph(node_id="abc123", depth=2, relationship_types=["OWNS", "MANAGES"])
        """
        body = {
            "node_id": node_id,
            "depth": min(max(depth, 1), 5),  # Clamp between 1 and 5
        }
        if relationship_types:
            body["relationship_types"] = relationship_types

        params = {}
        if integration:
            params["integration"] = integration

        result = self._make_request("POST", "/api/v1/graph/subgraph", params=params, body=body)
        return json.dumps(result, indent=2)

    def search_by_text(
        self,
        property_name: str,
        search_text: str,
        label: Optional[str] = None,
        integration: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> str:
        """
        Search nodes by text pattern in a property.

        Args:
            property_name: Property name to search in
            search_text: Text to search for (supports partial matching)
            label: Optional node label to filter by
            integration: Optional integration name to filter by
            skip: Number of results to skip
            limit: Maximum number of results to return

        Returns:
            JSON string with search results

        Example:
            search_by_text(property_name="name", search_text="kubernetes", label="Service")
        """
        body = {
            "property_name": property_name,
            "search_text": search_text,
        }
        if label:
            body["label"] = label

        params = {
            "skip": skip,
            "limit": limit or self.default_limit,
        }
        if integration:
            params["integration"] = integration

        result = self._make_request("POST", "/api/v1/graph/nodes/search/text", params=params, body=body)
        return json.dumps(result, indent=2)

    def execute_query(
        self,
        query: str,
    ) -> str:
        """
        Execute a custom Cypher query (read-only).

        The query will be automatically scoped to your organization's data.
        All node patterns will have the organization label injected.

        Args:
            query: Cypher query to execute (read-only)

        Returns:
            JSON string with query results

        Example:
            execute_query(query="MATCH (u:User)-[:OWNS]->(r:Repository) RETURN u.name, r.name LIMIT 10")
        """
        body = {"query": query}

        result = self._make_request("POST", "/api/v1/graph/query", body=body)
        return json.dumps(result, indent=2)

    def get_labels(
        self,
        integration: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> str:
        """
        Get all node labels in the context graph.

        Args:
            integration: Optional integration name to filter by
            skip: Number of results to skip
            limit: Maximum number of results to return

        Returns:
            JSON string with available labels

        Example:
            get_labels()
            get_labels(integration="github")
        """
        params = {
            "skip": skip,
            "limit": limit or self.default_limit,
        }
        if integration:
            params["integration"] = integration

        result = self._make_request("GET", "/api/v1/graph/labels", params=params)
        return json.dumps(result, indent=2)

    def get_relationship_types(
        self,
        integration: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> str:
        """
        Get all relationship types in the context graph.

        Args:
            integration: Optional integration name to filter by
            skip: Number of results to skip
            limit: Maximum number of results to return

        Returns:
            JSON string with available relationship types

        Example:
            get_relationship_types()
            get_relationship_types(integration="github")
        """
        params = {
            "skip": skip,
            "limit": limit or self.default_limit,
        }
        if integration:
            params["integration"] = integration

        result = self._make_request("GET", "/api/v1/graph/relationship-types", params=params)
        return json.dumps(result, indent=2)

    def _get_or_create_dataset(self) -> str:
        """
        Get or create dataset ID for memory operations (cached).

        Returns:
            Dataset ID (UUID string)
        """
        if self._dataset_id:
            return self._dataset_id

        try:
            # List datasets
            response = self._make_request("GET", "/api/v1/datasets")

            if isinstance(response, list):
                for ds in response:
                    if ds.get("name") == self.dataset_name:
                        self._dataset_id = ds["id"]
                        logger.info(f"Found dataset: {self.dataset_name} ({self._dataset_id})")
                        return self._dataset_id

            # Create dataset if not found
            create_body = {
                "name": self.dataset_name,
                "description": f"Memory dataset for {self.dataset_name}",
                "scope": "org",
            }
            result = self._make_request("POST", "/api/v1/datasets", body=create_body)
            self._dataset_id = result.get("id")
            logger.info(f"Created dataset: {self.dataset_name} ({self._dataset_id})")
            return self._dataset_id

        except Exception as e:
            logger.error(f"Failed to get/create dataset: {e}")
            raise

    def store_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store information in persistent memory for later recall.

        Use this to remember important information across conversations like:
        - User preferences and context
        - Task progress and decisions
        - System configurations and credentials
        - Important facts and observations

        Args:
            content: Information to remember (clear, descriptive text)
            metadata: Optional metadata (e.g., {"category": "user_preference", "priority": "high"})

        Returns:
            Success message with memory ID

        Example:
            store_memory("User prefers Python over JavaScript for scripting tasks")
            store_memory("Production database is read-only on weekends", metadata={"category": "policy"})
        """
        try:
            dataset_id = self._get_or_create_dataset()

            # API expects dataset_id and context in body, metadata optional in body
            body = {
                "dataset_id": dataset_id,
                "context": {"content": content},
                "metadata": metadata or {},
            }

            result = self._make_request("POST", "/api/v1/graph/memory/store", body=body)
            memory_id = result.get("memory_id", "unknown")
            return f"✓ Memory stored successfully (ID: {memory_id})"

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return f"Error storing memory: {str(e)}"

    def recall_memory(
        self,
        query: str,
        limit: int = 5,
        search_type: str = "GRAPH_COMPLETION",
    ) -> str:
        """
        Search and retrieve previously stored memories using semantic search.

        Use this to recall information from past conversations or stored context.
        The search is semantic (vector similarity), so use natural language queries.

        Args:
            query: What you want to remember (natural language query)
            limit: Maximum number of memories to return (default: 5, max: 100)
            search_type: Search strategy (default: "GRAPH_COMPLETION")
                - "GRAPH_COMPLETION": Best for general recall (default, recommended)
                - "CHUNKS": Raw text chunks without graph context
                - "RAG_COMPLETION": Retrieval-augmented generation format
                - "TEMPORAL": Time-based recall (if available)
                - "FEEDBACK": Feedback-enhanced results (if available)

        Returns:
            Formatted list of relevant memories with metadata and relevance scores

        Example:
            recall_memory("What are the user's preferences?")
            recall_memory("production database policies", limit=10)
            recall_memory("recent kubernetes issues", search_type="TEMPORAL")
        """
        try:
            # Validate search_type
            valid_types = ["GRAPH_COMPLETION", "CHUNKS", "RAG_COMPLETION", "TEMPORAL", "FEEDBACK"]
            if search_type and search_type not in valid_types:
                logger.warning(f"Invalid search_type '{search_type}', using GRAPH_COMPLETION")
                search_type = "GRAPH_COMPLETION"

            # Use semantic search endpoint (/api/v1/graph/search) which searches across all accessible memories
            # This performs vector similarity search with optional graph context
            body = {
                "query": query,
                "limit": min(max(limit, 1), 100),  # Clamp between 1 and 100
                "search_type": search_type,
            }

            result = self._make_request("POST", "/api/v1/graph/search", body=body)

            # API returns {query: str, results: list, count: int}
            results = result.get("results", [])

            if not results or len(results) == 0:
                return f"No memories found for query: '{query}'\n\nTry:\n- Using more specific keywords\n- Asking in a different way\n- Checking if memories were stored in this dataset"

            # Format results with proper structure
            formatted = f"Found {len(results)} relevant memories for '{query}':\n\n"

            for i, item in enumerate(results, 1):
                # Extract content from various possible structures
                if isinstance(item, dict):
                    content = (
                        item.get('text') or
                        item.get('content') or
                        item.get('chunk_text') or
                        (str(item.get('data')) if item.get('data') else None) or
                        'No content available'
                    )
                else:
                    content = str(item)

                # Truncate long content but show full length in metadata
                content_preview = content[:500]
                if len(content) > 500:
                    content_preview += f"... ({len(content)} chars total)"

                formatted += f"{i}. {content_preview}\n"

                # Add relevance score (most important metadata)
                if isinstance(item, dict):
                    score = item.get('score') or item.get('similarity_score')
                    if isinstance(item.get('distance'), (int, float)):
                        # Convert distance to similarity (0 distance = 100% similarity)
                        score = 1.0 - min(item.get('distance'), 1.0)

                    if score is not None:
                        score_pct = score * 100
                        quality = "excellent" if score >= 0.8 else "good" if score >= 0.6 else "moderate"
                        formatted += f"   📊 Relevance: {score_pct:.1f}% ({quality} match)\n"

                    # Add source/type if available
                    source_type = item.get('type') or item.get('node_type')
                    if source_type:
                        formatted += f"   🏷️  Type: {source_type}\n"

                    # Add dataset info if available
                    if item.get('dataset_name'):
                        formatted += f"   📁 Dataset: {item['dataset_name']}\n"

                    # Add timestamp if available
                    if item.get('created_at'):
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                            formatted += f"   📅 Created: {dt.strftime('%Y-%m-%d %H:%M')}\n"
                        except:
                            formatted += f"   📅 Created: {item['created_at']}\n"

                    # Add custom metadata if present (excluding internal fields)
                    if item.get('metadata'):
                        meta = item['metadata']
                        if isinstance(meta, dict):
                            # Filter out internal/empty metadata
                            display_meta = {k: v for k, v in meta.items()
                                          if v and k not in ['_internal', 'embedding', 'vector']}
                            if display_meta:
                                formatted += f"   ℹ️  Metadata: {json.dumps(display_meta)}\n"

                formatted += "\n"

            return formatted

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to recall memory: {error_msg}")

            # Provide helpful error messages
            if "404" in error_msg:
                return f"Memory search endpoint not found. Please check API configuration."
            elif "503" in error_msg:
                return f"Cognitive memory features are not enabled. Contact your administrator."
            elif "401" in error_msg or "403" in error_msg:
                return f"Authentication failed. Check your API key and permissions."
            else:
                return f"Error recalling memory: {error_msg}"

    def ingest_knowledge(
        self,
        text: str,
        dataset_name: Optional[str] = None,
    ) -> str:
        """
        Ingest text/knowledge into a dataset for later semantic search.

        This adds raw text to a dataset which can then be processed with process_dataset()
        to extract entities, relationships, and create embeddings for semantic search.

        Use this to add:
        - Documentation and guides
        - Code snippets and explanations  
        - Meeting notes and decisions
        - Technical specifications
        - Any textual knowledge

        Args:
            text: Text content to ingest (any length - can be multiple paragraphs)
            dataset_name: Target dataset name (optional, uses environment dataset if not specified)

        Returns:
            Success message with dataset info

        Example:
            ingest_knowledge("Kubernetes is a container orchestration platform...")
            ingest_knowledge("Our API uses REST...", dataset_name="api-docs")
        """
        try:
            # Use environment dataset if not specified
            target_dataset = dataset_name or self.dataset_name

            body = {
                "text": text,
                "dataset_name": target_dataset,
            }

            result = self._make_request("POST", "/api/v1/graph/knowledge", body=body)

            status = result.get("status")
            message = result.get("message", "")
            text_length = result.get("text_length", len(text))

            if status == "success":
                return f"✓ Knowledge ingested successfully into dataset '{target_dataset}'\n" \
                       f"   📄 {text_length} characters added\n" \
                       f"   ℹ️  Run process_dataset('{target_dataset}') to make it searchable"
            else:
                return f"⚠️  Knowledge ingestion completed with warnings: {message}"

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to ingest knowledge: {error_msg}")

            if "404" in error_msg:
                return f"Dataset '{dataset_name or self.dataset_name}' not found. Create it first with store_memory()."
            elif "503" in error_msg:
                return "Cognitive features are not enabled. Contact your administrator."
            else:
                return f"Error ingesting knowledge: {error_msg}"

    def process_dataset(
        self,
        dataset_name: Optional[str] = None,
    ) -> str:
        """
        Process a dataset to extract knowledge and create searchable embeddings.

        This transforms raw text added via ingest_knowledge() into a semantic knowledge graph:
        1. Extracts entities and concepts
        2. Identifies relationships
        3. Creates vector embeddings
        4. Makes content searchable via recall_memory()

        **Important**: This operation can take 10-60 seconds depending on dataset size.

        Args:
            dataset_name: Dataset to process (optional, uses environment dataset if not specified)

        Returns:
            Processing status and result info

        Example:
            process_dataset()
            process_dataset("api-docs")
        """
        try:
            # Use environment dataset if not specified
            target_dataset = dataset_name or self.dataset_name

            body = {
                "dataset_name": target_dataset,
            }

            result = self._make_request("POST", "/api/v1/graph/cognify", body=body)

            status = result.get("status")
            message = result.get("message", "")

            if status == "success":
                return f"✓ Dataset '{target_dataset}' processed successfully\n" \
                       f"   📊 Knowledge graph created and embeddings generated\n" \
                       f"   🔍 Content is now searchable with recall_memory()\n" \
                       f"   ℹ️  {message}"
            else:
                return f"⚠️  Processing completed with status: {status}\n" \
                       f"   Message: {message}"

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to process dataset: {error_msg}")

            if "404" in error_msg:
                return f"Dataset '{dataset_name or self.dataset_name}' not found."
            elif "400" in error_msg:
                return f"Dataset '{dataset_name or self.dataset_name}' has no data. Add content with ingest_knowledge() first."
            elif "503" in error_msg:
                return "Cognitive features are not enabled. Contact your administrator."
            else:
                return f"Error processing dataset: {error_msg}"
