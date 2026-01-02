/*
 * YARA Rules for Missing Timeout Configuration
 *
 * These rules detect patterns in tool definitions that indicate
 * missing or problematic timeout configuration.
 *
 * Note: These are heuristic patterns. The Heuristic provider does
 * more thorough structural checks. These catch descriptive indicators.
 */

rule TimeoutNotConfigured
{
    meta:
        title = "Timeout explicitly not configured"
        description = "Description indicates timeout is not configured or disabled"
        category = "missing_timeout"
        severity = "high"
        remediation = "Configure an appropriate timeout value (e.g., 30 seconds for network operations)"

    strings:
        $no_timeout = "no timeout" nocase
        $timeout_disabled = "timeout disabled" nocase
        $timeout_none = "timeout: none" nocase
        $timeout_null = "timeout: null" nocase
        $without_timeout = "without timeout" nocase
        $timeout_0 = /"timeout"\s*:\s*0/
        $timeoutMs_0 = /"timeoutMs"\s*:\s*0/

    condition:
        any of them
}

rule IndefiniteWait
{
    meta:
        title = "May wait indefinitely"
        description = "Operation may block or wait indefinitely without timeout protection"
        category = "missing_timeout"
        severity = "high"
        remediation = "Add timeout configuration to prevent indefinite blocking"

    strings:
        $indefinitely = "indefinitely" nocase
        $wait_forever = "wait forever" nocase
        $block_forever = "block forever" nocase
        $no_time_limit = "no time limit" nocase
        $unlimited_time = "unlimited time" nocase
        $hang_indefinitely = "hang indefinitely" nocase

    condition:
        any of them
}

rule LongRunning
{
    meta:
        title = "Long-running operation indicated"
        description = "Tool mentions long-running operations which may need special timeout handling"
        category = "missing_timeout"
        severity = "info"
        remediation = "Ensure appropriate timeouts are configured for long-running operations"

    strings:
        $long_running = "long-running" nocase
        $long_operation = "long operation" nocase
        $takes_time = "takes a long time" nocase
        $may_take_minutes = "may take minutes" nocase
        $can_take_hours = "can take hours" nocase

    condition:
        any of them
}

rule ExternalDependency
{
    meta:
        title = "External dependency without timeout mention"
        description = "Tool depends on external services but doesn't mention timeout handling"
        category = "missing_timeout"
        severity = "low"
        remediation = "Configure timeouts for all external service calls"

    strings:
        $calls_api = /calls?\s+(an?\s+)?(external\s+)?api/i nocase
        $http_request = "http request" nocase
        $network_call = "network call" nocase
        $remote_service = "remote service" nocase
        $external_service = "external service" nocase
        $third_party = "third-party" nocase

    condition:
        any of them and not /timeout/i
}
