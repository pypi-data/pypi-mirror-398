"""
SARIF Report Generator for MCP Readiness Scanner.

Produces SARIF 2.1.0 output for GitHub Code Scanning integration
and other SARIF-compatible tools.

SARIF Specification: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

import json
from typing import Any

from mcpreadiness import __version__
from mcpreadiness.core.models import Finding, ScanResult, Severity
from mcpreadiness.core.taxonomy import CATEGORY_DESCRIPTIONS, OperationalRiskCategory

# SARIF severity levels
SARIF_LEVELS = {
    Severity.CRITICAL: "error",
    Severity.HIGH: "error",
    Severity.MEDIUM: "warning",
    Severity.LOW: "note",
    Severity.INFO: "none",
}

# SARIF security severity for GitHub
SARIF_SECURITY_SEVERITY = {
    Severity.CRITICAL: "critical",
    Severity.HIGH: "high",
    Severity.MEDIUM: "medium",
    Severity.LOW: "low",
    Severity.INFO: "low",
}


def render_sarif(result: ScanResult) -> str:
    """
    Render a scan result as SARIF 2.1.0 JSON.

    Args:
        result: The scan result to render

    Returns:
        SARIF JSON string
    """
    sarif = _build_sarif(result)
    return json.dumps(sarif, indent=2)


def _build_sarif(result: ScanResult) -> dict[str, Any]:
    """Build the SARIF document structure."""
    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [_build_run(result)],
    }


def _build_run(result: ScanResult) -> dict[str, Any]:
    """Build a SARIF run object."""
    return {
        "tool": _build_tool(),
        "results": [_build_result(f, i, result.target) for i, f in enumerate(result.findings)],
        "invocations": [
            {
                "executionSuccessful": True,
                "endTimeUtc": result.timestamp.isoformat() + "Z",
            }
        ],
        "properties": {
            "readinessScore": result.readiness_score,
            "isProductionReady": result.is_production_ready,
            "target": result.target,
            "providersUsed": result.providers_used,
        },
    }


def _build_tool() -> dict[str, Any]:
    """Build the SARIF tool object."""
    return {
        "driver": {
            "name": "mcp-readiness-scanner",
            "version": __version__,
            "informationUri": "https://github.com/mcp-readiness/scanner",
            "rules": _build_rules(),
            "properties": {
                "tags": ["mcp", "operational-readiness", "agentic-ai"],
            },
        }
    }


def _build_rules() -> list[dict[str, Any]]:
    """Build SARIF rule definitions from taxonomy."""
    rules = []

    for category in OperationalRiskCategory:
        desc = CATEGORY_DESCRIPTIONS.get(category, {})
        default_severity = desc.get("default_severity", Severity.MEDIUM)

        rule = {
            "id": category.value,
            "name": desc.get("name", category.value),
            "shortDescription": {
                "text": desc.get("short_description", "Operational readiness issue")
            },
            "fullDescription": {
                "text": desc.get("long_description", "").strip()[:1000]
            },
            "helpUri": f"https://github.com/mcp-readiness/scanner/blob/main/docs/taxonomy.md#{category.value}",
            "help": {
                "text": desc.get("remediation", "Review the finding and address the issue.").strip(),
                "markdown": desc.get("remediation", "Review the finding and address the issue.").strip(),
            },
            "defaultConfiguration": {
                "level": SARIF_LEVELS.get(default_severity, "warning"),
            },
            "properties": {
                "tags": ["operational-readiness", category.value],
                "security-severity": SARIF_SECURITY_SEVERITY.get(default_severity, "medium"),
            },
        }
        rules.append(rule)

    return rules


def _parse_location_region(location: str | None) -> tuple[str | None, dict[str, int] | None]:
    """
    Parse a location string to extract file/path and line/region information.

    Supports formats:
    - "file.json:line"
    - "file.json:start-end"
    - "path.to.field"
    - "tool.name"

    Returns:
        Tuple of (logical_name, region) where region is a dict with startLine/endLine
    """
    if not location:
        return None, None

    # Check for line number format: "path:123" or "path:10-20"
    if ":" in location and location.split(":")[-1].replace("-", "").isdigit():
        parts = location.rsplit(":", 1)
        logical_name = parts[0]
        line_part = parts[1]

        if "-" in line_part:
            # Range format: "10-20"
            start, end = line_part.split("-", 1)
            region = {
                "startLine": int(start),
                "endLine": int(end),
            }
        else:
            # Single line: "123"
            line = int(line_part)
            region = {
                "startLine": line,
                "endLine": line,
            }
        return logical_name, region

    # No line numbers, just a logical location
    return location, None


def _build_location(finding_location: str | None, target: str | None) -> dict[str, Any] | None:
    """
    Build a SARIF location object with physical and logical locations.

    Args:
        finding_location: The location string from the finding
        target: The scan target (file path)

    Returns:
        SARIF location object or None
    """
    logical_name, region = _parse_location_region(finding_location)

    # Use target as the artifact URI if available, otherwise use logical name
    artifact_uri = target or logical_name or "unknown"

    location: dict[str, Any] = {}

    # Build physical location
    physical_location: dict[str, Any] = {
        "artifactLocation": {
            "uri": artifact_uri,
            "uriBaseId": "%SRCROOT%",
        },
    }

    # Add region if we have line information
    if region:
        physical_location["region"] = region

    location["physicalLocation"] = physical_location

    # Build logical location if we have a logical name
    if logical_name and logical_name != artifact_uri:
        location["logicalLocations"] = [
            {
                "name": logical_name,
                "fullyQualifiedName": logical_name,
                "kind": "member",  # Use "member" for fields, properties, etc.
            }
        ]

    return location


def _build_result(finding: Finding, index: int, target: str | None = None) -> dict[str, Any]:
    """
    Build a SARIF result object from a finding.

    Args:
        finding: The finding to convert
        index: Index of this finding in the results list
        target: The scan target (file path) for the result
    """
    result: dict[str, Any] = {
        "ruleId": finding.category.value,
        "ruleIndex": list(OperationalRiskCategory).index(finding.category),
        "level": SARIF_LEVELS.get(finding.severity, "warning"),
        "message": {
            "text": f"{finding.title}: {finding.description}",
        },
        "locations": [],
        "properties": {
            "provider": finding.provider,
            "severity": finding.severity.value,
        },
    }

    # Add rule ID if present
    if finding.rule_id:
        result["properties"]["ruleId"] = finding.rule_id

    # Add location if present
    if finding.location or target:
        location = _build_location(finding.location, target)
        if location:
            result["locations"].append(location)

    # Add evidence as properties
    if finding.evidence:
        result["properties"]["evidence"] = finding.evidence

    # Add remediation as fix suggestion
    if finding.remediation:
        result["fixes"] = [
            {
                "description": {
                    "text": finding.remediation,
                },
            }
        ]

    return result


def render_sarif_summary(result: ScanResult) -> dict[str, Any]:
    """
    Generate a SARIF summary without full results.

    Useful for quick status in CI without full details.
    """
    return {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "mcp-readiness-scanner",
                        "version": __version__,
                    }
                },
                "results": [],
                "properties": {
                    "readinessScore": result.readiness_score,
                    "isProductionReady": result.is_production_ready,
                    "findingsCount": len(result.findings),
                    "findingsBySeverity": result.finding_counts_by_severity,
                },
            }
        ],
    }
