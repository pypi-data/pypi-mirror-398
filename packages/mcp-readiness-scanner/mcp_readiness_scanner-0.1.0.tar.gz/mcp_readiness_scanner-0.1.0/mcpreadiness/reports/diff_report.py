"""
Diff report renderer for baseline comparisons.

Produces reports highlighting new and fixed findings compared to a baseline.
"""

from mcpreadiness.core.diff import ScanDiff
from mcpreadiness.core.models import Finding, Severity
from mcpreadiness.core.taxonomy import CATEGORY_DESCRIPTIONS

# Severity emoji mapping
SEVERITY_EMOJI = {
    Severity.CRITICAL: "🔴",
    Severity.HIGH: "🟠",
    Severity.MEDIUM: "🟡",
    Severity.LOW: "🔵",
    Severity.INFO: "⚪",
}


def render_diff_markdown(diff: ScanDiff, verbose: bool = False) -> str:
    """
    Render a scan diff as Markdown.

    Args:
        diff: The scan diff to render
        verbose: Include detailed information

    Returns:
        Markdown string representation
    """
    lines: list[str] = []

    # Header
    lines.append("# MCP Readiness Scan Diff Report")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"**Baseline:** `{diff.baseline.target}`")
    lines.append(f"**Current:** `{diff.current.target}`")
    lines.append("")
    lines.append(f"**Baseline Score:** {diff.baseline.readiness_score}/100")
    lines.append(f"**Current Score:** {diff.current.readiness_score}/100")

    score_delta = diff.current.readiness_score - diff.baseline.readiness_score
    if score_delta > 0:
        lines.append(f"**Score Change:** +{score_delta} ✅ (Improved)")
    elif score_delta < 0:
        lines.append(f"**Score Change:** {score_delta} ❌ (Regressed)")
    else:
        lines.append(f"**Score Change:** {score_delta} (No change)")

    lines.append("")

    # Change summary
    lines.append("### Changes")
    lines.append("")
    lines.append(f"- **New Findings:** {len(diff.new_findings)}")
    lines.append(f"- **Fixed Findings:** {len(diff.fixed_findings)}")
    lines.append(f"- **Unchanged:** {len(diff.unchanged_findings)}")
    lines.append("")

    # New findings
    if diff.new_findings:
        lines.append("## 🆕 New Findings (Regressions)")
        lines.append("")

        # Group by severity
        new_by_severity: dict[Severity, list[Finding]] = {}
        for finding in diff.new_findings:
            if finding.severity not in new_by_severity:
                new_by_severity[finding.severity] = []
            new_by_severity[finding.severity].append(finding)

        # Summary table
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for severity in Severity:
            findings = new_by_severity.get(severity, [])
            if findings:
                emoji = SEVERITY_EMOJI.get(severity, "")
                lines.append(f"| {emoji} {severity.value.capitalize()} | {len(findings)} |")
        lines.append("")

        # Detailed findings
        for severity in Severity:
            findings = new_by_severity.get(severity, [])
            if not findings:
                continue

            emoji = SEVERITY_EMOJI.get(severity, "")
            lines.append(f"### {emoji} {severity.value.capitalize()} ({len(findings)})")
            lines.append("")

            for i, finding in enumerate(findings, 1):
                lines.extend(_render_finding(finding, i, verbose))
                lines.append("")
    else:
        lines.append("## 🆕 New Findings")
        lines.append("")
        lines.append("*No new findings! No regressions detected.*")
        lines.append("")

    # Fixed findings
    if diff.fixed_findings:
        lines.append("## ✅ Fixed Findings (Improvements)")
        lines.append("")

        # Group by severity
        fixed_by_severity: dict[Severity, list[Finding]] = {}
        for finding in diff.fixed_findings:
            if finding.severity not in fixed_by_severity:
                fixed_by_severity[finding.severity] = []
            fixed_by_severity[finding.severity].append(finding)

        # Summary table
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for severity in Severity:
            findings = fixed_by_severity.get(severity, [])
            if findings:
                emoji = SEVERITY_EMOJI.get(severity, "")
                lines.append(f"| {emoji} {severity.value.capitalize()} | {len(findings)} |")
        lines.append("")

        # Detailed findings
        for severity in Severity:
            findings = fixed_by_severity.get(severity, [])
            if not findings:
                continue

            emoji = SEVERITY_EMOJI.get(severity, "")
            lines.append(f"### {emoji} {severity.value.capitalize()} ({len(findings)})")
            lines.append("")

            for i, finding in enumerate(findings, 1):
                lines.extend(_render_finding(finding, i, verbose))
                lines.append("")
    else:
        lines.append("## ✅ Fixed Findings")
        lines.append("")
        lines.append("*No findings were fixed.*")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Generated by [MCP Readiness Scanner](https://github.com/mcp-readiness/scanner)*")

    return "\n".join(lines)


def _render_finding(finding: Finding, index: int, verbose: bool) -> list[str]:
    """Render a single finding as Markdown."""
    lines: list[str] = []

    # Title with category
    category_desc = CATEGORY_DESCRIPTIONS.get(finding.category, {})
    category_name = category_desc.get("name", finding.category.value)

    lines.append(f"#### {index}. {finding.title}")
    lines.append("")

    # Metadata
    lines.append(f"- **Category:** {category_name}")
    if finding.rule_id:
        lines.append(f"- **Rule ID:** `{finding.rule_id}`")
    if finding.location:
        lines.append(f"- **Location:** `{finding.location}`")

    lines.append("")

    # Description (truncated if not verbose)
    if verbose:
        lines.append(finding.description)
    else:
        # Truncate to first 100 chars
        desc = finding.description[:100]
        if len(finding.description) > 100:
            desc += "..."
        lines.append(desc)

    return lines

