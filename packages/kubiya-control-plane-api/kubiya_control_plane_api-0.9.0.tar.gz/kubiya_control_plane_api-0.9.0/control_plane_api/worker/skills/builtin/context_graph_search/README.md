# Context Graph Search - Built-in Skill

A built-in skill that provides runtime-level tools for searching and querying the Kubiya Context Graph (Neo4j-based organizational data).

## Overview

This skill is **automatically available** in all runtimes (Agno, Claude Code, etc.) without requiring explicit configuration. It provides a comprehensive set of tools for interacting with your organization's context graph.

## Features

- ✅ **Runtime-agnostic**: Works with all supported runtimes
- ✅ **Auto-enabled**: Always available, no configuration needed
- ✅ **Production-ready**: Uses the official Context Graph API
- ✅ **Comprehensive**: 9 tools covering all graph operations

## Available Tools

### 1. `search_nodes`
Search for nodes by label and/or properties.

**Parameters:**
- `label` (optional): Node label to filter by (e.g., "User", "Repository", "Service")
- `property_name` (optional): Property name to filter by
- `property_value` (optional): Property value to match
- `integration` (optional): Integration name to filter by
- `skip` (optional): Number of results to skip (default: 0)
- `limit` (optional): Maximum results to return (default: 100)

**Example:**
```python
search_nodes(label="User", property_name="email", property_value="user@example.com")
search_nodes(label="Repository", integration="github")
```

### 2. `get_node`
Get a specific node by its ID.

**Parameters:**
- `node_id` (required): The node ID to retrieve
- `integration` (optional): Integration name to filter by

**Example:**
```python
get_node(node_id="abc123")
```

### 3. `get_relationships`
Get relationships for a specific node.

**Parameters:**
- `node_id` (required): The node ID
- `direction` (optional): "incoming", "outgoing", or "both" (default: "both")
- `relationship_type` (optional): Filter by relationship type
- `integration` (optional): Integration name to filter by
- `skip` (optional): Number of results to skip
- `limit` (optional): Maximum results to return

**Example:**
```python
get_relationships(node_id="abc123", direction="outgoing", relationship_type="OWNS")
```

### 4. `get_subgraph`
Get a subgraph starting from a node.

**Parameters:**
- `node_id` (required): Starting node ID
- `depth` (optional): Traversal depth 1-5 (default: 1)
- `relationship_types` (optional): List of relationship types to follow
- `integration` (optional): Integration name to filter by

**Example:**
```python
get_subgraph(node_id="abc123", depth=2, relationship_types=["OWNS", "MANAGES"])
```

### 5. `search_by_text`
Search nodes by text pattern in a property.

**Parameters:**
- `property_name` (required): Property name to search in
- `search_text` (required): Text to search for (supports partial matching)
- `label` (optional): Node label to filter by
- `integration` (optional): Integration name to filter by
- `skip` (optional): Number of results to skip
- `limit` (optional): Maximum results to return

**Example:**
```python
search_by_text(property_name="name", search_text="kubernetes", label="Service")
```

### 6. `execute_query`
Execute a custom Cypher query (read-only).

**Parameters:**
- `query` (required): Cypher query to execute

**Example:**
```python
execute_query(query="MATCH (u:User)-[:OWNS]->(r:Repository) RETURN u.name, r.name LIMIT 10")
```

**Note:** Queries are automatically scoped to your organization's data.

### 7. `get_labels`
Get all node labels in the context graph.

**Parameters:**
- `integration` (optional): Integration name to filter by
- `skip` (optional): Number of results to skip
- `limit` (optional): Maximum results to return

**Example:**
```python
get_labels()
get_labels(integration="github")
```

### 8. `get_relationship_types`
Get all relationship types in the context graph.

**Parameters:**
- `integration` (optional): Integration name to filter by
- `skip` (optional): Number of results to skip
- `limit` (optional): Maximum results to return

**Example:**
```python
get_relationship_types()
```

### 9. `get_stats`
Get statistics about the context graph.

**Parameters:**
- `integration` (optional): Integration name to filter by

**Example:**
```python
get_stats()
get_stats(integration="github")
```

## Environment Variables

- `CONTEXT_GRAPH_API_BASE`: Context Graph API base URL (default: `https://graph.kubiya.ai`)
- `KUBIYA_API_KEY`: Required - Kubiya API key for authentication
- `KUBIYA_ORG_ID`: Optional - Organization ID (usually set automatically)

## Runtime Integration

### Agno Runtime
Tools are available directly as methods on the `ContextGraphSearchTools` instance.

```python
from agno.agent import Agent

agent = Agent(
    # context_graph_search skill is auto-loaded
    tools=[...]
)
```

### Claude Code Runtime
Tools are automatically converted to an MCP server and exposed as:
- `mcp__context-graph-search__search_nodes`
- `mcp__context-graph-search__get_node`
- etc.

## How It Works

1. **Auto-Loading**: The skill is automatically added to all agents by the runtime executors (`agent_executor_v2.py`, `team_executor_v2.py`)

2. **Runtime Discovery**: The `SkillFactory` discovers the skill from the `builtin/context_graph_search/` directory

3. **Runtime Adaptation**:
   - **Agno**: Uses the Toolkit class directly
   - **Claude Code**: Converts Toolkit methods to MCP tools via `create_sdk_mcp_server()`

## Adding More Built-in Tools

To add additional built-in tools that are always available:

1. Create a new skill in `worker/skills/builtin/<skill_name>/`
2. Add the skill type to the `builtin_skill_types` set in:
   - `worker/services/agent_executor_v2.py`
   - `worker/services/team_executor_v2.py`

Example:
```python
builtin_skill_types = {'context_graph_search', 'your_new_skill'}
```

## Development

To test the skill locally:

```python
from control_plane_api.worker.skills.builtin.context_graph_search.agno_impl import ContextGraphSearchTools
import os

os.environ['KUBIYA_API_KEY'] = 'your_api_key'
os.environ['CONTEXT_GRAPH_API_BASE'] = 'https://graph.kubiya.ai'

tools = ContextGraphSearchTools()
result = tools.get_labels()
print(result)
```

## API Documentation

Full Context Graph API documentation: https://graph.kubiya.ai/docs
