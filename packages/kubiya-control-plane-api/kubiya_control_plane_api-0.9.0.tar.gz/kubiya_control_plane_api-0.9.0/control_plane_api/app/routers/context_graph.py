"""
Context Graph Router - Proxy to Context Graph API

This router provides access to the Context Graph API (Neo4j-based context graphs)
with org and integration namespaces. All endpoints are proxied with authentication.
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from typing import Optional, Dict, Any
import structlog

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/context-graph", tags=["context-graph"])


async def proxy_graph_request(
    request: Request,
    path: str,
    method: str = "GET",
    query_params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    organization: dict = None,
) -> Response:
    """
    Generic proxy function for Context Graph API requests.

    Args:
        request: FastAPI request object
        path: Path to proxy (e.g., "/api/v1/graph/nodes")
        method: HTTP method
        query_params: Query parameters
        body: Request body (for POST requests)
        organization: Organization context

    Returns:
        FastAPI Response with proxied content
    """
    try:
        token = request.state.kubiya_token
        auth_type = getattr(request.state, "kubiya_auth_type", "Bearer")
        org_id = organization["id"] if organization else None

        # Prepare headers for Context Graph API
        headers = {
            "Authorization": f"{auth_type} {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Kubiya-Client": "agent-control-plane",
        }

        if org_id:
            headers["X-Organization-ID"] = org_id

        # Forward Accept-Encoding header to disable gzip if requested by client
        if "accept-encoding" in request.headers:
            headers["Accept-Encoding"] = request.headers["accept-encoding"]

        # Build full URL
        base_url = settings.context_graph_api_base.rstrip("/")
        full_url = f"{base_url}{path}"

        # Make request to Context Graph API
        async with httpx.AsyncClient(timeout=settings.context_graph_api_timeout) as client:
            if method == "GET":
                response = await client.get(full_url, headers=headers, params=query_params)
            elif method == "POST":
                response = await client.post(full_url, headers=headers, params=query_params, json=body)
            elif method == "PUT":
                response = await client.put(full_url, headers=headers, params=query_params, json=body)
            elif method == "DELETE":
                response = await client.delete(full_url, headers=headers, params=query_params)
            else:
                raise HTTPException(status_code=405, detail=f"Method {method} not allowed")

            logger.info(
                "context_graph_request",
                org_id=org_id,
                path=path,
                method=method,
                status=response.status_code,
            )

            # Clean response headers - remove compression headers since we handle encoding
            response_headers = dict(response.headers)
            # Remove headers that might cause decompression issues
            response_headers.pop("content-encoding", None)
            response_headers.pop("content-length", None)  # Will be recalculated

            # Return response with original status code
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type", "application/json"),
            )

    except httpx.TimeoutException:
        logger.error("context_graph_timeout", path=path, method=method)
        raise HTTPException(status_code=504, detail="Context Graph API request timed out")
    except httpx.RequestError as e:
        logger.error("context_graph_request_error", error=str(e), path=path)
        raise HTTPException(status_code=502, detail=f"Failed to connect to Context Graph API: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("context_graph_unexpected_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def health_check(
    request: Request,
    organization: dict = Depends(get_current_organization),
):
    """Health check endpoint for Context Graph API."""
    return await proxy_graph_request(
        request=request,
        path="/health",
        method="GET",
        organization=organization,
    )


@router.post("/api/v1/graph/nodes/search")
async def search_nodes(
    request: Request,
    body: Dict[str, Any],
    integration: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    organization: dict = Depends(get_current_organization),
):
    """
    Search for nodes in the context graph.

    Body should contain NodeSearchRequest:
    - label: Optional node label to filter by
    - property_name: Optional property name to filter by
    - property_value: Optional property value to match
    """
    query_params = {"skip": skip, "limit": limit}
    if integration:
        query_params["integration"] = integration

    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/nodes/search",
        method="POST",
        query_params=query_params,
        body=body,
        organization=organization,
    )


@router.get("/api/v1/graph/nodes/{node_id}")
async def get_node(
    node_id: str,
    request: Request,
    integration: Optional[str] = None,
    organization: dict = Depends(get_current_organization),
):
    """Get a specific node by its ID."""
    query_params = {}
    if integration:
        query_params["integration"] = integration

    return await proxy_graph_request(
        request=request,
        path=f"/api/v1/graph/nodes/{node_id}",
        method="GET",
        query_params=query_params,
        organization=organization,
    )


@router.get("/api/v1/graph/nodes/{node_id}/relationships")
async def get_relationships(
    node_id: str,
    request: Request,
    direction: str = "both",
    relationship_type: Optional[str] = None,
    integration: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    organization: dict = Depends(get_current_organization),
):
    """Get relationships for a specific node."""
    query_params = {
        "direction": direction,
        "skip": skip,
        "limit": limit,
    }
    if relationship_type:
        query_params["relationship_type"] = relationship_type
    if integration:
        query_params["integration"] = integration

    return await proxy_graph_request(
        request=request,
        path=f"/api/v1/graph/nodes/{node_id}/relationships",
        method="GET",
        query_params=query_params,
        organization=organization,
    )


@router.post("/api/v1/graph/subgraph")
async def get_subgraph(
    request: Request,
    body: Dict[str, Any],
    integration: Optional[str] = None,
    organization: dict = Depends(get_current_organization),
):
    """
    Get a subgraph starting from a node.

    Body should contain SubgraphRequest:
    - node_id: Starting node ID
    - depth: Traversal depth (1-5)
    - relationship_types: Optional list of relationship types to follow
    """
    query_params = {}
    if integration:
        query_params["integration"] = integration

    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/subgraph",
        method="POST",
        query_params=query_params,
        body=body,
        organization=organization,
    )


@router.post("/api/v1/graph/nodes/search/text")
async def search_by_text(
    request: Request,
    body: Dict[str, Any],
    integration: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    organization: dict = Depends(get_current_organization),
):
    """
    Search nodes by text pattern in a property.

    Body should contain TextSearchRequest:
    - property_name: Property name to search in
    - search_text: Text to search for
    - label: Optional node label to filter by
    """
    query_params = {"skip": skip, "limit": limit}
    if integration:
        query_params["integration"] = integration

    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/nodes/search/text",
        method="POST",
        query_params=query_params,
        body=body,
        organization=organization,
    )


@router.get("/api/v1/graph/nodes")
async def get_all_nodes(
    request: Request,
    integration: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    organization: dict = Depends(get_current_organization),
):
    """
    Get all nodes in the organization.

    Optionally filter by integration label to get nodes from a specific integration.
    """
    query_params = {"skip": skip, "limit": limit}
    if integration:
        query_params["integration"] = integration

    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/nodes",
        method="GET",
        query_params=query_params,
        organization=organization,
    )


@router.get("/api/v1/graph/labels")
async def get_labels(
    request: Request,
    integration: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    organization: dict = Depends(get_current_organization),
):
    """Get all node labels in the context graph."""
    query_params = {"skip": skip, "limit": limit}
    if integration:
        query_params["integration"] = integration

    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/labels",
        method="GET",
        query_params=query_params,
        organization=organization,
    )


@router.get("/api/v1/graph/relationship-types")
async def get_relationship_types(
    request: Request,
    integration: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    organization: dict = Depends(get_current_organization),
):
    """Get all relationship types in the context graph."""
    query_params = {"skip": skip, "limit": limit}
    if integration:
        query_params["integration"] = integration

    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/relationship-types",
        method="GET",
        query_params=query_params,
        organization=organization,
    )


@router.get("/api/v1/graph/stats")
async def get_stats(
    request: Request,
    integration: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    organization: dict = Depends(get_current_organization),
):
    """Get statistics about the context graph."""
    query_params = {"skip": skip, "limit": limit}
    if integration:
        query_params["integration"] = integration

    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/stats",
        method="GET",
        query_params=query_params,
        organization=organization,
    )


@router.post("/api/v1/graph/query")
async def execute_query(
    request: Request,
    body: Dict[str, Any],
    organization: dict = Depends(get_current_organization),
):
    """
    Execute a custom Cypher query (read-only).

    The query will be automatically scoped to your organization's data.
    All node patterns will have the organization label injected.

    Body should contain CustomQueryRequest:
    - query: Cypher query to execute (read-only)
    """
    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/query",
        method="POST",
        body=body,
        organization=organization,
    )


@router.get("/api/v1/graph/integrations")
async def get_integrations(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    organization: dict = Depends(get_current_organization),
):
    """Get all available integrations for the organization."""
    query_params = {"skip": skip, "limit": limit}

    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/integrations",
        method="GET",
        query_params=query_params,
        organization=organization,
    )


# ============================================================================
# Semantic Search Endpoint
# ============================================================================


@router.post("/graph/search")
async def semantic_search(
    request: Request,
    body: Dict[str, Any],
    organization: dict = Depends(get_current_organization),
):
    """
    Semantic search across knowledge graph.

    Performs vector similarity search over processed knowledge to find
    relevant information based on natural language queries.

    Body should contain:
    - query: Natural language question or keywords (required)
    - limit: Maximum results (1-100, default 10)
    - filters: Optional filters (dataset_ids, etc.)
    - search_type: Search strategy (GRAPH_COMPLETION, CHUNKS, RAG_COMPLETION, TEMPORAL, FEEDBACK)
    """
    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/search",
        method="POST",
        body=body,
        organization=organization,
    )


# ============================================================================
# Intelligent Search Endpoints
# ============================================================================


@router.post("/intelligent-search")
async def intelligent_search(
    request: Request,
    body: Dict[str, Any],
    organization: dict = Depends(get_current_organization),
):
    """
    Perform AI-powered intelligent graph search using natural language.

    Body should contain IntelligentSearchRequest:
    - keywords: Natural language query (required)
    - max_turns: Maximum agent turns (1-20, default: 5)
    - system_prompt: Optional system prompt
    - additional_context: Optional additional context
    - model: LiteLLM model name (default: kubiya/claude-sonnet-4)
    - temperature: Model temperature (0.0-2.0, default: 0.7)
    - integration: Filter by integration
    - label_filter: Filter by node label
    - enable_semantic_search: Enable semantic search
    - enable_cypher_queries: Enable custom Cypher queries
    - strategy: Agent strategy (claude_sdk or agno)
    - session_id: Session ID for multi-turn conversations
    """
    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/intelligent-search",
        method="POST",
        body=body,
        organization=organization,
    )


@router.post("/intelligent-search/stream")
async def intelligent_search_stream(
    request: Request,
    body: Dict[str, Any],
    organization: dict = Depends(get_current_organization),
):
    """
    Perform streaming AI-powered intelligent graph search with real-time updates.

    Returns Server-Sent Events (SSE) stream with:
    - session: Session ID
    - progress: Progress updates with percentage
    - tool_call: Tool invocations
    - partial_answer: Incremental answer text
    - complete: Final results
    - error: Error messages
    """
    # For streaming, we need to handle SSE differently
    # Use the proxy but preserve streaming response
    try:
        token = request.state.kubiya_token
        auth_type = getattr(request.state, "kubiya_auth_type", "Bearer")
        org_id = organization["id"] if organization else None

        headers = {
            "Authorization": f"{auth_type} {token}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            "X-Kubiya-Client": "agent-control-plane",
        }

        if org_id:
            headers["X-Organization-ID"] = org_id

        base_url = settings.context_graph_api_base.rstrip("/")
        full_url = f"{base_url}/api/v1/graph/intelligent-search/stream"

        async with httpx.AsyncClient(timeout=settings.context_graph_api_timeout) as client:
            response = await client.post(full_url, headers=headers, json=body)

            logger.info(
                "context_graph_streaming_request",
                org_id=org_id,
                path="/api/v1/graph/intelligent-search/stream",
                status=response.status_code,
            )

            # Return streaming response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="text/event-stream",
            )

    except httpx.TimeoutException:
        logger.error("context_graph_stream_timeout")
        raise HTTPException(status_code=504, detail="Streaming search timed out")
    except httpx.RequestError as e:
        logger.error("context_graph_stream_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to connect: {str(e)}")
    except Exception as e:
        logger.error("context_graph_stream_unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/intelligent-search/health")
async def intelligent_search_health(
    request: Request,
    organization: dict = Depends(get_current_organization),
):
    """
    Check health status of intelligent search service.

    Returns:
    - status: "healthy", "degraded", or "unhealthy"
    - strategies: Available agent strategies
    - configuration: Service configuration
    - message: Status message
    """
    return await proxy_graph_request(
        request=request,
        path="/api/v1/graph/intelligent-search/health",
        method="GET",
        organization=organization,
    )
