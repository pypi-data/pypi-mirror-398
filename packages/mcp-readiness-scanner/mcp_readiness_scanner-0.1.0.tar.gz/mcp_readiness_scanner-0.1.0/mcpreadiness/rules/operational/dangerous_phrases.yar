/*
 * YARA Rules for Dangerous Phrases in MCP Tool Metadata
 *
 * These rules detect phrases in tool descriptions and metadata that
 * indicate potential silent failure paths or unreliable behavior.
 *
 * IMPORTANT: These rules target METADATA (descriptions, names, schemas),
 * NOT source code AST.
 */

rule IgnoreErrors
{
    meta:
        title = "Tool may ignore errors"
        description = "Description indicates errors may be ignored, leading to silent failures"
        category = "silent_failure"
        severity = "medium"
        remediation = "Ensure all errors are properly surfaced to callers with structured error responses"

    strings:
        $ignore_error = /ignore[sd]?\s+(the\s+)?error/i nocase
        $ignore_errors = "ignore errors" nocase
        $ignoring_error = "ignoring error" nocase
        $errors_ignored = "errors are ignored" nocase
        $errors_will_be_ignored = "errors will be ignored" nocase

    condition:
        any of them
}

rule BestEffort
{
    meta:
        title = "Best-effort semantics without guarantees"
        description = "Tool uses best-effort semantics which may not surface failures"
        category = "silent_failure"
        severity = "medium"
        remediation = "Document specific failure modes and ensure status is reported to callers"

    strings:
        $best_effort = "best effort" nocase
        $best_efforts = "best-effort" nocase
        $on_best_effort = "on a best effort" nocase

    condition:
        any of them
}

rule MayFail
{
    meta:
        title = "Tool explicitly may fail"
        description = "Description indicates the tool may fail without clear failure handling"
        category = "silent_failure"
        severity = "low"
        remediation = "Document specific failure conditions and ensure failures are properly reported"

    strings:
        $may_fail = "may fail" nocase
        $might_fail = "might fail" nocase
        $could_fail = "could fail" nocase
        $can_fail = "can fail" nocase
        $fails_silently = "fails silently" nocase
        $fail_silently = "fail silently" nocase

    condition:
        any of them
}

rule FireAndForget
{
    meta:
        title = "Fire-and-forget pattern detected"
        description = "Tool uses fire-and-forget pattern without confirmation of success"
        category = "silent_failure"
        severity = "high"
        remediation = "Implement confirmation mechanisms and status reporting for all operations"

    strings:
        $fire_and_forget = "fire and forget" nocase
        $fire_forget = "fire-and-forget" nocase
        $no_confirmation = "no confirmation" nocase
        $without_confirmation = "without confirmation" nocase
        $async_no_wait = "async without waiting" nocase

    condition:
        any of them
}

rule NoGuarantee
{
    meta:
        title = "No guarantee of success"
        description = "Tool provides no guarantees about operation success"
        category = "silent_failure"
        severity = "medium"
        remediation = "Define clear success criteria and report operation status"

    strings:
        $no_guarantee = "no guarantee" nocase
        $not_guaranteed = "not guaranteed" nocase
        $no_guarantees = "no guarantees" nocase
        $cannot_guarantee = "cannot guarantee" nocase
        $doesnt_guarantee = /does\s?n[o']t\s+guarantee/i nocase

    condition:
        any of them
}

rule SwallowException
{
    meta:
        title = "Exception swallowing indicated"
        description = "Description suggests exceptions may be caught and not re-raised"
        category = "silent_failure"
        severity = "high"
        remediation = "Ensure all exceptions are either handled with appropriate fallback or propagated to callers"

    strings:
        $swallow_exception = "swallow" nocase
        $catch_all = "catch all" nocase
        $catch_and_ignore = "catch and ignore" nocase
        $suppress_error = "suppress error" nocase
        $suppress_exception = "suppress exception" nocase

    condition:
        any of them
}

rule GracefulDegradation
{
    meta:
        title = "Graceful degradation without specifics"
        description = "Tool mentions graceful degradation but may not clearly indicate when it occurs"
        category = "no_fallback"
        severity = "info"
        remediation = "Document specific degradation conditions and how they are communicated to callers"

    strings:
        $graceful = "gracefully" nocase
        $degrade_gracefully = "degrade gracefully" nocase
        $graceful_degradation = "graceful degradation" nocase

    condition:
        any of them
}
