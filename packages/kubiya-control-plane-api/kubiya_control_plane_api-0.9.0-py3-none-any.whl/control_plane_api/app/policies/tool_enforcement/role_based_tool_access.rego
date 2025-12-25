# Role-Based Tool Access Policy
# Only admin and devops roles can execute command execution tools

package kubiya.tool_enforcement

import future.keywords.if
import future.keywords.in

# Default deny
default allow = false

# Allow if user has required role for command execution
allow if {
    input.tool.category == "command_execution"
    input.user.roles[_] == "admin"
}

allow if {
    input.tool.category == "command_execution"
    input.user.roles[_] == "devops"
}

# Allow all other tool categories for any authenticated user
allow if {
    input.tool.category != "command_execution"
    input.user.email != ""
}

# Violation message
violation[msg] if {
    input.tool.category == "command_execution"
    not input.user.roles[_] == "admin"
    not input.user.roles[_] == "devops"
    msg := sprintf("Command execution tools require 'admin' or 'devops' role. User %s has roles: %v", [input.user.email, input.user.roles])
}

# Metadata
metadata := {
    "name": "role_based_tool_access",
    "description": "Only admin and devops roles can execute command tools",
    "version": "1.0.0",
    "author": "Kubiya",
    "tags": ["rbac", "security", "command_execution"]
}
