# Timeout Required Policy
#
# Ensures MCP tools have proper timeout configuration to prevent
# indefinite hangs when external dependencies become unresponsive.

package mcp.readiness

# Violation: Tool must have timeout configured
violation[msg] {
    input.type == "tool"
    not input.has_timeout
    msg := sprintf("Tool '%s' must have timeout configured to prevent indefinite hangs", [input.tool_name])
}

# Violation: Timeout value cannot be zero
violation[msg] {
    input.type == "tool"
    input.has_timeout
    input.timeout_value == 0
    msg := sprintf("Tool '%s' has timeout set to 0, which effectively disables timeout protection", [input.tool_name])
}

# Violation: Timeout value cannot be negative
violation[msg] {
    input.type == "tool"
    input.has_timeout
    input.timeout_value < 0
    msg := sprintf("Tool '%s' has negative timeout value (%d), which is invalid", [input.tool_name, input.timeout_value])
}

# Warning: Very short timeout (less than 1 second)
violation[msg] {
    input.type == "tool"
    input.has_timeout
    input.timeout_value > 0
    input.timeout_value < 1000  # Assuming milliseconds
    msg := sprintf("Tool '%s' has very short timeout (%dms). Consider if this is intentional", [input.tool_name, input.timeout_value])
}

# Warning: Very long timeout (more than 5 minutes)
violation[msg] {
    input.type == "tool"
    input.has_timeout
    input.timeout_value > 300000  # 5 minutes in milliseconds
    msg := sprintf("Tool '%s' has very long timeout (%dms). Consider if this could cause user-facing delays", [input.tool_name, input.timeout_value])
}

# Config: Server must have timeout
violation[msg] {
    input.type == "config"
    not input.has_timeout
    msg := sprintf("Server '%s' should have timeout configured for initialization", [input.server_name])
}
