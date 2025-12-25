# Tool Restrictions Policy
# Controls which tools agents can use, with different restrictions per environment

package tool_restrictions

import future.keywords.if
import future.keywords.in

# Default deny
default allow = false

# Dangerous tools that require explicit approval
dangerous_tools := {
    "docker",
    "shell",
    "file_system"
}

# Production-safe tools
production_safe_tools := {
    "python",
    "sleep",
    "file_generation"
}

# Development environment - allow all tools
allow if {
    input.environment == "development"
}

# Staging environment - allow non-dangerous tools
allow if {
    input.environment == "staging"
    input.tool
    not input.tool in dangerous_tools
}

# Production environment - only allow production-safe tools
allow if {
    input.environment == "production"
    input.tool in production_safe_tools
}

# Allow dangerous tools in production with explicit approval
allow if {
    input.environment == "production"
    input.tool in dangerous_tools
    input.approved_by
    input.approval_id
}

# Violations
violations[msg] if {
    input.environment == "production"
    input.tool in dangerous_tools
    not input.approved_by
    msg := sprintf("Tool '%v' requires approval in production environment", [input.tool])
}

violations[msg] if {
    input.environment == "staging"
    input.tool in dangerous_tools
    msg := sprintf("Dangerous tool '%v' not allowed in staging environment", [input.tool])
}

violations[msg] if {
    input.environment == "production"
    input.tool
    not input.tool in production_safe_tools
    not input.approved_by
    msg := sprintf("Tool '%v' not allowed in production without approval", [input.tool])
}

violations[msg] if {
    not input.tool
    msg := "No tool specified in the request"
}

# Metadata
metadata := {
    "name": "tool-restrictions",
    "description": "Control which tools agents can use based on environment and approval status",
    "version": "1.0.0",
    "author": "Kubiya",
    "tags": ["security", "tools", "environment"]
}
