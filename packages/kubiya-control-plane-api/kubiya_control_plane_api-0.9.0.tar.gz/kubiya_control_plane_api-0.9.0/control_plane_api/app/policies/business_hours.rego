# Business Hours Policy
# Restricts agent executions to business hours (9 AM - 5 PM, Monday-Friday)

package business_hours

import future.keywords.if
import future.keywords.in

# Default deny
default allow = false

# Allow executions during business hours
allow if {
    is_business_hours
    not is_weekend
}

# Check if current time is within business hours (9 AM - 5 PM)
is_business_hours if {
    time_hour := time.parse_rfc3339_ns(input.time)
    hour := time.clock(time_hour)[0]
    hour >= 9
    hour < 17
}

# Check if current day is a weekend
is_weekend if {
    time_day := time.parse_rfc3339_ns(input.time)
    weekday := time.weekday(time_day)
    weekday in ["Saturday", "Sunday"]
}

# Violations
violations[msg] if {
    not is_business_hours
    msg := sprintf("Execution requested outside business hours (9 AM - 5 PM). Current time: %v", [input.time])
}

violations[msg] if {
    is_weekend
    msg := sprintf("Execution requested on weekend. Current day: %v", [time.weekday(time.parse_rfc3339_ns(input.time))])
}

# Metadata
metadata := {
    "name": "business-hours-only",
    "description": "Restrict agent executions to business hours (9 AM - 5 PM, Monday-Friday)",
    "version": "1.0.0",
    "author": "Kubiya",
    "tags": ["time", "compliance", "business-hours"]
}
