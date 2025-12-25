# Production Safeguards Policy
# Block high-risk and critical operations in production environment

package kubiya.tool_enforcement

import future.keywords.if

# Default deny
default allow = false

# Block high-risk tools in production
deny if {
    input.execution.environment == "production"
    input.tool.risk_level == "critical"
}

deny if {
    input.execution.environment == "production"
    input.tool.risk_level == "high"
    input.tool.category == "command_execution"
    contains(lower(input.tool.arguments.command), "delete")
}

deny if {
    input.execution.environment == "production"
    input.tool.category == "file_operation"
    input.tool.name == "Write"
    contains(input.tool.arguments.file_path, "/etc/")
}

# Allow everything in non-production
allow if {
    input.execution.environment != "production"
    input.user.email != ""
}

# Allow safe operations in production
allow if {
    input.execution.environment == "production"
    input.tool.risk_level == "low"
}

allow if {
    input.execution.environment == "production"
    input.tool.risk_level == "medium"
    not deny
}

# Allow with admin override
allow if {
    input.user.roles[_] == "admin"
}

# Violation messages
violation[msg] if {
    deny
    input.tool.risk_level == "critical"
    msg := sprintf("Critical tool '%s' is blocked in production. Use dev/staging for testing.", [input.tool.name])
}

violation[msg] if {
    deny
    input.tool.risk_level == "high"
    not input.tool.risk_level == "critical"
    msg := sprintf("High-risk tool '%s' is restricted in production. Contact admin for approval.", [input.tool.name])
}

# Helper function
lower(s) := lower_s {
    lower_s := lower(s)
}

# Metadata
metadata := {
    "name": "production_safeguards",
    "description": "Block high-risk operations in production environment",
    "version": "1.0.0",
    "author": "Kubiya",
    "tags": ["production", "security", "risk_management"]
}
