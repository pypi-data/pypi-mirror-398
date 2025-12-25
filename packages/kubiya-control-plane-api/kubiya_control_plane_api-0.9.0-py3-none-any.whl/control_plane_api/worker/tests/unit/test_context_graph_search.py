"""Unit tests for ContextGraphSearchTools built-in skill."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import httpx

# Add worker to sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.builtin.context_graph_search.agno_impl import ContextGraphSearchTools


class TestContextGraphSearchTools:
    """Test suite for ContextGraphSearchTools class"""

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set up environment variables for testing"""
        monkeypatch.setenv("KUBIYA_API_KEY", "test_api_key_123")
        monkeypatch.setenv("CONTEXT_GRAPH_API_BASE", "https://test-graph.kubiya.ai")
        monkeypatch.setenv("KUBIYA_ORG_ID", "test_org_123")

    @pytest.fixture
    def tools(self, mock_env_vars):
        """Create a ContextGraphSearchTools instance for testing"""
        return ContextGraphSearchTools()

    @pytest.fixture
    def mock_httpx_response(self):
        """Create a mock httpx response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nodes": [
                {"id": "node1", "label": "User", "properties": {"name": "Alice"}},
                {"id": "node2", "label": "User", "properties": {"name": "Bob"}}
            ],
            "count": 2
        }
        return mock_response

    def test_initialization(self, tools):
        """Test that tools initialize correctly with environment variables"""
        assert tools.api_base == "https://test-graph.kubiya.ai"
        assert tools.api_key == "test_api_key_123"
        assert tools.org_id == "test_org_123"
        assert tools.headers["Authorization"] == "UserKey test_api_key_123"
        assert tools.headers["X-Organization-ID"] == "test_org_123"

    def test_initialization_with_custom_config(self, mock_env_vars):
        """Test initialization with custom configuration"""
        tools = ContextGraphSearchTools(
            api_base="https://custom-graph.api",
            timeout=60,
            default_limit=50
        )
        assert tools.api_base == "https://custom-graph.api"
        assert tools.timeout == 60
        assert tools.default_limit == 50

    def test_initialization_strips_trailing_slash(self, mock_env_vars):
        """Test that trailing slashes are removed from api_base"""
        tools = ContextGraphSearchTools(api_base="https://test-graph.kubiya.ai/")
        assert tools.api_base == "https://test-graph.kubiya.ai"

    def test_initialization_without_api_key(self, monkeypatch):
        """Test initialization without API key logs warning"""
        monkeypatch.delenv("KUBIYA_API_KEY", raising=False)
        tools = ContextGraphSearchTools()
        assert tools.api_key is None

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_make_request_get_success(self, mock_client_class, tools, mock_httpx_response):
        """Test successful GET request"""
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        result = tools._make_request("GET", "/api/v1/graph/nodes", params={"limit": 10})

        assert result == mock_httpx_response.json()
        mock_client.__enter__.return_value.get.assert_called_once()

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_make_request_post_success(self, mock_client_class, tools, mock_httpx_response):
        """Test successful POST request"""
        mock_client = MagicMock()
        mock_client.__enter__.return_value.post.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        body = {"label": "User"}
        result = tools._make_request("POST", "/api/v1/graph/nodes/search", body=body)

        assert result == mock_httpx_response.json()
        mock_client.__enter__.return_value.post.assert_called_once()

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_make_request_timeout(self, mock_client_class, tools):
        """Test request timeout handling"""
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client_class.return_value = mock_client

        with pytest.raises(Exception, match="Request timed out"):
            tools._make_request("GET", "/api/v1/graph/nodes")

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_make_request_http_error(self, mock_client_class, tools):
        """Test HTTP error handling"""
        mock_client = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.__enter__.return_value.get.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )
        mock_client_class.return_value = mock_client

        with pytest.raises(Exception, match="HTTP 500"):
            tools._make_request("GET", "/api/v1/graph/nodes")

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_search_nodes(self, mock_client_class, tools, mock_httpx_response):
        """Test search_nodes method"""
        mock_client = MagicMock()
        mock_client.__enter__.return_value.post.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        result = tools.search_nodes(
            label="User",
            property_name="email",
            property_value="test@example.com"
        )

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "nodes" in parsed
        assert len(parsed["nodes"]) == 2

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_search_nodes_with_integration(self, mock_client_class, tools, mock_httpx_response):
        """Test search_nodes with integration filter"""
        mock_client = MagicMock()
        mock_client.__enter__.return_value.post.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        result = tools.search_nodes(label="Repository", integration="github")

        assert isinstance(result, str)
        # Verify the params included integration
        call_args = mock_client.__enter__.return_value.post.call_args
        assert call_args[1]["params"]["integration"] == "github"

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_get_node(self, mock_client_class, tools):
        """Test get_node method"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "node123",
            "label": "User",
            "properties": {"name": "Alice", "email": "alice@example.com"}
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = tools.get_node(node_id="node123")

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["id"] == "node123"
        assert parsed["label"] == "User"

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_get_relationships(self, mock_client_class, tools):
        """Test get_relationships method"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "relationships": [
                {"type": "OWNS", "target": "repo1"},
                {"type": "MANAGES", "target": "team1"}
            ]
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = tools.get_relationships(
            node_id="node123",
            direction="outgoing",
            relationship_type="OWNS"
        )

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "relationships" in parsed

        # Verify the params
        call_args = mock_client.__enter__.return_value.get.call_args
        assert call_args[1]["params"]["direction"] == "outgoing"
        assert call_args[1]["params"]["relationship_type"] == "OWNS"

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_get_subgraph(self, mock_client_class, tools):
        """Test get_subgraph method"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nodes": [{"id": "node1"}, {"id": "node2"}],
            "relationships": [{"type": "OWNS", "source": "node1", "target": "node2"}]
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = tools.get_subgraph(
            node_id="node123",
            depth=2,
            relationship_types=["OWNS", "MANAGES"]
        )

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "nodes" in parsed
        assert "relationships" in parsed

        # Verify the body (httpx uses 'json' param for POST body)
        call_args = mock_client.__enter__.return_value.post.call_args
        assert call_args[1]["json"]["node_id"] == "node123"
        assert call_args[1]["json"]["depth"] == 2
        assert call_args[1]["json"]["relationship_types"] == ["OWNS", "MANAGES"]

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_get_subgraph_depth_clamping(self, mock_client_class, tools):
        """Test that depth is clamped between 1 and 5"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"nodes": [], "relationships": []}

        mock_client = MagicMock()
        mock_client.__enter__.return_value.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Test depth > 5
        tools.get_subgraph(node_id="node123", depth=10)
        call_args = mock_client.__enter__.return_value.post.call_args
        assert call_args[1]["json"]["depth"] == 5

        # Test depth < 1
        tools.get_subgraph(node_id="node123", depth=0)
        call_args = mock_client.__enter__.return_value.post.call_args
        assert call_args[1]["json"]["depth"] == 1

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_search_by_text(self, mock_client_class, tools, mock_httpx_response):
        """Test search_by_text method"""
        mock_client = MagicMock()
        mock_client.__enter__.return_value.post.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        result = tools.search_by_text(
            property_name="name",
            search_text="kubernetes",
            label="Service"
        )

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "nodes" in parsed

        # Verify the body (httpx uses 'json' param for POST body)
        call_args = mock_client.__enter__.return_value.post.call_args
        assert call_args[1]["json"]["property_name"] == "name"
        assert call_args[1]["json"]["search_text"] == "kubernetes"
        assert call_args[1]["json"]["label"] == "Service"

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_execute_query(self, mock_client_class, tools):
        """Test execute_query method"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"u.name": "Alice", "r.name": "repo1"},
                {"u.name": "Bob", "r.name": "repo2"}
            ]
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        query = "MATCH (u:User)-[:OWNS]->(r:Repository) RETURN u.name, r.name"
        result = tools.execute_query(query=query)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "results" in parsed

        # Verify the body (httpx uses 'json' param for POST body)
        call_args = mock_client.__enter__.return_value.post.call_args
        assert call_args[1]["json"]["query"] == query

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_get_labels(self, mock_client_class, tools):
        """Test get_labels method"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "labels": ["User", "Repository", "Service", "Team"]
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = tools.get_labels()

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "labels" in parsed
        assert len(parsed["labels"]) == 4

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_get_relationship_types(self, mock_client_class, tools):
        """Test get_relationship_types method"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "relationship_types": ["OWNS", "MANAGES", "MEMBER_OF"]
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = tools.get_relationship_types()

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "relationship_types" in parsed

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_get_stats(self, mock_client_class, tools):
        """Test get_stats method"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "node_count": 1250,
            "relationship_count": 3450,
            "labels": {"User": 100, "Repository": 500}
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = tools.get_stats()

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["node_count"] == 1250
        assert parsed["relationship_count"] == 3450

    def test_toolkit_functions_registered(self, tools):
        """Test that all methods are registered as toolkit functions"""
        # Check that the toolkit has functions registered
        assert hasattr(tools, "functions")
        assert isinstance(tools.functions, dict)

        # Check for expected tool names
        expected_tools = [
            "search_nodes",
            "get_node",
            "get_relationships",
            "get_subgraph",
            "search_by_text",
            "execute_query",
            "get_labels",
            "get_relationship_types",
            "get_stats"
        ]

        for tool_name in expected_tools:
            assert tool_name in tools.functions, f"Tool {tool_name} not registered"

    def test_default_limit_parameter(self, tools):
        """Test that default_limit is used when limit is not specified"""
        assert tools.default_limit == 100

        # Create tools with custom default
        custom_tools = ContextGraphSearchTools(default_limit=50)
        assert custom_tools.default_limit == 50

    @patch('skills.builtin.context_graph_search.agno_impl.httpx.Client')
    def test_all_tools_return_json_string(self, mock_client_class, tools):
        """Test that all tool methods return JSON strings"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client.__enter__.return_value.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Test each method returns JSON string
        result = tools.search_nodes(label="Test")
        assert isinstance(result, str)
        json.loads(result)  # Should not raise

        result = tools.get_node(node_id="test")
        assert isinstance(result, str)
        json.loads(result)

        result = tools.get_relationships(node_id="test")
        assert isinstance(result, str)
        json.loads(result)

        result = tools.get_subgraph(node_id="test")
        assert isinstance(result, str)
        json.loads(result)

        result = tools.search_by_text(property_name="name", search_text="test")
        assert isinstance(result, str)
        json.loads(result)

        result = tools.execute_query(query="MATCH (n) RETURN n")
        assert isinstance(result, str)
        json.loads(result)

        result = tools.get_labels()
        assert isinstance(result, str)
        json.loads(result)

        result = tools.get_relationship_types()
        assert isinstance(result, str)
        json.loads(result)

        result = tools.get_stats()
        assert isinstance(result, str)
        json.loads(result)
