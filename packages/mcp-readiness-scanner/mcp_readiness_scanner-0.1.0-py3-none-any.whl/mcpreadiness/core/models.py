"""
Pydantic v2 models for MCP Readiness Scanner.

All serializable objects use Pydantic BaseModel for validation,
serialization, and schema generation.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    """Severity levels for findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OperationalRiskCategory(str, Enum):
    """
    Operational risk categories for MCP tools.

    These categories focus on production reliability and failure modes,
    NOT security vulnerabilities (which are covered by tools like Cisco's MCP Scanner).
    """

    SILENT_FAILURE_PATH = "silent_failure_path"
    NON_DETERMINISTIC_RESPONSE = "non_deterministic_response"
    MISSING_TIMEOUT_GUARD = "missing_timeout_guard"
    NO_OBSERVABILITY_HOOKS = "no_observability_hooks"
    UNSAFE_RETRY_LOOP = "unsafe_retry_loop"
    OVERLOADED_TOOL_SCOPE = "overloaded_tool_scope"
    NO_FALLBACK_CONTRACT = "no_fallback_contract"
    MISSING_ERROR_SCHEMA = "missing_error_schema"


class Finding(BaseModel):
    """
    A single finding from an inspection provider.

    Represents an operational readiness issue detected in an MCP tool
    or configuration.
    """

    category: OperationalRiskCategory = Field(
        description="The operational risk category this finding belongs to"
    )
    severity: Severity = Field(description="Severity level of the finding")
    title: str = Field(description="Short, descriptive title of the finding")
    description: str = Field(
        description="Detailed description of the issue and its impact"
    )
    location: str | None = Field(
        default=None,
        description="Where the issue was found (e.g., field path, line number)",
    )
    evidence: dict[str, Any] | None = Field(
        default=None,
        description="Supporting evidence (e.g., the problematic value, context)",
    )
    provider: str = Field(
        description="Name of the inspection provider that generated this finding"
    )
    remediation: str | None = Field(
        default=None,
        description="Suggested fix or remediation steps",
    )
    rule_id: str | None = Field(
        default=None,
        description="Identifier for the rule that triggered this finding",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category": "missing_timeout_guard",
                    "severity": "high",
                    "title": "No timeout configuration",
                    "description": "Tool does not specify a timeout, which may cause indefinite hangs in production",
                    "location": "tool.config",
                    "evidence": {"config_keys": ["retries", "rateLimit"]},
                    "provider": "heuristic",
                    "remediation": "Add a 'timeout' field with a reasonable value (e.g., 30 seconds)",
                    "rule_id": "HEUR-001",
                }
            ]
        }
    }


class ScanResult(BaseModel):
    """
    Result of scanning an MCP tool or configuration.

    Aggregates findings from all providers and computes a readiness score.
    """

    target: str = Field(
        description="Identifier for the scan target (file path, tool name, etc.)"
    )
    findings: list[Finding] = Field(
        default_factory=list, description="List of findings from all providers"
    )
    readiness_score: int = Field(
        ge=0,
        le=100,
        description="Readiness score from 0-100 (100 = fully ready for production)",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the scan was performed"
    )
    providers_used: list[str] = Field(
        default_factory=list,
        description="List of provider names that were used in this scan",
    )
    scan_duration_ms: int | None = Field(
        default=None, description="How long the scan took in milliseconds"
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata about the scan (e.g., tool version, config)",
    )

    @field_validator("readiness_score")
    @classmethod
    def clamp_score(cls, v: int) -> int:
        """Ensure score is within valid range."""
        return max(0, min(100, v))

    @property
    def has_critical_findings(self) -> bool:
        """Check if any critical findings exist."""
        return any(f.severity == Severity.CRITICAL for f in self.findings)

    @property
    def has_high_findings(self) -> bool:
        """Check if any high severity findings exist."""
        return any(f.severity == Severity.HIGH for f in self.findings)

    @property
    def finding_counts_by_severity(self) -> dict[str, int]:
        """Get count of findings grouped by severity."""
        counts = {s.value: 0 for s in Severity}
        for finding in self.findings:
            counts[finding.severity.value] += 1
        return counts

    @property
    def finding_counts_by_category(self) -> dict[str, int]:
        """Get count of findings grouped by category."""
        counts: dict[str, int] = {}
        for finding in self.findings:
            cat = finding.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    @property
    def is_production_ready(self) -> bool:
        """
        Determine if the target is production ready.

        Production ready means:
        - No critical findings
        - No high findings
        - Readiness score >= 80
        """
        return (
            not self.has_critical_findings
            and not self.has_high_findings
            and self.readiness_score >= 80
        )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "target": "examples/sample_tool_definitions/bad_tool.json",
                    "findings": [],
                    "readiness_score": 65,
                    "timestamp": "2024-01-15T10:30:00Z",
                    "providers_used": ["heuristic", "yara"],
                    "scan_duration_ms": 150,
                }
            ]
        }
    }


class ProviderStatus(BaseModel):
    """Status information for an inspection provider."""

    name: str = Field(description="Provider name")
    available: bool = Field(description="Whether the provider is available")
    reason: str | None = Field(
        default=None, description="Reason if provider is not available"
    )
    version: str | None = Field(default=None, description="Provider version if known")


class ScanConfig(BaseModel):
    """Configuration for a scan operation."""

    providers: list[str] | None = Field(
        default=None, description="List of providers to use (None = all available)"
    )
    fail_on_critical: bool = Field(
        default=True, description="Exit with error code if critical findings found"
    )
    fail_on_high: bool = Field(
        default=False, description="Exit with error code if high findings found"
    )
    min_score: int | None = Field(
        default=None, description="Minimum readiness score required to pass"
    )
    output_format: str = Field(
        default="json", description="Output format (json, markdown, sarif)"
    )
    verbose: bool = Field(default=False, description="Enable verbose output")
