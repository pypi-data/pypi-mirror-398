"""
Heuristic Provider - Zero-dependency operational readiness checks.

This is the highest priority provider as it requires no external
dependencies. It performs static analysis of tool definitions and
configurations using Python heuristics.
"""

import re
from typing import Any

from mcpreadiness.core.models import Finding, OperationalRiskCategory, Severity
from mcpreadiness.providers.base import InspectionProvider

# Patterns that suggest dangerous/unreliable behavior in descriptions
DANGEROUS_PHRASES = [
    (r"ignore\s*error", "ignores errors"),
    (r"best\s*effort", "uses best-effort semantics"),
    (r"may\s*fail", "explicitly states it may fail"),
    (r"fire\s*and\s*forget", "uses fire-and-forget pattern"),
    (r"no\s*guarantee", "provides no guarantees"),
    (r"silent(ly)?\s*(fail|error|ignore)", "may silently fail"),
    (r"swallow.*exception", "swallows exceptions"),
    (r"fail\s*gracefully", "may fail without clear indication"),
]

# Patterns suggesting non-deterministic behavior
NON_DETERMINISTIC_PHRASES = [
    (r"random", "uses randomness"),
    (r"approximate", "provides approximate results"),
    (r"eventually", "eventual consistency"),
    (r"may\s*return\s*different", "may return different results"),
    (r"non-deterministic", "explicitly non-deterministic"),
]

# Patterns suggesting blocking/synchronous operations
BLOCKING_PHRASES = [
    (r"\bblocks?\b", "blocks execution"),
    (r"waits?\s*for", "waits for completion"),
    (r"synchronous(ly)?", "synchronous operation"),
    (r"hang", "may hang"),
    (r"will\s*not\s*return\s*until", "blocks until completion"),
]

# Patterns suggesting deprecated or experimental status
UNSTABLE_PHRASES = [
    (r"deprecated", "marked as deprecated"),
    (r"experimental", "experimental feature"),
    (r"\bbeta\b", "beta status"),
    (r"preview", "preview/unstable"),
    (r"not\s*recommended", "not recommended for use"),
    (r"use\s*at\s*your\s*own\s*risk", "use at your own risk"),
]

# Patterns suggesting bulk/cascade operations
BULK_OPERATION_PHRASES = [
    (r"\ball\b.*\b(delete|remove|update|modify)", "operates on all items"),
    (r"batch\s*(delete|remove|update|modify)", "batch operation"),
    (r"bulk\s*(delete|remove|update|modify)", "bulk operation"),
    (r"cascade", "cascade operation"),
    (r"recursive(ly)?\s*(delete|remove)", "recursive operation"),
]

# Default thresholds
DEFAULT_MAX_CAPABILITIES = 10
DEFAULT_MAX_DESCRIPTION_LENGTH = 2000
MIN_DESCRIPTION_LENGTH = 20


class HeuristicProvider(InspectionProvider):
    """
    Heuristic-based inspection provider.

    Performs zero-dependency operational readiness checks on tool
    definitions and configurations. Checks include:

    - Missing timeout configuration
    - Missing or zero retry limits
    - Excessive capabilities count
    - Missing error response schema
    - Missing or vague descriptions
    - No input validation schema
    - Missing rate limit configuration
    - Dangerous phrases in descriptions
    - Non-deterministic behavior indicators
    - Missing output/response schema
    - Missing authentication configuration
    - Blocking operation warnings
    - Missing idempotency documentation
    - Missing version information
    - Deprecated/experimental warnings
    - Missing resource cleanup documentation
    - Bulk/cascade operation risks
    - Missing circuit breaker configuration
    - Missing observability hooks
    """

    def __init__(
        self,
        max_capabilities: int = DEFAULT_MAX_CAPABILITIES,
        min_description_length: int = MIN_DESCRIPTION_LENGTH,
    ) -> None:
        """
        Initialize the heuristic provider.

        Args:
            max_capabilities: Maximum allowed capabilities before warning
            min_description_length: Minimum description length before warning
        """
        self.max_capabilities = max_capabilities
        self.min_description_length = min_description_length

    @property
    def name(self) -> str:
        return "heuristic"

    @property
    def description(self) -> str:
        return (
            "Zero-dependency heuristic checks for timeout, retry, "
            "scope, error handling, and description quality"
        )

    async def analyze_tool(self, tool_definition: dict[str, Any]) -> list[Finding]:
        """
        Analyze a tool definition for operational readiness issues.

        Checks performed:
        - Missing timeout configuration
        - Missing or zero retry limits
        - Excessive capabilities count
        - Missing error response schema
        - Missing or vague descriptions
        - No input validation schema
        - Dangerous phrases in descriptions
        """
        findings: list[Finding] = []
        tool_name = tool_definition.get("name", "unknown")

        # Check timeout configuration
        findings.extend(self._check_timeout(tool_definition, tool_name))

        # Check retry configuration
        findings.extend(self._check_retries(tool_definition, tool_name))

        # Check capabilities count
        findings.extend(self._check_capabilities(tool_definition, tool_name))

        # Check error schema
        findings.extend(self._check_error_schema(tool_definition, tool_name))

        # Check description quality
        findings.extend(self._check_description(tool_definition, tool_name))

        # Check input schema
        findings.extend(self._check_input_schema(tool_definition, tool_name))

        # Check rate limiting
        findings.extend(self._check_rate_limit(tool_definition, tool_name))

        # Check for dangerous phrases
        findings.extend(self._check_dangerous_phrases(tool_definition, tool_name))

        # Check for non-deterministic indicators
        findings.extend(self._check_non_deterministic(tool_definition, tool_name))

        # Check for missing output schema
        findings.extend(self._check_output_schema(tool_definition, tool_name))

        # Check for missing authentication
        findings.extend(self._check_authentication(tool_definition, tool_name))

        # Check for blocking operations
        findings.extend(self._check_blocking_operations(tool_definition, tool_name))

        # Check for idempotency documentation
        findings.extend(self._check_idempotency(tool_definition, tool_name))

        # Check for versioning
        findings.extend(self._check_versioning(tool_definition, tool_name))

        # Check for deprecated/experimental warnings
        findings.extend(self._check_unstable_status(tool_definition, tool_name))

        # Check for resource cleanup documentation
        findings.extend(self._check_resource_cleanup(tool_definition, tool_name))

        # Check for bulk operation risks
        findings.extend(self._check_bulk_operations(tool_definition, tool_name))

        # Check for circuit breaker
        findings.extend(self._check_circuit_breaker(tool_definition, tool_name))

        # Check for observability hooks
        findings.extend(self._check_observability(tool_definition, tool_name))

        return findings

    async def analyze_config(self, config: dict[str, Any]) -> list[Finding]:
        """
        Analyze an MCP configuration for operational readiness issues.

        Checks performed:
        - Server-level timeout configurations
        - Environment variable security (warnings for sensitive patterns)
        - Missing server configurations
        """
        findings: list[Finding] = []

        mcp_servers = config.get("mcpServers", {})

        if not mcp_servers:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                    severity=Severity.INFO,
                    title="No MCP servers configured",
                    description="Configuration file contains no MCP server definitions",
                    location="mcpServers",
                    provider=self.name,
                    rule_id="HEUR-CFG-001",
                )
            )
            return findings

        for server_name, server_config in mcp_servers.items():
            findings.extend(self._check_server_config(server_name, server_config))

        return findings

    def _check_timeout(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for timeout configuration."""
        findings: list[Finding] = []

        # Check various common timeout field names
        timeout_fields = ["timeout", "timeoutMs", "timeout_ms", "timeoutSeconds"]
        has_timeout = any(field in tool_def for field in timeout_fields)

        # Also check nested config
        config = tool_def.get("config", {})
        has_timeout = has_timeout or any(field in config for field in timeout_fields)

        if not has_timeout:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
                    severity=Severity.HIGH,
                    title="No timeout configuration",
                    description=(
                        f"Tool '{tool_name}' does not specify a timeout. "
                        "Operations may hang indefinitely if external services "
                        "become unresponsive."
                    ),
                    location=f"tool.{tool_name}",
                    provider=self.name,
                    remediation=(
                        "Add a 'timeout' or 'timeoutMs' field with a reasonable "
                        "value (e.g., 30000 for 30 seconds)"
                    ),
                    rule_id="HEUR-001",
                )
            )
        else:
            # Check if timeout is zero or negative
            for field in timeout_fields:
                timeout_value = tool_def.get(field) if field in tool_def else config.get(field)
                if timeout_value is not None and timeout_value <= 0:
                    findings.append(
                        Finding(
                            category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
                            severity=Severity.HIGH,
                            title="Invalid timeout value",
                            description=(
                                f"Tool '{tool_name}' has timeout set to {timeout_value}. "
                                "Zero or negative timeouts are effectively disabled."
                            ),
                            location=f"tool.{tool_name}.{field}",
                            evidence={"field": field, "value": timeout_value},
                            provider=self.name,
                            remediation="Set timeout to a positive value (e.g., 30000ms)",
                            rule_id="HEUR-002",
                        )
                    )

        return findings

    def _check_retries(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for retry configuration."""
        findings: list[Finding] = []

        # Check various common retry field names
        retry_fields = ["retries", "maxRetries", "max_retries", "retryCount", "retryLimit"]
        has_retries = any(field in tool_def for field in retry_fields)

        config = tool_def.get("config", {})
        has_retries = has_retries or any(field in config for field in retry_fields)

        if not has_retries:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.UNSAFE_RETRY_LOOP,
                    severity=Severity.MEDIUM,
                    title="No retry limit configured",
                    description=(
                        f"Tool '{tool_name}' does not specify a retry limit. "
                        "Without limits, retry logic may cause resource exhaustion "
                        "or infinite loops."
                    ),
                    location=f"tool.{tool_name}",
                    provider=self.name,
                    remediation=(
                        "Add a 'maxRetries' or 'retryLimit' field with a "
                        "reasonable value (e.g., 3)"
                    ),
                    rule_id="HEUR-003",
                )
            )
        else:
            # Check for unlimited retries (very high values or special values)
            for field in retry_fields:
                retry_value = tool_def.get(field) or config.get(field)
                if retry_value is not None:
                    if retry_value < 0:
                        findings.append(
                            Finding(
                                category=OperationalRiskCategory.UNSAFE_RETRY_LOOP,
                                severity=Severity.HIGH,
                                title="Negative retry limit",
                                description=(
                                    f"Tool '{tool_name}' has {field}={retry_value}. "
                                    "Negative values may indicate unlimited retries."
                                ),
                                location=f"tool.{tool_name}.{field}",
                                evidence={"field": field, "value": retry_value},
                                provider=self.name,
                                remediation="Set a positive retry limit (e.g., 3)",
                                rule_id="HEUR-004",
                            )
                        )
                    elif retry_value > 10:
                        findings.append(
                            Finding(
                                category=OperationalRiskCategory.UNSAFE_RETRY_LOOP,
                                severity=Severity.MEDIUM,
                                title="High retry limit",
                                description=(
                                    f"Tool '{tool_name}' has {field}={retry_value}. "
                                    "High retry limits may cause extended delays "
                                    "and resource exhaustion during outages."
                                ),
                                location=f"tool.{tool_name}.{field}",
                                evidence={"field": field, "value": retry_value},
                                provider=self.name,
                                remediation="Consider reducing retry limit to 3-5",
                                rule_id="HEUR-005",
                            )
                        )

        return findings

    def _check_capabilities(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for excessive capabilities."""
        findings: list[Finding] = []

        # Check various capability field names
        capability_fields = ["capabilities", "permissions", "scopes", "actions"]

        for field in capability_fields:
            capabilities = tool_def.get(field, [])
            if isinstance(capabilities, list) and len(capabilities) > self.max_capabilities:
                findings.append(
                    Finding(
                        category=OperationalRiskCategory.OVERLOADED_TOOL_SCOPE,
                        severity=Severity.MEDIUM,
                        title="Excessive capabilities",
                        description=(
                            f"Tool '{tool_name}' has {len(capabilities)} {field}, "
                            f"exceeding the recommended maximum of {self.max_capabilities}. "
                            "Tools with many capabilities are harder to test, "
                            "secure, and maintain."
                        ),
                        location=f"tool.{tool_name}.{field}",
                        evidence={"count": len(capabilities), "threshold": self.max_capabilities},
                        provider=self.name,
                        remediation=(
                            "Consider splitting into multiple focused tools, "
                            "each with a specific set of related capabilities"
                        ),
                        rule_id="HEUR-006",
                    )
                )

        # Check input schema for excessive properties (another indicator of overloaded scope)
        input_schema = tool_def.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        if len(properties) > 15:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.OVERLOADED_TOOL_SCOPE,
                    severity=Severity.LOW,
                    title="Many input parameters",
                    description=(
                        f"Tool '{tool_name}' has {len(properties)} input parameters. "
                        "This may indicate an overloaded tool scope."
                    ),
                    location=f"tool.{tool_name}.inputSchema.properties",
                    evidence={"count": len(properties)},
                    provider=self.name,
                    remediation="Consider if all parameters are necessary or if the tool should be split",
                    rule_id="HEUR-007",
                )
            )

        return findings

    def _check_error_schema(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for error response schema."""
        findings: list[Finding] = []

        error_schema_fields = ["errorSchema", "error_schema", "errors", "errorResponse"]
        has_error_schema = any(field in tool_def for field in error_schema_fields)

        if not has_error_schema:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.MISSING_ERROR_SCHEMA,
                    severity=Severity.MEDIUM,
                    title="No error response schema",
                    description=(
                        f"Tool '{tool_name}' does not define an error response schema. "
                        "Without structured error responses, agents cannot "
                        "programmatically handle failures."
                    ),
                    location=f"tool.{tool_name}",
                    provider=self.name,
                    remediation=(
                        "Add an 'errorSchema' field defining the structure of "
                        "error responses with error codes and messages"
                    ),
                    rule_id="HEUR-008",
                )
            )

        return findings

    def _check_description(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check description quality."""
        findings: list[Finding] = []

        description = tool_def.get("description", "")

        if not description:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                    severity=Severity.HIGH,
                    title="Missing description",
                    description=(
                        f"Tool '{tool_name}' has no description. "
                        "Agents rely on descriptions to understand tool capabilities "
                        "and select the appropriate tool for tasks."
                    ),
                    location=f"tool.{tool_name}.description",
                    provider=self.name,
                    remediation="Add a clear, detailed description explaining what the tool does",
                    rule_id="HEUR-009",
                )
            )
        elif len(description) < self.min_description_length:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                    severity=Severity.LOW,
                    title="Vague description",
                    description=(
                        f"Tool '{tool_name}' has a very short description "
                        f"({len(description)} characters). Brief descriptions "
                        "may not provide enough context for agents to use the "
                        "tool correctly."
                    ),
                    location=f"tool.{tool_name}.description",
                    evidence={"length": len(description), "minimum": self.min_description_length},
                    provider=self.name,
                    remediation="Expand the description to explain the tool's purpose, inputs, and expected outputs",
                    rule_id="HEUR-010",
                )
            )

        return findings

    def _check_input_schema(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for input validation schema."""
        findings: list[Finding] = []

        input_schema = tool_def.get("inputSchema")

        if not input_schema:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                    severity=Severity.MEDIUM,
                    title="No input validation schema",
                    description=(
                        f"Tool '{tool_name}' does not define an input schema. "
                        "Without input validation, invalid inputs may cause "
                        "unexpected behavior or failures."
                    ),
                    location=f"tool.{tool_name}.inputSchema",
                    provider=self.name,
                    remediation=(
                        "Add an 'inputSchema' field with JSON Schema defining "
                        "expected input types and constraints"
                    ),
                    rule_id="HEUR-011",
                )
            )
        else:
            # Check if schema has required fields defined
            if "required" not in input_schema and "properties" in input_schema:
                findings.append(
                    Finding(
                        category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                        severity=Severity.LOW,
                        title="No required fields specified",
                        description=(
                            f"Tool '{tool_name}' has an input schema but doesn't "
                            "specify which fields are required. This may lead to "
                            "missing input errors at runtime."
                        ),
                        location=f"tool.{tool_name}.inputSchema.required",
                        provider=self.name,
                        remediation="Add a 'required' array listing mandatory input fields",
                        rule_id="HEUR-012",
                    )
                )

        return findings

    def _check_rate_limit(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for rate limiting configuration."""
        findings: list[Finding] = []

        rate_limit_fields = ["rateLimit", "rate_limit", "rateLimitPerMinute", "throttle"]
        has_rate_limit = any(field in tool_def for field in rate_limit_fields)

        config = tool_def.get("config", {})
        has_rate_limit = has_rate_limit or any(field in config for field in rate_limit_fields)

        if not has_rate_limit:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.UNSAFE_RETRY_LOOP,
                    severity=Severity.LOW,
                    title="No rate limit configuration",
                    description=(
                        f"Tool '{tool_name}' does not specify rate limits. "
                        "Without rate limits, rapid repeated calls may overwhelm "
                        "external services or exhaust resources."
                    ),
                    location=f"tool.{tool_name}",
                    provider=self.name,
                    remediation="Add a 'rateLimit' field specifying maximum calls per time period",
                    rule_id="HEUR-013",
                )
            )

        return findings

    def _check_dangerous_phrases(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for dangerous phrases in descriptions."""
        findings: list[Finding] = []

        description = tool_def.get("description", "").lower()

        for pattern, meaning in DANGEROUS_PHRASES:
            if re.search(pattern, description, re.IGNORECASE):
                findings.append(
                    Finding(
                        category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                        severity=Severity.MEDIUM,
                        title="Dangerous phrase in description",
                        description=(
                            f"Tool '{tool_name}' description {meaning}. "
                            "This suggests potential silent failure paths that "
                            "may be difficult for agents to handle."
                        ),
                        location=f"tool.{tool_name}.description",
                        evidence={"pattern": pattern, "meaning": meaning},
                        provider=self.name,
                        remediation=(
                            "Document specific failure modes and ensure errors "
                            "are properly surfaced to callers"
                        ),
                        rule_id="HEUR-014",
                    )
                )

        return findings

    def _check_non_deterministic(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for indicators of non-deterministic behavior."""
        findings: list[Finding] = []

        description = tool_def.get("description", "").lower()

        for pattern, meaning in NON_DETERMINISTIC_PHRASES:
            if re.search(pattern, description, re.IGNORECASE):
                findings.append(
                    Finding(
                        category=OperationalRiskCategory.NON_DETERMINISTIC_RESPONSE,
                        severity=Severity.INFO,
                        title="Non-deterministic behavior indicated",
                        description=(
                            f"Tool '{tool_name}' description mentions {meaning}. "
                            "Ensure agents are prepared to handle variable outputs."
                        ),
                        location=f"tool.{tool_name}.description",
                        evidence={"pattern": pattern, "meaning": meaning},
                        provider=self.name,
                        remediation=(
                            "Document the conditions under which outputs may vary "
                            "and provide deterministic alternatives if possible"
                        ),
                        rule_id="HEUR-015",
                    )
                )

        return findings

    def _check_output_schema(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for output/response schema."""
        findings: list[Finding] = []

        output_schema_fields = ["outputSchema", "output_schema", "responseSchema", "response_schema"]
        has_output_schema = any(field in tool_def for field in output_schema_fields)

        if not has_output_schema:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.MISSING_ERROR_SCHEMA,
                    severity=Severity.LOW,
                    title="No output schema defined",
                    description=(
                        f"Tool '{tool_name}' does not define an output schema. "
                        "Agents cannot reliably parse responses without knowing "
                        "the expected structure."
                    ),
                    location=f"tool.{tool_name}",
                    provider=self.name,
                    remediation="Add an 'outputSchema' field defining the structure of successful responses",
                    rule_id="HEUR-016",
                )
            )

        return findings

    def _check_authentication(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for authentication configuration."""
        findings: list[Finding] = []

        auth_fields = ["auth", "authentication", "credentials", "apiKey", "api_key"]
        has_auth = any(field in tool_def for field in auth_fields)

        config = tool_def.get("config", {})
        has_auth = has_auth or any(field in config for field in auth_fields)

        # Check if description mentions external services
        description = tool_def.get("description", "").lower()
        mentions_external = any(
            keyword in description
            for keyword in ["api", "service", "endpoint", "http", "rest", "request"]
        )

        if mentions_external and not has_auth:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                    severity=Severity.MEDIUM,
                    title="No authentication configuration",
                    description=(
                        f"Tool '{tool_name}' appears to interact with external services "
                        "but does not define authentication configuration. This may lead "
                        "to authorization failures at runtime."
                    ),
                    location=f"tool.{tool_name}",
                    provider=self.name,
                    remediation="Add authentication configuration (e.g., 'auth', 'apiKey', 'credentials')",
                    rule_id="HEUR-017",
                )
            )

        return findings

    def _check_blocking_operations(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for blocking operation indicators."""
        findings: list[Finding] = []

        description = tool_def.get("description", "").lower()

        for pattern, meaning in BLOCKING_PHRASES:
            if re.search(pattern, description, re.IGNORECASE):
                findings.append(
                    Finding(
                        category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
                        severity=Severity.MEDIUM,
                        title="Blocking operation indicated",
                        description=(
                            f"Tool '{tool_name}' description indicates it {meaning}. "
                            "Blocking operations can cause the entire agent workflow "
                            "to hang if not properly guarded with timeouts."
                        ),
                        location=f"tool.{tool_name}.description",
                        evidence={"pattern": pattern, "meaning": meaning},
                        provider=self.name,
                        remediation=(
                            "Ensure proper timeout configuration and consider making "
                            "the operation asynchronous or non-blocking"
                        ),
                        rule_id="HEUR-018",
                    )
                )

        return findings

    def _check_idempotency(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for idempotency documentation."""
        findings: list[Finding] = []

        description = tool_def.get("description", "").lower()

        # Check if tool appears to be state-changing
        state_changing_verbs = [
            "create", "delete", "update", "modify", "remove", "insert",
            "write", "post", "put", "patch"
        ]
        is_state_changing = any(verb in description for verb in state_changing_verbs)

        # Check if idempotency is documented
        idempotency_indicators = ["idempotent", "safe to retry", "can be retried"]
        has_idempotency_doc = any(indicator in description for indicator in idempotency_indicators)

        if is_state_changing and not has_idempotency_doc:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.UNSAFE_RETRY_LOOP,
                    severity=Severity.MEDIUM,
                    title="Missing idempotency documentation",
                    description=(
                        f"Tool '{tool_name}' appears to perform state-changing operations "
                        "but doesn't document whether it's idempotent. This is critical "
                        "for retry logic - non-idempotent operations may cause duplicates."
                    ),
                    location=f"tool.{tool_name}.description",
                    provider=self.name,
                    remediation=(
                        "Document whether the operation is idempotent and safe to retry. "
                        "If not idempotent, consider adding idempotency keys or tokens."
                    ),
                    rule_id="HEUR-019",
                )
            )

        return findings

    def _check_versioning(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for versioning information."""
        findings: list[Finding] = []

        version_fields = ["version", "apiVersion", "api_version", "schemaVersion"]
        has_version = any(field in tool_def for field in version_fields)

        if not has_version:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.NO_OBSERVABILITY_HOOKS,
                    severity=Severity.LOW,
                    title="No version information",
                    description=(
                        f"Tool '{tool_name}' does not specify a version. "
                        "Versioning helps track changes and ensure compatibility "
                        "when tools evolve over time."
                    ),
                    location=f"tool.{tool_name}",
                    provider=self.name,
                    remediation="Add a 'version' field (e.g., '1.0.0') following semantic versioning",
                    rule_id="HEUR-020",
                )
            )

        return findings

    def _check_unstable_status(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for deprecated or experimental warnings."""
        findings: list[Finding] = []

        description = tool_def.get("description", "").lower()

        for pattern, meaning in UNSTABLE_PHRASES:
            if re.search(pattern, description, re.IGNORECASE):
                findings.append(
                    Finding(
                        category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                        severity=Severity.MEDIUM,
                        title="Unstable or deprecated tool",
                        description=(
                            f"Tool '{tool_name}' is {meaning}. "
                            "Using unstable or deprecated tools in production "
                            "may lead to unexpected behavior or breakage."
                        ),
                        location=f"tool.{tool_name}.description",
                        evidence={"pattern": pattern, "meaning": meaning},
                        provider=self.name,
                        remediation=(
                            "Avoid using deprecated/experimental tools in production. "
                            "If necessary, implement additional safeguards and monitoring."
                        ),
                        rule_id="HEUR-021",
                    )
                )

        return findings

    def _check_resource_cleanup(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for resource cleanup documentation."""
        findings: list[Finding] = []

        description = tool_def.get("description", "").lower()

        # Check if tool appears to use resources that need cleanup
        resource_indicators = [
            "connection", "file", "stream", "socket", "handle",
            "session", "lock", "transaction"
        ]
        uses_resources = any(indicator in description for indicator in resource_indicators)

        # Check if cleanup is documented
        cleanup_indicators = ["close", "cleanup", "release", "dispose", "free"]
        has_cleanup_doc = any(indicator in description for indicator in cleanup_indicators)

        if uses_resources and not has_cleanup_doc:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                    severity=Severity.MEDIUM,
                    title="Missing resource cleanup documentation",
                    description=(
                        f"Tool '{tool_name}' appears to use resources (connections, "
                        "files, etc.) but doesn't document cleanup procedures. "
                        "Resource leaks can cause production instability."
                    ),
                    location=f"tool.{tool_name}.description",
                    provider=self.name,
                    remediation=(
                        "Document how resources are cleaned up. Ensure proper "
                        "cleanup in error paths and add timeout-based cleanup."
                    ),
                    rule_id="HEUR-022",
                )
            )

        return findings

    def _check_bulk_operations(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for bulk/cascade operation risks."""
        findings: list[Finding] = []

        description = tool_def.get("description", "").lower()

        for pattern, meaning in BULK_OPERATION_PHRASES:
            if re.search(pattern, description, re.IGNORECASE):
                # Check if there are safeguards mentioned
                safeguard_keywords = [
                    "confirm", "dry-run", "preview", "limit", "max",
                    "safeguard", "protection", "verify"
                ]
                has_safeguards = any(keyword in description for keyword in safeguard_keywords)

                if not has_safeguards:
                    findings.append(
                        Finding(
                            category=OperationalRiskCategory.OVERLOADED_TOOL_SCOPE,
                            severity=Severity.HIGH,
                            title="Bulk operation without safeguards",
                            description=(
                                f"Tool '{tool_name}' {meaning} but doesn't document "
                                "safeguards like confirmations, dry-run mode, or limits. "
                                "Unguarded bulk operations can cause catastrophic data loss."
                            ),
                            location=f"tool.{tool_name}.description",
                            evidence={"pattern": pattern, "meaning": meaning},
                            provider=self.name,
                            remediation=(
                                "Add safeguards: require confirmation, implement dry-run mode, "
                                "add item limits, or provide preview functionality"
                            ),
                            rule_id="HEUR-023",
                        )
                    )

        return findings

    def _check_circuit_breaker(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for circuit breaker configuration."""
        findings: list[Finding] = []

        description = tool_def.get("description", "").lower()

        # Check if tool interacts with external services
        external_service_indicators = [
            "api", "service", "endpoint", "http", "rest",
            "external", "third-party", "remote"
        ]
        uses_external = any(indicator in description for indicator in external_service_indicators)

        circuit_breaker_fields = [
            "circuitBreaker", "circuit_breaker", "failureThreshold",
            "failure_threshold", "healthCheck", "health_check"
        ]
        has_circuit_breaker = any(field in tool_def for field in circuit_breaker_fields)

        config = tool_def.get("config", {})
        has_circuit_breaker = has_circuit_breaker or any(
            field in config for field in circuit_breaker_fields
        )

        if uses_external and not has_circuit_breaker:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.UNSAFE_RETRY_LOOP,
                    severity=Severity.MEDIUM,
                    title="No circuit breaker configuration",
                    description=(
                        f"Tool '{tool_name}' interacts with external services "
                        "but doesn't configure a circuit breaker. Without circuit "
                        "breakers, cascading failures can overwhelm the system."
                    ),
                    location=f"tool.{tool_name}",
                    provider=self.name,
                    remediation=(
                        "Add circuit breaker configuration with failure thresholds "
                        "and automatic recovery mechanisms"
                    ),
                    rule_id="HEUR-024",
                )
            )

        return findings

    def _check_observability(
        self, tool_def: dict[str, Any], tool_name: str
    ) -> list[Finding]:
        """Check for observability/monitoring hooks."""
        findings: list[Finding] = []

        observability_fields = [
            "logging", "metrics", "telemetry", "tracing",
            "monitoring", "instrumentation", "logger"
        ]
        has_observability = any(field in tool_def for field in observability_fields)

        config = tool_def.get("config", {})
        has_observability = has_observability or any(
            field in config for field in observability_fields
        )

        if not has_observability:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.NO_OBSERVABILITY_HOOKS,
                    severity=Severity.LOW,
                    title="No observability configuration",
                    description=(
                        f"Tool '{tool_name}' does not configure observability hooks "
                        "(logging, metrics, tracing). Without observability, "
                        "debugging production issues becomes extremely difficult."
                    ),
                    location=f"tool.{tool_name}",
                    provider=self.name,
                    remediation=(
                        "Add logging, metrics, or tracing configuration to enable "
                        "monitoring and debugging in production"
                    ),
                    rule_id="HEUR-025",
                )
            )

        return findings

    def _check_server_config(
        self, server_name: str, server_config: dict[str, Any]
    ) -> list[Finding]:
        """Check server-level configuration."""
        findings: list[Finding] = []

        # Check for missing command
        if "command" not in server_config:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                    severity=Severity.HIGH,
                    title="Missing server command",
                    description=(
                        f"Server '{server_name}' does not specify a command. "
                        "The server cannot be started without a command."
                    ),
                    location=f"mcpServers.{server_name}.command",
                    provider=self.name,
                    rule_id="HEUR-CFG-002",
                )
            )

        # Check for env vars that might contain secrets
        env_vars = server_config.get("env", {})
        sensitive_patterns = ["key", "secret", "token", "password", "credential"]
        for env_name in env_vars:
            if any(p in env_name.lower() for p in sensitive_patterns):
                findings.append(
                    Finding(
                        category=OperationalRiskCategory.NO_OBSERVABILITY_HOOKS,
                        severity=Severity.INFO,
                        title="Sensitive environment variable",
                        description=(
                            f"Server '{server_name}' has environment variable "
                            f"'{env_name}' that may contain sensitive data. "
                            "Ensure this is not logged or exposed."
                        ),
                        location=f"mcpServers.{server_name}.env.{env_name}",
                        provider=self.name,
                        rule_id="HEUR-CFG-003",
                    )
                )

        # Check for timeout at server level
        if "timeout" not in server_config:
            findings.append(
                Finding(
                    category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
                    severity=Severity.MEDIUM,
                    title="No server timeout",
                    description=(
                        f"Server '{server_name}' does not specify a timeout. "
                        "Server initialization may hang indefinitely."
                    ),
                    location=f"mcpServers.{server_name}",
                    provider=self.name,
                    remediation="Add a 'timeout' field for server initialization",
                    rule_id="HEUR-CFG-004",
                )
            )

        return findings
