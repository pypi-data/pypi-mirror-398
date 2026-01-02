/*
 * YARA Rules for Non-Deterministic Response Patterns
 *
 * These rules detect indicators of non-deterministic behavior in tool
 * responses, which can make tools unpredictable and difficult to use
 * reliably in production.
 */

rule RandomOutput
{
    meta:
        title = "Random or unpredictable output"
        description = "Tool may produce random or varying outputs for the same input"
        category = "non_deterministic_response"
        severity = "high"
        remediation = "Ensure deterministic behavior or clearly document randomness and provide seed parameters for reproducibility"

    strings:
        $random_output = "random output" nocase
        $randomly_generated = "randomly generated" nocase
        $random_response = "random response" nocase
        $may_vary = "may vary" nocase
        $results_vary = "results vary" nocase
        $different_each_time = "different each time" nocase
        $unpredictable = "unpredictable" nocase
        $non_deterministic = "non-deterministic" nocase

    condition:
        any of them
}

rule InconsistentFormat
{
    meta:
        title = "Inconsistent response format"
        description = "Response format or schema may change between invocations"
        category = "non_deterministic_response"
        severity = "high"
        remediation = "Define a stable response schema and ensure consistent output structure"

    strings:
        $format_varies = "format varies" nocase
        $inconsistent_format = "inconsistent format" nocase
        $varying_structure = "varying structure" nocase
        $different_formats = "different formats" nocase
        $format_may_change = "format may change" nocase
        $schema_varies = "schema varies" nocase
        $sometimes_returns = "sometimes returns" nocase

    condition:
        any of them
}

rule TimeDependentBehavior
{
    meta:
        title = "Time-dependent behavior"
        description = "Tool behavior varies based on time of day, date, or temporal factors"
        category = "non_deterministic_response"
        severity = "medium"
        remediation = "Make temporal dependencies explicit in parameters rather than implicit in behavior"

    strings:
        $time_dependent = "time-dependent" nocase
        $time_of_day = "time of day" nocase
        $depends_on_time = "depends on time" nocase
        $varies_by_date = "varies by date" nocase
        $temporal_variation = "temporal variation" nocase
        $changes_over_time = "changes over time" nocase
        $date_specific = "date-specific behavior" nocase

    condition:
        any of them
}

rule RaceCondition
{
    meta:
        title = "Potential race condition"
        description = "Tool may have race conditions affecting output consistency"
        category = "non_deterministic_response"
        severity = "high"
        remediation = "Implement proper synchronization and locking for shared state"

    strings:
        $race_condition = "race condition" nocase
        $race_hazard = "race hazard" nocase
        $concurrent_access = "concurrent access without lock" nocase
        $unsynchronized = "unsynchronized access" nocase
        $thread_unsafe = "thread-unsafe" nocase
        $not_thread_safe = "not thread safe" nocase
        $timing_dependent = "timing-dependent" nocase
        $order_matters = "order of execution matters" nocase

    condition:
        any of them
}

rule ExternalStateDependency
{
    meta:
        title = "Dependency on external mutable state"
        description = "Tool depends on external state that may change between calls"
        category = "non_deterministic_response"
        severity = "medium"
        remediation = "Make state dependencies explicit in tool parameters or document state management"

    strings:
        $global_state = "global state" nocase
        $shared_state = "shared state" nocase
        $mutable_state = "mutable state" nocase
        $external_state = "external state" nocase
        $state_may_change = "state may change" nocase
        $depends_on_cache = "depends on cache" nocase
        $cache_dependent = "cache-dependent" nocase
        $stateful_behavior = "stateful behavior" nocase

    condition:
        any of them
}
