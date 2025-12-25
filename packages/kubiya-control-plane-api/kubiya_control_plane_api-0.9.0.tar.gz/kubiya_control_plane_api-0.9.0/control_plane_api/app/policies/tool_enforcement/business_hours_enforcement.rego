# Business Hours Enforcement Policy
# Restrict high-risk tools to business hours (9 AM - 6 PM UTC, Monday-Friday)

package kubiya.tool_enforcement

import future.keywords.if

# Default deny
default allow = false

# Parse timestamp and check business hours
is_business_hours if {
    # Parse the ISO 8601 timestamp
    time_ns := time.parse_rfc3339_ns(input.execution.timestamp)

    # Get time components [year, month, day, hour, minute, second, day_of_week]
    time_parts := time.clock(time_ns)
    hour := time_parts[3]

    # Get day of week (0 = Sunday, 1 = Monday, ..., 6 = Saturday)
    day_of_week := time.weekday(time_ns)

    # Business hours: 9 AM - 6 PM
    hour >= 9
    hour < 18

    # Business days: Monday-Friday
    day_of_week in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
}

# High-risk tools only during business hours
deny if {
    input.tool.risk_level == "high"
    not is_business_hours
}

deny if {
    input.tool.risk_level == "critical"
    not is_business_hours
}

# Allow low/medium risk anytime
allow if {
    input.tool.risk_level == "low"
}

allow if {
    input.tool.risk_level == "medium"
}

# Allow high-risk during business hours
allow if {
    input.tool.risk_level == "high"
    is_business_hours
}

allow if {
    input.tool.risk_level == "critical"
    is_business_hours
}

# Admins bypass time restrictions
allow if {
    input.user.roles[_] == "admin"
}

# Violation message
violation[msg] if {
    deny
    input.tool.risk_level in ["high", "critical"]
    not is_business_hours
    msg := "High-risk tools are restricted to business hours (9 AM - 6 PM UTC, Monday-Friday). Contact admin for urgent requests."
}

# Metadata
metadata := {
    "name": "business_hours_enforcement",
    "description": "Restrict high-risk tools to business hours",
    "version": "1.0.0",
    "author": "Kubiya",
    "tags": ["time_based", "security", "business_hours"]
}
