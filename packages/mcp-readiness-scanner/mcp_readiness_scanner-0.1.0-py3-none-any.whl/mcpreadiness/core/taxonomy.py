"""
Operational Risk Taxonomy for MCP Readiness Scanner.

This module provides detailed descriptions and guidance for each
operational risk category. These categories focus on production
reliability and failure modes, NOT security vulnerabilities.
"""

from typing import Any

from mcpreadiness.core.models import OperationalRiskCategory, Severity

__all__ = [
    "OperationalRiskCategory",
    "Severity",
    "CATEGORY_DESCRIPTIONS",
    "get_category_description",
    "get_category_severity",
    "format_category_help",
    "format_taxonomy_overview",
]

# Detailed descriptions for each category
CATEGORY_DESCRIPTIONS: dict[OperationalRiskCategory, dict[str, Any]] = {
    OperationalRiskCategory.SILENT_FAILURE_PATH: {
        "name": "Silent Failure Path",
        "short_description": "Tool may fail without surfacing errors to the caller",
        "long_description": """
A silent failure path exists when a tool can encounter an error condition
but continues execution without properly reporting the failure. This leads
to situations where:

- The calling agent believes the operation succeeded when it didn't
- Data may be partially processed or corrupted without indication
- Downstream operations proceed with invalid assumptions
- Debugging becomes extremely difficult due to lack of error signals

Common causes:
- Catching exceptions without re-raising or logging
- Using "best effort" semantics without status reporting
- Fire-and-forget patterns without confirmation
- Missing error response schemas
""",
        "default_severity": Severity.HIGH,
        "remediation": """
1. Define explicit error response schemas
2. Ensure all failure conditions return appropriate error responses
3. Avoid empty catch blocks or "swallow" patterns
4. Use structured error types that agents can interpret
5. Consider using observability hooks for error tracking
""",
    },
    OperationalRiskCategory.NON_DETERMINISTIC_RESPONSE: {
        "name": "Non-Deterministic Response",
        "short_description": "Tool response format or content varies unpredictably",
        "long_description": """
Non-deterministic responses occur when the same input can produce
structurally different outputs, making it difficult for agents to
reliably parse and act on results.

Symptoms include:
- Response schema varies based on internal state
- Optional fields that appear/disappear without clear rules
- Different field names for the same data
- Inconsistent data types (string vs number vs null)

Impact on agents:
- Parsing logic becomes fragile
- Agents may misinterpret data or crash
- Retry logic may behave inconsistently
- Test coverage becomes incomplete
""",
        "default_severity": Severity.MEDIUM,
        "remediation": """
1. Define strict response schemas with clear optionality rules
2. Use consistent field names and types across all responses
3. Document all possible response variations
4. Consider using discriminated unions for different response types
5. Add response validation in tests
""",
    },
    OperationalRiskCategory.MISSING_TIMEOUT_GUARD: {
        "name": "Missing Timeout Guard",
        "short_description": "Operations may hang indefinitely without timeout protection",
        "long_description": """
Without proper timeout guards, tool operations can hang indefinitely
when external dependencies become unresponsive. This creates cascading
failures in agent workflows.

Risk factors:
- Network calls without timeouts
- Database queries without limits
- External API calls without deadline propagation
- Long-running computations without checkpoints

Production impact:
- Agent threads/processes become stuck
- Resource exhaustion (connections, memory)
- User-facing latency spikes
- Cascading timeouts up the call chain
""",
        "default_severity": Severity.HIGH,
        "remediation": """
1. Configure explicit timeouts for all external calls
2. Set reasonable defaults based on expected operation duration
3. Implement deadline propagation from caller to callee
4. Add circuit breakers for repeated timeout failures
5. Monitor and alert on timeout rates
""",
    },
    OperationalRiskCategory.NO_OBSERVABILITY_HOOKS: {
        "name": "No Observability Hooks",
        "short_description": "Tool lacks logging, metrics, or tracing integration points",
        "long_description": """
Tools without observability hooks are difficult to monitor, debug, and
operate in production. When issues occur, operators lack the visibility
needed to diagnose and resolve problems quickly.

Missing observability includes:
- No structured logging
- No metrics emission
- No distributed tracing support
- No health check endpoints
- No performance profiling hooks

Operational impact:
- Blind spots in monitoring dashboards
- Extended incident resolution times
- Difficulty correlating issues across services
- No baseline for performance regression detection
""",
        "default_severity": Severity.MEDIUM,
        "remediation": """
1. Add structured logging with consistent fields
2. Emit key metrics (latency, error rate, throughput)
3. Support distributed tracing (trace ID propagation)
4. Implement health check responses
5. Consider adding debug/diagnostic modes
""",
    },
    OperationalRiskCategory.UNSAFE_RETRY_LOOP: {
        "name": "Unsafe Retry Loop",
        "short_description": "Retry logic may cause resource exhaustion or infinite loops",
        "long_description": """
Retry logic without proper safeguards can amplify failures rather than
recover from them. Unsafe retry patterns turn transient failures into
sustained outages.

Dangerous patterns:
- Unlimited retry attempts
- Fixed retry intervals (no backoff)
- Retrying non-idempotent operations
- No jitter in retry timing
- Retrying on all errors (including permanent failures)

Consequences:
- Thundering herd effects
- Resource exhaustion on dependent services
- Data duplication from non-idempotent retries
- Extended outages from retry amplification
""",
        "default_severity": Severity.HIGH,
        "remediation": """
1. Set maximum retry limits
2. Implement exponential backoff with jitter
3. Only retry on transient/retryable errors
4. Ensure idempotency for retried operations
5. Add circuit breakers to stop retries on sustained failures
""",
    },
    OperationalRiskCategory.OVERLOADED_TOOL_SCOPE: {
        "name": "Overloaded Tool Scope",
        "short_description": "Tool has too many capabilities, reducing reliability and predictability",
        "long_description": """
Tools with excessive capabilities become difficult to test, secure, and
maintain. They also create confusion for agents trying to select the
right tool for a task.

Signs of overloaded scope:
- Many unrelated capabilities in a single tool
- Complex branching logic based on parameters
- Large attack surface from capability combinations
- Difficulty documenting all behaviors
- Long, unfocused tool descriptions

Problems caused:
- Incomplete test coverage
- Unpredictable agent tool selection
- Higher maintenance burden
- Security review complexity
- Performance inconsistency across capabilities
""",
        "default_severity": Severity.MEDIUM,
        "remediation": """
1. Split into focused, single-purpose tools
2. Limit capabilities to related operations
3. Use composition over consolidation
4. Write clear, concise descriptions for each tool
5. Consider the principle of least authority
""",
    },
    OperationalRiskCategory.NO_FALLBACK_CONTRACT: {
        "name": "No Fallback Contract",
        "short_description": "Tool lacks defined degraded behavior or fallback modes",
        "long_description": """
Without a fallback contract, tools fail completely when dependencies
are unavailable, rather than providing degraded but useful responses.
This reduces system resilience.

Missing fallback patterns:
- No graceful degradation paths
- No cached/stale data options
- No default responses for unavailability
- No partial success handling
- No circuit breaker states

Impact:
- Complete failures propagate to users
- No graceful degradation during incidents
- Agents cannot adapt to reduced capability
- All-or-nothing behavior reduces availability
""",
        "default_severity": Severity.LOW,
        "remediation": """
1. Define explicit fallback behaviors
2. Implement graceful degradation modes
3. Consider caching for read operations
4. Document partial success semantics
5. Use feature flags for capability toggling
""",
    },
    OperationalRiskCategory.MISSING_ERROR_SCHEMA: {
        "name": "Missing Error Schema",
        "short_description": "Error responses lack structured schema for agent parsing",
        "long_description": """
Without a defined error schema, agents cannot programmatically handle
failures. They're left to parse error messages as text, which is
fragile and unreliable.

Problems with unstructured errors:
- Error types cannot be distinguished
- Retry decisions based on string matching
- Localized messages break parsing
- No machine-readable error codes
- Context information is unstructured

Agent limitations:
- Cannot implement proper error handling
- Fallback logic becomes heuristic
- Error reporting is inconsistent
- Recovery actions cannot be automated
""",
        "default_severity": Severity.MEDIUM,
        "remediation": """
1. Define explicit error response schema
2. Use error codes alongside messages
3. Include structured context in errors
4. Document all possible error types
5. Consider using standard error formats
""",
    },
}


def get_category_description(category: OperationalRiskCategory) -> dict[str, Any]:
    """Get the full description for an operational risk category."""
    return CATEGORY_DESCRIPTIONS.get(category, {})


def get_category_severity(category: OperationalRiskCategory) -> Severity:
    """Get the default severity for a category."""
    desc = CATEGORY_DESCRIPTIONS.get(category, {})
    return desc.get("default_severity", Severity.MEDIUM)


def format_category_help(category: OperationalRiskCategory) -> str:
    """Format a category's information for display."""
    desc = CATEGORY_DESCRIPTIONS.get(category, {})
    if not desc:
        return f"Unknown category: {category.value}"

    lines = [
        f"## {desc['name']}",
        "",
        f"**Category ID:** `{category.value}`",
        f"**Default Severity:** {desc['default_severity'].value}",
        "",
        "### Description",
        desc["short_description"],
        "",
        desc["long_description"].strip(),
        "",
        "### Remediation",
        desc["remediation"].strip(),
    ]
    return "\n".join(lines)


def format_taxonomy_overview() -> str:
    """Format the complete taxonomy for documentation."""
    lines = [
        "# MCP Readiness Scanner - Operational Risk Taxonomy",
        "",
        "This taxonomy covers operational readiness risks for MCP tools.",
        "For security vulnerabilities, see Cisco's MCP Scanner.",
        "",
    ]

    for category in OperationalRiskCategory:
        lines.append(format_category_help(category))
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
