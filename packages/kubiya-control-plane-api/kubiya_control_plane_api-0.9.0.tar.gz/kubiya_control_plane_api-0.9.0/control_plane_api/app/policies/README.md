# Policy Modules for Agent Control Plane

This directory contains pre-built OPA (Open Policy Agent) policy modules written in Rego for common agent control plane operations.

## Overview

Policies are stored and evaluated in the OPA Watchdog Enforcer Service. These modules provide templates and examples for:

- **Execution Policies**: Control when and how agents can execute
- **Resource Policies**: Limit resource usage and access
- **Time-based Policies**: Business hours and rate limiting
- **Tool Enforcement Policies**: Real-time validation of tool executions (NEW)
- **Tool Policies**: Control which tools agents can use
- **Team Policies**: Collaboration and approval workflows

### Tool Enforcement Policies (NEW)

The `tool_enforcement/` directory contains policies for **real-time tool call enforcement** during agent execution. These policies are evaluated before each tool execution and can block or allow tools based on:

- User roles and permissions
- Tool risk level (critical/high/medium/low)
- Environment (production/staging/dev)
- Time of day (business hours)
- Tool source (MCP/builtin/skill)
- Command patterns (dangerous bash commands)

See the [Tool Enforcement Guide](../../../docs/TOOL_ENFORCEMENT.md) for detailed documentation.

## Policy Structure

All policies follow this structure:

```rego
package <policy_name>

# Default decision (deny by default)
default allow = false

# Rules that grant permissions
allow {
    # conditions
}

# Violations that explain why requests are denied
violations[msg] {
    # condition
    msg := "Explanation"
}
```

## Policy Priority and Inheritance

Policies are associated with entities (agents, teams, environments) with automatic inheritance:

1. **Environment** policies (priority: 300) - apply to all agents/teams in the environment
2. **Team** policies (priority: 200) - apply to all agents in the team
3. **Agent** policies (priority: 100) - apply to specific agent

When the same policy is defined at multiple levels, **higher priority wins**.

## Usage

### 1. Create a Policy

```bash
curl -X POST https://your-control-plane.com/api/v1/policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "business-hours-only",
    "policy_content": "<rego_policy>",
    "description": "Allow executions only during business hours",
    "enabled": true,
    "tags": ["time", "compliance"]
  }'
```

### 2. Associate with Entity

```bash
curl -X POST https://your-control-plane.com/api/v1/policies/associations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "<policy_uuid>",
    "policy_name": "business-hours-only",
    "entity_type": "environment",
    "entity_id": "<environment_uuid>",
    "enabled": true
  }'
```

### 3. Evaluate Policy

Policies are automatically evaluated during agent execution. You can also test manually:

```bash
curl -X POST https://your-control-plane.com/api/v1/policies/evaluate/agent/<agent_id> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "action": "execute",
      "user": "alice@company.com",
      "time": "2025-01-15T14:30:00Z"
    }
  }'
```

## Available Policy Modules

### Tool Enforcement Policies (`tool_enforcement/`)

Real-time tool call validation policies:

- **`role_based_tool_access.rego`** - Restrict command execution tools to admin/devops roles
- **`production_safeguards.rego`** - Block critical/high-risk tools in production environment
- **`bash_command_validation.rego`** - Block dangerous bash patterns (rm -rf, dd, mkfs, etc.)
- **`business_hours_enforcement.rego`** - Restrict high-risk tools to business hours (9 AM - 6 PM UTC, Mon-Fri)
- **`mcp_tool_allowlist.rego`** - Whitelist approved MCP tools

All tool enforcement policies use package `kubiya.tool_enforcement` and evaluate against structured tool execution input. See [Tool Enforcement Guide](../../../docs/TOOL_ENFORCEMENT.md) for input schema and examples.

### General Policy Modules

See individual `.rego` files for detailed policies:

- `business_hours.rego` - Restrict executions to business hours
- `approved_users.rego` - Require user approval list
- `rate_limiting.rego` - Limit execution frequency
- `resource_limits.rego` - Enforce resource quotas
- `tool_restrictions.rego` - Control tool usage
- `approval_workflow.rego` - Require approvals for sensitive actions
- `environment_restrictions.rego` - Restrict access to environments

## Policy Development Tips

1. **Test policies locally** using OPA CLI before deploying
2. **Start with deny-by-default** for security
3. **Use clear violation messages** for debugging
4. **Document assumptions** in policy comments
5. **Version policies** using tags or metadata
6. **Test edge cases** thoroughly

## References

- [OPA Documentation](https://www.openpolicyagent.org/docs/latest/)
- [Rego Language Reference](https://www.openpolicyagent.org/docs/latest/policy-reference/)
- [OPA Watchdog Enforcer API](https://enforcer-psi.vercel.app/api/docs)
