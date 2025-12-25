# Approved Users Policy
# Only allows executions from a whitelist of approved users

package approved_users

import future.keywords.if
import future.keywords.in

# Default deny
default allow = false

# List of approved users (emails)
# This can be customized per organization or pulled from metadata
approved_user_list := {
    "admin@company.com",
    "devops@company.com",
    "alice@company.com",
    "bob@company.com"
}

# Allow if user is in the approved list
allow if {
    input.user in approved_user_list
}

# Also allow if user email domain is approved
allow if {
    user_email := input.user
    contains(user_email, "@")
    domain := split(user_email, "@")[1]
    domain in approved_domains
}

# Approved email domains
approved_domains := {
    "company.com",
    "trusted-partner.com"
}

# Violations
violations[msg] if {
    not input.user in approved_user_list
    user_email := input.user
    contains(user_email, "@")
    domain := split(user_email, "@")[1]
    not domain in approved_domains
    msg := sprintf("User '%v' is not in the approved user list or approved domain", [input.user])
}

violations[msg] if {
    not input.user
    msg := "No user specified in the request"
}

# Metadata
metadata := {
    "name": "approved-users-only",
    "description": "Only allow executions from approved users or domains",
    "version": "1.0.0",
    "author": "Kubiya",
    "tags": ["security", "access-control", "users"]
}
