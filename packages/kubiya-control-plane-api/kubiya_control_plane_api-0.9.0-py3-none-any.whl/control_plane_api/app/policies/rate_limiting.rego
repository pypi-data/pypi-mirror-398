# Rate Limiting Policy
# Limits the number of executions per user/agent within a time window

package rate_limiting

import future.keywords.if
import future.keywords.in

# Default deny
default allow = false

# Maximum executions per hour per user
max_executions_per_hour := 100

# Maximum executions per hour per agent
max_agent_executions_per_hour := 50

# Maximum concurrent executions per user
max_concurrent_executions := 5

# Allow if under user rate limit
allow if {
    input.user
    input.executions_last_hour < max_executions_per_hour
}

# Allow if under agent rate limit
allow if {
    input.agent_id
    input.agent_executions_last_hour < max_agent_executions_per_hour
}

# Allow if under concurrent execution limit
allow if {
    input.user
    input.concurrent_executions < max_concurrent_executions
}

# Special handling for admin users (higher limits)
allow if {
    is_admin_user
    input.executions_last_hour < (max_executions_per_hour * 2)
}

# Check if user is admin
is_admin_user if {
    input.user
    contains(input.user, "admin@")
}

is_admin_user if {
    input.user_role == "admin"
}

# Violations
violations[msg] if {
    input.user
    input.executions_last_hour >= max_executions_per_hour
    not is_admin_user
    msg := sprintf("User '%v' has exceeded rate limit: %v executions in the last hour (max: %v)", [
        input.user,
        input.executions_last_hour,
        max_executions_per_hour
    ])
}

violations[msg] if {
    input.agent_id
    input.agent_executions_last_hour >= max_agent_executions_per_hour
    msg := sprintf("Agent '%v' has exceeded rate limit: %v executions in the last hour (max: %v)", [
        input.agent_id,
        input.agent_executions_last_hour,
        max_agent_executions_per_hour
    ])
}

violations[msg] if {
    input.user
    input.concurrent_executions >= max_concurrent_executions
    msg := sprintf("User '%v' has too many concurrent executions: %v (max: %v)", [
        input.user,
        input.concurrent_executions,
        max_concurrent_executions
    ])
}

violations[msg] if {
    not input.user
    not input.agent_id
    msg := "No user or agent_id specified for rate limiting check"
}

# Metadata
metadata := {
    "name": "rate-limiting",
    "description": "Limit execution frequency per user and agent to prevent abuse",
    "version": "1.0.0",
    "author": "Kubiya",
    "tags": ["security", "rate-limiting", "quota"]
}
