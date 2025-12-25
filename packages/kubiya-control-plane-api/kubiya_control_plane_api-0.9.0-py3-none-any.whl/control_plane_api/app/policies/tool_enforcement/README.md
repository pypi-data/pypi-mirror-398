# Tool Enforcement Policies

This directory contains OPA policies for **real-time tool call enforcement** during agent execution. These policies validate tool executions before they happen and can inject violation messages into tool outputs (non-blocking).

## Overview

All policies in this directory use the package `kubiya.tool_enforcement` and evaluate against a structured input that includes:

- Tool information (name, arguments, source, category, risk level)
- User context (email, ID, roles)
- Organization and team context
- Execution environment (production/staging/dev)
- Timestamp

## Input Schema

Policies receive this input structure:

```json
{
  "action": "tool_execution",
  "tool": {
    "name": "Bash",
    "arguments": {"command": "ls -la"},
    "source": "builtin",
    "category": "command_execution",
    "risk_level": "high"
  },
  "user": {
    "email": "alice@company.com",
    "id": "user-123",
    "roles": ["developer"]
  },
  "organization": {
    "id": "org-456"
  },
  "team": {
    "id": "team-789",
    "name": "Platform Team"
  },
  "execution": {
    "agent_id": "agent-abc",
    "execution_id": "exec-def",
    "environment": "production",
    "timestamp": "2025-01-15T14:30:00Z"
  }
}
```

## Available Policies

### 1. Role-Based Tool Access (`role_based_tool_access.rego`)

**Purpose**: Restrict command execution tools to admin/devops roles

**Rules**:
- Allows command execution tools only for users with `admin` or `devops` roles
- All other users can use non-command-execution tools
- Admins can use any tool

**Example Violation**:
```
Tool execution blocked by policy enforcement.

Tool: Bash
Blocked by policies: role_based_tool_access

Only admin and devops roles can execute command tools.
Contact your team lead to request elevated permissions.
```

### 2. Production Safeguards (`production_safeguards.rego`)

**Purpose**: Block critical/high-risk tools in production environment

**Rules**:
- Denies critical-risk tools in production environment
- Denies high-risk tools in production environment
- Allows all tools in dev/staging environments
- Admins can bypass restrictions

**Example Violation**:
```
Tool execution blocked by policy enforcement.

Tool: Bash
Blocked by policies: production_safeguards

Critical and high-risk tools are restricted in production.
Use dev or staging environments for testing, or request admin approval.
```

### 3. Bash Command Validation (`bash_command_validation.rego`)

**Purpose**: Block dangerous bash command patterns

**Rules**:
- Denies commands containing `rm -rf /`
- Denies commands containing `dd if=/dev/zero`
- Denies commands containing `mkfs`
- Denies fork bombs `:(){ :|:& };:`
- Denies commands writing to `/dev/sda*` or `/dev/nvme*`
- Admins can bypass restrictions

**Example Violation**:
```
Tool execution blocked by policy enforcement.

Tool: Bash
Blocked by policies: bash_command_validation

This bash command contains dangerous patterns that can cause system damage.
Blocked pattern: rm -rf /
Contact security team if you need to run this command.
```

### 4. Business Hours Enforcement (`business_hours_enforcement.rego`)

**Purpose**: Restrict high-risk tools to business hours

**Rules**:
- Denies high-risk tools outside business hours (9 AM - 6 PM UTC)
- Denies critical-risk tools outside business hours
- Only enforced Monday-Friday
- Allows low/medium-risk tools anytime
- Admins can bypass restrictions

**Example Violation**:
```
Tool execution blocked by policy enforcement.

Tool: Bash
Blocked by policies: business_hours_enforcement

High-risk tools are restricted to business hours (9 AM - 6 PM UTC, Monday-Friday).
Contact admin for urgent requests outside business hours.
```

### 5. MCP Tool Allowlist (`mcp_tool_allowlist.rego`)

**Purpose**: Whitelist approved MCP tools

**Rules**:
- Only allows MCP tools in the approved list
- Approved tools include common integrations: GitHub, Slack, Jira, AWS
- All non-MCP tools are allowed (governed by other policies)
- Admins can use any MCP tool

**Approved MCP Tools**:
- `mcp__github__list_repos`
- `mcp__github__create_issue`
- `mcp__github__get_issue`
- `mcp__slack__send_message`
- `mcp__slack__list_channels`
- `mcp__jira__create_ticket`
- `mcp__jira__update_ticket`
- `mcp__aws__list_instances`
- `mcp__aws__describe_instance`

**Example Violation**:
```
Tool execution blocked by policy enforcement.

Tool: mcp__pagerduty__create_incident
Blocked by policies: mcp_tool_allowlist

MCP tool 'mcp__pagerduty__create_incident' is not in the approved list.
Approved tools: [mcp__github__list_repos, mcp__slack__send_message, ...]
Contact admin to request access.
```

## Tool Classification

### Risk Levels

Policies use the following risk levels automatically assigned by the enforcement service:

- **Critical**: Destructive commands (`rm -rf /`, `dd`, `mkfs`, fork bombs)
- **High**: Command execution tools, sensitive file access
- **Medium**: File write/edit operations
- **Low**: Read operations, safe tools

### Tool Sources

- **MCP**: Tools starting with `mcp__` prefix
- **Builtin**: Platform tools (Bash, Read, Write, Edit, Grep, Glob, etc.)
- **Skill**: Custom user-defined tools

### Tool Categories

- **command_execution**: Bash and similar command tools
- **file_operation**: Read, Write, Edit
- **file_search**: Grep, Glob
- **network**: WebFetch, API calls
- **general**: Other tools

## Policy Development

### Creating Custom Policies

All tool enforcement policies should:

1. Use package `kubiya.tool_enforcement`
2. Start with `default allow = false` (deny by default)
3. Define clear `allow` rules
4. Provide helpful `violation` messages
5. Include metadata (name, description, version)

Example template:

```rego
package kubiya.tool_enforcement

import future.keywords.if

# Default deny
default allow = false

# Allow rule
allow if {
    # Your conditions here
    input.user.roles[_] == "approved_role"
}

# Violation message
violation[msg] if {
    not allow
    msg := "Clear explanation of why the tool was blocked and what to do next"
}

# Metadata
metadata := {
    "name": "my_custom_policy",
    "description": "Description of what this policy does",
    "version": "1.0.0",
    "author": "Your Name",
    "tags": ["security", "custom"]
}
```

### Testing Policies

Test policies locally using OPA CLI:

```bash
# Test a single policy
opa test control_plane_api/app/policies/tool_enforcement/role_based_tool_access.rego

# Test with input
opa eval -d control_plane_api/app/policies/tool_enforcement/ \
         -i test_input.json \
         'data.kubiya.tool_enforcement.allow'

# Run policy benchmarks
opa test --benchmark control_plane_api/app/policies/tool_enforcement/
```

### Deploying Policies

Upload policies through the Control Plane API:

```bash
# Create policy
curl -X POST https://control-plane.example.com/api/v1/policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @policy.json

# Enable policy
curl -X PATCH https://control-plane.example.com/api/v1/policies/{id} \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"enabled": true}'
```

## Best Practices

1. **Start restrictive**: Begin with deny-by-default and explicit allow rules
2. **Clear messages**: Provide actionable violation messages
3. **Test thoroughly**: Test with various inputs before deploying
4. **Version policies**: Use metadata to track policy versions
5. **Document assumptions**: Comment complex logic in Rego code
6. **Monitor impact**: Track policy allow/deny metrics after deployment
7. **Admin overrides**: Always provide admin bypass for emergencies

## Troubleshooting

### Policy Not Applied

If a policy isn't being enforced:

1. Verify policy is loaded in enforcer:
   ```bash
   curl https://control-plane.example.com/api/v1/policies
   ```

2. Check policy is enabled:
   ```bash
   curl https://control-plane.example.com/api/v1/policies/{id}
   ```

3. Review worker logs for enforcement errors:
   ```bash
   tail -f /var/log/worker/worker.log | grep enforcement
   ```

### False Positives

If safe tools are being blocked incorrectly:

1. Review policy conditions with test input
2. Add exemptions for specific users/roles
3. Adjust risk level classifications if needed
4. Consider environment-specific policies

### Performance Issues

If policy evaluation is slow:

1. Simplify complex Rego logic
2. Profile policies with `opa test --bench`
3. Reduce policy count if possible
4. Consider caching frequently-evaluated decisions

## References

- [Tool Enforcement Guide](../../../../../docs/TOOL_ENFORCEMENT.md) - Complete documentation
- [OPA Documentation](https://www.openpolicyagent.org/docs/latest/)
- [Rego Language Reference](https://www.openpolicyagent.org/docs/latest/policy-reference/)
- [Policy Management API](../../README.md)

## Support

For issues with tool enforcement policies:
- [GitHub Issues](https://github.com/kubiyabot/agent-control-plane/issues)
- [Discord Community](https://discord.gg/kubiya)
- Email: support@kubiya.ai
