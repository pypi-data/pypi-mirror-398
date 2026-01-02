# MCP Readiness Scanner - Operational Risk Taxonomy

This document describes the operational risk categories used by MCP Readiness Scanner. These categories focus on **production reliability and failure modes**, not security vulnerabilities (which are covered by tools like Cisco's MCP Scanner).

## Overview

| Category | ID | Default Severity |
|----------|-----|------------------|
| Silent Failure Path | `silent_failure_path` | High |
| Non-Deterministic Response | `non_deterministic_response` | Medium |
| Missing Timeout Guard | `missing_timeout_guard` | High |
| No Observability Hooks | `no_observability_hooks` | Medium |
| Unsafe Retry Loop | `unsafe_retry_loop` | High |
| Overloaded Tool Scope | `overloaded_tool_scope` | Medium |
| No Fallback Contract | `no_fallback_contract` | Low |
| Missing Error Schema | `missing_error_schema` | Medium |

---

## Silent Failure Path

**ID:** `silent_failure_path`
**Default Severity:** High

### Description

A silent failure path exists when a tool can encounter an error condition but continues execution without properly reporting the failure. This leads to situations where:

- The calling agent believes the operation succeeded when it didn't
- Data may be partially processed or corrupted without indication
- Downstream operations proceed with invalid assumptions
- Debugging becomes extremely difficult due to lack of error signals

### Common Causes

- Catching exceptions without re-raising or logging
- Using "best effort" semantics without status reporting
- Fire-and-forget patterns without confirmation
- Missing error response schemas

### Remediation

1. Define explicit error response schemas
2. Ensure all failure conditions return appropriate error responses
3. Avoid empty catch blocks or "swallow" patterns
4. Use structured error types that agents can interpret
5. Consider using observability hooks for error tracking

---

## Non-Deterministic Response

**ID:** `non_deterministic_response`
**Default Severity:** Medium

### Description

Non-deterministic responses occur when the same input can produce structurally different outputs, making it difficult for agents to reliably parse and act on results.

### Symptoms

- Response schema varies based on internal state
- Optional fields that appear/disappear without clear rules
- Different field names for the same data
- Inconsistent data types (string vs number vs null)

### Impact on Agents

- Parsing logic becomes fragile
- Agents may misinterpret data or crash
- Retry logic may behave inconsistently
- Test coverage becomes incomplete

### Remediation

1. Define strict response schemas with clear optionality rules
2. Use consistent field names and types across all responses
3. Document all possible response variations
4. Consider using discriminated unions for different response types
5. Add response validation in tests

---

## Missing Timeout Guard

**ID:** `missing_timeout_guard`
**Default Severity:** High

### Description

Without proper timeout guards, tool operations can hang indefinitely when external dependencies become unresponsive. This creates cascading failures in agent workflows.

### Risk Factors

- Network calls without timeouts
- Database queries without limits
- External API calls without deadline propagation
- Long-running computations without checkpoints

### Production Impact

- Agent threads/processes become stuck
- Resource exhaustion (connections, memory)
- User-facing latency spikes
- Cascading timeouts up the call chain

### Remediation

1. Configure explicit timeouts for all external calls
2. Set reasonable defaults based on expected operation duration
3. Implement deadline propagation from caller to callee
4. Add circuit breakers for repeated timeout failures
5. Monitor and alert on timeout rates

---

## No Observability Hooks

**ID:** `no_observability_hooks`
**Default Severity:** Medium

### Description

Tools without observability hooks are difficult to monitor, debug, and operate in production. When issues occur, operators lack the visibility needed to diagnose and resolve problems quickly.

### Missing Observability Includes

- No structured logging
- No metrics emission
- No distributed tracing support
- No health check endpoints
- No performance profiling hooks

### Operational Impact

- Blind spots in monitoring dashboards
- Extended incident resolution times
- Difficulty correlating issues across services
- No baseline for performance regression detection

### Remediation

1. Add structured logging with consistent fields
2. Emit key metrics (latency, error rate, throughput)
3. Support distributed tracing (trace ID propagation)
4. Implement health check responses
5. Consider adding debug/diagnostic modes

---

## Unsafe Retry Loop

**ID:** `unsafe_retry_loop`
**Default Severity:** High

### Description

Retry logic without proper safeguards can amplify failures rather than recover from them. Unsafe retry patterns turn transient failures into sustained outages.

### Dangerous Patterns

- Unlimited retry attempts
- Fixed retry intervals (no backoff)
- Retrying non-idempotent operations
- No jitter in retry timing
- Retrying on all errors (including permanent failures)

### Consequences

- Thundering herd effects
- Resource exhaustion on dependent services
- Data duplication from non-idempotent retries
- Extended outages from retry amplification

### Remediation

1. Set maximum retry limits
2. Implement exponential backoff with jitter
3. Only retry on transient/retryable errors
4. Ensure idempotency for retried operations
5. Add circuit breakers to stop retries on sustained failures

---

## Overloaded Tool Scope

**ID:** `overloaded_tool_scope`
**Default Severity:** Medium

### Description

Tools with excessive capabilities become difficult to test, secure, and maintain. They also create confusion for agents trying to select the right tool for a task.

### Signs of Overloaded Scope

- Many unrelated capabilities in a single tool
- Complex branching logic based on parameters
- Large attack surface from capability combinations
- Difficulty documenting all behaviors
- Long, unfocused tool descriptions

### Problems Caused

- Incomplete test coverage
- Unpredictable agent tool selection
- Higher maintenance burden
- Security review complexity
- Performance inconsistency across capabilities

### Remediation

1. Split into focused, single-purpose tools
2. Limit capabilities to related operations
3. Use composition over consolidation
4. Write clear, concise descriptions for each tool
5. Consider the principle of least authority

---

## No Fallback Contract

**ID:** `no_fallback_contract`
**Default Severity:** Low

### Description

Without a fallback contract, tools fail completely when dependencies are unavailable, rather than providing degraded but useful responses. This reduces system resilience.

### Missing Fallback Patterns

- No graceful degradation paths
- No cached/stale data options
- No default responses for unavailability
- No partial success handling
- No circuit breaker states

### Impact

- Complete failures propagate to users
- No graceful degradation during incidents
- Agents cannot adapt to reduced capability
- All-or-nothing behavior reduces availability

### Remediation

1. Define explicit fallback behaviors
2. Implement graceful degradation modes
3. Consider caching for read operations
4. Document partial success semantics
5. Use feature flags for capability toggling

---

## Missing Error Schema

**ID:** `missing_error_schema`
**Default Severity:** Medium

### Description

Without a defined error schema, agents cannot programmatically handle failures. They're left to parse error messages as text, which is fragile and unreliable.

### Problems with Unstructured Errors

- Error types cannot be distinguished
- Retry decisions based on string matching
- Localized messages break parsing
- No machine-readable error codes
- Context information is unstructured

### Agent Limitations

- Cannot implement proper error handling
- Fallback logic becomes heuristic
- Error reporting is inconsistent
- Recovery actions cannot be automated

### Remediation

1. Define explicit error response schema
2. Use error codes alongside messages
3. Include structured context in errors
4. Document all possible error types
5. Consider using standard error formats
