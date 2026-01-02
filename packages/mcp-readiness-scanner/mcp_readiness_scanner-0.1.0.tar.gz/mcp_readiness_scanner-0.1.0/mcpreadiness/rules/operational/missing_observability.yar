/*
 * YARA Rules for Missing Observability
 *
 * These rules detect indicators of missing or inadequate observability
 * in tool definitions. Observability includes logging, metrics, tracing,
 * and health checks.
 */

rule NoLogging
{
    meta:
        title = "No logging mentioned"
        description = "Tool description doesn't mention logging, which is essential for debugging"
        category = "no_observability"
        severity = "info"
        remediation = "Add structured logging for key operations, errors, and state changes"

    strings:
        $no_logs = "no log" nocase
        $not_logged = "not logged" nocase
        $without_logging = "without logging" nocase
        $logging_disabled = "logging disabled" nocase

    condition:
        any of them
}

rule NoMetrics
{
    meta:
        title = "No metrics collection"
        description = "Tool explicitly doesn't collect metrics needed for monitoring"
        category = "no_observability"
        severity = "info"
        remediation = "Implement metrics for latency, error rates, and throughput"

    strings:
        $no_metrics = "no metrics" nocase
        $metrics_disabled = "metrics disabled" nocase
        $without_metrics = "without metrics" nocase
        $unmonitored = "unmonitored" nocase

    condition:
        any of them
}

rule NoTracing
{
    meta:
        title = "No distributed tracing"
        description = "Tool doesn't support distributed tracing for request correlation"
        category = "no_observability"
        severity = "info"
        remediation = "Implement trace ID propagation for request correlation across services"

    strings:
        $no_tracing = "no tracing" nocase
        $tracing_disabled = "tracing disabled" nocase
        $no_trace_id = "no trace id" nocase
        $without_tracing = "without tracing" nocase

    condition:
        any of them
}

rule DebugMode
{
    meta:
        title = "Debug mode reference"
        description = "Tool mentions debug mode which may affect production behavior"
        category = "no_observability"
        severity = "info"
        remediation = "Ensure debug mode is properly controlled and doesn't affect production reliability"

    strings:
        $debug_mode = "debug mode" nocase
        $debug_only = "debug only" nocase
        $in_debug = "in debug" nocase
        $when_debugging = "when debugging" nocase

    condition:
        any of them
}

rule SilentOperation
{
    meta:
        title = "Silent operation mode"
        description = "Tool operates silently, which may hinder debugging and monitoring"
        category = "no_observability"
        severity = "low"
        remediation = "Ensure silent mode still emits necessary operational telemetry"

    strings:
        $silent = "silent" nocase
        $quiet = "quiet mode" nocase
        $no_output = "no output" nocase
        $suppress_output = "suppress output" nocase

    condition:
        any of them
}
