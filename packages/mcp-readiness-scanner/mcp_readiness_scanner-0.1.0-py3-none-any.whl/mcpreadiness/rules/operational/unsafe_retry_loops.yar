/*
 * YARA Rules for Unsafe Retry Loops
 *
 * These rules detect patterns in tool descriptions and metadata that
 * indicate problematic retry behavior that could cause resource exhaustion,
 * cascading failures, or indefinite blocking.
 */

rule InfiniteRetries
{
    meta:
        title = "Infinite or unlimited retries"
        description = "Tool may retry indefinitely without bounds, risking resource exhaustion"
        category = "unsafe_retry_loop"
        severity = "critical"
        remediation = "Set a maximum retry count (e.g., 3-5 attempts) and implement exponential backoff"

    strings:
        $infinite_retry = "infinite retries" nocase
        $unlimited_retry = "unlimited retries" nocase
        $retry_forever = "retry forever" nocase
        $keep_retrying = "keep retrying" nocase
        $retry_until_success = "retry until success" nocase
        $never_give_up = "never give up" nocase
        $max_retries_none = /"max_retries"\s*:\s*null/
        $max_retries_negative = /"max_retries"\s*:\s*-1/
        $retries_infinite = /"retries"\s*:\s*"infinite"/i

    condition:
        any of them
}

rule NoBackoff
{
    meta:
        title = "Retry without backoff strategy"
        description = "Tool retries immediately without backoff, risking thundering herd problems"
        category = "unsafe_retry_loop"
        severity = "high"
        remediation = "Implement exponential backoff with jitter between retry attempts"

    strings:
        $immediate_retry = "immediate retry" nocase
        $retry_immediately = "retry immediately" nocase
        $no_backoff = "no backoff" nocase
        $without_backoff = "without backoff" nocase
        $no_delay = "no delay between retries" nocase
        $backoff_disabled = "backoff disabled" nocase
        $zero_backoff = /"backoff"\s*:\s*0/
        $backoff_false = /"backoff"\s*:\s*false/

    condition:
        any of them
}

rule ExcessiveRetries
{
    meta:
        title = "Excessive retry count"
        description = "Tool configured with very high retry count that may cause delays"
        category = "unsafe_retry_loop"
        severity = "medium"
        remediation = "Reduce retry count to 3-5 attempts with appropriate backoff"

    strings:
        // Match retry counts >= 10 or very high numbers
        $many_retries_1 = /"max_retries"\s*:\s*[1-9]\d{2,}/  // >= 100
        $many_retries_2 = /"retries"\s*:\s*[1-9]\d{2,}/
        $many_retries_3 = /"retry_count"\s*:\s*[1-9]\d{2,}/
        $many_attempts = "many retry attempts" nocase
        $too_many_retries = "too many retries" nocase

    condition:
        any of them
}

rule RetryAllErrors
{
    meta:
        title = "Retries on non-retryable errors"
        description = "Tool retries all errors including permanent failures, wasting resources"
        category = "unsafe_retry_loop"
        severity = "high"
        remediation = "Only retry transient errors (network timeouts, rate limits); fail fast on permanent errors (auth failures, invalid input)"

    strings:
        $retry_all = "retry all errors" nocase
        $retry_any_error = "retry any error" nocase
        $retry_everything = "retry on all failures" nocase
        $always_retry = "always retry" nocase
        $retry_regardless = "retry regardless" nocase
        $catch_all_retry = /retry.*catch.*all/i nocase

    condition:
        any of them
}

rule CascadingRetries
{
    meta:
        title = "Potential cascading retry behavior"
        description = "Retry behavior may cause cascading failures in dependent services"
        category = "unsafe_retry_loop"
        severity = "medium"
        remediation = "Implement circuit breaker pattern and coordinate retry budgets across services"

    strings:
        $nested_retry = "nested retries" nocase
        $retry_chain = "retry chain" nocase
        $cascading = "cascading retries" nocase
        $multiple_layers = "multiple retry layers" nocase
        $retry_on_retry = "retry on retry" nocase
        $no_circuit_breaker = "no circuit breaker" nocase

    condition:
        any of them
}
