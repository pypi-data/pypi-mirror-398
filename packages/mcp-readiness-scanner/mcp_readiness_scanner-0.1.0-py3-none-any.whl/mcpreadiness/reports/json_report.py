"""
JSON Report Generator for MCP Readiness Scanner.

Produces JSON output suitable for CI pipelines, APIs, and
programmatic consumption.
"""

import json
from typing import Any

from mcpreadiness.core.models import ScanResult


def render_json(
    result: ScanResult,
    indent: int | None = 2,
    include_metadata: bool = True,
) -> str:
    """
    Render a scan result as JSON.

    Args:
        result: The scan result to render
        indent: JSON indentation (None for compact)
        include_metadata: Whether to include scan metadata

    Returns:
        JSON string representation of the scan result
    """
    data = result.model_dump(mode="json")

    if not include_metadata:
        data.pop("metadata", None)
        data.pop("scan_duration_ms", None)

    return json.dumps(data, indent=indent, default=str)


def render_json_summary(result: ScanResult) -> str:
    """
    Render a compact JSON summary of the scan result.

    Useful for quick status checks in CI pipelines.

    Args:
        result: The scan result to summarize

    Returns:
        Compact JSON summary
    """
    summary = {
        "target": result.target,
        "readiness_score": result.readiness_score,
        "is_production_ready": result.is_production_ready,
        "findings_count": len(result.findings),
        "findings_by_severity": result.finding_counts_by_severity,
        "has_critical": result.has_critical_findings,
        "has_high": result.has_high_findings,
    }

    return json.dumps(summary, indent=None)


def findings_to_json(result: ScanResult) -> list[dict[str, Any]]:
    """
    Extract just the findings as a list of dicts.

    Args:
        result: The scan result

    Returns:
        List of finding dictionaries
    """
    return [f.model_dump(mode="json") for f in result.findings]
