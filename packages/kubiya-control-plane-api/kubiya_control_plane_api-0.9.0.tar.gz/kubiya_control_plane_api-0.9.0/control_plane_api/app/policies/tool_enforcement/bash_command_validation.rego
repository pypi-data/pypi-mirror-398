# Bash Command Validation Policy
# Block dangerous bash command patterns

package kubiya.tool_enforcement

import future.keywords.if

# Default deny
default allow = false

# Dangerous command patterns
dangerous_patterns := [
    "rm -rf /",
    "dd if=",
    "mkfs",
    ":(){:|:&};:",  # Fork bomb
    "> /dev/sda",
    "chmod 777",
    "wget http://",  # Untrusted downloads
    "curl http://",  # Untrusted downloads (non-HTTPS)
    "nc -l",  # Netcat listener
    "python -m http.server",  # Exposing server
]

# Check if command contains dangerous patterns
has_dangerous_pattern if {
    input.tool.name == "Bash"
    command := input.tool.arguments.command
    pattern := dangerous_patterns[_]
    contains(command, pattern)
}

# Block Bash commands with dangerous patterns
deny if {
    input.tool.name == "Bash"
    has_dangerous_pattern
}

# Allow Bash if no dangerous patterns
allow if {
    input.tool.name == "Bash"
    not has_dangerous_pattern
    input.user.email != ""
}

# Allow non-Bash tools
allow if {
    input.tool.name != "Bash"
    input.user.email != ""
}

# Admin override
allow if {
    input.user.roles[_] == "admin"
}

# Violation message
violation[msg] if {
    deny
    has_dangerous_pattern
    msg := sprintf("Bash command contains dangerous pattern: '%s'. This command is blocked for security reasons.", [input.tool.arguments.command])
}

# Metadata
metadata := {
    "name": "bash_command_validation",
    "description": "Block dangerous bash command patterns",
    "version": "1.0.0",
    "author": "Kubiya",
    "tags": ["bash", "security", "command_validation"]
}
