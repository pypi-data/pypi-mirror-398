# MCP Tool Allowlist Policy
# Only allow approved MCP tools to be executed

package kubiya.tool_enforcement

import future.keywords.if
import future.keywords.in

# Default deny
default allow = false

# Approved MCP tools (whitelist)
approved_mcp_tools := [
    "mcp__github__list_repos",
    "mcp__github__create_issue",
    "mcp__github__get_issue",
    "mcp__slack__send_message",
    "mcp__slack__list_channels",
    "mcp__jira__create_ticket",
    "mcp__jira__update_ticket",
    "mcp__aws__list_instances",
    "mcp__aws__describe_instance",
]

# Allow approved MCP tools
allow if {
    input.tool.source == "mcp"
    input.tool.name in approved_mcp_tools
}

# Allow non-MCP tools (governed by other policies)
allow if {
    input.tool.source != "mcp"
    input.user.email != ""
}

# Admins can use any MCP tool
allow if {
    input.tool.source == "mcp"
    input.user.roles[_] == "admin"
}

# Violation message
violation[msg] if {
    input.tool.source == "mcp"
    not input.tool.name in approved_mcp_tools
    not input.user.roles[_] == "admin"
    msg := sprintf("MCP tool '%s' is not in the approved list. Approved tools: %v. Contact admin to request access.", [input.tool.name, approved_mcp_tools])
}

# Metadata
metadata := {
    "name": "mcp_tool_allowlist",
    "description": "Whitelist of approved MCP tools",
    "version": "1.0.0",
    "author": "Kubiya",
    "tags": ["mcp", "whitelist", "security"]
}
