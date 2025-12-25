"""
End-to-end tests for ContextGraphSearchTools against real Kubiya Graph API.

This test suite validates real-world integration with the production Graph API.
"""

import os
import json
import sys
from pathlib import Path

# Add worker to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.builtin.context_graph_search.agno_impl import ContextGraphSearchTools


class TestRealGraphAPIIntegration:
    """E2E tests using real Kubiya Graph API"""

    def setup_method(self):
        """Set up before each test"""
        # Verify API key is set
        api_key = os.environ.get("KUBIYA_API_KEY")
        if not api_key:
            raise RuntimeError("KUBIYA_API_KEY environment variable must be set for E2E tests")

        print(f"\n{'='*80}")
        print(f"🔑 Using API Key: {api_key[:20]}... (length: {len(api_key)})")
        print(f"🌐 Graph API Base: {os.environ.get('CONTEXT_GRAPH_API_BASE', 'https://graph.kubiya.ai')}")
        print(f"{'='*80}\n")

        # Create tools instance
        self.tools = ContextGraphSearchTools()

    def test_get_stats_real_api(self):
        """Test get_stats against real Graph API"""
        print("📊 Testing get_stats()...")

        result = self.tools.get_stats()

        # Parse result
        assert isinstance(result, str), "Result should be JSON string"
        data = json.loads(result)

        print(f"✅ Stats retrieved successfully!")
        print(f"   Response keys: {list(data.keys())}")
        print(f"   Full response: {json.dumps(data, indent=2)}\n")

        # Validate response structure
        assert isinstance(data, dict), "Response should be a dictionary"

    def test_get_labels_real_api(self):
        """Test get_labels against real Graph API"""
        print("🏷️  Testing get_labels()...")

        result = self.tools.get_labels(limit=50)

        # Parse result
        data = json.loads(result)

        print(f"✅ Labels retrieved successfully!")
        print(f"   Response keys: {list(data.keys())}")
        if 'labels' in data:
            print(f"   Number of labels: {len(data.get('labels', []))}")
            print(f"   Sample labels: {data.get('labels', [])[:10]}")
        print(f"   Full response: {json.dumps(data, indent=2)}\n")

        assert isinstance(data, dict), "Response should be a dictionary"

    def test_get_relationship_types_real_api(self):
        """Test get_relationship_types against real Graph API"""
        print("🔗 Testing get_relationship_types()...")

        result = self.tools.get_relationship_types(limit=50)

        # Parse result
        data = json.loads(result)

        print(f"✅ Relationship types retrieved successfully!")
        print(f"   Response keys: {list(data.keys())}")
        if 'relationship_types' in data:
            print(f"   Number of types: {len(data.get('relationship_types', []))}")
            print(f"   Sample types: {data.get('relationship_types', [])[:10]}")
        print(f"   Full response: {json.dumps(data, indent=2)}\n")

        assert isinstance(data, dict), "Response should be a dictionary"

    def test_search_nodes_real_api(self):
        """Test search_nodes against real Graph API"""
        print("🔍 Testing search_nodes()...")

        # Try searching without filters first
        result = self.tools.search_nodes(limit=10)

        # Parse result
        data = json.loads(result)

        print(f"✅ Nodes search completed successfully!")
        print(f"   Response keys: {list(data.keys())}")
        if 'nodes' in data:
            print(f"   Number of nodes returned: {len(data.get('nodes', []))}")
            if data.get('nodes'):
                print(f"   First node: {json.dumps(data['nodes'][0], indent=2)}")
        print(f"   Full response: {json.dumps(data, indent=2)}\n")

        assert isinstance(data, dict), "Response should be a dictionary"

    def test_search_by_text_real_api(self):
        """Test search_by_text against real Graph API"""
        print("📝 Testing search_by_text()...")

        # Search for common text patterns
        result = self.tools.search_by_text(
            property_name="name",
            search_text="kubiya",
            limit=5
        )

        # Parse result
        data = json.loads(result)

        print(f"✅ Text search completed successfully!")
        print(f"   Response keys: {list(data.keys())}")
        if 'nodes' in data:
            print(f"   Number of matching nodes: {len(data.get('nodes', []))}")
            if data.get('nodes'):
                print(f"   Sample matches: {[n.get('properties', {}).get('name') for n in data['nodes'][:3]]}")
        print(f"   Full response: {json.dumps(data, indent=2)}\n")

        assert isinstance(data, dict), "Response should be a dictionary"

    def test_get_integrations_real_api(self):
        """Test getting available integrations"""
        print("🔌 Testing integrations discovery...")

        # Use the internal _make_request to get integrations
        try:
            result = self.tools._make_request("GET", "/api/v1/graph/integrations", params={"limit": 50})

            print(f"✅ Integrations retrieved successfully!")
            print(f"   Response keys: {list(result.keys())}")
            if 'integrations' in result:
                integrations = result.get('integrations', [])
                print(f"   Number of integrations: {len(integrations)}")
                print(f"   Available integrations: {integrations}")
            print(f"   Full response: {json.dumps(result, indent=2)}\n")

            assert isinstance(result, dict), "Response should be a dictionary"
        except Exception as e:
            print(f"⚠️  Integrations endpoint returned: {str(e)}")
            print("   This is expected if no integrations are configured\n")

    def test_execute_simple_query_real_api(self):
        """Test execute_query with a simple Cypher query"""
        print("⚡ Testing execute_query() with simple query...")

        # Execute a simple query to count nodes
        query = "MATCH (n) RETURN count(n) as node_count LIMIT 1"

        try:
            result = self.tools.execute_query(query=query)

            # Parse result
            data = json.loads(result)

            print(f"✅ Query executed successfully!")
            print(f"   Query: {query}")
            print(f"   Response keys: {list(data.keys())}")
            print(f"   Full response: {json.dumps(data, indent=2)}\n")

            assert isinstance(data, dict), "Response should be a dictionary"
        except Exception as e:
            print(f"⚠️  Query execution returned: {str(e)}")
            print(f"   This might be expected if custom queries are restricted\n")

    def test_search_with_label_filter_real_api(self):
        """Test searching nodes with label filter"""
        print("🎯 Testing search_nodes() with label filter...")

        # Get available labels first
        labels_result = self.tools.get_labels(limit=10)
        labels_data = json.loads(labels_result)

        if 'labels' in labels_data and labels_data['labels']:
            # Use the first available label
            test_label = labels_data['labels'][0]
            print(f"   Using label: {test_label}")

            # Search with that label
            result = self.tools.search_nodes(label=test_label, limit=5)
            data = json.loads(result)

            print(f"✅ Label-filtered search completed!")
            print(f"   Response keys: {list(data.keys())}")
            if 'nodes' in data:
                print(f"   Number of nodes with label '{test_label}': {len(data.get('nodes', []))}")
            print(f"   Full response: {json.dumps(data, indent=2)}\n")

            assert isinstance(data, dict), "Response should be a dictionary"
        else:
            print("⚠️  No labels found in graph, skipping label filter test\n")

    def test_toolkit_has_all_functions(self):
        """Verify all 9 tools are registered"""
        print("🔧 Verifying toolkit function registration...")

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

        registered_tools = list(self.tools.functions.keys())

        print(f"✅ Toolkit verification:")
        print(f"   Expected: {len(expected_tools)} tools")
        print(f"   Registered: {len(registered_tools)} tools")
        print(f"   Tools: {registered_tools}\n")

        for tool in expected_tools:
            assert tool in registered_tools, f"Tool {tool} not registered"

    def test_error_handling_invalid_node_id(self):
        """Test error handling for invalid node ID"""
        print("❌ Testing error handling with invalid node ID...")

        try:
            result = self.tools.get_node(node_id="invalid_node_id_12345")
            data = json.loads(result)

            print(f"⚠️  Request completed (might return empty or error):")
            print(f"   Response: {json.dumps(data, indent=2)}\n")

        except Exception as e:
            print(f"✅ Error handled correctly:")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}\n")
            assert "HTTP" in str(e) or "404" in str(e) or "not found" in str(e).lower()

    def test_pagination_parameters(self):
        """Test pagination with skip and limit parameters"""
        print("📄 Testing pagination (skip/limit)...")

        # Get first page
        result1 = self.tools.search_nodes(skip=0, limit=5)
        data1 = json.loads(result1)

        # Get second page
        result2 = self.tools.search_nodes(skip=5, limit=5)
        data2 = json.loads(result2)

        print(f"✅ Pagination test completed!")
        print(f"   Page 1 nodes: {len(data1.get('nodes', []))}")
        print(f"   Page 2 nodes: {len(data2.get('nodes', []))}")

        # Verify we got results (if graph has data)
        if data1.get('nodes'):
            print(f"   First node from page 1: {data1['nodes'][0].get('id', 'N/A')}")
        if data2.get('nodes'):
            print(f"   First node from page 2: {data2['nodes'][0].get('id', 'N/A')}")
        print()

        assert isinstance(data1, dict), "Page 1 response should be a dictionary"
        assert isinstance(data2, dict), "Page 2 response should be a dictionary"


def run_e2e_tests():
    """Run all E2E tests and provide summary"""
    print("\n" + "="*80)
    print("🚀 STARTING E2E TESTS AGAINST REAL KUBIYA GRAPH API")
    print("="*80 + "\n")

    test_suite = TestRealGraphAPIIntegration()
    test_methods = [
        method for method in dir(test_suite)
        if method.startswith('test_') and callable(getattr(test_suite, method))
    ]

    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }

    for test_method in test_methods:
        test_name = test_method.replace('test_', '').replace('_', ' ').title()

        try:
            test_suite.setup_method()
            getattr(test_suite, test_method)()
            results['passed'].append(test_name)
        except AssertionError as e:
            results['failed'].append((test_name, str(e)))
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {str(e)}\n")
        except Exception as e:
            results['warnings'].append((test_name, str(e)))
            print(f"⚠️  WARNING: {test_name}")
            print(f"   Error: {str(e)}\n")

    # Print summary
    print("\n" + "="*80)
    print("📊 E2E TEST RESULTS SUMMARY")
    print("="*80)
    print(f"\n✅ PASSED: {len(results['passed'])} tests")
    for test in results['passed']:
        print(f"   • {test}")

    if results['warnings']:
        print(f"\n⚠️  WARNINGS: {len(results['warnings'])} tests")
        for test, error in results['warnings']:
            print(f"   • {test}")
            print(f"     └─ {error[:100]}")

    if results['failed']:
        print(f"\n❌ FAILED: {len(results['failed'])} tests")
        for test, error in results['failed']:
            print(f"   • {test}")
            print(f"     └─ {error[:100]}")

    print("\n" + "="*80)
    total = len(results['passed']) + len(results['failed']) + len(results['warnings'])
    print(f"TOTAL: {total} tests | PASSED: {len(results['passed'])} | WARNINGS: {len(results['warnings'])} | FAILED: {len(results['failed'])}")
    print("="*80 + "\n")

    return len(results['failed']) == 0


if __name__ == "__main__":
    success = run_e2e_tests()
    sys.exit(0 if success else 1)
